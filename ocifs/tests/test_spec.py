# -*- coding: utf-8 -*-
# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from contextlib import contextmanager
import io
import time
import fsspec
import pytest
import oci
import os
from itertools import chain
from concurrent.futures import ProcessPoolExecutor
from ..core import OCIFileSystem
from ..errors import translate_oci_error
from oci._vendor.requests.structures import CaseInsensitiveDict
from oci.exceptions import (
    ServiceError,
    ProfileNotFound,
    ConfigFileNotFound,
)
from copy import deepcopy
from oci.object_storage import ObjectStorageClient


namespace_name = os.environ["OCIFS_TEST_NAMESPACE"]
test_bucket_name = os.environ.get("OCIFS_TEST_BUCKET", "ocifs-test")
security_token_profile = os.environ["OCIFS_TEST_SECURITY_TOKEN_PROFILE"]
full_test_bucket_name = f"{test_bucket_name}@{namespace_name}"

new_bucket_name = test_bucket_name + "-new"
full_new_bucket_name = f"{new_bucket_name}@{namespace_name}"

versioned_bucket_name = f"{test_bucket_name}-versioned"
full_versioned_bucket_name = f"{versioned_bucket_name}@{namespace_name}"

files = {
    "test/accounts.1.json": (
        b'{"amount": 100, "name": "Alice"}\n'
        b'{"amount": 200, "name": "Bob"}\n'
        b'{"amount": 300, "name": "Charlie"}\n'
        b'{"amount": 400, "name": "Dennis"}\n'
    ),
    "test/accounts.2.json": (
        b'{"amount": 500, "name": "Alice"}\n'
        b'{"amount": 600, "name": "Bob"}\n'
        b'{"amount": 700, "name": "Charlie"}\n'
        b'{"amount": 800, "name": "Dennis"}\n'
    ),
}

csv_files = {
    "2014-01-01.csv": (
        b"name,amount,id\n" b"Alice,100,1\n" b"Bob,200,2\n" b"Charlie,300,3\n"
    ),
    "2014-01-02.csv": (b"name,amount,id\n"),
    "2014-01-03.csv": (
        b"name,amount,id\n" b"Dennis,400,4\n" b"Edith,500,5\n" b"Frank,600,6\n"
    ),
}
text_files = {
    "nested/file1": b"hello\n",
    "nested/file2": b"world",
    "nested/nested2/file1": b"hello\n",
    "nested/nested2/file2": b"world",
}
glob_files = {"file.dat": b"", "filexdat": b""}
a_path = "tmp/test/a"
b_path = "tmp/test/b"
c_path = "tmp/test/c"
d_path = "tmp/test/d"
a = os.path.join(full_test_bucket_name, a_path)
b = os.path.join(full_test_bucket_name, b_path)
c = os.path.join(full_test_bucket_name, c_path)
d = os.path.join(full_test_bucket_name, d_path)

iam_type = os.environ.get("OCIFS_IAM_TYPE", "api_key")
if iam_type == "api_key":
    config = oci.config.from_file("~/.oci/config")
    storage_options = {"config": config}


SAFETY_SLEEP_TIME = 10


@pytest.fixture
def fs():
    try:
        client = ObjectStorageClient(config)
    except ServiceError as e:
        raise translate_oci_error(e) from e

    assert client.get_namespace().data == namespace_name

    for bucket_name in [test_bucket_name, new_bucket_name]:
        try:
            for mpu in client.list_multipart_uploads(
                namespace_name=namespace_name, bucket_name=bucket_name
            ).data:
                client.abort_multipart_upload(
                    namespace_name=namespace_name,
                    bucket_name=bucket_name,
                    object_name=mpu.object,
                    upload_id=mpu.upload_id,
                )
        except ServiceError as e:
            if e.code != "BucketNotFound" and e.status != 404:
                raise translate_oci_error(e) from e

    try:
        bucket_details = oci.object_storage.models.CreateBucketDetails(
            name=test_bucket_name, compartment_id=config.get("tenancy")
        )
        client.create_bucket(
            namespace_name=namespace_name, create_bucket_details=bucket_details
        )
    except ServiceError as e:
        if e.code != "BucketAlreadyExists":
            raise e

    for k in [a_path, b_path, c_path, d_path]:
        try:
            client.delete_object(
                namespace_name=namespace_name,
                bucket_name=test_bucket_name,
                object_name=k,
            )
        except Exception as e:
            if e.code != "ObjectNotFound" and e.status != 404:
                raise translate_oci_error(e) from e
    for flist in [files, csv_files, text_files, glob_files]:
        for f, data in flist.items():
            client.put_object(
                namespace_name=namespace_name,
                bucket_name=test_bucket_name,
                object_name=f,
                put_object_body=data,
            )
    OCIFileSystem.clear_instance_cache()
    fs = OCIFileSystem()  # Using env var to set IAM type
    fs.invalidate_cache()
    yield fs


@contextmanager
def expect_errno(expected_errno):
    """Expect an OSError and validate its errno code."""
    with pytest.raises(OSError) as error:
        yield
    assert error.value.errno == expected_errno, "OSError has wrong error code."


def test_simple(fs):
    data = b"a" * (10 * 2**20)

    with fs.open(a, "wb") as f:
        f.write(data)

    with fs.open(a, "rb") as f:
        out = f.read(len(data))
        assert len(data) == len(out)
        assert out == data


@pytest.mark.skip("Implementation Pending")
def test_security_token():
    data = b"a" * (10 * 2**20)
    oci_fs = OCIFileSystem(profile=security_token_profile, auth="security_token")

    with oci_fs.open(a, "wb") as f:
        f.write(data)

    with oci_fs.open(a, "rb") as f:
        out = f.read(len(data))
        assert len(data) == len(out)
        assert out == data


@pytest.mark.parametrize("default_cache_type", ["none", "bytes"])
def test_default_cache_type(default_cache_type):
    data = b"a" * (10 * 2**20)
    oci_fs = OCIFileSystem(config=config, default_cache_type=default_cache_type)

    with oci_fs.open(a, "wb") as f:
        f.write(data)

    with oci_fs.open(a, "rb") as f:
        assert isinstance(f.cache, fsspec.core.caches[default_cache_type])
        out = f.read(len(data))
        assert len(data) == len(out)
        assert out == data


def test_append_mode(fs):
    filename = f"oci://{full_test_bucket_name}/nested/file1"
    assert fs.cat(filename) == b"hello\n"
    with fs.open(filename, "ab") as f:
        f.write(b"world")
    assert fs.cat(filename) == b"hello\nworld"


