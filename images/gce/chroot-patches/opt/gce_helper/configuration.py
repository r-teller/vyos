import requests

from utils import get_metadata


class Configuration:
    def __init__(self, project_id: str, bucket_id: str, object_id: str):
        """Constructor."""
        self._project_id = project_id
        self._bucket_id = bucket_id
        self._object_id = object_id

    @property
    def project_id(self):
        """Project-id where this daemon is running on."""
        return self._project_id

    @property
    def bucket_id(self):
        """Bucket id where the configuration is stored"""
        return self._bucket_id

    @property
    def object_id(self):
        """Object id of the configuration"""
        return self._object_id

    @staticmethod
    def load_from_metadata() -> "Configuration":
        """Loads the configuration from instance metadata"""
        project_id = str(
            get_metadata(
                metadata_path="/computeMetadata/v1/project/project-id", alt="text"
            )
        )
        bucket_id = str(
            get_metadata(
                metadata_path="/computeMetadata/v1/instance/attributes/configuration_bucket_id",
                alt="text",
            )
        )
        object_id = str(
            get_metadata(
                metadata_path="/computeMetadata/v1/instance/attributes/configuration_object_id",
                alt="text",
            )
        )

        return Configuration(
            project_id=project_id, bucket_id=bucket_id, object_id=object_id
        )

    def __repr__(self):
        return self.__dict__


configuration = Configuration.load_from_metadata()
