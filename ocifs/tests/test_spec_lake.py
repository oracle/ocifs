# -*- coding: utf-8 -*-
# Copyright (c) 2024 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import io
import fsspec
import pytest
import oci
import os
from ocifs import OCIFileSystem
from ocifs.errors import translate_oci_error
from oci._vendor.requests.structures import CaseInsensitiveDict
from oci.exceptions import ServiceError, ProfileNotFound
from ocifs.data_lake.lake_sharing_object_storage_client import (
    LakeSharingObjectStorageClient,
)


profile_name = os.environ["OCIFS_CONFIG_PROFILE"]
config = oci.config.from_file("~/.oci/config", profile_name=profile_name)
full_external_mount_name = os.environ["OCIFS_EXTERNAL_MOUNT_URI"]
storage_options = {"config": config}
test_bucket_with_namespace = ""
os.environ["OCIFS_IAM_TYPE"] = "api_key"
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
a = os.path.join(full_external_mount_name, a_path)
b = os.path.join(full_external_mount_name, b_path)
c = os.path.join(full_external_mount_name, c_path)


@pytest.fixture
def fs():
    OCIFileSystem.clear_instance_cache()
    fs = OCIFileSystem(
        config="~/.oci/config", profile=profile_name
    )  # Using env var to set IAM type
    try:
        client = LakeSharingObjectStorageClient(config)
    except ServiceError as e:
        raise translate_oci_error(e) from e
    for flist in [files, csv_files, text_files, glob_files]:
        for f, values in flist.items():
            file_path = os.path.join(full_external_mount_name, f)
            fs.touch(file_path, truncate=True, data=values)
    fs.invalidate_cache()
    yield fs


def test_simple(fs):
    data = b"a" * (10 * 2**20)

    with fs.open(a, "wb") as f:
        f.write(data)

    with fs.open(a, "rb") as f:
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


def test_idempotent_connect(fs):
    con1 = fs.connect()
    con2 = fs.connect(refresh=False)
    con3 = fs.connect(refresh=True)
    assert con1 is con2
    assert con1 is not con3


def test_find(fs):
    assert fs.find(full_external_mount_name)


def test_oci_file_access(fs):
    fn = full_external_mount_name + "/nested/file1"
    data = b"hello\n"
    assert fs.cat(fn) == data
    assert fs.head(fn, 3) == data[:3]
    assert fs.tail(fn, 3) == data[-3:]
    assert fs.tail(fn, 10000) == data


def test_multiple_objects(fs):
    fs.connect()
    assert fs.ls(full_external_mount_name)
    fs2 = OCIFileSystem(storage_options["config"])
    assert fs.ls(full_external_mount_name) == fs2.ls(full_external_mount_name)


def test_ls(fs):
    bucket, namespace, key = fs.split_path(full_external_mount_name + "/test")
    test_bucket_with_namespace = bucket + "@" + namespace + "/"
    fn = test_bucket_with_namespace + "test/accounts.1.json"
    assert fn in fs.ls(full_external_mount_name + "/test")


def test_ls_touch(fs):
    bucket, namespace, key = fs.split_path(full_external_mount_name + "/test")
    test_bucket_with_namespace = bucket + "@" + namespace + "/"
    test_dir_path = test_bucket_with_namespace + "tmp/test/"
    fs.touch(a)
    fs.touch(b)
    L = fs.ls(full_external_mount_name + "/tmp/test", detail=True)
    assert {d["name"] for d in L} == {test_dir_path + "a", test_dir_path + "b"}


def test_isfile(fs):
    assert not fs.isfile(full_external_mount_name)
    assert not fs.isfile(full_external_mount_name + "/test")
    assert fs.isfile(full_external_mount_name + "/test/accounts.1.json")
    assert fs.isfile(full_external_mount_name + "/test/accounts.2.json")


def test_isdir(fs):
    assert fs.isdir(full_external_mount_name)
    assert fs.isdir(full_external_mount_name + "/test")
    assert not fs.isdir(full_external_mount_name + "/test/accounts.1.json")
    assert not fs.isdir(full_external_mount_name + "/test/accounts.2.json")
    assert not fs.isdir(b + "/")
    assert not fs.isdir(c)


def test_oci_file_info(fs):
    bucket, namespace, key = fs.split_path(full_external_mount_name + "/test")
    test_bucket_with_namespace = bucket + "@" + namespace + "/"
    nested_file1_path = test_bucket_with_namespace + "nested/file1"
    fn = full_external_mount_name + "/nested/file1"
    data = b"hello\n"
    assert nested_file1_path in fs.find(full_external_mount_name)
    assert fs.exists(fn)
    assert not fs.exists(fn + "another")
    assert fs.info(fn)["size"] == len(data)
    with pytest.raises(FileNotFoundError):
        fs.info(fn + "another")


