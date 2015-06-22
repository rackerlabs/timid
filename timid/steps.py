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

import abc
import collections
import os
import sys

import six
import yaml

from timid import entry
from timid import utils


NAMESPACE_ACTION = 'timid.actions'
NAMESPACE_MODIFIER = 'timid.modifiers'

# Possible result states
SKIPPED = 0
SUCCESS = 1
FAILURE = 2
ERROR = 3
states = ['SKIPPED', 'SUCCESS', 'FAILURE', 'ERROR']


class ConfigError(Exception):
    """
    Report a configuration error.
    """

    def __init__(self, msg, step_addr=None):
        """
        Initialize a ``ConfigError`` exception.

        :param msg: A message describing the configuration error.
        :param step_addr: The address of the step in the test
                          configuration.
        """

        # Add the step index to the message
        if step_addr is not None:
            msg += ' (%s)' % step_addr

        # Initialize the exception
        super(ConfigError, self).__init__(msg)

        # Save the step index
        self.step_addr = step_addr


class StepAddress(object):
    """
    The "address" of a step.
    """

    def __init__(self, fname, idx, key=None):
        """
        Initialize a ``StepAddress`` instance.

        :param fname: The file name of the YAML file.
        :param idx: The index of the step within the file, or within
                    the designated key of the file.
        :param key: A key within the file.  If the file consists of a
                    single list, this should be ``None`` (the
                    default).
        """

        self.fname = fname
        self.idx = idx
        self.key = key

        # Cache for the string representation
        self._str = None

    def __str__(self):
        """
        Retrieve a string representation for the address.

        :returns: The string representation.
        """

        # Build the string if necessary...
        if self._str is None:
            if self.key is None:
                self._str = '%s step %d' % (self.fname, self.idx + 1)
            else:
                self._str = '%s[%s] step %d' % (self.fname, self.key,
                                                self.idx + 1)

        return self._str


@six.add_metaclass(abc.ABCMeta)
class StepPart(object):
    """
    A superclass for actions and modifiers that contains common
    pieces, such as config validation.
    """

    def __init__(self, ctxt, name, config, step_addr):
        """
        Initialize the action or modifier.  This should process and store
        the configuration provided.

        :param ctxt: The context object.
        :param name: The name.
        :param config: The configuration.  This may be a scalar value
                       (e.g., "run: command"), a list, or a
                       dictionary.  If the configuration provided is
                       invalid, a ``ConfigError`` should be raised.
        :param step_addr: The address of the step in the test
                          configuration.  Should be passed to the
                          ``ConfigError``.
        """

        # Validate the configuration
        self.validate_conf(name, config, step_addr)

        # Store the name and base configuration
        self.name = name
        self.config = config
        self.step_addr = step_addr

    def validate_conf(self, name, config, step_addr):
        """
        Use JSONSchema validation to validate the configuration.
        Validation errors will be reported by raising ConfigError.

        :param name: The name of the action or modifier.
        :param config: The actual configuration.
        :param step_addr: The address of the step in the test
                          configuration.
        """

        utils.schema_validate(config, self.schema, ConfigError, name,
                              step_addr=step_addr)

    @abc.abstractproperty
    def schema(self):
        """
        A JSONSchema.  This is used in validating the configuration.
        """

        pass  # pragma: no cover


class Action(StepPart):
    """
    A step *action*.  Actions are responsible for the actual operation
    performed by the test step.  Each step must have exactly one
    action.
    """

    # Specify as True to designate a "step" action, an action which
    # should be executed during step parsing, and which returns a list
    # of steps
    step_action = False

    @abc.abstractmethod
    def __call__(self, ctxt):
        """
        Invoke the action.  This should perform the actual step.  Note
        that it is possible, given some modifiers, that this method
        may be called any number of times (including 0 times) with
        slightly modified contexts.

        :param ctxt: The context object.

        :returns: A ``StepResult`` object, or if the ``step_action``
                  class attribute is ``True``, a list of zero or more
                  ``Step`` objects.
        """

        pass  # pragma: no cover


