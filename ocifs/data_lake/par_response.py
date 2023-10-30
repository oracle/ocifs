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
class ParResponse(object):
    """
    LakeSharing Par Hash
    """

    #: A constant which can be used with the par_type property of a ParResponse.
    #: This constant has a value of "DATABASE"
    PAR_TYPE_DATABASE = "DATABASE"

    #: A constant which can be used with the par_type property of a ParResponse.
    #: This constant has a value of "TABLE"
    PAR_TYPE_TABLE = "TABLE"

    #: A constant which can be used with the par_type property of a ParResponse.
    #: This constant has a value of "MOUNT"
    PAR_TYPE_MOUNT = "MOUNT"

    #: A constant which can be used with the par_type property of a ParResponse.
    #: This constant has a value of "PATH"
    PAR_TYPE_PATH = "PATH"

    def __init__(self, **kwargs):
        """
        Initializes a new ParResponse object with values from keyword arguments.
        The following keyword arguments are supported (corresponding to the getters/setters of this class):

        :param par_hash:
            The value to assign to the par_hash property of this ParResponse.
        :type par_hash: str

        :param prefix_path:
            The value to assign to the prefix_path property of this ParResponse.
        :type prefix_path: str

        :param par_type:
            The value to assign to the par_type property of this ParResponse.
            Allowed values for this property are: "DATABASE", "TABLE", "MOUNT", "PATH", 'UNKNOWN_ENUM_VALUE'.
            Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.
        :type par_type: str

        """
        self.swagger_types = {
            "par_hash": "str",
            "prefix_path": "str",
            "par_type": "str",
        }

        self.attribute_map = {
            "par_hash": "parHash",
            "prefix_path": "prefixPath",
            "par_type": "parType",
        }

        self._par_hash = None
        self._prefix_path = None
        self._par_type = None

    @property
    def par_hash(self):
        """
        **[Required]** Gets the par_hash of this ParResponse.
        PAR Hash for the bucket/object for a given namespace, scoped to the operation and exipry time


        :return: The par_hash of this ParResponse.
        :rtype: str
        """
        return self._par_hash

    @par_hash.setter
    def par_hash(self, par_hash):
        """
        Sets the par_hash of this ParResponse.
        PAR Hash for the bucket/object for a given namespace, scoped to the operation and exipry time


        :param par_hash: The par_hash of this ParResponse.
        :type: str
        """
        self._par_hash = par_hash

    @property
    def prefix_path(self):
        """
        Gets the prefix_path of this ParResponse.
        Prefix path for the parHash.


        :return: The prefix_path of this ParResponse.
        :rtype: str
        """
        return self._prefix_path

    @prefix_path.setter
    def prefix_path(self, prefix_path):
        """
        Sets the prefix_path of this ParResponse.
        Prefix path for the parHash.


        :param prefix_path: The prefix_path of this ParResponse.
        :type: str
        """
        self._prefix_path = prefix_path

    @property
    def par_type(self):
        """
        Gets the par_type of this ParResponse.
        Type of Par (DB/TABLE)

        Allowed values for this property are: "DATABASE", "TABLE", "MOUNT", "PATH", 'UNKNOWN_ENUM_VALUE'.
        Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.


        :return: The par_type of this ParResponse.
        :rtype: str
        """
        return self._par_type

    @par_type.setter
    def par_type(self, par_type):
        """
        Sets the par_type of this ParResponse.
        Type of Par (DB/TABLE)


        :param par_type: The par_type of this ParResponse.
        :type: str
        """
        allowed_values = ["DATABASE", "TABLE", "MOUNT", "PATH"]
        if not value_allowed_none_or_none_sentinel(par_type, allowed_values):
            par_type = "UNKNOWN_ENUM_VALUE"
        self._par_type = par_type

    def __repr__(self):
        return formatted_flat_dict(self)

    def __eq__(self, other):
        if other is None:
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
