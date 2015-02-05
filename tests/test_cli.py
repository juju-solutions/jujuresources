#!/usr/bin/env python

import mock
import unittest

import jujuresources.cli


class TestCLI(unittest.TestCase):
    resdefs = {
        'resources': {
            'valid': {}, 'invalid': {},
        },
        'all_resources': {
            'valid': {
                'url': 'valid',
                'filename': 'valid',
                'destination': 'res-defaults.yaml',
                'hash': '4f08575d804517cea2265a7d43022771',
                'hash_type': 'md5',
            },
            'invalid': {
                'url': 'invalid',
                'filename': 'invalid',
                'destination': 'res-defaults.yaml',
                'hash': 'deadbeef',
                'hash_type': 'md5',
            },
            'opt-invalid': {
                'url': 'opt-invalid',
                'filename': 'opt-invalid',
                'destination': 'res-defaults.yaml',
                'hash': 'deadbeef',
                'hash_type': 'md5',
            },
        }
    }

    @mock.patch('argparse.ArgumentParser._print_message')
    def test_resources_help(self, mprint_help):
        jujuresources.cli.resources(['help', 'fetch'])
        self.assertIn('usage: test_cli.py fetch', mprint_help.call_args_list[0][0][0])

    @mock.patch('jujuresources.cli.print')
    def test_resources_desc(self, mprint):
        jujuresources.cli.resources(['--description'])
        self.assertEqual(mprint.call_args_list[0][0][0], 'Manage and mirror charm resources')

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.reporthook')
    @mock.patch('jujuresources.cli.verify')
    @mock.patch('jujuresources.cli._fetch_resources')
    @mock.patch('jujuresources.cli._load_resources')
    def test_fetch(self, mload, mfetch, mverify, mreporthook, mexit):
        mload.return_value = self.resdefs
        mverify.return_value = -1
        jujuresources.cli.resources(['fetch'])
        mload.assert_called_once_with('resources.yaml', None)
        mreporthook.assert_called_once_with(False)
        mfetch.assert_called_once_with(
            self.resdefs, mock.ANY, None,
            False, mreporthook.return_value)
        self.assertItemsEqual(mfetch.call_args_list[0][0][1],
                              ['valid', 'invalid'])
        mexit.assert_called_once_with(-1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.reporthook')
    @mock.patch('jujuresources.cli.verify')
    @mock.patch('jujuresources.cli._fetch_resources')
    @mock.patch('jujuresources.cli._load_resources')
    def test_fetch_opts(self, mload, mfetch, mverify, mreporthook, mexit):
        mload.return_value = self.resdefs
        mverify.return_value = 1
        jujuresources.cli.resources(['fetch', '-r', 'r.y', '-d', 'od', '-u', 'url',
                                     '-a', '-q', '-f'])
        mload.assert_called_once_with('r.y', 'od')
        mreporthook.assert_called_once_with(True)
        mfetch.assert_called_once_with(
            self.resdefs, mock.ANY, 'url',
            True, mreporthook.return_value)
        self.assertItemsEqual(mfetch.call_args_list[0][0][1],
                              ['valid', 'invalid', 'opt-invalid'])
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.reporthook')
    @mock.patch('jujuresources.cli.verify')
    @mock.patch('jujuresources.cli._fetch_resources')
    @mock.patch('jujuresources.cli._load_resources')
    def test_fetch_names(self, mload, mfetch, mverify, mreporthook, mexit):
        mload.return_value = self.resdefs
        mverify.return_value = 2
        jujuresources.cli.resources(['fetch', 'foo', 'bar'])
        self.assertItemsEqual(mfetch.call_args_list[0][0][1],
                              ['foo', 'bar'])
        mexit.assert_called_once_with(2)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid_resources')
    @mock.patch('jujuresources.cli._load_resources')
    def test_verify(self, mload, minvalid, mprint, mexit):
        mload.return_value = self.resdefs
        minvalid.return_value = ['invalid']
        jujuresources.cli.resources(['verify'])
        mload.assert_called_once_with('resources.yaml', None)
        minvalid.assert_called_once_with(self.resdefs, mock.ANY)
        self.assertItemsEqual(minvalid.call_args_list[0][0][1],
                              ['valid', 'invalid'])
        mprint.assert_called_once_with('Invalid or missing resources: invalid')
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid_resources')
    @mock.patch('jujuresources.cli._load_resources')
    def test_verify_opts(self, mload, minvalid, mprint, mexit):
        mload.return_value = self.resdefs
        minvalid.return_value = ['invalid', 'opt-invalid']
        jujuresources.cli.resources(['verify', '-r', 'r.y', '-d', 'od',
                                     '-a', '-q'])
        mload.assert_called_once_with('r.y', 'od')
        minvalid.assert_called_once_with(self.resdefs, mock.ANY)
        self.assertItemsEqual(minvalid.call_args_list[0][0][1],
                              ['valid', 'invalid', 'opt-invalid'])
        assert not mprint.called
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid_resources')
    @mock.patch('jujuresources.cli._load_resources')
    def test_verify_names(self, mload, minvalid, mprint, mexit):
        mload.return_value = self.resdefs
        minvalid.return_value = []
        jujuresources.cli.resources(['verify', 'foo', 'bar'])
        minvalid.assert_called_once_with(self.resdefs, mock.ANY)
        self.assertItemsEqual(minvalid.call_args_list[0][0][1],
                              ['foo', 'bar'])
        mprint.assert_called_once_with('All resources successfully downloaded')
        mexit.assert_called_once_with(0)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._load_resources')
    def test_resource_path(self, mload, mprint, mexit):
        mload.return_value = self.resdefs
        jujuresources.cli.resources(['resource_path', 'valid'])
        mload.assert_called_once_with('resources.yaml', None)
        mprint.assert_called_once_with('res-defaults.yaml')
        mexit.assert_called_once_with(0)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.sys')
    @mock.patch('jujuresources.cli._load_resources')
    def test_resource_path_invalid_resource(self, mload, msys, mexit):
        mload.return_value = self.resdefs
        jujuresources.cli.resources(['resource_path', 'foo', '-d', 'od', '-r', 'r.y'])
        mload.assert_called_once_with('r.y', 'od')
        msys.stderr.write.assert_called_once_with('Invalid resource name: foo\n')
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli.SocketServer')
    @mock.patch('jujuresources.cli.os')
    @mock.patch('jujuresources.cli._load_resources')
    def test_serve(self, mload, mos, mSocketServer, mprint, mexit):
        mload.return_value = {'options': {'output_dir': 'myod'}}
        mos.path.exists.return_value = True
        jujuresources.cli.resources(['serve', '-H', 'host', '-p', '0000'])
        mos.chdir.assert_called_once_with('myod')
        self.assertIs(mSocketServer.TCPServer.allow_reuse_address, True)
        mSocketServer.TCPServer.assert_called_once_with(('host', '0000'), jujuresources.cli.SimpleHTTPRequestHandler)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli.SocketServer')
    @mock.patch('jujuresources.cli.os')
    @mock.patch('jujuresources.cli._load_resources')
    def test_serve_default_dir(self, mload, mos, mSocketServer, mprint, mexit):
        mload.return_value = {}
        mos.path.exists.return_value = True
        jujuresources.cli.resources(['serve', '-H', 'host', '-p', '0000'])
        mos.chdir.assert_called_once_with('resources')
        self.assertIs(mSocketServer.TCPServer.allow_reuse_address, True)
        mSocketServer.TCPServer.assert_called_once_with(('host', '0000'), jujuresources.cli.SimpleHTTPRequestHandler)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.sys')
    @mock.patch('jujuresources.cli.os')
    def test_serve_no_fetch(self, mos, msys, mexit):
        mos.path.exists.return_value = False
        jujuresources.cli.resources(['serve', '-d', 'od'])
        msys.stderr.write.assert_called_once_with("Resources dir 'od' not found.  Did you fetch?\n")
        mexit.assert_called_once_with(1)

    def test_reporthook_quiet(self):
        self.assertEqual(jujuresources.cli.reporthook(True), None)

    @mock.patch('jujuresources.cli.print')
    def test_reporthook(self, mprint):
        hook = jujuresources.cli.reporthook(False)
        hook(None, 0, 0, 0)
        assert not mprint.called
        hook('one', 0, 0, 0)
        mprint.assert_called_once_with('Fetching one...')
        mprint.reset_mock()
        hook('one', 0, 0, 0)
        hook('one', 0, 0, 0)
        assert not mprint.called
        hook('two', 0, 0, 0)
        mprint.assert_called_once_with('Fetching two...')


if __name__ == '__main__':
    unittest.main()
