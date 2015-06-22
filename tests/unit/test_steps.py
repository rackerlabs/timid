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
import unittest

import mock
import six
from six.moves import builtins

from timid import entry
from timid import steps


class TestingException(Exception):
    pass


class ConfigErrorTest(unittest.TestCase):
    def test_init_base(self):
        result = steps.ConfigError('message')

        self.assertEqual(six.text_type(result), 'message')
        self.assertEqual(result.step_addr, None)

    def test_init_step_addr(self):
        result = steps.ConfigError('message', 'addr')

        self.assertEqual(six.text_type(result), 'message (addr)')
        self.assertEqual(result.step_addr, 'addr')


class StepAddressTest(unittest.TestCase):
    def test_init_base(self):
        result = steps.StepAddress('fname', 3)

        self.assertEqual(result.fname, 'fname')
        self.assertEqual(result.idx, 3)
        self.assertEqual(result.key, None)
        self.assertEqual(result._str, None)

    def test_init_alt(self):
        result = steps.StepAddress('fname', 3, 'key')

        self.assertEqual(result.fname, 'fname')
        self.assertEqual(result.idx, 3)
        self.assertEqual(result.key, 'key')
        self.assertEqual(result._str, None)

    def test_str_cached(self):
        addr = steps.StepAddress('fname', 3)
        addr._str = 'cached'

        self.assertEqual(six.text_type(addr), 'cached')
        self.assertEqual(addr._str, 'cached')

    def test_str_uncached_nokey(self):
        addr = steps.StepAddress('fname', 3)

        self.assertEqual(six.text_type(addr), 'fname step 4')
        self.assertEqual(addr._str, 'fname step 4')

    def test_str_uncached_withkey(self):
        addr = steps.StepAddress('fname', 3, 'key')

        self.assertEqual(six.text_type(addr), 'fname[key] step 4')
        self.assertEqual(addr._str, 'fname[key] step 4')


class StepPartForTest(steps.StepPart):
    schema = 'schema'


class StepPartTest(unittest.TestCase):
    @mock.patch.object(steps.StepPart, 'validate_conf')
    def test_init(self, mock_validate_conf):
        result = StepPartForTest('ctxt', 'name', 'config', 'step_addr')

        self.assertEqual(result.name, 'name')
        self.assertEqual(result.config, 'config')
        self.assertEqual(result.step_addr, 'step_addr')
        mock_validate_conf.assert_called_once_with(
            'name', 'config', 'step_addr')

    @mock.patch('timid.utils.schema_validate')
    def test_validate_conf(self, mock_schema_validate):
        with mock.patch.object(steps.StepPart, 'validate_conf'):
            obj = StepPartForTest('ctxt', 'name', 'config', 'step_addr')

        obj.validate_conf('name', 'config', 'step_addr')

        mock_schema_validate.assert_called_once_with(
            'config', 'schema', steps.ConfigError, 'name',
            step_addr='step_addr')


class ModifierForTest(steps.Modifier):
    schema = 'schema'
    priority = 25


class ModifierTest(unittest.TestCase):
    @mock.patch.object(steps.StepPart, '__init__', return_value=None)
    def test_action_conf(self, mock_init):
        obj = ModifierForTest()

        result = obj.action_conf('ctxt', 'action_class', 'action_name',
                                 'config', 'step_addr')

        self.assertEqual(result, 'config')

    @mock.patch.object(steps.StepPart, '__init__', return_value=None)
    def test_pre_call(self, mock_init):
        obj = ModifierForTest()

        result = obj.pre_call('ctxt', 'pre_mod', 'post_mod', 'action')

        self.assertEqual(result, None)

    @mock.patch.object(steps.StepPart, '__init__', return_value=None)
    def test_post_call(self, mock_init):
        obj = ModifierForTest()

        result = obj.post_call('ctxt', 'result', 'action',
                               'post_mod', 'pre_mod')

        self.assertEqual(result, 'result')


class StepItemTest(unittest.TestCase):
    def test_init(self):
        result = steps.StepItem('cls', 'name', 'conf')

        self.assertEqual(result.cls, 'cls')
        self.assertEqual(result.name, 'name')
        self.assertEqual(result.conf, 'conf')

    def test_class_init(self):
        cls = mock.Mock()
        obj = steps.StepItem(cls, 'name', 'conf')

        result = obj.init('ctxt', 'step_addr')

        self.assertEqual(result, cls.return_value)
        cls.assert_called_once_with('ctxt', 'name', 'conf', 'step_addr')


class ActionForTest(object):
    pass


