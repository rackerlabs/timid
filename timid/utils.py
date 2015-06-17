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

import collections
import itertools
import os

import jsonschema
import six


# An object to represent an "unset" value
unset = object()


def canonicalize_path(cwd, path):
    """
    Canonicalizes a path relative to a given working directory.  That
    is, the path, if not absolute, is interpreted relative to the
    working directory, then converted to absolute form.

    :param cwd: The working directory.
    :param path: The path to canonicalize.

    :returns: The absolute path.
    """

    if not os.path.isabs(path):
        path = os.path.join(cwd, path)

    return os.path.abspath(path)


class SensitiveDict(collections.MutableMapping):
    """
    A dictionary containing some keys which contain sensitive data.
    """

    # The mask to use
    masking = '<masked {key}>'

    def __init__(self, data=None, sensitive=None):
        """
        Initialize a new ``SensitiveDict`` instance.

        :param data: An optional dictionary containing the data.
        :param sensitive: An optional set of "sensitive" keys, keys
                          whose values should be considered sensitive.
        """

        # Save the data and the sensitive set
        self._data = data or {}
        self._sensitive = sensitive or set()

        # Initialize the demand-allocated 'masked' property
        self._masked = None

    def __str__(self):
        """
        Obtain a string form of a ``SensitiveDict`` instance.

        :returns: The string form of the ``SensitiveDict``.
        """

        return six.text_type(self._data)

    def __len__(self):
        """
        Obtain the length of a ``SensitiveDict`` instance.

        :returns: The number of keys in the dictionary.
        """

        return len(self._data)

    def __getitem__(self, key):
        """
        Retrieve the value of a key.

        :param key: The key to retrieve the value of.

        :returns: The value of the key.
        """

        return self._data[key]

    def __setitem__(self, key, value):
        """
        Set the value of a key.

        :param key: The key to set the value of.
        :param value: The value to set the key to.
        """

        self._data[key] = value

    def __delitem__(self, key):
        """
        Delete the value of a key.

        :param key: The key to delete.
        """

        del self._data[key]

    def __iter__(self):
        """
        Iterate over the dictionary.

        :returns: An iterator over the keys in the dictionary.
        """

        return iter(self._data)

    def copy(self):
        """
        Retrieve a copy of the sensitive dictionary.  Note that this is a
        shallow copy.
        """

        return self.__class__(self._data.copy(), self._sensitive.copy())

    def declare_sensitive(self, key):
        """
        Declare a key as a "sensitive" key, a key for which the data
        should be treated as sensitive.  The key need not be set to be
        declared as sensitive.

        :param key: The key to mark as sensitive.
        """

        self._sensitive.add(key)

    @property
    def sensitive(self):
        """
        Retrieve a set of the "sensitive" keys, keys for which the data
        should be treated as sensitive.  This will be a copy;
        modifications will not affect the set.
        """

        return frozenset(self._sensitive)

    @property
    def masked(self):
        """
        Retrieve a read-only subordinate mapping.  All values are
        stringified, and sensitive values are masked.  The subordinate
        mapping implements the context manager protocol for
        convenience.
        """

        if self._masked is None:
            self._masked = MaskedDict(self)

        return self._masked


class MaskedDict(collections.Mapping):
    """
    A read-only proxy for ``SensitiveDict`` which applies appropriate
    masking.  Implements the context manager protocol for convenience.
    """

    def __init__(self, parent):
        """
        Initialize a new ``MaskedDict`` instance.

        :param parent: The ``SensitiveDict`` instance to be wrapped.
        """

        self._parent = parent

    def __enter__(self):
        """
        Called upon entry to a context manager.

        :returns: The ``MaskedDict`` instance.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called upon exit from a context manager.

        :param exc_type: The type of any exception that occurred
                         within the context manager.
        :param exc_value: The actual value of any exception that
                          occurred within the context manager.
        :param traceback: The traceback of any exception that occurred
                          within the context manager.

        :returns: A ``None`` value to indicate that exceptions were
                  not handled.
        """

        pass

    def __str__(self):
        """
        Obtain a string form of a ``MaskedDict`` instance.

        :returns: The string form of the ``MaskedDict`` instance.
        """

        return six.text_type(dict(self))

    def __len__(self):
        """
        Obtain the length of a ``MaskedDict`` instance.

        :returns: The number of keys in the dictionary.
        """

        return len(self._parent)

    def __getitem__(self, key):
        """
        Retrieve the value of a key.  All values are returned as simple
        strings, and sensitive values are masked--that is, their value
        is reported as the string "<masked VAR>", where "VAR" will be
        the key.

        :param key: The name of the key to retrieve.

        :returns: The value of the designated key, with appropriate
                  masking applied.
        """

        # Well, if it doesn't even exist, raise KeyError immediately
        if key not in self._parent:
            raise KeyError(key)

        # Apply masking
        if key in self._parent.sensitive:
            return self._parent.masking.format(key=key)

        # OK, just stringify the value
        return self._parent[key]

    def __iter__(self):
        """
        Iterate over the dictionary.

        :returns: An iterator over the keys in the dictionary.
        """

        return iter(self._parent)

    @property
    def sensitive(self):
        """
        Retrieve a set of the "sensitive" keys, keys for which the data
        should be treated as sensitive.  This will be a copy;
        modifications will not affect the set.
        """

        return self._parent.sensitive

    @property
    def masked(self):
        """
        Retrieve a read-only subordinate mapping.  All values are
        stringified, and sensitive values are masked.  The subordinate
        mapping implements the context manager protocol for
        convenience.
        """

        return self


def schema_validate(instance, schema, exc_class, *prefix, **kwargs):
    """
    Schema validation helper.  Performs JSONSchema validation.  If a
    schema validation error is encountered, an exception of the
    designated class is raised with the validation error message
    appropriately simplified and passed as the sole positional
    argument.

    :param instance: The object to schema validate.
    :param schema: The schema to use for validation.
    :param exc_class: The exception class to raise instead of the
                      ``jsonschema.ValidationError`` exception.
    :param prefix: Positional arguments are interpreted as a list of
                   keys to prefix to the path contained in the
                   validation error.
    :param kwargs: Keyword arguments to pass to the exception
                   constructor.
    """

    try:
        # Do the validation
        jsonschema.validate(instance, schema)
    except jsonschema.ValidationError as exc:
        # Assemble the path
        path = '/'.join((a if isinstance(a, six.string_types) else '[%d]' % a)
                        for a in itertools.chain(prefix, exc.path))

        # Construct the message
        message = 'Failed to validate "%s": %s' % (path, exc.message)

        # Raise the target exception
        raise exc_class(message, **kwargs)


def iter_prio_dict(prio_dict):
    """
    Iterate over a priority dictionary.  A priority dictionary is a
    dictionary keyed by integer priority, with the values being lists
    of objects.  This generator will iterate over the dictionary in
    priority order (from lowest integer value to highest integer
    value), yielding each object in the lists in turn.

    :param prio_dict: A priority dictionary, as described above.

    :returns: An iterator that yields each object in the correct
              order, based on priority and ordering within the
              priority values.
    """

    for _prio, objs in sorted(prio_dict.items(), key=lambda x: x[0]):
        for obj in objs:
            yield obj