def test_medium_append(fs):
    data1 = b"a" * (10 * 2**20)
    data2 = b"b" * (10 * 2**20)

    with fs.open(a, "wb") as f:
        f.write(data1)

    with fs.open(a, "ab") as f:
        f.write(data2)

    with fs.open(a, "rb") as f:
        out = f.read(2 * len(data1))
        assert len(data1) + len(data2) == len(out)
        assert out == data1 + data2


def test_large_append(fs):
    data1 = b"a" * (2**30)
    data2 = b"b" * (2**30)

    with fs.open(a, "wb") as f:
        f.write(data1)

    with fs.open(a, "ab") as f:
        f.write(data2)

    with fs.open(a, "rb") as f:
        out = f.read(2 * len(data1))
        assert len(data1) + len(data2) == len(out)
        assert out == data1 + data2


@pytest.mark.skip()
def test_client_kwargs():
    bad_fs = OCIFileSystem(
        config=config,
        config_kwargs={
            "service_endpoint": "http://foo",
            "timeout": 1000,
            "retry_strategy": None,
        },
    )
    try:
        bad_fs.ls("oci://")
    except ServiceError as e:
        if e.status != 502:
            raise e
    # Test invalid kwargs
    oci_fs = OCIFileSystem(
        config="~/.oci/config",
        client_kwargs={
            "hello": "world",
            "service_endpoint": "https://objectstorage.us-ashburn-1.oraclecloud.com",
        },
    )
    assert (
        oci_fs.oci_client.base_client.endpoint
        == "https://objectstorage.us-ashburn-1.oraclecloud.com"
    )


def test_config():
    hw_text = b"hello world"
    # Test config with string and dict
    fs = OCIFileSystem(config="~/.oci/config")
    fs.touch(a, data=hw_text)
    assert fs.exists(a)
    assert fs.cat(a) == hw_text
    fs2 = OCIFileSystem(config=oci.config.from_file("~/.oci/config"))
    assert fs2.exists(a)
    assert fs2.cat(a) == hw_text

    # Test that profile is getting pulled from config kwargs
    faulty_config_kwargs = {"timeout": -1}
    with pytest.raises(ProfileNotFound):
        OCIFileSystem(
            config="~/.oci/config",
            profile="nonexistent",
            config_kwargs=fs.config_kwargs,
        )

    # Test that config_kwargs persist between refreshes
    fs.config_kwargs = faulty_config_kwargs
    fs.profile = None
    fs.connect(refresh=True)
    assert fs.config_kwargs["timeout"] == -1

    # Test refresh
    fs.connect(refresh=False)


@pytest.mark.skip()
def test_connect_errors():
    # Because RP is not setup, config should fail for a variety of empty config arguments
    os.environ["OCIFS_IAM_TYPE"] = ""
    with pytest.raises(ConfigFileNotFound):
        OCIFileSystem()
    with pytest.raises(ConfigFileNotFound):
        OCIFileSystem(config=None)
    with pytest.raises(ConfigFileNotFound):
        OCIFileSystem(config=dict())
    os.environ["OCIFS_IAM_TYPE"] = "api_key"


def test_idempotent_connect(fs):
    con1 = fs.connect()
    con2 = fs.connect(refresh=False)
    con3 = fs.connect(refresh=True)
    assert con1 is con2
    assert con1 is not con3


def test_connect_many():
    from multiprocessing.pool import ThreadPool

    def task(i):
        OCIFileSystem(config=storage_options["config"]).ls(f"@{namespace_name}")
        return True

    pool = ThreadPool(processes=20)
    out = pool.map(task, range(40))
    assert all(out)
    pool.close()
    pool.join()


def test_connect_args(fs):
    original_client_id = id(fs.oci_client)
    fs.connect(refresh=True)
    new_client_id = id(fs.oci_client)
    assert new_client_id != original_client_id
    fs.connect(refresh=False)
    assert new_client_id == id(fs.oci_client)

    fs.kwargs.update({"region": "us-ashburn-1", "tenancy": "tenancy1"})
    fs.connect(refresh=True)
    fs._get_region()
    fs._get_default_tenancy()
    assert fs.region == "us-ashburn-1"
    assert fs.default_tenancy == "tenancy1"

    fs.profile = "profile123456789"
    fs.config = "~/.oci/config"
    with pytest.raises(ProfileNotFound):
        fs.connect(refresh=True)

    fs.config = None
    with pytest.raises(ProfileNotFound):
        fs.connect(refresh=True)

    fs.kwargs = dict()
    with pytest.raises(ProfileNotFound):
        fs.connect(refresh=True)


# TODO: need to find better kwarg parsing
def test_add_kwargs():
    oci_add_kwargs = {"retry_strategy": None}  # "hello": "world",
    oci_fs = OCIFileSystem(config=config, oci_additional_kwargs=oci_add_kwargs)
    oci_fs.touch(a, data="hello world")
    oci_fs.copy(a, b, destination_region="us-ashburn-1")
    time.sleep(SAFETY_SLEEP_TIME)
    assert oci_fs.cat(a) == oci_fs.cat(b)


def test_multiple_objects(fs):
    fs.connect()
    assert fs.ls(full_test_bucket_name)
    fs2 = OCIFileSystem(storage_options["config"])
    assert fs.ls(full_test_bucket_name) == fs2.ls(full_test_bucket_name)


def test_region_support():
    regional_full_bucket_name = f"{test_bucket_name}-regional@{namespace_name}"
    test_folder = f"{regional_full_bucket_name}/test"
    endpoints_to_test = [
        "https://objectstorage.us-ashburn-1.oraclecloud.com",
        "https://objectstorage.ap-sydney-1.oraclecloud.com",
    ]
    for endpoint in endpoints_to_test:
        fs_reg = OCIFileSystem(
            config=config, config_kwargs={"service_endpoint": endpoint}
        )
        assert (
            fs_reg.oci_client.base_client.endpoint == endpoint
        ), "Endpoint failed ot setup"
        if fs_reg.exists(regional_full_bucket_name):
            fs_reg.rm(regional_full_bucket_name, recursive=True)
        fs_reg.mkdir(test_folder)
        fs_reg.touch(f"{test_folder}/hello.txt", data="Hello World")
        assert fs_reg.cat(f"{test_folder}/hello.txt") == b"Hello World"
        fs_reg.rm(regional_full_bucket_name, recursive=True)


