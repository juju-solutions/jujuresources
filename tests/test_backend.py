#!/usr/bin/env python

import mock
import os
import unittest

from jujuresources import backend


class TestResourceContainer(unittest.TestCase):
    @mock.patch.object(backend.Resource, 'get')
    def test_add_required(self, mget):
        rc = backend.ResourceContainer('od')
        rc.add_required('name', 'resource')
        self.assertIn('name', rc._required)
        mget.assert_called_once_with('name', 'resource', 'od')
        self.assertIn('name', rc)
        self.assertEqual(rc['name'], mget.return_value)

    @mock.patch.object(backend.Resource, 'get')
    def test_add_optional(self, mget):
        rc = backend.ResourceContainer('od')
        rc.add_optional('name', 'resource')
        self.assertNotIn('name', rc._required)
        mget.assert_called_once_with('name', 'resource', 'od')
        self.assertIn('name', rc)
        self.assertEqual(rc['name'], mget.return_value)

    def test_all(self):
        rc = backend.ResourceContainer('od')
        rc['req'] = 'foo'
        rc['opt'] = 'bar'
        rc._required.add('req')
        self.assertItemsEqual(rc.all(), ['foo', 'bar'])

    def test_required(self):
        rc = backend.ResourceContainer('od')
        rc['req'] = 'foo'
        rc['opt'] = 'bar'
        rc._required.add('req')
        self.assertItemsEqual(rc.required(), ['foo'])

    def test_subset(self):
        rc = backend.ResourceContainer('od')
        rc['req'] = 'foo'
        rc['opt'] = 'bar'
        rc['rq2'] = 'qux'
        rc._required.add('req')
        rc._required.add('rq2')
        self.assertItemsEqual(rc.subset(None), ['foo', 'qux'])
        self.assertItemsEqual(rc.subset([]), ['foo', 'qux'])
        self.assertItemsEqual(rc.subset(backend.ALL), ['foo', 'bar', 'qux'])
        self.assertItemsEqual(rc.subset('opt'), ['bar'])
        self.assertItemsEqual(rc.subset(['opt', 'rq2']), ['bar', 'qux'])


class TestResource(unittest.TestCase):
    test_data = os.path.join(os.path.dirname(__file__), 'data')

    def test_get(self):
        self.assertIsInstance(
            backend.Resource.get('name', {'url': 'foo'}, 'od'),
            backend.URLResource)
        self.assertIsInstance(
            backend.Resource.get('name', {'filename': 'foo'}, 'od'),
            backend.Resource)
        self.assertRaises(NotImplementedError,
                          backend.Resource.get, 'name', {'pip': 'foo'}, 'od')

    def test_init(self):
        res = backend.Resource('name', {
            'filename': 'fn',
            'hash': 'hash',
            'hash_type': 'hash_type',
        }, 'od')
        self.assertEqual(res.name, 'name')
        self.assertEqual(res.filename, 'fn')
        self.assertEqual(res.destination, 'od/fn')
        self.assertEqual(res.hash, 'hash')
        self.assertEqual(res.hash_type, 'hash_type')
        self.assertEqual(res.output_dir, 'od')

    def test_init_empty(self):
        res = backend.Resource('name', {}, 'od')
        self.assertEqual(res.name, 'name')
        self.assertEqual(res.filename, '')
        self.assertEqual(res.destination, 'od/')
        self.assertEqual(res.hash, '')
        self.assertEqual(res.hash_type, '')

    def test_init_explicit_destination(self):
        res = backend.Resource('name', {
            'filename': 'fn',
            'destination': 'dst'
        }, 'od')
        self.assertEqual(res.destination, 'dst')

    def test_fetch(self):
        res = backend.Resource('name', {'filename': 'fn'}, 'od')
        res.fetch()
        res.fetch('mirror')

    def test_verify(self):
        res = backend.Resource('name', {
            'filename': 'res-defaults.yaml',
            'hash': '4f08575d804517cea2265a7d43022771',
            'hash_type': 'md5',
        }, self.test_data)
        assert res.verify()

    def test_verify_invalid(self):
        res = backend.Resource('name', {
            'filename': 'res-defaults.yaml',
            'hash': 'deadbeef',
            'hash_type': 'md5',
        }, self.test_data)
        assert not res.verify()

    def test_verify_missing(self):
        res = backend.Resource('name', {
            'filename': 'nonce',
            'hash': '4f08575d804517cea2265a7d43022771',
            'hash_type': 'md5',
        }, self.test_data)
        assert not res.verify()


class TestURLResource(unittest.TestCase):
    def test_init(self):
        res = backend.URLResource('name', {
            'url': 'http://example.com/fn',
            'hash': 'hash',
            'hash_type': 'hash_type',
        }, 'od')
        self.assertEqual(res.url, 'http://example.com/fn')
        self.assertEqual(res.filename, 'fn')
        self.assertEqual(res.destination, 'od/fn')
        self.assertEqual(res.hash, 'hash')
        self.assertEqual(res.hash_type, 'hash_type')

    def test_init_empty(self):
        res = backend.URLResource('name', {}, 'od')
        self.assertEqual(res.url, '')
        self.assertEqual(res.filename, '')
        self.assertEqual(res.destination, 'od/')
        self.assertEqual(res.hash, '')
        self.assertEqual(res.hash_type, '')
        self.assertEqual(res.output_dir, 'od')

    def test_init_explicit_filename(self):
        res = backend.URLResource('name', {
            'url': 'http://example.com/fn',
            'filename': 'myfn'
        }, 'od')
        self.assertEqual(res.filename, 'myfn')
        self.assertEqual(res.destination, 'od/myfn')

    def test_init_explicit_destination(self):
        res = backend.URLResource('name', {
            'url': 'http://example.com/fn',
            'destination': 'dst'
        }, 'od')
        self.assertEqual(res.destination, 'dst')

    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(backend, 'urlretrieve')
    def test_fetch(self, murlretrieve, mexists, mmakedirs):
        res = backend.URLResource('name', {
            'url': 'http://example.com/path/fn',
            'hash': 'hash',
            'hash_type': 'hash_type',
        }, 'od')
        mexists.return_value = True
        res.fetch()
        assert not mmakedirs.called
        murlretrieve.assert_called_with('http://example.com/path/fn', 'od/fn')

        mexists.return_value = False
        res.fetch('http://mirror.com/')
        mmakedirs.assert_called_with('od')
        murlretrieve.assert_called_with('http://mirror.com/fn', 'od/fn')


if __name__ == '__main__':
    unittest.main()
