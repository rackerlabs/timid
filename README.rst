=================
Timid Test Runner
=================

Timid is a command line tool for running tests.  It differs from
Python tools like tox in that it is not limited to Python.  It uses a
YAML file to describe how to build the environment to run the test
in.

Why Timid?
==========

Timid is intended to provide a very flexible test description
language.  It provides functionality for setting up various aspects of
the test environment, as well as for actually invoking the test
command.  While not too dissimilar from a Python tool like tox, Timid
does not make any assumptions about what that environment should look
like; in particular, it does not create a virtual environment unless
the test description includes the appropriate commands to do so.  This
makes it suitable for running any set of tests.

Another aspect of Timid is the ability to reference any subset of test
steps from other files.  This enables easy reuse for complicated test
descriptions, and even means a library of test description fragments
may be easily established and used.  Timid also allows the working
directory to be directly set from the command line, allowing the test
descriptions to be separated from the actual code to test.  Finally,
Timid is extremely extensible; new test step actions and modifiers may
be created by including a class in the appropriate entrypoint
namespaces ("timid.actions" and "timid.modifiers", respectively), and
extensions (namespace "timid.extensions") may also be created that can
perform specific tasks under control of the command line--for
instance, an extension could allow a Timid test to run on a Github
pull request, setting test status information using the Github status
API.

Basic Test Description Syntax
=============================

Test descriptions are YAML files consisting of a list of dictionaries,
where each dictionary describes a *step* in the testing process.  Each
step consists of one *action* and zero or more *modifiers* which alter
the action in some way.  A step may also have a *name*, which is used
to identify the step in the output, and a *description*.  The action
and the modifiers are identified by the keys of the step dictionary;
the values of those keys identify the options for that action or
modifier.  The options may be any legal YAML entity, such as a string,
integer, boolean, list, or a dictionary; the documentation for each of
the actions and modifiers will describe what that action or modifier
expects.

The test description could also be a smaller component of a YAML file
containing a dictionary; each value of this dictionary must be a list
of dictionaries, as described above.  This could be used to describe
several different but related tests for a single project (e.g., style
tests, unit tests, functional tests, and integration tests), or it
could be used to provide a library of test steps that can be included
using the "include" action.

Templating and Expressions
--------------------------

Many actions and modifiers allow Jinja2-style templates to be
specified for values, which enhances reusability of test description
components.  Jinja2-style expressions can also be used; an example
would be the "when" modifier, which provides simple conditional
control of an action.  Template variables can be set on the command
line, read from a YAML file, or set up directly in the test
description.

Security
--------

Timid provides a way to mark both template variables and environment
variables as being "sensitive".  This is to allow security-sensitive
data, such as usernames and passwords, to be used, while ensuring that
that sensitive data is scrubbed from any verbose or debugging output
from Timid itself.  For template variables, this can only be done from
the test description file, but environment variables can also be
marked sensitive by listing them in the ``TIMID_SENSITIVE``
environment variable, separated by your system's path separator
character.  (On UNIX and Linux systems, this character would be the
":" character.)  The ``TIMID_SENSITIVE`` environment variable will
also be present in the environment of any subordinate processes,
updated with any additional environment variables marked as sensitive
by the test description; this can be used by test scripts to omit
sensitive information from the environment in debugging output.

Extending Timid
===============

As mentioned previously, Timid uses Python entrypoints for simple
extensibility.  Each action or modifier in a test description is
looked up for in the "timid.actions" or "timid.modifiers" namespaces,
respectively.  These entrypoints must map to subclasses of
``timid.Action`` or ``timid.Modifier``, as appropriate.  Timid also
provides extensions, which allow extending the actual command line
interface and other per-step behavior; these are listed in the
"timid.extensions" interface, and the entrypoints must map to
subclasses of ``timid.Extension``.

Creating a New Action
---------------------

