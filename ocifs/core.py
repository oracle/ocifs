# coding: utf-8
# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/
import importlib
import os
from ast import literal_eval
import inspect
import logging
from typing import Union  # pragma: no cover

from fsspec import AbstractFileSystem
from fsspec.utils import tokenize, stringify_path
from fsspec.spec import AbstractBufferedFile

from oci.signer import AbstractBaseSigner
from oci.auth.signers import (
    get_resource_principals_signer,
    InstancePrincipalsSecurityTokenSigner,
)
from oci.config import DEFAULT_PROFILE, from_file, DEFAULT_LOCATION
from oci.exceptions import ServiceError, ConfigFileNotFound

from oci.object_storage.models import (
    CreateBucketDetails,
    CommitMultipartUploadDetails,
    CreateMultipartUploadDetails,
    CopyObjectDetails,
)
from oci.pagination import list_call_get_all_results
from oci.retry import DEFAULT_RETRY_STRATEGY
from oci._vendor.requests.structures import CaseInsensitiveDict
from .errors import translate_oci_error
from .lake_sharing_object_storage_client import LakeSharingObjectStorageClient
from .utils import __version__

logger = logging.getLogger("ocifs")


def setup_logging(level=None):
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
    setup_logging()

IAM_POLICIES = {"api_key", "resource_principal", "instance_principal", "unknown_signer"}


def get_mount_type(mount_spec):
    mount_type: str = None
    if len(mount_spec) == 1:
        mount_type = "EXTERNAL"
    elif 3 <= len(mount_spec) <= 4:
        mount_entity_type = mount_spec[1].upper()
        if mount_entity_type == 'DATABASE' or mount_entity_type == 'TABLE' or mount_entity_type == 'USER':
            mount_type = "MANAGED"
    return mount_type


def _get_valid_oci_detail_methods(func):
    func_attrs = dir(func)

    def is_parameter_kwarg(param_name):
        return (param_name[0] != "_") and not param_name.isupper()

    first_param_idx = next(
        (i for i, x in enumerate(func_attrs) if is_parameter_kwarg(x)), None
    )
    relevant_args = func_attrs[first_param_idx:]
    return relevant_args


def _validate_kwargs(func, kwargs, is_detail_method=False):
    """
    Helper method to check kwargs are valid for a given function
    """
    if not is_detail_method:
        valid_params = inspect.signature(func).parameters
        if "kwargs" in valid_params:
            return kwargs
    else:
        valid_params = _get_valid_oci_detail_methods(func)
    return {k: v for k, v in kwargs.items() if k in valid_params}


def _build_full_path(bucket, namespace, key=None, **kwargs):
    """
    This method is used internally to build consistent cache keys
    """
    if key:
        return f"{bucket}@{namespace}/{key}"
    return f"{bucket}@{namespace}"


