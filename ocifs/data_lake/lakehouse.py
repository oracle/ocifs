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
class Lakehouse(object):
    """
    Description of Lakehouse.
    """

    #: A constant which can be used with the lifecycle_state property of a Lakehouse.
    #: This constant has a value of "CREATING"
    LIFECYCLE_STATE_CREATING = "CREATING"

    #: A constant which can be used with the lifecycle_state property of a Lakehouse.
    #: This constant has a value of "UPDATING"
    LIFECYCLE_STATE_UPDATING = "UPDATING"

    #: A constant which can be used with the lifecycle_state property of a Lakehouse.
    #: This constant has a value of "ACTIVE"
    LIFECYCLE_STATE_ACTIVE = "ACTIVE"

    #: A constant which can be used with the lifecycle_state property of a Lakehouse.
    #: This constant has a value of "DELETING"
    LIFECYCLE_STATE_DELETING = "DELETING"

    #: A constant which can be used with the lifecycle_state property of a Lakehouse.
    #: This constant has a value of "DELETED"
    LIFECYCLE_STATE_DELETED = "DELETED"

    #: A constant which can be used with the lifecycle_state property of a Lakehouse.
    #: This constant has a value of "FAILED"
    LIFECYCLE_STATE_FAILED = "FAILED"

    def __init__(self, **kwargs):
        """
        Initializes a new Lakehouse object with values from keyword arguments.
        The following keyword arguments are supported (corresponding to the getters/setters of this class):

        :param id:
            The value to assign to the id property of this Lakehouse.
        :type id: str

        :param display_name:
            The value to assign to the display_name property of this Lakehouse.
        :type display_name: str

        :param lakeshare_endpoint:
            The value to assign to the lakeshare_endpoint property of this Lakehouse.
        :type lakeshare_endpoint: str

        :param lakeproxy_endpoint:
            The value to assign to the lakeproxy_endpoint property of this Lakehouse.
        :type lakeproxy_endpoint: str

        :param compartment_id:
            The value to assign to the compartment_id property of this Lakehouse.
        :type compartment_id: str

        :param time_created:
            The value to assign to the time_created property of this Lakehouse.
        :type time_created: datetime

        :param time_updated:
            The value to assign to the time_updated property of this Lakehouse.
        :type time_updated: datetime

        :param lifecycle_state:
            The value to assign to the lifecycle_state property of this Lakehouse.
            Allowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", 'UNKNOWN_ENUM_VALUE'.
            Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.
        :type lifecycle_state: str

        :param lifecycle_details:
            The value to assign to the lifecycle_details property of this Lakehouse.
        :type lifecycle_details: str

        :param metastore_id:
            The value to assign to the metastore_id property of this Lakehouse.
        :type metastore_id: str

        :param dis_work_space_details:
            The value to assign to the dis_work_space_details property of this Lakehouse.
        :type dis_work_space_details: oci.lakehouse.models.DisWorkSpaceDetails

        :param catalog_details:
            The value to assign to the catalog_details property of this Lakehouse.
        :type catalog_details: oci.lakehouse.models.CatalogDetails

        :param managed_bucket_uri:
            The value to assign to the managed_bucket_uri property of this Lakehouse.
        :type managed_bucket_uri: str

        :param policy_ids:
            The value to assign to the policy_ids property of this Lakehouse.
        :type policy_ids: list[str]

        :param freeform_tags:
            The value to assign to the freeform_tags property of this Lakehouse.
        :type freeform_tags: dict(str, str)

        :param defined_tags:
            The value to assign to the defined_tags property of this Lakehouse.
        :type defined_tags: dict(str, dict(str, object))

        :param system_tags:
            The value to assign to the system_tags property of this Lakehouse.
        :type system_tags: dict(str, dict(str, object))

        """
        self.swagger_types = {
            "id": "str",
            "display_name": "str",
            "lakeshare_endpoint": "str",
            "lakeproxy_endpoint": "str",
            "compartment_id": "str",
            "time_created": "datetime",
            "time_updated": "datetime",
            "lifecycle_state": "str",
            "lifecycle_details": "str",
            "metastore_id": "str",
            "dis_work_space_details": "DisWorkSpaceDetails",
            "catalog_details": "CatalogDetails",
            "managed_bucket_uri": "str",
            "policy_ids": "list[str]",
            "freeform_tags": "dict(str, str)",
            "defined_tags": "dict(str, dict(str, object))",
            "system_tags": "dict(str, dict(str, object))",
        }

        self.attribute_map = {
            "id": "id",
            "display_name": "displayName",
            "lakeshare_endpoint": "lakeshareEndpoint",
            "lakeproxy_endpoint": "lakeproxyEndpoint",
            "compartment_id": "compartmentId",
            "time_created": "timeCreated",
            "time_updated": "timeUpdated",
            "lifecycle_state": "lifecycleState",
            "lifecycle_details": "lifecycleDetails",
            "metastore_id": "metastoreId",
            "dis_work_space_details": "disWorkSpaceDetails",
            "catalog_details": "catalogDetails",
            "managed_bucket_uri": "managedBucketUri",
            "policy_ids": "policyIds",
            "freeform_tags": "freeformTags",
            "defined_tags": "definedTags",
            "system_tags": "systemTags",
        }

        self._id = None
        self._display_name = None
        self._lakeshare_endpoint = None
        self._lakeproxy_endpoint = None
        self._compartment_id = None
        self._time_created = None
        self._time_updated = None
        self._lifecycle_state = None
        self._lifecycle_details = None
        self._metastore_id = None
        self._dis_work_space_details = None
        self._catalog_details = None
        self._managed_bucket_uri = None
        self._policy_ids = None
        self._freeform_tags = None
        self._defined_tags = None
        self._system_tags = None

    @property
    def id(self):
        """
        **[Required]** Gets the id of this Lakehouse.
        Unique identifier that is immutable on creation


        :return: The id of this Lakehouse.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """
        Sets the id of this Lakehouse.
        Unique identifier that is immutable on creation


        :param id: The id of this Lakehouse.
        :type: str
        """
        self._id = id

    @property
    def display_name(self):
        """
        **[Required]** Gets the display_name of this Lakehouse.
        Lakehouse Identifier, can be renamed


        :return: The display_name of this Lakehouse.
        :rtype: str
        """
        return self._display_name

    @display_name.setter
    def display_name(self, display_name):
        """
        Sets the display_name of this Lakehouse.
        Lakehouse Identifier, can be renamed


        :param display_name: The display_name of this Lakehouse.
        :type: str
        """
        self._display_name = display_name

    @property
    def lakeshare_endpoint(self):
        """
        Gets the lakeshare_endpoint of this Lakehouse.
        Lakeshare access endpoint


        :return: The lakeshare_endpoint of this Lakehouse.
        :rtype: str
        """
        return self._lakeshare_endpoint

    @lakeshare_endpoint.setter
    def lakeshare_endpoint(self, lakeshare_endpoint):
        """
        Sets the lakeshare_endpoint of this Lakehouse.
        Lakeshare access endpoint


        :param lakeshare_endpoint: The lakeshare_endpoint of this Lakehouse.
        :type: str
        """
        self._lakeshare_endpoint = lakeshare_endpoint

    @property
    def lakeproxy_endpoint(self):
        """
        Gets the lakeproxy_endpoint of this Lakehouse.
        Lakeproxy access endpoint


        :return: The lakeproxy_endpoint of this Lakehouse.
        :rtype: str
        """
        return self._lakeproxy_endpoint

    @lakeproxy_endpoint.setter
    def lakeproxy_endpoint(self, lakeproxy_endpoint):
        """
        Sets the lakeproxy_endpoint of this Lakehouse.
        Lakeproxy access endpoint


        :param lakeproxy_endpoint: The lakeproxy_endpoint of this Lakehouse.
        :type: str
        """
        self._lakeproxy_endpoint = lakeproxy_endpoint

    @property
    def compartment_id(self):
        """
        **[Required]** Gets the compartment_id of this Lakehouse.
        Compartment Identifier


        :return: The compartment_id of this Lakehouse.
        :rtype: str
        """
        return self._compartment_id

    @compartment_id.setter
    def compartment_id(self, compartment_id):
        """
        Sets the compartment_id of this Lakehouse.
        Compartment Identifier


        :param compartment_id: The compartment_id of this Lakehouse.
        :type: str
        """
        self._compartment_id = compartment_id

    @property
    def time_created(self):
        """
        **[Required]** Gets the time_created of this Lakehouse.
        The time the the Lakehouse was created. An RFC3339 formatted datetime string


        :return: The time_created of this Lakehouse.
        :rtype: datetime
        """
        return self._time_created

    @time_created.setter
    def time_created(self, time_created):
        """
        Sets the time_created of this Lakehouse.
        The time the the Lakehouse was created. An RFC3339 formatted datetime string


        :param time_created: The time_created of this Lakehouse.
        :type: datetime
        """
        self._time_created = time_created

    @property
    def time_updated(self):
        """
        Gets the time_updated of this Lakehouse.
        The time the Lakehouse was updated. An RFC3339 formatted datetime string


        :return: The time_updated of this Lakehouse.
        :rtype: datetime
        """
        return self._time_updated

    @time_updated.setter
    def time_updated(self, time_updated):
        """
        Sets the time_updated of this Lakehouse.
        The time the Lakehouse was updated. An RFC3339 formatted datetime string


        :param time_updated: The time_updated of this Lakehouse.
        :type: datetime
        """
        self._time_updated = time_updated

    @property
    def lifecycle_state(self):
        """
        **[Required]** Gets the lifecycle_state of this Lakehouse.
        The current state of the Lakehouse.

        Allowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", 'UNKNOWN_ENUM_VALUE'.
        Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.


        :return: The lifecycle_state of this Lakehouse.
        :rtype: str
        """
        return self._lifecycle_state

    @lifecycle_state.setter
    def lifecycle_state(self, lifecycle_state):
        """
        Sets the lifecycle_state of this Lakehouse.
        The current state of the Lakehouse.


        :param lifecycle_state: The lifecycle_state of this Lakehouse.
        :type: str
        """
        allowed_values = [
            "CREATING",
            "UPDATING",
            "ACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
        ]
        if not value_allowed_none_or_none_sentinel(lifecycle_state, allowed_values):
            lifecycle_state = "UNKNOWN_ENUM_VALUE"
        self._lifecycle_state = lifecycle_state

    @property
    def lifecycle_details(self):
        """
        Gets the lifecycle_details of this Lakehouse.
        A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.


        :return: The lifecycle_details of this Lakehouse.
        :rtype: str
        """
        return self._lifecycle_details

    @lifecycle_details.setter
    def lifecycle_details(self, lifecycle_details):
        """
        Sets the lifecycle_details of this Lakehouse.
        A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.


        :param lifecycle_details: The lifecycle_details of this Lakehouse.
        :type: str
        """
        self._lifecycle_details = lifecycle_details

    @property
    def metastore_id(self):
        """
        **[Required]** Gets the metastore_id of this Lakehouse.
        Metastore OCID


        :return: The metastore_id of this Lakehouse.
        :rtype: str
        """
        return self._metastore_id

    @metastore_id.setter
    def metastore_id(self, metastore_id):
        """
        Sets the metastore_id of this Lakehouse.
        Metastore OCID


        :param metastore_id: The metastore_id of this Lakehouse.
        :type: str
        """
        self._metastore_id = metastore_id

    @property
    def dis_work_space_details(self):
        """
        **[Required]** Gets the dis_work_space_details of this Lakehouse.

        :return: The dis_work_space_details of this Lakehouse.
        :rtype: oci.lakehouse.models.DisWorkSpaceDetails
        """
        return self._dis_work_space_details

    @dis_work_space_details.setter
    def dis_work_space_details(self, dis_work_space_details):
        """
        Sets the dis_work_space_details of this Lakehouse.

        :param dis_work_space_details: The dis_work_space_details of this Lakehouse.
        :type: oci.lakehouse.models.DisWorkSpaceDetails
        """
        self._dis_work_space_details = dis_work_space_details

    @property
    def catalog_details(self):
        """
        **[Required]** Gets the catalog_details of this Lakehouse.

        :return: The catalog_details of this Lakehouse.
        :rtype: oci.lakehouse.models.CatalogDetails
        """
        return self._catalog_details

    @catalog_details.setter
    def catalog_details(self, catalog_details):
        """
        Sets the catalog_details of this Lakehouse.

        :param catalog_details: The catalog_details of this Lakehouse.
        :type: oci.lakehouse.models.CatalogDetails
        """
        self._catalog_details = catalog_details

    @property
    def managed_bucket_uri(self):
        """
        **[Required]** Gets the managed_bucket_uri of this Lakehouse.
        The warehouse bucket URI. It is a Oracle Cloud Infrastructure Object Storage bucket URI as defined here https://docs.oracle.com/en/cloud/paas/atp-cloud/atpud/object-storage-uris.html


        :return: The managed_bucket_uri of this Lakehouse.
        :rtype: str
        """
        return self._managed_bucket_uri

    @managed_bucket_uri.setter
    def managed_bucket_uri(self, managed_bucket_uri):
        """
        Sets the managed_bucket_uri of this Lakehouse.
        The warehouse bucket URI. It is a Oracle Cloud Infrastructure Object Storage bucket URI as defined here https://docs.oracle.com/en/cloud/paas/atp-cloud/atpud/object-storage-uris.html


        :param managed_bucket_uri: The managed_bucket_uri of this Lakehouse.
        :type: str
        """
        self._managed_bucket_uri = managed_bucket_uri

    @property
    def policy_ids(self):
        """
        **[Required]** Gets the policy_ids of this Lakehouse.
        All policy ids, created by lakehouse in customer tenancy


        :return: The policy_ids of this Lakehouse.
        :rtype: list[str]
        """
        return self._policy_ids

    @policy_ids.setter
    def policy_ids(self, policy_ids):
        """
        Sets the policy_ids of this Lakehouse.
        All policy ids, created by lakehouse in customer tenancy


        :param policy_ids: The policy_ids of this Lakehouse.
        :type: list[str]
        """
        self._policy_ids = policy_ids

    @property
    def freeform_tags(self):
        """
        **[Required]** Gets the freeform_tags of this Lakehouse.
        Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.
        Example: `{\"bar-key\": \"value\"}`


        :return: The freeform_tags of this Lakehouse.
        :rtype: dict(str, str)
        """
        return self._freeform_tags

    @freeform_tags.setter
    def freeform_tags(self, freeform_tags):
        """
        Sets the freeform_tags of this Lakehouse.
        Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.
        Example: `{\"bar-key\": \"value\"}`


        :param freeform_tags: The freeform_tags of this Lakehouse.
        :type: dict(str, str)
        """
        self._freeform_tags = freeform_tags

    @property
    def defined_tags(self):
        """
        **[Required]** Gets the defined_tags of this Lakehouse.
        Defined tags for this resource. Each key is predefined and scoped to a namespace.
        Example: `{\"foo-namespace\": {\"bar-key\": \"value\"}}`


        :return: The defined_tags of this Lakehouse.
        :rtype: dict(str, dict(str, object))
        """
        return self._defined_tags

    @defined_tags.setter
    def defined_tags(self, defined_tags):
        """
        Sets the defined_tags of this Lakehouse.
        Defined tags for this resource. Each key is predefined and scoped to a namespace.
        Example: `{\"foo-namespace\": {\"bar-key\": \"value\"}}`


        :param defined_tags: The defined_tags of this Lakehouse.
        :type: dict(str, dict(str, object))
        """
        self._defined_tags = defined_tags

    @property
    def system_tags(self):
        """
        Gets the system_tags of this Lakehouse.
        Usage of system tag keys. These predefined keys are scoped to namespaces.
        Example: `{\"orcl-cloud\": {\"free-tier-retained\": \"true\"}}`


        :return: The system_tags of this Lakehouse.
        :rtype: dict(str, dict(str, object))
        """
        return self._system_tags

    @system_tags.setter
    def system_tags(self, system_tags):
        """
        Sets the system_tags of this Lakehouse.
        Usage of system tag keys. These predefined keys are scoped to namespaces.
        Example: `{\"orcl-cloud\": {\"free-tier-retained\": \"true\"}}`


        :param system_tags: The system_tags of this Lakehouse.
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
