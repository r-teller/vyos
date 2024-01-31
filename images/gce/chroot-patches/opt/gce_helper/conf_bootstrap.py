import tempfile
import os
import logging
from gcelogging import setup_logging
from constants import VYOS_API_PORT, CONF_BOOTSTRAP_LOG_NAME
from configuration import configuration
from utils import download_gcs_file
from vyos_api import get_local_api_client
from vyos.configtree import (
    ConfigTree,
)  # This is imported via symbolic link to system's python3.7 dist-packages
from exceptions import ConfigurationDownloadException


_CLIENT_ID = "CONF_BOOTSTRAP"


l = logging.getLogger(CONF_BOOTSTRAP_LOG_NAME)


def load_configuration(project_id, bucket_id, object_id):
    """Downloads the latest version of the configuration and loads it"""
    # Before acknowledging the message, we first perform a backup of the current configuration,
    # then we try to apply the new desired state.
    api_client = get_local_api_client(_CLIENT_ID)
    with tempfile.NamedTemporaryFile() as tmp:
        try:
            l.info(
                "Fetching new configuration file from gs://%s/%s", bucket_id, object_id
            )
            download_gcs_file(
                project_id=project_id,
                bucket_id=bucket_id,
                object_id=object_id,
                file_obj=tmp,
            )
            tmp.flush()
            l.info("New configuration loaded to %s", tmp.name)

        except:
            l.exception("Failed to download the configuration file from bucket.")
            raise ConfigurationDownloadException(
                "Failed to download the configuration file from bucket."
            )

        # Read the file into memory to perform some manipulation
        tmp.seek(0)
        conf_text = tmp.read()
        conf = ConfigTree(conf_text.decode("utf-8"))

        # Patch the configuration file with the API Keys being used right now:
        api_keys = api_client.get_config(["service", "https", "api", "keys"])
        conf.set(["service", "https", "api", "port"], VYOS_API_PORT)
        conf.set(["service", "https", "api-restrict", "virtual-host"], "localhost")
        conf.set(["service", "https", "api", "keys", "id"])
        for key_name, key_value in api_keys["id"].items():
            conf.set(["service", "https", "api", "keys", "id"], key_name)
            conf.set_tag(["service", "https", "api", "keys", "id"])
            conf.set(
                ["service", "https", "api", "keys", "id", key_name, "key"],
                key_value["key"],
            )
        patched_conf = conf.to_string()

        l.debug("Patched configuration file (%s): %s", tmp.name, patched_conf)

        # Write back the modified file
        tmp.seek(0)
        tmp.truncate()
        tmp.write(patched_conf.encode("utf-8"))
        tmp.flush()

        # Align permissions
        os.chmod(tmp.name, 0o750)
        api_client.load_configuration_from_file(file_path=tmp.name)


def main() -> None:
    """Entry point of the application."""
    l.info("Starting conf_bootstrap daemon.")

    setup_logging()

    # Perform a first load
    load_configuration(
        configuration.project_id, configuration.bucket_id, configuration.object_id
    )


if __name__ == "__main__":
    main()
