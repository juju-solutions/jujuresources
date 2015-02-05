Resource Defintions (``resources.yaml``)
========================================

Resources are described in a ``resources.yaml`` file, which can contain
the following sections:

* ``resources``
* ``optional_resources``
* ``options``


``resources``
-------------

The file **must** contain a ``resources`` section containing a mapping of
resource names to definitions.  Definitions should be mappings with the
following keys:

  * ``url`` URL for the resource
  * ``hash`` Cryptographic hash for the resource
  * ``hash_type`` Algorithm used to generate the hash; e.g., md5, sha512, etc.


``optional_resources``
----------------------

The file may contain an ``optional_resources`` section containing a mapping
of resource names to defintions.  These take the same form as the required
resource definitions.

Optional resources will not be fetched or verified by default, and must
either be explicitly named, or the ``all`` option given.


``options``
-----------

The file may contain an ``options`` section, which supports the
following options:

* ``output_dir`` Location for the fetched resources (default: ``./resources``)
