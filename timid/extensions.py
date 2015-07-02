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

import abc
import inspect
import os
import sys
import traceback

import six

from timid import entry
from timid import utils


NAMESPACE_EXTENSIONS = 'timid.extensions'


@six.add_metaclass(abc.ABCMeta)
class Extension(object):
    """
    Represent an extension.  A timid extension provides functionality
    beyond that provided by actions or modifiers, in that it is able
    to add arguments to the CLI interface, provide alternate
    reporters, insert steps, etc.
    """

    @classmethod
    def prepare(cls, parser):
        """
        Called to prepare the extension.  The extension is prepared during
        argument parser preparation.  An extension implementing this
        method is able to add command line arguments specific for that
        extension.  Note that this is a class method; the extension
        will not be instantiated prior to calling this method, nor
        should this method attempt to initialize the extension.

        :param parser: The argument parser, an instance of
                       ``argparse.ArgumentParser``.
        """

        pass  # pragma: no cover

    @classmethod
    def activate(cls, ctxt, args):
        """
        Called to determine whether to activate the extension.  This call
        is made after processing command line arguments, and must
        return either ``None`` or an initialized instance of the
        extension.  Note that this is a class method.

        :param ctxt: An instance of ``timid.context.Context``.
        :param args: An instance of ``argparse.Namespace`` containing
                     the result of processing command line arguments.

        :returns: An instance of the extension class if the extension
                  has been activated, ``None`` if it has not.  If this
                  method returns ``None``, no further extension
                  methods will be called.
        """

        return None

    def read_steps(self, ctxt, steps):
        """
        Called after reading steps, prior to adding them to the list of
        test steps.  This allows an extension to alter the list (in
        place).

        :param ctxt: An instance of ``timid.context.Context``.
        :param steps: A list of ``timid.steps.Step`` instances.
        """

        pass  # pragma: no cover

    def pre_step(self, ctxt, step, idx):
        """
        Called prior to executing a step.

        :param ctxt: An instance of ``timid.context.Context``.
        :param step: An instance of ``timid.steps.Step`` describing
                     the step to be executed.
        :param idx: The index of the step in the list of steps.

        :returns: A ``True`` value if the step is to be skipped.  Any
                  ``False`` value (including ``None``) will result in
                  the step being executed as normal.
        """

        return None

    def post_step(self, ctxt, step, idx, result):
        """
        Called after executing a step.

        :param ctxt: An instance of ``timid.context.Context``.
        :param step: An instance of ``timid.steps.Step`` describing
                     the step that was executed.
        :param idx: The index of the step in the list of steps.
        :param result: An instance of ``timid.steps.StepResult``
                       describing the result of executing the step.
                       May be altered by the extension, e.g., to set
                       the ``ignore`` attribute.
        """

        pass  # pragma: no cover

    def finalize(self, ctxt, result):
        """
        Called at the end of processing.  This call allows the extension
        to emit any additional data, such as timing information, prior
        to ``timid``'s exit.  The extension may also alter the return
        value.

        :param ctxt: An instance of ``timid.context.Context``.
        :param result: The return value of the basic ``timid`` call,
                       or an ``Exception`` instance if an exception
                       was raised.  Without the extension, this would
                       be passed directly to ``sys.exit()``.

        :returns: Should return ``result`` unless the extension wishes
                  to change the return value.
        """

        return result

    @abc.abstractproperty
    def priority(self):
        """
        An integer value.  This provides a primitive means of controlling
        the order in which extensions will be called.  The higher the
        number, the later the modifier will be applied.

        This must be a class attribute, not a property.
        """

        pass  # pragma: no cover