class Modifier(StepPart):
    """
    A step *modifier*.  Modifiers modify a step in some fashion, such
    as through repetition or applying a condition.
    """

    # Value for "restriction" to indicate a modifier compatible only
    # with "normal" actions, that is, actions that are not step
    # actions.
    NORMAL = 0x01

    # Value for "restriction" to indicate a modifier compatible only
    # with step actions.
    STEP = 0x02

    # Value for "restriction" to indicate a modifier compatible with
    # either normal or step actions.
    UNRESTRICTED = NORMAL | STEP

    # Specify one of the above restriction values to control which
    # actions the modifier is compatible with.
    restriction = NORMAL

    def action_conf(self, ctxt, action_class, action_name, config, step_addr):
        """
        A modifier hook function.  This is called in priority order prior
        to initializing the ``Action`` for the step.  This allows a
        modifier to alter the configuration to be fed to the action.

        :param ctxt: The context object.
        :param action_class: The ``Action`` subclass the modifier is
                             modifying.  This method should not
                             attempt to initialize the action.
        :param action_name: The name of the action.
        :param config: The configuration for the action.  This may be
                       a scalar value (e.g., "run: command"), a list,
                       or a dictionary.  If the configuration provided
                       is invalid for the action, a ``ConfigError``
                       should be raised.
        :param step_addr: The address of the step in the test
                          configuration.  Should be passed to the
                          ``ConfigError``.

        :returns: The configuration for the action, optionally
                  modified.  If the configuration is not modified,
                  ``config`` must be returned unchanged.  The default
                  implementation of this method does so.
        """

        return config

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
                  proceed to the ``post_call()`` processing.  The
                  default implementation of this method returns
                  ``None``.
        """

        return None

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
                  returned unchanged.  The default implementation of
                  this method does so.
        """

        return result

    @abc.abstractproperty
    def priority(self):
        """
        An integer value.  This provides a primitive means of controlling
        the order of application of modifiers.  The higher the number,
        the later the modifier will be applied.  The action has a
        priority equivalent to positive infinity.

        This must be a class attribute, not a property.
        """

        pass  # pragma: no cover


class StepItem(object):
    """
    A helper class to represent a step item, either an action or a
    modifier.  This is only used during step parsing.
    """

    def __init__(self, cls, name, conf):
        """
        Initialize a ``StepItem`` instance.

        :param cls: The class implementing the action or modifier.
        :param name: The name of the action or modifier.
        :param conf: The configuration for the action or modifier.
        """

        self.cls = cls
        self.name = name
        self.conf = conf

    def init(self, ctxt, step_addr):
        """
        Initialize the item.  This calls the class constructor with the
        appropriate arguments and returns the initialized object.

        :param ctxt: The context object.
        :param step_addr: The address of the step in the test
                          configuration.
        """

        return self.cls(ctxt, self.name, self.conf, step_addr)


