=============
Release Notes
=============

.. toctree::
    :maxdepth: 2

1.2.1
-----
Release date: March 29, 2023

* Patch issue with region parameter being required for unknown signers


1.2.0
-----
Release date: March 24, 2023

* Filter ``ls`` to not show empty files with names ending in "/".
* Add ``sync`` method to allow copying folders between local and object storage.
* Update ``copy`` to forward requests to ``sync`` when one of the paths is local and the other is ``oci`` prefixed.
* Add ``oci-cli`` as an optional requirement.
* Create a default region upon instantiation of the filesystem instance.
