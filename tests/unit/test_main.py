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

import sys
import unittest

import mock
import six

from timid import main
from timid import steps


class TestingException(Exception):
    pass


class TimidTest(unittest.TestCase):
    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_base(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml')

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            step.assert_called_once_with(ctxt)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.post_step.call_count, len(steps))
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . SUCCESS\n'
                         '[Step 3]: step3 . . . SUCCESS\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_debug(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml', debug=True)

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            step.assert_called_once_with(ctxt)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.post_step.call_count, len(steps))
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . SUCCESS\n'
                         '[Step 3]: step3 . . . SUCCESS\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(),
                         'Reading test steps from test.yaml...\n')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_key(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml', key='key')

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', 'key')
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            step.assert_called_once_with(ctxt)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.post_step.call_count, len(steps))
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . SUCCESS\n'
                         '[Step 3]: step3 . . . SUCCESS\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_key_debug(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml', key='key', debug=True)

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', 'key')
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            step.assert_called_once_with(ctxt)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.post_step.call_count, len(steps))
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . SUCCESS\n'
                         '[Step 3]: step3 . . . SUCCESS\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(),
                         'Reading test steps from test.yaml[key]...\n')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_external_exts(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock.Mock(**{
            'read_steps.side_effect': lambda c, s: s,
            'pre_step.return_value': False,
        })
        int_exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml', exts=exts)

        self.assertEqual(result, None)
        self.assertFalse(mock_ExtensionSet.called)
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        self.assertFalse(int_exts.read_steps.called)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        self.assertFalse(int_exts.pre_step.called)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            step.assert_called_once_with(ctxt)
        self.assertFalse(int_exts.post_step.called)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.post_step.call_count, len(steps))
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . SUCCESS\n'
                         '[Step 3]: step3 . . . SUCCESS\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_check(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml', check=True)

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        self.assertFalse(exts.pre_step.called)
        for step in steps:
            self.assertFalse(step.called)
        self.assertFalse(exts.post_step.called)
        self.assertEqual(sys.stdout.getvalue(), '')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.side_effect': lambda c, s, i: i == 2,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': False,
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
    ])
    def test_skip(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml')

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            if step.call_expected:
                step.assert_called_once_with(ctxt)
            else:
                self.assertFalse(step.called)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
            if step.call_expected
        ])
        self.assertEqual(exts.post_step.call_count, len(steps) - 1)
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . SKIPPED\n'
                         '[Step 3]: step3 . . . SUCCESS\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.FAILURE, ignore=True),
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS, ignore=True),
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
        }),
    ])
    def test_ignored(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml')

        self.assertEqual(result, None)
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps))
        for step in steps:
            step.assert_called_once_with(ctxt)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
        ])
        self.assertEqual(exts.post_step.call_count, len(steps))
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . FAILURE (ignored)\n'
                         '[Step 3]: step3 . . . SUCCESS (ignored)\n'
                         '[Step 4]: step4 . . . SUCCESS\n')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.FAILURE),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': False,
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': False,
        }),
    ])
    def test_failure(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml')

        self.assertEqual(result, 'Test step failure')
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
            if step.call_expected
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps) - 2)
        for step in steps:
            if step.call_expected:
                step.assert_called_once_with(ctxt)
            else:
                self.assertFalse(step.called)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
            if step.call_expected
        ])
        self.assertEqual(exts.post_step.call_count, len(steps) - 2)
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . FAILURE\n')
        self.assertEqual(sys.stderr.getvalue(), '')

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('timid.extensions.ExtensionSet', return_value=mock.Mock(**{
        'read_steps.side_effect': lambda c, s: s,
        'pre_step.return_value': False,
    }))
    @mock.patch.object(steps.Step, 'parse_file', return_value=[
        mock.Mock(**{
            'st_name': 'step0',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step1',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step2',
            'return_value': steps.StepResult(steps.FAILURE, msg='eek!'),
            'call_expected': True,
        }),
        mock.Mock(**{
            'st_name': 'step3',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': False,
        }),
        mock.Mock(**{
            'st_name': 'step4',
            'return_value': steps.StepResult(steps.SUCCESS),
            'call_expected': False,
        }),
    ])
    def test_failure_msg(self, mock_parse_file, mock_ExtensionSet):
        steps = mock_parse_file.return_value
        exts = mock_ExtensionSet.return_value
        for step in steps:
            # I hate this one feature of the mock library...
            step.name = step.st_name
        ctxt = mock.Mock(steps=[])

        result = main.timid(ctxt, 'test.yaml')

        self.assertEqual(result, 'Test step failure: eek!')
        mock_ExtensionSet.assert_called_once_with()
        mock_parse_file.assert_called_once_with(ctxt, 'test.yaml', None)
        exts.read_steps.assert_called_once_with(ctxt, steps)
        exts.pre_step.assert_has_calls([
            mock.call(ctxt, step, idx) for idx, step in enumerate(steps)
            if step.call_expected
        ])
        self.assertEqual(exts.pre_step.call_count, len(steps) - 2)
        for step in steps:
            if step.call_expected:
                step.assert_called_once_with(ctxt)
            else:
                self.assertFalse(step.called)
        exts.post_step.assert_has_calls([
            mock.call(ctxt, step, idx, step.return_value)
            for idx, step in enumerate(steps)
            if step.call_expected
        ])
        self.assertEqual(exts.post_step.call_count, len(steps) - 2)
        self.assertEqual(sys.stdout.getvalue(),
                         '[Step 0]: step0 . . . SUCCESS\n'
                         '[Step 1]: step1 . . . SUCCESS\n'
                         '[Step 2]: step2 . . . FAILURE\n')
        self.assertEqual(sys.stderr.getvalue(), '')


