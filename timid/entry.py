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

import pkg_resources
import six


# Indicate that the entrypoint cannot be loaded
_unavailable = object()


class NamespaceCache(object):
    """
    Cache of loaded entrypoints for a designated namespace.  A given
    entrypoint may be accessed using item notation.
    """

    def __init__(self, namespace):
        """
        Initialize a ``NamespaceCache``.

        :param namespace: The namespace to cache.
        """

        # Save the namespace
        self.namespace = namespace

        # Formulate the entrypoints so we only iterate once
        self._entrypoints = {}
        for ep in pkg_resources.iter_entry_points(namespace):
            self._entrypoints.setdefault(ep.name, [])
            self._entrypoints[ep.name].append(ep)

        # Cache of successfully loaded entrypoints
        self._epcache = {}

        # Cache of successfully iterated entrypoints
        self._eplist = None

    def __iter__(self):
        """
        Iterate over all the defined entrypoints.  This may return
        multiple entrypoints of the same name.

        :returns: An iterator over all defined and loadable entrypoint
                  objects.  The iteration will be ordered by
                  entrypoint name, but no further ordering is imposed
                  on the objects.
        """

        # Short-circuit and use our cached list
        if self._eplist is not None:
            for ep_obj in self._eplist:
                yield ep_obj
            return

        # OK, the list is not cached yet, so we'll have to create it
        self._eplist = []
        for name, eps in sorted(self._entrypoints.items(), key=lambda x: x[0]):
            for ep in eps:
                # Load the entrypoint
                try:
                    ep_obj = ep.load()
                except (ImportError, AttributeError,
                        pkg_resources.UnknownExtra):
                    continue

                # If it's the first for that entrypoint, cache it
                self._epcache.setdefault(name, ep_obj)

                # Cache it in the list
                self._eplist.append(ep_obj)

                yield ep_obj

            # At the end of the entrypoints loop, the _epcache[name]
            # should be set to something; if it's not, we couldn't
            # load any of the entrypoints, so mark it unavailable
            self._epcache.setdefault(name, _unavailable)

    def __contains__(self, name):
        """
        Determine if an entrypoint is available.  Note that no attempt is
        made to load the entrypoint, so referencing the entrypoint
        later may raise an exception.

        :param name: The name of the entrypoint.

        :returns: A ``True`` or ``False`` value, depending on if the
                  entrypoint is available.
        """

        return (name in self._entrypoints and
                self._epcache.get(name) is not _unavailable)

    def __getitem__(self, name):
        """
        Retrieve the designated entrypoint object.

        :param name: The name of the entrypoint.

        :returns: The loaded object referenced by the entrypoint.
        """

        # If it's not defined, or if we failed to load it last time,
        # bail out with a KeyError
        if (name not in self._entrypoints or
                self._epcache.get(name) is _unavailable):
            raise KeyError(name)

        # OK, do we need to load it?
        if name not in self._epcache:
            error = None
            for ep in self._entrypoints[name]:
                try:
                    self._epcache[name] = ep.load()
                except (ImportError, AttributeError,
                        pkg_resources.UnknownExtra):
                    # Save the error for later re-raise
                    if error is None:
                        error = sys.exc_info()
                else:
                    # Successfully resolved it
                    break
            else:
                # Couldn't resolve it...
                self._epcache[name] = _unavailable
                if error is None:
                    raise KeyError(name)
                six.reraise(*error)

        return self._epcache[name]


class EntrypointCache(object):
    """
    Cache of entrypoint namespaces.  A given namespace may be accessed
    using item notation.
    """

    def __init__(self):
        """
        Initialize an ``EntrypointCache``.
        """

        self._namespaces = {}

    def __getitem__(self, name):
        """
        Retrieve a ``NamespaceCache`` for a designated entrypoint
        namespace.

        :param name: The entrypoint namespace.

        :returns: An instance of ``NamespaceCache``.
        """

        # Look up the namespace
        if name not in self._namespaces:
            self._namespaces[name] = NamespaceCache(name)

        return self._namespaces[name]


# The cache
points = EntrypointCache()
