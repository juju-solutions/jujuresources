import contextlib
import subprocess
from urllib import urlopen

import yaml

from jujuresources.backend import ResourceContainer
from jujuresources.backend import ALL


__all__ = ['fetch', 'verify', 'resource_path', 'config_get', 'ALL']
resources_cache = {}


def config_get(option_name):
    """
    Helper to access a Juju config option when charmhelpers is not available.
    """
    try:
        raw = subprocess.check_output(['config-get', option_name, '--format=yaml'])
        return yaml.load(raw.decode('UTF-8'))
    except ValueError:
        return None


def _load(resources_yaml, output_dir=None):
    if (resources_yaml, output_dir) not in resources_cache:
        with contextlib.closing(urlopen(resources_yaml)) as fp:
            resdefs = yaml.load(fp)
        _output_dir = output_dir or resdefs.get('options', {}).get('output_dir', 'resources')
        resources = ResourceContainer(_output_dir)
        for name, resource in resdefs.get('resources', {}).iteritems():
            resources.add_required(name, resource)
        for name, resource in resdefs.get('optional_resources', {}).iteritems():
            resources.add_optional(name, resource)
        resources_cache[(resources_yaml, output_dir)] = resources
    return resources_cache[(resources_yaml, output_dir)]


def _invalid(resources, which):
    invalid = set()
    for resource in resources.subset(which):
        if not resource.verify():
            invalid.add(resource.name)
    return invalid


def _fetch(resources, which, mirror_url, force=False, reporthook=None):
    invalid = _invalid(resources, which)
    for resource in resources.subset(which):
        if resource.name not in invalid and not force:
            continue
        if reporthook:
            reporthook(resource.name)
        resource.fetch(mirror_url)


def invalid(which=None, resources_yaml='resources.yaml'):
    """
    Return a list of the names of the resources which do not
    pass :func:`verify`.

    :param list which: A name, or a list of one or more resource names, to
        fetch.  If ommitted, all non-optional resources are verified.
        You can also pass ``jujuresources.ALL`` to fetch all optional *and*
        required resources.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions (default: ``./resources.yaml``).
        Can be a local file name or a remote URL.
    """
    resources = _load(resources_yaml, None)
    return _invalid(resources, which)


def verify(which=None, resources_yaml='resources.yaml'):
    """
    Verify if some or all resources previously fetched with :func:`fetch_resources`,
    including validating their cryptographic hash.

    :param list which: A list of one or more resource names to
        check.  If ommitted, all non-optional resources are verified.
        You can also pass ``jujuresources.ALL`` to fetch all optional and
        required resources.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions (default: ``resources.yaml``).
        Can be a local file name or a remote URL.
    :param str output_dir: Override ``output_dir`` option from `resources_yaml`
        (this is intended for mirroring via the CLI and it is not recommended
        to be used otherwise)
    :return: True if all of the resources are available and valid, otherwise False.
    """
    resources = _load(resources_yaml, None)
    return not _invalid(resources, which)


def fetch(which=None, resources_yaml='resources.yaml',
          mirror_url=None, force=False, reporthook=None):
    """
    Attempt to fetch all resources for a charm.

    :param list which: A name, or a list of one or more resource names, to
        fetch.  If ommitted, all non-optional resources are fetched.
        You can also pass ``jujuresources.ALL`` to fetch all optional *and*
        required resources.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions (default: ``./resources.yaml``).
        Can be a local file name or a remote URL.
    :param str mirror_url: Override the location to fetch all resources from.
        If given, only the filename from the resource definitions are used,
        with the rest of the URL being ignored in favor of the given
        ``mirror_url``.
    :param force bool: Force re-downloading of valid resources.
    :param func reporthook: Callback for reporting download progress.
        Will be called once for each resource, just prior to fetching, and will
        be passed the resource name.
    :return: True or False indicating whether the resources were successfully
        downloaded.
    """
    resources = _load(resources_yaml, None)
    _fetch(resources, which, mirror_url, force, reporthook)
    return not _invalid(resources, which)


def resource_path(resource_name, resources_yaml='resources.yaml'):
    """
    Get the destination path for a named resource.

    :param str resource_name: The name of a resource to resolve.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions (default: ``./resources.yaml``).
        Can be a local file name or a remote URL.
    """
    resources = _load(resources_yaml, None)
    return resources[resource_name].destination