class StepTest(unittest.TestCase):
    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load', side_effect=TestingException("couldn't read"))
    @mock.patch.object(steps, 'StepAddress', side_effect=lambda f, i, k:
                       '%s[%s]:%s' % (f, k or '', i))
    @mock.patch.object(steps.Step, 'parse_step', return_value=[])
    def test_parse_file_unreadable(self, mock_parse_step, mock_StepAddress,
                                   mock_load, mock_open):
        filemock = mock.MagicMock()
        filemock.__enter__.return_value = filemock
        mock_open.return_value = filemock

        self.assertRaises(steps.ConfigError, steps.Step.parse_file,
                          'ctxt', 'fname')
        mock_open.assert_called_once_with('fname')
        mock_load.assert_called_once_with(filemock)
        self.assertFalse(mock_StepAddress.called)
        self.assertFalse(mock_parse_step.called)

    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load', return_value={})
    @mock.patch.object(steps, 'StepAddress', side_effect=lambda f, i, k:
                       '%s[%s]:%s' % (f, k or '', i))
    @mock.patch.object(steps.Step, 'parse_step', return_value=[])
    def test_parse_file_badlist(self, mock_parse_step, mock_StepAddress,
                                mock_load, mock_open):
        filemock = mock.MagicMock()
        filemock.__enter__.return_value = filemock
        mock_open.return_value = filemock

        self.assertRaises(steps.ConfigError, steps.Step.parse_file,
                          'ctxt', 'fname')
        mock_open.assert_called_once_with('fname')
        mock_load.assert_called_once_with(filemock)
        self.assertFalse(mock_StepAddress.called)
        self.assertFalse(mock_parse_step.called)

    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load', return_value=[])
    @mock.patch.object(steps, 'StepAddress', side_effect=lambda f, i, k:
                       '%s[%s]:%s' % (f, k or '', i))
    @mock.patch.object(steps.Step, 'parse_step', return_value=[])
    def test_parse_file_baddict(self, mock_parse_step, mock_StepAddress,
                                mock_load, mock_open):
        filemock = mock.MagicMock()
        filemock.__enter__.return_value = filemock
        mock_open.return_value = filemock

        self.assertRaises(steps.ConfigError, steps.Step.parse_file,
                          'ctxt', 'fname', 'key')
        mock_open.assert_called_once_with('fname')
        mock_load.assert_called_once_with(filemock)
        self.assertFalse(mock_StepAddress.called)
        self.assertFalse(mock_parse_step.called)

    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load', return_value=['step0', 'step1', 'step2'])
    @mock.patch.object(steps, 'StepAddress', side_effect=lambda f, i, k:
                       '%s[%s]:%s' % (f, k or '', i))
    @mock.patch.object(steps.Step, 'parse_step', return_value=['steps'])
    def test_parse_file_list(self, mock_parse_step, mock_StepAddress,
                             mock_load, mock_open):
        filemock = mock.MagicMock()
        filemock.__enter__.return_value = filemock
        mock_open.return_value = filemock

        result = steps.Step.parse_file('ctxt', 'fname')

        self.assertEqual(result, ['steps', 'steps', 'steps'])
        mock_open.assert_called_once_with('fname')
        mock_load.assert_called_once_with(filemock)
        mock_StepAddress.assert_has_calls([
            mock.call('fname', i, None) for i in range(3)
        ])
        self.assertEqual(mock_StepAddress.call_count, 3)
        mock_parse_step.assert_has_calls([
            mock.call('ctxt', 'fname[]:%d' % i, 'step%d' % i)
            for i in range(3)
        ])
        self.assertEqual(mock_parse_step.call_count, 3)

    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load', return_value={
        'key': ['step0', 'step1', 'step2'],
        'bad': ['bad0', 'bad1', 'bad2'],
    })
    @mock.patch.object(steps, 'StepAddress', side_effect=lambda f, i, k:
                       '%s[%s]:%s' % (f, k or '', i))
    @mock.patch.object(steps.Step, 'parse_step', return_value=['steps'])
    def test_parse_file_list(self, mock_parse_step, mock_StepAddress,
                             mock_load, mock_open):
        filemock = mock.MagicMock()
        filemock.__enter__.return_value = filemock
        mock_open.return_value = filemock

        result = steps.Step.parse_file('ctxt', 'fname', 'key')

        self.assertEqual(result, ['steps', 'steps', 'steps'])
        mock_open.assert_called_once_with('fname')
        mock_load.assert_called_once_with(filemock)
        mock_StepAddress.assert_has_calls([
            mock.call('fname', i, 'key') for i in range(3)
        ])
        self.assertEqual(mock_StepAddress.call_count, 3)
        mock_parse_step.assert_has_calls([
            mock.call('ctxt', 'fname[key]:%d' % i, 'step%d' % i)
            for i in range(3)
        ])
        self.assertEqual(mock_parse_step.call_count, 3)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.NORMAL,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_base(self, mock_call, mock_init, mock_schema_validate):
        step_conf = {
            'act': {'a': 1, 'b': 2},
            'mod1': {'c': 3, 'd': 4},
            'mod2': {'e': 5, 'f': 6},
            'mod3': {'g': 7, 'h': 8},
            'name': 'step name',
            'description': 'step description',
        }

        result = steps.Step.parse_step('ctxt', 'address', step_conf)

        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], steps.Step))
        mock_schema_validate.assert_has_calls([
            mock.call('step name', {'type': 'string'}, steps.ConfigError,
                      'name', step_addr='address'),
            mock.call('step description', {'type': 'string'},
                      steps.ConfigError, 'description', step_addr='address'),
        ], any_order=True)
        self.assertEqual(mock_schema_validate.call_count, 2)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            mod.assert_called_once_with(
                'ctxt', mod.modname, step_conf[mod.modname], 'address')
            mod.return_value.action_conf.assert_called_once_with(
                'ctxt', act, 'act', step_conf['act'], 'address')
        act.assert_called_once_with(
            'ctxt', 'act', step_conf['act'], 'address')
        mock_init.assert_called_once_with(
            'address', act.return_value, [mod.return_value for mod in mods],
            name='step name', description='step description')
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.NORMAL,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_str(self, mock_call, mock_init, mock_schema_validate):
        result = steps.Step.parse_step('ctxt', 'address', 'act')

        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], steps.Step))
        self.assertFalse(mock_schema_validate.called)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            self.assertFalse(mod.called)
            self.assertFalse(mod.return_value.action_conf.called)
        act.assert_called_once_with(
            'ctxt', 'act', None, 'address')
        mock_init.assert_called_once_with(
            'address', act.return_value, [])
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.NORMAL,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_badconf(self, mock_call, mock_init,
                                mock_schema_validate):
        step_conf = []

        self.assertRaises(steps.ConfigError, steps.Step.parse_step,
                          'ctxt', 'address', step_conf)
        self.assertFalse(mock_schema_validate.called)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            self.assertFalse(mod.called)
            self.assertFalse(mod.return_value.action_conf.called)
        self.assertFalse(act.called)
        self.assertFalse(mock_init.called)
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.NORMAL,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_missingkey(self, mock_call, mock_init,
                                   mock_schema_validate):
        step_conf = {
            'act': {'a': 1, 'b': 2},
            'mod1': {'c': 3, 'd': 4},
            'mod2': {'e': 5, 'f': 6},
            'mod3': {'g': 7, 'h': 8},
            'missing': {'i': 9, 'j': 10},
        }

        self.assertRaises(steps.ConfigError, steps.Step.parse_step,
                          'ctxt', 'address', step_conf)
        self.assertFalse(mock_schema_validate.called)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            self.assertFalse(mod.called)
            self.assertFalse(mod.return_value.action_conf.called)
        self.assertFalse(act.called)
        self.assertFalse(mock_init.called)
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act1': mock.Mock(step_action=False),
            'act2': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.NORMAL,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_multiact(self, mock_call, mock_init,
                                 mock_schema_validate):
        step_conf = {
            'act1': {'a': 1, 'b': 2},
            'mod1': {'c': 3, 'd': 4},
            'mod2': {'e': 5, 'f': 6},
            'mod3': {'g': 7, 'h': 8},
            'act2': {'i': 9, 'j': 10},
        }

        self.assertRaises(steps.ConfigError, steps.Step.parse_step,
                          'ctxt', 'address', step_conf)
        self.assertFalse(mock_schema_validate.called)
        act1 = entry.points[steps.NAMESPACE_ACTION]['act1']
        act2 = entry.points[steps.NAMESPACE_ACTION]['act2']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            self.assertFalse(mod.called)
            self.assertFalse(mod.return_value.action_conf.called)
        self.assertFalse(act1.called)
        self.assertFalse(act2.called)
        self.assertFalse(mock_init.called)
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.NORMAL,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_noact(self, mock_call, mock_init,
                              mock_schema_validate):
        step_conf = {
            'mod1': {'c': 3, 'd': 4},
            'mod2': {'e': 5, 'f': 6},
            'mod3': {'g': 7, 'h': 8},
        }

        self.assertRaises(steps.ConfigError, steps.Step.parse_step,
                          'ctxt', 'address', step_conf)
        self.assertFalse(mock_schema_validate.called)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            self.assertFalse(mod.called)
            self.assertFalse(mod.return_value.action_conf.called)
        self.assertFalse(act.called)
        self.assertFalse(mock_init.called)
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=False),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.STEP,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.NORMAL,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.NORMAL,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_badmod(self, mock_call, mock_init,
                               mock_schema_validate):
        step_conf = {
            'act': {'a': 1, 'b': 2},
            'mod1': {'c': 3, 'd': 4},
            'mod2': {'e': 5, 'f': 6},
            'mod3': {'g': 7, 'h': 8},
        }

        self.assertRaises(steps.ConfigError, steps.Step.parse_step,
                          'ctxt', 'address', step_conf)
        self.assertFalse(mock_schema_validate.called)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods[:-1]:
            mod.assert_called_once_with(
                'ctxt', mod.modname, step_conf[mod.modname], 'address')
            mod.return_value.action_conf.assert_called_once_with(
                'ctxt', act, 'act', step_conf['act'], 'address')
        self.assertFalse(mods[-1].called)
        self.assertFalse(mods[-1].return_value.action_conf.called)
        self.assertFalse(act.called)
        self.assertFalse(mock_init.called)
        self.assertFalse(mock_call.called)

    @mock.patch.object(entry, 'points', {
        steps.NAMESPACE_ACTION: {
            'act': mock.Mock(step_action=True),
        },
        steps.NAMESPACE_MODIFIER: {
            'mod1': mock.Mock(
                modname='mod1',
                restriction=steps.Modifier.STEP,
                priority=100,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod2': mock.Mock(
                modname='mod2',
                restriction=steps.Modifier.UNRESTRICTED,
                priority=50,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
            'mod3': mock.Mock(
                modname='mod3',
                restriction=steps.Modifier.STEP,
                priority=0,
                return_value=mock.Mock(**{
                    'action_conf.side_effect': lambda x, a, n, conf, r: conf,
                }),
            ),
        },
    })
    @mock.patch('timid.utils.schema_validate')
    @mock.patch.object(steps.Step, '__init__', return_value=None)
    @mock.patch.object(steps.Step, '__call__', return_value='called')
    def test_parse_step_step(self, mock_call, mock_init, mock_schema_validate):
        step_conf = {
            'act': {'a': 1, 'b': 2},
            'mod1': {'c': 3, 'd': 4},
            'mod2': {'e': 5, 'f': 6},
            'mod3': {'g': 7, 'h': 8},
        }

        result = steps.Step.parse_step('ctxt', 'address', step_conf)

        self.assertEqual(result, 'called')
        self.assertFalse(mock_schema_validate.called)
        act = entry.points[steps.NAMESPACE_ACTION]['act']
        mods = sorted(entry.points[steps.NAMESPACE_MODIFIER].values(),
                      key=lambda x: x.priority)
        for mod in mods:
            mod.assert_called_once_with(
                'ctxt', mod.modname, step_conf[mod.modname], 'address')
            mod.return_value.action_conf.assert_called_once_with(
                'ctxt', act, 'act', step_conf['act'], 'address')
        act.assert_called_once_with(
            'ctxt', 'act', step_conf['act'], 'address')
        mock_init.assert_called_once_with(
            'address', act.return_value, [mod.return_value for mod in mods])
        mock_call.assert_called_once_with('ctxt')

    def test_init_base(self):
        action = ActionForTest()

        result = steps.Step('addr', action)

        self.assertEqual(result.step_addr, 'addr')
        self.assertEqual(id(result.action), id(action))
        self.assertEqual(result.modifiers, [])
        self.assertEqual(result.name, 'ActionForTest')
        self.assertEqual(result.description, None)

    def test_init_alt(self):
        action = ActionForTest()

        result = steps.Step('addr', action, 'mods', 'name', 'desc')

        self.assertEqual(result.step_addr, 'addr')
        self.assertEqual(id(result.action), id(action))
        self.assertEqual(result.modifiers, 'mods')
        self.assertEqual(result.name, 'name')
        self.assertEqual(result.description, 'desc')

    @mock.patch.object(steps, 'StepResult')
    def test_call_base(self, mock_StepResult):
        action = mock.Mock(return_value='result')
        mods = [mock.Mock(**{
            'pre_call.return_value': None,
            'post_call.side_effect': lambda x, r, a, m_l, m_e: r,
        }) for i in range(5)]
        obj = steps.Step('addr', action, mods, 'name', 'desc')

        result = obj('ctxt')

        self.assertEqual(result, 'result')
        action.assert_called_once_with('ctxt')
        for i, mod in enumerate(mods):
            mod.assert_has_calls([
                mock.call.pre_call('ctxt', mods[:i], mods[i + 1:], action),
                mock.call.post_call(
                    'ctxt', result, action, mods[i + 1:], mods[:i]),
            ])
            self.assertEqual(len(mod.method_calls), 2)
        self.assertFalse(mock_StepResult.called)

    @mock.patch.object(steps, 'StepResult')
    def test_call_exception(self, mock_StepResult):
        action = mock.Mock(side_effect=TestingException('failure'))
        mods = [mock.Mock(**{
            'pre_call.return_value': None,
            'post_call.side_effect': lambda x, r, a, m_l, m_e: r,
        }) for i in range(5)]
        obj = steps.Step('addr', action, mods, 'name', 'desc')

        result = obj('ctxt')

        self.assertEqual(result, mock_StepResult.return_value)
        action.assert_called_once_with('ctxt')
        for i, mod in enumerate(mods):
            mod.assert_has_calls([
                mock.call.pre_call('ctxt', mods[:i], mods[i + 1:], action),
                mock.call.post_call(
                    'ctxt', result, action, mods[i + 1:], mods[:i]),
            ])
            self.assertEqual(len(mod.method_calls), 2)
        mock_StepResult.assert_called_once_with(
            exc_info=(TestingException, mock.ANY, mock.ANY))

    @mock.patch.object(steps, 'StepResult')
    def test_call_noresult(self, mock_StepResult):
        action = mock.Mock(return_value=None)
        mods = [mock.Mock(**{
            'pre_call.return_value': None,
            'post_call.side_effect': lambda x, r, a, m_l, m_e: r,
        }) for i in range(5)]
        obj = steps.Step('addr', action, mods, 'name', 'desc')

        result = obj('ctxt')

        self.assertEqual(result, mock_StepResult.return_value)
        action.assert_called_once_with('ctxt')
        for i, mod in enumerate(mods):
            mod.assert_has_calls([
                mock.call.pre_call('ctxt', mods[:i], mods[i + 1:], action),
                mock.call.post_call(
                    'ctxt', result, action, mods[i + 1:], mods[:i]),
            ])
            self.assertEqual(len(mod.method_calls), 2)
        mock_StepResult.assert_called_once_with(status=steps.ERROR)

    @mock.patch.object(steps, 'StepResult')
    def test_call_modpreempt(self, mock_StepResult):
        action = mock.Mock(return_value='result')
        mods = [mock.Mock(**{
            'pre_call.return_value': 'preempt' if i == 2 else None,
            'post_call.side_effect': lambda x, r, a, m_l, m_e: r,
        }) for i in range(5)]
        obj = steps.Step('addr', action, mods, 'name', 'desc')

        result = obj('ctxt')

        self.assertEqual(result, 'preempt')
        self.assertFalse(action.called)
        for i, mod in enumerate(mods):
            if i <= 2:
                mod.assert_has_calls([
                    mock.call.pre_call('ctxt', mods[:i], mods[i + 1:], action),
                    mock.call.post_call(
                        'ctxt', result, action, mods[i + 1:], mods[:i]),
                ])
                self.assertEqual(len(mod.method_calls), 2)
            else:
                self.assertEqual(len(mod.method_calls), 0)
        self.assertFalse(mock_StepResult.called)

    @mock.patch.object(steps, 'StepResult')
    def test_call_nomod(self, mock_StepResult):
        action = mock.Mock(return_value='result')
        obj = steps.Step('addr', action, [], 'name', 'desc')

        result = obj('ctxt')

        self.assertEqual(result, 'result')
        action.assert_called_once_with('ctxt')
        self.assertFalse(mock_StepResult.called)


class StepResultTest(unittest.TestCase):
    def test_init_base(self):
        result = steps.StepResult()

        self.assertEqual(result.msg, None)
        self.assertEqual(result.exc_info, None)
        self.assertEqual(result.returncode, None)
        self.assertEqual(result.results, [])
        self.assertEqual(result.state, None)
        self.assertEqual(result._ignore, None)

    def test_init_alt(self):
        result = steps.StepResult(
            state='state', msg='msg', ignore='ignore', returncode=1,
            exc_info=('type', 'val', 'tb'), results=['res1', 'res2', 'res3'])

        self.assertEqual(result.msg, 'msg')
        self.assertEqual(result.exc_info, ('type', 'val', 'tb'))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.results, ['res1', 'res2', 'res3'])
        self.assertEqual(result.state, 'state')
        self.assertEqual(result._ignore, 'ignore')

    def test_init_state_exc_info(self):
        result = steps.StepResult(exc_info=('type', 'val', 'tb'))

        self.assertEqual(result.exc_info, ('type', 'val', 'tb'))
        self.assertEqual(result.state, steps.ERROR)

    def test_init_state_returncode_0(self):
        result = steps.StepResult(returncode=0)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.state, steps.SUCCESS)

    def test_init_state_returncode_1(self):
        result = steps.StepResult(returncode=1)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.state, steps.FAILURE)

    def test_init_state_results_skipped(self):
        others = [
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
        ]

        result = steps.StepResult(results=others)

        self.assertEqual(result.results, others)
        self.assertEqual(result.state, steps.SKIPPED)
        self.assertEqual(result._ignore, False)

    def test_init_state_results_success(self):
        others = [
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SUCCESS, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
        ]

        result = steps.StepResult(results=others)

        self.assertEqual(result.results, others)
        self.assertEqual(result.state, steps.SUCCESS)
        self.assertEqual(result._ignore, False)

    def test_init_state_results_failure(self):
        others = [
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SUCCESS, ignore=None),
            mock.Mock(state=steps.FAILURE, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
        ]

        result = steps.StepResult(results=others)

        self.assertEqual(result.results, others)
        self.assertEqual(result.state, steps.FAILURE)
        self.assertEqual(result._ignore, False)

    def test_init_state_results_error(self):
        others = [
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SKIPPED, ignore=None),
            mock.Mock(state=steps.SUCCESS, ignore=None),
            mock.Mock(state=steps.FAILURE, ignore=None),
            mock.Mock(state=steps.ERROR, ignore=None),
        ]

        result = steps.StepResult(results=others)

        self.assertEqual(result.results, others)
        self.assertEqual(result.state, steps.ERROR)
        self.assertEqual(result._ignore, False)

    def test_init_ignore_results_false(self):
        others = [
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=False),
        ]

        result = steps.StepResult(results=others)

        self.assertEqual(result.results, others)
        self.assertEqual(result.state, steps.SKIPPED)
        self.assertEqual(result._ignore, False)

    def test_init_ignore_results_true(self):
        others = [
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=True),
            mock.Mock(state=steps.SKIPPED, ignore=False),
            mock.Mock(state=steps.SKIPPED, ignore=False),
        ]

        result = steps.StepResult(results=others)

        self.assertEqual(result.results, others)
        self.assertEqual(result.state, steps.SKIPPED)
        self.assertEqual(result._ignore, True)

    def test_bool_skipped(self):
        obj = steps.StepResult(state=steps.SKIPPED)

        self.assertTrue(obj)

    def test_bool_success(self):
        obj = steps.StepResult(state=steps.SUCCESS)

        self.assertTrue(obj)

    def test_bool_failure(self):
        obj = steps.StepResult(state=steps.FAILURE)

        self.assertFalse(obj)

    def test_bool_error(self):
        obj = steps.StepResult(state=steps.ERROR)

        self.assertFalse(obj)

    def test_bool_skipped_ignore(self):
        obj = steps.StepResult(state=steps.SKIPPED, ignore=True)

        self.assertTrue(obj)

    def test_bool_success_ignore(self):
        obj = steps.StepResult(state=steps.SUCCESS, ignore=True)

        self.assertTrue(obj)

    def test_bool_failure_ignore(self):
        obj = steps.StepResult(state=steps.FAILURE, ignore=True)

        self.assertTrue(obj)

    def test_bool_error_ignore(self):
        obj = steps.StepResult(state=steps.ERROR, ignore=True)

        self.assertTrue(obj)

    def test_ignore_get_none(self):
        obj = steps.StepResult()

        self.assertEqual(obj.ignore, False)

    def test_ignore_get_false(self):
        obj = steps.StepResult(ignore=False)

        self.assertEqual(obj.ignore, False)

    def test_ignore_get_true(self):
        obj = steps.StepResult(ignore=True)

        self.assertEqual(obj.ignore, True)

    def test_ignore_set_none(self):
        obj = steps.StepResult()

        obj.ignore = 'ignore'

        self.assertEqual(obj._ignore, 'ignore')

    def test_ignore_set_false(self):
        obj = steps.StepResult(ignore=False)

        obj.ignore = 'ignore'

        self.assertEqual(obj._ignore, False)

    def test_ignore_set_true(self):
        obj = steps.StepResult(ignore=True)

        obj.ignore = 'ignore'

        self.assertEqual(obj._ignore, True)