class OCIFileSystem(AbstractFileSystem):
    """Access oci as if it were a file system.

    This exposes a filesystem-like API (ls, cp, open, etc.) on top of oci
    object storage.

    Parameters
    ----------
    config : Union[dict, str, None]
        Config for the connection to OCI.
        If a dict, it should be returned from oci.config.from_file
        If a str, it should be the location of the config file
        If None, user should have a Resource Principal configured environment
        If Resource Principal is not available, Instance Principal
    signer : oci.auth.signers
        A signer from the OCI sdk. More info: oci.auth.signers
    profile : str
        The profile to use from the config (If the config is passed in)
    iam_type : str (None)
        The IAM Auth principal type to use.
        Values can be one of ["api_key", "resource_principal", "instance_principal"]
    region : str (None)
        The Region Identifier that the client should connnect to.
        Regions can be found here:
        https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm
    default_block_size : int (None)
        If given, the default block size value used for ``open()``, if no
        specific value is given at all time. The built-in default is 5MB.
    config_kwargs : dict
        dict of parameters passed to the OCI Client upon connection
        more info here: oci.object_storage.ObjectStorageClient.__init__
    oci_additional_kwargs : dict
        dict of parameters that are used when calling oci api
        methods. Typically used for things like "retry_strategy".
    kwargs : dict
        dict of other parameters for oci session
        This includes default parameters for tenancy, namespace, and region
        Any other parameters are passed along to AbstractFileSystem's init method.
    """

    root_marker = ""
    connect_timeout = 5
    read_timeout = 15
    default_block_size = 5 * 2 ** 20
    protocol = ["oci", "ocilake"]

    def __init__(
            self,
            config: Union[dict, str, None] = None,
            signer: Union[AbstractBaseSigner, None] = None,
            profile: str = None,
            iam_type: str = None,
            region: str = None,
            default_block_size: int = None,
            default_cache_type: str = "bytes",
            default_cache_options: dict = None,
            config_kwargs: dict = None,
            oci_additional_kwargs: dict = None,
            **kwargs,
    ):
        self.kwargs = kwargs or dict()
        self.default_block_size = default_block_size or self.default_block_size
        self.oci_additional_kwargs = oci_additional_kwargs or dict()
        self.config_kwargs = config_kwargs or dict()
        self.config = config or dict()
        logger.debug(
            f"External Object Storage Client is being set up using the config "
            f"passed in:: {self.config} "
        )
        self._signer = signer
        self.profile = profile
        self._iam_type = iam_type
        self.oci_client = None
        self.region = region
        self.default_tenancy = None
        self.default_namespace = None
        self.connect()
        super().__init__(**kwargs)
        self.default_cache_options = default_cache_options
        self.default_cache_type = default_cache_type

    def _get_oci_method_kwargs(
            self, method, is_detail_method=False, *akwarglist, **kwargs
    ):
        """
        This method handles combining and resolving conflicts between all of the args and
        kwargs. The highest priority arguments are in `kwargs`. If the desired argument is
        not found in `kwargs`, then we will look in `akwarglist`. If the desired argument
        is not found in `kwargs` or `akwarglist`, then we will look in
        `oci_additional_kwargs`.

        This means that in calling a method, you needn't use
        arg=kwargs.get("arg", default_arg), as this will be done automatically.
        """
        additional_kwargs = self.oci_additional_kwargs.copy()
        for arg in akwarglist:
            additional_kwargs.update(arg)
        # Add the normal kwargs in
        additional_kwargs.update(kwargs)
        # filter all kwargs
        return _validate_kwargs(
            method, additional_kwargs, is_detail_method=is_detail_method
        )

    def _call_oci(self, method, is_detail_method=False, *akwarglist, **kwargs):
        """
        Helper method to call a method on the object storage client and wrap any errors
        """
        additional_kwargs = self._get_oci_method_kwargs(
            method, is_detail_method=is_detail_method, *akwarglist, **kwargs
        )
        logger.debug("CALL: %s - %s" % (method.__name__, additional_kwargs))
        try:
            return method(**additional_kwargs)
        except Exception as e:
            if str(getattr(e, "code", "")) in ["401", "402", "403"]:
                self.connect(refresh=True)
                return method(**additional_kwargs)
            raise e

    def sync(self, src_dir, dest_dir, **kwargs):
        """
        The `sync` method is a bulk copy where one location is local and the other is OCI Object Storage.
        `sync` wraps the functionality of the oci cli method by the same name: https://docs.oracle.com/en-us/iaas/tools/oci-cli/3.22.4/oci_cli_docs/cmdref/os/object/sync.html
        `sync` specifically handles the case where one file is local and the other is remote. If both are local use `os.copy`, if both are remote use `OCIFileSystem.copy`

        Parameters
        ----------
        src_dir: str
            The source of the data you want to copy.
            Either a local or oci object storage path.
            If oci object storage path, you must include the oci:// prefix
        dest_dir: str
            The destination where you want to put the data.
            Must be a local path if src_dir is an oci object storage path, and vice versa.
            If oci object storage path, you must include the oci:// prefix
        kwargs:
            Any additional args you want to send to the sync method.
            List of all args/kwargs here: https://docs.oracle.com/en-us/iaas/tools/oci-cli/3.22.4/oci_cli_docs/cmdref/os/object/sync.html
        """
        import subprocess
        import pkg_resources

        assert (
                "oci-cli" in pkg_resources.working_set.by_key.keys()
        ), "Must download oci-cli to use sync: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#Quickstart"

        if self.is_local_path(src_dir):
            if self.is_local_path(dest_dir):
                raise ValueError(
                    "Detected both src_dir and dest_dir as local paths. If both are local, please use `os.copy`. If one is remote, please specify by prefixing it with `oci://`"
                )
            bucket, namespace, obj_path = self.split_path(dest_dir)
            return subprocess.run(
                [
                    "oci",
                    "os",
                    "object",
                    "sync",
                    "-bn",
                    bucket,
                    "-ns",
                    namespace,
                    "--prefix",
                    obj_path,
                    "--src-dir",
                    src_dir,
                ]
            )
        elif self.is_local_path(dest_dir):
            bucket, namespace, obj_path = self.split_path(src_dir)
            return subprocess.run(
                [
                    "oci",
                    "os",
                    "object",
                    "sync",
                    "-bn",
                    bucket,
                    "-ns",
                    namespace,
                    "--prefix",
                    obj_path,
                    "--dest-dir",
                    dest_dir,
                ]
            )
        else:
            logger.warn(
                "Detected both src_dir and dest_dir as object storage paths. Passing call to the `copy` method."
            )
            return self.copy(path1=src_dir, path2=dest_dir, **kwargs)

    def is_local_path(self, path):
        return path[:6] != "oci://"

    def split_path(self, path, **kwargs):
        """Normalise OCI path string into bucket and key.
        Parameters
        ----------
        path : string
            Input path, like `oci://mybucket@mynamespace/path/to/file`
            or
            Input path(External Mount), like `ocilake://mountname@lakeocid/path/to/file`
            or
            Input path(DB Mount), like `ocilake://mountname:database:db1@lakeocid/path/to/file`
            or
            Input path(Table Mount), like `ocilake://mountname:table:db1:tbl1@lakeocid/path/to/file`
             or
            Input path(User Mount), like `ocilake://mountname:user:userOcid@lakeocid/path/to/file`
        Examples
        --------
        >>> split_path("oci://mybucket@mynamespace/path/to/file")
        ['mybucket', 'mynamespace', 'path/to/file']
        >>> split_path("ocilake://mountname@lakeocid/path/to/file")
        ['mybucket', 'mynamespace', 'path/to/file']
        >>> split_path("ocilake://mountname:datbase:db1@lakeocid/path/to/file")
        ['mybucket', 'mynamespace', 'path/to/file']
        >>> split_path("ocilake://mountname:table:db1:tbl1@lakeocid/path/to/file")
        ['mybucket', 'mynamespace', 'path/to/file']
        >>> split_path("ocilake://mountname:user:userid@lakeocid/path/to/file")
        ['mybucket', 'mynamespace', 'path/to/file']
        """
        lake_ocid = None
        path_sans_protocol = self._strip_protocol(path)
        full_bucket, _, obj_path = path_sans_protocol.partition("/")
        # Added the below check for lake support
        if "@ocid1.lake" in full_bucket:
            mount_name, _, lake_ocid = full_bucket.partition("@")
            mount_spc_information = mount_name.split(":")
            mount_type = get_mount_type(mount_spc_information)
            logger.debug(f"mount_type:: {mount_type}")
            if not mount_type:
                raise ValueError('mount path mentioned in ocifs URI is invalid.Please check the URI format!!!')
            bucket_namespace_map = self.oci_client.get_bucket_namespace_for_given_mount_name(lake_ocid,
                                                                                             mount_spc_information,
                                                                                             mount_type,
                                                                                             **kwargs)
            bucket = bucket_namespace_map.get("bucket_name")
            namespace = bucket_namespace_map.get("namespace")
        else:
            bucket, _, namespace = full_bucket.partition("@")
        if not namespace:
            namespace = self._get_default_namespace()
        obj_path = obj_path.rstrip("/")
        return bucket, namespace, obj_path

    def connect(self, refresh=True):
        """Establish oci connection object.

        Parameters
        ----------
        refresh : bool
            Whether to create new session/client, even if a previous one with
            the same parameters already exists. If False (default), an
            existing one will be used if possible.

        """
        logger.debug("Setting up OCI Connection.")
        if refresh is False:
            return self.oci_client

        self._determine_iam_auth()

        logger.debug(
            f"Object Storage Client is being set up using IAM type: {self._iam_type}."
        )
        self._update_service_endpoint()
        self._update_retry_strategy()
        self._refresh_signer()
        self.config.update(
            {"additional_user_agent": f"Oracle-ocifs/version={__version__}"}
        )
        self._get_region()
        try:
            self.oci_client = LakeSharingObjectStorageClient(self.config, **self.config_kwargs)
            logger.debug(
                f"Lakesharing Object Storage Client is being set up for supporting data lake support and "
                f"interacting with object storage using the config passed in: {self.config}"
            )
        except Exception as e:
            logger.error(
                "Exception encountered when attempting to initialize the Lakesharing Object Storage Client"
                " using the config:{self.config}"
            )
            raise e
        return self.oci_client

    def invalidate_cache(self, path=None):
        """Deletes the filesystem cache.

        Parameters
        ----------
        path : str (optional)
            The directory from which to clear. If not specificed, deleted entire cache.

        """
        if path is None:
            self.dircache.clear()
        else:
            path = self._strip_protocol(path)
            self.dircache.pop(path, None)
            self.dircache.pop(self._parent(path), None)

    def _lsbuckets(self, namespace: str, refresh=False, compartment_id=None, **kwargs):
        if f"@{namespace}" not in self.dircache or refresh:
            try:
                comp_id = (
                    compartment_id
                    if compartment_id
                    else kwargs.pop("compartment_id", self._get_default_tenancy())
                )
                relevant_kwargs = self._get_oci_method_kwargs(
                    self.oci_client.list_buckets,
                    namespace_name=namespace,
                    compartment_id=comp_id,
                    fields=["tags"],
                    **kwargs,
                )
                logger.debug("Get directory listing page for namespace %s" % namespace)
                files = list_call_get_all_results(
                    self.oci_client.list_buckets, **relevant_kwargs
                ).data
            except ServiceError as e:
                raise translate_oci_error(e) from e

            new_files = []
            for f in files:
                new_files.append(
                    CaseInsensitiveDict(
                        {
                            "size": 0,
                            "type": "directory",
                            "name": f"{f.name}@{f.namespace}",
                            "timeCreated": f.time_created,
                            "compartmentId": f.compartment_id,
                            "createdBy": f.created_by,
                            "definedTags": f.defined_tags,
                            "etag": f.etag,
                            "freeformTags": f.freeform_tags,
                            "namespace": f.namespace,
                        }
                    )
                )
            self.dircache[f"@{namespace}"] = new_files
            return new_files
        return self.dircache[f"@{namespace}"]

    def _lsdir(self, path: str, refresh: bool = False, **kwargs):
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        full_bucket_name = _build_full_path(bucket=bucket, namespace=namespace)
        prefix = key + "/" if key else ""
        if path not in self.dircache or refresh:
            try:
                relevant_kwargs = self._get_oci_method_kwargs(
                    self.oci_client.list_objects,
                    namespace_name=namespace,
                    bucket_name=bucket,
                    prefix=prefix,
                    delimiter="/",
                    fields=kwargs.pop(
                        "fields",
                        "name,size,etag,timeCreated,md5,"
                        "timeModified,storageTier,"
                        "archivalState",
                    ),
                    **kwargs,
                )
                logger.debug("Get directory listing page for %s" % path)
                results = list_call_get_all_results(
                    self.oci_client.list_objects, **relevant_kwargs
                ).data

                formatted_files = []
                for f in results.objects:
                    # ODSC-38899: phantom files get created, named the same as subdir
                    if f.name.endswith("/") and f.size == 0:
                        continue
                    new_key = os.path.join(full_bucket_name, f.name)
                    formatted_files.append(
                        CaseInsensitiveDict(
                            {
                                "name": new_key,
                                "type": "file",
                                "size": f.size,
                                "etag": f.etag,
                                "md5": f.md5,
                                "timeCreated": f.time_created,
                                "timeModified": f.time_modified,
                                "storageTier": f.storage_tier,
                                "archivalState": f.archival_state,
                            }
                        )
                    )
                for p in results.prefixes:
                    folder_name = p[:-1] if p.endswith("/") else p
                    full_folder_name = os.path.join(full_bucket_name, folder_name)
                    formatted_files.append(
                        CaseInsensitiveDict(
                            {
                                "name": full_folder_name,
                                "type": "directory",
                                "size": 0,
                            }
                        )
                    )
                self.dircache[path] = formatted_files
                return formatted_files
            except ServiceError as e:
                raise translate_oci_error(e) from e
        return self.dircache[path]

    def _ls(self, path: str, refresh: bool = False, **kwargs):
        """List files in given bucket, or list of buckets.
        Listing is cached unless `refresh=True`.
        Parameters
        ----------
        path : string/bytes
            location at which to list files
        refresh : bool (=False)
            if False, look in local cache for file details first
        """
        bucket, namespace, _ = self.split_path(path)
        if not bucket:
            return self._lsbuckets(namespace=namespace, refresh=refresh, **kwargs)
        else:
            return self._lsdir(path=path, refresh=refresh, **kwargs)

    def ls(self, path: str, detail: bool = False, refresh: bool = False, **kwargs):
        """List single "directory" with or without details

        Parameters
        ----------
        path : string/bytes
            location at which to list files
        detail : bool (=False)
            if True, each list item is a dict of file properties;
            otherwise, returns list of filenames
        refresh : bool (=False)
            if False, look in local cache for file details first
        kwargs : dict
            additional arguments passed on

        """
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        files = self._ls(path=path, refresh=refresh, **kwargs)
        if not files:
            files = self._ls(path=self._parent(path), refresh=refresh, **kwargs)
            files = [
                o
                for o in files
                if o["name"].rstrip("/") == path and o["type"] != "directory"
            ]
        if detail:
            return files
        else:
            return list(sorted(set([f["name"] for f in files])))

    def touch(self, path: str, truncate: bool = True, data=None, **kwargs):
        """Create empty file or truncate

        Parameters
        ----------
        path : string/bytes
            location at which to list files
        truncate : bool (=True)
            if True, delete the existing file, replace with empty file
        data : bool
            if provided, writes this content to the file
        kwargs : dict
            additional arguments passed on

        """
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        assert isinstance(truncate, bool), "The truncate argument must be of type bool."
        if not truncate and self.exists(path):
            raise ValueError("OCI does not support touching existent files")
        if not key:
            raise ValueError(
                f"The path {path} seems to be a new bucket. We do not support creating "
                "buckets with touch"
            )
        try:
            self._call_oci(
                self.oci_client.put_object,
                namespace_name=namespace,
                bucket_name=bucket,
                object_name=key,
                put_object_body=data,
                **kwargs,
            )
        except ServiceError as e:
            raise translate_oci_error(e) from e
        self.invalidate_cache(self._parent(path))

    def checksum(self, path, **kwargs):
        """Unique value for current version of file

        If the checksum is the same from one moment to another, the contents
        are guaranteed to be the same. If the checksum changes, the contents
        *might* have changed.

        Parameters
        ----------
        path : string/bytes
            path of file to get checksum for
        refresh : bool (=False)
            if False, look in local cache for file details first
        """
        info = self.info(path)
        return int(info.get("etag", tokenize(info)).replace("-", ""), 16)

    def copy_basic(self, path1, path2, destination_region=None, **kwargs):
        """Copy file between locations on OCI

        Not allowed where the origin is >50GB

        Parameters
        ----------
        path1 : str
            URI of source data
        path2 : str
            URI of destination data
        destination_region : str
            the region you want path2 to be written in
            (defaults region of your config)

        """
        bucket1, namespace1, key1 = self.split_path(path1)
        bucket2, namespace2, key2 = self.split_path(path2)
        path2 = _build_full_path(
            bucket=bucket2, namespace=namespace2, key=key2, **kwargs
        )

        total_kwargs = self.oci_additional_kwargs.copy()
        total_kwargs.update(kwargs)

        # OCI SDK will throw an error if the kwarg is not expected, so we need to
        # explicitly grab them for now.
        dest_region = destination_region or self.region
        if not dest_region:
            raise ValueError(
                "No region specified. Please set the 'region' parameter in the kwargs."
            )
        try:
            copy_src = self._call_oci(
                CopyObjectDetails,
                is_detail_method=True,
                source_object_name=key1,
                destination_region=dest_region,
                destination_namespace=namespace2,
                destination_bucket=bucket2,
                destination_object_name=key2,
                **kwargs,
            )
            self._call_oci(
                self.oci_client.copy_object,
                namespace_name=namespace1,
                bucket_name=bucket1,
                copy_object_details=copy_src,
                retry_strategy=total_kwargs.get("retry_strategy"),
                opc_client_request_id=total_kwargs.get("opc_client_request_id"),
                opc_sse_customer_algorithm=total_kwargs.get(
                    "opc_sse_customer_algorithm"
                ),
                opc_sse_customer_key=total_kwargs.get("opc_sse_customer_key"),
                opc_sse_customer_key_sha256=total_kwargs.get(
                    "opc_sse_customer_key_sha256"
                ),
                opc_source_sse_customer_algorithm=total_kwargs.get(
                    "opc_source_sse_customer_algorithm"
                ),
                opc_source_sse_customer_key=total_kwargs.get(
                    "opc_source_sse_customer_key"
                ),
                opc_source_sse_customer_key_sha256=total_kwargs.get(
                    "opc_source_sse_customer_key_sha256"
                ),
            )
        except ServiceError as e:
            raise translate_oci_error(e) from e
        self.invalidate_cache(path2)

    def copy(self, path1, path2, destination_region=None, **kwargs):
        """Copy file between locations on OCI

        Parameters
        ----------
        path1 : str
            URI of source data
        path2 : str
            URI of destination data
        destination_region : str
            the region you want path2 to be written in
            (defaults region of your config)

        """
        gb50 = 50 * 2 ** 30
        dest_region = destination_region or self.region
        if not dest_region:
            raise ValueError(
                "No region specified. Please set the 'region' parameter in the kwargs."
            )
        # We xor the paths to see if one is local and the other oci:// prefixed. If so, forward to `sync`
        if self.is_local_path(path1) != self.is_local_path(path2):
            logger.info(
                "Detected one of the input paths to ocifs `copy` as a local path. Forwarding call to `sync` method."
            )
            self.sync(src_dir=path1, dest_dir=path2, region=dest_region, **kwargs)
        path1 = self._strip_protocol(path1)
        path1_info = self.info(path1)
        size = path1_info.get("size", None)
        try:
            self.copy_basic(path1, path2, destination_region=dest_region, **kwargs)
        except Exception as e:
            if size >= gb50:
                raise NotImplementedError(
                    f"copy does not support files over 50gb. Got the error {e}"
                )
            raise e

    def info(self, path, **kwargs):
        """Get metadata about a file from a head or list call.

        Parameters
        ----------
        path : str
            URI of the directory/file
        kwargs : dict
            additional args for OCI

        """
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        generic_dir = CaseInsensitiveDict(
            {"name": path, "size": 0, "type": "directory"}
        )
        # self.invalidate_cache(path=path)
        if key:
            try:
                obj_data = self._call_oci(
                    self.oci_client.head_object,
                    namespace_name=namespace,
                    bucket_name=bucket,
                    object_name=key,
                    **kwargs,
                ).headers
            except ServiceError as e:
                if e.status == 404:
                    # Check for subdirectories
                    try:
                        if self._call_oci(
                                self.oci_client.list_objects,
                                namespace_name=namespace,
                                bucket_name=bucket,
                                prefix=key.rstrip("/") + "/",
                                limit=1,
                        ).data.objects:
                            generic_dir
                            return generic_dir
                    except Exception as e:
                        raise translate_oci_error(e) from e
                raise translate_oci_error(e) from e
            return CaseInsensitiveDict(
                {
                    "name": path,
                    "type": "file",
                    "size": int(obj_data["Content-Length"]),
                    "timeModified": obj_data["last-modified"],
                    "acceptRanges": obj_data["accept-ranges"],
                    "etag": obj_data["etag"],
                    "versionId": obj_data["version-id"],
                    "storageTier": obj_data["storage-tier"],
                }
            )
        if bucket:
            try:
                bucket_data = self._call_oci(
                    self.oci_client.head_bucket,
                    namespace_name=namespace,
                    bucket_name=bucket,
                    **kwargs,
                ).headers
            except ServiceError as e:
                raise translate_oci_error(e) from e
            bucket_dict = CaseInsensitiveDict({"etag": bucket_data["etag"]})
            bucket_dict.update(generic_dir)
            return bucket_dict
        try:
            ns_metadata = self._call_oci(
                self.oci_client.get_namespace_metadata,
                namespace_name=namespace,
                **kwargs,
            ).data
        except ServiceError as e:
            raise translate_oci_error(e) from e
        ns_dict = {k: getattr(ns_metadata, k) for k in ns_metadata.attribute_map.keys()}
        ns_dict.update(generic_dir)
        return ns_dict

    def metadata(self, path, **kwargs):
        """Get metadata about a file from a head or list call.

        Parameters
        ----------
        path : str
            URI of the directory/file
        kwargs : dict
            additional args for OCI

        """
        return self.info(path, **kwargs)

    def mkdir(
            self,
            path: str,
            create_parents: bool = True,
            compartment_id: str = None,
            **kwargs,
    ):
        """Make a new bucket or folder

        Parameters
        ----------
        path : str
            URI of the directory
        create_parents : bool (=True)
            If Ture, will create all nested dirs
        compartment_id : str
            If the compartment to create the bucket is different from the compartment of
            your auth mechanism.
        kwargs : dict
            additional args for OCI

        """
        path = self._strip_protocol(path).rstrip("/")
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        comp_id = (
            compartment_id
            if compartment_id
            else kwargs.get("compartment_id", self._get_default_tenancy())
        )
        if not key or create_parents:
            try:
                bucket_d = self._call_oci(
                    CreateBucketDetails,
                    is_detail_method=True,
                    compartment_id=comp_id,
                    name=bucket,
                    **kwargs,
                )
                logger.debug(
                    f"Creating bucket: {bucket}, in namespace: {namespace}, in "
                    f"compartment_id: {comp_id}, and with kwargs: {kwargs}"
                )
                self._call_oci(
                    self.oci_client.create_bucket,
                    namespace_name=namespace,
                    create_bucket_details=bucket_d,
                    **kwargs,
                )
                self.invalidate_cache(f"@{namespace}")
                self.invalidate_cache(path)
            except ServiceError as e:
                if e.code != "BucketAlreadyExists":
                    raise translate_oci_error(e) from e
        elif not self.exists(f"{bucket}@{namespace}"):
            raise FileNotFoundError(f"{bucket}@{namespace}")

    def rmdir(self, path, **kwargs):
        bucket, namespace, key = self.split_path(path)
        key = key.rstrip("/")
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        if self.ls(path):
            raise OSError("Directory is not empty")
        if not key:
            try:
                self._call_oci(
                    self.oci_client.delete_bucket,
                    namespace_name=namespace,
                    bucket_name=bucket,
                    **kwargs,
                )
            except ServiceError as e:
                raise translate_oci_error(e) from e
            self.invalidate_cache(path)
            self.invalidate_cache(f"@{namespace}")

    def bulk_delete(self, pathlist, **kwargs):
        """
        Remove multiple keys with one call
        Parameters
        ----------
        pathlist : listof strings
            The keys to remove, must all be in the same bucket.
        """
        if not pathlist or not isinstance(pathlist, list):
            return
        bucket_namespace = {self.split_path(path)[:2] for path in pathlist}
        if len(bucket_namespace) > 1:
            raise ValueError("Bulk delete files should refer to only one " "bucket")
        bucket, namespace = bucket_namespace.pop()

        for path in pathlist:
            # Invalidate the Cache
            self.invalidate_cache(self._parent(path))
            # Try to delete the object
            _, _, key = self.split_path(path)
            try:
                self._call_oci(
                    self.oci_client.delete_object,
                    namespace_name=namespace,
                    bucket_name=bucket,
                    object_name=key,
                    **kwargs,
                )
            except ServiceError as e:
                raise translate_oci_error(e) from e

    def rm(self, path, recursive=False, **kwargs):
        """Remove keys and/or bucket.

        Parameters
        ----------
        path : str
            The location to remove.
        recursive : bool (True)
            Whether to remove also all entries below, i.e., which are returned
            by `walk()`.

        """
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        if recursive:
            files = self.find(path, maxdepth=None, **kwargs)
            if key and not files:
                raise FileNotFoundError(path)
            self.bulk_delete(files, **kwargs)
            if not key:
                self.rmdir(path, **kwargs)
            return
        if key:
            if not self.exists(path):
                raise FileNotFoundError(path)
            try:
                self._call_oci(
                    self.oci_client.delete_object,
                    namespace_name=namespace,
                    bucket_name=bucket,
                    object_name=key,
                    **kwargs,
                )
            except ServiceError as e:
                raise translate_oci_error(e) from e
            self.invalidate_cache(self._parent(path))
        else:
            if self.exists(path):
                try:
                    self._call_oci(
                        self.oci_client.delete_bucket,
                        namespace_name=namespace,
                        bucket_name=bucket,
                        **kwargs,
                    )
                except ServiceError as e:
                    raise translate_oci_error(e) from e
                self.invalidate_cache(path)
                self.invalidate_cache(f"@{namespace}")
            else:
                raise FileNotFoundError(path)

    @classmethod
    def _parent(cls, path):
        path = cls._strip_protocol(path.rstrip("/"))
        if "/" in path:
            return cls.root_marker + path.rsplit("/", 1)[0]
        elif "@" in path:
            return cls.root_marker + "@" + path.split("@", 1)[1]
        else:
            raise ValueError(f"the following path does not specify a namespace: {path}")

    @classmethod
    def _strip_protocol(cls, path):
        if isinstance(path, list):
            return [cls._strip_protocol(p) for p in path]
        path = stringify_path(path)
        stripped_path = super()._strip_protocol(path)
        if stripped_path == cls.root_marker and "@" in path:
            return "@" + path.rstrip("/").split("@", 1)[1]
        return stripped_path

    def _get_region(self, **kwargs):
        region = self.region or self.kwargs.get("region")
        if not region:
            region = (
                self.config.get("region") if isinstance(self.config, dict) else None
            )
            if not region and self._iam_type == "resource_principal":
                region = os.environ.get(
                    "OCI_RESOURCE_PRINCIPAL_REGION"
                ) or literal_eval(os.environ.get("OCI_REGION_METADATA") or "{}").get(
                    "regionIdentifier"
                )
        self.region = region
        logger.debug(f"Using Region: {region}.")
        return region

    def _get_default_tenancy(self):
        tenancy = self.default_tenancy or self.kwargs.get("tenancy")
        if not tenancy:
            if self._iam_type == "resource_principal":
                tenancy = os.environ.get("TENANCY_OCID")
            else:
                namespace_name = self._get_default_namespace()
                tenancy = self.oci_client.get_namespace_metadata(
                    namespace_name=namespace_name
                ).data.default_swift_compartment_id

        logger.debug(
            f"Using Tenancy: {tenancy}. If you wish to use a different tenancy, "
            "pass it in through the kwarg 'tenancy'"
        )
        self.default_tenancy = tenancy
        return tenancy

    def _get_default_namespace(self):
        namespace = self.default_namespace or self.kwargs.get("namespace")
        if not namespace:
            namespace = self.oci_client.get_namespace().data
        self.default_namespace = namespace
        return namespace

    def _update_service_endpoint(self):
        if self.region is not None and "service_endpoint" not in self.config_kwargs:
            self.config_kwargs[
                "service_endpoint"
            ] = f"https://objectstorage.{self.region}.oraclecloud.com"

    def _get_iam_auth(self):
        assert self._iam_type in IAM_POLICIES, (
            "Unrecognized IAM Prinicipal type passed into `iam_type` arg: "
            f"{self._iam_type}. Please select a valid arg from: {IAM_POLICIES}."
        )
        return getattr(self, f"_set_up_{self._iam_type}")()

    def _determine_iam_auth(self):
        # This get complicated quickly. Essentially the flow is:
        # If the user has passed in a signer explicitly, use it
        # If the user has passed in a config explicitly, use it
        # otherwise check global variables, attempt resource principal, then throw error
        if not self._iam_type:
            if self._signer:
                self._iam_type = "unknown_signer"
            elif self.config:
                self._iam_type = "api_key"
            elif os.environ.get("OCIFS_IAM_TYPE"):
                self._iam_type = os.environ["OCIFS_IAM_TYPE"]
            else:
                try:  # pragma: no cover
                    self._iam_type = "resource_principal"
                    self._set_up_resource_principal()
                except OSError as e:  # pragma: no cover
                    raise ConfigFileNotFound(
                        "No iam_type was given, no signer was given, no config file was"
                        " given, OCIFS_IAM_TYPE environment variable not found, and failed "
                        f"to create a Resource Principal signer with error: {e}."
                    )
        self._get_iam_auth()

    def _set_up_resource_principal(self):
        self.config_kwargs["signer"] = get_resource_principals_signer()

    def _set_up_instance_principal(self):
        self.config_kwargs["signer"] = InstancePrincipalsSecurityTokenSigner()

    def _set_up_api_key(self):
        if not self.config:
            self.config = os.environ.get("OCIFS_CONFIG_LOCATION", DEFAULT_LOCATION)
        if isinstance(self.config, str):
            config_path = self.config
            if self.profile is None:
                self.profile = os.environ.get("OCIFS_CONFIG_PROFILE", DEFAULT_PROFILE)
                logger.debug(f"No profile specified, using: {self.profile}.")
            self.config = from_file(
                file_location=config_path, profile_name=self.profile
            )
        elif isinstance(self.config, dict):
            self.config = self.config.copy()

    def _set_up_unknown_signer(self):
        self.config_kwargs["signer"] = self._signer

    def _update_retry_strategy(self):
        if not self.config_kwargs.get("retry_strategy"):
            self.config_kwargs["retry_strategy"] = DEFAULT_RETRY_STRATEGY

    def _refresh_signer(self):
        if self._iam_type in {
            "resource_principal",
            "instance_principal",
            "unknown_signer",
        }:
            if hasattr(self.config_kwargs["signer"], "refresh_security_token"):
                self.config_kwargs.get("signer").refresh_security_token()

    def open(
            self,
            path: str,
            mode: str = "rb",
            block_size: int = None,
            cache_options: dict = None,
            compression: str = None,
            cache_type: str = None,
            autocommit: bool = True,
            **kwargs,
    ):
        """Open a file for reading or writing

        Parameters
        ----------
        path: string
            Path of file on oci
        mode: string
            One of 'r', 'w', 'rb', or 'wb'. These have the same meaning
            as they do for the built-in `open` function.
        block_size: int
            Size of data-node blocks if reading
        cache_options : dict, optional
            Extra arguments to pass through to the cache.
        compression: string or None
            If given, open file using compression codec. Can either be a compression
            name (a key in ``fsspec.compression.compr``) or "infer" to guess the
            compression from the filename suffix.
        cache_type: str
            Caching policy in read mode
            Valid types are: {"readahead", "none", "mmap", "bytes"}, default "readahead"
        autocommit : bool
            If True, the OCIFile will automatically commit the multipart upload when done
        encoding : str
            The encoding to use if opening the file in text mode. The platform's
            default text encoding is used if not given.
        kwargs: dict-like
            Additional parameters used for oci methods.  Typically used for
            ServerSideEncryption.
        """

        return super().open(
            path=path,
            mode=mode,
            block_size=block_size,
            cache_options=cache_options,
            compression=compression,
            cache_type=cache_type,
            autocommit=autocommit,
            **kwargs,
        )

    def _open(
            self,
            path: str,
            mode: str = "rb",
            block_size: int = None,
            autocommit: bool = True,
            cache_options: dict = None,
            cache_type: str = None,
            **kwargs,
    ):
        """Open a file for reading or writing

        Parameters
        ----------
        path: string
            Path of file on oci
        mode: string
            One of 'r', 'w', 'rb', or 'wb'. These have the same meaning
            as they do for the built-in `open` function.
        block_size: int
            Size of data-node blocks if reading
        cache_options : dict, optional
            Extra arguments to pass through to the cache.
        cache_type: str
            Caching policy in read mode
            Valid types are: {"readahead", "none", "mmap", "bytes"}, default "readahead"
        autocommit : bool
            If True, the OCIFile will automatically commit the multipart upload when done
        encoding : str
            The encoding to use if opening the file in text mode. The platform's
            default text encoding is used if not given.
        kwargs: dict-like
            Additional parameters used for oci methods.  Typically used for
            ServerSideEncryption.
        """

        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        block_size = block_size or self.default_block_size
        cache_options = cache_options or self.default_cache_options
        cache_type = cache_type or self.default_cache_type
        assert mode in {"r", "w", "rb", "wb", "a", "ab"}, ValueError(
            "Mode must be one of 'r', 'w', 'rb', 'wb', 'a', 'ab'"
        )
        return OCIFile(
            fs=self,
            path=path,
            mode=mode,
            block_size=block_size,
            cache_options=cache_options,
            cache_type=cache_type,
            autocommit=autocommit,
            **kwargs,
        )

    def walk(self, path, maxdepth=None, **kwargs):
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        if not bucket:
            raise ValueError("Cannot crawl all of OCI Object Storage")
        return super().walk(path, maxdepth=maxdepth, **kwargs)

    def cat(self, path, recursive=False, on_error="raise", **kwargs):
        """Fetch (potentially multiple) paths' contents

        Parameters
        ----------
        path: string
            Path of file on oci
        recursive: bool
            If True, assume the path(s) are directories, and get all the
            contained files
        on_error : "raise", "omit", "return"
            If raise, an underlying exception will be raised (converted to KeyError
            if the type is in self.missing_exceptions); if omit, keys with exception
            will simply not be included in the output; if "return", all keys are
            included in the output, but the value will be bytes or an exception
            instance.
        kwargs: passed to cat_file

        Returns
        -------
        dict of {path: contents} if there are multiple paths
        or the path has been otherwise expanded
        """
        bucket, namespace, key = self.split_path(path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        return super().cat(path, recursive, on_error, **kwargs)


class OCIFile(AbstractBufferedFile):
    """Open OCI URI as a file.

    This imitates the native python file object. Data is only loaded and cached on demand.

    Parameters
    ----------
    fs: OCIFileSystem
        instance of FileSystem
    path: str
        location in file-system
    mode: str
        Normal file modes. Currently only 'w', 'wb', 'r' or 'rb'.
    block_size: int
        Buffer size for reading or writing, 'default' for class default
    autocommit: bool
        Whether to write to final destination; may only impact what
        happens when file is being closed.
    cache_type: {"readahead", "none", "mmap", "bytes"}, default "readahead"
        Caching policy in read mode. See the definitions in ``core``.
    cache_options : dict
        Additional options passed to the constructor for the cache specified
        by `cache_type`.
    size: int
        If given and in read mode, suppressed having to look up the file size
    kwargs:
        Gets stored as self.kwargs
    """

    retries = 5
    MINIMUM_BLOCK_SIZE = 5 * 2 ** 20
    MAXIMUM_BLOCK_SIZE = 5 * 2 ** 30

    def __init__(
            self,
            fs: OCIFileSystem,
            path: str,
            mode: str = "rb",
            block_size: int = MINIMUM_BLOCK_SIZE,
            autocommit: bool = True,
            cache_type: str = "bytes",
            cache_options: dict = None,
            additional_kwargs: dict = None,
            size: int = None,
            **kwargs,
    ):
        self.bucket, self.namespace, self.key = fs.split_path(path)
        self.path = _build_full_path(bucket=self.bucket, namespace=self.namespace, key=self.key, **kwargs)
        if not self.key:
            raise ValueError("Attempt to open non key-like path: %s" % path)

        super().__init__(
            fs,
            path,
            mode,
            block_size,
            autocommit=autocommit,
            cache_type=cache_type,
            cache_options=cache_options,
            size=size,
            **kwargs,
        )

        self.additional_kwargs = additional_kwargs or dict()
        self.mpu = None
        self.parts = None

        if self.writable():
            if block_size < self.MINIMUM_BLOCK_SIZE:
                raise ValueError(
                    f"Block size must be >={self.MINIMUM_BLOCK_SIZE / (2 ** 20)}MB"
                )

        # when not using autocommit we want to have transactional state to manage
        self.append_block = False
        if "a" in mode and self.fs.exists(path):
            head = self.fs._call_oci(
                self.fs.oci_client.head_object,
                namespace_name=self.namespace,
                bucket_name=self.bucket,
                object_name=self.key,
            ).headers

            loc = int(head.pop("Content-Length"))
            self.write(self.fs.cat(self.path))
            logger.debug("'ab' and 'a' are experimental modes for large files.")
            self.loc = loc

            # Reflect head
            self.additional_kwargs.update(head)

    def _fetch_range(self, start, end, max_attempts=10, **kwargs):
        """Download a block of data

        The expectation is that the server returns only the requested bytes,
        with HTTP code 206. If this is not the case, we first check the headers,
        and then stream the output - if the data size is bigger than we
        requested, an exception is raised.
        """
        logger.debug(
            "Fetch: %s@%s/%s, %s-%s", self.bucket, self.namespace, self.key, start, end
        )
        for i in range(max_attempts):
            try:
                response = self.fs._call_oci(
                    self.fs.oci_client.get_object,
                    namespace_name=self.namespace,
                    bucket_name=self.bucket,
                    object_name=self.key,
                    range="bytes=%i-%i" % (start, end - 1),
                    **kwargs,
                )
                return response.data.raw.read()
            except ServiceError as e:
                raise translate_oci_error(e) from e
        raise RuntimeError("Max number of OCI Object Storage retries exceeded")

    def _initiate_upload(self, **kwargs):
        if self.autocommit and self.tell() < self.blocksize:
            # only happens when closing small file, use on-shot PUT
            return
        self.parts = []
        logger.debug("Initiate upload for %s" % self)
        try:
            mpu_details = self.fs._call_oci(
                CreateMultipartUploadDetails,
                is_detail_method=True,
                object=self.key,
                **kwargs,
            )
            self.mpu = self.fs._call_oci(
                self.fs.oci_client.create_multipart_upload,
                namespace_name=self.namespace,
                bucket_name=self.bucket,
                create_multipart_upload_details=mpu_details,
                **kwargs,
            ).data
        except ServiceError as e:
            raise translate_oci_error(e) from e

    def _upload_chunk(self, final=False, **kwargs):
        bucket, namespace, key = self.fs.split_path(self.path)
        path = _build_full_path(bucket=bucket, namespace=namespace, key=key, **kwargs)
        logger.debug(
            "Upload for %s, final=%s, loc=%s, buffer loc=%s"
            % (self, final, self.loc, self.buffer.tell() if self.buffer else -1)
        )
        if self.autocommit and final and self.tell() < self.blocksize:
            # only happens when closing small file, use on-shot PUT
            data1 = False
        else:
            self.buffer.seek(0)
            (data0, data1) = (None, self.buffer.read(self.blocksize))

        while data1:
            (data0, data1) = (data1, self.buffer.read(self.blocksize))
            data1_size = len(data1)

            if 0 < data1_size < self.blocksize:
                remainder = data0 + data1
                remainder_size = self.blocksize + data1_size

                if remainder_size <= self.MAXIMUM_BLOCK_SIZE:
                    (data0, data1) = (remainder, None)
                else:
                    partition = remainder_size // 2
                    (data0, data1) = (remainder[:partition], remainder[partition:])

            part = len(self.parts) + 1
            logger.debug("Upload chunk %s, %s" % (self, part))

            for attempt in range(self.retries + 1):
                try:
                    try:
                        out = self.fs._call_oci(
                            self.fs.oci_client.upload_part,
                            namespace_name=namespace,
                            bucket_name=bucket,
                            object_name=key,
                            upload_id=self.mpu.upload_id,
                            upload_part_num=part,
                            upload_part_body=data0,
                            **kwargs,
                        )
                        break
                    except ServiceError as e:
                        raise translate_oci_error(e) from e
                except Exception as exc:
                    raise IOError("Write failed: %r" % exc)
            self.parts.append({"partNum": part, "etag": out.headers["etag"]})

        if self.autocommit and final:
            self.commit()
        return not final

    def commit(self, **kwargs):
        logger.debug("Commit %s" % self)
        if self.tell() == 0:
            if self.buffer is not None:
                logger.debug("Empty file committed %s" % self)
                self._abort_mpu()
                self.fs.touch(self.path)
        elif not self.parts:
            if self.buffer is not None:
                logger.debug("One-shot upload of %s" % self)
                self.buffer.seek(0)
                data = self.buffer.read()
                try:
                    self.fs._call_oci(
                        self.fs.oci_client.put_object,
                        namespace_name=self.namespace,
                        bucket_name=self.bucket,
                        object_name=self.key,
                        put_object_body=data,
                        **kwargs,
                    )
                except ServiceError as e:
                    raise translate_oci_error(e) from e
            else:
                raise RuntimeError
        else:
            logger.debug("Complete multi-part upload for %s " % self)
            try:
                commit_details = self.fs._call_oci(
                    CommitMultipartUploadDetails,
                    is_detail_method=True,
                    parts_to_commit=self.parts,
                    **kwargs,
                )
                write_result = self.fs._call_oci(
                    self.fs.oci_client.commit_multipart_upload,
                    namespace_name=self.namespace,
                    bucket_name=self.bucket,
                    object_name=self.key,
                    upload_id=self.mpu.upload_id,
                    commit_multipart_upload_details=commit_details,
                )
            except ServiceError as e:
                raise translate_oci_error(e) from e

        # complex cache invalidation, since file's appearance can cause several directories
        self.buffer = None
        parts = self.path.split("/")
        path = parts[0]
        for p in parts[1:]:
            if path in self.fs.dircache and not [
                True for f in self.fs.dircache[path] if f["name"] == path + "/" + p
            ]:
                self.fs.invalidate_cache(path)
            path = path + "/" + p

    def discard(self):
        logger.debug("discard:%s" % self)
        self._abort_mpu()
        self.buffer = None  # file becomes unusable

    def _abort_mpu(self, **kwargs):
        logger.debug("abort mpu:%s" % self)
        if self.mpu:
            try:
                self.fs._call_oci(
                    self.fs.oci_client.abort_multipart_upload,
                    namespace_name=self.namespace,
                    bucket_name=self.bucket,
                    object_name=self.key,
                    upload_id=self.mpu.upload_id,
                    **kwargs,
                )
            except ServiceError as e:
                raise translate_oci_error(e) from e
            self.mpu = None

    def __str__(self):
        return "<OCI Storage File %s@%s/%s>" % (self.bucket, self.namespace, self.key)
