import os
import contextlib
from functools import partial
import hashlib
import subprocess
from urlparse import urlparse, urljoin
from urllib import urlretrieve, urlopen

import yaml


__all__ = ['fetch_resources', 'verify_resources', 'resource_path', 'config_get']
resources_cache = {}


class ALL(object):
    pass


def config_get(option_name):
    """
    Helper to access a Juju config option when charmhelpers is not available.
    """
    try:
        raw = subprocess.check_output(['config-get', option_name, '--format=yaml'])
        return yaml.load(raw.decode('UTF-8'))
    except ValueError:
        return None


def _load_resources(resources_yaml, output_dir=None):
    if (resources_yaml, output_dir) not in resources_cache:
        with contextlib.closing(urlopen(resources_yaml)) as fp:
            resources_cache[(resources_yaml, output_dir)] = resdefs = yaml.load(fp)
        _output_dir = output_dir or resdefs.get('options', {}).get('output_dir', 'resources')
        resdefs.setdefault('optional_resources', {})
        resdefs['all_resources'] = dict(resdefs['resources'], **resdefs['optional_resources'])
        for name, resource in resdefs['all_resources'].iteritems():
            resource.setdefault('url', '')
            resource.setdefault('hash', '')
            resource.setdefault('hash_type', '')
            resource.setdefault(
                'filename', os.path.basename(urlparse(resource['url']).path))
            resource.setdefault(
                'destination', os.path.join(_output_dir, resource['filename']))
    return resources_cache[(resources_yaml, output_dir)]


def _invalid_resources(resdefs, resources_to_check):
    invalid = set()
    if not resources_to_check:
        resources_to_check = resdefs['resources'].keys()
    if resources_to_check is ALL:
        resources_to_check = resdefs['all_resources'].keys()
    if not isinstance(resources_to_check, list):
        resources_to_check = [resources_to_check]
    for name in resources_to_check:
        resource = resdefs['all_resources'][name]
        if not os.path.isfile(resource['destination']):
            invalid.add(name)
            continue
        with open(resource['destination']) as fp:
            hash = hashlib.new(resource['hash_type'])
            hash.update(fp.read())
            if resource['hash'] != hash.hexdigest():
                invalid.add(name)
                continue
    return invalid


def _fetch_resources(resdefs, resources_to_fetch, base_url, force=False, reporthook=None):
    if not resources_to_fetch:
        resources_to_fetch = resdefs['resources'].keys()
    if resources_to_fetch is ALL:
        resources_to_fetch = resdefs['all_resources'].keys()
    if not isinstance(resources_to_fetch, list):
        resources_to_fetch = [resources_to_fetch]
    invalid = _invalid_resources(resdefs, resources_to_fetch)
    for name in resources_to_fetch:
        if name not in invalid and not force:
            continue
        resource = resdefs['all_resources'][name]
        if base_url:
            url = urljoin(base_url, resource['filename'])
        else:
            url = resource['url']
        if url.startswith('./'):
            url = url[2:]  # urlretrieve complains about this for some reason
        if not os.path.exists(os.path.dirname(resource['destination'])):
            os.makedirs(os.path.dirname(resource['destination']))
        try:
            _reporthook = partial(reporthook, name) if reporthook else None
            urlretrieve(url, resource['destination'], _reporthook)
        except IOError:
            continue


def verify_resources(resources_to_check=None, resources_yaml='resources.yaml'):
    """
    Verify if some or all resources previously fetched with :func:`fetch_resources`,
    including validating their cryptographic hash.

    :param list resources_to_check: A list of one or more resource names to
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
    resdefs = _load_resources(resources_yaml, None)
    return not _invalid_resources(resdefs, resources_to_check)


def fetch_resources(resources_to_fetch=None, resources_yaml='resources.yaml',
                    base_url=None, force=False, reporthook=None):
    """
    Attempt to fetch all resources for a charm.

    Note that errors fetching resources, incomplete or corrupted downloads,
    and other issues are silently ignored.  You should **always** call
    :func:`verify_resources` after this to confirm that everything was
    retrieved successfully.

    :param list resources_to_fetch: A list of one or more resource names to
        fetch.  If ommitted, all non-optional resources are fetched.
        You can also pass ``jujuresources.ALL`` to fetch all optional and
        required resources.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions (default: ``./resources.yaml``).
        Can be a local file name or a remote URL.
    :param str base_url: Override the location to fetch all resources from.
        If given, only the filename from the resource definitions are used,
        with the rest of the URL being ignored in favor of the given
        ``base_url``.
    :param force bool: Force re-downloading of valid resources.
    :param func reporthook: Callback for reporting download progress.
        Will be called with the arguments: resource name, current block,
        block size, and total size.
    """
    resdefs = _load_resources(resources_yaml, None)
    return _fetch_resources(resdefs, resources_to_fetch, base_url, force, reporthook)


def resource_path(resource_name, resources_yaml='resources.yaml'):
    """
    Get the destination path for a named resource.

    :param str resource_name: The name of a resource to resolve.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions (default: ``./resources.yaml``).
        Can be a local file name or a remote URL.
    """
    resdefs = _load_resources(resources_yaml, None)
    return resdefs['all_resources'][resource_name]['destination']
