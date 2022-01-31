#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2021, 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

import io
import json
import os
from setuptools import setup


def open_relative(*path):
    """
    Opens files in read-only with a fixed utf-8 encoding.
    All locations are relative to this setup.py file.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(here, *path)
    return io.open(filename, mode="r", encoding="utf-8")


with open_relative("ocifs", ".version.json") as version_file:
    OCIFS_VERSION = json.load(version_file)["version"]
    if not OCIFS_VERSION:
        raise RuntimeError("Cannot find version information")

with open_relative("README.md") as f:
    readme = f.read()

setup(
    name="ocifs",
    version=OCIFS_VERSION,
    url="https://docs.oracle.com/en-us/iaas/tools/ocifs-sdk/latest/index.html#",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Universal Permissive License (UPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Convenient filesystem interface over Oracle Cloud's Object Storage",
    maintainer="Allen Hosler",
    maintainer_email="allen.hosler@oracle.com",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="UPL",
    keywords="Oracle Cloud Infrastructure, OCI, Object Storage",
    packages=["ocifs"],
    python_requires=">= 3.6",
    include_package_data=True,
    install_requires=[open("requirements.txt").read().strip().split("\n")],
    zip_safe=False,
)
