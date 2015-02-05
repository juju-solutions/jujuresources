.. Juju Resources documentation master file, created by
   sphinx-quickstart on Thu Feb  5 10:48:31 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Juju Resources's documentation!
==========================================

Juju Resources provides helpers for `Juju Charms`_ to load binary resources from
external sources, as well as tools for creating mirrors of external resources
for network-restricted deployments.

This is intended as a stop-gap until Juju has core support for resources,
as well as to prototype what features are needed.

Using Juju Resources in a Charm requires defining a set of resources in
a :doc:`resources.yaml <resource_definitions>` file, and then using the Python
API or the command-line to :func:`fetch <jujuresources.fetch_resources>`,
:func:`verify <jujuresources.verify_resources>`, and
:func:`reference <jujuresources.resource_path>` the resources.

.. toctree::
   :maxdepth: 3

   resource_definitions
   api/jujuresources
   cli



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _Juju Charms: https://juju.ubuntu.com/docs/
