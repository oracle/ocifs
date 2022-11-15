.. Copyright (c) 2021, 2022 Oracle and/or its affiliates.
.. Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

.. ocifs documentation master file, created by
   sphinx-quickstart on Tue Mar 30 10:10:53 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

OCIFS
=====

Installation
------------
Install using pip:

.. code-block:: bash

   python3 -m pip install ocifs

Overview
---------

`ocifs`_ is a Pythonic filesystem interface to Oracle Cloud Infrastructure (OCI) Object Storage.  It builds on top of `oci`_.

The top-level class ``OCIFileSystem`` holds connection information and allows
typical file-system style operations like ``cp``, ``mv``, ``ls``, ``du``,
``glob``, as well as put/get of local files to/from OCI.

The connection gets validated via a configuration file (usually ~/.oci/config) or `Resource Principal`_.

Calling ``open()`` on a ``OCIFileSystem`` (typically using a context manager)
provides an ``OCIFile`` for read or write access to a particular key. The object
emulates the standard `file object`_ (``read``, ``write``, ``tell``,
``seek``), such that functions can interact with OCI Object Storage. Only
binary read and write modes are implemented, with blocked caching.

`ocifs`_ uses and is based upon `fsspec`_.


.. _fsspec: https://filesystem-spec.readthedocs.io/en/latest/
.. _Resource Principal: https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/signing.html?highlight=resource%20principal#resource-principals-signer
.. _file object: https://docs.python.org/3/glossary.html#term-file-object
.. _ocifs: https://pypi.org/project/ocifs/

Examples
--------

Simple locate and read a file:

.. code-block:: python

   >>> import ocifs
   >>> fs = ocifs.OCIFileSystem()
   >>> fs.ls('my-bucket@my-namespace')
   ['my-bucket@my-namespace/my-file.txt']
   >>> with fs.open('my-bucket@my-namespace/my-file.txt', 'rb') as f:
   ...     print(f.read())
   b'Hello, world'

(see also ``walk`` and ``glob`` in the Unix Operations section)

Reading with delimited blocks:

.. code-block:: python

   >>> fs.read_block(path, offset=1000, length=10, delimiter=b'\n')
   b'A whole line of text\n'

Learn more about `read_block`_.

Writing with blocked caching:

.. code-block:: python

   >>> fs = ocifs.OCIFileSystem(config=".oci/config")  # uses default credentials
   >>> with fs.open('mybucket@mynamespace/new-file', 'wb') as f:
   ...     f.write(2*2**20 * b'a')
   ...     f.write(2*2**20 * b'a') # data is flushed and file closed
   >>> fs.du('mybucket@mynamespace/new-file')
   {'mybucket@mynamespace/new-file': 4194304}

Learn more about ``fsspec``'s `caching system`_.

Because ``ocifs`` copies the Python file interface it can be used with
other projects that consume the file interface like ``gzip`` or ``pandas``.

.. code-block:: python

   >>> with fs.open('mybucket@mynamespace/my-file.csv.gz', 'rb') as f:
   ...     g = gzip.GzipFile(fileobj=f)  # Decompress data with gzip
   ...     df = pd.read_csv(g)           # Read CSV file with Pandas


.. _read_block: https://filesystem-spec.readthedocs.io/en/latest/api.html?highlight=read_block#fsspec.spec.AbstractFileSystem.read_block
.. _caching system: https://filesystem-spec.readthedocs.io/en/latest/features.html?highlight=cache#instance-caching


Integration
-----------

The libraries ``intake``, ``pandas`` and ``dask`` accept URLs with the prefix
"oci://", and will use ``ocifs`` to complete the IO operation in question. The
IO functions take an argument ``storage_options``, which will be passed verbatim
to ``OCIFileSystem``, for example:

.. code-block:: python

   df = pd.read_excel("oci://bucket@namespace/path/file.xls",
                      storage_options={"config": "~/.oci/config"})

Use the ``storage_options`` parameter to pass any additional arguments to ``ocifs``,
for example security credentials.


Authentication and Credentials
------------------------------

An OCI config file (API Keys) may be provided as a filepath or a config instance returned
from ``oci.config.from_file`` when creating an ``OCIFileSystem`` using the ``config`` argument.
For example, two valid inputs to the ``config`` argument are: ``oci.config.from_file("~/.oci/config")``
and ``~/.oci/config``. Specify the profile using the ``profile`` argument: ``OCIFileSystem(config="~/.oci/config", profile='PROFILE')``.

Alternatively a signer may be used to create an ``OCIFileSystem`` using the ``signer`` argument.
A Resource Principal Signer can be created using ``oci.auth.signers.get_resource_principals_signer()``.
An Instance Principal Signer can be created using ``oci.auth.signers.InstancePrincipalsSecurityTokenSigner()``
If neither config nor signer is provided, ``OCIFileSystem`` will attempt to create a Resource Principal, then an Instance Principal.
However, passing a signer directly is always preferred.

Learn more about using signers with `ocifs` in the Getting Connected tab, or learn more about `Resource Principal here`_.

.. _oci: https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/index.html
.. _Resource Principal here: https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/signing.html


Logging
-------

The logger named ``ocifs`` provides information about the operations of the file
system.  To see all messages, set the logging level to ``INFO``:

.. code-block:: python

   import logging
   logging.getLogger("ocifs").setLevel(logging.INFO)

Info mode will print messages to stderr. More advanced logging configuration is possible using
Python's standard `logging framework`_.

.. _logging framework: https://docs.python.org/3/library/logging.html


Limitations
-----------

This project is meant for convenience, rather than feature completeness.
The following are known current omissions:

- file access is always binary (although reading files line by line as strings is possible)

- no permissions/access-control (no ``chmod``/``chown`` methods)

- ``ocifs`` only reads the latest version of a file. Versioned support is on the roadmap for a future release.


A Note on Caching
-----------------
To save time and bandwidth, ocifs caches the results from listing buckets and objects. To refresh the cache,
set the ``refresh`` argument to ``True`` in the ``ls()`` method. However, ``info``, and as a result ``exists``,
ignores the cache and makes a call to Object Storage directly. If the underlying bucket is modified after a call
to list, the change will be reflected in calls to info, but not list (unless ``refresh=True``).


Contents
========

.. toctree::
   getting-started.ipynb
   getting-connected.ipynb
   unix-operations.ipynb
   modules.rst
   faqs_title.rst
   telemetry.rst
   :maxdepth: 4


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
