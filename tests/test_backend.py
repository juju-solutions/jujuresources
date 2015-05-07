#!/usr/bin/env python

import mock
import os
import unittest
import shutil
import subprocess
from tempfile import mkdtemp

from jujuresources import backend

if not hasattr(unittest.TestCase, 'assertItemsEqual'):
    # for Python 3.  assertCountEqual is a stupid name
    unittest.TestCase.assertItemsEqual = unittest.TestCase.assertCountEqual


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
        self.assertIsInstance(
            backend.Resource.get('name', {'pypi': 'foo'}, 'od'),
            backend.PyPIResource)

    def test_init(self):
        res = backend.Resource('name', {
            'file': 'path/fn',
            'hash': 'hash',
            'hash_type': 'hash_type',
        }, 'od')
        self.assertEqual(res.name, 'name')
        self.assertEqual(res.source, 'path/fn')
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
            'file': 'fn',
            'destination': 'dst'
        }, 'od')
        self.assertEqual(res.destination, 'dst')

    def test_fetch(self):
        res = backend.Resource('name', {'file': 'fn'}, 'od')
        res.fetch()
        res.fetch('mirror')

    def test_verify(self):
        res = backend.Resource('name', {
            'file': 'res-defaults.yaml',
            'hash': '4f08575d804517cea2265a7d43022771',
            'hash_type': 'md5',
        }, self.test_data)
        assert res.verify()

    def test_verify_invalid(self):
        res = backend.Resource('name', {
            'file': 'res-defaults.yaml',
            'hash': 'deadbeef',
            'hash_type': 'md5',
        }, self.test_data)
        assert not res.verify()

    def test_verify_missing(self):
        res = backend.Resource('name', {
            'file': 'nonce',
            'hash': '4f08575d804517cea2265a7d43022771',
            'hash_type': 'md5',
        }, self.test_data)
        assert not res.verify()

    def test_install_invalid(self):
        res = backend.Resource('name', {
            'file': 'res-defaults.yaml',
            'hash': 'deadbeef',
            'hash_type': 'md5',
        }, self.test_data)
        tmpdir = mkdtemp()
        try:
            assert not res.install(tmpdir)
            self.assertEqual(os.listdir(tmpdir), [])
        finally:
            shutil.rmtree(tmpdir)

    def test_install_tgz(self):
        res = backend.Resource('name', {
            'file': 'test.tgz',
            'hash': '347153cce7f15a6d3e47d34fbccb6afa',
            'hash_type': 'md5',
        }, self.test_data)
        tmpdir = mkdtemp()
        try:
            assert res.install(tmpdir)
            self.assertItemsEqual(os.listdir(tmpdir), ['toplevel'])
            self.assertItemsEqual(os.listdir(os.path.join(tmpdir, 'toplevel')), ['foo', 'bar'])
        finally:
            shutil.rmtree(tmpdir)

    def test_install_tgz_skip_top_level(self):
        res = backend.Resource('name', {
            'file': 'test.tgz',
            'hash': '347153cce7f15a6d3e47d34fbccb6afa',
            'hash_type': 'md5',
        }, self.test_data)
        tmpdir = mkdtemp()
        os.rmdir(tmpdir)
        try:
            assert res.install(tmpdir, skip_top_level=True)
            self.assertItemsEqual(os.listdir(tmpdir), ['foo', 'bar'])
            self.assertItemsEqual(os.listdir(os.path.join(tmpdir, 'bar')), ['qux'])
        finally:
            shutil.rmtree(tmpdir)

    @mock.patch('tarfile.is_tarfile', mock.Mock(return_value=False))
    def test_install_tgz_workaround(self):
        self.test_install_tgz()

    @mock.patch('tarfile.is_tarfile', mock.Mock(return_value=False))
    def test_install_tgz_skip_top_level_workaround(self):
        self.test_install_tgz_skip_top_level()

    def test_install_zip(self):
        res = backend.Resource('name', {
            'file': 'test.zip',
            'hash': '5c7b6a3c4bf38ac9d2f0ab0088fff1a9',
            'hash_type': 'md5',
        }, self.test_data)
        tmpdir = mkdtemp()
        try:
            assert res.install(tmpdir)
            self.assertItemsEqual(os.listdir(tmpdir), ['toplevel'])
            self.assertItemsEqual(os.listdir(os.path.join(tmpdir, 'toplevel')), ['foo', 'bar'])
        finally:
            shutil.rmtree(tmpdir)

    def test_install_zip_skip_top_level(self):
        res = backend.Resource('name', {
            'file': 'test.zip',
            'hash': '5c7b6a3c4bf38ac9d2f0ab0088fff1a9',
            'hash_type': 'md5',
        }, self.test_data)
        tmpdir = mkdtemp()
        try:
            assert res.install(tmpdir, skip_top_level=True)
            self.assertItemsEqual(os.listdir(tmpdir), ['foo', 'bar'])
            self.assertItemsEqual(os.listdir(os.path.join(tmpdir, 'bar')), ['qux'])
        finally:
            shutil.rmtree(tmpdir)

    def test_install_file(self):
        res = backend.Resource('name', {
            'file': 'res-defaults.yaml',
            'hash': '4f08575d804517cea2265a7d43022771',
            'hash_type': 'md5',
        }, self.test_data)
        tmpdir = mkdtemp()
        try:
            assert res.install(tmpdir)
            self.assertEqual(os.listdir(tmpdir), ['res-defaults.yaml'])
        finally:
            shutil.rmtree(tmpdir)


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

    @mock.patch.object(os, 'remove')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(backend, 'urlretrieve')
    def test_fetch(self, murlretrieve, mexists, mmakedirs, mremove):
        res = backend.URLResource('name', {
            'url': 'http://example.com/path/fn',
            'hash': 'hash',
            'hash_type': 'hash_type',
        }, 'od')
        mexists.return_value = True
        res.fetch()
        assert not mmakedirs.called
        mremove.assert_called_with('od/fn')
        murlretrieve.assert_called_with('http://example.com/path/fn', 'od/fn')

        mexists.return_value = False
        res.fetch('http://mirror.com/')
        mmakedirs.assert_called_with('od')
        murlretrieve.assert_called_with('http://mirror.com/fn', 'od/fn')

    @mock.patch.object(backend, 'urlopen')
    @mock.patch.object(os, 'remove')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(backend, 'urlretrieve')
    def test_fetch_hash_url(self, murlretrieve, mexists, mmakedirs, mremove, murlopen):
        res = backend.URLResource('name', {
            'url': 'http://example.com/path/fn',
            'hash': 'http://hash.com/',
            'hash_type': 'hash_type',
        }, 'od')
        mexists.return_value = True
        murlopen.return_value.read.return_value = 'myhash'
        res.fetch()
        assert not mmakedirs.called
        mremove.assert_called_with('od/fn')
        murlretrieve.assert_called_with('http://example.com/path/fn', 'od/fn')
        murlopen.assert_called_with('http://hash.com/')
        self.assertEqual(res.hash, 'myhash')


