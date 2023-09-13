# coding: utf-8
# Copyright (c) 2021, 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import logging
import os

import requests
import six
from oci import circuit_breaker
from oci.base_client import BaseClient
from oci.config import get_config_value_or_default, validate_config
from oci.object_storage import ObjectStorageClient
from oci.retry import retry
from oci.signer import Signer
from oci.util import Sentinel, get_signer_from_authentication_type, AUTHENTICATION_TYPE_FIELD_NAME, \
    is_content_length_calculable_by_req_util, back_up_body_calculate_stream_content_length
from oci.object_storage.models import object_storage_type_mapping

from .lake_sharing_client import LakeSharingClient
from .lakehouse_client import LakehouseClient

missing = Sentinel("Missing")

logger = logging.getLogger("lakesharing")


def setup_logging_for_lakesharing(level=None):
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
    setup_logging_for_lakesharing()


def get_lake_service_endpoint(lake_ocid: str):
    lake_service_api_endpoint = 'https://lake.' + lake_ocid.split('.')[3] + '.oci.oraclecloud.com'
    return lake_service_api_endpoint


def validate_mount_scope_entity(mount_spec_array):
    mount_scope_entity = mount_spec_array[1].upper()
    mount_scope_entity_allowed_values = ["DATABASE", "TABLE", "USER"]
    if mount_scope_entity not in mount_scope_entity_allowed_values:
        raise ValueError(
            "Invalid value for `mount_scope_entity_type`, must be one of {0}".format(
                mount_scope_entity_allowed_values)
        )
    if mount_scope_entity == 'DATABASE' and len(mount_spec_array) != 3:
        raise ValueError('DATABASE mount mentioned in ocifs URI is invalid.Please follow the URI format like '
                         '<mountName>:<mount_scope_entity_type>:<databaseKey>')
    elif mount_scope_entity == 'TABLE' and len(mount_spec_array) != 4:
        raise ValueError('TABLE mount mentioned in ocifs URI is invalid.Please follow the URI format like '
                         '<mountName>:<mount_scope_entity_type>:<databaseKey>:<tableKey>')
    elif mount_scope_entity == 'USER' and len(mount_spec_array) != 3:
        raise ValueError('USER mount mentioned in ocifs URI is invalid.Please follow the URI format like '
                         '<mountName>:<mount_scope_entity_type>:<userOcid>')
    return