Actions perform the actual test step.  Creating a new action is a
matter of extending ``timid.Action``.  In the new action class, the
``schema`` class attribute must be set to a JSONSchema description of
the expected configuration; and the ``__call__()`` method, taking as
its sole argument a *context* object, must be defined to implement the
actual action; it should return an instance of ``timid.StepResult``.
The ``timid.Action`` class declares a ``__init__()`` method taking
four arguments (a context object, the name of the action (the key read
from the test description), the configuration for the action (the
value for that key), and a *step address* object); it validates the
configuration, then stores the last three arguments in the ``name``,
``config``, and ``step_addr`` attributes, respectively.  (The context
object should not be stored; it will be passed in to the
``__call__()`` method.)

There are two types of actions.  By default, all ``timid.Action``
subclasses are instantiated while reading the test description, then
their ``__call__()`` methods are invoked in order during the actual
test run--or not invoked at all, if a syntax check is being
performed.  However, it is possible to create a "step action", an
action invoked immediately after it is read from the test description;
this is used, for instance, to implement the "include" step, which
reads steps from another file and inserts them in place of the
"include" step.  These are implemented by setting the ``step_action``
class attribute to ``True`` and having ``__call__()`` return a list of
``timid.Step`` objects, instead of a ``timid.StepResult`` object.

Creating a New Modifier
-----------------------

Modifiers modify a step in some fashion, such as by running the step
in a loop or applying a conditional prior to invoking the step.
Creating a new action is a matter of extending ``timid.Modifier``.
Like actions, the new subclass must have a ``schema`` class attribute
set to a JSONSchema description of the expected configuration, and a
``__init__()`` method identical to that for ``timid.Action`` is also
implemented; however, modifiers do not have a ``__call__()`` method,
and the class attribute ``priority`` must be set to an integer value.
The ``priority`` attribute controls the order in which modifiers are
applied while running a step, with lower values invoked before higher
values.

A modifier actually consists of a set of hook functions.  The
``timid.Modifier`` superclass contains default implementations of
these hook functions, so a developer need only override the ones
needed to implement the modifier.

The first hook is the ``action_conf()`` hook, which takes 5 arguments:
a context object, the class implementing the modified action, the name
of the action (key read from the test description), the configuration
for the *action* (the ``__init__()`` method receives the configuration
for the *modifier*), and a *step address* object.  The hook function
must return the configuration that should be passed to the action
class, giving the modifier the opportunity to alter the configuration.

The remaining two hooks are the ``pre_call()`` and ``post_call()``
methods, which are invoked prior to and after calling the action's
``__call__()`` method, respectively.  The ``pre_call()`` method can
return a ``timid.StepResult`` object, which aborts further processing
(including the call to the action) and proceeds with invoking any
``post_call()`` methods.  The ``post_call()`` method receives the
``timid.StepResult`` object and can modify it or even replace it
entirely, by returning a different object.  The ``pre_call()`` method
takes 4 arguments: a context object, a "pre_mod" list, a "post_mod"
list, and the instance of the ``timid.Action`` subclass.  The
``post_call()`` method gets 5 arguments: a context object, the result
of the call (an instance of ``timid.StepResult``), the instance of the
``timid.Action`` subclass, a "post_mod" list, and a "pre_mod" list.
The "pre_mod" and "post_mod" lists are lists of ``timid.Modifier``
instances that have lower priority and higher priority, respectively.
It should also be noted that ``post_call()`` is called in the inverse
order of ``pre_call()``.

Context Objects
---------------

The context object passed to the actions and modifier methods provides
several services throughout Timid.  The ``verbose`` attribute contains
an integer value controlling the verbosity of Timid's output (0 means
no output at all), and ``debug`` is a boolean indicating whether
debugging is enabled.  The ``variables`` attribute contains a
dictionary of template variables, and ``environment`` contains the
environment variables.  (The environment dictionary-like object also
allows control of the current working directory, by setting its
``cwd`` attribute, and its ``call()`` method should be used to invoke
external programs.)

Timid provides an interface to Jinja2, and two utility methods on the
context object facilitate this: the ``template()`` method takes a
string and returns a callable of one argument that will render the
template, and ``expression()`` works similarly for Jinja2
expressions.  (It is safe to pass objects other than strings to these
two methods as well; the result will still be a callable of one
argument, but no template expansion will be performed.)  The context
object should be passed to the callable returned by ``template()`` and
``expression()``.