def test_info(fs):
    fs.touch(a)
    fs.touch(b)
    info = deepcopy(fs.info(a))
    linfo = deepcopy(fs.ls(a, detail=True)[0])

    def equal_info(info, linfo):
        assert linfo["name"] == info["name"]
        assert linfo["type"] == info["type"]
        assert linfo["size"] == info["size"]
        assert linfo["etag"] == info["etag"]

    equal_info(info, linfo)
    parent = a.rsplit("/", 1)[0]
    a_info = deepcopy(fs.info(a))
    fs.invalidate_cache()  # remove full path from the cache
    fs.ls(parent)  # fill the cache with parent dir
    equal_info(a_info, fs.dircache[parent][0])  # main details should be equal

    new_parent = full_test_bucket_name + "/foo"
    fs.mkdir(new_parent)
    with pytest.raises(FileNotFoundError):
        fs.info(new_parent)
    fs.ls(new_parent)
    with pytest.raises(FileNotFoundError):
        fs.info(new_parent)

    # check that info works for in order for exist to work
    ns_info = fs.info(f"@{namespace_name}")
    assert ns_info["name"] == f"@{namespace_name}"
    assert ns_info["type"] == "directory"
    assert ns_info["size"] == 0

    bucket_info = deepcopy(fs.info(full_test_bucket_name))
    assert bucket_info["name"] == full_test_bucket_name
    assert bucket_info["type"] == "directory"
    assert bucket_info["size"] == 0

    dir_info = deepcopy(fs.info(full_test_bucket_name + "/test"))
    assert dir_info.pop("name") == full_test_bucket_name + "/test"
    assert dir_info.pop("type") == "directory"
    assert dir_info.pop("size") == 0
    assert not dir_info

    file_info = deepcopy(fs.info(full_test_bucket_name + "/test/accounts.1.json"))
    assert file_info["name"] == full_test_bucket_name + "/test/accounts.1.json"
    assert file_info["type"] == "file"
    assert file_info["size"] == 133
    assert file_info.pop("storageTier")

    with pytest.raises(FileNotFoundError):
        fs.info(full_test_bucket_name + "/tes")


def test_metadata(fs):
    fs.touch(a)
    fs.touch(b)
    # check that metad works for in order for exist to work
    ns_metad = fs.metadata(f"@{namespace_name}")
    assert ns_metad["name"] == f"@{namespace_name}"
    assert ns_metad["type"] == "directory"
    assert ns_metad["size"] == 0

    bucket_metad = deepcopy(fs.metadata(full_test_bucket_name))
    assert bucket_metad["name"] == full_test_bucket_name
    assert bucket_metad["type"] == "directory"
    assert bucket_metad["size"] == 0
    with pytest.raises(KeyError):
        assert bucket_metad.pop("compartmentId")

    dir_metad = deepcopy(fs.metadata(full_test_bucket_name + "/test"))
    assert dir_metad.pop("name") == full_test_bucket_name + "/test"
    assert dir_metad.pop("type") == "directory"
    assert dir_metad.pop("size") == 0
    assert not dir_metad

    file_metad = deepcopy(fs.metadata(full_test_bucket_name + "/test/accounts.1.json"))
    assert file_metad["name"] == full_test_bucket_name + "/test/accounts.1.json"
    assert file_metad["type"] == "file"
    assert file_metad["size"] == 133
    assert file_metad.pop("storageTier")
    assert file_metad.pop("versionId")

    with pytest.raises(FileNotFoundError):
        fs.metadata(full_test_bucket_name + "/tes")
    pass


def test_info_cached(fs):
    path = full_test_bucket_name + "/tmp"
    fqpath = "oci://" + path
    fs.touch(path + "/test")
    info = fs.info(fqpath)
    assert info == fs.info(fqpath)
    assert info == fs.info(path)
    fs.rm(path, recursive=True)
    assert not fs.exists(path + "/test")


def test_checksum(fs):
    bucket = test_bucket_name
    root_path = full_test_bucket_name + "/test"
    prefix = "test/checksum" + "/e"
    o1 = prefix + "1"
    o2 = prefix + "2"
    path1 = full_test_bucket_name + "/" + o1
    path2 = full_test_bucket_name + "/" + o2
    client = fs.oci_client

    # init client and files
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o1,
        put_object_body="",
    )
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o2,
        put_object_body="",
    )

    # change one file, using cache
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o1,
        put_object_body="foo",
    )
    checksum = fs.checksum(path1)
    fs.ls(path1)  # force caching
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o1,
        put_object_body="bar",
    )
    assert checksum != fs.checksum(path1)

    # change one file, without cache
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o1,
        put_object_body="foo",
    )
    checksum = fs.checksum(path1)
    fs.ls(path1)  # force caching
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o1,
        put_object_body="bar",
    )
    assert checksum != fs.checksum(path1)

    # Test for nonexistent file
    client.put_object(
        namespace_name=namespace_name,
        bucket_name=bucket,
        object_name=o1,
        put_object_body="bar",
    )
    fs.ls(path1)  # force caching
    client.delete_object(
        namespace_name=namespace_name, bucket_name=bucket, object_name=o1
    )
    client.delete_object(
        namespace_name=namespace_name, bucket_name=bucket, object_name=o2
    )
    with pytest.raises(FileNotFoundError):
        checksum = fs.checksum(o1)
    with pytest.raises(FileNotFoundError):
        checksum = fs.checksum("b@ns" + o1)
    try:
        fs.rm(root_path, recursive=True)
    except FileNotFoundError:
        pass
    fs.ls(path1, refresh=True)  # force caching
    assert not fs.exists(path1)


def test_ls(fs):
    # If we mock the obj stor, this would be a good test
    # assert set(fs.ls('')) == {full_test_bucket_name, full_versioned_bucket_name}
    assert full_test_bucket_name in set(fs.ls(f"@{namespace_name}"))
    # assert full_versioned_bucket_name in set(fs.ls(''))
    with pytest.raises(FileNotFoundError):
        fs.ls("nonexistent@ns")
    fn = full_test_bucket_name + "/test/accounts.1.json"
    assert fn in fs.ls(full_test_bucket_name + "/test")

    with pytest.raises(FileNotFoundError):
        fs.ls(
            f"@{namespace_name}", compartment_id=fs.default_tenancy + "j", refresh=True
        )


def test_ls_touch(fs):
    assert not fs.exists(full_test_bucket_name + "/tmp/test")
    fs.touch(a)
    fs.touch(b)
    L = fs.ls(full_test_bucket_name + "/tmp/test", detail=True)
    assert {d["name"] for d in L} == {a, b}
    L = fs.ls(full_test_bucket_name + "/tmp/test", detail=False)
    assert set(L) == {a, b}