class SensitiveDictActionForTest(steps.SensitiveDictAction):
    context_attr = 'attr'


class SensitiveDictActionTest(unittest.TestCase):
    @mock.patch.object(os.path, 'dirname', return_value='/root/dir')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_base(self, mock_init, mock_dirname):
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: '%s_tmpl' % x,
        })
        conf = {
            'set': {'a': 5, 'b': 7},
            'unset': ['b', 'c', 'd'],
            'sensitive': ['a', 'c', 'e'],
            'files': ['file1', 'file2', 'file3'],
        }
        addr = mock.Mock(fname='file/name')

        result = SensitiveDictActionForTest(ctxt, 'test', conf, addr)

        self.assertEqual(result.set_vars, {'a': '5_tmpl', 'b': '7_tmpl'})
        self.assertEqual(result.unset_vars, set(['b', 'c', 'd']))
        self.assertEqual(result.sensitive_vars, set(['a', 'c', 'e']))
        self.assertEqual(result.files,
                         ['file1_tmpl', 'file2_tmpl', 'file3_tmpl'])
        self.assertEqual(result.dirname, '/root/dir')
        mock_init.assert_called_once_with(ctxt, 'test', conf, addr)
        ctxt.template.assert_has_calls([
            mock.call(5),
            mock.call(7),
            mock.call('file1'),
            mock.call('file2'),
            mock.call('file3'),
        ], any_order=True)
        mock_dirname.assert_called_once_with('file/name')

    @mock.patch.object(os.path, 'dirname', return_value='')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_alt(self, mock_init, mock_dirname):
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: '%s_tmpl' % x,
        })
        conf = {
            'set': {'a': 5, 'b': 7},
            'unset': ['b', 'c', 'd'],
            'sensitive': ['a', 'c', 'e'],
            'files': ['file1', 'file2', 'file3'],
        }
        addr = mock.Mock(fname='file/name')

        result = SensitiveDictActionForTest(ctxt, 'test', conf, addr)

        self.assertEqual(result.set_vars, {'a': '5_tmpl', 'b': '7_tmpl'})
        self.assertEqual(result.unset_vars, set(['b', 'c', 'd']))
        self.assertEqual(result.sensitive_vars, set(['a', 'c', 'e']))
        self.assertEqual(result.files,
                         ['file1_tmpl', 'file2_tmpl', 'file3_tmpl'])
        self.assertEqual(result.dirname, os.curdir)
        mock_init.assert_called_once_with(ctxt, 'test', conf, addr)
        ctxt.template.assert_has_calls([
            mock.call(5),
            mock.call(7),
            mock.call('file1'),
            mock.call('file2'),
            mock.call('file3'),
        ], any_order=True)
        mock_dirname.assert_called_once_with('file/name')

    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load')
    @mock.patch('timid.utils.canonicalize_path', side_effect=lambda x, y: y)
    @mock.patch.object(os.path, 'dirname', return_value='/root/dir')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_call_base(self, mock_init, mock_dirname, mock_canonicalize_path,
                       mock_load, mock_open):
        def fake_load(fh):
            if isinstance(fh.data, Exception):
                raise fh.data
            return fh.data
        mock_load.side_effect = fake_load
        files = {
            'f1.yaml': TestingException("can't open"),
            'f2.yaml': mock.MagicMock(data=TestingException("can't read")),
            'f3.yaml': mock.MagicMock(data=['one', 'two', 'three']),
            'f4.yaml': mock.MagicMock(data={'a': 2, 'f': 11}),
            'f5.yaml': mock.MagicMock(data={'f': 12, 'g': 13}),
        }
        for fhmock in files.values():
            if not isinstance(fhmock, Exception):
                fhmock.__enter__.return_value = fhmock
                fhmock.__exit__.return_value = False
        mock_open.side_effect = lambda x: files[x]
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: (lambda y: x),
            'attr': {'a': 1, 'b': 3, 'c': 5, 'd': 7, 'e': 9},
        })
        conf = {
            'set': {'a': 5, 'b': 7},
            'unset': ['b', 'c', 'd'],
            'files': ['f1.yaml', 'f2.yaml', 'f3.yaml', 'f4.yaml', 'f5.yaml'],
        }
        addr = mock.Mock(fname='file_name')
        action = SensitiveDictActionForTest(ctxt, 'test', conf, addr)

        result = action(ctxt)

        self.assertTrue(isinstance(result, steps.StepResult))
        self.assertEqual(result.state, steps.SUCCESS)
        self.assertEqual(ctxt.attr, {'a': 5, 'b': 7, 'e': 9, 'f': 12, 'g': 13})

    @mock.patch.object(builtins, 'open')
    @mock.patch('yaml.load')
    @mock.patch('timid.utils.canonicalize_path', side_effect=lambda x, y: y)
    @mock.patch.object(os.path, 'dirname', return_value='/root/dir')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_call_sensitive(self, mock_init, mock_dirname,
                            mock_canonicalize_path, mock_load, mock_open):
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: (lambda y: x),
        })
        conf = {
            'sensitive': ['a', 'c', 'e'],
        }
        addr = mock.Mock(fname='file_name')
        action = SensitiveDictActionForTest(ctxt, 'test', conf, addr)

        result = action(ctxt)

        self.assertTrue(isinstance(result, steps.StepResult))
        self.assertEqual(result.state, steps.SUCCESS)
        ctxt.attr.declare_sensitive.assert_has_calls([
            mock.call('a'),
            mock.call('c'),
            mock.call('e'),
        ], any_order=True)
        self.assertFalse(mock_canonicalize_path.called)
        self.assertFalse(mock_load.called)
        self.assertFalse(mock_open.called)


