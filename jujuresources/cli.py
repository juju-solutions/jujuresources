import os
import sys
import socket
import argparse
from pkg_resources import iter_entry_points
from SimpleHTTPServer import SimpleHTTPRequestHandler
import SocketServer

from jujuresources import _fetch_resources
from jujuresources import _verify_resources
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

    if '--description' in sys.argv:
        print 'Manage and mirror charm resources'
        return

    parser = argparse.ArgumentParser()
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
    opts = parser.parse_args()
    if opts.subcommand == 'help':
        if opts.command:
            subparsers[opts.command].print_help()
        else:
            parser.print_help()
    else:
        sys.exit(opts.subcommand(opts) or 0)


@arg('-r', '--resources', default='resources.yaml',
     help='File or URL containing the YAML resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir', default='resources',
     help='Directory to place the fetched resources (default ./resources/)')
@arg('-u', '--base-url',
     help='Base URL from which to fetch the resources (if given, only the '
          'filename portion will be used from the resource descriptions)')
def fetch(opts):
    """
    Create a local mirror of all resources (mandatory and optional) for a charm
    """
    resdefs = _load_resources(opts.resources, opts.output_dir)
    all_resources = resdefs['all_resources'].keys()

    def reporthook(name, block, block_size, total_size):
        if name != reporthook.last_name:
            if reporthook.last_name:
                print
            sys.stdout.write('Fetching {}'.format(name))
            reporthook.last_name = name
        tenth = int(block * block_size * 10 / total_size)
        if tenth != reporthook.last_tenth:
            sys.stdout.write('.' * (tenth - reporthook.last_tenth))
            reporthook.last_tenth = tenth
        sys.stdout.flush()
    reporthook.last_name = None
    reporthook.last_tenth = 0
    _fetch_resources(resdefs, all_resources, opts.base_url, reporthook=reporthook)
    print
    if _verify_resources(resdefs, all_resources):
        print "All resources successfully downloaded"
        return 0
    else:
        print "One or more resources failed to download correctly"
        return 1


@argset('dest', '-u', '--unit', help='Unit to upload resources to')
@argset('dest', '-s', '--service', help='Service to upload resources to (all units of)')
@arg('-r', '--resources', default='resources.yaml',
     help='File or URL containing the YAML resource descriptions (default: ./resources.yaml)')
@arg('-d', '--output-dir', default='resources',
     help='Directory containing the fetched resources (default ./resources/)')
def upload(opts):
    """
    Upload resources from local copies to a deployed charm
    """
    raise NotImplementedError('Uploading resources is not yet implemented')
    resources = _load_resources(opts.resources)
    for name, resource in resources.iteritems():
        pass


@arg('-d', '--output-dir', default='resources',
     help='Directory containing the fetched resources (default ./resources/)')
@arg('-H', '--host', default='',
     help='IP address on which to bind the mirror server')
@arg('-p', '--port', default=8080,
     help='Port on which to bind the mirror server')
def serve(opts):
    """
    Run a light-weight HTTP server hosting previously mirrored resources
    """
    os.chdir(opts.output_dir)
    SocketServer.TCPServer.allow_reuse_address = True
    httpd = SocketServer.TCPServer(("", opts.port), SimpleHTTPRequestHandler)

    print "Serving at: http://{}:{}/".format(socket.gethostname(), opts.port)
    httpd.serve_forever()
