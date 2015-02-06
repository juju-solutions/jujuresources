#!/usr/bin/env python

import mock
import os
import unittest

import jujuresources


class TestAPI(unittest.TestCase):
    test_data = os.path.join(os.path.dirname(__file__), 'data')

    def setUp(self):
        self.resources = jujuresources.backend.ResourceContainer('resources')
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
        for resource in self.resources.all():
            resource.fetch = mock.Mock()
            resource.verify = mock.Mock(return_value='invalid' not in resource.name)

    def test_load_defaults(self):
        resources = jujuresources._load(os.path.join(self.test_data, 'res-defaults.yaml'))
        self.assertItemsEqual(resources._required, set(['foo', 'bar']))
        self.assertItemsEqual(resources.keys(), ['foo', 'bar', 'qux'])

        self.assertEqual(resources['foo'].url, 'http://foo.com/foo.tgz')
        self.assertEqual(resources['foo'].hash, 'deadbeef1')
        self.assertEqual(resources['foo'].hash_type, 'nonce')
        self.assertEqual(resources['foo'].filename, 'foo.tgz')
        self.assertEqual(resources['foo'].destination, 'resources/foo.tgz')

        self.assertEqual(resources['bar'].url, 'http://bar.com/bar.tgz')
        self.assertEqual(resources['bar'].hash, 'deadbeef2')
        self.assertEqual(resources['bar'].hash_type, 'nonce')
        self.assertEqual(resources['bar'].filename, 'BAR')
        self.assertEqual(resources['bar'].destination, 'custom/bar')

        self.assertEqual(resources['qux'].url, 'http://qux.com/qux.tgz')
        self.assertEqual(resources['qux'].hash, 'deadbeef3')
        self.assertEqual(resources['qux'].hash_type, 'nonce')
        self.assertEqual(resources['qux'].filename, 'qux.tgz')
        self.assertEqual(resources['qux'].destination, 'resources/qux.tgz')

    def test_load_options(self):
        resfile = os.path.join(self.test_data, 'res-options.yaml')
        resources = jujuresources._load(resfile)
        self.assertEqual(resources['foo'].destination, 'custom/foo.tgz')
        resources = jujuresources._load(resfile, 'different')
        self.assertEqual(resources['foo'].destination, 'different/foo.tgz')

    def test_invalid(self):
        self.assertItemsEqual(jujuresources._invalid(self.resources, 'valid'), [])
        self.assertItemsEqual(jujuresources._invalid(self.resources, 'invalid'), ['invalid'])
        self.assertItemsEqual(jujuresources._invalid(self.resources, 'opt-invalid'), ['opt-invalid'])
        self.assertItemsEqual(jujuresources._invalid(self.resources, None), ['invalid'])
        self.assertItemsEqual(jujuresources._invalid(self.resources, []), ['invalid'])

    @mock.patch('jujuresources._invalid')
    def test_fetch(self, minvalid):
        minvalid.return_value = set(['invalid'])
        jujuresources._fetch(self.resources, None, 'mirror')
        self.resources['invalid'].fetch.assert_called_once_with('mirror')
        assert not self.resources['valid'].fetch.called
        assert not self.resources['opt-invalid'].fetch.called

    @mock.patch('jujuresources._invalid')
    def test_fetch_force(self, minvalid):
        minvalid.return_value = set(['invalid'])
        jujuresources._fetch(self.resources, [], None, force=True)
        self.resources['invalid'].fetch.assert_called_once_with(None)
        self.resources['valid'].fetch.assert_called_once_with(None)
        assert not self.resources['opt-invalid'].fetch.called

    @mock.patch('jujuresources._invalid')
    def test_fetch_reporthook(self, minvalid):
        reporthook = mock.Mock()
        minvalid.return_value = set(['invalid', 'opt-invalid'])
        jujuresources._fetch(self.resources, jujuresources.ALL, 'mirror', reporthook=reporthook)
        self.resources['invalid'].fetch.assert_called_once_with('mirror')
        assert not self.resources['valid'].fetch.called
        self.resources['opt-invalid'].fetch.assert_called_once_with('mirror')
        reporthook.assert_has_calls([
            mock.call('invalid'),
            mock.call('opt-invalid'),
        ], any_order=True)
        self.assertNotIn(mock.call('valid'), reporthook.call_args_list)

    @mock.patch.object(jujuresources, '_load')
    def test_resource_path(self, mload):
        mload.return_value = self.resources
        self.assertEqual(jujuresources.resource_path('valid'), 'res-defaults.yaml')


if __name__ == '__main__':
    unittest.main()
