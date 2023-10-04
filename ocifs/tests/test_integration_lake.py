# coding: utf-8
# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

import pandas as pd
import os
import pytest
import oci
from ocifs import OCIFileSystem

config = oci.config.from_file("~/.oci/config", profile_name='iad_prod')
full_external_mount_name = os.environ["OCIFS_EXTERNAL_MOUNT_URI"]
storage_options = {"config": config}


@pytest.fixture(autouse=True)
def reset_folder():
    oci_fs = OCIFileSystem(config=config, profile='iad_prod')
    try:
        if oci_fs.lexists(full_external_mount_name + "/a/employees.csv"):
            oci_fs.rm(full_external_mount_name + "/a/employees.csv")
    except FileNotFoundError:
        pass
    yield


def test_rw_small():
    users = {'Name': ['Amit', 'Cody', 'Drew'],
             'Age': [20, 21, 25]}
    # create DataFrame
    df = pd.DataFrame(users, columns=['Name', 'Age'])
    df.to_csv(full_external_mount_name + "/a/employees.csv", index=False, header=True, storage_options=storage_options)
    df_reloaded = pd.read_csv(full_external_mount_name + "/a/employees.csv", storage_options=storage_options)
    assert df_reloaded.equals(df)