class IncludeActionTest(unittest.TestCase):
    @mock.patch.object(os.path, 'dirname', return_value='/root/dir')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_base(self, mock_init, mock_dirname):
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: 'template:%s' % x,
        })
        addr = mock.Mock(fname='included/from')

        result = steps.IncludeAction(
            ctxt, 'include', {'path': 'some/path'}, addr)

        self.assertEqual(result.path, 'template:some/path')
        self.assertEqual(result.key, 'template:None')
        self.assertEqual(result.start, None)
        self.assertEqual(result.stop, None)
        self.assertEqual(result.dirname, '/root/dir')
        mock_init.assert_called_once_with(
            ctxt, 'include', {'path': 'some/path'}, addr)
        mock_dirname.assert_called_once_with('included/from')

    @mock.patch.object(os.path, 'dirname', return_value='/root/dir')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_str(self, mock_init, mock_dirname):
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: 'template:%s' % x,
        })
        addr = mock.Mock(fname='included/from')

        result = steps.IncludeAction(
            ctxt, 'include', 'some/path', addr)

        self.assertEqual(result.path, 'template:some/path')
        self.assertEqual(result.key, 'template:None')
        self.assertEqual(result.start, None)
        self.assertEqual(result.stop, None)
        self.assertEqual(result.dirname, '/root/dir')
        mock_init.assert_called_once_with(
            ctxt, 'include', {'path': 'some/path'}, addr)
        mock_dirname.assert_called_once_with('included/from')

    @mock.patch.object(os.path, 'dirname', return_value='')
    @mock.patch.object(steps.Action, '__init__', return_value=None)
    def test_init_alt(self, mock_init, mock_dirname):
        ctxt = mock.Mock(**{
            'template.side_effect': lambda x: 'template:%s' % x,
        })
        conf = {
            'path': 'some/path',
            'key': 'some_key',
            'start': 2,
            'stop': 7,
        }
        addr = mock.Mock(fname='included/from')

        result = steps.IncludeAction(
            ctxt, 'include', conf, addr)

        self.assertEqual(result.path, 'template:some/path')
        self.assertEqual(result.key, 'template:some_key')
        self.assertEqual(result.start, 2)
        self.assertEqual(result.stop, 7)
        self.assertEqual(result.dirname, os.curdir)
        mock_init.assert_called_once_with(
            ctxt, 'include', conf, addr)
        mock_dirname.assert_called_once_with('included/from')

    def get_action(self, path, key=None, start=None, stop=None):
        with mock.patch.object(steps.IncludeAction, '__init__',
                               return_value=None):
            obj = steps.IncludeAction()

        obj.dirname = 'dirname'
        obj.path = mock.Mock(return_value=path)
        obj.key = mock.Mock(return_value=key)
        obj.step_addr = 'step_addr'
        obj.start = start
        obj.stop = stop

        return obj

    @mock.patch('timid.utils.canonicalize_path',
                side_effect=lambda x, y: '%s/%s' % (x, y))
    @mock.patch.object(steps.Step, 'parse_file',
                       return_value=['step%d' % i for i in range(7)])
    def test_call_base(self, mock_parse_file, mock_canonicalize_path):
        obj = self.get_action('some/path')

        result = obj('ctxt')

        self.assertEqual(result, ['step%d' % i for i in range(7)])
        obj.path.assert_called_once_with('ctxt')
        mock_canonicalize_path.assert_called_once_with('dirname', 'some/path')
        obj.key.assert_called_once_with('ctxt')
        mock_parse_file.assert_called_once_with(
            'ctxt', 'dirname/some/path', None, 'step_addr')

    @mock.patch('timid.utils.canonicalize_path',
                side_effect=lambda x, y: '%s/%s' % (x, y))
    @mock.patch.object(steps.Step, 'parse_file',
                       return_value=['step%d' % i for i in range(7)])
    def test_call_key(self, mock_parse_file, mock_canonicalize_path):
        obj = self.get_action('some/path', key='key')

        result = obj('ctxt')

        self.assertEqual(result, ['step%d' % i for i in range(7)])
        obj.path.assert_called_once_with('ctxt')
        mock_canonicalize_path.assert_called_once_with('dirname', 'some/path')
        obj.key.assert_called_once_with('ctxt')
        mock_parse_file.assert_called_once_with(
            'ctxt', 'dirname/some/path', 'key', 'step_addr')

    @mock.patch('timid.utils.canonicalize_path',
                side_effect=lambda x, y: '%s/%s' % (x, y))
    @mock.patch.object(steps.Step, 'parse_file',
                       return_value=['step%d' % i for i in range(7)])
    def test_call_start(self, mock_parse_file, mock_canonicalize_path):
        obj = self.get_action('some/path', start=1)

        result = obj('ctxt')

        self.assertEqual(result, ['step%d' % i for i in range(1, 7)])
        obj.path.assert_called_once_with('ctxt')
        mock_canonicalize_path.assert_called_once_with('dirname', 'some/path')
        obj.key.assert_called_once_with('ctxt')
        mock_parse_file.assert_called_once_with(
            'ctxt', 'dirname/some/path', None, 'step_addr')

    @mock.patch('timid.utils.canonicalize_path',
                side_effect=lambda x, y: '%s/%s' % (x, y))
    @mock.patch.object(steps.Step, 'parse_file',
                       return_value=['step%d' % i for i in range(7)])
    def test_call_stop(self, mock_parse_file, mock_canonicalize_path):
        obj = self.get_action('some/path', stop=6)

        result = obj('ctxt')

        self.assertEqual(result, ['step%d' % i for i in range(6)])
        obj.path.assert_called_once_with('ctxt')
        mock_canonicalize_path.assert_called_once_with('dirname', 'some/path')
        obj.key.assert_called_once_with('ctxt')
        mock_parse_file.assert_called_once_with(
            'ctxt', 'dirname/some/path', None, 'step_addr')

    @mock.patch('timid.utils.canonicalize_path',
                side_effect=lambda x, y: '%s/%s' % (x, y))
    @mock.patch.object(steps.Step, 'parse_file',
                       return_value=['step%d' % i for i in range(7)])
    def test_call_range(self, mock_parse_file, mock_canonicalize_path):
        obj = self.get_action('some/path', start=1, stop=6)

        result = obj('ctxt')

        self.assertEqual(result, ['step%d' % i for i in range(1, 6)])
        obj.path.assert_called_once_with('ctxt')
        mock_canonicalize_path.assert_called_once_with('dirname', 'some/path')
        obj.key.assert_called_once_with('ctxt')
        mock_parse_file.assert_called_once_with(
            'ctxt', 'dirname/some/path', None, 'step_addr')
