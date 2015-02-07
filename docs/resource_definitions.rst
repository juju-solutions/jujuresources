========================================
Resource Defintions (``resources.yaml``)
========================================

Resources are described in a ``resources.yaml`` file, which can contain
the following sections:

* ``resources``
* ``optional_resources``
* ``options``


``resources`` Section
=====================

The file **must** contain a ``resources`` section containing a mapping of
resource names to definitions.  Definitions should be mappings with one of
the following sets of keys:

**URL Resources**

  * ``url`` URL for the resource
  * ``hash`` Cryptographic hash for the resource
  * ``hash_type`` Algorithm used to generate the hash; e.g., md5, sha512, etc.

**PyPI Resources**

  * ``pypi`` A Python package requirement spec, such as ``jujuresources>=0.2``.

**Local or Bundled File Resources**

  * ``file`` Path to local file (can be relative to ``$CHARM_DIR``)
  * ``hash`` Cryptographic hash for the resource
  * ``hash_type`` Algorithm used to generate the hash; e.g., md5, sha512, etc.


``optional_resources`` Section
==============================

The file may contain an ``optional_resources`` section containing a mapping
of resource names to defintions.  These take the same form as the required
resource definitions.

Optional resources will not be fetched or verified by default, and must
either be explicitly named, or the ``all`` option given.


``options`` Section
===================

The file may contain an ``options`` section, which supports the
following options:

* ``output_dir`` Location for the fetched resources (default: ``./resources``)

Example
=======

An example ``resources.yaml`` might be::

    resources:
        charmhelpers:
            pypi: charmhelpers>=0.2.2
        pyaml:
            pypi: pyaml>=3.11
    optional_resources:
        java-x86_64:
            url: http://jr-packages.s3-website-us-east-1.amazonaws.com/ibm/x86_64/java.bin
            hash: b377b7cccdd281bc5e4c4071f80e84a3
            hash_type: md5
        java-amd:
            url: http://jr-packages.s3-website-us-east-1.amazonaws.com/ibm/amd.bin
            hash: e0c54b25e2199c3bb325520d9f9d047a
            hash_type: md5
    options:
        ouptut_dir: /var/share/resources