The usual way to use the ``template()`` and ``expression()`` methods
is to override the ``__init__()`` method of the ``timid.Action`` or
``timid.Modifier`` subclass; the method should invoke the superclass's
version of ``__init__()`` (using a ``super()`` expression), and would
then process the configuration, saving the callables produced by
calling ``template()`` and ``expression()``.  Then, where the values
are used in the action's ``__call__()`` or the modifier's hook
methods, simply pass the context to the callable and use the result as
the actual value to use.

Step Addresses
--------------

To aid debugging, each action or modifier has a *step address* object
associated with it.  The address has three attributes: the filename
from which the step was read (``fname``); the 0-based index of the
step within the file (``idx``); and the key for the list containing
the steps (``key``).  (This latter attribute will be ``None`` if the
file was a simple list of steps.)  The object also has a
straightforward string representation which includes the filename,
key, and step index (1-based; that is, if ``idx`` is 3, the string
will identify the step as step 4).

Creating an Extension
---------------------

Extensions are the most powerful extensibility mechanism in Timid.
Creating one is a matter of extending ``timid.Extension`` and
implementing the desired hook methods, similar to creating a new
modifier, except that a Timid extension must implement an
``activate()`` class method if it actually intends to do anything.
Additionally, a ``timid.Extension`` subclass must set the ``priority``
class attribute to a numerical value, just like a ``timid.Modifier``
subclass; extension hook functions will be called in the order
dictated by the priorities.

The first hook method that an extension may implement is the
``prepare()`` method.  This must be a class method, and will receive
as its sole argument an ``argparse.ArgumentParser`` instance, which
the extension may use to declare new command line options.  All
extensions will have their ``prepare()`` method called during Timid
initialization.

Once the command line has been processed by
``argparse.ArgumentParser``, each extension's ``activate()`` method
will be called with a context object and an ``argparse.Namespace``
containing the results of the command line processing.  This method
must also be a class method, and must return either ``None`` or an
instance of the ``timid.Extension`` subclass; if it returns ``None``,
the extension is treated as inactive and no other hook methods will be
called.

The remaining hook methods are all instance methods, called on the
object returned by the ``activate()`` method.  The ``read_steps()``
method is called with a context object and a list of ``timid.Step``
instances; the extension may perform any in-place modifications to the
list of steps that are appropriate.  The ``pre_step()`` and
``post_step()`` methods are called before and after executing a step,
respectively; ``pre_step()`` is called with a context object, the
``timid.Step`` instance, and the index of the step, and may return a
``True`` value to cause the step to be skipped.  The ``post_step()``
method is called with the same arguments, and a fourth argument, which
will be a ``timid.StepResult`` object, which it may alter in place;
the return value of ``post_step()`` is ignored.  Note that
``post_step()`` is called in extension order, in contrast to the
``post_call()`` method of ``timid.Modifier`` instances.

The final hook function is the ``finalize()`` method, which is called
just before the command line tool exits.  It is called with a context
object and the result, which will typically be ``None`` for success,
or a text string indicating an error.  (It could also be called with
an ``Exception`` instance if an error occurred.)  This method's return
value will replace the result.

Debugging Extensions
--------------------

The implementation of extensions explicitly ignores exceptions raised
by a given extension.  This would make it difficult to debug a newly
developed extension, so Timid provides a debugging mechanism: the
``TIMID_EXTENSION_DEBUG`` environment variable may be set to an
integer value, with larger values resulting in more verbose debugging.
If ``TIMID_EXTENSION_DEBUG`` is present in the environment with no
value, or with a non-integer value, the debugging level will be set to
1; a debugging level of 0 (or any negative value) is exactly the same
as if ``TIMID_EXTENSION_DEBUG`` was not present in the environment at
all.

Note that this environment variable is checked directly from the
environment, unlike the ``TIMID_SENSITIVE`` environment variable.
This means that the value used by extension debugging cannot be
altered by any instructions in the test description; only child
processes can be affected by such instructions.  Even command line
environment variable manipulations are ignored for the purposes of
extension debugging.  This design decision was made so that debugging
could be enabled before even calling the extension ``prepare()``
method, which is called before any argument processing is done, and
thus prior to reading any test description files.
