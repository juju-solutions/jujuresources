Juju Resources provides helpers for charms to load binary resources from
external sources, as well as tools for creating mirrors of external resources
for network-restricted deployments.

This is intended as a stop-gap until Juju has core support for resources,
as well as to prototype what features are needed.


Installing
----------

Install Juju Resources using pip:

    pip install jujuresources


Charm Usage
-----------

A charm using Juju Resources will need to define a ``resources.yaml``,
such as::

    resources:
        my_resource:
            url: http://example.com/path/to/my_resource.tgz
            hash: b377b7cccdd281bc5e4c4071f80e84a3
            hash_type: sha256
    optional_resources:
        my_optional_resource:
            url: http://example.com/path/to/my_optional_resource.tgz
            hash: 476881ef4012262dfc8adc645ee786c4
            hash_type: sha256

Then, once the charm has installed Juju Resources, it can fetch
and verify resources, either in Python::

    from jujuresources import fetch_resources, verify_resources, config_get

    fetch_resources(base_url=config_get('resources_mirror'))
    if not verify_resources():
        print "Mandatory resources did not download; check resources_mirror option"
        sys.exit(1)

    fetch_resources('my_optional_resource', base_url=config_get('resources_mirror'))
    if verify_resources('my_optional_resource'):
        install_tgz(resource_path('my_optional_resource'))

Or via the command-line / bash::

    juju-resources fetch -u `config-get resources_mirror`
    if ! juju-resources verify; then
        echo "Mandatory resources did not download; check resources_mirror option"
        exit 1
    fi

    juju-resources fetch -u `config-get resources_mirror` my_optional_resource
    if juju-resources verify my_optional_resource; then
        actions/install_tgz `juju-resources resource_path my_optional_resource`
    fi


Mirroring Resources
-------------------

You can also create a local mirror for deploying in network-restricted environments::

    mkdir local_mirror
    juju-resources fetch --all -d local_mirror -r http://github.com/me/my-charm/blob/master/resources.yaml
    juju-resources serve -d local_mirror

You will then have a lightweight HTTP server running to which you can set the
charm's ``resources_mirror`` (or equivalent) config option to point to,
serving all (``--all``, optional as well as required) resources defined in the
remote ``resources.yaml`` (``-r <url-or-file>``), which are cached in the
``local_mirror`` directory (``-d local_mirror``).
