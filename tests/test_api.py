#!/usr/bin/env python

import mock
import os
import unittest

import jujuresources


class TestAPI(unittest.TestCase):
    test_data = os.path.join(os.path.dirname(__file__), 'data')
    resdefs = {
        'resources': {
            'valid': {}, 'invalid': {},
        },
        'all_resources': {
            'valid': {
                'url': 'valid',
                'filename': 'valid',
                'destination': os.path.join(test_data, 'res-defaults.yaml'),
                'hash': '4f08575d804517cea2265a7d43022771',
                'hash_type': 'md5',
            },
            'invalid': {
                'url': 'invalid',
                'filename': 'invalid',
                'destination': os.path.join(test_data, 'res-defaults.yaml'),
                'hash': 'deadbeef',
                'hash_type': 'md5',
            },
            'opt-invalid': {
                'url': 'opt-invalid',
                'filename': 'opt-invalid',
                'destination': os.path.join(test_data, 'res-defaults.yaml'),
                'hash': 'deadbeef',
                'hash_type': 'md5',
            },
        }
    }

    def test__load_resources_defaults(self):
        resdefs = jujuresources._load_resources(os.path.join(self.test_data, 'res-defaults.yaml'))
        self.assertEqual(resdefs, {
            'resources': {
                'foo': {
                    'url': 'http://foo.com/foo.tgz',
                    'hash': 'deadbeef1',
                    'hash_type': 'nonce',
                    'filename': 'foo.tgz',
                    'destination': 'resources/foo.tgz',
                },
                'bar': {
                    'url': 'http://bar.com/bar.tgz',
                    'hash': 'deadbeef2',
                    'hash_type': 'nonce',
                    'filename': 'BAR',
                    'destination': 'custom/bar',
                },
            },
            'optional_resources': {
                'qux': {
                    'url': 'http://qux.com/qux.tgz',
                    'hash': 'deadbeef3',
                    'hash_type': 'nonce',
                    'filename': 'qux.tgz',
                    'destination': 'resources/qux.tgz',
                },
            },
            'all_resources': {
                'foo': {
                    'url': 'http://foo.com/foo.tgz',
                    'hash': 'deadbeef1',
                    'hash_type': 'nonce',
                    'filename': 'foo.tgz',
                    'destination': 'resources/foo.tgz',
                },
                'bar': {
                    'url': 'http://bar.com/bar.tgz',
                    'hash': 'deadbeef2',
                    'hash_type': 'nonce',
                    'filename': 'BAR',
                    'destination': 'custom/bar',
                },
                'qux': {
                    'url': 'http://qux.com/qux.tgz',
                    'hash': 'deadbeef3',
                    'hash_type': 'nonce',
                    'filename': 'qux.tgz',
                    'destination': 'resources/qux.tgz',
                },
            },
        })

    def test__load_resources_options(self):
        resfile = os.path.join(self.test_data, 'res-options.yaml')
        resdefs = jujuresources._load_resources(resfile)
        self.assertEqual(resdefs['resources']['foo']['destination'], 'custom/foo.tgz')
        resdefs = jujuresources._load_resources(resfile, 'different')
        self.assertEqual(resdefs['resources']['foo']['destination'], 'different/foo.tgz')

    def test__invalid_resources(self):
        self.assertItemsEqual(jujuresources._invalid_resources(self.resdefs, 'valid'), [])
        self.assertItemsEqual(jujuresources._invalid_resources(self.resdefs, 'invalid'), ['invalid'])
        self.assertItemsEqual(jujuresources._invalid_resources(self.resdefs, 'opt-invalid'), ['opt-invalid'])
        self.assertItemsEqual(jujuresources._invalid_resources(self.resdefs, None), ['invalid'])

    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(jujuresources, 'urlretrieve')
    def test__fetch_resources(self, murlretrieve, mmakedirs):
        dest = os.path.join(self.test_data, 'res-defaults.yaml')
        jujuresources._fetch_resources(self.resdefs, None, '')
        murlretrieve.assert_called_once_with('invalid', dest, None)

        murlretrieve.reset_mock()
        jujuresources._fetch_resources(self.resdefs, 'opt-invalid', '')
        murlretrieve.assert_called_once_with('opt-invalid', dest, None)

        murlretrieve.reset_mock()
        jujuresources._fetch_resources(self.resdefs, ['invalid', 'opt-invalid'], 'http://example.com/')
        self.assertEqual(murlretrieve.call_args_list, [
            mock.call('http://example.com/invalid', dest, None),
            mock.call('http://example.com/opt-invalid', dest, None),
        ])

        murlretrieve.reset_mock()
        jujuresources._fetch_resources(self.resdefs, [], '', force=True)
        self.assertItemsEqual(murlretrieve.call_args_list, [
            mock.call('valid', dest, None),
            mock.call('invalid', dest, None),
        ])

    @mock.patch.object(jujuresources, '_load_resources')
    def test_resource_path(self, m_load_resources):
        dest = os.path.join(self.test_data, 'res-defaults.yaml')
        m_load_resources.return_value = self.resdefs
        self.assertEqual(jujuresources.resource_path('valid'), dest)


if __name__ == '__main__':
    unittest.main()
