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

import os
import sys
import unittest

import mock
import six

from timid import entry
from timid import extensions


class TestingException(Exception):
    pass


class TestingBaseException(BaseException):
    pass


def make_debugger(exit_status=False):
    debugger = mock.MagicMock()
    debugger.__enter__.return_value = debugger
    debugger.__exit__.return_value = exit_status
    return debugger


class ExtensionForTest(extensions.Extension):
    priority = 10


class ExtensionTest(unittest.TestCase):
    def test_activate(self):
        result = ExtensionForTest.activate('ctxt', 'args')

        self.assertEqual(result, None)

    def test_pre_step(self):
        obj = ExtensionForTest()

        result = obj.pre_step('ctxt', 'step', 5)

        self.assertEqual(result, None)

    def test_finalize(self):
        obj = ExtensionForTest()

        result = obj.finalize('ctxt', 'retval')

        self.assertEqual(result, 'retval')


class ExtensionDebugger(unittest.TestCase):
    @mock.patch.dict(os.environ, clear=True)
    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_init_base(self, mock_debug):
        result = extensions.ExtensionDebugger('method')

        self.assertEqual(result.method, 'method')
        self.assertEqual(result.ext_cls, None)
        self.assertEqual(result._debug, 0)
        mock_debug.assert_called_once_with(
            2, 'Calling extension method "method()"')

    @mock.patch.dict(os.environ, clear=True, TIMID_EXTENSION_DEBUG='')
    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_init_present(self, mock_debug):
        result = extensions.ExtensionDebugger('method')

        self.assertEqual(result.method, 'method')
        self.assertEqual(result.ext_cls, None)
        self.assertEqual(result._debug, 1)
        mock_debug.assert_called_once_with(
            2, 'Calling extension method "method()"')

    @mock.patch.dict(os.environ, clear=True, TIMID_EXTENSION_DEBUG='str')
    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_init_string(self, mock_debug):
        result = extensions.ExtensionDebugger('method')

        self.assertEqual(result.method, 'method')
        self.assertEqual(result.ext_cls, None)
        self.assertEqual(result._debug, 1)
        mock_debug.assert_called_once_with(
            2, 'Calling extension method "method()"')

    @mock.patch.dict(os.environ, clear=True, TIMID_EXTENSION_DEBUG='-5')
    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_init_negative(self, mock_debug):
        result = extensions.ExtensionDebugger('method')

        self.assertEqual(result.method, 'method')
        self.assertEqual(result.ext_cls, None)
        self.assertEqual(result._debug, 0)
        mock_debug.assert_called_once_with(
            2, 'Calling extension method "method()"')

    @mock.patch.dict(os.environ, clear=True, TIMID_EXTENSION_DEBUG='0')
    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_init_zero(self, mock_debug):
        result = extensions.ExtensionDebugger('method')

        self.assertEqual(result.method, 'method')
        self.assertEqual(result.ext_cls, None)
        self.assertEqual(result._debug, 0)
        mock_debug.assert_called_once_with(
            2, 'Calling extension method "method()"')

    @mock.patch.dict(os.environ, clear=True, TIMID_EXTENSION_DEBUG='3')
    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_init_positive(self, mock_debug):
        result = extensions.ExtensionDebugger('method')

        self.assertEqual(result.method, 'method')
        self.assertEqual(result.ext_cls, None)
        self.assertEqual(result._debug, 3)
        mock_debug.assert_called_once_with(
            2, 'Calling extension method "method()"')

    def get_obj(self, ext_cls=None, debug=0):
        with mock.patch.object(extensions.ExtensionDebugger, '__init__',
                               return_value=None):
            obj = extensions.ExtensionDebugger()

        obj.method = 'method'
        obj.ext_cls = ext_cls
        obj._debug = debug

        return obj

    def test_enter(self):
        obj = self.get_obj()

        result = obj.__enter__()

        self.assertEqual(result, obj)

    @mock.patch('traceback.print_exception')
    @mock.patch('sys.exit')
    def test_exit_noerror(self, mock_exit, mock_print_exception):
        obj = self.get_obj(ext_cls=mock.Mock(__module__='mod',
                                             __name__='name'))

        result = obj.__exit__(None, None, None)

        self.assertEqual(result, None)
        self.assertEqual(obj.ext_cls, None)
        self.assertFalse(mock_print_exception.called)
        self.assertFalse(mock_exit.called)

    @mock.patch('traceback.print_exception')
    @mock.patch('sys.exit')
    def test_exit_noerror_debug(self, mock_exit, mock_print_exception):
        obj = self.get_obj(ext_cls=mock.Mock(__module__='mod',
                                             __name__='name'),
                           debug=1)

        result = obj.__exit__(None, None, None)

        self.assertEqual(result, None)
        self.assertEqual(obj.ext_cls, None)
        self.assertFalse(mock_print_exception.called)
        self.assertFalse(mock_exit.called)

    @mock.patch('traceback.print_exception')
    @mock.patch('sys.exit')
    def test_exit_exception(self, mock_exit, mock_print_exception):
        exc = TestingException('error')
        obj = self.get_obj(ext_cls=mock.Mock(__module__='mod',
                                             __name__='name'))

        result = obj.__exit__(TestingException, exc, 'tb')

        self.assertEqual(result, True)
        self.assertEqual(obj.ext_cls, None)
        self.assertFalse(mock_print_exception.called)
        self.assertFalse(mock_exit.called)

    @mock.patch('traceback.print_exception')
    @mock.patch('sys.exit')
    def test_exit_exception_debug(self, mock_exit, mock_print_exception):
        exc = TestingException('error')
        obj = self.get_obj(ext_cls=mock.Mock(__module__='mod',
                                             __name__='name'),
                           debug=1)

        result = obj.__exit__(TestingException, exc, 'tb')

        self.assertEqual(result, False)
        mock_print_exception.assert_called_once_with(
            TestingException, exc, 'tb', file=sys.stderr)
        mock_exit.assert_called_once_with(
            'Extension failure calling "method()" for extension "mod.name"')

    @mock.patch('traceback.print_exception')
    @mock.patch('sys.exit')
    def test_exit_base_exception(self, mock_exit, mock_print_exception):
        exc = TestingBaseException('error')
        obj = self.get_obj(ext_cls=mock.Mock(__module__='mod',
                                             __name__='name'))

        result = obj.__exit__(TestingBaseException, exc, 'tb')

        self.assertEqual(result, False)
        self.assertEqual(obj.ext_cls, None)
        self.assertFalse(mock_print_exception.called)
        self.assertFalse(mock_exit.called)

    @mock.patch('traceback.print_exception')
    @mock.patch('sys.exit')
    def test_exit_base_exception_debug(self, mock_exit, mock_print_exception):
        exc = TestingBaseException('error')
        obj = self.get_obj(ext_cls=mock.Mock(__module__='mod',
                                             __name__='name'),
                           debug=1)

        result = obj.__exit__(TestingBaseException, exc, 'tb')

        self.assertEqual(result, False)
        mock_print_exception.assert_called_once_with(
            TestingBaseException, exc, 'tb', file=sys.stderr)
        mock_exit.assert_called_once_with(
            'Extension failure calling "method()" for extension "mod.name"')

    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_call_object(self, mock_debug):
        class TestClass(object):
            pass
        ext_obj = TestClass()
        obj = self.get_obj()

        result = obj(ext_obj)

        self.assertEqual(result, obj)
        self.assertEqual(obj.ext_cls, TestClass)
        mock_debug.assert_called_once_with(
            3, 'Calling extension "%s.%s" method "method()"' %
            (TestClass.__module__, TestClass.__name__))

    @mock.patch.object(extensions.ExtensionDebugger, 'debug')
    def test_call_class(self, mock_debug):
        class TestClass(object):
            pass
        obj = self.get_obj()

        result = obj(TestClass)

        self.assertEqual(result, obj)
        self.assertEqual(obj.ext_cls, TestClass)
        mock_debug.assert_called_once_with(
            3, 'Calling extension "%s.%s" method "method()"' %
            (TestClass.__module__, TestClass.__name__))

    @mock.patch('sys.stderr', six.StringIO())
    def test_debug_low(self):
        obj = self.get_obj(debug=1)

        obj.debug(2, 'test message')

        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stderr', six.StringIO())
    def test_debug_high(self):
        obj = self.get_obj(debug=3)

        obj.debug(2, 'test message')

        self.assertEqual(sys.stderr.getvalue(), 'test message\n')


