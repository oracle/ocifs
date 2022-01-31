# coding: utf-8
# Copyright (c) 2021, 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from .core import OCIFileSystem
from fsspec import register_implementation
import json
import os
import sys

__version__ = "UNKNOWN"
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".version.json")
) as version_file:
    __version__ = json.load(version_file)["version"]

if sys.version_info.major < 3:
    raise ImportError("Python < 3 is unsupported.")

register_implementation("oci", OCIFileSystem)
