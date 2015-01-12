import argparse
from pkg_resources import iter_entry_points

from jujuresources import fetch_resources
from jujuresources import verify_resources
from jujuresources import _load_resources


def arg(*args, **kwargs):
    """
    Decorator to add args to subcommands.
    """
    def _arg(f):
        if not hasattr(f, '_subcommand_args'):
            f._subcommand_args = []
        f._subcommand_args.append((args, kwargs))
        return f
    return _arg


def argset(name, *args, **kwargs):
    """
    Decorator to add sets of required mutually exclusive args to subcommands.
    """
    def _arg(f):
        if not hasattr(f, '_subcommand_argsets'):
            f._subcommand_argsets = {}
        f._subcommand_argsets.setdefault(name, []).append((args, kwargs))
        return f
    return _arg


def resources():
    """
    Juju CLI subcommand for dispatching resources subcommands.
    """
    eps = iter_entry_points('jujuresources.subcommands')
    ep_map = {ep.name: ep.load() for ep in eps}

    parser = argparse.ArgumentParser(
        description='Manage resources for a charm',
        epilog='\n'.join(
            ['Available subcommands:'] +
            ['    %s' % c for c in ep_map.keys()]),
    )
    subparsers = parser.add_subparsers()
    for name, subcommand in ep_map.iteritems():
        subparser = subparsers.add_parser(name, help=subcommand.__doc__)
        subparser.set_defaults(subcommand=subcommand)
        for args, kwargs in getattr(subcommand, '_subcommand_args', []):
            subparser.add_argument(*args, **kwargs)
        for argset in getattr(subcommand, '_subcommand_argsets', {}).values():
            group = subparser.add_mutually_exclusive_group(required=True)
            for args, kwargs in argset:
                group.add_argument(*args, **kwargs)
    opts = parser.parse_args()
    opts.subcommand(opts)


@arg('-r', '--resources', default='resources.yaml',
     help='YAML file containing the resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir',
     help='Directory to place the fetched resources (default ./resources/)')
@arg('-u', '--base-url',
     help='Base URL from which to fetch the resources (if given, only the '
          'filename portion will be used from the resource descriptions)')
def fetch(opts):
    """
    Attempt to fetch all resources for a charm
    """
    fetch_resources(opts.resources, opts.output_dir, opts.base_url)
    if verify_resources(None, opts.resources, opts.output_dir):
        print "All resources successfully downloaded"
    else:
        print "One or more resources failed to download correctly"


@argset('dest', '-u', '--unit', help='Unit to upload resources to')
@argset('dest', '-s', '--service', help='Service to upload resources to (all units of)')
@arg('-r', '--resources', default='resources.yaml',
     help='YAML file containing the resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir',
     help='Directory to place the fetched resources (default ./resources/)')
def upload(opts):
    """
    Upload resources from local copies to a deployed charm
    """
    raise NotImplementedError('Uploading resources is not yet implemented')
    resources = _load_resources(opts.resources)
    for name, resource in resources.iteritems():
        pass