def test_isfile(fs):
    assert not fs.isfile(f"@{namespace_name}")
    assert not fs.isfile("/")
    assert not fs.isfile(full_test_bucket_name)
    assert not fs.isfile(full_test_bucket_name + "/test")

    assert not fs.isfile(full_test_bucket_name + "/test/foo")
    assert fs.isfile(full_test_bucket_name + "/test/accounts.1.json")
    assert fs.isfile(full_test_bucket_name + "/test/accounts.2.json")

    assert not fs.isfile(a)
    fs.touch(a)
    assert fs.isfile(a)

    assert not fs.isfile(b)
    assert not fs.isfile(b + "/")
    fs.mkdir(b)
    assert not fs.isfile(b)
    assert not fs.isfile(b + "/")

    assert not fs.isfile(c)
    assert not fs.isfile(c + "/")
    fs.mkdir(c + "/")
    assert not fs.isfile(c)
    assert not fs.isfile(c + "/")


def test_isdir(fs):
    assert fs.isdir(f"@{namespace_name}")
    # TODO should this be a dir?
    # assert fs.isdir('/')
    assert fs.isdir(full_test_bucket_name)
    assert fs.isdir(full_test_bucket_name + "/test")

    assert not fs.isdir(full_test_bucket_name + "/test/foo")
    assert not fs.isdir(full_test_bucket_name + "/test/accounts.1.json")
    assert not fs.isdir(full_test_bucket_name + "/test/accounts.2.json")

    assert not fs.isdir(a)
    fs.touch(a)
    assert not fs.isdir(a)

    assert not fs.isdir(b)
    assert not fs.isdir(b + "/")

    assert not fs.isdir(c)
    assert not fs.isdir(c + "/")

    # test cache
    fs.invalidate_cache()
    assert not fs.dircache
    fs.ls(full_test_bucket_name + "/nested")
    assert full_test_bucket_name + "/nested" in fs.dircache
    assert not fs.isdir(full_test_bucket_name + "/nested/file1")
    assert not fs.isdir(full_test_bucket_name + "/nested/file2")
    assert fs.isdir(full_test_bucket_name + "/nested/nested2")
    assert fs.isdir(full_test_bucket_name + "/nested/nested2/")

    letters_dir = full_test_bucket_name + "/tmp/test"
    fs.touch(a)
    fs.touch(b)
    # Check that touching the files updated the cache and isdir can recognize that
    fs.ls(letters_dir, refresh=True)  # force cache update
    assert letters_dir in fs.dircache
    assert any([fp["name"] != letters_dir for fp in fs.dircache[letters_dir]])
    assert fs.isdir(letters_dir)


def test_find(fs):
    assert fs.find(full_test_bucket_name) == [
        f"{test_bucket_name}@{namespace_name}/2014-01-01.csv",
        f"{test_bucket_name}@{namespace_name}/2014-01-02.csv",
        f"{test_bucket_name}@{namespace_name}/2014-01-03.csv",
        f"{test_bucket_name}@{namespace_name}/file.dat",
        f"{test_bucket_name}@{namespace_name}/filexdat",
        f"{test_bucket_name}@{namespace_name}/nested/file1",
        f"{test_bucket_name}@{namespace_name}/nested/file2",
        f"{test_bucket_name}@{namespace_name}/nested/nested2/file1",
        f"{test_bucket_name}@{namespace_name}/nested/nested2/file2",
        f"{test_bucket_name}@{namespace_name}/test/accounts.1.json",
        f"{test_bucket_name}@{namespace_name}/test/accounts.2.json",
    ]


def test_rm(fs):
    assert not fs.exists(a)
    fs.touch(a)
    assert fs.exists(a)
    fs.rm(a)
    assert not fs.exists(a)
    with pytest.raises(FileNotFoundError):
        fs.rm(full_test_bucket_name + "/nonexistent")
    with pytest.raises(FileNotFoundError):
        fs.rm(f"nonexistent789098767890@{namespace_name}")
    with pytest.raises(FileNotFoundError):
        fs.rm("nonexistent789098767890")
    fs.rm(full_test_bucket_name + "/nested", recursive=True)
    assert not fs.exists(full_test_bucket_name + "/nested/nested2/file1")

    # whole bucket
    fs.rm(full_test_bucket_name, recursive=True)
    assert not fs.exists(full_test_bucket_name + "/2014-01-01.csv")
    assert not fs.exists(full_test_bucket_name)
    # TODO should this exist?
    # assert fs.exists("")


def test_rmdir(fs):
    fs.mkdir(full_new_bucket_name)
    fs.rmdir(full_new_bucket_name)
    assert full_new_bucket_name not in fs.ls(f"@{namespace_name}")


def test_mkdir(fs):
    fs.mkdir(full_new_bucket_name)
    assert full_new_bucket_name in fs.ls(f"@{namespace_name}")


def test_bulk_delete(fs):
    with pytest.raises(FileNotFoundError):
        fs.bulk_delete([f"nonexistent@{namespace_name}/file"])
    with pytest.raises(FileNotFoundError):
        fs.bulk_delete([f"{full_test_bucket_name}/this_file_doesnt_exist"])
    with pytest.raises(ValueError):
        fs.bulk_delete(
            [f"bucket1@{namespace_name}/file", f"bucket2@{namespace_name}/file"]
        )
    filelist = fs.find(full_test_bucket_name + "/nested")
    fs.bulk_delete([])
    fs.bulk_delete(filelist)
    assert not fs.exists(full_test_bucket_name + "/nested/nested2/file1")


def test_oci_file_access(fs):
    fn = full_test_bucket_name + "/nested/file1"
    data = b"hello\n"
    assert fs.cat(fn) == data
    assert fs.head(fn, 3) == data[:3]
    assert fs.tail(fn, 3) == data[-3:]
    assert fs.tail(fn, 10000) == data


def test_oci_file_info(fs):
    fn = full_test_bucket_name + "/nested/file1"
    data = b"hello\n"
    assert fn in fs.find(full_test_bucket_name)
    assert fs.exists(fn)
    assert not fs.exists(fn + "another")
    assert fs.info(fn)["size"] == len(data)
    with pytest.raises(FileNotFoundError):
        fs.info(fn + "another")


