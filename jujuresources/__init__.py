import os
import hashlib
from urlparse import urlparse, urljoin
from urllib import urlretrieve

import yaml


resources_cache = {}


def _load_resources(resources_yaml, output_dir=None):
    """
    Parse `resources.yaml` file and remap the values for easier use.
    """
    if resources_yaml not in resources_cache:
        with open(resources_yaml) as fp:
            resources_cache[resources_yaml] = resdefs = yaml.load(fp)
        output_dir = output_dir or resdefs.get('options', {}).get('output_dir', 'resources')
        resdefs.setdefault('optional_resources', {})
        resdefs['all_resources'] = dict(resdefs['resources'], **resdefs['optional_resources'])
        for name, resource in resdefs['all_resources'].iteritems():
            resource.setdefault(
                'filename', os.path.basename(urlparse(resource['url']).path))
            resource.setdefault(
                'destination', os.path.join(output_dir, resource['filename']))
    return resources_cache[resources_yaml]


def _verify_resources(resdefs, resources_to_check):
    if resources_to_check is None:
        resources_to_check = resdefs['resources'].keys()
    for name in resources_to_check:
        resource = resdefs['all_resources'][name]
        if not os.path.exists(resource['destination']):
            return False
        with open(resource['destination']) as fp:
            hash = hashlib.new(resource['hash_type'])
            hash.update(fp.read())
            if resource['hash'] != hash.hexdigest():
                return False
    return True


def _fetch_resources(resdefs, resources_to_fetch, base_url):
    if resources_to_fetch is None:
        resources_to_fetch = resdefs['resources'].keys()
    for name in resources_to_fetch:
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
            urlretrieve(url, resource['destination'])
        except IOError:
            continue


def verify_resources(resources_to_check=None, resources_yaml='resources.yaml'):
    """
    Verify if some or all resources previously fetched with :func:`fetch_resources`,
    including validating their cryptographic hash.

    :param list resources_to_check: A list of one or more resource names to
        check.  If ommitted, all non-optional resources are verified.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions  Defaults to `resources.yaml` in the current
        directory.
    :param str output_dir: Override `output_dir` option from `resources_yaml`
        (this is intended for mirroring via the CLI and it is not recommended
        to be used otherwise)
    :return: True if all of the resources are available and valid, otherwise False.
    """
    resdefs = _load_resources(resources_yaml, None)
    return _verify_resources(resdefs, resources_to_check)


def fetch_resources(resources_to_fetch=None, resources_yaml='resources.yaml', base_url=None):
    """
    Attempt to fetch all resources for a charm.

    Resources are described in a `resources.yaml` file, which should contain
    a `resources` item containing a mapping of resource names to definitions.
    Definitions should be mappings with the following keys:

      * *url* URL for the resource
      * *hash* Cryptographic hash for the resource
      * *hash_type* Algorithm used to generate the hash; e.g., md5, sha512, etc.

    The file may also contain an `options` section, which supports the
    following options:

      * *output_dir* Location for the fetched resources (default `./resources`)

    Note that errors fetching resources, incomplete or corrupted downloads,
    and other issues are silently ignored.  You should *always* call
    :func:`verify_resources` after this to confirm that everything was
    retrieved successfully.

    :param list resources_to_fetch: A list of one or more resource names to
        fetch.  If ommitted, all non-optional resources are fetched.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions  Defaults to `resources.yaml` in the current
        directory.
    :param str base_url: Override the location to fetch all resources from.
        If given, only the filename from the resource definitions are used,
        with the rest of the URL being ignored in favor of the given
        `base_url`.
    :param str output_dir: Override `output_dir` option from `resources_yaml`
        (this is intended for mirroring via the CLI and it is not recommended
        to be used otherwise)
    """
    resdefs = _load_resources(resources_yaml, None)
    return _fetch_resources(resdefs, resources_to_fetch, base_url)


def resource_path(resource_name, resources_yaml='resources.yaml'):
    """
    Get the destination path for a named resource.
    """
    resdefs = _load_resources(resources_yaml, None)
    return resdefs['all_resources'][resource_name]['destination']
