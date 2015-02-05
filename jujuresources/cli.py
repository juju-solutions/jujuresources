from __future__ import print_function
import os
import sys
import socket
import argparse
from pkg_resources import iter_entry_points
from SimpleHTTPServer import SimpleHTTPRequestHandler
import SocketServer

from jujuresources import _fetch_resources
from jujuresources import _invalid_resources
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


print = print  # for testing
_exit = sys.exit  # for testing


def resources(argv=sys.argv[1:]):
    """
    Juju CLI subcommand for dispatching resources subcommands.
    """
    eps = iter_entry_points('jujuresources.subcommands')
    ep_map = {ep.name: ep.load() for ep in eps}

    parser = argparse.ArgumentParser()
    if '--description' in argv:
        print('Manage and mirror charm resources')
        return 0

    subparsers = {}
    subparser_factory = parser.add_subparsers()
    subparsers['help'] = subparser_factory.add_parser('help', help='Display help for a subcommand')
    subparsers['help'].add_argument('command', nargs='?')
    subparsers['help'].set_defaults(subcommand='help')
    for name, subcommand in ep_map.iteritems():
        subparsers[name] = subparser_factory.add_parser(name, help=subcommand.__doc__)
        subparsers[name].set_defaults(subcommand=subcommand)
        for args, kwargs in getattr(subcommand, '_subcommand_args', []):
            subparsers[name].add_argument(*args, **kwargs)
        for argset in getattr(subcommand, '_subcommand_argsets', {}).values():
            group = subparsers[name].add_mutually_exclusive_group(required=True)
            for args, kwargs in argset:
                group.add_argument(*args, **kwargs)
    opts = parser.parse_args(argv)
    if opts.subcommand == 'help':
        if opts.command:
            subparsers[opts.command].print_help()
        else:
            parser.print_help()
    else:
        return _exit(opts.subcommand(opts) or 0)


def reporthook(quiet):
    if quiet:
        return None
    closure_data = {'last_name': None}  # gotta love closure scoping rules :/

    def _reporthook(name, block, block_size, total_size):
        if name != closure_data['last_name']:
            print('Fetching {}...'.format(name))
            closure_data['last_name'] = name
    return _reporthook


@arg('-r', '--resources', default='resources.yaml',
     help='File or URL containing the YAML resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir', default=None,
     help='Directory to place the fetched resources (default: ./resources/)')
@arg('-u', '--base-url',
     help='Base URL from which to fetch the resources (if given, only the '
          'filename portion will be used from the resource descriptions)')
@arg('-a', '--all', action='store_true',
     help='Include all optional resources as well as required')
@arg('-q', '--quiet', action='store_true',
     help='Suppress output and only set the return code')
@arg('-f', '--force', action='store_true',
     help='Force re-download of valid resources')
@arg('resource_names', nargs='*',
     help='Names of specific resources to fetch (defaults to all required, '
          'or all if --all is given)')
def fetch(opts):
    """
    Create a local mirror of all resources (mandatory and optional) for a charm
    """
    resdefs = _load_resources(opts.resources, opts.output_dir)
    required_resources = resdefs['resources'].keys()
    all_resources = resdefs['all_resources'].keys()
    if not opts.resource_names:
        opts.resource_names = all_resources if opts.all else required_resources
    _fetch_resources(resdefs, opts.resource_names, opts.base_url,
                     opts.force, reporthook(opts.quiet))
    return verify(opts)


@arg('-r', '--resources', default='resources.yaml',
     help='File or URL containing the YAML resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir', default=None,
     help='Directory containing the fetched resources (default: ./resources/)')
@arg('-a', '--all', action='store_true',
     help='Include all optional resources as well as required')
@arg('-q', '--quiet', action='store_true',
     help='Suppress output and only set the return code')
@arg('resource_names', nargs='*',
     help='Names of specific resources to verify (defaults to all required, '
          'or all if --all is given)')
def verify(opts):
    """
    Create a local mirror of all resources (mandatory and optional) for a charm
    """
    resdefs = _load_resources(opts.resources, opts.output_dir)
    required_resources = resdefs['resources'].keys()
    all_resources = resdefs['all_resources'].keys()
    if not opts.resource_names:
        opts.resource_names = all_resources if opts.all else required_resources

    invalid = _invalid_resources(resdefs, opts.resource_names)
    if not invalid:
        if not opts.quiet:
            print("All resources successfully downloaded")
        return 0
    else:
        if not opts.quiet:
            print("Invalid or missing resources: {}".format(', '.join(invalid)))
        return 1


@arg('-r', '--resources', default='resources.yaml',
     help='File or URL containing the YAML resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir', default=None,
     help='Directory containing the fetched resources (default: ./resources/)')
@arg('resource_name', help='Name of a resource')
def resource_path(opts):
    """
    Return the full path to a named resource.
    """
    resdefs = _load_resources(opts.resources, opts.output_dir)
    if opts.resource_name not in resdefs['all_resources']:
        sys.stderr.write('Invalid resource name: {}\n'.format(opts.resource_name))
        return 1
    print(resdefs['all_resources'][opts.resource_name]['destination'])


@arg('-r', '--resources', default='resources.yaml',
     help='File or URL containing the YAML resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir', default=None,
     help='Directory containing the fetched resources (default: ./resources/)')
@arg('-H', '--host', default='',
     help='IP address on which to bind the mirror server')
@arg('-p', '--port', default=8080,
     help='Port on which to bind the mirror server')
def serve(opts):
    """
    Run a light-weight HTTP server hosting previously mirrored resources
    """
    if not opts.output_dir:
        resdefs = _load_resources(opts.resources, opts.output_dir)
        opts.output_dir = resdefs.get('options', {}).get('output_dir', 'resources')
    if not os.path.exists(opts.output_dir):
        sys.stderr.write("Resources dir '{}' not found.  Did you fetch?\n".format(opts.output_dir))
        return 1
    os.chdir(opts.output_dir)
    SocketServer.TCPServer.allow_reuse_address = True
    httpd = SocketServer.TCPServer((opts.host, opts.port), SimpleHTTPRequestHandler)

    print("Serving at: http://{}:{}/".format(socket.gethostname(), opts.port))
    httpd.serve_forever()
