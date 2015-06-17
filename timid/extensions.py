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

    @staticmethod
    def extensions():
        """
        Retrieve a list of extensions in the appropriate order.

        :returns: The list of ``Extension`` classes in the proper
                  order.
        """

        exts = {}

        # Iterate over the entrypoints
        for ext in entry.points[NAMESPACE_EXTENSIONS]:
            exts.setdefault(ext.priority, [])
            exts[ext.priority].append(ext)

        # Now return the list in the proper order
        return list(utils.iter_prio_dict(exts))

    @classmethod
    def prepare(cls, parser):
        """
        Called to prepare the extension.  The extension is prepared during
        argument parser preparation.  An extension implementing this
        method is able to add command line arguments specific for that
        extension.  Note that this is a class method; the extension
        will not be instantiated prior to calling this method, nor
        should this method attempt to initialize the extension.

        :param parser: The argument parser, an
                       ``argparse.ArgumentParser`` instance.
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

    def finalize(self, ctxt, retval):
        """
        Called at the end of processing.  This call allows the extension
        to emit any additional data, such as timing information, prior
        to ``timid``'s exit.  The extension may also alter the return
        value.

        :param ctxt: An instance of ``timid.context.Context``.
        :param retval: The return value of the basic ``timid`` call,
                       or an ``Exception`` instance if an exception
                       was raised.  Without the extension, this would
                       be passed directly to ``sys.exit()``.

        :returns: Should return ``retval`` unless the extension wishes
                  to change the return value.
        """

        return retval

    @abc.abstractproperty
    def priority(self):
        """
        An integer value.  This provides a primitive means of controlling
        the order in which extensions will be called.  The higher the
        number, the later the modifier will be applied.

        This must be a class attribute, not a property.
        """

        pass  # pragma: no cover
