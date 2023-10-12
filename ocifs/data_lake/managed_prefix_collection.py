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
class ManagedPrefixCollection(object):
    """
    Results of a managedprefix path search for a bucket/namespace. Contains both ManagedPrefixPathSummary items and the fsUri.
    """

    def __init__(self, **kwargs):
        """
        Initializes a new ManagedPrefixCollection object with values from keyword arguments.
        The following keyword arguments are supported (corresponding to the getters/setters of this class):

        :param items:
            The value to assign to the items property of this ManagedPrefixCollection.
        :type items: list[oci.lakesharing.models.ManagedPrefixSummary]

        :param fs_uri:
            The value to assign to the fs_uri property of this ManagedPrefixCollection.
        :type fs_uri: str

        :param service_namespace:
            The value to assign to the service_namespace property of this ManagedPrefixCollection.
        :type service_namespace: str

        :param is_force_fallback_for_managed:
            The value to assign to the is_force_fallback_for_managed property of this ManagedPrefixCollection.
        :type is_force_fallback_for_managed: bool

        """
        self.swagger_types = {
            "items": "list[ManagedPrefixSummary]",
            "fs_uri": "str",
            "service_namespace": "str",
            "is_force_fallback_for_managed": "bool",
        }

        self.attribute_map = {
            "items": "items",
            "fs_uri": "fsUri",
            "service_namespace": "serviceNamespace",
            "is_force_fallback_for_managed": "isForceFallbackForManaged",
        }

        self._items = None
        self._fs_uri = None
        self._service_namespace = None
        self._is_force_fallback_for_managed = None

    @property
    def items(self):
        """
        **[Required]** Gets the items of this ManagedPrefixCollection.
        list of managedprefixes summary


        :return: The items of this ManagedPrefixCollection.
        :rtype: list[oci.lakesharing.models.ManagedPrefixSummary]
        """
        return self._items

    @items.setter
    def items(self, items):
        """
        Sets the items of this ManagedPrefixCollection.
        list of managedprefixes summary


        :param items: The items of this ManagedPrefixCollection.
        :type: list[oci.lakesharing.models.ManagedPrefixSummary]
        """
        self._items = items

    @property
    def fs_uri(self):
        """
        **[Required]** Gets the fs_uri of this ManagedPrefixCollection.
        fs Uri


        :return: The fs_uri of this ManagedPrefixCollection.
        :rtype: str
        """
        return self._fs_uri

    @fs_uri.setter
    def fs_uri(self, fs_uri):
        """
        Sets the fs_uri of this ManagedPrefixCollection.
        fs Uri


        :param fs_uri: The fs_uri of this ManagedPrefixCollection.
        :type: str
        """
        self._fs_uri = fs_uri

    @property
    def service_namespace(self):
        """
        **[Required]** Gets the service_namespace of this ManagedPrefixCollection.
        lakehouse service namespace


        :return: The service_namespace of this ManagedPrefixCollection.
        :rtype: str
        """
        return self._service_namespace

    @service_namespace.setter
    def service_namespace(self, service_namespace):
        """
        Sets the service_namespace of this ManagedPrefixCollection.
        lakehouse service namespace


        :param service_namespace: The service_namespace of this ManagedPrefixCollection.
        :type: str
        """
        self._service_namespace = service_namespace

    @property
    def is_force_fallback_for_managed(self):
        """
        **[Required]** Gets the is_force_fallback_for_managed of this ManagedPrefixCollection.
        If the request is from trusted entity server returns this flag true, otherwise false.


        :return: The is_force_fallback_for_managed of this ManagedPrefixCollection.
        :rtype: bool
        """
        return self._is_force_fallback_for_managed

    @is_force_fallback_for_managed.setter
    def is_force_fallback_for_managed(self, is_force_fallback_for_managed):
        """
        Sets the is_force_fallback_for_managed of this ManagedPrefixCollection.
        If the request is from trusted entity server returns this flag true, otherwise false.


        :param is_force_fallback_for_managed: The is_force_fallback_for_managed of this ManagedPrefixCollection.
        :type: bool
        """
        self._is_force_fallback_for_managed = is_force_fallback_for_managed

    def __repr__(self):
        return formatted_flat_dict(self)

    def __eq__(self, other):
        if other is None:
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