def test_bucket_exists(fs):
    assert fs.exists(full_test_bucket_name)
    assert not fs.exists(full_test_bucket_name + "x")
    fs2 = OCIFileSystem(storage_options["config"])
    assert fs2.exists(full_test_bucket_name)
    assert not fs2.exists(full_test_bucket_name + "x")


def test_du(fs):
    d = fs.du(full_test_bucket_name, total=False)
    assert all(isinstance(v, int) and v >= 0 for v in d.values())
    assert full_test_bucket_name + "/nested/file1" in d

    assert fs.du(full_test_bucket_name + "/test/", total=True) == sum(
        map(len, files.values())
    )
    assert fs.du(full_test_bucket_name) == fs.du("oci://" + full_test_bucket_name)


def test_oci_ls(fs):
    fn = full_test_bucket_name + "/nested/file1"
    assert fn not in fs.ls(full_test_bucket_name + "/")
    assert fn in fs.ls(full_test_bucket_name + "/nested/")
    assert fn in fs.ls(full_test_bucket_name + "/nested")
    assert fs.ls("oci://" + full_test_bucket_name + "/nested/") == fs.ls(
        full_test_bucket_name + "/nested"
    )


@pytest.mark.skip("takes a long time")
def test_oci_big_ls(fs):
    for x in range(1200):
        fs.touch(full_test_bucket_name + "/test/thousand/%i.part" % x)
    assert len(fs.find(full_test_bucket_name)) > 1200
    fs.rm(full_test_bucket_name + "/test/thousand/", recursive=True)
    assert len(fs.find(full_test_bucket_name + "/test/thousand/")) == 0


def test_oci_ls_detail(fs):
    L = fs.ls(full_test_bucket_name + "/nested", detail=True)
    assert all(isinstance(item, CaseInsensitiveDict) for item in L)


def test_glob(fs):
    fn = full_test_bucket_name + "/nested/file1"
    assert fn not in fs.glob(full_test_bucket_name + "/")
    assert fn not in fs.glob(full_test_bucket_name + "/*")
    assert fn not in fs.glob(full_test_bucket_name + "/nested")
    assert fn in fs.glob(full_test_bucket_name + "/nested/*")
    assert fn in fs.glob(full_test_bucket_name + "/nested/file*")
    assert fn in fs.glob(full_test_bucket_name + "/*/*")
    assert all(
        any(p.startswith(f + "/") or p == f for p in fs.find(full_test_bucket_name))
        for f in fs.glob(full_test_bucket_name + "/nested/*")
    )
    assert [full_test_bucket_name + "/nested/nested2"] == fs.glob(
        full_test_bucket_name + "/nested/nested2"
    )
    out = fs.glob(full_test_bucket_name + "/nested/nested2/*")
    assert {
        f"{test_bucket_name}@{namespace_name}/nested/nested2/file1",
        f"{test_bucket_name}@{namespace_name}/nested/nested2/file2",
    } == set(out)

    # Make sure glob() deals with the dot character (.) correctly.
    assert full_test_bucket_name + "/file.dat" in fs.glob(
        full_test_bucket_name + "/file.*"
    )
    assert full_test_bucket_name + "/filexdat" not in fs.glob(
        full_test_bucket_name + "/file.*"
    )


def test_get_list_of_summary_objects(fs):
    L = fs.ls(full_test_bucket_name + "/test")

    assert len(L) == 2
    assert [l.lstrip(full_test_bucket_name).lstrip("/") for l in sorted(L)] == sorted(
        list(files)
    )

    L2 = fs.ls("oci://" + full_test_bucket_name + "/test")

    assert L == L2


def test_read_keys_from_bucket(fs):
    for k, data in files.items():
        file_contents = fs.cat("/".join([full_test_bucket_name, k]))
        assert file_contents == data

        assert fs.cat("/".join([full_test_bucket_name, k])) == fs.cat(
            "oci://" + "/".join([full_test_bucket_name, k])
        )


def test_seek(fs):
    with fs.open(a, "wb") as f:
        f.write(b"123")

    with fs.open(a) as f:
        f.seek(1000)
        with pytest.raises(ValueError):
            f.seek(-1)
        with pytest.raises(ValueError):
            f.seek(-5, 2)
        with pytest.raises(ValueError):
            f.seek(0, 10)
        f.seek(0)
        assert f.read(1) == b"1"
        f.seek(0)
        assert f.read(1) == b"1"
        f.seek(3)
        assert f.read(1) == b""
        f.seek(-1, 2)
        assert f.read(1) == b"3"
        f.seek(-1, 1)
        f.seek(-1, 1)
        assert f.read(1) == b"2"
        for i in range(4):
            assert f.seek(i) == i


def test_bad_open(fs):
    with pytest.raises(ValueError):
        fs.open(f"@{namespace_name}")


def test_copy(fs):
    fn = full_test_bucket_name + "/test/accounts.1.json"
    fs.copy(fn, fn + "2", destination_region="us-ashburn-1")
    time.sleep(SAFETY_SLEEP_TIME)
    assert fs.cat(fn) == fs.cat(fn + "2")
    fs.rm(fn + "2")
    assert not fs.exists(fn + "2")


@pytest.mark.skip("takes a long time")
def test_copy_large(fs):
    data = b"abc" * 12 * 2**20
    foldername = full_test_bucket_name + "/test"
    fn = foldername + "/biggerfile"
    with fs.open(fn, "wb") as f:
        f.write(data)
    fs.copy(fn, fn + "2", destination_region="us-ashburn-1")
    time.sleep(SAFETY_SLEEP_TIME)
    assert fs.cat(fn) == fs.cat(fn + "2")
    fs.rm(foldername, recursive=True)
    assert not fs.exists(foldername)


@pytest.mark.xfail(reason="Sometimes this test takes too long.")
def test_move(fs):
    fn = full_test_bucket_name + "/test/accounts.1.json"
    data = fs.cat(fn)
    fs.mv(fn, fn + "2")
    time.sleep(SAFETY_SLEEP_TIME)
    assert fs.cat(fn + "2") == data
    assert not fs.exists(fn)
    fs.rm(fn + "2")
    assert not fs.exists(fn + "2")


def test_get_put(fs, tmpdir):
    test_file = str(tmpdir.join("test.json"))

    fs.get(full_test_bucket_name + "/test/accounts.1.json", test_file)
    data = files["test/accounts.1.json"]
    assert open(test_file, "rb").read() == data
    fs.put(test_file, full_test_bucket_name + "/temp")
    assert fs.du(full_test_bucket_name + "/temp", total=False)[
        full_test_bucket_name + "/temp"
    ] == len(data)
    assert fs.cat(full_test_bucket_name + "/temp") == data
    fs.rm(full_test_bucket_name + "/temp")
    assert not fs.exists(full_test_bucket_name + "/temp")


