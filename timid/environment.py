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
import shlex
import subprocess

import six

from timid import steps
from timid import utils


@six.add_metaclass(abc.ABCMeta)
class SpecialVariable(object):
    """
    A mix-in class for "special" environment variables.  These are
    variables which can be represented as lists or sets.
    """

    def __init__(self, env, var, sep=os.pathsep, value=utils.unset):
        """
        Initialize a ``SpecialVariable`` instance.

        :param env: The ``Environment`` containing the variable.
        :param var: The name of the environment variable.
        :param sep: The separator used.  Defaults to the value of
                    ``os.pathsep``.
        """

        # Save the basic data we need to function
        self._env = env
        self._var = var
        self._sep = sep

        # Select the current value
        if value is utils.unset:
            value = env._data.get(var)

        # Set up the value cache
        self._update(value)

    def __str__(self):
        """
        Obtain a string form of the ``EnvListVariable`` instance.

        :returns: The string form of the variable.
        """

        return self._env._data.get(self._var) or ''

    def __repr__(self):
        """
        Obtain a representation of the ``EnvListVariable`` instance.

        :returns: A representation of the variable.
        """

        return repr(self._value)

    def __len__(self):
        """
        Obtain the length of an ``EnvListVariable`` instance.

        :returns: The number of elements in the variable.
        """

        return len(self._value)

    def _rebuild(self):
        """
        Helper method used to alter the variable's value in a linked
        ``Environment`` instance when a change is made to the
        ``SpecialVariable`` instance.
        """

        self._env._data[self._var] = self._sep.join(self._value)

    def _update(self, value):
        """
        Alert method used when the variable's value in an ``Environment``
        instance has been altered.

        :param value: The new value to set the value to.
        """

        if not value:
            # Empty string or None, so use the empty value
            value = self._coerce()
        elif isinstance(value, six.string_types):
            # It's a string, so split and coerce to the right type
            value = self._coerce(value.split(self._sep))
        else:
            # It's already a compatible type, so just coerce it
            value = self._coerce(value)

        # Set the value
        self._value = value

    @abc.abstractproperty
    def _type(self):
        """
        The abstract type the value should be represented as, e.g.,
        ``collections.Set`` or ``collections.Sequence``.
        """

        pass  # pragma: no cover

    @abc.abstractproperty
    def _coerce(self):
        """
        The underlying type the value should be represented as, e.g.,
        ``set`` or ``list``.  Used to convert a value into the
        appropriate type.
        """

        pass  # pragma: no cover


class ListVariable(SpecialVariable, collections.MutableSequence):
    """
    Represent the value of an environment variable which is list form.
    This is used for representing the PATH environment variable, and
    may be used for other similar variables as well.
    """

    _type = collections.Sequence
    _coerce = list

    def __getitem__(self, idx):
        """
        Retrieve an item from a ``ListVariable`` instance.

        :param idx: The index or index-like object (e.g., slice) to
                    retrieve.

        :returns: The value at the designated index.
        """

        return self._value[idx]

    def __setitem__(self, idx, value):
        """
        Set an item on the ``ListVariable`` instance.

        :param idx: The index or index-like object (e.g., slice) to
                    set.
        :param value: The value to set it to.
        """

        self._value[idx] = value
        self._rebuild()

    def __delitem__(self, idx):
        """
        Delete an item from the ``ListVariable`` instance.

        :param idx: The index or index-like object (e.g., slice) to
                    delete.
        """

        del self._value[idx]
        self._rebuild()

    def insert(self, idx, value):
        """
        Inserts a value in the ``ListVariable`` at an appropriate index.

        :param idx: The index before which to insert the new value.
        :param value: The value to insert.
        """

        self._value.insert(idx, value)
        self._rebuild()


class SetVariable(SpecialVariable, collections.MutableSet):
    """
    Represent the value of an environment variable which is set form.
    This is used for representing the TIMID_SENSITIVE environment
    variable, and may be used for other similar variables as well.
    """

    _type = collections.Set
    _coerce = set

    def __contains__(self, item):
        """
        Check if an item is a member of the ``SetVariable`` instance.

        :param item: The item to check.

        :returns: A ``True`` value if the item is a member, ``False``
                  otherwise.
        """

        return item in self._value

    def __iter__(self):
        """
        Iterate over the items in the ``SetVariable`` instance.

        :returns: An iterator over the items.
        """

        return iter(self._value)

    def add(self, item):
        """
        Add a new item to the ``SetVariable`` instance.

        :param item: The item to add.
        """

        self._value.add(item)
        self._rebuild()

    def discard(self, item):
        """
        Discard an item from the ``SetVariable`` instance.

        :param item: The item to discard.
        """

        self._value.discard(item)
        self._rebuild()


