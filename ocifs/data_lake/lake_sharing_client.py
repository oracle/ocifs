# coding: utf-8
# Copyright (c) 2021, 2024 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import logging
import os

from oci._vendor import requests  # noqa: F401
from oci._vendor import six
from oci.base_client import BaseClient
from oci import retry, circuit_breaker  # noqa: F401
from oci.config import get_config_value_or_default, validate_config
from oci.signer import Signer
from oci.util import (
    Sentinel,
    get_signer_from_authentication_type,
    AUTHENTICATION_TYPE_FIELD_NAME,
)
from ocifs.errors import translate_oci_error

from .managed_prefix_collection import ManagedPrefixCollection
from .managed_prefix_summary import ManagedPrefixSummary
from .par_response import ParResponse
from .rename_object_details import RenameObjectDetails


missing = Sentinel("Missing")

lakesharing_type_mapping = {
    "ManagedPrefixCollection": ManagedPrefixCollection,
    "ManagedPrefixSummary": ManagedPrefixSummary,
    "ParResponse": ParResponse,
}

logger = logging.getLogger("lakesharingClient")


def setup_logging_for_lakesharing_client(level=None):
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
    setup_logging_for_lakesharing_client()


class LakeSharingClient(object):
    """
    A description of the Lakesharing API.
    """

    def __init__(
        self, config, oci_lake_sharing_service_api_endpoint: str = None, **kwargs
    ):
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
        validate_config(config, signer=kwargs.get("signer"))
        if "signer" in kwargs:
            signer = kwargs["signer"]

        elif AUTHENTICATION_TYPE_FIELD_NAME in config:
            signer = get_signer_from_authentication_type(config)

        else:
            signer = Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content"),
            )
        self.oci_lake_sharing_service_api_endpoint = (
            oci_lake_sharing_service_api_endpoint
        )
        base_client_init_kwargs = {
            "regional_client": True,
            "service_endpoint": self.oci_lake_sharing_service_api_endpoint,
            "base_path": "/20180828",
            "service_endpoint_template": "https://lakesharing.{region}.oci.{secondLevelDomain}",
            "endpoint_service_name": "lake_sharing",
            "skip_deserialization": kwargs.get("skip_deserialization", False),
            "circuit_breaker_strategy": kwargs.get(
                "circuit_breaker_strategy",
                circuit_breaker.GLOBAL_CIRCUIT_BREAKER_STRATEGY,
            ),
        }
        if "timeout" in kwargs:
            base_client_init_kwargs["timeout"] = kwargs.get("timeout")
        if base_client_init_kwargs.get("circuit_breaker_strategy") is None:
            base_client_init_kwargs["circuit_breaker_strategy"] = (
                circuit_breaker.DEFAULT_CIRCUIT_BREAKER_STRATEGY
            )
        if "allow_control_chars" in kwargs:
            base_client_init_kwargs["allow_control_chars"] = kwargs.get(
                "allow_control_chars"
            )
        self.retry_strategy = kwargs.get("retry_strategy")
        self.circuit_breaker_callback = kwargs.get("circuit_breaker_callback")
        self.base_client = BaseClient(
            "lake_sharing",
            config,
            signer,
            lakesharing_type_mapping,
            **base_client_init_kwargs,
        )

    def delete_object(self, namespace, bucket, object, **kwargs):
        """
        Delete an object in a particular bucket in tenancy namespace


        :param str namespace: (required)
            Unique Namespace identifier

        :param str bucket: (required)
            Unique Bucket identifier

        :param str object: (required)
            Unique Object identifier

        :param str opc_request_id: (optional)
            The client request ID for tracing.

        :param str if_match: (optional)
            For optimistic concurrency control. In the PUT or DELETE call
            for a resource, set the `if-match` parameter to the value of the
            etag from a previous GET or POST response for that resource.
            The resource will be updated or deleted only if the etag you
            provide matches the resource's current etag value.

        :param str opc_retry_token: (optional)
            A token that uniquely identifies a request so it can be retried in case of a timeout or
            server error without risk of executing that same action again. Retry tokens expire after 24
            hours, but can be invalidated before then due to conflicting operations. For example, if a resource
            has been deleted and purged from the system, then a retry of the original creation request
            might be rejected.

        :param str lakeshare_client_resource_family: (optional)
            HTTP header describing client resource type

        :param str lakeshare_client_resource_ocid: (optional)
            HTTP header containing client resource ocid

        :param obj retry_strategy: (optional)
            A retry strategy to apply to this specific operation/call. This will override any retry strategy set at the client-level.

            This should be one of the strategies available in the :py:mod:`~oci.retry` module. A convenience :py:data:`~oci.retry.DEFAULT_RETRY_STRATEGY`
            is also available. The specifics of the default retry strategy are described `here <https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/sdk_behaviors/retries.html>`__.

            To have this operation explicitly not perform any retries, pass an instance of :py:class:`~oci.retry.NoneRetryStrategy`.

        :return: A :class:`~oci.response.Response` object with data of type None
        :rtype: :class:`~oci.response.Response`
        """
        resource_path = "/deleteObject"
        method = "POST"
        query_params = {"namespace": namespace, "bucket": bucket, "object": object}
        query_params = {
            k: v
            for (k, v) in six.iteritems(query_params)
            if v is not missing and v is not None
        }

        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
            "opc-request-id": kwargs.get("opc_request_id", missing),
            "if-match": kwargs.get("if_match", missing),
            "opc-retry-token": kwargs.get("opc_retry_token", missing),
            "lakeshare-client-resource-family": kwargs.get(
                "lakeshare_client_resource_family", missing
            ),
            "lakeshare-client-resource-ocid": kwargs.get(
                "lakeshare_client_resource_ocid", missing
            ),
        }
        header_params = {
            k: v
            for (k, v) in six.iteritems(header_params)
            if v is not missing and v is not None
        }

        delete_object_response = None
        try:
            if self.retry_strategy:
                delete_object_response = self.retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                )
            else:
                delete_object_response = self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                )
            logger.debug(
                "Deleting object from the lakesharing server"
                " for the given lake namespace: "
                f"{namespace} ,bucket:{bucket},object:{object}"
                f",delete_object_response status:{delete_object_response.status}"
                f",delete_object_response data:{delete_object_response.data}"
                f" and it's opc-request-id:{delete_object_response.headers['opc-request-id']}"
            )
        except Exception as excep:
            logger.error(
                "Exception encountered when deleting the object "
                "for the given lake namespace:"
                f"{namespace} ,bucket :{bucket} ,object:{object} "
                f" and exception details: : {excep}"
            )
            raise translate_oci_error(excep) from excep
        return delete_object_response

    def generate_par(self, namespace, bucket, access_type, object_name, **kwargs):
        """
        Gets a LakeSharing by identifier
        :param access_type:  (required)
        :param str namespace: (required)
            Unique Namespace identifier

        :param str bucket: (required)
            Unique Bucket identifier

        :param str object: (optional)
            Unique Object identifier

        :param str x_oci_lakeshare_op: (optional)
            HTTP header describing lakeshare op type.

        :param str lakeshare_client_resource_family: (optional)
            HTTP header describing client resource type

        :param str lakeshare_client_resource_ocid: (optional)
            HTTP header containing client resource ocid

        :param str opc_request_id: (optional)
            The client request ID for tracing.

        :param obj retry_strategy: (optional)
            A retry strategy to apply to this specific operation/call. This will override any retry strategy set at the client-level.

            This should be one of the strategies available in the :py:mod:`~oci.retry` module. A convenience :py:data:`~oci.retry.DEFAULT_RETRY_STRATEGY`
            is also available. The specifics of the default retry strategy are described `here <https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/sdk_behaviors/retries.html>`__.

            To have this operation explicitly not perform any retries, pass an instance of :py:class:`~oci.retry.NoneRetryStrategy`.

        :return: A :class:`~oci.response.Response` object with data of type :class:`~oci.lakesharing.models.ParResponse`
        :rtype: :class:`~oci.response.Response`
        """
        resource_path = "/par"
        method = "GET"
        prefix = kwargs.get("prefix")
        if not object_name:
            object_name = ""
            if prefix:
                object_name = prefix[:-1] if prefix.endswith("/") else prefix
        logger.debug(f"lakesharing object_name:{object_name}")
        query_params = {
            "namespace": namespace,
            "bucket": bucket,
            "x_oci_lakeshare_op": access_type,
            "object": object_name,
        }
        query_params = {
            k: v
            for (k, v) in six.iteritems(query_params)
            if v is not missing and v is not None
        }

        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-oci-lakeshare-op": access_type,
            "object": object_name,
            "lakeshare-client-resource-family": kwargs.get(
                "lakeshare_client_resource_family", missing
            ),
            "lakeshare-client-resource-ocid": kwargs.get(
                "lakeshare_client_resource_ocid", missing
            ),
            "opc-request-id": kwargs.get("opc_request_id", missing),
        }

        header_params = {
            k: v
            for (k, v) in six.iteritems(header_params)
            if v is not missing and v is not None
        }
        par_response = None

        try:
            if self.retry_strategy:
                par_response = self.retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="ParResponse",
                )
            else:
                par_response = self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="ParResponse",
                )
            logger.debug(
                f" PAR response:{par_response.data}"
                f",PAR response status:{par_response.status}"
                " for the given lake namespace:"
                f"{namespace} ,bucket:{bucket}"
                f",object: {object_name} and "
                f" opc-request-id : {par_response.headers['opc-request-id']}"
            )
        except Exception as excep:
            logger.error(
                "Exception encountered when generating PAR"
                " for the given lake namespace: "
                f"{namespace} ,bucket:{bucket}"
                f" and exception details:{excep}"
            )
            raise translate_oci_error(excep) from excep
        return par_response

    def is_healthy(self, **kwargs):
        """
        check whether service is healthy or not


        :param obj retry_strategy: (optional)
            A retry strategy to apply to this specific operation/call. This will override any retry strategy set at the client-level.

            This should be one of the strategies available in the :py:mod:`~oci.retry` module. A convenience :py:data:`~oci.retry.DEFAULT_RETRY_STRATEGY`
            is also available. The specifics of the default retry strategy are described `here <https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/sdk_behaviors/retries.html>`__.

            To have this operation explicitly not perform any retries, pass an instance of :py:class:`~oci.retry.NoneRetryStrategy`.

        :return: A :class:`~oci.response.Response` object with data of type None
        :rtype: :class:`~oci.response.Response`
        """
        resource_path = "/isHealthy"
        method = "GET"
        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
        }

        lake_sharing_health_check_response = None
        oci_lake_sharing_service_health_status = False
        try:
            if self.retry_strategy:
                lake_sharing_health_check_response = (
                    self.retry_strategy.make_retrying_call(
                        self.base_client.call_api,
                        resource_path=resource_path,
                        method=method,
                        header_params=header_params,
                    )
                )
            else:
                lake_sharing_health_check_response = self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    header_params=header_params,
                )
            if (
                lake_sharing_health_check_response
                and lake_sharing_health_check_response.status == 200
            ):
                oci_lake_sharing_service_health_status = True
        except Exception as excep:
            logger.error(
                "Exception encountered when fetching health check status from the lakesharing server "
                f" and exception details:{excep}"
            )
            raise translate_oci_error(excep) from excep

        return oci_lake_sharing_service_health_status

    def list_managed_prefixes(self, namespace, bucket, **kwargs):
        """
        Gets all the managed prefix paths

        :param str namespace: (required)
            Namespace of the bucket

        :param str bucket: (required)
            Bucket Name

        :param str opc_request_id: (optional)
            The client request ID for tracing.

        :param int limit: (optional)
            The maximum number of items to return.

        :param str page: (optional)
            A token representing the position at which to start retrieving results. This must come from the `opc-next-page` header field of a previous response.

        :param str lakeshare_client_resource_family: (optional)
            HTTP header describing client resource type

        :param str lakeshare_client_resource_ocid: (optional)
            HTTP header containing client resource ocid

        :param obj retry_strategy: (optional)
            A retry strategy to apply to this specific operation/call. This will override any retry strategy set at the client-level.

            This should be one of the strategies available in the :py:mod:`~oci.retry` module. A convenience :py:data:`~oci.retry.DEFAULT_RETRY_STRATEGY`
            is also available. The specifics of the default retry strategy are described `here <https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/sdk_behaviors/retries.html>`__.

            To have this operation explicitly not perform any retries, pass an instance of :py:class:`~oci.retry.NoneRetryStrategy`.

        :return: A :class:`~oci.response.Response` object with data of type :class:`~oci.lakesharing.models.ManagedPrefixCollection`
        :rtype: :class:`~oci.response.Response`
        """
        resource_path = "/managedprefixes"
        method = "GET"
        query_params = {
            "namespace": namespace,
            "bucket": bucket,
            "limit": kwargs.get("limit", missing),
            "page": kwargs.get("page", missing),
        }
        query_params = {
            k: v
            for (k, v) in six.iteritems(query_params)
            if v is not missing and v is not None
        }

        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
            "opc-request-id": kwargs.get("opc_request_id", missing),
            "lakeshare-client-resource-family": kwargs.get(
                "lakeshare_client_resource_family", missing
            ),
            "lakeshare-client-resource-ocid": kwargs.get(
                "lakeshare_client_resource_ocid", missing
            ),
        }
        header_params = {
            k: v
            for (k, v) in six.iteritems(header_params)
            if v is not missing and v is not None
        }
        managed_prefix_collection_response = None
        managed_prefix_collection_response_data = None
        try:
            if self.retry_strategy:
                managed_prefix_collection_response = (
                    self.retry_strategy.make_retrying_call(
                        self.base_client.call_api,
                        resource_path=resource_path,
                        method=method,
                        query_params=query_params,
                        header_params=header_params,
                        response_type="ManagedPrefixCollection",
                    )
                )
            else:
                managed_prefix_collection_response = self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="ManagedPrefixCollection",
                )
            managed_prefix_collection_response_data = (
                managed_prefix_collection_response.data
            )
            logger.debug(
                f"managed_prefix_collection_response data:{managed_prefix_collection_response.data}"
                f",managed_prefix_collection_response status:{managed_prefix_collection_response.status}"
                " for the given lake namespace:"
                f"{namespace} ,bucket:{bucket}"
                f" opc-request-id:{managed_prefix_collection_response.headers['opc-request-id']}"
            )
        except Exception as excep:
            logger.error(
                "Exception encountered when fetching  all the managed prefix paths from the lakesharing server "
                "for the given lake namespace:"
                f"{namespace} and it's bucket:{bucket}"
                f" and exception details:{excep}"
            )
            raise translate_oci_error(excep) from excep
        return managed_prefix_collection_response_data

    def rename_object(
        self, rename_object_details: RenameObjectDetails, namespace, bucket, **kwargs
    ):
        """
        Renames a object in a particular bucket in tenancy namespace

        :param oci.lakesharing.models.RenameObjectDetails rename_object_details: (required)
            The object details to be renamed.

        :param str namespace: (required)
            Unique Namespace identifier

        :param str bucket: (required)
            Unique Bucket identifier

        :param str opc_request_id: (optional)
            The client request ID for tracing.

        :param str if_match: (optional)
            For optimistic concurrency control. In the PUT or DELETE call
            for a resource, set the `if-match` parameter to the value of the
            etag from a previous GET or POST response for that resource.
            The resource will be updated or deleted only if the etag you
            provide matches the resource's current etag value.

        :param str lakeshare_client_resource_family: (optional)
            HTTP header describing client resource type

        :param str lakeshare_client_resource_ocid: (optional)
            HTTP header containing client resource ocid

        :param obj retry_strategy: (optional)
            A retry strategy to apply to this specific operation/call. This will override any retry strategy set at the client-level.

            This should be one of the strategies available in the :py:mod:`~oci.retry` module. A convenience :py:data:`~oci.retry.DEFAULT_RETRY_STRATEGY`
            is also available. The specifics of the default retry strategy are described `here <https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/sdk_behaviors/retries.html>`__.

            To have this operation explicitly not perform any retries, pass an instance of :py:class:`~oci.retry.NoneRetryStrategy`.

        :return: A :class:`~oci.response.Response` object with data of type None
        :rtype: :class:`~oci.response.Response`
        """
        resource_path = "/renameObject"
        method = "POST"
        query_params = {"namespace": namespace, "bucket": bucket}
        query_params = {
            k: v
            for (k, v) in six.iteritems(query_params)
            if v is not missing and v is not None
        }

        header_params = {
            "accept": "application/json",
            "content-type": "application/json",
            "opc-request-id": kwargs.get("opc_request_id", missing),
            "if-match": kwargs.get("if_match", missing),
            "lakeshare-client-resource-family": kwargs.get(
                "lakeshare_client_resource_family", missing
            ),
            "lakeshare-client-resource-ocid": kwargs.get(
                "lakeshare_client_resource_ocid", missing
            ),
        }
        header_params = {
            k: v
            for (k, v) in six.iteritems(header_params)
            if v is not missing and v is not None
        }

        rename_object_response = None
        try:
            if self.retry_strategy:
                rename_object_response = self.retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    body=rename_object_details,
                )
            else:
                rename_object_response = self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    query_params=query_params,
                    header_params=header_params,
                    body=rename_object_details,
                )
            logger.debug(
                "Renaming object from the lakesharing server"
                " for the given lake namespace: "
                f"{namespace} ,bucket:{bucket},source_name:{rename_object_details.source_name}"
                f",new_name:{rename_object_details.new_name}"
                f",rename_object_response status:{rename_object_response.status}"
                f",rename_object_response data:{rename_object_response.data}"
                f" and it's opc-request-id:{rename_object_response.headers['opc-request-id']}"
            )
        except Exception as excep:
            logger.error(
                "Exception encountered when renaming the object "
                "for the given lake namespace:"
                f"{namespace} ,bucket :{bucket} ,object:{object} "
                f" and exception details: : {excep}"
            )
            raise translate_oci_error(excep) from excep
        return rename_object_response