def test_du(fs):
    d = fs.du(full_external_mount_name, total=False)
    assert all(isinstance(v, int) and v >= 0 for v in d.values())
    bucket, namespace, key = fs.split_path(full_external_mount_name + "/test")
    test_bucket_with_namespace = bucket + "@" + namespace + "/"
    nested_file1_path = test_bucket_with_namespace + "nested/file1"
    assert nested_file1_path in d
    assert fs.du(full_external_mount_name + "/test/", total=True) == sum(
        map(len, files.values())
    )


def test_oci_ls(fs):
    bucket, namespace, key = fs.split_path(full_external_mount_name + "/test")
    test_bucket_with_namespace = bucket + "@" + namespace + "/"
    nested_file1_path = test_bucket_with_namespace + "nested/file1"
    assert nested_file1_path not in fs.ls(full_external_mount_name + "/")
    assert nested_file1_path in fs.ls(full_external_mount_name + "/nested/")
    assert nested_file1_path in fs.ls(full_external_mount_name + "/nested")


def test_glob(fs):
    fn = full_external_mount_name + "/nested/file1"
    assert fn not in fs.glob(full_external_mount_name + "/")
    assert fn not in fs.glob(full_external_mount_name + "/*")
    assert fn not in fs.glob(full_external_mount_name + "/nested")
    assert fn in fs.glob(full_external_mount_name + "/nested/*")
    assert fn in fs.glob(full_external_mount_name + "/nested/file*")
    assert fn in fs.glob(full_external_mount_name + "/*/*")
    assert [full_external_mount_name + "/nested/nested2"] == fs.glob(
        full_external_mount_name + "/nested/nested2"
    )
    out = fs.glob(full_external_mount_name + "/nested/nested2/*")
    assert {
        f"{full_external_mount_name}/nested/nested2/file1",
        f"{full_external_mount_name}/nested/nested2/file2",
    } == set(out)

    # Make sure glob() deals with the dot character (.) correctly.
    assert full_external_mount_name + "/file.dat" in fs.glob(
        full_external_mount_name + "/file.*"
    )
    assert full_external_mount_name + "/filexdat" not in fs.glob(
        full_external_mount_name + "/file.*"
    )


def test_oci_ls_detail(fs):
    L = fs.ls(full_external_mount_name + "/nested", detail=True)
    assert all(isinstance(item, CaseInsensitiveDict) for item in L)


def test_get(fs):
    data = files["test/accounts.1.json"]
    with fs.open(full_external_mount_name + "/test/accounts.1.json", "rb") as f:
        assert f.read() == data


def test_read_small(fs):
    fn = full_external_mount_name + "/2014-01-01.csv"
    with fs.open(fn, "rb", block_size=10) as f:
        out = []
        while True:
            data = f.read(3)
            if data == b"":
                break
            out.append(data)
        assert fs.cat(fn) == b"".join(out)
        assert len(f.cache) < len(out)


def test_read_oci_block(fs):
    data = files["test/accounts.1.json"]
    lines = io.BytesIO(data).readlines()
    path = full_external_mount_name + "/test/accounts.1.json"
    assert fs.read_block(path, 1, 35, b"\n") == lines[1]
    assert fs.read_block(path, 0, 30, b"\n") == lines[0]
    assert fs.read_block(path, 0, 35, b"\n") == lines[0] + lines[1]
    assert fs.read_block(path, 0, 5000, b"\n") == data
    assert len(fs.read_block(path, 0, 5)) == 5
    assert len(fs.read_block(path, 4, 5000)) == len(data) - 4
    assert fs.read_block(path, 5000, 5010) == b""
    assert fs.read_block(path, 5, None) == fs.read_block(path, 5, 1000)


def test_write_small(fs):
    with fs.open(a, "wb") as f:
        f.write(b"hello")
    assert fs.cat(a) == b"hello"
    fs.open(a, "wb").close()
    assert fs.info(a)["size"] == 0
    fs.rm(a, recursive=True)
    assert not fs.exists(a)


def test_write_fails(fs):
    with pytest.raises(ValueError):
        fs.touch(full_external_mount_name + "/temp")
        fs.open(full_external_mount_name + "/temp", "rb").write(b"hello")
    with pytest.raises(ValueError):
        fs.open(full_external_mount_name + "/temp", "wb", block_size=10)
    f = fs.open(full_external_mount_name + "/temp", "wb")
    f.close()
    with pytest.raises(ValueError):
        f.write(b"hello")
    with pytest.raises(FileNotFoundError):
        fs.open("nonexistentbucket@ns/temp", "wb").close()
    fs.rm(full_external_mount_name + "/temp", recursive=True)
    assert not fs.exists(full_external_mount_name + "/temp")


