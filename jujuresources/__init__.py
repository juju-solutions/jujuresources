import os
import hashlib
from urlparse import urlparse, urljoin
from urllib import urlretrieve

import yaml


def _load_resources(resources_yaml):
    """
    Parse `resources.yaml` file and remap the values for easier use.
    """
    with open(resources_yaml) as fp:
        resources = yaml.load(fp).get('resources', {})
    for name, resource in resources.iteritems():
        filename = os.path.basename(urlparse(resource['url']).path)
        resource.update({
            'name': name,
            'filename': filename,
        })
    return resources


def verify_resources(resources_to_check=None, resources_yaml='resources.yaml', output_dir=None):
    """
    Verify if some or all of the resources were successfully fetched,
    including validating their cryptographic hash.

    :param list resources_to_check: A list of one or more resource names to
        check.  If ommitted, all resources are verified.
    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions  Defaults to `resources.yaml` in the current
        directory.
    :param str output_dir: Directory in which the fetched resources were placed.
        Defaults to `resources/` in the current directory.
    :return: True if all of the resources are available and valid, otherwise False.
    """
    resources = _load_resources(resources_yaml)
    if output_dir is None:
        output_dir = 'resources'
    if resources_to_check is None:
        resources_to_check = resources.keys()
    for name in resources_to_check:
        resource = resources[name]
        filename = os.path.join(output_dir, resource['filename'])
        if not os.path.exists(filename):
            return False
        with open(filename) as fp:
            hash = hashlib.new(resource['hash_type'])
            hash.update(fp.read())
            if resource['hash'] != hash.hexdigest():
                return False
    return True


def fetch_resources(resources_yaml='resources.yaml', output_dir=None, base_url=None):
    """
    Attempt to fetch all resources for a charm.

    Resources are described in a `resources.yaml` file, which should contain
    a `resources` item containing a mapping of resource names to definitions.
    Definitions should be mappings with the following keys:

      * *url* URL for the resource
      * *hash* Cryptographic hash for the resource
      * *hash_type* Algorithm used to generate the hash; e.g., md5, sha512, etc.

    Note that errors fetching resources, incomplete or corrupted downloads,
    and other issues are silently ignored.  You should *always* call
    :func:`verify_resources` after this to confirm that everything was
    retrieved successfully.

    :param str resources_yaml: Location of the yaml file containing the
        resource descriptions  Defaults to `resources.yaml` in the current
        directory.
    :param str output_dir: Directory in which to place the fetched resources.
        Defaults to `resources/` in the current directory.
    :param str base_url: Base URL from which to fetch the resources.  If
        given, only the filename from the resource descriptions are used,
        with the rest of the URLs being ignored in favor of the given
        `base_url`.
    """
    resources = _load_resources(resources_yaml)
    if output_dir is None:
        output_dir = 'resources'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for name, resource in resources.iteritems():
        if base_url:
            url = urljoin(base_url, resource['filename'])
        else:
            url = resource['url']
        dest = os.path.join(output_dir, resource['filename'])
        try:
            urlretrieve(url, dest)
        except IOError:
            continue
