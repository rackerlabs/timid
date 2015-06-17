# Copyright 2015 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the
#    License. You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing,
#    software distributed under the License is distributed on an "AS
#    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#    express or implied. See the License for the specific language
#    governing permissions and limitations under the License.

import unittest

import mock
import pkg_resources
import six

from timid import entry


class NamespaceCacheTest(unittest.TestCase):
    @mock.patch.object(pkg_resources, 'iter_entry_points')
    def test_init(self, mock_iter_entry_points):
        eps = [
            mock.Mock(ep_name='ep1', inst='ep1.1'),
            mock.Mock(ep_name='ep2', inst='ep2.1'),
            mock.Mock(ep_name='ep1', inst='ep1.2'),
        ]
        for ep in eps:
            ep.name = ep.ep_name
        mock_iter_entry_points.return_value = eps

        result = entry.NamespaceCache('namespace')

        self.assertEqual(result.namespace, 'namespace')
        self.assertEqual(result._entrypoints, {
            'ep1': [eps[0], eps[2]],
            'ep2': [eps[1]],
        })
        self.assertEqual(result._epcache, {})
        self.assertEqual(result._eplist, None)

    def make_obj(self, namespace='namespace', entrypoints=None, epcache=None,
                 eplist=None):
        with mock.patch.object(entry.NamespaceCache, '__init__',
                               return_value=None):
            obj = entry.NamespaceCache()

        obj.namespace = namespace
        obj._entrypoints = entrypoints or {}
        obj._epcache = epcache or {}
        obj._eplist = eplist

        return obj

    def test_iter_cached(self):
        obj = self.make_obj(eplist=['obj1', 'obj2', 'obj3'])

        result = list(iter(obj))

        self.assertEqual(result, ['obj1', 'obj2', 'obj3'])
        self.assertEqual(obj._eplist, ['obj1', 'obj2', 'obj3'])
        self.assertEqual(obj._epcache, {})

    def test_iter_uncached(self):
        obj = self.make_obj(entrypoints={
            'ep1': [
                mock.Mock(**{'load.side_effect': ImportError('spam')}),
                mock.Mock(**{'load.side_effect': AttributeError('spam')}),
                mock.Mock(**{
                    'load.side_effect': pkg_resources.UnknownExtra('spam'),
                }),
            ],
            'ep2': [
                mock.Mock(**{'load.return_value': 'obj0'}),
                mock.Mock(**{'load.return_value': 'obj1'}),
            ],
            'ep3': [
                mock.Mock(**{'load.side_effect': ImportError('spam')}),
                mock.Mock(**{'load.return_value': 'obj2'}),
                mock.Mock(**{'load.side_effect': AttributeError('spam')}),
                mock.Mock(**{'load.return_value': 'obj3'}),
            ],
        }, epcache={'ep2': 'cached'})

        result = list(iter(obj))

        self.assertEqual(result, ['obj0', 'obj1', 'obj2', 'obj3'])
        self.assertEqual(obj._eplist, ['obj0', 'obj1', 'obj2', 'obj3'])
        self.assertEqual(obj._epcache, {
            'ep1': entry._unavailable,
            'ep2': 'cached',
            'ep3': 'obj2',
        })

    def test_contains_empty(self):
        obj = self.make_obj()

        self.assertFalse('spam' in obj)

    def test_contains_no_entrypoint(self):
        obj = self.make_obj(epcache={'spam': 'ep'})

        self.assertFalse('spam' in obj)

    def test_contains_ep_unavailable(self):
        obj = self.make_obj(entrypoints={'spam': []},
                            epcache={'spam': entry._unavailable})

        self.assertFalse('spam' in obj)

    def test_contains_with_entrypoint(self):
        obj = self.make_obj(entrypoints={'spam': []})

        self.assertTrue('spam' in obj)

    def test_getitem_empty(self):
        obj = self.make_obj()

        self.assertRaises(KeyError, lambda: obj['spam'])
        self.assertFalse('spam' in obj._epcache)

    def test_getitem_no_entrypoint(self):
        obj = self.make_obj(epcache={'spam': 'cached'})

        self.assertRaises(KeyError, lambda: obj['spam'])
        self.assertEqual(obj._epcache, {'spam': 'cached'})

    def test_getitem_ep_unavailable(self):
        obj = self.make_obj(entrypoints={'spam': []},
                            epcache={'spam': entry._unavailable})

        self.assertRaises(KeyError, lambda: obj['spam'])
        self.assertEqual(obj._epcache, {'spam': entry._unavailable})

    def test_getitem_ep_cached(self):
        obj = self.make_obj(entrypoints={'spam': []},
                            epcache={'spam': 'cached'})

        self.assertEqual(obj['spam'], 'cached')
        self.assertEqual(obj._epcache, {'spam': 'cached'})

    def test_getitem_ep_emptylist(self):
        obj = self.make_obj(entrypoints={'spam': []})

        self.assertRaises(KeyError, lambda: obj['spam'])
        self.assertEqual(obj._epcache, {'spam': entry._unavailable})

    def test_getitem_ep_errors(self):
        eps = [
            mock.Mock(**{'load.side_effect': ImportError('spam')}),
            mock.Mock(**{'load.side_effect': AttributeError('spam')}),
            mock.Mock(**{
                'load.side_effect': pkg_resources.UnknownExtra('spam'),
            }),
        ]
        obj = self.make_obj(entrypoints={'spam': eps})

        self.assertRaises(ImportError, lambda: obj['spam'])
        self.assertEqual(obj._epcache, {'spam': entry._unavailable})
        for ep in eps:
            ep.load.assert_called_once_with()

    def test_getitem_ep_success(self):
        eps = [
            mock.Mock(**{
                'load.side_effect': ImportError('spam'),
                'load_expected': True,
            }),
            mock.Mock(**{
                'load.side_effect': AttributeError('spam'),
                'load_expected': True,
            }),
            mock.Mock(**{
                'load.side_effect': pkg_resources.UnknownExtra('spam'),
                'load_expected': True,
            }),
            mock.Mock(**{
                'load.return_value': 'object',
                'load_expected': True,
            }),
            mock.Mock(**{
                'load.return_value': 'other',
                'load_expected': False,
            }),
        ]
        obj = self.make_obj(entrypoints={'spam': eps})

        self.assertEqual(obj['spam'], 'object')
        self.assertEqual(obj._epcache, {'spam': 'object'})
        for ep in eps:
            if ep.load_expected:
                ep.load.assert_called_once_with()
            else:
                self.assertFalse(ep.load.called)


class EntrypointCacheTest(unittest.TestCase):
    def test_init(self):
        result = entry.EntrypointCache()

        self.assertEqual(result._namespaces, {})

    @mock.patch.object(entry, 'NamespaceCache', return_value='ns_cache')
    def test_getitem_cached(self, mock_NamespaceCache):
        obj = entry.EntrypointCache()
        obj._namespaces['spam'] = 'cached'

        self.assertEqual(obj['spam'], 'cached')
        self.assertEqual(obj._namespaces, {'spam': 'cached'})
        self.assertFalse(mock_NamespaceCache.called)

    @mock.patch.object(entry, 'NamespaceCache', return_value='ns_cache')
    def test_getitem_uncached(self, mock_NamespaceCache):
        obj = entry.EntrypointCache()

        self.assertEqual(obj['spam'], 'ns_cache')
        self.assertEqual(obj._namespaces, {'spam': 'ns_cache'})
        mock_NamespaceCache.assert_called_once_with('spam')

    def test_points(self):
        self.assertTrue(isinstance(entry.points, entry.EntrypointCache))
        self.assertEqual(entry.points._namespaces, {})