def test_write_blocks(fs):
    with fs.open(full_external_mount_name + "/temp", "wb") as f:
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
    assert fs.info(full_external_mount_name + "/temp")["size"] == 6 * 2**20
    with fs.open(
        full_external_mount_name + "/temp", "wb", block_size=10 * 2**20
    ) as f:
        f.write(b"a" * 15 * 2**20)
        assert f.buffer.tell() == 0
    assert fs.info(full_external_mount_name + "/temp")["size"] == 15 * 2**20
    fs.rm(full_external_mount_name + "/temp", recursive=True)
    assert not fs.exists(full_external_mount_name + "/temp")


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
    with fs.open(full_external_mount_name + "/2014-01-01.csv") as f:
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
    fn = full_external_mount_name + "/" + list(files)[0]
    with fs.open(fn) as f:
        assert f.blocksize == 20
    with fs.open(fn, block_size=40) as f:
        assert f.blocksize == 40


def test_text_io__stream_wrapper_works(fs):
    with fs.open(f"{full_external_mount_name}/file.txt", "wb") as fd:
        fd.write("\u00af\\_(\u30c4)_/\u00af".encode("utf-16-le"))

    with fs.open(f"{full_external_mount_name}/file.txt", "rb") as fd:
        with io.TextIOWrapper(fd, "utf-16-le") as stream:
            assert stream.readline() == "\u00af\\_(\u30c4)_/\u00af"

    fs.rm(f"{full_external_mount_name}/file.txt")
    assert not fs.exists(f"{full_external_mount_name}/file.txt")


def test_text_io__basic(fs):
    """Text mode is now allowed."""
    with fs.open(f"{full_external_mount_name}/file.txt", "w") as fd:
        fd.write("\u00af\\_(\u30c4)_/\u00af")

    with fs.open(f"{full_external_mount_name}/file.txt", "r") as fd:
        assert fd.read() == "\u00af\\_(\u30c4)_/\u00af"

    fs.rm(f"{full_external_mount_name}/file.txt")
    assert not fs.exists(f"{full_external_mount_name}/file.txt")


def test_text_io__override_encoding(fs):
    """Allow overriding the default text encoding."""
    with fs.open(f"{full_external_mount_name}/file.txt", "w", encoding="ibm500") as fd:
        fd.write("Hello, World!")

    with fs.open(f"{full_external_mount_name}/file.txt", "r", encoding="ibm500") as fd:
        assert fd.read() == "Hello, World!"

    fs.rm(f"{full_external_mount_name}/file.txt")
    assert not fs.exists(f"{full_external_mount_name}/file.txt")


def test_readinto(fs):
    with fs.open(f"{full_external_mount_name}/file.txt", "wb") as fd:
        fd.write(b"Hello, World!")

    contents = bytearray(15)

    with fs.open(f"{full_external_mount_name}/file.txt", "rb") as fd:
        assert fd.readinto(contents) == 13

    assert contents.startswith(b"Hello, World!")

    fs.rm(f"{full_external_mount_name}/file.txt")
    assert not fs.exists(f"{full_external_mount_name}/file.txt")


def test_autocommit():
    auto_file = full_external_mount_name + "/auto_file"
    committed_file = full_external_mount_name + "/commit_file"
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
    with pytest.raises(Exception):
        fo.commit()


def test_autocommit_mpu(fs):
    """When not autocommitting we always want to use multipart uploads"""
    path = full_external_mount_name + "/auto_commit_with_mpu"
    with fs.open(path, "wb", autocommit=False) as fo:
        fo.write(b"1")
    assert fo.mpu is not None
    assert len(fo.parts) == 1


def test_touch(fs):
    with fs.open(a, "wb") as f:
        f.write(b"data")
    assert fs.size(a) == 4
    fs.touch(a, truncate=True)
    assert fs.size(a) == 0


def test_seek_reads(fs):
    fn = full_external_mount_name + "/myfile"
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


def test_rename(fs):
    with fs.open(a, "wb") as f:
        f.write(b"data")
    assert fs.size(a) == 4
    fs.rename(a, b)
    assert fs.exists(b)
    assert fs.size(b) == 4


def test_rm(fs):
    assert not fs.exists(a)
    fs.touch(a)
    assert fs.exists(a)
    fs.rm(a)
    assert not fs.exists(a)


def test_bulk_delete(fs):
    filelist = fs.find(full_external_mount_name + "/nested")
    fs.bulk_delete([])
    fs.bulk_delete(filelist)
    assert not fs.exists(full_external_mount_name + "/nested/file1")