class ArgsTest(unittest.TestCase):
    @mock.patch('timid.extensions.ExtensionSet.prepare')
    def test_function(self, mock_prepare):
        main._args('parser')

        mock_prepare.assert_called_once_with('parser')


class ProcessorTest(unittest.TestCase):
    @mock.patch('timid.context.Context', return_value='ctxt')
    @mock.patch('timid.extensions.ExtensionSet.activate',
                return_value=mock.Mock(**{
                    'finalize.side_effect': lambda c, r: r,
                }))
    @mock.patch('traceback.print_exc')
    def test_base(self, mock_print_exc, mock_activate, mock_Context):
        ctxt = mock_Context.return_value
        exts = mock_activate.return_value
        args = mock.Mock(directory='directory', debug=False)

        gen = main._processor(args)
        gen.next()

        self.assertEqual(args.ctxt, ctxt)
        self.assertEqual(args.exts, exts)
        self.assertFalse(mock_print_exc.called)
        self.assertFalse(exts.finalize.called)

        result = gen.send(None)

        self.assertEqual(result, None)
        self.assertFalse(mock_print_exc.called)
        exts.finalize.assert_called_once_with(ctxt, None)

    @mock.patch('timid.context.Context', return_value='ctxt')
    @mock.patch('timid.extensions.ExtensionSet.activate',
                return_value=mock.Mock(**{
                    'finalize.side_effect': lambda c, r: r,
                }))
    @mock.patch('traceback.print_exc')
    def test_debug(self, mock_print_exc, mock_activate, mock_Context):
        ctxt = mock_Context.return_value
        exts = mock_activate.return_value
        args = mock.Mock(directory='directory', debug=True)

        gen = main._processor(args)
        gen.next()

        self.assertEqual(args.ctxt, ctxt)
        self.assertEqual(args.exts, exts)
        self.assertFalse(mock_print_exc.called)
        self.assertFalse(exts.finalize.called)

        result = gen.send(None)

        self.assertEqual(result, None)
        self.assertFalse(mock_print_exc.called)
        exts.finalize.assert_called_once_with(ctxt, None)

    @mock.patch('timid.context.Context', return_value='ctxt')
    @mock.patch('timid.extensions.ExtensionSet.activate',
                return_value=mock.Mock(**{
                    'finalize.return_value': 'alt result',
                }))
    @mock.patch('traceback.print_exc')
    def test_change_result(self, mock_print_exc, mock_activate, mock_Context):
        ctxt = mock_Context.return_value
        exts = mock_activate.return_value
        args = mock.Mock(directory='directory', debug=False)

        gen = main._processor(args)
        gen.next()

        self.assertEqual(args.ctxt, ctxt)
        self.assertEqual(args.exts, exts)
        self.assertFalse(mock_print_exc.called)
        self.assertFalse(exts.finalize.called)

        result = gen.send(None)

        self.assertEqual(result, 'alt result')
        self.assertFalse(mock_print_exc.called)
        exts.finalize.assert_called_once_with(ctxt, None)

    @mock.patch('timid.context.Context', return_value='ctxt')
    @mock.patch('timid.extensions.ExtensionSet.activate',
                return_value=mock.Mock(**{
                    'finalize.side_effect': lambda c, r: r,
                }))
    @mock.patch('traceback.print_exc')
    def test_exception(self, mock_print_exc, mock_activate, mock_Context):
        ctxt = mock_Context.return_value
        exts = mock_activate.return_value
        args = mock.Mock(directory='directory', debug=False)

        gen = main._processor(args)
        gen.next()

        self.assertEqual(args.ctxt, ctxt)
        self.assertEqual(args.exts, exts)
        self.assertFalse(mock_print_exc.called)
        self.assertFalse(exts.finalize.called)

        exc = TestingException('test failure')
        result = gen.throw(exc)

        self.assertEqual(result, 'test failure')
        self.assertFalse(mock_print_exc.called)
        exts.finalize.assert_called_once_with(ctxt, exc)

    @mock.patch('timid.context.Context', return_value='ctxt')
    @mock.patch('timid.extensions.ExtensionSet.activate',
                return_value=mock.Mock(**{
                    'finalize.side_effect': lambda c, r: r,
                }))
    @mock.patch('traceback.print_exc')
    def test_exception_debug(self, mock_print_exc, mock_activate,
                             mock_Context):
        ctxt = mock_Context.return_value
        exts = mock_activate.return_value
        args = mock.Mock(directory='directory', debug=True)

        gen = main._processor(args)
        gen.next()

        self.assertEqual(args.ctxt, ctxt)
        self.assertEqual(args.exts, exts)
        self.assertFalse(mock_print_exc.called)
        self.assertFalse(exts.finalize.called)

        exc = TestingException('test failure')
        result = gen.throw(exc)

        self.assertEqual(result, 'test failure')
        mock_print_exc.assert_called_once_with(file=sys.stderr)
        exts.finalize.assert_called_once_with(ctxt, exc)