class Step(object):
    """
    Represents a test step.
    """

    schemas = {
        'name': {'type': 'string'},
        'description': {'type': 'string'},
    }

    @classmethod
    def parse_file(cls, ctxt, fname, key=None, step_addr=None):
        """
        Parse a YAML file containing test steps.

        :param ctxt: The context object.
        :param fname: The name of the file to parse.
        :param key: An optional dictionary key.  If specified, the
                    file must be a YAML dictionary, and the referenced
                    value will be interpreted as a list of steps.  If
                    not provided, the file must be a YAML list, which
                    will be interpreted as the list of steps.
        :param step_addr: The address of the step in the test
                          configuration.  This may be used in the case
                          of includes, for instance.

        :returns: A list of ``Step`` objects.
        """

        # Load the YAML file
        try:
            with open(fname) as f:
                step_data = yaml.load(f)
        except Exception as exc:
            raise ConfigError(
                'Failed to read file "%s": %s' % (fname, exc),
                step_addr,
            )

        # Do we have a key?
        if key is not None:
            if (not isinstance(step_data, collections.Mapping) or
                    key not in step_data):
                raise ConfigError(
                    'Bad step configuration file "%s": expecting dictionary '
                    'with key "%s"' % (fname, key),
                    step_addr,
                )

            # Extract just the step data
            step_data = step_data[key]

        # Validate that it's a sequence
        if not isinstance(step_data, collections.Sequence):
            addr = ('%s[%s]' % (fname, key)) if key is not None else fname
            raise ConfigError(
                'Bad step configuration sequence at %s: expecting list, '
                'not "%s"' % (addr, step_data.__class__.__name__),
                step_addr,
            )

        # OK, assemble the step list and return it
        steps = []
        for idx, step_conf in enumerate(step_data):
            steps.extend(cls.parse_step(
                ctxt, StepAddress(fname, idx, key), step_conf))

        return steps

    @classmethod
    def parse_step(cls, ctxt, step_addr, step_conf):
        """
        Parse a step dictionary.

        :param ctxt: The context object.
        :param step_addr: The address of the step in the test
                          configuration.
        :param step_conf: The description of the step.  This may be a
                          scalar string or a dictionary.

        :returns: A list of steps.
        """

        # Make sure the step makes sense
        if isinstance(step_conf, six.string_types):
            # Convert string to a dict for uniformity of processing
            step_conf = {step_conf: None}
        elif not isinstance(step_conf, collections.Mapping):
            raise ConfigError(
                'Unable to parse step configuration: expecting string or '
                'dictionary, not "%s"' % step_conf.__class__.__name__,
                step_addr,
            )

        # Parse the configuration into the action and modifier classes
        # and the configuration to apply to each
        action_item = None
        mod_items = {}
        kwargs = {}  # extra args for Step.__init__()
        for key, key_conf in step_conf.items():
            # Handle special keys first
            if key in cls.schemas:
                # Validate the key
                utils.schema_validate(key_conf, cls.schemas[key], ConfigError,
                                      key, step_addr=step_addr)

                # Save the value
                kwargs[key] = key_conf

            # Is it an action?
            elif key in entry.points[NAMESPACE_ACTION]:
                if action_item is not None:
                    raise ConfigError(
                        'Bad step configuration: action "%s" specified, '
                        'but action "%s" already processed' %
                        (key, action_item.name),
                        step_addr,
                    )

                action_item = StepItem(
                    entry.points[NAMESPACE_ACTION][key], key, key_conf)

            # OK, is it a modifier?
            elif key in entry.points[NAMESPACE_MODIFIER]:
                mod_class = entry.points[NAMESPACE_MODIFIER][key]

                # Store it in priority order
                mod_items.setdefault(mod_class.priority, [])
                mod_items[mod_class.priority].append(StepItem(
                    mod_class, key, key_conf))

            # Couldn't resolve it
            else:
                raise ConfigError(
                    'Bad step configuration: unable to resolve action '
                    '"%s"' % key,
                    step_addr,
                )

        # Make sure we have an action
        if action_item is None:
            raise ConfigError(
                'Bad step configuration: no action specified',
                step_addr,
            )

        # What is the action type?
        action_type = (Modifier.STEP if action_item.cls.step_action
                       else Modifier.NORMAL)

        # OK, build our modifiers list and preprocess the action
        # configuration
        modifiers = []
        for mod_item in utils.iter_prio_dict(mod_items):
            # Verify that the modifier is compatible with the
            # action
            if mod_item.cls.restriction & action_type == 0:
                raise ConfigError(
                    'Bad step configuration: modifier "%s" is '
                    'incompatible with the action "%s"' %
                    (mod_item.name, action_item.name),
                    step_addr,
                )

            # Initialize the modifier
            modifier = mod_item.init(ctxt, step_addr)

            # Add it to the list of modifiers
            modifiers.append(modifier)

            # Apply the modifier's configuration processing
            action_item.conf = modifier.action_conf(
                ctxt, action_item.cls, action_item.name, action_item.conf,
                step_addr)

        # Now we can initialize the action
        action = action_item.init(ctxt, step_addr)

        # Create the step
        step = cls(step_addr, action, modifiers, **kwargs)

        # If the final_action is a StepAction, invoke it now and
        # return the list of steps.  We do this after creating the
        # Step object so that we can take advantage of its handling of
        # modifiers.
        if action_item.cls.step_action:
            return step(ctxt)

        # Not a step action, return the step as a list of one element
        return [step]

    def __init__(self, step_addr, action, modifiers=None, name=None,
                 description=None):
        """
        Initialize a ``Step`` instance.

        :param step_addr: The address of the step in the test
                          configuration.
        :param action: An ``Action`` instance.
        :param modifiers: A list of ``Modifier`` instances, in the
                          order in which processing should be
                          performed.  Optional.
        :param name: A name for the step.  Optional.
        :param description: A description of the step.  Optional.
        """

        self.step_addr = step_addr
        self.action = action
        self.modifiers = modifiers or []
        self.name = name or action.__class__.__name__
        self.description = description

    def __call__(self, ctxt):
        """
        Invoke the step.

        :param ctxt: The context object.

        :returns: A ``StepResult`` object, or if the action is a step
                  action, a list of zero or more ``Step`` objects.
        """

        # Begin by walking the modifiers
        i = -1
        for i in six.moves.range(len(self.modifiers)):
            result = self.modifiers[i].pre_call(
                ctxt, self.modifiers[:i], self.modifiers[i + 1:], self.action)

            # Did a modifier return a result?
            if result is not None:
                break
        else:
            # All modifiers have weighed in without returning a
            # result, so let's call the action
            try:
                result = self.action(ctxt)
            except Exception:
                # Wrap the exception in a StepResult instance
                result = StepResult(exc_info=sys.exc_info())
            else:
                # Convert a None into an error StepResult
                if result is None:
                    result = StepResult(status=ERROR)

        # Now walk the modifiers in reverse order for result
        # processing
        for j in six.moves.range(i, -1, -1):
            result = self.modifiers[j].post_call(
                ctxt, result, self.action, self.modifiers[j + 1:],
                self.modifiers[:j])

        return result