class ExtensionSetTest(unittest.TestCase):
    @mock.patch.object(entry, 'points', {
        extensions.NAMESPACE_EXTENSIONS: [
            mock.Mock(priority=5, ext='ext1'),
            mock.Mock(priority=0, ext='ext0'),
            mock.Mock(priority=10, ext='ext2'),
            mock.Mock(priority=10, ext='ext3'),
        ],
    })
    @mock.patch.object(extensions.ExtensionSet, '_extension_classes', 'cached')
    def test_get_extension_classes_cached(self):
        result = extensions.ExtensionSet._get_extension_classes()

        self.assertEqual(result, 'cached')
        self.assertEqual(extensions.ExtensionSet._extension_classes, 'cached')

    @mock.patch.object(entry, 'points', {
        extensions.NAMESPACE_EXTENSIONS: [
            mock.Mock(priority=5, ext='ext1'),
            mock.Mock(priority=0, ext='ext0'),
            mock.Mock(priority=10, ext='ext2'),
            mock.Mock(priority=10, ext='ext3'),
        ],
    })
    @mock.patch.object(extensions.ExtensionSet, '_extension_classes', None)
    def test_get_extension_classes_uncached(self):
        result = extensions.ExtensionSet._get_extension_classes()

        self.assertEqual([r.ext for r in result],
                         ['ext0', 'ext1', 'ext2', 'ext3'])
        self.assertEqual(extensions.ExtensionSet._extension_classes, result)

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger())
    @mock.patch.object(extensions.ExtensionSet, '_get_extension_classes',
                       return_value=[mock.Mock(), mock.Mock(), mock.Mock()])
    def test_prepare(self, mock_get_extension_classes, mock_ExtensionDebugger):
        extensions.ExtensionSet.prepare('parser')

        mock_ExtensionDebugger.assert_called_once_with('prepare')
        mock_get_extension_classes.assert_called_once_with()
        for ext_cls in mock_get_extension_classes.return_value:
            ext_cls.prepare.assert_called_once_with('parser')

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger(True))
    @mock.patch.object(extensions.ExtensionSet, '_get_extension_classes',
                       return_value=[
                           mock.Mock(**{
                               '__module__': 'mod0',
                               '__name__': 'ext0',
                               'activate.return_value': None,
                           }),
                           mock.Mock(**{
                               '__module__': 'mod1',
                               '__name__': 'ext1',
                               'activate.side_effect': TestingException('foo'),
                           }),
                           mock.Mock(**{
                               '__module__': 'mod2',
                               '__name__': 'ext2',
                               'activate.return_value': 'obj2',
                           }),
                           mock.Mock(**{
                               '__module__': 'mod3',
                               '__name__': 'ext3',
                               'activate.return_value': None,
                           }),
                           mock.Mock(**{
                               '__module__': 'mod4',
                               '__name__': 'ext4',
                               'activate.return_value': 'obj4',
                           }),
                       ])
    @mock.patch.object(extensions.ExtensionSet, '__init__', return_value=None)
    def test_activate_nodebug(self, mock_init, mock_get_extension_classes,
                              mock_ExtensionDebugger):
        result = extensions.ExtensionSet.activate('ctxt', 'args')

        self.assertTrue(isinstance(result, extensions.ExtensionSet))
        mock_ExtensionDebugger.assert_called_once_with('activate')
        debugger = mock_ExtensionDebugger.return_value
        mock_get_extension_classes.assert_called_once_with()
        exts = mock_get_extension_classes.return_value
        for ext_cls in exts:
            ext_cls.activate.assert_called_once_with('ctxt', 'args')
        debugger.assert_has_calls([
            mock.call(exts[0]),
            mock.call(exts[1]),
            mock.call.__exit__(TestingException, mock.ANY, mock.ANY),
            mock.call(exts[2]),
            mock.call.debug(2, 'Activating extension "mod2.ext2"'),
            mock.call(exts[3]),
            mock.call(exts[4]),
            mock.call.debug(2, 'Activating extension "mod4.ext4"'),
        ])
        # The call to __exit__() doesn't get counted
        self.assertEqual(len(debugger.method_calls) + debugger.call_count, 7)
        mock_init.assert_called_once_with(['obj2', 'obj4'])

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger(False))
    @mock.patch.object(extensions.ExtensionSet, '_get_extension_classes',
                       return_value=[
                           mock.Mock(**{
                               '__module__': 'mod0',
                               '__name__': 'ext0',
                               'activate.return_value': None,
                               'call_expected': True,
                           }),
                           mock.Mock(**{
                               '__module__': 'mod1',
                               '__name__': 'ext1',
                               'activate.side_effect': TestingException('foo'),
                               'call_expected': True,
                           }),
                           mock.Mock(**{
                               '__module__': 'mod2',
                               '__name__': 'ext2',
                               'activate.return_value': 'obj2',
                               'call_expected': False,
                           }),
                           mock.Mock(**{
                               '__module__': 'mod3',
                               '__name__': 'ext3',
                               'activate.return_value': None,
                               'call_expected': False,
                           }),
                           mock.Mock(**{
                               '__module__': 'mod4',
                               '__name__': 'ext4',
                               'activate.return_value': 'obj4',
                               'call_expected': False,
                           }),
                       ])
    @mock.patch.object(extensions.ExtensionSet, '__init__', return_value=None)
    def test_activate_debug(self, mock_init, mock_get_extension_classes,
                            mock_ExtensionDebugger):
        self.assertRaises(TestingException, extensions.ExtensionSet.activate,
                          'ctxt', 'args')
        mock_ExtensionDebugger.assert_called_once_with('activate')
        debugger = mock_ExtensionDebugger.return_value
        mock_get_extension_classes.assert_called_once_with()
        exts = mock_get_extension_classes.return_value
        for ext_cls in exts:
            if ext_cls.call_expected:
                ext_cls.activate.assert_called_once_with('ctxt', 'args')
            else:
                self.assertFalse(ext_cls.activate.called)
        debugger.assert_has_calls([
            mock.call(exts[0]),
            mock.call(exts[1]),
            mock.call.__exit__(TestingException, mock.ANY, mock.ANY),
        ])
        # The call to __exit__() doesn't get counted
        self.assertEqual(len(debugger.method_calls) + debugger.call_count, 2)
        self.assertFalse(mock_init.called)

    def test_init_base(self):
        result = extensions.ExtensionSet()

        self.assertEqual(result.exts, [])

    def test_init_alt(self):
        result = extensions.ExtensionSet(['ext0', 'ext1', 'ext2'])

        self.assertEqual(result.exts, ['ext0', 'ext1', 'ext2'])

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger())
    def test_read_steps(self, mock_ExtensionDebugger):
        exts = [mock.Mock() for i in range(5)]
        obj = extensions.ExtensionSet(exts)

        result = obj.read_steps('ctxt', 'steps')

        self.assertEqual(result, 'steps')
        mock_ExtensionDebugger.assert_called_once_with('read_steps')
        for ext in exts:
            ext.read_steps.assert_called_once_with('ctxt', 'steps')

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger())
    def test_pre_step_noskip(self, mock_ExtensionDebugger):
        exts = [mock.Mock(**{'pre_step.return_value': False})
                for i in range(5)]
        obj = extensions.ExtensionSet(exts)

        result = obj.pre_step('ctxt', 'step', 5)

        self.assertEqual(result, False)
        mock_ExtensionDebugger.assert_called_once_with('pre_step')
        debugger = mock_ExtensionDebugger.return_value
        for ext in exts:
            ext.pre_step.assert_called_once_with('ctxt', 'step', 5)
        self.assertFalse(debugger.debug.called)

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger())
    def test_pre_step_withskip(self, mock_ExtensionDebugger):
        exts = [
            mock.Mock(**{
                'pre_step.return_value': False,
                'call_expected': True,
            }),
            mock.Mock(**{
                'pre_step.return_value': False,
                'call_expected': True,
            }),
            mock.Mock(**{
                'pre_step.return_value': True,
                'call_expected': True,
            }),
            mock.Mock(**{
                'pre_step.return_value': False,
                'call_expected': False,
            }),
            mock.Mock(**{
                'pre_step.return_value': False,
                'call_expected': False,
            }),
        ]
        obj = extensions.ExtensionSet(exts)

        result = obj.pre_step('ctxt', 'step', 5)

        self.assertEqual(result, True)
        mock_ExtensionDebugger.assert_called_once_with('pre_step')
        debugger = mock_ExtensionDebugger.return_value
        for ext in exts:
            if ext.call_expected:
                ext.pre_step.assert_called_once_with('ctxt', 'step', 5)
            else:
                self.assertFalse(ext.pre_step.called)
        debugger.debug.assert_called_once_with(
            3, 'Skipping step 5')

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger())
    def test_post_step(self, mock_ExtensionDebugger):
        exts = [mock.Mock() for i in range(5)]
        obj = extensions.ExtensionSet(exts)

        result = obj.post_step('ctxt', 'step', 5, 'result')

        self.assertEqual(result, 'result')
        mock_ExtensionDebugger.assert_called_once_with('post_step')
        for ext in exts:
            ext.post_step.assert_called_once_with('ctxt', 'step', 5, 'result')

    @mock.patch.object(extensions, 'ExtensionDebugger',
                       return_value=make_debugger())
    def test_finalize(self, mock_ExtensionDebugger):
        exts = [mock.Mock(**{'finalize.return_value': 'result%d' % (i + 1)})
                for i in range(5)]
        obj = extensions.ExtensionSet(exts)

        result = obj.finalize('ctxt', 'result0')

        self.assertEqual(result, 'result5')
        mock_ExtensionDebugger.assert_called_once_with('finalize')
        for i, ext in enumerate(exts):
            ext.finalize.assert_called_once_with('ctxt', 'result%d' % i)
