# coding: utf-8
# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
from oci.util import (
    formatted_flat_dict,
    NONE_SENTINEL,
    value_allowed_none_or_none_sentinel,
)  # noqa: F401
from oci.decorators import init_model_state_from_kwargs


@init_model_state_from_kwargs
class MountSpecification(object):
    """
    Specification related to a new Mount.
    """

    #: A constant which can be used with the mount_scope_entity_type property of a MountSpecification.
    #: This constant has a value of "DATABASE"
    MOUNT_SCOPE_ENTITY_TYPE_DATABASE = "DATABASE"

    #: A constant which can be used with the mount_scope_entity_type property of a MountSpecification.
    #: This constant has a value of "TABLE"
    MOUNT_SCOPE_ENTITY_TYPE_TABLE = "TABLE"

    #: A constant which can be used with the mount_scope_entity_type property of a MountSpecification.
    #: This constant has a value of "USER"
    MOUNT_SCOPE_ENTITY_TYPE_USER = "USER"

    def __init__(self, **kwargs):
        """
        Initializes a new MountSpecification object with values from keyword arguments.
        The following keyword arguments are supported (corresponding to the getters/setters of this class):

        :param obj_store_location:
            The value to assign to the obj_store_location property of this MountSpecification.
        :type obj_store_location: str

        :param file_path:
            The value to assign to the file_path property of this MountSpecification.
        :type file_path: str

        :param namespace:
            The value to assign to the namespace property of this MountSpecification.
        :type namespace: str

        :param bucket_name:
            The value to assign to the bucket_name property of this MountSpecification.
        :type bucket_name: str

        :param mount_scope_entity_type:
            The value to assign to the mount_scope_entity_type property of this MountSpecification.
            Allowed values for this property are: "DATABASE", "TABLE", "USER", 'UNKNOWN_ENUM_VALUE'.
            Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.
        :type mount_scope_entity_type: str

        :param mount_scope_database_key:
            The value to assign to the mount_scope_database_key property of this MountSpecification.
        :type mount_scope_database_key: str

        :param mount_scope_schema_key:
            The value to assign to the mount_scope_schema_key property of this MountSpecification.
        :type mount_scope_schema_key: str

        :param mount_scope_table_key:
            The value to assign to the mount_scope_table_key property of this MountSpecification.
        :type mount_scope_table_key: str

        :param mount_scope_user_id:
            The value to assign to the mount_scope_user_id property of this MountSpecification.
        :type mount_scope_user_id: str

        :param oci_fs_uri:
            The value to assign to the oci_fs_uri property of this MountSpecification.
        :type oci_fs_uri: str

        """
        self.swagger_types = {
            "obj_store_location": "str",
            "file_path": "str",
            "namespace": "str",
            "bucket_name": "str",
            "mount_scope_entity_type": "str",
            "mount_scope_database_key": "str",
            "mount_scope_schema_key": "str",
            "mount_scope_table_key": "str",
            "mount_scope_user_id": "str",
            "oci_fs_uri": "str",
        }

        self.attribute_map = {
            "obj_store_location": "objStoreLocation",
            "file_path": "filePath",
            "namespace": "namespace",
            "bucket_name": "bucketName",
            "mount_scope_entity_type": "mountScopeEntityType",
            "mount_scope_database_key": "mountScopeDatabaseKey",
            "mount_scope_schema_key": "mountScopeSchemaKey",
            "mount_scope_table_key": "mountScopeTableKey",
            "mount_scope_user_id": "mountScopeUserId",
            "oci_fs_uri": "ociFsUri",
        }

        self._obj_store_location = None
        self._file_path = None
        self._namespace = None
        self._bucket_name = None
        self._mount_scope_entity_type = None
        self._mount_scope_database_key = None
        self._mount_scope_schema_key = None
        self._mount_scope_table_key = None
        self._mount_scope_user_id = None
        self._oci_fs_uri = None

    @property
    def obj_store_location(self):
        """
        Gets the obj_store_location of this MountSpecification.
        path for the Object Storage Path.


        :return: The obj_store_location of this MountSpecification.
        :rtype: str
        """
        return self._obj_store_location

    @obj_store_location.setter
    def obj_store_location(self, obj_store_location):
        """
        Sets the obj_store_location of this MountSpecification.
        path for the Object Storage Path.


        :param obj_store_location: The obj_store_location of this MountSpecification.
        :type: str
        """
        self._obj_store_location = obj_store_location

    @property
    def file_path(self):
        """
        Gets the file_path of this MountSpecification.
        path to the File relative to the bucket.


        :return: The file_path of this MountSpecification.
        :rtype: str
        """
        return self._file_path

    @file_path.setter
    def file_path(self, file_path):
        """
        Sets the file_path of this MountSpecification.
        path to the File relative to the bucket.


        :param file_path: The file_path of this MountSpecification.
        :type: str
        """
        self._file_path = file_path

    @property
    def namespace(self):
        """
        Gets the namespace of this MountSpecification.
        Namespace where to create the new External Mount.


        :return: The namespace of this MountSpecification.
        :rtype: str
        """
        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        """
        Sets the namespace of this MountSpecification.
        Namespace where to create the new External Mount.


        :param namespace: The namespace of this MountSpecification.
        :type: str
        """
        self._namespace = namespace

    @property
    def bucket_name(self):
        """
        Gets the bucket_name of this MountSpecification.
        Bucket to be used to create new External Mount.


        :return: The bucket_name of this MountSpecification.
        :rtype: str
        """
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, bucket_name):
        """
        Sets the bucket_name of this MountSpecification.
        Bucket to be used to create new External Mount.


        :param bucket_name: The bucket_name of this MountSpecification.
        :type: str
        """
        self._bucket_name = bucket_name

    @property
    def mount_scope_entity_type(self):
        """
        Gets the mount_scope_entity_type of this MountSpecification.
        Scope of the new Managed Mount.

        Allowed values for this property are: "DATABASE", "TABLE", "USER", 'UNKNOWN_ENUM_VALUE'.
        Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.


        :return: The mount_scope_entity_type of this MountSpecification.
        :rtype: str
        """
        return self._mount_scope_entity_type

    @mount_scope_entity_type.setter
    def mount_scope_entity_type(self, mount_scope_entity_type):
        """
        Sets the mount_scope_entity_type of this MountSpecification.
        Scope of the new Managed Mount.


        :param mount_scope_entity_type: The mount_scope_entity_type of this MountSpecification.
        :type: str
        """
        allowed_values = ["DATABASE", "TABLE", "USER"]
        if not value_allowed_none_or_none_sentinel(
            mount_scope_entity_type, allowed_values
        ):
            mount_scope_entity_type = "UNKNOWN_ENUM_VALUE"
        self._mount_scope_entity_type = mount_scope_entity_type

    @property
    def mount_scope_database_key(self):
        """
        Gets the mount_scope_database_key of this MountSpecification.
        Name of the entity as per the Scope selected.


        :return: The mount_scope_database_key of this MountSpecification.
        :rtype: str
        """
        return self._mount_scope_database_key

    @mount_scope_database_key.setter
    def mount_scope_database_key(self, mount_scope_database_key):
        """
        Sets the mount_scope_database_key of this MountSpecification.
        Name of the entity as per the Scope selected.


        :param mount_scope_database_key: The mount_scope_database_key of this MountSpecification.
        :type: str
        """
        self._mount_scope_database_key = mount_scope_database_key

    @property
    def mount_scope_schema_key(self):
        """
        Gets the mount_scope_schema_key of this MountSpecification.
        Name of the entity as per the Scope selected.


        :return: The mount_scope_schema_key of this MountSpecification.
        :rtype: str
        """
        return self._mount_scope_schema_key

    @mount_scope_schema_key.setter
    def mount_scope_schema_key(self, mount_scope_schema_key):
        """
        Sets the mount_scope_schema_key of this MountSpecification.
        Name of the entity as per the Scope selected.


        :param mount_scope_schema_key: The mount_scope_schema_key of this MountSpecification.
        :type: str
        """
        self._mount_scope_schema_key = mount_scope_schema_key

    @property
    def mount_scope_table_key(self):
        """
        Gets the mount_scope_table_key of this MountSpecification.
        Name of the entity as per the Scope selected.


        :return: The mount_scope_table_key of this MountSpecification.
        :rtype: str
        """
        return self._mount_scope_table_key

    @mount_scope_table_key.setter
    def mount_scope_table_key(self, mount_scope_table_key):
        """
        Sets the mount_scope_table_key of this MountSpecification.
        Name of the entity as per the Scope selected.


        :param mount_scope_table_key: The mount_scope_table_key of this MountSpecification.
        :type: str
        """
        self._mount_scope_table_key = mount_scope_table_key

    @property
    def mount_scope_user_id(self):
        """
        Gets the mount_scope_user_id of this MountSpecification.
        Name of the entity as per the Scope selected.


        :return: The mount_scope_user_id of this MountSpecification.
        :rtype: str
        """
        return self._mount_scope_user_id

    @mount_scope_user_id.setter
    def mount_scope_user_id(self, mount_scope_user_id):
        """
        Sets the mount_scope_user_id of this MountSpecification.
        Name of the entity as per the Scope selected.


        :param mount_scope_user_id: The mount_scope_user_id of this MountSpecification.
        :type: str
        """
        self._mount_scope_user_id = mount_scope_user_id

    @property
    def oci_fs_uri(self):
        """
        Gets the oci_fs_uri of this MountSpecification.
        OCI FS URI which is used as URI for OCI FS (Python)


        :return: The oci_fs_uri of this MountSpecification.
        :rtype: str
        """
        return self._oci_fs_uri

    @oci_fs_uri.setter
    def oci_fs_uri(self, oci_fs_uri):
        """
        Sets the oci_fs_uri of this MountSpecification.
        OCI FS URI which is used as URI for OCI FS (Python)


        :param oci_fs_uri: The oci_fs_uri of this MountSpecification.
        :type: str
        """
        self._oci_fs_uri = oci_fs_uri

    def __repr__(self):
        return formatted_flat_dict(self)

    def __eq__(self, other):
        if other is None:
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
