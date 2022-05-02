============
Development
============

The target audience for this README is developers wanting to contribute to ocifs, Oracle
Cloud Infrastructure (OCI) Object Storage implementation of fsspec's filesystem.
If you want to use the SDK with your own programs, see README.rst.

Getting Started
===============
Assuming that you have Python and `virtualenv` installed, set up your environment and install the required dependencies like this:

.. code-block:: sh

    git clone https://github.com/oracle/ocifs.git
    cd ocifs
    virtualenv ocifs-env
    . ocifs-env/bin/activate
    python3 -m pip install -r requirements.txt
    python3 -m pip install -e .

You should also set up your configuration files, see the `SDK and CLI Configuration File`__.

__ https://docs.cloud.oracle.com/Content/API/Concepts/sdkconfig.htm

Running Tests
=============
The SDK uses `pytest` as its test framework. You can run tests against Python 3.6+ using the `tox` command. Note that this requires that you have those versions of Python installed,
or you must pass `-e` or run tests directly:

.. code-block:: sh

    # This runs tests against all configured Pythons in tox.ini (3.6+). You must have those versions installed.
    tox

    # This runs tests against a specific Python version:
    tox -e py36

If you want to run an individual test, then run:

.. code-block:: sh

    python -m pytest ocifs/tests/test_spec.py::test_simple


Specifying environment variables
--------------------------------
In addition to a valid config file for your tenancy, the tests also require the following environment
variables to be set:

    * ``OCIFS_TEST_NAMESPACE``: The namespace of a bucket in Object Storage to use for testing.
    * ``OCIFS_TEST_BUCKET``: The bucket in Object Storage to use for testing.


Checking Style
==============
The ocifs SDK adheres to PEP8 style guilds, and uses Flake8 to validate style.  There are some exceptions and they can
be viewed in the ``setup.cfg`` file.

There is a pre-commit hook setup for this repo. To use this pre-commit hook, run the following:

.. code-block:: sh
    python3 -m pip install pre-commit
    pre-commit install


Signing Commits
================
Please ensure that all commits are signed following the process outlined here:
https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits


Generating Documentation
========================
Sphinx is used for documentation. You can generate HTML locally with the following:

.. code-block:: sh

    python3 -m pip install -r requirements.txt
    cd docs
    make html

Generating the wheel
====================
The SDK is packaged as a wheel. To generate the wheel, you can run:

.. code-block:: sh

    python setup.py sdist bdist_wheel

This wheel can then be installed using `pip`.
