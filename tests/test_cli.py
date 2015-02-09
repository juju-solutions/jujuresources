import mock
import unittest

import jujuresources.cli
from jujuresources import ALL
from jujuresources.backend import ResourceContainer


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.resources = ResourceContainer('resources')
        self.resources.add_required('valid', {
            'url': 'valid',
            'filename': 'valid',
            'destination': 'res-defaults.yaml',
            'hash': '4f08575d804517cea2265a7d43022771',
            'hash_type': 'md5',
        })
        self.resources.add_required('invalid', {
            'url': 'invalid',
            'filename': 'invalid',
            'destination': 'res-defaults.yaml',
            'hash': 'deadbeef',
            'hash_type': 'md5',
        })
        self.resources.add_optional('opt-invalid', {
            'url': 'opt-invalid',
            'filename': 'opt-invalid',
            'destination': 'res-defaults.yaml',
            'hash': 'deadbeef',
            'hash_type': 'md5',
        })

        def mep(name, target):
            m = mock.Mock()
            m.name = name
            m.load.return_value = target
            return m
        self._piep = mock.patch.object(jujuresources.cli, 'iter_entry_points')
        self._miep = self._piep.start()
        self._miep.return_value = [
            mep('fetch', jujuresources.cli.fetch),
            mep('verify', jujuresources.cli.verify),
            mep('install', jujuresources.cli.install),
            mep('resource_path', jujuresources.cli.resource_path),
            mep('resource_spec', jujuresources.cli.resource_spec),
            mep('serve', jujuresources.cli.serve),
        ]

    def tearDown(self):
        self._piep.stop()

    @mock.patch('argparse.ArgumentParser._print_message')
    def test_resources_help(self, mprint_help):
        jujuresources.cli.resources(['help', 'fetch'])
        self.assertRegexpMatches(mprint_help.call_args_list[0][0][0], '^usage: [^ ]+ fetch')

    @mock.patch('jujuresources.cli.print')
    def test_resources_desc(self, mprint):
        jujuresources.cli.resources(['--description'])
        self.assertEqual(mprint.call_args_list[0][0][0], 'Manage and mirror charm resources')

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.verify')
    @mock.patch('jujuresources.cli._fetch')
    @mock.patch('jujuresources.cli._load')
    def test_fetch(self, mload, mfetch, mverify, mexit):
        mload.return_value = self.resources
        mverify.return_value = -1
        jujuresources.cli.resources(['fetch'])
        mload.assert_called_once_with('resources.yaml', None)
        mfetch.assert_called_once_with(self.resources, [], None, False, mock.ANY)
        self.assertIsNotNone(mfetch.call_args_list[0][0][4])
        mexit.assert_called_once_with(-1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.verify')
    @mock.patch('jujuresources.cli._fetch')
    @mock.patch('jujuresources.cli._load')
    def test_fetch_opts(self, mload, mfetch, mverify, mexit):
        mload.return_value = self.resources
        mverify.return_value = 1
        jujuresources.cli.resources(['fetch', '-r', 'r.y', '-d', 'od', '-u', 'url',
                                     '-a', '-q', '-f'])
        mload.assert_called_once_with('r.y', 'od')
        mfetch.assert_called_once_with(self.resources, ALL, 'url', True, None)
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.verify')
    @mock.patch('jujuresources.cli._fetch')
    @mock.patch('jujuresources.cli._load')
    def test_fetch_names(self, mload, mfetch, mverify, mexit):
        mload.return_value = self.resources
        mverify.return_value = 2
        jujuresources.cli.resources(['fetch', 'foo', 'bar'])
        self.assertItemsEqual(mfetch.call_args_list[0][0][1],
                              ['foo', 'bar'])
        mexit.assert_called_once_with(2)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid')
    @mock.patch('jujuresources.cli._load')
    def test_verify(self, mload, minvalid, mprint, mexit):
        mload.return_value = self.resources
        minvalid.return_value = ['invalid']
        jujuresources.cli.resources(['verify'])
        mload.assert_called_once_with('resources.yaml', None)
        minvalid.assert_called_once_with(self.resources, [])
        mprint.assert_called_once_with('Invalid or missing resources: invalid')
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid')
    @mock.patch('jujuresources.cli._load')
    def test_verify_opts(self, mload, minvalid, mprint, mexit):
        mload.return_value = self.resources
        minvalid.return_value = ['invalid', 'opt-invalid']
        jujuresources.cli.resources(['verify', '-r', 'r.y', '-d', 'od',
                                     '-a', '-q'])
        mload.assert_called_once_with('r.y', 'od')
        minvalid.assert_called_once_with(self.resources, ALL)
        assert not mprint.called
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid')
    @mock.patch('jujuresources.cli._load')
    def test_verify_names(self, mload, minvalid, mprint, mexit):
        mload.return_value = self.resources
        minvalid.return_value = []
        jujuresources.cli.resources(['verify', 'foo', 'bar'])
        minvalid.assert_called_once_with(self.resources, ['foo', 'bar'])
        mprint.assert_called_once_with('All resources successfully downloaded')
        mexit.assert_called_once_with(0)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._load')
    def test_resource_path(self, mload, mprint, mexit):
        mload.return_value = self.resources
        jujuresources.cli.resources(['resource_path', 'valid'])
        mload.assert_called_once_with('resources.yaml', None)
        mprint.assert_called_once_with('res-defaults.yaml')
        mexit.assert_called_once_with(0)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.sys')
    @mock.patch('jujuresources.cli._load')
    def test_resource_path_invalid_resource(self, mload, msys, mexit):
        mload.return_value = self.resources
        jujuresources.cli.resources(['resource_path', 'foo', '-d', 'od', '-r', 'r.y'])
        mload.assert_called_once_with('r.y', 'od')
        msys.stderr.write.assert_called_once_with('Invalid resource name: foo\n')
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli.SocketServer')
    @mock.patch('jujuresources.cli.backend')
    @mock.patch('jujuresources.cli.os')
    @mock.patch('jujuresources.cli._load')
    def test_serve(self, mload, mos, mbackend, mSocketServer, mprint, mexit):
        mload.return_value = self.resources
        mos.path.exists.return_value = True
        jujuresources.cli.resources(['serve', '-H', 'host', '-p', '9999'])
        mos.chdir.assert_called_once_with('resources')
        mbackend.PyPIResource.build_pypi_indexes.assert_called_with('resources')
        self.assertIs(mSocketServer.TCPServer.allow_reuse_address, True)
        mSocketServer.TCPServer.assert_called_once_with(('host', 9999), jujuresources.cli.SimpleHTTPRequestHandler)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli.SocketServer')
    @mock.patch('jujuresources.cli.backend')
    @mock.patch('jujuresources.cli.os')
    @mock.patch('jujuresources.cli._load')
    def test_serve_dir(self, mload, mos, mbackend, mSocketServer, mprint, mexit):
        mload.return_value = ResourceContainer('od')
        mos.path.exists.return_value = True
        jujuresources.cli.resources(['serve', '-d', 'od'])
        mload.assert_called_once_with('resources.yaml', 'od')
        mos.path.exists.assert_called_once_with('od')
        mbackend.PyPIResource.build_pypi_indexes.assert_called_with('od')
        mos.chdir.assert_called_once_with('od')
        self.assertIs(mSocketServer.TCPServer.allow_reuse_address, True)
        mSocketServer.TCPServer.assert_called_once_with(('', 8080), jujuresources.cli.SimpleHTTPRequestHandler)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.sys')
    @mock.patch('jujuresources.cli.os')
    @mock.patch('jujuresources.cli._load')
    def test_serve_no_fetch(self, mload, mos, msys, mexit):
        mload.return_value = ResourceContainer('od')
        mos.path.exists.return_value = False
        jujuresources.cli.resources(['serve', '-d', 'od'])
        msys.stderr.write.assert_called_once_with("Resources dir 'od' not found.  Did you fetch?\n")
        mexit.assert_called_once_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._install')
    @mock.patch('jujuresources.cli._load')
    def test_install(self, mload, minstall, mprint, mexit):
        mload.return_value = self.resources
        minstall.return_value = True
        jujuresources.cli.resources(['install'])
        mload.assert_called_once_with('resources.yaml', None)
        minstall.assert_called_once_with(self.resources, [], None, None, False)
        mprint.assert_called_with('All resources successfully installed')
        mexit.assert_called_with(0)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._invalid')
    @mock.patch('jujuresources.cli._install')
    @mock.patch('jujuresources.cli._load')
    def test_install_fail(self, mload, minstall, minvalid, mprint, mexit):
        mload.return_value = self.resources
        minstall.return_value = False
        minvalid.return_value = ['foo', 'bar']
        jujuresources.cli.resources(['install'])
        mload.assert_called_once_with('resources.yaml', None)
        minstall.assert_called_once_with(self.resources, [], None, None, False)
        mprint.assert_called_with('Unable to install some resources: foo, bar')
        mexit.assert_called_with(1)

    @mock.patch('jujuresources.cli._exit')
    @mock.patch('jujuresources.cli.print')
    @mock.patch('jujuresources.cli._install')
    @mock.patch('jujuresources.cli._load')
    def test_install_opts(self, mload, minstall, mprint, mexit):
        mload.return_value = self.resources
        minstall.return_value = False
        jujuresources.cli.resources(['install', '-r', 'r.y', '-d', 'od', '-u', 'url',
                                     '-D', 'dst', '-s', '-q', '-a'])
        mload.assert_called_once_with('r.y', 'od')
        minstall.assert_called_once_with(self.resources, ALL, 'url', 'dst', True)
        assert not mprint.called
        mexit.assert_called_with(1)


if __name__ == '__main__':
    unittest.main()
