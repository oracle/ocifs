# coding: utf-8 Copyright (c) 2016, 2023, Oracle and/or its affiliates.  All rights reserved. This software is
# dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at
# https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0.
# You may choose either license.

from __future__ import absolute_import

import logging
import os

from oci._vendor import requests  # noqa: F401
from oci._vendor import six

from oci import retry, circuit_breaker  # noqa: F401
from oci.base_client import BaseClient
from oci.config import get_config_value_or_default, validate_config
from oci.signer import Signer
from oci.util import Sentinel, get_signer_from_authentication_type, AUTHENTICATION_TYPE_FIELD_NAME
from ocifs.errors import translate_oci_error

from .lakehouse import Lakehouse
from .lake_mount import LakeMount
from .mount_specification import MountSpecification

missing = Sentinel("Missing")

# Maps type name to class for lakehouse services.
lakehouse_type_mapping = {
    "Lakehouse": Lakehouse,
    "LakeMount": LakeMount,
    "MountSpecification": MountSpecification
}

logger = logging.getLogger("lakehouse")


def setup_logging_for_lakehouse(level=None):
    level = level or os.environ["OCIFS_LOGGING_LEVEL"]
    handle = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s " "- %(message)s"
    )
    handle.setFormatter(formatter)
    logger.addHandler(handle)
    logger.setLevel(level)


# To quickly see all messages, you can set the environment variable OCIFS_LOGGING_LEVEL=DEBUG.
if "OCIFS_LOGGING_LEVEL" in os.environ:
    setup_logging_for_lakehouse()