def test_errors(fs):
    with pytest.raises(FileNotFoundError):
        fs.open(full_test_bucket_name + "/tmp/test/shfoshf", "rb")

    with pytest.raises(FileNotFoundError):
        fs.rm(full_test_bucket_name + "/tmp/test/shfoshf/x")

    with pytest.raises(FileNotFoundError):
        fs.mv(full_test_bucket_name + "/tmp/test/shfoshf/x", "tmp/test/shfoshf/y")

    with pytest.raises(ValueError):
        fs.open("x", "rb")

    with pytest.raises(FileNotFoundError):
        fs.rm("unknodftyuiuytrtyuiuytrwn@ns")

    with pytest.raises(ValueError):
        with fs.open(full_test_bucket_name + "/temp", "wb") as f:
            f.read()

    with pytest.raises(ValueError):
        f = fs.open(full_test_bucket_name + "/temp", "rb")
        f.close()
        f.read()

    with pytest.raises(OSError):
        fs.mkdir("@/")

    with pytest.raises(ValueError):
        fs.find(f"@{namespace_name}")

    # with pytest.raises(ValueError):
    #     fs.ls(f'@{namespace_name}')

    with pytest.raises(ValueError):
        fs.find("oci://")

    # confirm touch cannot make a new bucket
    with pytest.raises(ValueError):
        fs.touch(f"q{full_test_bucket_name}")

    with pytest.raises(FileNotFoundError):
        fs.copy(
            path1=f"oci://{full_test_bucket_name}test/accounts.3.json",
            path2=f"oci://{full_test_bucket_name}test/accounts.4.json",
        )

    with pytest.raises(FileNotFoundError):
        fs.mkdir(f"q{full_test_bucket_name}/test", create_parents=False)

    with pytest.raises(OSError):
        fs.mkdir("bucket@nonexistent-ns")

    with pytest.raises(OSError):
        fs.metadata(f"{full_test_bucket_name}/test", **{"version_id": 6})

    with pytest.raises(FileNotFoundError):
        fs.info(f"q{full_test_bucket_name}")


def test_read_small(fs):
    fn = full_test_bucket_name + "/2014-01-01.csv"
    with fs.open(fn, "rb", block_size=10) as f:
        out = []
        while True:
            data = f.read(3)
            if data == b"":
                break
            out.append(data)
        assert fs.cat(fn) == b"".join(out)
        # cache drop
        assert len(f.cache) < len(out)


def test_read_oci_block(fs):
    data = files["test/accounts.1.json"]
    lines = io.BytesIO(data).readlines()
    path = full_test_bucket_name + "/test/accounts.1.json"
    assert fs.read_block(path, 1, 35, b"\n") == lines[1]
    assert fs.read_block(path, 0, 30, b"\n") == lines[0]
    assert fs.read_block(path, 0, 35, b"\n") == lines[0] + lines[1]
    assert fs.read_block(path, 0, 5000, b"\n") == data
    assert len(fs.read_block(path, 0, 5)) == 5
    assert len(fs.read_block(path, 4, 5000)) == len(data) - 4
    assert fs.read_block(path, 5000, 5010) == b""

    assert fs.read_block(path, 5, None) == fs.read_block(path, 5, 1000)


@pytest.mark.skip("temporarily disabled")
def test_new_bucket(fs):
    if fs.exists(full_new_bucket_name):
        fs.rmdir(full_new_bucket_name)
        time.sleep(5)  # Allow time to update
    fs.rmdir(full_new_bucket_name)
    assert not fs.exists(full_new_bucket_name)
    fs.mkdir(full_new_bucket_name)
    assert fs.exists(full_new_bucket_name)
    with fs.open(f"{full_new_bucket_name}/temp", "wb") as f:
        f.write(b"hello")
    with pytest.raises(OSError):
        fs.rmdir(full_new_bucket_name)

    fs.rm(f"{full_new_bucket_name}/temp")
    fs.rmdir(full_new_bucket_name)
    assert full_new_bucket_name not in fs.ls(f"@{namespace_name}")
    assert not fs.exists(full_new_bucket_name)
    with pytest.raises(FileNotFoundError):
        fs.ls(full_new_bucket_name)
    # Test deleting empty bucket
    fs.mkdir(full_new_bucket_name)
    fs.rm(full_new_bucket_name)


def test_new_bucket_auto(fs):
    if fs.exists(full_new_bucket_name):
        fs.rmdir(full_new_bucket_name)
        time.sleep(5)  # Allow time to update
    assert not fs.exists(full_new_bucket_name)
    with pytest.raises(Exception):
        fs.mkdir(f"{full_new_bucket_name}/other", create_parents=False)
    fs.mkdir(f"{full_new_bucket_name}/other", create_parents=True)
    assert fs.exists(full_new_bucket_name)
    fs.touch(f"{full_new_bucket_name}/afile")
    with pytest.raises(Exception):
        fs.rm(full_new_bucket_name)
    with pytest.raises(Exception):
        fs.rmdir(full_new_bucket_name)
    fs.rm(full_new_bucket_name, recursive=True)
    assert not fs.exists(full_new_bucket_name)


def test_dynamic_add_rm(fs):
    fs.mkdir(full_new_bucket_name)
    fs.mkdir(f"{full_new_bucket_name}/two")
    assert fs.exists(full_new_bucket_name)
    fs.ls(full_new_bucket_name)
    fs.touch(f"{full_new_bucket_name}/two/file_a")
    assert fs.exists(f"{full_new_bucket_name}/two/file_a")
    fs.rm(full_new_bucket_name, recursive=True)
    assert not fs.exists(full_new_bucket_name)


def test_write_small(fs):
    with fs.open(a, "wb") as f:
        f.write(b"hello")
    assert fs.cat(a) == b"hello"
    fs.open(a, "wb").close()
    assert fs.info(a)["size"] == 0
    fs.rm(a, recursive=True)
    time.sleep(SAFETY_SLEEP_TIME)
    assert not fs.exists(a)


@pytest.mark.skip("takes a long time")
def test_write_large(fs):
    "flush() chunks buffer when processing large singular payload"
    mb = 2**20
    payload_size = int(2.5 * 5 * mb)
    payload = b"0" * payload_size

    with fs.open(a, "wb") as fd:
        fd.write(payload)

    assert fs.cat(a) == payload
    assert fs.info(a)["size"] == payload_size
    fs.rm(a, recursive=True)
    time.sleep(SAFETY_SLEEP_TIME)
    assert not fs.exists(a)


