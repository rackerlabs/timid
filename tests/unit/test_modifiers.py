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

from timid import modifiers
from timid import steps


class ConditionalModifierTest(unittest.TestCase):
    @mock.patch.object(steps.Modifier, '__init__', return_value=None)
    def test_init(self, mock_init):
        ctxt = mock.Mock(**{'expression.side_effect': lambda x: '%s_expr' % x})

        result = modifiers.ConditionalModifier(
            ctxt, 'when', 'expr', 'step_addr')

        self.assertEqual(result.condition, 'expr_expr')
        ctxt.expression.assert_called_once_with('expr')

    def get_modifier(self, result):
        with mock.patch.object(modifiers.ConditionalModifier, '__init__',
                               return_value=None):
            mod = modifiers.ConditionalModifier()

        mod.condition = lambda x: result

        return mod

    def test_pre_call_false(self):
        mod = self.get_modifier(False)

        result = mod.pre_call('ctxt', 'pre_mod', 'post_mod', 'action')

        self.assertTrue(isinstance(result, steps.StepResult))
        self.assertEqual(result.state, steps.SKIPPED)

    def test_pre_call_true(self):
        mod = self.get_modifier(True)

        result = mod.pre_call('ctxt', 'pre_mod', 'post_mod', 'action')

        self.assertEqual(result, None)


class IgnoreErrorsModifierTest(unittest.TestCase):
    def get_modifier(self, config):
        with mock.patch.object(modifiers.IgnoreErrorsModifier, '__init__',
                               return_value=None):
            mod = modifiers.IgnoreErrorsModifier()

        mod.config = config

        return mod

    def test_post_call(self):
        orig_result = mock.Mock(ignore=None)
        mod = self.get_modifier('config')

        new_result = mod.post_call('ctxt', orig_result, 'action',
                                   'post_mod', 'pre_mod')

        self.assertEqual(id(new_result), id(orig_result))
        self.assertEqual(orig_result.ignore, 'config')
