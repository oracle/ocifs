# coding: utf-8
# Copyright (c) 2016, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.


from oci.util import formatted_flat_dict, NONE_SENTINEL, value_allowed_none_or_none_sentinel  # noqa: F401
from oci.decorators import init_model_state_from_kwargs


@init_model_state_from_kwargs
class LakeMount(object):
    """
    A Mount under the given lake.
    """

    #: A constant which can be used with the lifecycle_state property of a LakeMount.
    #: This constant has a value of "ACTIVE"
    LIFECYCLE_STATE_ACTIVE = "ACTIVE"

    def __init__(self, **kwargs):
        """
        Initializes a new LakeMount object with values from keyword arguments.
        The following keyword arguments are supported (corresponding to the getters/setters of this class):

        :param key:
            The value to assign to the key property of this LakeMount.
        :type key: str

        :param display_name:
            The value to assign to the display_name property of this LakeMount.
        :type display_name: str

        :param is_operation_pending:
            The value to assign to the is_operation_pending property of this LakeMount.
        :type is_operation_pending: bool

        :param mount_type:
            The value to assign to the mount_type property of this LakeMount.
        :type mount_type: str

        :param storage_type:
            The value to assign to the storage_type property of this LakeMount.
        :type storage_type: str

        :param access_type:
            The value to assign to the access_type property of this LakeMount.
        :type access_type: str

        :param mount_spec:
            The value to assign to the mount_spec property of this LakeMount.
        :type mount_spec: oci.lakehouse.models.MountSpecification

        :param credentials:
            The value to assign to the credentials property of this LakeMount.
        :type credentials: str

        :param encryption:
            The value to assign to the encryption property of this LakeMount.
        :type encryption: str

        :param mount_options:
            The value to assign to the mount_options property of this LakeMount.
        :type mount_options: str

        :param permissions:
            The value to assign to the permissions property of this LakeMount.
        :type permissions: list[oci.lakehouse.models.PermissionLine]

        :param time_created:
            The value to assign to the time_created property of this LakeMount.
        :type time_created: datetime

        :param time_updated:
            The value to assign to the time_updated property of this LakeMount.
        :type time_updated: datetime

        :param created_by:
            The value to assign to the created_by property of this LakeMount.
        :type created_by: str

        :param is_assigned:
            The value to assign to the is_assigned property of this LakeMount.
        :type is_assigned: bool

        :param lifecycle_state:
            The value to assign to the lifecycle_state property of this LakeMount.
            Allowed values for this property are: "ACTIVE", 'UNKNOWN_ENUM_VALUE'.
            Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.
        :type lifecycle_state: str

        :param lifecycle_details:
            The value to assign to the lifecycle_details property of this LakeMount.
        :type lifecycle_details: str

        :param description:
            The value to assign to the description property of this LakeMount.
        :type description: str

        :param lake_id:
            The value to assign to the lake_id property of this LakeMount.
        :type lake_id: str

        :param compartment_id:
            The value to assign to the compartment_id property of this LakeMount.
        :type compartment_id: str

        :param freeform_tags:
            The value to assign to the freeform_tags property of this LakeMount.
        :type freeform_tags: dict(str, str)

        :param defined_tags:
            The value to assign to the defined_tags property of this LakeMount.
        :type defined_tags: dict(str, dict(str, object))

        :param system_tags:
            The value to assign to the system_tags property of this LakeMount.
        :type system_tags: dict(str, dict(str, object))

        """
        self.swagger_types = {
            'key': 'str',
            'display_name': 'str',
            'is_operation_pending': 'bool',
            'mount_type': 'str',
            'storage_type': 'str',
            'access_type': 'str',
            'mount_spec': 'MountSpecification',
            'credentials': 'str',
            'encryption': 'str',
            'mount_options': 'str',
            'permissions': 'list[PermissionLine]',
            'time_created': 'datetime',
            'time_updated': 'datetime',
            'created_by': 'str',
            'is_assigned': 'bool',
            'lifecycle_state': 'str',
            'lifecycle_details': 'str',
            'description': 'str',
            'lake_id': 'str',
            'compartment_id': 'str',
            'freeform_tags': 'dict(str, str)',
            'defined_tags': 'dict(str, dict(str, object))',
            'system_tags': 'dict(str, dict(str, object))'
        }

        self.attribute_map = {
            'key': 'key',
            'display_name': 'displayName',
            'is_operation_pending': 'isOperationPending',
            'mount_type': 'mountType',
            'storage_type': 'storageType',
            'access_type': 'accessType',
            'mount_spec': 'mountSpec',
            'credentials': 'credentials',
            'encryption': 'encryption',
            'mount_options': 'mountOptions',
            'permissions': 'permissions',
            'time_created': 'timeCreated',
            'time_updated': 'timeUpdated',
            'created_by': 'createdBy',
            'is_assigned': 'isAssigned',
            'lifecycle_state': 'lifecycleState',
            'lifecycle_details': 'lifecycleDetails',
            'description': 'description',
            'lake_id': 'lakeId',
            'compartment_id': 'compartmentId',
            'freeform_tags': 'freeformTags',
            'defined_tags': 'definedTags',
            'system_tags': 'systemTags'
        }

        self._key = None
        self._display_name = None
        self._is_operation_pending = None
        self._mount_type = None
        self._storage_type = None
        self._access_type = None
        self._mount_spec = None
        self._credentials = None
        self._encryption = None
        self._mount_options = None
        self._permissions = None
        self._time_created = None
        self._time_updated = None
        self._created_by = None
        self._is_assigned = None
        self._lifecycle_state = None
        self._lifecycle_details = None
        self._description = None
        self._lake_id = None
        self._compartment_id = None
        self._freeform_tags = None
        self._defined_tags = None
        self._system_tags = None

    @property
    def key(self):
        """
        **[Required]** Gets the key of this LakeMount.
        A unique key for the Mount, that is immutable on creation.


        :return: The key of this LakeMount.
        :rtype: str
        """
        return self._key

    @key.setter
    def key(self, key):
        """
        Sets the key of this LakeMount.
        A unique key for the Mount, that is immutable on creation.


        :param key: The key of this LakeMount.
        :type: str
        """
        self._key = key

    @property
    def display_name(self):
        """
        **[Required]** Gets the display_name of this LakeMount.
        The Mount name. It can't be changed.


        :return: The display_name of this LakeMount.
        :rtype: str
        """
        return self._display_name

    @display_name.setter
    def display_name(self, display_name):
        """
        Sets the display_name of this LakeMount.
        The Mount name. It can't be changed.


        :param display_name: The display_name of this LakeMount.
        :type: str
        """
        self._display_name = display_name

    @property
    def is_operation_pending(self):
        """
        Gets the is_operation_pending of this LakeMount.
        Identifies if there is a ongoing operation on the mount.


        :return: The is_operation_pending of this LakeMount.
        :rtype: bool
        """
        return self._is_operation_pending

    @is_operation_pending.setter
    def is_operation_pending(self, is_operation_pending):
        """
        Sets the is_operation_pending of this LakeMount.
        Identifies if there is a ongoing operation on the mount.


        :param is_operation_pending: The is_operation_pending of this LakeMount.
        :type: bool
        """
        self._is_operation_pending = is_operation_pending

    @property
    def mount_type(self):
        """
        Gets the mount_type of this LakeMount.
        Type of the Mount.


        :return: The mount_type of this LakeMount.
        :rtype: str
        """
        return self._mount_type

    @mount_type.setter
    def mount_type(self, mount_type):
        """
        Sets the mount_type of this LakeMount.
        Type of the Mount.


        :param mount_type: The mount_type of this LakeMount.
        :type: str
        """
        self._mount_type = mount_type

    @property
    def storage_type(self):
        """
        Gets the storage_type of this LakeMount.
        Type of the Storage being used by the Mount.


        :return: The storage_type of this LakeMount.
        :rtype: str
        """
        return self._storage_type

    @storage_type.setter
    def storage_type(self, storage_type):
        """
        Sets the storage_type of this LakeMount.
        Type of the Storage being used by the Mount.


        :param storage_type: The storage_type of this LakeMount.
        :type: str
        """
        self._storage_type = storage_type

    @property
    def access_type(self):
        """
        Gets the access_type of this LakeMount.
        Access Type of the Mount.


        :return: The access_type of this LakeMount.
        :rtype: str
        """
        return self._access_type

    @access_type.setter
    def access_type(self, access_type):
        """
        Sets the access_type of this LakeMount.
        Access Type of the Mount.


        :param access_type: The access_type of this LakeMount.
        :type: str
        """
        self._access_type = access_type

    @property
    def mount_spec(self):
        """
        Gets the mount_spec of this LakeMount.

        :return: The mount_spec of this LakeMount.
        :rtype: oci.lakehouse.models.MountSpecification
        """
        return self._mount_spec

    @mount_spec.setter
    def mount_spec(self, mount_spec):
        """
        Sets the mount_spec of this LakeMount.

        :param mount_spec: The mount_spec of this LakeMount.
        :type: oci.lakehouse.models.MountSpecification
        """
        self._mount_spec = mount_spec

    @property
    def credentials(self):
        """
        Gets the credentials of this LakeMount.
        Credential for the Mount.


        :return: The credentials of this LakeMount.
        :rtype: str
        """
        return self._credentials

    @credentials.setter
    def credentials(self, credentials):
        """
        Sets the credentials of this LakeMount.
        Credential for the Mount.


        :param credentials: The credentials of this LakeMount.
        :type: str
        """
        self._credentials = credentials

    @property
    def encryption(self):
        """
        Gets the encryption of this LakeMount.
        Encryption for the Mount.


        :return: The encryption of this LakeMount.
        :rtype: str
        """
        return self._encryption

    @encryption.setter
    def encryption(self, encryption):
        """
        Sets the encryption of this LakeMount.
        Encryption for the Mount.


        :param encryption: The encryption of this LakeMount.
        :type: str
        """
        self._encryption = encryption

    @property
    def mount_options(self):
        """
        Gets the mount_options of this LakeMount.
        Additional Options for the Mount.


        :return: The mount_options of this LakeMount.
        :rtype: str
        """
        return self._mount_options

    @mount_options.setter
    def mount_options(self, mount_options):
        """
        Sets the mount_options of this LakeMount.
        Additional Options for the Mount.


        :param mount_options: The mount_options of this LakeMount.
        :type: str
        """
        self._mount_options = mount_options

    @property
    def permissions(self):
        """
        Gets the permissions of this LakeMount.
        The permissions in the Mount.


        :return: The permissions of this LakeMount.
        :rtype: list[oci.lakehouse.models.PermissionLine]
        """
        return self._permissions

    @permissions.setter
    def permissions(self, permissions):
        """
        Sets the permissions of this LakeMount.
        The permissions in the Mount.


        :param permissions: The permissions of this LakeMount.
        :type: list[oci.lakehouse.models.PermissionLine]
        """
        self._permissions = permissions

    @property
    def time_created(self):
        """
        Gets the time_created of this LakeMount.
        The time the Mount was created. An RFC3339 formatted datetime string.


        :return: The time_created of this LakeMount.
        :rtype: datetime
        """
        return self._time_created

    @time_created.setter
    def time_created(self, time_created):
        """
        Sets the time_created of this LakeMount.
        The time the Mount was created. An RFC3339 formatted datetime string.


        :param time_created: The time_created of this LakeMount.
        :type: datetime
        """
        self._time_created = time_created

    @property
    def time_updated(self):
        """
        Gets the time_updated of this LakeMount.
        The time the Mount was updated. An RFC3339 formatted datetime string.


        :return: The time_updated of this LakeMount.
        :rtype: datetime
        """
        return self._time_updated

    @time_updated.setter
    def time_updated(self, time_updated):
        """
        Sets the time_updated of this LakeMount.
        The time the Mount was updated. An RFC3339 formatted datetime string.


        :param time_updated: The time_updated of this LakeMount.
        :type: datetime
        """
        self._time_updated = time_updated

    @property
    def created_by(self):
        """
        Gets the created_by of this LakeMount.
        OCID of the Principal who created the Mount.


        :return: The created_by of this LakeMount.
        :rtype: str
        """
        return self._created_by

    @created_by.setter
    def created_by(self, created_by):
        """
        Sets the created_by of this LakeMount.
        OCID of the Principal who created the Mount.


        :param created_by: The created_by of this LakeMount.
        :type: str
        """
        self._created_by = created_by

    @property
    def is_assigned(self):
        """
        Gets the is_assigned of this LakeMount.
        The Mount is assigned to the current user or a group that the user is part of.


        :return: The is_assigned of this LakeMount.
        :rtype: bool
        """
        return self._is_assigned

    @is_assigned.setter
    def is_assigned(self, is_assigned):
        """
        Sets the is_assigned of this LakeMount.
        The Mount is assigned to the current user or a group that the user is part of.


        :param is_assigned: The is_assigned of this LakeMount.
        :type: bool
        """
        self._is_assigned = is_assigned

    @property
    def lifecycle_state(self):
        """
        Gets the lifecycle_state of this LakeMount.
        The state of the Lake Mount.

        Allowed values for this property are: "ACTIVE", 'UNKNOWN_ENUM_VALUE'.
        Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.


        :return: The lifecycle_state of this LakeMount.
        :rtype: str
        """
        return self._lifecycle_state

    @lifecycle_state.setter
    def lifecycle_state(self, lifecycle_state):
        """
        Sets the lifecycle_state of this LakeMount.
        The state of the Lake Mount.


        :param lifecycle_state: The lifecycle_state of this LakeMount.
        :type: str
        """
        allowed_values = ["ACTIVE"]
        if not value_allowed_none_or_none_sentinel(lifecycle_state, allowed_values):
            lifecycle_state = 'UNKNOWN_ENUM_VALUE'
        self._lifecycle_state = lifecycle_state

    @property
    def lifecycle_details(self):
        """
        Gets the lifecycle_details of this LakeMount.
        A message describing the current state in more detail. For example, it can be used to provide actionable information for a resource in Failed state.


        :return: The lifecycle_details of this LakeMount.
        :rtype: str
        """
        return self._lifecycle_details

    @lifecycle_details.setter
    def lifecycle_details(self, lifecycle_details):
        """
        Sets the lifecycle_details of this LakeMount.
        A message describing the current state in more detail. For example, it can be used to provide actionable information for a resource in Failed state.


        :param lifecycle_details: The lifecycle_details of this LakeMount.
        :type: str
        """
        self._lifecycle_details = lifecycle_details

    @property
    def description(self):
        """
        Gets the description of this LakeMount.
        The description of the Mount.


        :return: The description of this LakeMount.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """
        Sets the description of this LakeMount.
        The description of the Mount.


        :param description: The description of this LakeMount.
        :type: str
        """
        self._description = description

    @property
    def lake_id(self):
        """
        Gets the lake_id of this LakeMount.
        The Lake wherein the Mount resides.


        :return: The lake_id of this LakeMount.
        :rtype: str
        """
        return self._lake_id

    @lake_id.setter
    def lake_id(self, lake_id):
        """
        Sets the lake_id of this LakeMount.
        The Lake wherein the Mount resides.


        :param lake_id: The lake_id of this LakeMount.
        :type: str
        """
        self._lake_id = lake_id

    @property
    def compartment_id(self):
        """
        Gets the compartment_id of this LakeMount.
        The compartment id.


        :return: The compartment_id of this LakeMount.
        :rtype: str
        """
        return self._compartment_id

    @compartment_id.setter
    def compartment_id(self, compartment_id):
        """
        Sets the compartment_id of this LakeMount.
        The compartment id.


        :param compartment_id: The compartment_id of this LakeMount.
        :type: str
        """
        self._compartment_id = compartment_id

    @property
    def freeform_tags(self):
        """
        Gets the freeform_tags of this LakeMount.
        Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.
        Example: `{\"bar-key\": \"value\"}`


        :return: The freeform_tags of this LakeMount.
        :rtype: dict(str, str)
        """
        return self._freeform_tags

    @freeform_tags.setter
    def freeform_tags(self, freeform_tags):
        """
        Sets the freeform_tags of this LakeMount.
        Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.
        Example: `{\"bar-key\": \"value\"}`


        :param freeform_tags: The freeform_tags of this LakeMount.
        :type: dict(str, str)
        """
        self._freeform_tags = freeform_tags

    @property
    def defined_tags(self):
        """
        Gets the defined_tags of this LakeMount.
        Defined tags for this resource. Each key is predefined and scoped to a namespace.
        Example: `{\"foo-namespace\": {\"bar-key\": \"value\"}}`


        :return: The defined_tags of this LakeMount.
        :rtype: dict(str, dict(str, object))
        """
        return self._defined_tags

    @defined_tags.setter
    def defined_tags(self, defined_tags):
        """
        Sets the defined_tags of this LakeMount.
        Defined tags for this resource. Each key is predefined and scoped to a namespace.
        Example: `{\"foo-namespace\": {\"bar-key\": \"value\"}}`


        :param defined_tags: The defined_tags of this LakeMount.
        :type: dict(str, dict(str, object))
        """
        self._defined_tags = defined_tags

    @property
    def system_tags(self):
        """
        Gets the system_tags of this LakeMount.
        Usage of system tag keys. These predefined keys are scoped to namespaces.
        Example: `{\"orcl-cloud\": {\"free-tier-retained\": \"true\"}}`


        :return: The system_tags of this LakeMount.
        :rtype: dict(str, dict(str, object))
        """
        return self._system_tags

    @system_tags.setter
    def system_tags(self, system_tags):
        """
        Sets the system_tags of this LakeMount.
        Usage of system tag keys. These predefined keys are scoped to namespaces.
        Example: `{\"orcl-cloud\": {\"free-tier-retained\": \"true\"}}`


        :param system_tags: The system_tags of this LakeMount.
        :type: dict(str, dict(str, object))
        """
        self._system_tags = system_tags

    def __repr__(self):
        return formatted_flat_dict(self)

    def __eq__(self, other):
        if other is None:
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
