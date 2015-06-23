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

import jinja2
import mock

from timid import context
from timid import environment
from timid import utils


class ContextTest(unittest.TestCase):
    @mock.patch.object(environment, 'Environment')
    def test_init_base(self, mock_Environment):
        result = context.Context()

        self.assertEqual(result.verbose, 1)
        self.assertEqual(result.debug, False)
        self.assertTrue(isinstance(result.variables, utils.SensitiveDict))
        self.assertEqual(result.variables, {})
        self.assertEqual(result.environment, mock_Environment.return_value)
        self.assertEqual(result.steps, [])
        self.assertTrue(isinstance(result._jinja, jinja2.Environment))
        self.assertEqual(id(result._jinja.globals['env']),
                         id(result.environment))
        mock_Environment.assert_called_once_with(cwd=None)

    @mock.patch.object(environment, 'Environment')
    def test_init_alt(self, mock_Environment):
        result = context.Context(5, True, 'some/dir/ectory')

        self.assertEqual(result.verbose, 5)
        self.assertEqual(result.debug, True)
        self.assertTrue(isinstance(result.variables, utils.SensitiveDict))
        self.assertEqual(result.variables, {})
        self.assertEqual(result.environment, mock_Environment.return_value)
        self.assertEqual(result.steps, [])
        self.assertTrue(isinstance(result._jinja, jinja2.Environment))
        self.assertEqual(id(result._jinja.globals['env']),
                         id(result.environment))
        mock_Environment.assert_called_once_with(cwd='some/dir/ectory')

    @mock.patch.object(jinja2, 'Environment', return_value=mock.Mock(**{
        'globals': {},
        'from_string.return_value': mock.Mock(**{
            'render.return_value': 'rendered',
        }),
    }))
    def test_template_nonstr(self, mock_Environment):
        jinja_env = mock_Environment.return_value
        tmpl = jinja_env.from_string.return_value
        obj = context.Context()

        result = obj.template(1234)

        self.assertTrue(callable(result))
        self.assertFalse(jinja_env.from_string.called)
        self.assertFalse(tmpl.render.called)

        rendered = result(obj)

        self.assertEqual(rendered, 1234)
        self.assertFalse(tmpl.render.called)

    @mock.patch.object(jinja2, 'Environment', return_value=mock.Mock(**{
        'globals': {},
        'from_string.return_value': mock.Mock(**{
            'render.return_value': 'rendered',
        }),
    }))
    def test_template_str(self, mock_Environment):
        jinja_env = mock_Environment.return_value
        tmpl = jinja_env.from_string.return_value
        obj = context.Context()

        result = obj.template('spam')

        self.assertTrue(callable(result))
        jinja_env.from_string.assert_called_once_with('spam')
        self.assertFalse(tmpl.render.called)

        rendered = result(obj)

        self.assertEqual(rendered, 'rendered')
        tmpl.render.assert_called_once_with(obj.variables)

    @mock.patch.object(jinja2, 'Environment', return_value=mock.Mock(**{
        'globals': {},
        'compile_expression.return_value': mock.Mock(**{
            'return_value': 'rendered',
        }),
    }))
    def test_expression_nonstr(self, mock_Environment):
        jinja_env = mock_Environment.return_value
        expr = jinja_env.compile_expression.return_value
        obj = context.Context()

        result = obj.expression(1234)

        self.assertTrue(callable(result))
        self.assertFalse(jinja_env.compile_expression.called)
        self.assertFalse(expr.called)

        rendered = result(obj)

        self.assertEqual(rendered, 1234)
        self.assertFalse(expr.called)

    @mock.patch.object(jinja2, 'Environment', return_value=mock.Mock(**{
        'globals': {},
        'compile_expression.return_value': mock.Mock(**{
            'return_value': 'rendered',
        }),
    }))
    def test_expression_str(self, mock_Environment):
        jinja_env = mock_Environment.return_value
        expr = jinja_env.compile_expression.return_value
        obj = context.Context()

        result = obj.expression('spam')

        self.assertTrue(callable(result))
        jinja_env.compile_expression.assert_called_once_with('spam')
        self.assertFalse(expr.called)

        rendered = result(obj)

        self.assertEqual(rendered, 'rendered')
        expr.assert_called_once_with(obj.variables)
