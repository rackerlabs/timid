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

import os
import sys
import traceback

import cli_tools

from timid import context
from timid import extensions
from timid import steps


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
    '--debug', '-d',
    action='store_true',
    default=False,
    help='Enable debugging.',
)
def timid(ctxt, test, key=None, check=False, exts=None, debug=False):
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
    :param debug: Controls debugging output.  Defaults to ``False``.
    """

    # Normalize the extension set
    if exts is None:
        exts = extensions.ExtensionSet()

    # Begin by reading the steps and adding them to the list in the
    # context (which may already have elements thanks to the
    # extensions)
    if debug:
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
        print('[Step %d]: %s . . . ' % (idx, step.name), end='')

        # Run through extension hooks
        if exts.pre_step(ctxt, step, idx):
            print(steps.states[steps.SKIPPED])
            continue

        # Now execute the step
        result = step(ctxt)

        # Let the extensions process the result of the step
        exts.post_step(ctxt, step, idx, result)

        # Emit the result
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
    args.ctxt = context.Context(args.directory)

    # Now set up the extension set
    args.exts = extensions.ExtensionSet.activate(args.ctxt, args)

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