class Environment(utils.SensitiveDict):
    """
    Represents a calling environment for a process.  This contains
    environment variables and the working directory that processes
    should be executed with.
    """

    def __init__(self, environ=None, sensitive=None, cwd=None):
        """
        Initialize a new ``Environment`` instance.

        :param environ: An optional dictionary containing the initial
                        set of environment variables.  If omitted,
                        ``os.environ`` will be used.
        :param sensitive: An optional set of "sensitive" variables,
                          environment variables whose values should
                          not be printed out.
        :param cwd: The working directory processes should be executed
                    in.  If not given, the current working directory
                    will be used.  If a relative path, it will be
                    interpreted relative to the current working
                    directory.
        """

        # Select the starting environment
        environ = environ or os.environ.copy()

        # Build the 'sensitive' set
        sensitive_var = SetVariable(self, 'TIMID_SENSITIVE',
                                    value=environ.get('TIMID_SENSITIVE'))
        if sensitive:
            sensitive_var |= sensitive

        # Initialize the SensitiveDict
        super(Environment, self).__init__(environ, sensitive_var)

        # Track special variables
        self._special = {
            'PATH': ListVariable(self, 'PATH'),
            'TIMID_SENSITIVE': sensitive_var,
        }

        # Initialize the working directory
        self._cwd = utils.canonicalize_path(os.getcwd(), cwd or os.curdir)

    def __getitem__(self, name):
        """
        Retrieve the value of a variable from the environment.  If the
        variable has been declared as a list-like variable, the return
        value will be a list of strings; otherwise, it will be a
        string.

        :param name: The name of the variable to retrieve.

        :returns: The value of the designated variable.
        """

        # Raise a KeyError if needed
        if name not in self._data:
            raise KeyError(name)

        # If it's special, return the special instance
        if name in self._special:
            return self._special[name]

        return self._data[name]

    def __setitem__(self, name, value):
        """
        Set the value of a variable in the environment.  If the variable
        has been declared as a list-like variable, an intelligent
        conversion of the value will be performed.

        :param name: The name of the variable to set.
        :param value: The value to set.  Must be a string or, for
                      list-like variables, a sequence.  A ``None``
                      value is interpreted as a delete.
        """

        # Get the special variable, if any
        special = self._special.get(name)

        # Handle the delete case first
        if value is None:
            self._data.pop(name, None)
            if special:
                special._update(None)

        # Is the value a string type?
        elif isinstance(value, six.string_types):
            self._data[name] = value
            if special:
                special._update(value)

        # Is the value a type compatible with a special variable?
        elif (special and
              (isinstance(value, collections.Iterable) or
               isinstance(value, special._type))):
            # Let the special variable handle the change directly
            special._update(value)

            # Rebuild the value into a string
            special._rebuild()

        # Unable to handle the data type
        else:
            raise ValueError('invalid value %r' % value)

    def __delitem__(self, name):
        """
        Delete the value of a variable from the environment.

        :param name: The name of the variable to delete.
        """

        # Will raise the KeyError if the variable doesn't exist
        del self._data[name]

        # Notify special variables
        if name in self._special:
            self._special[name]._update(None)

    def copy(self):
        """
        Retrieve a copy of the Environment.  Note that this is a shallow
        copy.
        """

        return self.__class__(self._data.copy(), self._sensitive.copy(),
                              self._cwd)

    def _declare_special(self, name, sep, klass):
        """
        Declare an environment variable as a special variable.  This can
        be used even if the environment variable is not present.

        :param name: The name of the environment variable that should
                     be considered special.
        :param sep: The separator to be used.
        :param klass: The subclass of ``SpecialVariable`` used to
                      represent the variable.
        """

        # First, has it already been declared?
        if name in self._special:
            special = self._special[name]
            if not isinstance(special, klass) or sep != special._sep:
                raise ValueError('variable %s already declared as %s '
                                 'with separator "%s"' %
                                 (name, special.__class__.__name__,
                                  special._sep))

        # OK, it's new; declare it
        else:
            self._special[name] = klass(self, name, sep)

    def declare_list(self, name, sep=os.pathsep):
        """
        Declare an environment variable as a list-like special variable.
        This can be used even if the environment variable is not
        present.

        :param name: The name of the environment variable that should
                     be considered list-like.
        :param sep: The separator to be used.  Defaults to the value
                    of ``os.pathsep``.
        """

        self._declare_special(name, sep, ListVariable)

    def declare_set(self, name, sep=os.pathsep):
        """
        Declare an environment variable as a set-like special variable.
        This can be used even if the environment variable is not
        present.

        :param name: The name of the environment variable that should
                     be considered set-like.
        :param sep: The separator to be used.  Defaults to the value
                    of ``os.pathsep``.
        """

        self._declare_special(name, sep, SetVariable)

    def call(self, args, **kwargs):
        """
        A thin wrapper around ``subprocess.Popen``.  Takes the same
        options as ``subprocess.Popen``, with the exception of the
        ``cwd``, and ``env`` parameters, which come from the
        ``Environment`` instance.  Note that if the sole positional
        argument is a string, it will be converted into a sequence
        using the ``shlex.split()`` function.
        """

        # Convert string args into a sequence
        if isinstance(args, six.string_types):
            args = shlex.split(args)

        # Substitute cwd and env
        kwargs['cwd'] = self._cwd
        kwargs['env'] = self._data

        # Set a default for close_fds
        kwargs.setdefault('close_fds', True)

        return subprocess.Popen(args, **kwargs)

    @property
    def cwd(self):
        """
        Retrieve the current working directory processes will be executed
        in.
        """

        return self._cwd

    @cwd.setter
    def cwd(self, value):
        """
        Change the working directory that processes should be executed in.

        :param value: The new path to change to.  If relative, will be
                      interpreted relative to the current working
                      directory.
        """

        self._cwd = utils.canonicalize_path(self._cwd, value)