class StepResult(object):
    """
    Represent the result(s) of an action.
    """

    def __init__(self, state=None, msg=None, ignore=None,
                 returncode=None, exc_info=None, results=None):
        """
        Initialize a ``StepResult`` instance.

        :param state: One of the possible result states.  If not
                      provided, its value will be inferred from the
                      other arguments.
        :param msg: A message giving more detail regarding the result.
        :param ignore: Whether to ignore errors.  A ``True`` will
                       ignore an error condition.  Defaults to
                       ``False``.
        :param returncode: The return code of an external process.  If
                           provided, ``state`` is inferred to be
                           SUCCESS or FAILURE based on whether the
                           value is zero or non-zero, respectively.
        :param exc_info: Exception information.  If provided,
                         ``state`` is inferred to be ERROR.
        :param results: Used when the ``StepResult`` is encapsulating
                        a list of other ``StepResult`` instances.
        """

        # Save the result message
        self.msg = msg

        # If an exception was recorded, store it and default the state
        # appropriately
        self.exc_info = exc_info
        if exc_info is not None and state is None:
            state = ERROR

        # If the return code was provided, default the state
        # appropriately
        self.returncode = returncode
        if returncode is not None and state is None:
            state = SUCCESS if returncode == 0 else FAILURE

        # If a list of instances was provided, default the state
        # appropriately
        self.results = results or []
        if results is not None:
            if state is None:
                state = max(r.state for r in results)
            if ignore is None:
                ignore = any(r.ignore for r in results)

        # Save the error state
        self.state = state

        # Track whether we're ignoring the error
        self._ignore = ignore

    def __bool__(self):
        """
        Cast the ``StepResult`` instance to boolean.  It tests as
        equivalent to ``True`` if the state is "skipped" or "success",
        and ``False`` if the state is "error" or "failure".

        :returns: A boolean value indicating if the result succeeded
                  or failed.
        """

        return self._ignore or self.state in (SKIPPED, SUCCESS)
    __nonzero__ = __bool__

    @property
    def ignore(self):
        """
        Determine whether an error result should be ignored.
        """

        return self._ignore or False

    @ignore.setter
    def ignore(self, value):
        """
        Update the ignore state if it hasn't been set yet.
        """

        if self._ignore is None:
            self._ignore = value