class LakeSharingObjectStorageClient(ObjectStorageClient):
    def __init__(self, config, **kwargs):
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
            is also available. The specifics of the default retry strategy are described `here <https://docs.oracle.com/en-us/iaas/tools/python/latest/sdk_behaviors/retries.html>`__.

        :param obj circuit_breaker_strategy: (optional)
            A circuit breaker strategy to apply to all calls made by this service client (i.e. at the client level).
            This client uses :py:data:`~oci.circuit_breaker.DEFAULT_CIRCUIT_BREAKER_STRATEGY` as default if no circuit breaker strategy is provided.
            The specifics of circuit breaker strategy are described `here <https://docs.oracle.com/en-us/iaas/tools/python/latest/sdk_behaviors/circuit_breakers.html>`__.

        :param function circuit_breaker_callback: (optional)
            Callback function to receive any exceptions triggerred by the circuit breaker.

        :param bool client_level_realm_specific_endpoint_template_enabled: (optional)
            A boolean flag to indicate whether or not this client should be created with realm specific endpoint template enabled or disable. By default, this will be set as None.

        :param allow_control_chars: (optional)
            allow_control_chars is a boolean to indicate whether or not this client should allow control characters in the response object. By default, the client will not
            allow control characters to be in the response object.
        """
        super().__init__(config, **kwargs)
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

        base_client_init_kwargs = {
            'regional_client': True,
            'service_endpoint': kwargs.get('service_endpoint'),
            'base_path': '/',
            'service_endpoint_template': 'https://objectstorage.{region}.{secondLevelDomain}',
            'endpoint_service_name': 'objectstorage',
            'service_endpoint_template_per_realm': {
                'oc1': 'https://{namespaceName+Dot}objectstorage.{region}.oci.customer-oci.com'},  # noqa: E201 E202
            'skip_deserialization': kwargs.get('skip_deserialization', False),
            'circuit_breaker_strategy': kwargs.get('circuit_breaker_strategy',
                                                   circuit_breaker.GLOBAL_CIRCUIT_BREAKER_STRATEGY),
            'client_level_realm_specific_endpoint_template_enabled': kwargs.get(
                'client_level_realm_specific_endpoint_template_enabled')
        }
        if 'timeout' in kwargs:
            base_client_init_kwargs['timeout'] = kwargs.get('timeout')
        if base_client_init_kwargs.get('circuit_breaker_strategy') is None:
            base_client_init_kwargs['circuit_breaker_strategy'] = circuit_breaker.DEFAULT_CIRCUIT_BREAKER_STRATEGY
        if 'allow_control_chars' in kwargs:
            base_client_init_kwargs['allow_control_chars'] = kwargs.get('allow_control_chars')
        self.base_client = BaseClient("object_storage", config, signer, object_storage_type_mapping,
                                      **base_client_init_kwargs)
        self.retry_strategy = kwargs.get('retry_strategy')
        self.circuit_breaker_callback = kwargs.get('circuit_breaker_callback')
        self.config = config or dict()
        self.lake_sharing_client = None
        self.bucket_namespace_to_lake_ocid_map = {}
        self.lake_ocid_to_lake_sharing_client_map = {}
        self.managed_prefix_collection_response_cache = {}
        self.lake_ocid_to_lake_client_map = {}

    def get_lake_sharing_client_by_bucket_namespace(self, namespace_name, bucket_name, **kwargs):
        lake_sharing_client: LakeSharingClient = None
        cache_key: str = namespace_name + '-' + bucket_name
        lake_ocid = self.bucket_namespace_to_lake_ocid_map.get(cache_key)
        lake_sharing_client = self.lake_ocid_to_lake_sharing_client_map.get(lake_ocid)
        return lake_sharing_client

    def get_lake_sharing_client(self, lake_ocid: str, lake_client: LakehouseClient = None, **kwargs):
        lake_sharing_client: LakeSharingClient = None
        if self.lake_ocid_to_lake_sharing_client_map.get(lake_ocid):
            lake_sharing_client = self.lake_ocid_to_lake_sharing_client_map.get(lake_ocid)
        else:
            lakeshare_endpoint = lake_client.get_lakeshare_endpoint(lake_ocid, **kwargs)
            logger.debug(f"lakeSharing server api endpoint is:{lakeshare_endpoint}")
            lake_sharing_client = LakeSharingClient(self.config, lakeshare_endpoint, **kwargs)
            lake_sharing_service_health_status = lake_sharing_client.is_healthy(**kwargs)
            logger.debug(f"lakeSharing api server health check status:{lake_sharing_service_health_status}")
            if lake_sharing_service_health_status:
                self.lake_ocid_to_lake_sharing_client_map[lake_ocid] = lake_sharing_client
        return lake_sharing_client

    def get_bucket_namespace_for_given_mount_name(self, lake_ocid: str, mount_spec_array, mount_type: str = None,
                                                  **kwargs):
        if mount_type == 'MANAGED':
            validate_mount_scope_entity(mount_spec_array)
        mount_name = mount_spec_array[0]
        lake_service_api_endpoint = get_lake_service_endpoint(lake_ocid)
        logger.debug(f"lake_service_api_endpoint:{lake_service_api_endpoint}")
        lake_client = None
        lake_sharing_client = None
        bucket_namespace_map = dict()
        if self.lake_ocid_to_lake_client_map.get(lake_ocid):
            lake_client = self.lake_ocid_to_lake_client_map.get(lake_ocid)
        else:
            lake_client = LakehouseClient(self.config, lake_service_api_endpoint, **kwargs)
            self.lake_ocid_to_lake_client_map[lake_ocid] = lake_client
        self.lake_ocid_to_lake_sharing_client_map[lake_ocid] = self.get_lake_sharing_client(lake_ocid, lake_client,
                                                                                            **kwargs)
        mount_scope_entity_type: str = None
        mount_scope_schema_key: str = None
        mount_scope_table_key: str = None
        mount_scope_user_id: str = None
        if mount_type == 'MANAGED':
            mount_scope_entity_type = mount_spec_array[1].upper()
            if mount_scope_entity_type == 'DATABASE':
                mount_scope_schema_key = mount_spec_array[2]
            elif mount_scope_entity_type == 'TABLE':
                mount_scope_schema_key = mount_spec_array[2]
                mount_scope_table_key = mount_spec_array[3]
            elif mount_scope_entity_type == 'USER':
                mount_scope_user_id = mount_spec_array[2]
        lake_mount_response = lake_client.get_lakehouse_mount(lake_ocid, mount_name, mount_type,
                                                              mount_scope_entity_type,
                                                              mount_scope_schema_key,
                                                              mount_scope_table_key,
                                                              mount_scope_user_id,
                                                              **kwargs)

        if lake_mount_response.status == 200:
            bucket_namespace_map['namespace'] = lake_mount_response.data.mount_spec.namespace
            bucket_namespace_map['bucket_name'] = lake_mount_response.data.mount_spec.bucket_name
        else:
            raise ValueError('Invalid value given for mountName or lakeOcid.Please check !!!!!!')
        cache_key: str = bucket_namespace_map['namespace'] + '-' + bucket_namespace_map['bucket_name']
        self.bucket_namespace_to_lake_ocid_map[cache_key] = lake_ocid
        return bucket_namespace_map

    def is_lakehouse_managed_bucket(self, namespace_name, bucket_name):
        cache_key: str = namespace_name + '-' + bucket_name
        oci_lake_managed: bool = False
        if self.bucket_namespace_to_lake_ocid_map.get(cache_key) is None:
            return False
        else:
            oci_lake_managed = True
        logger.debug(
            "is_lakehouse_managed"
            " for the given lake namespace:"
            f"{namespace_name} and it's bucket:{bucket_name} is:{oci_lake_managed}"
        )
        return oci_lake_managed

    def abort_multipart_upload(self, namespace_name, bucket_name, object_name, upload_id, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'WRITE', object_name,
                                                            **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName', 'objectName', 'uploadId']
            resource_path = "/p/" + par_hash + "/n/{namespaceName}/b/{bucketName}/u/{objectName}"
            method = "DELETE"
            operation_name = "abort_multipart_upload"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/MultipartUpload/AbortMultipartUpload"

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "opc_client_request_id"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "abort_multipart_upload got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            query_params = {
                "uploadId": upload_id
            }
            query_params = {k: v for (k, v) in six.iteritems(query_params) if v is not missing and v is not None}

            header_params = {
                "accept": "application/json",
                "content-type": "application/json",
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.abort_multipart_upload(self, namespace_name, bucket_name, object_name, upload_id,
                                                              **kwargs)

    def cancel_work_request(self, work_request_id, **kwargs):
        return ObjectStorageClient.cancel_work_request(self, work_request_id, **kwargs)

    def commit_multipart_upload(self, namespace_name, bucket_name, object_name, upload_id,
                                commit_multipart_upload_details, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'WRITE', object_name,
                                                                 **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName', 'objectName', 'uploadId']
            resource_path = "/p/" + par_hash + \
                            "/n/{namespaceName}/b/{bucketName}/u/{objectName}/id/{uploadId}"
            method = "POST"
            operation_name = "commit_multipart_upload"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/MultipartUpload" \
                                 "/CommitMultipartUpload "

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "if_match",
                "if_none_match",
                "opc_client_request_id"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "commit_multipart_upload got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name,
                "uploadId": upload_id
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            query_params = {
                "uploadId": upload_id
            }
            query_params = {k: v for (k, v) in six.iteritems(query_params) if v is not missing and v is not None}

            header_params = {
                "accept": "application/json",
                "content-type": "application/json",
                "if-match": kwargs.get("if_match", missing),
                "if-none-match": kwargs.get("if_none_match", missing),
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    body=commit_multipart_upload_details,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    body=commit_multipart_upload_details,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.commit_multipart_upload(self, namespace_name, bucket_name, object_name,
                                                               upload_id,
                                                               commit_multipart_upload_details, **kwargs)

    def copy_object(self, namespace_name, bucket_name, copy_object_details, **kwargs):
        return ObjectStorageClient.copy_object(self, namespace_name, bucket_name, copy_object_details, **kwargs)

    def create_bucket(self, namespace_name, create_bucket_details, **kwargs):
        return ObjectStorageClient.create_bucket(self, namespace_name, create_bucket_details, **kwargs)

    def create_multipart_upload(self, namespace_name, bucket_name, create_multipart_upload_details, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            object_name = create_multipart_upload_details.object
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'WRITE', object_name,
                                                                 **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName']
            resource_path = "/p/" + par_hash + "/n/{namespaceName}/b/{bucketName}/o/{objectName}"
            method = "PUT"
            operation_name = "create_multipart_upload"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/MultipartUpload" \
                                 "/CreateMultipartUpload "

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "if_match",
                "if_none_match",
                "opc_client_request_id",
                "opc_sse_customer_algorithm",
                "opc_sse_customer_key",
                "opc_sse_customer_key_sha256",
                "opc_sse_kms_key_id"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "create_multipart_upload got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            header_params = {
                "accept": "application/json",
                "content-type": "application/json",
                "opc-multipart": "true",
                "if-match": kwargs.get("if_match", missing),
                "if-none-match": kwargs.get("if_none_match", missing),
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing),
                "opc-sse-customer-algorithm": kwargs.get("opc_sse_customer_algorithm", missing),
                "opc-sse-customer-key": kwargs.get("opc_sse_customer_key", missing),
                "opc-sse-customer-key-sha256": kwargs.get("opc_sse_customer_key_sha256", missing),
                "opc-sse-kms-key-id": kwargs.get("opc_sse_kms_key_id", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    header_params=header_params,
                    body=create_multipart_upload_details,
                    response_type="MultipartUpload",
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    header_params=header_params,
                    body=create_multipart_upload_details,
                    response_type="MultipartUpload",
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.create_multipart_upload(self, namespace_name, bucket_name,
                                                               create_multipart_upload_details, **kwargs)

    def create_preauthenticated_request(self, namespace_name, bucket_name, create_preauthenticated_request_details,
                                        **kwargs):
        return ObjectStorageClient.create_preauthenticated_request(self, namespace_name, bucket_name,
                                                                   create_preauthenticated_request_details,
                                                                   **kwargs)

    def create_replication_policy(self, namespace_name, bucket_name, create_replication_policy_details, **kwargs):
        return ObjectStorageClient.create_replication_policy(self, namespace_name, bucket_name,
                                                             create_replication_policy_details, **kwargs)

    def create_retention_rule(self, namespace_name, bucket_name, create_retention_rule_details, **kwargs):
        return ObjectStorageClient.create_retention_rule(self, namespace_name, bucket_name,
                                                         create_retention_rule_details,
                                                         **kwargs)

    def delete_bucket(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.delete_bucket(self, namespace_name, bucket_name, **kwargs)

    def delete_object(self, namespace_name, bucket_name, object_name, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            return lake_sharing_client.delete_object(namespace_name, bucket_name, object_name, **kwargs)
        else:
            return ObjectStorageClient.delete_object(self, namespace_name, bucket_name, object_name, **kwargs)

    def delete_object_lifecycle_policy(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.delete_object_lifecycle_policy(self, namespace_name, bucket_name, **kwargs)

    def delete_preauthenticated_request(self, namespace_name, bucket_name, par_id, **kwargs):
        return ObjectStorageClient.delete_preauthenticated_request(self, namespace_name, bucket_name, par_id, **kwargs)

    def delete_replication_policy(self, namespace_name, bucket_name, replication_id, **kwargs):
        return ObjectStorageClient.delete_replication_policy(self, namespace_name, bucket_name, replication_id,
                                                             **kwargs)

    def delete_retention_rule(self, namespace_name, bucket_name, retention_rule_id, **kwargs):
        return ObjectStorageClient.delete_retention_rule(self, namespace_name, bucket_name, retention_rule_id, **kwargs)

    def get_bucket(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.get_bucket(self, namespace_name, bucket_name, **kwargs)

    def get_namespace(self, **kwargs):
        return ObjectStorageClient.get_namespace(self, **kwargs)

    def get_namespace_metadata(self, namespace_name, **kwargs):
        return ObjectStorageClient.get_namespace_metadata(self, namespace_name, **kwargs)

    def get_object(self, namespace_name, bucket_name, object_name, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'READ', object_name,
                                                                 **kwargs)
            par_hash = par_response.data.par_hash
            resource_path = "/p/" + par_hash + "/n/{namespaceName}/b/{bucketName}/o/{objectName}"
            required_arguments = ['namespaceName', 'bucketName', 'objectName']
            method = "GET"
            operation_name = "get_object"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/Object/GetObject"

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "version_id",
                "if_match",
                "if_none_match",
                "opc_client_request_id",
                "range",
                "opc_sse_customer_algorithm",
                "opc_sse_customer_key",
                "opc_sse_customer_key_sha256",
                "http_response_content_disposition",
                "http_response_cache_control",
                "http_response_content_type",
                "http_response_content_language",
                "http_response_content_encoding",
                "http_response_expires"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "get_object got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            query_params = {
                "versionId": kwargs.get("version_id", missing),
                "httpResponseContentDisposition": kwargs.get("http_response_content_disposition", missing),
                "httpResponseCacheControl": kwargs.get("http_response_cache_control", missing),
                "httpResponseContentType": kwargs.get("http_response_content_type", missing),
                "httpResponseContentLanguage": kwargs.get("http_response_content_language", missing),
                "httpResponseContentEncoding": kwargs.get("http_response_content_encoding", missing),
                "httpResponseExpires": kwargs.get("http_response_expires", missing)
            }
            query_params = {k: v for (k, v) in six.iteritems(query_params) if v is not missing and v is not None}

            header_params = {
                "accept": "application/json",
                "content-type": "application/json",
                "if-match": kwargs.get("if_match", missing),
                "if-none-match": kwargs.get("if_none_match", missing),
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing),
                "range": kwargs.get("range", missing),
                "opc-sse-customer-algorithm": kwargs.get("opc_sse_customer_algorithm", missing),
                "opc-sse-customer-key": kwargs.get("opc_sse_customer_key", missing),
                "opc-sse-customer-key-sha256": kwargs.get("opc_sse_customer_key_sha256", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="stream",
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="stream",
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.get_object(self, namespace_name, bucket_name, object_name, **kwargs)

    def get_object_lifecycle_policy(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.get_object_lifecycle_policy(self, namespace_name, bucket_name, **kwargs)

    def get_preauthenticated_request(self, namespace_name, bucket_name, par_id, **kwargs):
        return ObjectStorageClient.get_preauthenticated_request(self, namespace_name, bucket_name, par_id, **kwargs)

    def get_replication_policy(self, namespace_name, bucket_name, replication_id, **kwargs):
        return ObjectStorageClient.get_replication_policy(self, namespace_name, bucket_name, bucket_name,
                                                          **kwargs)

    def get_retention_rule(self, namespace_name, bucket_name, retention_rule_id, **kwargs):
        return ObjectStorageClient.get_retention_rule(self, namespace_name, bucket_name, retention_rule_id, **kwargs)

    def get_work_request(self, work_request_id, **kwargs):
        return ObjectStorageClient.get_work_request(self, work_request_id, **kwargs)

    def head_bucket(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.head_bucket(self, namespace_name, bucket_name, **kwargs)

    def head_object(self, namespace_name, bucket_name, object_name, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'READ', object_name,
                                                                 **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName', 'objectName']
            resource_path = "/p/" + par_hash + "/n/{namespaceName}/b/{bucketName}/o/{objectName}"
            method = "HEAD"
            operation_name = "head_object"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/Object/HeadObject"

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "version_id",
                "if_match",
                "if_none_match",
                "opc_client_request_id",
                "opc_sse_customer_algorithm",
                "opc_sse_customer_key",
                "opc_sse_customer_key_sha256"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "head_object got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            query_params = {
                "versionId": kwargs.get("version_id", missing)
            }
            query_params = {k: v for (k, v) in six.iteritems(query_params) if v is not missing and v is not None}

            header_params = {
                "accept": "application/json",
                "content-type": "application/json",
                "if-match": kwargs.get("if_match", missing),
                "if-none-match": kwargs.get("if_none_match", missing),
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing),
                "opc-sse-customer-algorithm": kwargs.get("opc_sse_customer_algorithm", missing),
                "opc-sse-customer-key": kwargs.get("opc_sse_customer_key", missing),
                "opc-sse-customer-key-sha256": kwargs.get("opc_sse_customer_key_sha256", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)

        else:
            return ObjectStorageClient.head_object(self, namespace_name, bucket_name, object_name, **kwargs)

    def list_buckets(self, namespace_name, compartment_id, **kwargs):
        return ObjectStorageClient.list_buckets(self, namespace_name, compartment_id, **kwargs)

    def list_multipart_upload_parts(self, namespace_name, bucket_name, object_name, upload_id, **kwargs):
        return ObjectStorageClient.list_multipart_upload_parts(self, namespace_name, bucket_name,
                                                               object_name, upload_id, **kwargs)

    def list_multipart_uploads(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.list_multipart_uploads(self, namespace_name, bucket_name, **kwargs)

    def list_object_versions(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.list_object_versions(self, namespace_name, bucket_name, **kwargs)

    def list_objects(self, namespace_name, bucket_name, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'READ', None, **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName']
            resource_path = "/p/" + par_hash + "/n/{namespaceName}/b/{bucketName}/o"
            method = "GET"
            operation_name = "list_objects"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/Object/ListObjects"

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "prefix",
                "start",
                "end",
                "limit",
                "delimiter",
                "fields",
                "opc_client_request_id",
                "start_after"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "list_objects got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            query_params = {
                "prefix": kwargs.get("prefix", missing),
                "start": kwargs.get("start", missing),
                "end": kwargs.get("end", missing),
                "limit": kwargs.get("limit", missing),
                "delimiter": kwargs.get("delimiter", missing),
                "fields": kwargs.get("fields", missing),
                "startAfter": kwargs.get("start_after", missing)
            }
            query_params = {k: v for (k, v) in six.iteritems(query_params) if v is not missing and v is not None}

            header_params = {
                "accept": "application/json",
                "content-type": "application/json",
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="ListObjects",
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    response_type="ListObjects",
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.list_objects(self, namespace_name, bucket_name, **kwargs)

    def list_preauthenticated_requests(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.list_preauthenticated_requests(self, namespace_name, bucket_name, **kwargs)

    def list_replication_policies(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.list_replication_policies(self, namespace_name, bucket_name, **kwargs)

    def list_replication_sources(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.list_replication_sources(self, namespace_name, bucket_name, **kwargs)

    def list_retention_rules(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.list_retention_rules(self, namespace_name, bucket_name, **kwargs)

    def list_work_request_errors(self, work_request_id, **kwargs):
        return ObjectStorageClient.list_work_request_errors(self, work_request_id, **kwargs)

    def list_work_request_logs(self, work_request_id, **kwargs):
        return ObjectStorageClient.list_work_request_logs(self, work_request_id, **kwargs)

    def list_work_requests(self, compartment_id, **kwargs):
        return ObjectStorageClient.list_work_requests(self, compartment_id, **kwargs)

    def make_bucket_writable(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.make_bucket_writable(self, namespace_name, bucket_name, **kwargs)

    def put_object(self, namespace_name, bucket_name, object_name, put_object_body, **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'WRITE', object_name,
                                                                 **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName', 'objectName']
            resource_path = "/p/" + par_hash + "/n/{namespaceName}/b/{bucketName}/o/{objectName}"
            method = "PUT"
            operation_name = "put_object"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/Object/PutObject"
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "buffer_limit",
                "content_length",
                "if_match",
                "if_none_match",
                "opc_client_request_id",
                "expect",
                "content_md5",
                "content_type",
                "content_language",
                "content_encoding",
                "content_disposition",
                "cache_control",
                "opc_sse_customer_algorithm",
                "opc_sse_customer_key",
                "opc_sse_customer_key_sha256",
                "opc_sse_kms_key_id",
                "storage_tier",
                "opc_meta"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "put_object got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            header_params = {
                "accept": "application/json",
                "if-match": kwargs.get("if_match", missing),
                "if-none-match": kwargs.get("if_none_match", missing),
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing),
                "Expect": kwargs.get("expect", missing),
                "Content-Length": kwargs.get("content_length", missing),
                "Content-MD5": kwargs.get("content_md5", missing),
                "Content-Type": kwargs.get("content_type", missing),
                "Content-Language": kwargs.get("content_language", missing),
                "Content-Encoding": kwargs.get("content_encoding", missing),
                "Content-Disposition": kwargs.get("content_disposition", missing),
                "Cache-Control": kwargs.get("cache_control", missing),
                "opc-sse-customer-algorithm": kwargs.get("opc_sse_customer_algorithm", missing),
                "opc-sse-customer-key": kwargs.get("opc_sse_customer_key", missing),
                "opc-sse-customer-key-sha256": kwargs.get("opc_sse_customer_key_sha256", missing),
                "opc-sse-kms-key-id": kwargs.get("opc_sse_kms_key_id", missing),
                "storage-tier": kwargs.get("storage_tier", missing),

            }
            for key, value in six.iteritems(kwargs.get("opc_meta", {})):
                header_params["opc-meta-" + key] = value
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}
            # Set default value for expect header if user has not overridden it
            lowercase_header_params_keys = [k.lower() for k in header_params]
            if "expect" not in lowercase_header_params_keys:
                header_params["expect"] = "100-continue"
            try:
                put_object_body
            except NameError:
                put_object_body = kwargs.get("put_object_body", missing)

            if put_object_body is not missing and put_object_body is not None:
                if (not isinstance(put_object_body, (six.binary_type, six.string_types)) and
                        not hasattr(put_object_body, "read")):
                    raise TypeError('The body must be a string, bytes, or provide a read() method.')

                if hasattr(put_object_body, 'fileno') and hasattr(put_object_body,
                                                                  'name') and put_object_body.name != '<stdin>':
                    if requests.utils.super_len(put_object_body) == 0:
                        header_params['Content-Length'] = '0'
                elif 'Content-Length' not in header_params and not is_content_length_calculable_by_req_util(
                        put_object_body):
                    calculated_obj = back_up_body_calculate_stream_content_length(put_object_body,
                                                                                  kwargs.get("buffer_limit"))
                    header_params['Content-Length'] = calculated_obj["content_length"]
                    put_object_body = calculated_obj["byte_content"]

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    header_params=header_params,
                    body=put_object_body,
                    enforce_content_headers=False,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    header_params=header_params,
                    body=put_object_body,
                    enforce_content_headers=False,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.put_object(self, namespace_name, bucket_name, object_name, put_object_body,
                                                  **kwargs)

    def put_object_lifecycle_policy(self, namespace_name, bucket_name, put_object_lifecycle_policy_details, **kwargs):
        return ObjectStorageClient.put_object_lifecycle_policy(self, namespace_name, bucket_name,
                                                               put_object_lifecycle_policy_details, **kwargs)

    def reencrypt_bucket(self, namespace_name, bucket_name, **kwargs):
        return ObjectStorageClient.reencrypt_bucket(self, namespace_name, bucket_name, **kwargs)

    def reencrypt_object(self, namespace_name, bucket_name, object_name, reencrypt_object_details, **kwargs):
        return ObjectStorageClient.reencrypt_object(self, namespace_name, bucket_name, object_name,
                                                    reencrypt_object_details, **kwargs)

    def rename_object(self, namespace_name, bucket_name, rename_object_details, **kwargs):
        return ObjectStorageClient.rename_object(self, namespace_name, bucket_name, rename_object_details,
                                                 **kwargs)

    def restore_objects(self, namespace_name, bucket_name, restore_objects_details, **kwargs):
        return ObjectStorageClient.restore_objects(self, namespace_name, bucket_name, restore_objects_details,
                                                   **kwargs)

    def update_bucket(self, namespace_name, bucket_name, update_bucket_details, **kwargs):
        return ObjectStorageClient.update_bucket(self, namespace_name, bucket_name,
                                                 update_bucket_details, **kwargs)

    def update_namespace_metadata(self, namespace_name, update_namespace_metadata_details, **kwargs):
        return ObjectStorageClient.update_namespace_metadata(self, namespace_name, update_namespace_metadata_details,
                                                             **kwargs)

    def update_object_storage_tier(self, namespace_name, bucket_name, update_object_storage_tier_details, **kwargs):
        return ObjectStorageClient.update_object_storage_tier(self, namespace_name, bucket_name,
                                                              update_object_storage_tier_details, **kwargs)

    def update_retention_rule(self, namespace_name, bucket_name, retention_rule_id, update_retention_rule_details,
                              **kwargs):
        return ObjectStorageClient.update_retention_rule(self, namespace_name, bucket_name, retention_rule_id,
                                                         update_retention_rule_details,
                                                         **kwargs)

    def upload_part(self, namespace_name, bucket_name, object_name, upload_id, upload_part_num, upload_part_body,
                    **kwargs):
        oci_lake_managed_by_bucket = self.is_lakehouse_managed_bucket(namespace_name, bucket_name)
        if oci_lake_managed_by_bucket:
            lake_sharing_client = self.get_lake_sharing_client_by_bucket_namespace(namespace_name, bucket_name)
            par_response = lake_sharing_client.generate_par(namespace_name, bucket_name, 'WRITE', object_name,
                                                                 **kwargs)
            par_hash = par_response.data.par_hash
            required_arguments = ['namespaceName', 'bucketName', 'objectName', 'uploadId', 'uploadPartNum']
            resource_path = "/p/" + par_hash + \
                            "/n/{namespaceName}/b/{bucketName}/u/{objectName}/id/{uploadId}/{uploadPartNum}"
            method = "PUT"
            operation_name = "upload_part"
            api_reference_link = "https://docs.oracle.com/iaas/api/#/en/objectstorage/20160918/MultipartUpload" \
                                 "/UploadPart "

            # Don't accept unknown kwargs
            expected_kwargs = [
                "allow_control_chars",
                "retry_strategy",
                "buffer_limit",
                "content_length",
                "opc_client_request_id",
                "if_match",
                "if_none_match",
                "expect",
                "content_md5",
                "opc_sse_customer_algorithm",
                "opc_sse_customer_key",
                "opc_sse_customer_key_sha256",
                "opc_sse_kms_key_id"
            ]
            extra_kwargs = [_key for _key in six.iterkeys(kwargs) if _key not in expected_kwargs]
            if extra_kwargs:
                raise ValueError(
                    "upload_part got unknown kwargs: {!r}".format(extra_kwargs))

            path_params = {
                "namespaceName": namespace_name,
                "bucketName": bucket_name,
                "objectName": object_name,
                "uploadId": upload_id,
                "uploadPartNum": upload_part_num,
            }

            path_params = {k: v for (k, v) in six.iteritems(path_params) if v is not missing}

            for (k, v) in six.iteritems(path_params):
                if v is None or (isinstance(v, six.string_types) and len(v.strip()) == 0):
                    raise ValueError('Parameter {} cannot be None, whitespace or empty string'.format(k))

            query_params = {
                "uploadId": upload_id,
                "uploadPartNum": upload_part_num
            }
            query_params = {k: v for (k, v) in six.iteritems(query_params) if v is not missing and v is not None}

            header_params = {
                "accept": "application/json",
                "opc-multipart": "true",
                "opc-client-request-id": kwargs.get("opc_client_request_id", missing),
                "if-match": kwargs.get("if_match", missing),
                "if-none-match": kwargs.get("if_none_match", missing),
                "Expect": kwargs.get("expect", missing),
                "Content-Length": kwargs.get("content_length", missing),
                "Content-MD5": kwargs.get("content_md5", missing),
                "opc-sse-customer-algorithm": kwargs.get("opc_sse_customer_algorithm", missing),
                "opc-sse-customer-key": kwargs.get("opc_sse_customer_key", missing),
                "opc-sse-customer-key-sha256": kwargs.get("opc_sse_customer_key_sha256", missing),
                "opc-sse-kms-key-id": kwargs.get("opc_sse_kms_key_id", missing)
            }
            header_params = {k: v for (k, v) in six.iteritems(header_params) if v is not missing and v is not None}
            lowercase_header_params_keys = [k.lower() for k in header_params]
            if "expect" not in lowercase_header_params_keys:
                header_params["expect"] = "100-continue"

            try:
                upload_part_body
            except NameError:
                upload_part_body = kwargs.get("upload_part_body", missing)

            if upload_part_body is not missing and upload_part_body is not None:
                if (not isinstance(upload_part_body, (six.binary_type, six.string_types)) and
                        not hasattr(upload_part_body, "read")):
                    raise TypeError('The body must be a string, bytes, or provide a read() method.')

                if hasattr(upload_part_body, 'fileno') and hasattr(upload_part_body,
                                                                   'name') and upload_part_body.name != '<stdin>':
                    if requests.utils.super_len(upload_part_body) == 0:
                        header_params['Content-Length'] = '0'

                elif 'Content-Length' not in header_params and not is_content_length_calculable_by_req_util(
                        upload_part_body):
                    calculated_obj = back_up_body_calculate_stream_content_length(upload_part_body,
                                                                                  kwargs.get("buffer_limit"))
                    header_params['Content-Length'] = calculated_obj["content_length"]
                    upload_part_body = calculated_obj["byte_content"]

            retry_strategy = self.base_client.get_preferred_retry_strategy(
                operation_retry_strategy=kwargs.get('retry_strategy'),
                client_retry_strategy=self.retry_strategy
            )
            if retry_strategy is None:
                retry_strategy = retry.DEFAULT_RETRY_STRATEGY

            if retry_strategy:
                if not isinstance(retry_strategy, retry.NoneRetryStrategy):
                    self.base_client.add_opc_client_retries_header(header_params)
                    retry_strategy.add_circuit_breaker_callback(self.circuit_breaker_callback)
                return retry_strategy.make_retrying_call(
                    self.base_client.call_api,
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    body=upload_part_body,
                    enforce_content_headers=False,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
            else:
                return self.base_client.call_api(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    body=upload_part_body,
                    enforce_content_headers=False,
                    allow_control_chars=kwargs.get('allow_control_chars'),
                    operation_name=operation_name,
                    api_reference_link=api_reference_link,
                    required_arguments=required_arguments)
        else:
            return ObjectStorageClient.upload_part(self, namespace_name, bucket_name, object_name, upload_id,
                                                   upload_part_num, upload_part_body,
                                                   **kwargs)