class EnvironmentAction(steps.SensitiveDictAction):
    """
    An action for updating and otherwise modifying the execution
    environment.  The base usage is::

        - env:
            set:
              ENV_VAR: value
            unset:
            - OTHER_VAR
            sensitive:
            - SENS_VAR
            files:
            - fname1.yaml
            - fname2.yaml

    This action would set the environment variable named "ENV_VAR" to
    the value "value", unset the environment variable "OTHER_VAR",
    mark the environment variable "SENS_VAR" as a sensitive variable,
    and read the files "fname1.yaml" and "fname2.yaml" from the
    directory containing the file specifying the action.

    Note that if an environment variable is present under both the
    "set" and "unset" keys, the "set" will take precedence.  Also note
    that variable file reading is performed before any other
    operations.
    """

    # Schema for validating the configuration; this contains tweaks
    # specific to environment variables
    schema = {
        'type': 'object',
        'properties': {
            'set': {
                'type': 'object',
                'additionalProperties': {'type': 'string'},
            },
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

    # The name of the context attribute affected by this action
    context_attr = 'environment'


class DirectoryAction(steps.Action):
    """
    An action for changing the working directory.  The base usage is::

        - chdir: path/to/change/to

    This action would cause a change to the indicated directory,
    relative to the current working directory.
    """

    # Schema for validating the configuration
    schema = {'type': 'string'}

    def __init__(self, ctxt, name, config, step_addr):
        """
        Initialize a ``DirectoryAction`` instance.

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
        super(DirectoryAction, self).__init__(ctxt, name, config, step_addr)

        # Save the directory to switch to
        self.target_dir = ctxt.template(config)

    def __call__(self, ctxt):
        """
        Invoke the action.  This changes to the directory specified by the
        configuration.

        :param ctxt: The context object.

        :returns: A ``StepResult`` object.
        """

        # Change to the target directory
        ctxt.environment.cwd = self.target_dir(ctxt)

        # We're done!
        return steps.StepResult(state=steps.SUCCESS)


class RunAction(steps.Action):
    """
    An action for invoking a shell command.  The base usage is::

        - run: ./command.py arg1 arg2 arg3

    Note that template substitution is performed *before* splitting
    the arguments up into a list.  (This splitting is performed using
    ``shlex.split()``, so shell quoting is honored.)  In particular,
    this means that any given template substitution that renders into
    a string containing spaces may result into multiple arguments
    passed to the command, unless shell quoting is used.  If more
    control over arguments is desired, use the more advanced list
    form::

        - run:
          - ./command.py
          - arg1
          - arg2
          - arg3

    In this form, no shell syntax quoting is honored.
    """

    # Schema for validating the configuration
    schema = {
        'oneOf': [
            {'type': 'string'},
            {
                'type': 'array',
                'items': {'type': 'string'},
            },
        ],
    }

    def __init__(self, ctxt, name, config, step_addr):
        """
        Initialize a ``RunAction`` instance.

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
        super(RunAction, self).__init__(ctxt, name, config, step_addr)

        # Build up the correct command
        if isinstance(config, six.string_types):
            self.command = ctxt.template(config)
        else:
            self.command = [ctxt.template(arg) for arg in config]

    def __call__(self, ctxt):
        """
        Invoke the action.  This executes the command specified in the
        configuration.

        :param ctxt: The context object.

        :returns: A ``StepResult`` object.
        """

        # First, do the correct splitting/rendering
        if isinstance(self.command, list):
            args = [arg(ctxt) for arg in self.command]
        else:
            args = shlex.split(self.command(ctxt))

        # Invoke the command
        subproc = ctxt.environment.call(args)

        # All done...
        return steps.StepResult(returncode=subproc.wait())
