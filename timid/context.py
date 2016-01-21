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

import sys

import jinja2
import six

from timid import environment
from timid import steps
from timid import utils


class Context(object):
    """
    Represent the context for executing a test file.  This contains
    the environment, template variables, test steps, and any other
    data required to execute a test sequence.
    """

    def __init__(self, verbose=1, debug=False, cwd=None):
        """
        Initialize a new ``Context`` instance.
        """

        # Save the verbosity and debugging settings
        self.verbose = verbose
        self.debug = debug

        # Set up the basic variables
        self.variables = utils.SensitiveDict()
        self.environment = environment.Environment(cwd=cwd)

        # The list of test steps
        self.steps = []

        # Set up a Jinja2 environment for substitutions
        self._jinja = jinja2.Environment()
        self._jinja.globals['env'] = self.environment

    def emit(self, msg, level=1, debug=False):
        """
        Emit a message to the user.

        :param msg: The message to emit.  If ``debug`` is ``True``,
                    the message will be emitted to ``stderr`` only if
                    the ``debug`` attribute is ``True``.  If ``debug``
                    is ``False``, the message will be emitted to
                    ``stdout`` under the control of the ``verbose``
                    attribute.
        :param level: Ignored if ``debug`` is ``True``.  The message
                      will only be emitted if the ``verbose``
                      attribute is greater than or equal to the value
                      of this parameter.  Defaults to 1.
        :param debug: If ``True``, marks the message as a debugging
                      message.  The message will only be emitted if
                      the ``debug`` attribute is ``True``.
        """

        # Is it a debug message?
        if debug:
            if not self.debug:
                # Debugging not enabled, don't emit the message
                return
            stream = sys.stderr
        else:
            # Not a debugging message; is verbose high enough?
            if self.verbose < level:
                return
            stream = sys.stdout

        # Emit the message
        print(msg, file=stream)

    def template(self, string):
        """
        Interpret a template string.  This returns a callable taking one
        argument--this context--and returning a string rendered from
        the template.

        :param string: The template string.

        :returns: A callable of one argument that will return the
                  desired string.
        """

        # Short-circuit if the template "string" isn't actually a
        # string
        if not isinstance(string, six.string_types):
            return lambda ctxt: string

        # Create the template and return the callable
        tmpl = self._jinja.from_string(string)
        return lambda ctxt: tmpl.render(ctxt.variables)

    def expression(self, string):
        """
        Interpret an expression string.  This returns a callable taking
        one argument--this context--and returning the result of
        evaluating the expression.

        :param string: The expression.

        :returns: A callable of one argument that will return the
                  desired expression.
        """

        # Short-circuit if the expression "string" isn't actually a
        # string
        if not isinstance(string, six.string_types):
            return lambda ctxt: string

        # Create the expression and return the callable
        expr = self._jinja.compile_expression(string)
        return lambda ctxt: expr(ctxt.variables)


class VariableAction(steps.SensitiveDictAction):
    """
    An action for updating and otherwise modifying the template
    variables.  The base usage is::

        - var:
            set:
              var: value
            unset:
            - other_var
            sensitive:
            - sens_var
            files:
            - fname1.yaml
            - fname2.yaml

    This action would set the variable named "var" to the value
    "value", unset the variable "other_var", mark the variable
    "sens_var" as a sensitive variable, and read the files
    "fname1.yaml" and "fname2.yaml" from the directory containing the
    file specifying the action.

    Note that if a variable is present under both the "set" and
    "unset" keys, the "set" will take precedence.  Also note that
    variable file reading is performed before any other operations.
    """

    # The name of the context attribute affected by this action
    context_attr = 'variables'
