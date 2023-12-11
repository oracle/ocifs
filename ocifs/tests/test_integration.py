# coding: utf-8
# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
import pandas as pd
import numpy as np
import os
import pytest
import oci
from ocifs import OCIFileSystem


namespace_name = os.environ["OCIFS_TEST_NAMESPACE"]
test_bucket_name = os.environ.get("OCIFS_TEST_BUCKET", "ocifs-test")
remote_folder = f"oci://{test_bucket_name}-int@{namespace_name}/sample_data"

iam_type = os.environ.get("OCIFS_IAM_TYPE", "api_key")
if iam_type == "api_key":
    config = oci.config.from_file("~/.oci/config")
    storage_options = {"config": config}


@pytest.fixture(autouse=True)
def reset_folder():
    oci_fs = OCIFileSystem(config=config)
    try:
        oci_fs.rm(remote_folder, recursive=True)
    except FileNotFoundError:
        pass
    yield


def test_rw_small():
    sample_data = {"A": [1, 2], "B": [3, 4]}
    small_fn = os.path.join(remote_folder, "small.csv")

    df = pd.DataFrame(sample_data)
    df.to_csv(small_fn, index=False, storage_options=storage_options)
    df_reloaded = pd.read_csv(small_fn, storage_options=storage_options)
    assert df_reloaded.equals(df)


def test_rw_large():
    sample_data = {
        "A": np.arange(10000),
        "B": np.arange(10000) * 2,
        "C": np.arange(10000) * 3,
    }
    large_fn = os.path.join(remote_folder, "large.csv")

    df = pd.DataFrame(sample_data)
    df.to_csv(large_fn, index=False, storage_options=storage_options)
    df_reloaded = pd.read_csv(large_fn, storage_options=storage_options)
    assert df_reloaded.equals(df)


def test_new_bucket():
    storage_options2 = {
        "create_parents": True,
    }
    storage_options2.update(storage_options)
    sample_data = {"A": [1, 2], "B": [3, 4]}
    small_fn = os.path.join(remote_folder, "small.csv")

    df = pd.DataFrame(sample_data)
    df.to_csv(small_fn, index=False, storage_options=storage_options2)

    df_reloaded = pd.read_csv(small_fn, storage_options=storage_options2)
    assert df_reloaded.equals(df)


def test_dask_extra_large():
    # TODO: read something larger than memory into dask dataframe
    pass
