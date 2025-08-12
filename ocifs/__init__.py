# coding: utf-8
# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import sys

from fsspec import register_implementation

from .core import OCIFileSystem
from .utils import __version__

if sys.version_info.major < 3:
    raise ImportError("Python < 3 is unsupported.")

register_implementation("oci", OCIFileSystem)