@pytest.mark.skip(
    "Sometimes get a write failed OSError. ignore for now, large payload."
)
def test_write_limit(fs):
    "flush() respects part_max when processing large singular payload"
    mb = 2**20
    block_size = 15 * mb
    part_max = 28 * mb
    payload_size = 44 * mb
    payload = b"0" * payload_size

    with fs.open(a, "wb") as fd:
        fd.blocksize = block_size
        fd.write(payload)

    assert fs.cat(a) == payload

    assert fs.info(a)["size"] == payload_size
    fs.rm(a, recursive=True)
    time.sleep(SAFETY_SLEEP_TIME)
    assert not fs.exists(a)


def test_write_fails(fs):
    with pytest.raises(ValueError):
        fs.touch(full_test_bucket_name + "/temp")
        fs.open(full_test_bucket_name + "/temp", "rb").write(b"hello")
    with pytest.raises(ValueError):
        fs.open(full_test_bucket_name + "/temp", "wb", block_size=10)
    f = fs.open(full_test_bucket_name + "/temp", "wb")
    f.close()
    with pytest.raises(ValueError):
        f.write(b"hello")
    with pytest.raises(FileNotFoundError):
        fs.open("nonexistentbucket@ns/temp", "wb").close()
    fs.rm(full_test_bucket_name + "/temp", recursive=True)
    assert not fs.exists(full_test_bucket_name + "/temp")


def test_write_blocks(fs):
    with fs.open(full_test_bucket_name + "/temp", "wb") as f:
        f.write(b"a" * 2 * 2**20)
        assert f.buffer.tell() == 2 * 2**20
        assert not (f.parts)
        f.flush()
        assert f.buffer.tell() == 2 * 2**20
        assert not (f.parts)
        f.write(b"a" * 2 * 2**20)
        f.write(b"a" * 2 * 2**20)
        assert f.mpu
        assert f.parts
    assert fs.info(full_test_bucket_name + "/temp")["size"] == 6 * 2**20
    with fs.open(full_test_bucket_name + "/temp", "wb", block_size=10 * 2**20) as f:
        f.write(b"a" * 15 * 2**20)
        assert f.buffer.tell() == 0
    assert fs.info(full_test_bucket_name + "/temp")["size"] == 15 * 2**20
    fs.rm(full_test_bucket_name + "/temp", recursive=True)
    assert not fs.exists(full_test_bucket_name + "/temp")


def test_readline(fs):
    all_items = chain.from_iterable(
        [files.items(), csv_files.items(), text_files.items()]
    )
    for k, data in all_items:
        with fs.open("/".join([full_test_bucket_name, k]), "rb") as f:
            result = f.readline()
            expected = data.split(b"\n")[0] + (b"\n" if data.count(b"\n") else b"")
            assert result == expected


def test_readline_empty(fs):
    data = b""
    with fs.open(a, "wb") as f:
        f.write(data)
    with fs.open(a, "rb") as f:
        result = f.readline()
        assert result == data


def test_readline_blocksize(fs):
    data = b"ab\n" + b"a" * (10 * 2**20) + b"\nab"
    with fs.open(a, "wb") as f:
        f.write(data)
    with fs.open(a, "rb") as f:
        result = f.readline()
        expected = b"ab\n"
        assert result == expected

        result = f.readline()
        expected = b"a" * (10 * 2**20) + b"\n"
        assert result == expected

        result = f.readline()
        expected = b"ab"
        assert result == expected


def test_next(fs):
    expected = csv_files["2014-01-01.csv"].split(b"\n")[0] + b"\n"
    with fs.open(full_test_bucket_name + "/2014-01-01.csv") as f:
        result = next(f)
        assert result == expected


def test_iterable(fs):
    data = b"abc\n123"
    with fs.open(a, "wb") as f:
        f.write(data)
    with fs.open(a) as f, io.BytesIO(data) as g:
        for fromoci, fromio in zip(f, g):
            assert fromoci == fromio
        f.seek(0)
        assert f.readline() == b"abc\n"
        assert f.readline() == b"123"
        f.seek(1)
        assert f.readline() == b"bc\n"

    with fs.open(a) as f:
        out = list(f)
    with fs.open(a) as f:
        out2 = f.readlines()
    assert out == out2
    assert b"".join(out) == data


def test_readable(fs):
    with fs.open(a, "wb") as f:
        assert not f.readable()

    with fs.open(a, "rb") as f:
        assert f.readable()


def test_seekable(fs):
    with fs.open(a, "wb") as f:
        assert not f.seekable()

    with fs.open(a, "rb") as f:
        assert f.seekable()


def test_writable(fs):
    with fs.open(a, "wb") as f:
        assert f.writable()

    with fs.open(a, "rb") as f:
        assert not f.writable()


def test_bigger_than_block_read(fs):
    with fs.open(full_test_bucket_name + "/2014-01-01.csv", "rb", block_size=3) as f:
        out = []
        while True:
            data = f.read(20)
            out.append(data)
            if len(data) == 0:
                break
    assert b"".join(out) == csv_files["2014-01-01.csv"]


def test_current(fs):
    fs._cache.clear()
    fs = OCIFileSystem(storage_options["config"])
    assert fs.current() is fs
    assert OCIFileSystem.current() is fs


def test_array(fs):
    from array import array

    data = array("B", [65] * 1000)

    with fs.open(a, "wb") as f:
        f.write(data)

    with fs.open(a, "rb") as f:
        out = f.read()
        assert out == b"A" * 1000


def _get_oci_id(fs):
    return id(fs.oci_client)


def test_no_connection_sharing_among_processes(fs):
    executor = ProcessPoolExecutor()
    conn_id = executor.submit(_get_oci_id, fs).result()
    assert id(fs.connect()) != conn_id, "Processes should not share OCI connections."


def test_upload_with_oci_prefix(fs):
    path = f"oci://{full_test_bucket_name}/prefix/key"

    with fs.open(path, "wb") as f:
        f.write(b"a" * (10 * 2**20))

    assert fs.exists(path)
    fs.rm(path)
    assert not fs.exists(path)


def test_multipart_upload_blocksize(fs):
    blocksize = 5 * (2**20)
    expected_parts = 3

    fs2 = fs.open(a, "wb", block_size=blocksize)
    for _ in range(3):
        data = b"b" * blocksize
        fs2.write(data)

    # Ensure that the multipart upload consists of only 3 parts
    assert len(fs2.parts) == expected_parts
    fs2.close()


