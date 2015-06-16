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

import collections
import os
import unittest

import mock
import six

from timid import environment
from timid import steps
from timid import utils


class BaseVariableTest(unittest.TestCase):
    def get_var(self, env, var, value=None):
        with mock.patch.object(environment.SpecialVariable, '_update'):
            obj = self.class_for_test(env, var, ',')

        obj._value = value or self.class_for_test._type()

        return obj


class SpecialVariableForTest(environment.SpecialVariable):
    _type = list
    _coerce = list


class SpecialVariableTest(BaseVariableTest):
    class_for_test = SpecialVariableForTest

    @mock.patch.object(environment.SpecialVariable, '_update')
    def test_init_base(self, mock_update):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})

        result = SpecialVariableForTest(env, 'a')

        self.assertEqual(result._env, env)
        self.assertEqual(result._var, 'a')
        self.assertEqual(result._sep, os.pathsep)
        mock_update.assert_called_once_with('one')

    @mock.patch.object(environment.SpecialVariable, '_update')
    def test_init_missing_var(self, mock_update):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})

        result = SpecialVariableForTest(env, 'c')

        self.assertEqual(result._env, env)
        self.assertEqual(result._var, 'c')
        self.assertEqual(result._sep, os.pathsep)
        mock_update.assert_called_once_with(None)

    @mock.patch.object(environment.SpecialVariable, '_update')
    def test_init_altsep(self, mock_update):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})

        result = SpecialVariableForTest(env, 'a', ',')

        self.assertEqual(result._env, env)
        self.assertEqual(result._var, 'a')
        self.assertEqual(result._sep, ',')
        mock_update.assert_called_once_with('one')

    @mock.patch.object(environment.SpecialVariable, '_update')
    def test_init_value(self, mock_update):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})

        result = SpecialVariableForTest(env, 'a', value='spam')

        self.assertEqual(result._env, env)
        self.assertEqual(result._var, 'a')
        self.assertEqual(result._sep, os.pathsep)
        mock_update.assert_called_once_with('spam')

    def test_str_base(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a')

        self.assertEqual(six.text_type(obj), 'one')

    def test_str_alt(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'c')

        self.assertEqual(six.text_type(obj), '')

    def test_repr(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['a', 'b', 'c'])

        self.assertEqual(repr(obj), repr(['a', 'b', 'c']))

    def test_len(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['a', 'b', 'c'])

        self.assertEqual(len(obj), 3)

    def test_rebuild(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['a', 'b', 'c'])

        obj._rebuild()

        self.assertEqual(env._data, {'a': 'a,b,c', 'b': 'two'})

    def test_update_none(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a')

        obj._update(None)

        self.assertEqual(obj._value, [])

    def test_update_emptystr(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a')

        obj._update('')

        self.assertEqual(obj._value, [])

    def test_update_str(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a')

        obj._update('a,b,c')

        self.assertEqual(obj._value, ['a', 'b', 'c'])

    def test_update_type(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a')

        obj._update(['a', 'b', 'c'])

        self.assertEqual(obj._value, ['a', 'b', 'c'])


class ListVariableTest(BaseVariableTest):
    class_for_test = environment.ListVariable

    def test_getitem(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['1', '2', '3'])

        self.assertEqual(obj[0], '1')
        self.assertEqual(obj[1], '2')
        self.assertEqual(obj[2], '3')
        self.assertEqual(obj[:], ['1', '2', '3'])

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_setitem_single(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['1', '2', '3'])

        obj[1] = 'b'

        self.assertEqual(obj._value, ['1', 'b', '3'])
        mock_rebuild.assert_called_once_with()

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_setitem_multiple(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['1', '2', '3'])

        obj[1:] = ['b']

        self.assertEqual(obj._value, ['1', 'b'])
        mock_rebuild.assert_called_once_with()

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_delitem_single(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['1', '2', '3'])

        del obj[1]

        self.assertEqual(obj._value, ['1', '3'])
        mock_rebuild.assert_called_once_with()

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_delitem_multiple(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['1', '2', '3'])

        del obj[1:]

        self.assertEqual(obj._value, ['1'])
        mock_rebuild.assert_called_once_with()

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_insert(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', ['1', '2', '3'])

        obj.insert(1, 'a')

        self.assertEqual(obj._value, ['1', 'a', '2', '3'])
        mock_rebuild.assert_called_once_with()


class SetVariableTest(BaseVariableTest):
    class_for_test = environment.SetVariable

    def test_contains(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', set(['a']))

        self.assertTrue('a' in obj)
        self.assertFalse('b' in obj)

    def test_iter(self):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', set(['a', 'b']))

        self.assertEqual(set(iter(obj)), set(['a', 'b']))

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_add(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', set(['a', 'b']))

        obj.add('c')

        self.assertEqual(obj._value, set(['a', 'b', 'c']))
        mock_rebuild.assert_called_once_with()

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_discard_present(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', set(['a', 'b']))

        obj.discard('b')

        self.assertEqual(obj._value, set(['a']))
        mock_rebuild.assert_called_once_with()

    @mock.patch.object(environment.SpecialVariable, '_rebuild')
    def test_discard_absent(self, mock_rebuild):
        env = mock.Mock(_data={'a': 'one', 'b': 'two'})
        obj = self.get_var(env, 'a', set(['a', 'b']))

        obj.discard('c')

        self.assertEqual(obj._value, set(['a', 'b']))
        mock_rebuild.assert_called_once_with()


class EnvironmentTest(unittest.TestCase):
    @mock.patch.dict(os.environ, clear=True, a='one', b='two')
    @mock.patch.object(os, 'getcwd', return_value='/current')
    @mock.patch.object(utils, 'canonicalize_path', return_value='/canon/path')
    @mock.patch.object(utils.SensitiveDict, '__init__', return_value=None)
    @mock.patch.object(environment, 'ListVariable',
                       side_effect=lambda e, n, **k: '%s list' % n)
    @mock.patch.object(environment, 'SetVariable',
                       side_effect=lambda e, n, **k: set([n]))
    def test_init_base(self, mock_SetVariable, mock_ListVariable, mock_init,
                       mock_canonicalize_path, mock_getcwd):
        result = environment.Environment()

        self.assertEqual(result._special, {
            'PATH': 'PATH list',
            'TIMID_SENSITIVE': set(['TIMID_SENSITIVE']),
        })
        self.assertEqual(result._cwd, '/canon/path')
        mock_SetVariable.assert_called_once_with(
            result, 'TIMID_SENSITIVE', value=None)
        mock_init.assert_called_once_with(
            {'a': 'one', 'b': 'two'}, set(['TIMID_SENSITIVE']))
        self.assertNotEqual(id(os.environ), id(mock_init.call_args[0][0]))
        mock_ListVariable.assert_called_once_with(
            result, 'PATH')
        mock_getcwd.assert_called_once_with()
        mock_canonicalize_path.assert_called_once_with(
            '/current', os.curdir)

    @mock.patch.dict(os.environ, clear=True, a='one', b='two')
    @mock.patch.object(os, 'getcwd', return_value='/current')
    @mock.patch.object(utils, 'canonicalize_path', return_value='/canon/path')
    @mock.patch.object(utils.SensitiveDict, '__init__', return_value=None)
    @mock.patch.object(environment, 'ListVariable',
                       side_effect=lambda e, n, **k: '%s list' % n)
    @mock.patch.object(environment, 'SetVariable',
                       side_effect=lambda e, n, **k: set([n]))
    def test_init_alt(self, mock_SetVariable, mock_ListVariable, mock_init,
                      mock_canonicalize_path, mock_getcwd):
        result = environment.Environment(
            environ={'c': 'three', 'd': 'four'},
            sensitive=set(['c', 'd']),
            cwd='/other/dir',
        )

        self.assertEqual(result._special, {
            'PATH': 'PATH list',
            'TIMID_SENSITIVE': set(['TIMID_SENSITIVE', 'c', 'd']),
        })
        self.assertEqual(result._cwd, '/canon/path')
        mock_SetVariable.assert_called_once_with(
            result, 'TIMID_SENSITIVE', value=None)
        mock_init.assert_called_once_with(
            {'c': 'three', 'd': 'four'}, set(['TIMID_SENSITIVE', 'c', 'd']))
        mock_ListVariable.assert_called_once_with(
            result, 'PATH')
        mock_getcwd.assert_called_once_with()
        mock_canonicalize_path.assert_called_once_with(
            '/current', '/other/dir')

    def get_env(self, environ=None, special=None, cwd='/current'):
        with mock.patch.object(environment.Environment, '__init__',
                               return_value=None):
            obj = environment.Environment()

        obj._data = environ or {}
        obj._special = special or {}
        obj._cwd = cwd

        return obj

    def test_getitem_missing(self):
        env = self.get_env({'a': 'one'}, {'b': 'special b'})

        self.assertRaises(KeyError, lambda: env['b'])

    def test_getitem_special(self):
        env = self.get_env({'a': 'one'}, {'a': 'special a'})

        self.assertEqual(env['a'], 'special a')

    def test_getitem_normal(self):
        env = self.get_env({'a': 'one'})

        self.assertEqual(env['a'], 'one')

    def test_setitem_none_normal(self):
        env = self.get_env({'a': 'one'})

        env['a'] = None

        self.assertEqual(env._data, {})

    def test_setitem_none_special(self):
        special = mock.Mock(_type=collections.Sequence)
        env = self.get_env({'a': 'one'}, {'a': special})

        env['a'] = None

        self.assertEqual(env._data, {})
        special._update.assert_called_once_with(None)
        self.assertFalse(special._rebuild.called)

    def test_setitem_str_normal(self):
        env = self.get_env({'a': 'one'})

        env['a'] = 'two'

        self.assertEqual(env._data, {'a': 'two'})

    def test_setitem_str_special(self):
        special = mock.Mock(_type=collections.Sequence)
        env = self.get_env({'a': 'one'}, {'a': special})

        env['a'] = 'two'

        self.assertEqual(env._data, {'a': 'two'})
        special._update.assert_called_once_with('two')
        self.assertFalse(special._rebuild.called)

    def test_setitem_iterable_special(self):
        value = mock.MagicMock()  # collections.Iterable
        special = mock.Mock(_type=collections.Sequence)
        env = self.get_env({'a': 'one'}, {'a': special})

        env['a'] = value

        self.assertEqual(env._data, {'a': 'one'})  # changed by _rebuild()
        special._update.assert_called_once_with(value)
        special._rebuild.assert_called_once_with()

    def test_setitem_sequence_special(self):
        value = ['a', 'b', 'c']
        special = mock.Mock(_type=collections.Sequence)
        env = self.get_env({'a': 'one'}, {'a': special})

        env['a'] = value

        self.assertEqual(env._data, {'a': 'one'})  # changed by _rebuild()
        special._update.assert_called_once_with(value)
        special._rebuild.assert_called_once_with()

    def test_setitem_badtype_normal(self):
        value = {'b': 'two'}
        env = self.get_env({'a': 'one'})

        def setter():
            env['a'] = value

        self.assertRaises(ValueError, setter)
        self.assertEqual(env._data, {'a': 'one'})

    def test_setitem_badtype_special(self):
        value = mock.Mock()
        special = mock.Mock(_type=collections.Sequence)
        env = self.get_env({'a': 'one'}, {'a': special})

        def setter():
            env['a'] = value

        self.assertRaises(ValueError, setter)
        self.assertEqual(env._data, {'a': 'one'})
        self.assertFalse(special._update.called)
        self.assertFalse(special._rebuild.called)

    def test_delitem_present_normal(self):
        env = self.get_env({'a': 'one'})

        del env['a']

        self.assertEqual(env._data, {})

    def test_delitem_present_special(self):
        special = mock.Mock()
        env = self.get_env({'a': 'one'}, {'a': special})

        del env['a']

        self.assertEqual(env._data, {})
        special._update.assert_called_once_with(None)

    def test_delitem_absent_normal(self):
        env = self.get_env({'b': 'one'})

        def deleter():
            del env['a']

        self.assertRaises(KeyError, deleter)
        self.assertEqual(env._data, {'b': 'one'})

    def test_delitem_absent_special(self):
        special = mock.Mock()
        env = self.get_env({'b': 'one'}, {'a': special})

        def deleter():
            del env['a']

        self.assertRaises(KeyError, deleter)
        self.assertEqual(env._data, {'b': 'one'})
        self.assertFalse(special._update.called)

    def test_copy(self):
        env = self.get_env({'a': 'one'})
        env._sensitive = set(['b'])

        with mock.patch.object(environment.Environment, '__init__',
                               return_value=None) as mock_init:
            result = env.copy()

            self.assertTrue(isinstance(result, environment.Environment))
            mock_init.assert_called_once_with(
                {'a': 'one'}, set(['b']), '/current')
            self.assertNotEqual(id(mock_init.call_args[0][0]), id(env._data))
            self.assertNotEqual(id(mock_init.call_args[0][1]),
                                id(env._sensitive))

    def test_declare_special_base(self):
        klass = mock.Mock()
        env = self.get_env({'a': 'one'})

        env._declare_special('a', ',', klass)

        self.assertEqual(env._special, {'a': klass.return_value})
        klass.assert_called_once_with(env, 'a', ',')

    def test_declare_special_sep_mismatch(self):
        class Special(object):
            _sep = ':'
        special = Special()
        env = self.get_env({'a': 'one'}, {'a': special})

        with mock.patch.object(Special, '__init__',
                               return_value=None) as mock_init:
            self.assertRaises(ValueError, env._declare_special,
                              'a', ',', Special)
            self.assertEqual(env._special, {'a': special})
            self.assertFalse(mock_init.called)

    def test_declare_special_klass_mismatch(self):
        class Special1(object):
            _sep = ','

        class Special2(object):
            pass

        special = Special1()
        env = self.get_env({'a': 'one'}, {'a': special})

        with mock.patch.object(Special2, '__init__',
                               return_value=None) as mock_init:
            self.assertRaises(ValueError, env._declare_special,
                              'a', ',', Special2)
            self.assertEqual(env._special, {'a': special})
            self.assertFalse(mock_init.called)

    def test_declare_special_sep_match(self):
        class Special(object):
            _sep = ','
        special = Special()
        env = self.get_env({'a': 'one'}, {'a': special})

        with mock.patch.object(Special, '__init__',
                               return_value=None) as mock_init:
            env._declare_special('a', ',', Special)

            self.assertEqual(env._special, {'a': special})
            self.assertFalse(mock_init.called)

    @mock.patch.object(environment.Environment, '_declare_special')
    def test_declare_list_base(self, mock_declare_special):
        env = self.get_env({'a': 'one'})

        env.declare_list('spam')

        mock_declare_special.assert_called_once_with(
            'spam', os.pathsep, environment.ListVariable)

    @mock.patch.object(environment.Environment, '_declare_special')
    def test_declare_list_alt(self, mock_declare_special):
        env = self.get_env({'a': 'one'})

        env.declare_list('spam', ',')

        mock_declare_special.assert_called_once_with(
            'spam', ',', environment.ListVariable)

    @mock.patch.object(environment.Environment, '_declare_special')
    def test_declare_set_base(self, mock_declare_special):
        env = self.get_env({'a': 'one'})

        env.declare_set('spam')

        mock_declare_special.assert_called_once_with(
            'spam', os.pathsep, environment.SetVariable)

    @mock.patch.object(environment.Environment, '_declare_special')
    def test_declare_set_alt(self, mock_declare_special):
        env = self.get_env({'a': 'one'})

        env.declare_set('spam', ',')

        mock_declare_special.assert_called_once_with(
            'spam', ',', environment.SetVariable)

    @mock.patch('subprocess.Popen')
    def test_call_base(self, mock_Popen):
        env = self.get_env({'a': 'one'})

        env.call(['prog', 'ram'])

        mock_Popen.assert_called_once_with(
            ['prog', 'ram'], cwd='/current', env={'a': 'one'}, close_fds=True)

    @mock.patch('subprocess.Popen')
    def test_call_alt(self, mock_Popen):
        env = self.get_env({'a': 'one'})

        env.call('prog ram', cwd='/other', env={'b': 'two'}, spam='spam',
                 close_fds=False)

        mock_Popen.assert_called_once_with(
            ['prog', 'ram'], cwd='/current', env={'a': 'one'}, spam='spam',
            close_fds=False)

    @mock.patch.object(utils, 'canonicalize_path', return_value='/canon/path')
    def test_cwd_get(self, mock_canonicalize_path):
        env = self.get_env()

        self.assertEqual(env.cwd, '/current')
        self.assertEqual(env._cwd, '/current')
        self.assertFalse(mock_canonicalize_path.called)

    @mock.patch.object(utils, 'canonicalize_path', return_value='/canon/path')
    def test_cwd_set(self, mock_canonicalize_path):
        env = self.get_env()

        env.cwd = '../other'

        self.assertEqual(env._cwd, '/canon/path')
        mock_canonicalize_path.assert_called_once_with(
            '/current', '../other')


class DirectoryActionTest(unittest.TestCase):
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init(self, mock_init):
        ctxt = mock.Mock(**{'template.return_value': 'templated'})

        result = environment.DirectoryAction(
            ctxt, 'chdir', 'directory', 'step_addr')

        self.assertEqual(result.target_dir, 'templated')
        mock_init.assert_called_once_with(
            ctxt, 'chdir', 'directory', 'step_addr')
        ctxt.template.assert_called_once_with('directory')

    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_call(self, mock_init):
        tmpl = mock.Mock(return_value='target_dir')
        ctxt = mock.Mock(**{
            'template.return_value': tmpl,
            'environment.cwd': 'unchanged',
        })
        action = environment.DirectoryAction(
            ctxt, 'chdir', 'directory', 'step_addr')

        result = action(ctxt)

        self.assertTrue(isinstance(result, steps.StepResult))
        self.assertEqual(result.state, steps.SUCCESS)
        self.assertEqual(ctxt.environment.cwd, 'target_dir')
        tmpl.assert_called_once_with(ctxt)


class RunActionTest(unittest.TestCase):
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_string(self, mock_init):
        ctxt = mock.Mock(**{'template.side_effect': lambda x: '%s_tmpl' % x})

        result = environment.RunAction(ctxt, 'run', 'command', 'step_addr')

        self.assertEqual(result.command, 'command_tmpl')
        ctxt.template.assert_called_once_with('command')

    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_list(self, mock_init):
        ctxt = mock.Mock(**{'template.side_effect': lambda x: '%s_tmpl' % x})

        result = environment.RunAction(
            ctxt, 'run', ['command', 'arg1', 'arg2', 'arg3'], 'step_addr')

        self.assertEqual(result.command, ['command_tmpl', 'arg1_tmpl',
                                          'arg2_tmpl', 'arg3_tmpl'])
        ctxt.template.assert_has_calls([
            mock.call('command'),
            mock.call('arg1'),
            mock.call('arg2'),
            mock.call('arg3'),
        ])

    def get_action(self, command):
        with mock.patch.object(environment.RunAction, '__init__',
                               return_value=None):
            action = environment.RunAction()

        action.command = command

        return action

    def test_call_string(self):
        subproc = mock.Mock(**{'wait.return_value': 5})
        ctxt = mock.Mock(**{'environment.call.return_value': subproc})
        command = mock.Mock(return_value='cmd arg1 arg2 arg3')
        action = self.get_action(command)

        result = action(ctxt)

        self.assertTrue(isinstance(result, steps.StepResult))
        self.assertEqual(result.returncode, 5)
        command.assert_called_once_with(ctxt)
        ctxt.environment.call.assert_called_once_with(
            ['cmd', 'arg1', 'arg2', 'arg3'])
        subproc.wait.assert_called_once_with()

    def test_call_list(self):
        subproc = mock.Mock(**{'wait.return_value': 5})
        ctxt = mock.Mock(**{'environment.call.return_value': subproc})
        command = [
            mock.Mock(return_value='cmd'),
            mock.Mock(return_value='arg1'),
            mock.Mock(return_value='arg2'),
            mock.Mock(return_value='arg3'),
        ]
        action = self.get_action(command)

        result = action(ctxt)

        self.assertTrue(isinstance(result, steps.StepResult))
        self.assertEqual(result.returncode, 5)
        for part in command:
            part.assert_called_once_with(ctxt)
        ctxt.environment.call.assert_called_once_with(
            ['cmd', 'arg1', 'arg2', 'arg3'])
        subproc.wait.assert_called_once_with()
