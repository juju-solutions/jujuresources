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
API or the command-line to :func:`fetch <jujuresources.fetch>`,
:func:`verify <jujuresources.verify>`, and
:func:`reference <jujuresources.resource_path>` the resources.

If you are going to deploy one or more Charms that uses Juju Resources in an
environment with limited network connectivity, you can also manually create a
mirror of the Charms' resources by using the command-line to
:func:`fetch <jujuresources.cli.fetch>` them ahead of time, when you have
network access, and then :func:`serve <jujuresources.cli.serve>` the resources
to the charms when you deploy them.

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