class LakehouseClient(object):
    """
    Data Lake helps secure and govern data stored in Object Storage and other Oracle databases.
    """

    def __init__(self, config, lake_service_api_endpoint: str = None, **kwargs):
        """
        Creates a new service client

        :param dict config:
            Configuration keys and values as per `SDK and Tool Configuration <https://docs.cloud.oracle.com/Content/API/Concepts/sdkconfig.htm>`__.
            The :py:meth:`~oci.config.from_file` method can be used to load configuration from a file. Alternatively, a ``dict`` can be passed. You can validate_config
            the dict using :py:meth:`~oci.config.validate_config`

        :param str service_endpoint: (optional)
            The endpoint of the service to call using this client. For example ``https://iaas.us-ashburn-1.oraclecloud.com``. If this keyword argument is
            not provided then it will be derived using the region in the config parameter. You should only provide this keyword argument if you have an explicit
            need to specify a service endpoint.

        :param timeout: (optional)
            The connection and read timeouts for the client. The default values are connection timeout 10 seconds and read timeout 60 seconds. This keyword argument can be provided
            as a single float, in which case the value provided is used for both the read and connection timeouts, or as a tuple of two floats. If
            a tuple is provided then the first value is used as the connection timeout and the second value as the read timeout.
        :type timeout: float or tuple(float, float)

        :param signer: (optional)
            The signer to use when signing requests made by the service client. The default is to use a :py:class:`~oci.signer.Signer` based on the values
            provided in the config parameter.

            One use case for this parameter is for `Instance Principals authentication <https://docs.cloud.oracle.com/Content/Identity/Tasks/callingservicesfrominstances.htm>`__
            by passing an instance of :py:class:`~oci.auth.signers.InstancePrincipalsSecurityTokenSigner` as the value for this keyword argument
        :type signer: :py:class:`~oci.signer.AbstractBaseSigner`

        :param obj retry_strategy: (optional)
            A retry strategy to apply to all calls made by this service client (i.e. at the client level). There is no retry strategy applied by default.
            Retry strategies can also be applied at the operation level by passing a ``retry_strategy`` keyword argument as part of calling the operation.
            Any value provided at the operation level will override whatever is specified at the client level.

            This should be one of the strategies available in the :py:mod:`~oci.retry` module. A convenience :py:data:`~oci.retry.DEFAULT_RETRY_STRATEGY`
            is also available. The specifics of the default retry strategy are described `here <https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/sdk_behaviors/retries.html>`__.
        """
        validate_config(config, signer=kwargs.get('signer'))
        if 'signer' in kwargs:
            signer = kwargs['signer']
        elif AUTHENTICATION_TYPE_FIELD_NAME in config:
            signer = get_signer_from_authentication_type(config)
        else:
            signer = Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
        self.lake_service_api_endpoint = lake_service_api_endpoint
        logger.debug(f"lakehouse service api endpoint is: {self.lake_service_api_endpoint}")
        base_client_init_kwargs = {
            'regional_client': True,
            'service_endpoint': self.lake_service_api_endpoint,
            'base_path': '/20221010',
            'service_endpoint_template': 'https://lake.{region}.oci.{secondLevelDomain}',
            'service_endpoint_template': 'https://objectstorage.{region}.{secondLevelDomain}',
            'endpoint_service_name': 'lakehouse',
            'skip_deserialization': kwargs.get('skip_deserialization', False),
            'circuit_breaker_strategy': kwargs.get('circuit_breaker_strategy',
                                                   circuit_breaker.GLOBAL_CIRCUIT_BREAKER_STRATEGY)
        }
        if 'timeout' in kwargs:
            base_client_init_kwargs['timeout'] = kwargs.get('timeout')
        if base_client_init_kwargs.get('circuit_breaker_strategy') is None:
            base_client_init_kwargs['circuit_breaker_strategy'] = circuit_breaker.DEFAULT_CIRCUIT_BREAKER_STRATEGY
        if 'allow_control_chars' in kwargs:
            base_client_init_kwargs['allow_control_chars'] = kwargs.get('allow_control_chars')
        self.retry_strategy = kwargs.get('retry_strategy')
        self.circuit_breaker_callback = kwargs.get('circuit_breaker_callback')
        self.base_client = BaseClient("lakehouse", config, signer, lakehouse_type_mapping,
                                      **base_client_init_kwargs)
        logger.debug(f"lakehouse client got initialized !!!!!!!!")

    def get_lakeshare_endpoint(self, lake_id, **kwargs):
        """
        Gets a lakesharing endpoint  by for the given
        :param str lake_id: (required)
            unique Lake identifier
        :return: A :class:`~oci.response.Response` object with data of type :class:`~oci.lakehouse.models.Lakehouse`
        :rtype: :class:`~oci.response.Response`
        """
        lake_resource_path = "/lakes/" + lake_id
        method = "GET"
        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
            "opc-request-id": kwargs.get("opc_request_id", missing)
        }
        header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}
        lakeresponse = None
        lakeshare_endpoint = None
        try:
            if self.retry_strategy:
                lakeresponse = self.retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=lake_resource_path,
                    method=method,
                    header_params=header_params,
                    response_type="Lakehouse")
            else:
                lakeresponse = self.base_client.call_api(
                    resource_path=lake_resource_path,
                    method=method,
                    header_params=header_params,
                    response_type="Lakehouse")
            lakeshare_endpoint = lakeresponse.data.lakeshare_endpoint
            logger.debug(
                f"lake response status:{lakeresponse.status}"
                f",lakeresponse data:{lakeresponse.data}"
                f",lakeshare_endpoint data:{lakeshare_endpoint}"
                f" and it's opc-request-id:{lakeresponse.headers['opc-request-id']}"
            )

        except Exception as excep:
            logger.error(
                "Exception encountered when fetching lakesharing endpoint from lakeshouse details request fetch call "
                "for the given lake Ocid: "
                f"{lake_id} and exception details:{excep}"
            )
            raise translate_oci_error(excep) from excep
        return lakeshare_endpoint

    def get_lakehouse_mount(self, lakehouse_id, mount_key: str, mount_type: str = None,
                            mount_scope_entity_type: str = None, mount_scope_schema_key: str = None,
                            mount_scope_table_key: str = None, mount_scope_user_id: str = None,
                            **kwargs):
        """
        Returns a Mount identified by the Mount Key.
        :param str lake_id: (required)
            unique Lake identifier
        :param str mount_key: (required)
            The unique key of the Mount.
        :param str mount_type: (required)
            mandatory parameter which decides type of Mount.
            Allowed values are: "EXTERNAL", "MANAGED"
        :param str mount_scope_entity_type: (optional)
            Scope for the Managed Mount to be queried
            Allowed values are: "DATABASE", "TABLE", "USER"
        :param str mount_scope_schema_key: (optional)
            Entity key for the selected scope of the Managed Mount.
        :param str mount_scope_table_key: (optional)
            Entity key for the selected scope of the Managed Mount.
        :param str mount_scope_user_id: (optional)
            Entity Id for the selected scope of the Managed Mount.
        :return: A :class:`~oci.response.Response` object with data of type :class:`~oci.lakehouse.models.LakehouseMountCollection`
        :rtype: :class:`~oci.response.Response`

        Parameters
        ----------
        mount_name
        """
        lake_resource_path = "/lakes/" + lakehouse_id + "/lakeMounts/" + mount_key
        method = "GET"
        if not mount_type:
            mount_type = "EXTERNAL"
        mount_type_allowed_values = ["EXTERNAL", "MANAGED"]
        if mount_type not in mount_type_allowed_values:
            raise ValueError(
                "Invalid value for `mount_type`, must be one of {0}".format(mount_type_allowed_values)
            )
        query_params = {}
        if mount_type == 'MANAGED':
            mount_scope_entity_type_allowed_values = ["DATABASE", "TABLE", "USER"]
            if mount_scope_entity_type not in mount_scope_entity_type_allowed_values:
                raise ValueError(
                    "Invalid value for `mount_scope_entity_type`, must be one of {0}".format(
                        mount_scope_entity_type_allowed_values)
                )
            if mount_scope_entity_type == 'DATABASE' and not mount_scope_schema_key:
                raise ValueError('mount_scope_schema_key parameter cannot be None, whitespace or empty string')
            if mount_scope_entity_type == 'TABLE':
                if not mount_scope_schema_key or mount_scope_table_key:
                    raise ValueError('mount_scope_schema_key and mount_scope_table_key  parameters cannot be None, '
                                     'whitespace or empty string')
            if mount_scope_entity_type == 'USER':
                if not mount_scope_user_id:
                    raise ValueError('mount_scope_user_id parameter cannot be None, whitespace or empty string')
            query_params = {
                "mountType": mount_type,
                "mountScopeEntityType": mount_scope_entity_type,
                "mountScopeSchemaKey": mount_scope_schema_key,
                "mountScopeTableKey": mount_scope_table_key,
                "mountScopeUserId": mount_scope_entity_type
            }
        else:
            query_params = {
                "mountType": mount_type
            }
        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
            "opc-request-id": kwargs.get("opc_request_id", missing)
        }
        header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

        retry_strategy = self.retry_strategy
        lake_mount = None
        try:
            if self.retry_strategy:
                lake_mount = retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=lake_resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="LakeMount")
            else:
                lake_mount = self.base_client.call_api(
                    resource_path=lake_resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="LakeMount")
            logger.debug(
                f"lake_mount response status:{lake_mount.status}"
                f",lake_mount data:{lake_mount.data}")
        except Exception as excep:
            logger.error(
                "Exception encountered when fetching bucket and namespace for the given mountName "
                "for the given lake Ocid: "
                f"{lakehouse_id}, mountName: {mount_key} and exception details:{excep}"
            )
            raise translate_oci_error(excep) from excep

        return lake_mount
