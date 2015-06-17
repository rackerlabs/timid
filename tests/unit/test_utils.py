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

import jsonschema
import mock
import six

from timid import utils


class CanonicalizePathTest(unittest.TestCase):
    @mock.patch('os.path.abspath', return_value='/absolute/path')
    def test_absolute(self, mock_abspath):
        result = utils.canonicalize_path('/foo/bar', '/bar/baz')

        self.assertEqual(result, '/absolute/path')
        mock_abspath.assert_called_once_with('/bar/baz')

    @mock.patch('os.path.abspath', return_value='/absolute/path')
    def test_relative(self, mock_abspath):
        result = utils.canonicalize_path('/foo/bar', 'bar/baz')

        self.assertEqual(result, '/absolute/path')
        mock_abspath.assert_called_once_with('/foo/bar/bar/baz')


class SensitiveDictTest(unittest.TestCase):
    def test_init_base(self):
        result = utils.SensitiveDict()

        self.assertEqual(result._data, {})
        self.assertEqual(result._sensitive, set())
        self.assertEqual(result._masked, None)

    def test_init_alt(self):
        result = utils.SensitiveDict({'a': 'one', 'b': 'two'}, set(['a', 'c']))

        self.assertEqual(result._data, {'a': 'one', 'b': 'two'})
        self.assertEqual(result._sensitive, set(['a', 'c']))
        self.assertEqual(result._masked, None)

    def test_str(self):
        obj = utils.SensitiveDict({'a': 'one'})

        self.assertEqual(six.text_type(obj), six.text_type({'a': 'one'}))

    def test_len(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two', 'c': 'three'})

        self.assertEqual(len(obj), 3)

    def test_getitem(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two'}, set(['a', 'c']))

        self.assertEqual(obj['a'], 'one')
        self.assertEqual(obj['b'], 'two')
        self.assertRaises(KeyError, lambda: obj['c'])
        self.assertRaises(KeyError, lambda: obj['d'])

    def test_setitem(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two'}, set(['a', 'c']))

        obj['a'] = '1'
        obj['b'] = '2'
        obj['c'] = '3'
        obj['d'] = '4'

        self.assertEqual(obj._data, {'a': '1', 'b': '2', 'c': '3', 'd': '4'})
        self.assertEqual(obj._sensitive, set(['a', 'c']))

    def test_delitem(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two', 'e': 'five'},
                                  set(['a', 'c']))

        def deleter(key):
            del obj[key]

        del obj['a']
        del obj['b']

        self.assertRaises(KeyError, deleter, 'c')
        self.assertRaises(KeyError, deleter, 'd')
        self.assertEqual(obj._data, {'e': 'five'})
        self.assertEqual(obj._sensitive, set(['a', 'c']))

    def test_iter(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two'}, set(['a', 'c']))

        self.assertEqual(set(iter(obj)), set(['a', 'b']))

    def test_copy(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two'}, set(['a', 'c']))

        result = obj.copy()

        self.assertEqual(obj._data, result._data)
        self.assertNotEqual(id(obj._data), id(result._data))
        self.assertEqual(obj._sensitive, result._sensitive)
        self.assertNotEqual(id(obj._sensitive), id(result._sensitive))

    def test_declare_sensitive(self):
        obj = utils.SensitiveDict({'a': 'one', 'b': 'two'}, set(['a', 'c']))

        obj.declare_sensitive('a')

        self.assertEqual(obj._sensitive, set(['a', 'c']))

        obj.declare_sensitive('b')

        self.assertEqual(obj._sensitive, set(['a', 'b', 'c']))

        obj.declare_sensitive('d')

        self.assertEqual(obj._sensitive, set(['a', 'b', 'c', 'd']))

    def test_sensitive(self):
        obj = utils.SensitiveDict(sensitive=set(['a', 'c']))

        result = obj.sensitive

        self.assertEqual(result, set(['a', 'c']))
        self.assertNotEqual(id(result), id(obj._sensitive))

    @mock.patch.object(utils, 'MaskedDict', return_value='masked')
    def test_masked_cached(self, mock_MaskedDict):
        obj = utils.SensitiveDict()
        obj._masked = 'cached'

        self.assertEqual(obj.masked, 'cached')
        self.assertEqual(obj._masked, 'cached')
        self.assertFalse(mock_MaskedDict.called)

    @mock.patch.object(utils, 'MaskedDict', return_value='masked')
    def test_masked_uncached(self, mock_MaskedDict):
        obj = utils.SensitiveDict()

        self.assertEqual(obj.masked, 'masked')
        self.assertEqual(obj._masked, 'masked')
        mock_MaskedDict.assert_called_once_with(obj)


class MaskedDictTest(unittest.TestCase):
    def test_init(self):
        result = utils.MaskedDict('parent')

        self.assertEqual(result._parent, 'parent')

    def test_enter(self):
        obj = utils.MaskedDict('parent')

        result = obj.__enter__()

        self.assertEqual(id(result), id(obj))

    def test_exit_success(self):
        obj = utils.MaskedDict('parent')

        result = obj.__exit__(None, None, None)

        self.assertEqual(result, None)

    def test_exit_failure(self):
        obj = utils.MaskedDict('parent')

        result = obj.__exit__('any', 'any', 'any')

        self.assertEqual(result, None)

    def test_str_base(self):
        data = {'a': 'one'}
        parent = mock.Mock(
            __iter__=lambda s: iter(data),
            __contains__=lambda s, n: n in data,
            __getitem__=lambda s, n: data[n],
            sensitive=set(),
            masking='<masked {key}>',
        )
        obj = utils.MaskedDict(parent)

        self.assertEqual(six.text_type(obj), six.text_type({'a': 'one'}))

    def test_str_masked(self):
        data = {'a': 'one'}
        parent = mock.Mock(
            __iter__=lambda s: iter(data),
            __contains__=lambda s, n: n in data,
            __getitem__=lambda s, n: data[n],
            sensitive=set(['a']),
            masking='<masked {key}>',
        )
        obj = utils.MaskedDict(parent)

        self.assertEqual(six.text_type(obj),
                         six.text_type({'a': '<masked a>'}))

    def test_len(self):
        parent = mock.Mock(__len__=lambda s: 3)
        obj = utils.MaskedDict(parent)

        self.assertEqual(len(obj), 3)

    def test_getitem(self):
        data = {'a': 'one', 'b': 'two'}
        parent = mock.Mock(
            __contains__=lambda s, x: x in data,
            __getitem__=lambda s, x: data[x],
            sensitive=set(['a', 'c']),
            masking='<masked {key}>',
        )
        obj = utils.MaskedDict(parent)

        self.assertEqual(obj['a'], '<masked a>')
        self.assertEqual(obj['b'], 'two')
        self.assertRaises(KeyError, lambda: obj['c'])
        self.assertRaises(KeyError, lambda: obj['d'])

    def test_iter(self):
        parent = mock.Mock(__iter__=lambda s: iter(['a', 'b']))
        obj = utils.MaskedDict(parent)

        self.assertEqual(list(iter(obj)), ['a', 'b'])

    def test_sensitive(self):
        parent = mock.Mock(sensitive=set(['a', 'c']))
        obj = utils.MaskedDict(parent)

        self.assertEqual(obj.sensitive, set(['a', 'c']))

    def test_masked(self):
        obj = utils.MaskedDict('parent')

        self.assertEqual(id(obj), id(obj.masked))


class SchemaException(Exception):
    def __init__(self, msg, **kwargs):
        super(SchemaException, self).__init__(msg)
        self.msg = msg
        self.kwargs = kwargs


class SchemaValidateTest(unittest.TestCase):
    @mock.patch.object(jsonschema, 'validate')
    def test_success(self, mock_validate):
        utils.schema_validate('inst', 'sch', SchemaException, 'foo', 'bar',
                              spam='one', maps='two')

        mock_validate.assert_called_once_with('inst', 'sch')

    @mock.patch.object(jsonschema, 'validate',
                       side_effect=jsonschema.ValidationError(
                           'validation failed', path=('a', 2, 'b', 3, 'c')))
    def test_failure(self, mock_validate):
        try:
            utils.schema_validate('inst', 'sch', SchemaException, 'foo', 'bar',
                                  spam='one', maps='two')
        except SchemaException as exc:
            self.assertEqual(exc.msg,
                             'Failed to validate "foo/bar/a/[2]/b/[3]/c": '
                             'validation failed')
            self.assertEqual(exc.kwargs, {
                'spam': 'one',
                'maps': 'two',
            })
        else:
            self.fail('Failed to raise SchemaException')


class IterPrioDictTest(unittest.TestCase):
    def test_function(self):
        prio_dict = {
            5: ['obj0', 'obj1', 'obj2', 'obj3'],
            10: ['obj4', 'obj5'],
            11: ['obj6'],
            15: [],
            20: ['obj7'],
        }

        result = list(utils.iter_prio_dict(prio_dict))

        self.assertEqual(result, ['obj%d' % i for i in range(8)])
