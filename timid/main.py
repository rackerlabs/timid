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

from __future__ import print_function

import argparse
import os
import sys
import traceback

import cli_tools
import six

from timid import context
from timid import extensions
from timid import steps


class DictAction(argparse.Action):
    """
    An ``argparse.Action`` subclass used for command line arguments
    that are used to designate a key and its corresponding value for a
    dictionary.
    """

    # Mapping between types and conversion functions
    _types = {
        'str': six.text_type,
        'string': six.text_type,
        'int': int,
        'integer': int,
        'bool': lambda x: x.lower() == 'true',
        'boolean': lambda x: x.lower() == 'true',
    }

    def __init__(self, option_strings, dest, **kwargs):
        """
        Initialize a ``DictAction`` object.

        :param option_strings: A list of option strings.
        :param dest: The target attribute to store the option values
                     in.
        :param allow_type: A boolean indicating whether the value type
                           may be designated.  If ``False``, the value
                           type is always treated as a string.
        """

        # Figure out whether to allow a type designation
        allow_type = kwargs.pop('allow_type', False)

        # Initialize the Action
        super(DictAction, self).__init__(option_strings, dest, **kwargs)

        # Save the information about allowing type designations
        self.allow_type = allow_type

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Called when encountering an argument bound to the ``DictAction``
        object.

        :param parser: An ``argparse.ArgumentParser`` object.
        :param namespace: The ``argparse.Namespace`` into which to
                          store argument values.
        :param values: The values that were passed for the argument.
        :param option_string: The string used to invoke the option.
        """

        # Get the dictionary out of the namespace
        argdict = getattr(namespace, self.dest, {})
        setattr(namespace, self.dest, argdict)

        # Now parse the values
        type_ = six.text_type
        key, _eq, value = values.partition('=')
        if self.allow_type and ':' in key:
            type_str, _colon, key = key.partition(':')
            if type_str not in self._types:
                parser.error('Unrecognized value type "%s"' % type_str)
            type_ = self._types[type_str]

        # Store the value in the dictionary
        argdict[key] = type_(value)


@cli_tools.argument(
    'test',
    help='Description of the test to run.  This should be the path to a '
    'YAML file, e.g. "test1.yaml".',
)
@cli_tools.argument(
    'directory',
    nargs='?',
    help='The directory to execute the tests from.  Defaults to '
    '"%(default)s".  Note that this does *not* affect the interpretation '
    'of the location of the test file.',
)
@cli_tools.argument(
    '--key', '-k',
    help='An optional key within the test file.  When provided, the test '
    'file is expected to contain a dictionary of lists of steps, instead '
    'of a flat list of steps.',
)
@cli_tools.argument(
    '--check', '-K',
    default=False,
    action='store_true',
    help='Syntax check the test steps specified.',
)
@cli_tools.argument(
    '--variable', '-V',
    dest='variables',
    action=DictAction,
    default={},
    help='Specify the value of a variable.  Variables are specified as '
    '"key=value".  The value type may be specified by prefixing the key '
    'name with the type name, followed by a ":", e.g., "bool:var=true".  '
    'Recognized types are: "str", "string", "int", "integer", "bool", and '
    '"boolean".  For boolean values, only "true" (in any case) is recognized '
    'as a true value; all other values map to a false value.',
    allow_type=True,
)
@cli_tools.argument(
    '--environment', '-e',
    action=DictAction,
    default={},
    help='Specify the value of an environment variable.  This overrides any '
    'variable of the same name present in the current environment.',
)
@cli_tools.argument(
    '--verbose', '-v',
    action='count',
    default=1,
    help='Increase verbosity.',
)
@cli_tools.argument(
    '--quiet', '-q',
    dest='verbose',
    action='store_const',
    const=0,
    help='Decrease verbosity to its minimum.',
)
@cli_tools.argument(
    '--debug', '-d',
    action='store_true',
    default=False,
    help='Enable debugging.',
)
def timid(ctxt, test, key=None, check=False, exts=None):
    """
    Execute a test described by a YAML file.

    :param ctxt: A ``timid.context.Context`` object.
    :param test: The name of a YAML file containing the test
                 description.  Note that the current working directory
                 set up in ``ctxt.environment`` does not affect the
                 resolution of this file.
    :param key: An optional key into the test description file.  If
                not ``None``, the file named by ``test`` must be a
                YAML dictionary of lists of steps; otherwise, it must
                be a simple list of steps.
    :param check: If ``True``, only performs a syntax check of the
                  test steps indicated by ``test`` and ``key``; the
                  test itself is not run.
    :param exts: An instance of ``timid.extensions.ExtensionSet``
                 describing the extensions to be called while
                 processing the test steps.
    """

    # Normalize the extension set
    if exts is None:
        exts = extensions.ExtensionSet()

    # Begin by reading the steps and adding them to the list in the
    # context (which may already have elements thanks to the
    # extensions)
    if ctxt.debug:
        print('Reading test steps from %s%s...' %
              (test, '[%s]' % key if key else ''), file=sys.stderr)
    ctxt.steps += exts.read_steps(ctxt, steps.Step.parse_file(ctxt, test, key))

    # If all we were supposed to do was check, well, we've
    # accomplished that...
    if check:
        return None

    # Now we execute each step in turn
    for idx, step in enumerate(ctxt.steps):
        # Emit information about what we're doing
        if ctxt.verbose >= 1:
            print('[Step %d]: %s . . . ' % (idx, step.name), end='')
        sys.stdout.flush()

        # Run through extension hooks
        if exts.pre_step(ctxt, step, idx):
            print(steps.states[steps.SKIPPED])
            continue

        # Now execute the step
        result = step(ctxt)

        # Let the extensions process the result of the step
        exts.post_step(ctxt, step, idx, result)

        # Emit the result
        if ctxt.verbose >= 1:
            print('%s%s' % (steps.states[result.state],
                            ' (ignored)' if result.ignore else ''))

        # Was the step a success?
        if not result:
            msg = 'Test step failure'
            if result.msg:
                msg += ': %s' % result.msg

            return msg

    # All done!  And a success, to boot...
    return None


@timid.args_hook
def _args(parser):
    """
    A ``cli_tools`` argument hook function that allows extensions to
    attach extra command line arguments to the argument parser built
    for executing ``timid``.

    :param parser: The ``argparse.ArgumentParser`` instance containing
                   the command line arguments recognized by ``timid``.
    """

    # Give the extensions the opportunity to add command line options
    extensions.ExtensionSet.prepare(parser)


@timid.processor
def _processor(args):
    """
    A ``cli_tools`` processor function that interfaces between the
    command line and the ``timid()`` function.  This function is
    responsible for allocating a ``timid.context.Context`` object and
    initializing the activated extensions, and for calling those
    extensions' ``finalize()`` method.

    :param args: The ``argparse.Namespace`` object containing the
                 results of argument processing.
    """

    # Begin by initializing a context
    args.ctxt = context.Context(args.verbose, args.debug, args.directory)

    # Now set up the extension set
    args.exts = extensions.ExtensionSet.activate(args.ctxt, args)

    # Update the environment and the variables
    args.ctxt.environment.update(args.environment)
    args.ctxt.variables.update(args.variables)

    # Call the actual timid() function
    try:
        result = yield

    # If an exception occurred, give the extensions an opportunity to
    # handle it
    except Exception as exc:
        if args.debug:
            # Make sure we emit a proper traceback
            traceback.print_exc(file=sys.stderr)

        # The exception is the result, from the point of view of the
        # extensions
        result = exc

    # Allow the extensions to handle the result
    result = args.exts.finalize(args.ctxt, result)

    # If the final result is an exception, convert it to a string for
    # yielding back to cli_tools
    if isinstance(result, Exception):
        result = str(result)

    yield result