class TestPyPIResource(unittest.TestCase):
    test_data = os.path.join(os.path.dirname(__file__), 'data')

    def test_init(self):
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, 'od')
        self.assertEqual(res.spec, 'jujuresources>=0.2')
        self.assertEqual(res.package_name, 'jujuresources')
        self.assertEqual(res.destination_dir, 'od/jujuresources')
        self.assertEqual(res.filename, '')
        self.assertEqual(res.destination, '')
        self.assertEqual(res.hash, '')
        self.assertEqual(res.hash_type, '')
        res = backend.PyPIResource('name', {'pypi': 'http://example.com/foo#egg=jujuresources'}, 'od')
        self.assertEqual(res.spec, 'http://example.com/foo#egg=jujuresources')
        self.assertEqual(res.package_name, 'jujuresources')
        self.assertEqual(res.filename, 'foo')
        self.assertEqual(res.destination, 'od/foo')
        res = backend.PyPIResource('name', {'pypi': 'http://example.com/foo'}, 'od')
        self.assertEqual(res.package_name, '')
        self.assertEqual(res.filename, 'foo')
        self.assertEqual(res.destination, 'od/foo')
        res = backend.PyPIResource('name', {'pypi': 'foo', 'hash': 'h', 'hash_type': 'ht'}, 'od')
        self.assertEqual(res.hash, 'h')
        self.assertEqual(res.hash_type, 'ht')

    @mock.patch.object(os, 'listdir')
    @mock.patch.object(backend, 'subprocess')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(shutil, 'rmtree')
    @mock.patch.object(os.path, 'exists')
    def test_fetch(self, mexists, mrmtree, mmakedirs, msubprocess, mlistdir):
        mexists.return_value = False
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, 'od')
        res.get_remote_hash = mock.Mock()
        res._write_file = mock.Mock()
        res.process_dependency = mock.Mock()
        mlistdir.return_value = ['pyaml-3.0.tgz', 'jujuresources-0.2.tgz']
        res.get_remote_hash.return_value = ('hash_type', 'hash')
        res.fetch()
        assert not mrmtree.called
        mmakedirs.assert_called_with(res.destination_dir)
        msubprocess.check_output.assert_called_once_with(
            ['pip', 'install', 'jujuresources>=0.2',
                '--download', 'od/jujuresources'],
            stderr=msubprocess.STDOUT)
        res.get_remote_hash.assert_called_once_with(
            'jujuresources-0.2.tgz', 'https://pypi.python.org/simple/')
        res._write_file.assert_called_once_with(
            'od/jujuresources/jujuresources-0.2.tgz.hash_type', 'hash\n')
        self.assertEqual(res.filename, 'jujuresources-0.2.tgz')
        self.assertEqual(res.destination, 'od/jujuresources/jujuresources-0.2.tgz')
        self.assertEqual(res.hash, 'hash')
        self.assertEqual(res.hash_type, 'hash_type')
        res.process_dependency.assert_called_once_with(
            'pyaml-3.0.tgz', 'https://pypi.python.org/simple/')

    @mock.patch.object(os, 'listdir')
    @mock.patch.object(backend, 'subprocess')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(shutil, 'rmtree')
    @mock.patch.object(os.path, 'exists')
    def test_fetch_mirror(self, mexists, mrmtree, mmakedirs, msubprocess, mlistdir):
        mexists.return_value = True
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, 'od')
        res.get_remote_hash = mock.Mock()
        res._write_file = mock.Mock()
        res.process_dependency = mock.Mock()
        mlistdir.return_value = ['pyaml-3.0.tgz', 'jujuresources-0.2.tgz']
        res.get_remote_hash.return_value = ('hash_type', 'hash')
        res.fetch('mirror')
        assert mrmtree.called
        assert mmakedirs.called
        msubprocess.check_output.assert_called_once_with(
            ['pip', 'install', 'jujuresources>=0.2',
                '--download', 'od/jujuresources',
                '-i', 'mirror'],
            stderr=msubprocess.STDOUT)
        res.get_remote_hash.assert_called_once_with(
            'jujuresources-0.2.tgz', 'mirror/')
        res._write_file.assert_called_once_with(
            'od/jujuresources/jujuresources-0.2.tgz.hash_type', 'hash\n')
        self.assertEqual(res.filename, 'jujuresources-0.2.tgz')
        self.assertEqual(res.destination, 'od/jujuresources/jujuresources-0.2.tgz')
        self.assertEqual(res.hash, 'hash')
        self.assertEqual(res.hash_type, 'hash_type')
        res.process_dependency.assert_called_once_with('pyaml-3.0.tgz', 'mirror/')

    @mock.patch.object(subprocess, 'check_output')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(shutil, 'rmtree')
    @mock.patch.object(os.path, 'exists')
    def test_fetch_fail(self, mexists, mrmtree, mmakedirs, mcheck_output):
        mexists.return_value = True
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, 'od')
        res.get_remote_hash = mock.Mock()
        mcheck_output.side_effect = subprocess.CalledProcessError(
            1, ['cmd'],
        )
        res.fetch()
        mcheck_output.assert_called_once_with(
            ['pip', 'install', 'jujuresources>=0.2',
                '--download', 'od/jujuresources'],
            stderr=subprocess.STDOUT)
        assert not res.get_remote_hash.called

    @mock.patch.object(os, 'listdir')
    @mock.patch.object(backend.URLResource, 'fetch')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(os.path, 'exists')
    def test_fetch_urlspec(self, mexists, mmakedirs, murlfetch, mlistdir):
        mexists.return_value = True
        mmakedirs.side_effect = AssertionError('makedirs should not be called')
        mlistdir.return_value = ['bar-0.2.tgz']
        res = backend.PyPIResource('name', {
            'pypi': 'http://example.com/foo#egg=bar',
            'hash': 'hash',
            'hash_type': 'hash_type',
        }, 'od')
        res.get_remote_hash = mock.Mock(side_effect=AssertionError('get_remote_hash should not be called'))
        res.fetch()
        murlfetch.assert_called_once_with(None)
        self.assertEqual(res.hash, 'hash')
        self.assertEqual(res.hash_type, 'hash_type')

    def test_verify(self):
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, self.test_data)
        res.filename = 'res-defaults.yaml'
        res.destination = os.path.join(self.test_data, res.filename)
        res.hash = '4f08575d804517cea2265a7d43022771'
        res.hash_type = 'md5'
        res.get_local_hash = mock.Mock()
        assert res.verify()
        assert res.get_local_hash.called

    def test_get_local_hash(self):
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, self.test_data)
        res.filename = 'jujuresources-0.2.tar.gz'
        res.get_local_hash()
        self.assertEqual(res.hash, '4f08575d804517cea2265a7d43022771')
        self.assertEqual(res.hash_type, 'md5')

    @mock.patch('os.listdir')
    def test_get_local_hash_missing(self, mlistdir):
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, self.test_data)
        res.filename = 'jujuresources-0.2.tar.gz'
        mlistdir.return_value = ['jujuresources-0.2.tar.gz.md5']
        res.get_local_hash()
        self.assertEqual(res.hash, '')
        self.assertEqual(res.hash_type, '')

    @mock.patch.object(backend, 'urlopen')
    def test_get_remote_hash(self, murlopen):
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.1'}, 'od')
        murlopen.return_value.__iter__.return_value = [
            '<html>',
            '<a href="../../packages/source/j/jujuresources/'
            'jujuresources-0.1.tar.gz#md5=4fdc461dcde13b1e919c17bac6e01464">'
            'jujuresources-0.1.tar.gz'
            '</a>',
            '<a href="../../packages/source/j/jujuresources/'
            'jujuresources-0.2.tar.gz#md5=deadbeef">'
            'jujuresources-0.2.tar.gz'
            '</a>',
            '</html>']
        hash_type, hash = res.get_remote_hash('jujuresources-0.2.tar.gz', 'mirror')
        self.assertEqual(hash, 'deadbeef')
        self.assertEqual(hash_type, 'md5')

    @mock.patch.object(backend, 'urlopen')
    def test_get_remote_hash_no_match(self, murlopen):
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, 'od')
        murlopen.return_value.read.return_value = (
            '<html>'
            '<a href="../../packages/source/j/jujuresources/'
            'jujuresources-0.1.tar.gz#md5=4fdc461dcde13b1e919c17bac6e01464">'
            'jujuresources-0.1.tar.gz'
            '</a>'
            '</html>')
        hash_type, hash = res.get_remote_hash('jujuresources-0.2.tar.gz', 'mirror')
        self.assertEqual(hash, '')
        self.assertEqual(hash_type, '')

    @mock.patch.object(backend.PyPIResource, '_get_index')
    def test_package_name_from_filename(self, mget_index):
        mget_index.return_value = set(['foo', 'bar', 'qux-zod', 'foo-bar'])
        cases = {
            'qux-1.0.zip': '',
            'foo-1.0.tar.gz': 'foo',
            'bar-1.0-x86_64.tar.gz': 'bar',
            'qux-zod-1.0dev-py2.4.egg': 'qux-zod',
            'foo-bar-1.0.tar.gz': 'foo-bar',
        }
        for input, expected in cases.items():
            actual = backend.PyPIResource._package_name_from_filename(input, 'mirror')
            self.assertEqual(expected, actual)
        mget_index.assert_called_with('mirror')

    @mock.patch.object(os, 'rename')
    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(os.path, 'exists')
    def test_process_dependency(self, mexists, mmakedirs, mrename):
        mexists.return_value = False
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.2'}, 'od')
        res._package_name_from_filename = mock.Mock(return_value='new-package')
        res.get_remote_hash = mock.Mock(return_value=('hash_type', 'hash'))
        res._write_file = mock.Mock()
        res.process_dependency('new-package-1.0-python2.7.egg', 'mirror')
        mexists.assert_called_with('od/new-package')
        mmakedirs.assert_called_with('od/new-package')
        mrename.assert_called_with(
            'od/jujuresources/new-package-1.0-python2.7.egg',
            'od/new-package/new-package-1.0-python2.7.egg')
        res.get_remote_hash.assert_called_with('new-package-1.0-python2.7.egg', 'mirror')
        res._write_file.assert_called_with(
            'od/new-package/new-package-1.0-python2.7.egg.hash_type',
            'hash\n')

    @mock.patch.object(backend, 'urlopen')
    def test_get_index(self, murlopen):
        murlopen.return_value.__iter__.return_value = (
            '<html>',
            '<a href="foo">Foo</a>',
            '<a href="bar">bar</a>',
            '<a href="baz-0">baz-0</a>',
            '</html>',
        )
        backend.PyPIResource._index = None
        result = backend.PyPIResource._get_index('url')
        self.assertItemsEqual(result, ['Foo', 'bar', 'baz-0'])
        self.assertIs(backend.PyPIResource._index, result)

    def test_get_index_cached(self):
        backend.PyPIResource._index = 'foo'
        self.assertEqual(backend.PyPIResource._get_index('url'), 'foo')

    @mock.patch.object(backend.PyPIResource, '_write_file')
    def test_build_pypi_indexes(self, mwrite_file):
        backend.PyPIResource.build_pypi_indexes(self.test_data)
        self.assertEqual(mwrite_file.call_count, 1)
        self.assertEqual(mwrite_file.call_args_list[0][0][0],
                         os.path.join(self.test_data, 'jujuresources', 'index.html'))
        self.assertIn('href="jujuresources-0.2.tar.gz#md5=4f08575d804517cea2265a7d43022771"',
                      mwrite_file.call_args_list[0][0][1])

    @mock.patch.object(subprocess, 'call')
    def test_install(self, mcall):
        mcall.return_value = 0
        res = backend.PyPIResource('name', {'pypi': 'jujuresources>=0.1'}, 'od')
        res.destination = 'od/foo'
        res.verify = mock.Mock(return_value=False)
        assert not res.install()
        assert not mcall.called
        res.verify.return_value = True
        assert res.install()
        mcall.assert_called_with(['pip', 'install', 'od/foo'])
        mcall.return_value = 1
        assert not res.install()

    @mock.patch.object(subprocess, 'call')
    def test_install_group(self, mcall):
        resources = [
            backend.PyPIResource('name', {'pypi': 'foo>=0.1'}, 'od'),
            backend.PyPIResource('name', {'pypi': 'bar>=0.1'}, 'od'),
        ]
        resources[0].verify = mock.Mock(return_value=False)
        resources[1].verify = mock.Mock(return_value=True)
        resources[1].destination = 'od/bar'
        backend.PyPIResource.install_group(resources)
        mcall.assert_called_with(['pip', 'install', 'foo>=0.1', 'od/bar'])
        backend.PyPIResource.install_group(resources, mirror_url='mirror')
        mcall.assert_called_with(['pip', 'install', 'foo>=0.1', 'od/bar', '-i', 'mirror'])


if __name__ == '__main__':
    unittest.main()