def test_default_pars():
    fs = OCIFileSystem(storage_options["config"], default_block_size=20)
    fn = full_test_bucket_name + "/" + list(files)[0]
    with fs.open(fn) as f:
        assert f.blocksize == 20
    with fs.open(fn, block_size=40) as f:
        assert f.blocksize == 40


def test_text_io__stream_wrapper_works(fs):
    """Ensure using TextIOWrapper works."""
    fs.mkdir(full_new_bucket_name)

    with fs.open(f"{full_new_bucket_name}/file.txt", "wb") as fd:
        fd.write("\u00af\\_(\u30c4)_/\u00af".encode("utf-16-le"))

    with fs.open(f"{full_new_bucket_name}/file.txt", "rb") as fd:
        with io.TextIOWrapper(fd, "utf-16-le") as stream:
            assert stream.readline() == "\u00af\\_(\u30c4)_/\u00af"

    fs.rm(full_new_bucket_name, recursive=True)
    assert not fs.exists(full_new_bucket_name)


def test_text_io__basic(fs):
    """Text mode is now allowed."""
    fs.mkdir(full_new_bucket_name)

    with fs.open(f"{full_new_bucket_name}/file.txt", "w") as fd:
        fd.write("\u00af\\_(\u30c4)_/\u00af")

    with fs.open(f"{full_new_bucket_name}/file.txt", "r") as fd:
        assert fd.read() == "\u00af\\_(\u30c4)_/\u00af"

    fs.rm(full_new_bucket_name, recursive=True)
    assert not fs.exists(full_new_bucket_name)


def test_text_io__override_encoding(fs):
    """Allow overriding the default text encoding."""
    fs.mkdir(full_new_bucket_name)

    with fs.open(f"{full_new_bucket_name}/file.txt", "w", encoding="ibm500") as fd:
        fd.write("Hello, World!")

    with fs.open(f"{full_new_bucket_name}/file.txt", "r", encoding="ibm500") as fd:
        assert fd.read() == "Hello, World!"

    fs.rm(full_new_bucket_name, recursive=True)
    assert not fs.exists(full_new_bucket_name)


def test_readinto(fs):
    fs.mkdir(full_new_bucket_name)

    with fs.open(f"{full_new_bucket_name}/file.txt", "wb") as fd:
        fd.write(b"Hello, World!")

    contents = bytearray(15)

    with fs.open(f"{full_new_bucket_name}/file.txt", "rb") as fd:
        assert fd.readinto(contents) == 13

    assert contents.startswith(b"Hello, World!")

    fs.rm(full_new_bucket_name, recursive=True)
    assert not fs.exists(full_new_bucket_name)


def test_autocommit():
    auto_file = full_test_bucket_name + "/auto_file"
    committed_file = full_test_bucket_name + "/commit_file"
    aborted_file = full_test_bucket_name + "/aborted_file"
    fs = OCIFileSystem(storage_options["config"], version_aware=True)

    def write_and_flush(path, autocommit):
        with fs.open(path, "wb", autocommit=autocommit) as fo:
            fo.write(b"1")
        return fo

    # regular behavior
    fo = write_and_flush(auto_file, autocommit=True)
    assert fo.autocommit
    assert fs.exists(auto_file)
    fs.rm(auto_file)
    assert not fs.exists(auto_file)

    fo = write_and_flush(committed_file, autocommit=False)
    assert not fo.autocommit
    assert not fs.exists(committed_file)
    fo.commit()
    assert fs.exists(committed_file)
    fs.rm(committed_file)
    assert not fs.exists(committed_file)

    fo = write_and_flush(aborted_file, autocommit=False)
    assert not fs.exists(aborted_file)
    fo.discard()
    assert not fs.exists(aborted_file)
    # Cannot commit a file that was discarded
    with pytest.raises(Exception):
        fo.commit()


def test_autocommit_mpu(fs):
    """When not autocommitting we always want to use multipart uploads"""
    path = full_test_bucket_name + "/auto_commit_with_mpu"
    with fs.open(path, "wb", autocommit=False) as fo:
        fo.write(b"1")
    assert fo.mpu is not None
    assert len(fo.parts) == 1


def test_touch(fs):
    # create
    assert not fs.exists(a)
    fs.touch(a)
    assert fs.exists(a)
    assert fs.size(a) == 0

    # truncates
    with fs.open(a, "wb") as f:
        f.write(b"data")
    assert fs.size(a) == 4
    fs.touch(a, truncate=True)
    assert fs.size(a) == 0

    # exists error
    with fs.open(a, "wb") as f:
        f.write(b"data")
    assert fs.size(a) == 4
    with pytest.raises(ValueError):
        fs.touch(a, truncate=False)
    assert fs.size(a) == 4

    with pytest.raises(AssertionError):
        fs.touch(a, "aaa")


def test_seek_reads(fs):
    fn = full_test_bucket_name + "/myfile"
    with fs.open(fn, "wb") as f:
        f.write(b"a" * 175627146)
    with fs.open(fn, "rb", blocksize=100) as f:
        f.seek(175561610)
        d1 = f.read(65536)

        f.seek(4)
        size = 17562198
        d2 = f.read(size)
        assert len(d2) == size

        f.seek(17562288)
        size = 17562187
        d3 = f.read(size)
        assert len(d3) == size
    fs.rm(fn)
    assert not fs.exists(fn)


def test_user_agent_leak():
    from oci.config import from_file

    config = from_file()
    new_fs = OCIFileSystem(config=config)
    assert new_fs.config["additional_user_agent"]
    assert not config["additional_user_agent"]


def test_sync(fs):
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        remote_dir = os.path.join("oci://", full_test_bucket_name, "test")
        fs.sync(src_dir=remote_dir, dest_dir=tmpdirname)
        assert len(fs.ls(remote_dir)) == len(os.listdir(tmpdirname))

    remote_dir = os.path.join("oci://", full_test_bucket_name, "sync") + "/"
    remote_loc = remote_dir + "test"
    with tempfile.TemporaryDirectory() as tmpdirname:
        for i in range(10):
            with open(os.path.join(tmpdirname, f"test{i}.json"), "w") as f:
                f.write("{'Hello': 'World', 'Answer': '42'}")
        fs.sync(src_dir=tmpdirname, dest_dir=remote_loc)
        assert len(fs.ls(remote_dir)) == len(os.listdir(tmpdirname))

    fs.rm(remote_dir, recursive=True)