class SensitiveDictAction(Action):
    """
    An abstract action for updating a ``SensitiveDict`` instance.  The
    base usage is::

        - name:
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

    # Schema for validating the configuration
    schema = {
        'type': 'object',
        'properties': {
            'set': {'type': 'object'},
            'unset': {
                'type': 'array',
                'items': {'type': 'string'},
            },
            'sensitive': {
                'type': 'array',
                'items': {'type': 'string'},
            },
            'files': {
                'type': 'array',
                'items': {'type': 'string'},
            },
        },
        'additionalProperties': False,
    }

    def __init__(self, ctxt, name, config, step_addr):
        """
        Initialize a ``SensitiveDictAction`` instance.

        :param ctxt: The context object.
        :param name: The name of the action.
        :param config: The configuration for the action.  This may be
                       a scalar value (e.g., "run: command"), a list,
                       or a dictionary.  If the configuration provided
                       is invalid for the action, a ``ConfigError``
                       should be raised.
        :param step_addr: The address of the step in the test
                          configuration.  Should be passed to the
                          ``ConfigError``.
        """

        # Perform superclass initialization
        super(SensitiveDictAction, self).__init__(
            ctxt, name, config, step_addr)

        # Set up the 'set' portion
        self.set_vars = {}
        for key, value in config.get('set', {}).items():
            self.set_vars[key] = ctxt.template(value)

        # Now do the unset and sensitive sets
        self.unset_vars = set(config.get('unset', []))
        self.sensitive_vars = set(config.get('sensitive', []))
        self.files = [ctxt.template(fn) for fn in config.get('files', [])]

        # Save the directory of the file the action is in for relative
        # interpretation
        self.dirname = os.path.dirname(step_addr.fname) or os.curdir

    def __call__(self, ctxt):
        """
        Invoke the action.  This updates the appropriate ``SensitiveDict``
        instance from the context as specified in the configuration.

        :param ctxt: The context object.

        :returns: A ``StepResult`` object.
        """

        # First, select the correct context attribute
        sensitive_dict = getattr(ctxt, self.context_attr)

        # Next, read in the files in order
        for ftmpl in self.files:
            fpath = utils.canonicalize_path(self.dirname, ftmpl(ctxt))
            try:
                with open(fpath) as f:
                    var_data = yaml.load(f)
            except Exception as exc:
                # Ignore missing variable files
                continue

            # Make sure the contents are a dictionary
            if not isinstance(var_data, collections.Mapping):
                continue

            # Update the dictionary
            sensitive_dict.update(var_data)

        # Now, apply the sensitive and unset changes
        for var in self.sensitive_vars:
            sensitive_dict.declare_sensitive(var)
        for var in self.unset_vars:
            sensitive_dict.pop(var, None)

        # Finally, apply the sets
        for var, tmpl in self.set_vars.items():
            sensitive_dict[var] = tmpl(ctxt)

        # We're done!
        return StepResult(state=SUCCESS)

    @abc.abstractproperty
    def context_attr(self):
        """
        The name of an attribute of the context containing the
        ``SensitiveDict`` instance that should be acted upon by this
        action.
        """

        pass  # pragma: no cover


class IncludeAction(Action):
    """
    An action that includes steps from another file.  The base usage
    is::

        - include: filename.yaml

    With this syntax, all steps in the "filename.yaml" (which must be
    a YAML list) will be included at the point of the "include"
    action.  Note that the filename is resolved relative to the
    directory of the file containing the "include" action.

    More advanced syntax allows selection of subsets of the steps from
    the referenced file::

        - include:
            path: filename.yaml
            key: special
            start: 2
            stop: 7

    The only required element is the "path" element.  The "key"
    element causes the file to be treated as a YAML mapping, and the
    list contained in the value for the specified key will be
    included.  The "start" and "stop" elements allow selection of a
    subset, and are interpreted as in a Python range syntax; that is,
    for the example above, steps 2, 3, 4, 5, and 6 will be included,
    but not steps 0, 1, 7, etc.
    """

    # This is a special "step" action, an action that returns a list
    # of steps
    step_action = True

    # Schema for validating the configuration
    schema = {
        'type': 'object',
        'properties': {
            'path': {'type': 'string'},
            'key': {'type': 'string'},
            'start': {'type': 'integer'},
            'stop': {'type': 'integer'},
        },
        'additionalProperties': False,
        'required': ['path'],
    }

    def __init__(self, ctxt, name, config, step_addr):
        """
        Initialize an ``IncludeAction`` instance.

        :param ctxt: The context object.
        :param name: The name of the action.
        :param config: The configuration for the action.  This may be
                       a scalar value (e.g., "run: command"), a list,
                       or a dictionary.  If the configuration provided
                       is invalid for the action, a ``ConfigError``
                       should be raised.
        :param step_addr: The address of the step in the test
                          configuration.  Should be passed to the
                          ``ConfigError``.
        """

        # Convert bare strings intelligently
        if isinstance(config, six.string_types):
            config = {'path': config}

        # Perform superclass initialization
        super(IncludeAction, self).__init__(ctxt, name, config, step_addr)

        # Extract the appropriate values
        self.path = ctxt.template(config['path'])
        self.key = ctxt.template(config.get('key'))
        self.start = config.get('start')
        self.stop = config.get('stop')

        # Save the directory of the file the include is in for
        # relative interpretation
        self.dirname = os.path.dirname(step_addr.fname) or os.curdir

    def __call__(self, ctxt):
        """
        Invoke the action.  This reads and interprets the referenced steps
        file.

        :param ctxt: The context object.

        :returns: A list of zero or more ``Step`` objects.
        """

        # Interpret the path
        path = utils.canonicalize_path(self.dirname, self.path(ctxt))

        # Import the desired steps
        steps = Step.parse_file(
            ctxt, path, self.key(ctxt), self.step_addr)

        # Narrow the steps, if desired
        if self.start is not None or self.stop is not None:
            return steps[self.start:self.stop]

        return steps
