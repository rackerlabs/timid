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

from timid import steps


class ConditionalModifier(steps.Modifier):
    """
    A modifier that controls whether an action should be performed.
    The base usage is::

        - action: config
          when: branch == "master"

    Here the action will only be performed if the variable "branch" is
    set to the value "master".  The configuration for "when" is a
    simple string containing a Jinja2-parsable expression that will be
    evaluated.
    """

    # Set the priority, restriction, and schema
    priority = 200
    restriction = steps.Modifier.UNRESTRICTED
    schema = {'type': 'string'}

    def __init__(self, ctxt, name, config, step_addr):
        """
        Initialize a ``ConditionalModifier`` instance.

        :param ctxt: The context object.
        :param name: The name of the modifier.
        :param config: The configuration for the modifier.  This may
                       be a scalar value (e.g., "run: command"), a
                       list, or a dictionary.  If the configuration
                       provided is invalid for the action, a
                       ``ConfigError`` should be raised.
        :param step_addr: The address of the step in the test
                          configuration.  Should be passed to the
                          ``ConfigError``.
        """

        # Perform superclass initialization
        super(ConditionalModifier, self).__init__(
            ctxt, name, config, step_addr)

        # Save the condition
        self.condition = ctxt.expression(config)

    def pre_call(self, ctxt, pre_mod, post_mod, action):
        """
        A modifier hook function.  This is called in priority order prior
        to invoking the ``Action`` for the step.  This allows a
        modifier to alter the context, or to take over subsequent
        action invocation.

        :param ctxt: The context object.
        :param pre_mod: A list of the modifiers preceding this
                        modifier in the list of modifiers that is
                        applicable to the action.  This list is in
                        priority order.
        :param post_mod: A list of the modifiers following this
                         modifier in the list of modifiers that is
                         applicable to the action.  This list is in
                         priority order.
        :param action: The action that will be performed.

        :returns: A ``None`` return value indicates that the modifier
                  is taking no action.  A non-``None`` return value
                  should consist of a ``StepResult`` object; this will
                  suspend further ``pre_call()`` processing and
                  proceed to the ``post_call()`` processing.  This
                  implementation returns a ``StepResult`` with state
                  ``SKIPPED`` if the condition does not evaluate to
                  ``True``.
        """

        # Check the condition
        if not self.condition(ctxt):
            return steps.StepResult(state=steps.SKIPPED)

        return None


class IgnoreErrorsModifier(steps.Modifier):
    """
    A modifier that causes an action failure to be ignored.  The base
    usage is::

        - action: config
          ignore-errors: True

    With this configuration, any failures or errors encountered while
    performing the action will be ignored.
    """

    priority = 300
    schema = {'type': 'bool'}

    def post_call(self, ctxt, result, action, post_mod, pre_mod):
        """
        A modifier hook function.  This is called in reverse-priority
        order after invoking the ``Action`` for the step.  This allows
        a modifier to inspect or alter the result of the step.

        :param ctxt: The context object.
        :param result: The result of the action.  This will be a
                       ``StepResult`` object.
        :param action: The action that was performed.
        :param post_mod: A list of modifiers following this modifier
                         in the list of modifiers that is applicable
                         to the action.  This list is in priority
                         order.
        :param pre_mod: A list of modifiers preceding this modifier in
                        the list of modifiers that is applicable to
                        the action.  This list is in priority order.

        :returns: The result for the action, optionally modified.  If
                  the result is not modified, ``result`` must be
                  returned unchanged.  This implementation alters the
                  ``ignore`` property of the ``result`` object to
                  match the configured value.
        """

        # Set the ignore state
        result.ignore = self.config

        return result
