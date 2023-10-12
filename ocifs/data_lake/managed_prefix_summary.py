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
class ManagedPrefixSummary(object):
    """
    Returns the list of Managed prefix paths for a given bucket/namespace
    """

    def __init__(self, **kwargs):
        """
        Initializes a new ManagedPrefixSummary object with values from keyword arguments.
        The following keyword arguments are supported (corresponding to the getters/setters of this class):

        :param prefix_path:
            The value to assign to the prefix_path property of this ManagedPrefixSummary.
        :type prefix_path: str

        """
        self.swagger_types = {"prefix_path": "str"}

        self.attribute_map = {"prefix_path": "prefixPath"}

        self._prefix_path = None

    @property
    def prefix_path(self):
        """
        **[Required]** Gets the prefix_path of this ManagedPrefixSummary.
        managed prefix path


        :return: The prefix_path of this ManagedPrefixSummary.
        :rtype: str
        """
        return self._prefix_path

    @prefix_path.setter
    def prefix_path(self, prefix_path):
        """
        Sets the prefix_path of this ManagedPrefixSummary.
        managed prefix path


        :param prefix_path: The prefix_path of this ManagedPrefixSummary.
        :type: str
        """
        self._prefix_path = prefix_path

    def __repr__(self):
        return formatted_flat_dict(self)

    def __eq__(self, other):
        if other is None:
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