class ExtensionDebugger(object):
    """
    A context manager to facilitate debugging of extensions.  Under
    normal circumstances, exceptions raised by an extension are
    ignored, but a developer working on an extension can set the
    environment variable ``TIMID_EXTENSION_DEBUG`` to enable debugging
    output.  If the environment variable is just present and set to a
    non-zero integer value, basic debugging is enabled that will emit
    a stack trace for any exception generated by an extension.  Higher
    integer values of ``TIMID_EXTENSION_DEBUG`` will emit further
    debugging information for each extension method call.
    """

    def __init__(self, method):
        """
        Initialize an ``ExtensionDebugger`` instance.

        :param where: A string indicating the name of the extension
                      method that will be called.
        """

        # Save the method and initialize the ext_cls tracker
        self.method = method
        self.ext_cls = None

        # Are we enabling debugging?
        debug = os.environ.get('TIMID_EXTENSION_DEBUG')
        if debug is None:
            self._debug = 0
        else:
            try:
                # The max() ensures -1 becomes 0
                self._debug = max(0, int(debug))
            except ValueError:
                # Not an integer value, just set it to 1
                self._debug = 1

        # If we're in level 2 debugging, log what's about to be called
        self.debug(2, 'Calling extension method "%s()"' % self.method)

    def __enter__(self):
        """
        Called upon entry to the context manager.

        :returns: The ``ExtensionDebugger`` instance.
        """

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Called upon exit from the context manager.  Implements the
        debugging output.

        :param exc_type: The exception type.  If no exception was
                         generated, will be ``None``.
        :param exc_value: The exception value.  If no exception was
                          generated, will be ``None``.
        :param exc_tb: The exception traceback.  If no exception was
                       generated, will be ``None``.

        :returns: A ``True`` value if any exception should be ignored,
                  ``False`` otherwise.  Will return ``True`` for all
                  ``Exception`` subclasses unless debugging is
                  enabled.
        """

        # Are we in debugging mode?  Was there an exception?
        if self._debug >= 1 and exc_type is not None:
            # Emit a traceback
            traceback.print_exception(exc_type, exc_value, exc_tb,
                                      file=sys.stderr)

            # Exit with an informative message
            sys.exit('Extension failure calling "%s()" for extension "%s.%s"' %
                     (self.method, self.ext_cls.__module__,
                      self.ext_cls.__name__))

            # Just in case; shouldn't ever be reached except in the
            # test suite
            return False

        # Clear the extension class
        self.ext_cls = None
        return exc_type and issubclass(exc_type, Exception)

    def __call__(self, ext):
        """
        Called to save the extension class that is being processed.

        :param ext: A subclass of ``Extension``, or an instance of a
                    subclass of ``Extension``.  This is the extension
                    that is about to be called.

        :returns: The ``ExtensionDebugger`` instance, for convenience.
        """

        # Save the extension class
        self.ext_cls = ext if inspect.isclass(ext) else ext.__class__

        # If the highest level of debugging is set, log which
        # extension we're about to call
        self.debug(3, 'Calling extension "%s.%s" method "%s()"' %
                   (self.ext_cls.__module__, self.ext_cls.__name__,
                    self.method))

        return self

    def debug(self, level, message):
        """
        Emit a debugging message depending on the debugging level.

        :param level: The debugging level.
        :param message: The message to emit.
        """

        if self._debug >= level:
            print(message, file=sys.stderr)


class ExtensionSet(object):
    """
    Maintain a list of activated extensions.  This also provides
    convenience methods for invoking the extension methods correctly.
    """

    # An ordered cache of extension classes
    _extension_classes = None

    @classmethod
    def _get_extension_classes(cls):
        """
        Retrieve the extension classes in priority order.

        :returns: A list of extension classes, in proper priority
                  order.
        """

        if cls._extension_classes is None:
            exts = {}

            # Iterate over the entrypoints
            for ext in entry.points[NAMESPACE_EXTENSIONS]:
                exts.setdefault(ext.priority, [])
                exts[ext.priority].append(ext)

            # Save the list of extension classes
            cls._extension_classes = list(utils.iter_prio_dict(exts))

        return cls._extension_classes

    @classmethod
    def prepare(cls, parser):
        """
        Prepare all the extensions.  Extensions are prepared during
        argument parser preparation.  An extension implementing the
        ``prepare()`` method is able to add command line arguments
        specific for that extension.

        :param parser: The argument parser, an instance of
                       ``argparse.ArgumentParser``.
        """

        debugger = ExtensionDebugger('prepare')

        for ext in cls._get_extension_classes():
            with debugger(ext):
                ext.prepare(parser)

    @classmethod
    def activate(cls, ctxt, args):
        """
        Initialize the extensions.  This loops over each extension
        invoking its ``activate()`` method; those extensions that
        return an object are considered "activated" and will be called
        at later phases of extension processing.

        :param ctxt: An instance of ``timid.context.Context``.
        :param args: An instance of ``argparse.Namespace`` containing
                     the result of processing command line arguments.

        :returns: An instance of ``ExtensionSet``.
        """

        debugger = ExtensionDebugger('activate')

        exts = []
        for ext in cls._get_extension_classes():
            # Not using debugger as a context manager here, because we
            # want to know about the exception even if we're ignoring
            # it...but we need to notify which extension is being
            # processed!
            debugger(ext)

            try:
                # Check if the extension is being activated
                obj = ext.activate(ctxt, args)
            except Exception:
                # Hmmm, failed to activate; handle the error
                exc_info = sys.exc_info()
                if not debugger.__exit__(*exc_info):
                    six.reraise(*exc_info)
            else:
                # OK, if the extension is activated, use it
                if obj is not None:
                    exts.append(obj)
                    debugger.debug(2, 'Activating extension "%s.%s"' %
                                   (ext.__module__, ext.__name__))

        # Initialize and return the ExtensionSet
        return cls(exts)

    def __init__(self, exts=None):
        """
        Initialize an ``ExtensionSet`` instance.

        :param exts: A list of extensions that have been activated.
        """

        self.exts = exts or []

    def read_steps(self, ctxt, steps):
        """
        Called after reading steps, prior to adding them to the list of
        test steps.  Extensions are able to alter the list (in place).

        :param ctxt: An instance of ``timid.context.Context``.
        :param steps: A list of ``timid.steps.Step`` instances.

        :returns: The ``steps`` parameter, for convenience.
        """

        debugger = ExtensionDebugger('read_steps')

        for ext in self.exts:
            with debugger(ext):
                ext.read_steps(ctxt, steps)

        # Convenience return
        return steps

    def pre_step(self, ctxt, step, idx):
        """
        Called prior to executing a step.

        :param ctxt: An instance of ``timid.context.Context``.
        :param step: An instance of ``timid.steps.Step`` describing
                     the step to be executed.
        :param idx: The index of the step in the list of steps.

        :returns: A ``True`` value if the step is to be skipped,
                  ``False`` otherwise.
        """

        debugger = ExtensionDebugger('pre_step')

        for ext in self.exts:
            with debugger(ext):
                if ext.pre_step(ctxt, step, idx):
                    # Step must be skipped
                    debugger.debug(3, 'Skipping step %d' % idx)
                    return True

        return False

    def post_step(self, ctxt, step, idx, result):
        """
        Called after executing a step.

        :param ctxt: An instance of ``timid.context.Context``.
        :param step: An instance of ``timid.steps.Step`` describing
                     the step that was executed.
        :param idx: The index of the step in the list of steps.
        :param result: An instance of ``timid.steps.StepResult``
                       describing the result of executing the step.
                       May be altered by the extension, e.g., to set
                       the ``ignore`` attribute.

        :returns: The ``result`` parameter, for convenience.
        """

        debugger = ExtensionDebugger('post_step')

        for ext in self.exts:
            with debugger(ext):
                ext.post_step(ctxt, step, idx, result)

        # Convenience return
        return result

    def finalize(self, ctxt, result):
        """
        Called at the end of processing.  This call allows extensions to
        emit any additional data, such as timing information, prior to
        ``timid``'s exit.  Extensions may also alter the return value.

        :param ctxt: An instance of ``timid.context.Context``.
        :param result: The return value of the basic ``timid`` call,
                       or an ``Exception`` instance if an exception
                       was raised.  Without the extension, this would
                       be passed directly to ``sys.exit()``.

        :returns: The final result.
        """

        debugger = ExtensionDebugger('finalize')

        for ext in self.exts:
            with debugger(ext):
                result = ext.finalize(ctxt, result)

        return result
