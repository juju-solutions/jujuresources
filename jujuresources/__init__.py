import os
import hashlib
from urlparse import urlparse, urljoin
from urllib import urlretrieve

import yaml


resources_cache = {}


def _load_resources(resources_yaml):
    """
    Parse `resources.yaml` file and remap the values for easier use.
    """
    if resources_yaml not in resources_cache:
        with open(resources_yaml) as fp:
            resources_cache[resources_yaml] = resdefs = yaml.load(fp)
        output_dir = resdefs.get('options', {}).get('output_dir', 'resources')
        for name, resource in resdefs['resources'].iteritems():
            resource.setdefault(
                'filename', os.path.basename(urlparse(resource['url']).path))
            resource.setdefault(
                'destination', os.path.join(output_dir, resource['filename']))
    return resources_cache[resources_yaml]['resources']


def verify_resources(resources_to_check=None, resources_yaml='resources.yaml'):
    """
    Verify if some or all resources previously fetched with :func:`fetch_resources`,
    including validating their cryptographic hash.

    :param list resources_to_check: A list of one or more resource names to
        check.  If ommitted, all resources are verified.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions  Defaults to `resources.yaml` in the current
        directory.
    :return: True if all of the resources are available and valid, otherwise False.
    """
    resources = _load_resources(resources_yaml)
    if resources_to_check is None:
        resources_to_check = resources.keys()
    for name in resources_to_check:
        resource = resources[name]
        if not os.path.exists(resource['destination']):
            return False
        with open(resource['destination']) as fp:
            hash = hashlib.new(resource['hash_type'])
            hash.update(fp.read())
            if resource['hash'] != hash.hexdigest():
                return False
    return True


def fetch_resources(resources_yaml='resources.yaml', base_url=None):
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

    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions  Defaults to `resources.yaml` in the current
        directory.
    :param str base_url: Override the location to fetch all resources from.
        If given, only the filename from the resource definitions are used,
        with the rest of the URL being ignored in favor of the given
        `base_url`.
    """
    resources = _load_resources(resources_yaml)
    for name, resource in resources.iteritems():
        if base_url:
            url = urljoin(base_url, resource['filename'])
        else:
            url = resource['url']
        if url.startswith('./'):
            url = url[2:]  # urlretrieve complains about this for some reason
        if not os.path.exists(os.path.dirname(resource['dest'])):
            os.makedirs(os.path.dirname(resource['destination']))
        try:
            urlretrieve(url, resource['destination'])
        except IOError:
            continue


def resource_path(resource_name, resources_yaml='resources.yaml'):
    """
    Get the destination path for a named resource.
    """
    resources = _load_resources(resources_yaml)
    return resources[resource_name]['destination']
