# -*- coding: utf-8 -*-
"""This module implements most of those tools, that involve some tricks to
simplify using the HydPy framework.

These tools are primarily designed for features like hiding model
initialization routines from model users and for allowing readable definitions
of doctests.  Hence, along with some metaclasses defined in other modules and
with the cythonization features of module :mod:`~hydpy.cythons.modelutils` and
the documentation features of module :mod:`~hydpy.cythons.autodoctools`,
module :mod:`~hydpy.core.magictools` somehow modifies the Python API a little
to the advantage of model users and model developers.  Programmers who work
on the core routines of HydPy and encounter unexpected side effects, should
first have a look into this module and the other modules mentioned.
"""
# import...
# ...from the Python standard library
from __future__ import division, print_function
import os
import sys
import inspect
import warnings
import importlib
import doctest
import functools
import tempfile
import time
import itertools
# ...from site-packages
import wrapt
# ...from HydPy
import hydpy
from hydpy import pub
from hydpy.core import autodoctools
# from hydpy.core import devicetools # the actual import is done below
# from hydpy.core import filetools # the actual import is done below
from hydpy.core import objecttools
# from hydpy.core import parametertools # the actual import is done below
from hydpy.core import sequencetools
from hydpy.core import timetools
# from hydpy.core import testtools # the actual import is done below


class Tester(object):

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.filepath = frame.f_code.co_filename
        self.package = frame.f_locals['__package__']
        self.ispackage = os.path.split(self.filepath)[-1] == '__init__.py'

    @property
    def filenames(self):
        if self.ispackage:
            return os.listdir(os.path.dirname(self.filepath))
        return [self.filepath]

    @property
    def modulenames(self):
        return [os.path.split(fn)[-1].split('.')[0] for fn in self.filenames
                if (fn.endswith('.py') and not fn.startswith('_'))]

    def doit(self):
        from hydpy.core import devicetools
        from hydpy.core import parametertools
        from hydpy.core import testtools
        opt = pub.options
        par = parametertools.Parameter
        with opt.usedefaultvalues(False), \
                opt.usedefaultvalues(False), \
                opt.printprogress(False), \
                opt.printincolor(False), \
                opt.warnsimulationstep(False), \
                opt.reprcomments(False), \
                opt.ellipsis(0), \
                opt.reprdigits(6), \
                opt.warntrim(False), \
                par.parameterstep.delete(), \
                par.simulationstep.delete():
            timegrids = pub.timegrids
            pub.timegrids = None
            nodes = devicetools.Node._registry.copy()
            elements = devicetools.Element._registry.copy()
            devicetools.Node.clear_registry()
            devicetools.Element.clear_registry()
            plotting_options = testtools.IntegrationTest.plotting_options
            testtools.IntegrationTest.plotting_options = \
                testtools.PlottingOptions()
            try:
                color = 34 if pub.options.usecython else 36
                with PrintStyle(color=color, font=4):
                    print(
                        'Test %s %s in %sython mode.'
                        % ('package' if self.ispackage else 'module',
                           self.package if self.ispackage else
                           self.modulenames[0],
                           'C' if pub.options.usecython else 'P'))
                with PrintStyle(color=color, font=2):
                    for name in self.modulenames:
                        print('    * %s:' % name, )
                        with StdOutErr(indent=8):
                            modulename = '.'.join((self.package, name))
                            module = importlib.import_module(modulename)
                            with warnings.catch_warnings():
                                warnings.filterwarnings(
                                    'error', module=modulename)
                                warnings.filterwarnings(
                                    'ignore', category=ImportWarning)
                                doctest.testmod(
                                    module, extraglobs={'testing': True},
                                    optionflags=doctest.ELLIPSIS)
            finally:
                pub.timegrids = timegrids
                devicetools.Node.clear_registry()
                devicetools.Element.clear_registry()
                devicetools.Node._registry = nodes
                devicetools.Element._registry = elements
                testtools.IntegrationTest.plotting_options = plotting_options
                hydpy.dummies.clear()


class PrintStyle(object):

    def __init__(self, color, font, file=None):
        self.color = color
        self.font = font
        self.file = sys.stdout if file is None else file

    def __enter__(self):
        if pub.options.printincolor:
            print(end='\x1B[%d;30;%dm' % (self.font, self.color),
                  file=self.file)

    def __exit__(self, exception, message, traceback_):
        if pub.options.printincolor:
            print(end='\x1B[0m', file=self.file)
        if exception:
            objecttools.augment_excmessage()


class StdOutErr(object):

    def __init__(self, indent=0):
        self.indent = indent
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.encoding = sys.stdout.encoding
        self.texts = []

    def __enter__(self):
        self.encoding = sys.stdout.encoding
        sys.stdout = self
        sys.stderr = self

    def __exit__(self, exception, message, traceback_):
        if not self.texts:
            self.print_('no failures occurred')
        else:
            for text in self.texts:
                self.print_(text)
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        if exception:
            objecttools.augment_excmessage()

    def write(self, text):
        self.texts.extend(text.split('\n'))

    def print_(self, text):
        if text.strip():
            self.stdout.write(self.indent*' ' + text + '\n')

    def flush(self):
        pass


def parameterstep(timestep=None):
    """Define a parameter time step size within a parameter control file.

    Argument:
      * timestep(:class:`~hydpy.core.timetools.Period`): Time step size.

    Function parameterstep should usually be be applied in a line
    immediately behind the model import.  Defining the step size of time
    dependent parameters is a prerequisite to access any model specific
    parameter.

    Note that parameterstep implements some namespace magic by
    means of the module :mod:`inspect`.  This makes things a little
    complicated for framework developers, but it eases the definition of
    parameter control files for framework users.
    """
    from hydpy.core import parametertools
    if timestep is not None:
        parametertools.Parameter.parameterstep(timetools.Period(timestep))
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        model = namespace['Model']()
        namespace['model'] = model
        if pub.options.usecython and 'cythonizer' in namespace:
            cythonizer = namespace['cythonizer']
            namespace['cythonmodule'] = cythonizer.cymodule
            model.cymodel = cythonizer.cymodule.Model()
            namespace['cymodel'] = model.cymodel
            model.cymodel.parameters = cythonizer.cymodule.Parameters()
            model.cymodel.sequences = cythonizer.cymodule.Sequences()
            for numpars_name in ('NumConsts', 'NumVars'):
                if hasattr(cythonizer.cymodule, numpars_name):
                    numpars_new = getattr(cythonizer.cymodule, numpars_name)()
                    numpars_old = getattr(model, numpars_name.lower())
                    for (name_numpar, numpar) in vars(numpars_old).items():
                        setattr(numpars_new, name_numpar, numpar)
                    setattr(model.cymodel, numpars_name.lower(), numpars_new)
            for name in dir(model.cymodel):
                if (not name.startswith('_')) and hasattr(model, name):
                    setattr(model, name, getattr(model.cymodel, name))
        if 'Parameters' not in namespace:
            namespace['Parameters'] = parametertools.Parameters
        model.parameters = namespace['Parameters'](namespace)
        if 'Sequences' not in namespace:
            namespace['Sequences'] = sequencetools.Sequences
        model.sequences = namespace['Sequences'](**namespace)
        namespace['parameters'] = model.parameters
        for pars in model.parameters:
            namespace[pars.name] = pars
        namespace['sequences'] = model.sequences
        for seqs in model.sequences:
            namespace[seqs.name] = seqs
    try:
        namespace.update(namespace['CONSTANTS'])
    except KeyError:
        pass
    focus = namespace.get('focus')
    for par in model.parameters.control:
        try:
            if (focus is None) or (par is focus):
                namespace[par.name] = par
            else:
                namespace[par.name] = lambda *args, **kwargs: None
        except AttributeError:
            pass


def reverse_model_wildcard_import():
    """Clear the local namespace from a model wildcard import.

    Calling this method should remove the critical imports into the local
    namespace due the last wildcard import of a certain application model.
    It is thought for securing the successive preperation of different
    types of models via wildcard imports.  See the following example, on
    how it can be applied.

    >>> from hydpy import reverse_model_wildcard_import

    Assume you wildcard import the first version of HydPy-L-Land
    (:mod:`~hydpy.models.lland_v1`):

    >>> from hydpy.models.lland_v1 import *

    This for example adds the collection class for handling control
    parameters of `lland_v1` into the local namespace:

    >>> print(ControlParameters(None).name)
    control

    Calling function |parameterstep| for example prepares the control
    parameter object :class:`~hydpy.models.lland.lland_control.nhru`:

    >>> parameterstep('1d')
    >>> nhru
    nhru(-999999)

    Calling function |reverse_model_wildcard_import| removes both
    objects (and many more, but not all) from the local namespace:

    >>> reverse_model_wildcard_import()

    >>> ControlParameters
    Traceback (most recent call last):
    ...
    NameError: name 'ControlParameters' is not defined

    >>> nhru
    Traceback (most recent call last):
    ...
    NameError: name 'nhru' is not defined
    """
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is not None:
        for subpars in model.parameters:
            for par in subpars:
                namespace.pop(par.name, None)
                namespace.pop(objecttools.classname(par), None)
            namespace.pop(subpars.name, None)
            namespace.pop(objecttools.classname(subpars), None)
        for subseqs in model.sequences:
            for seq in subseqs:
                namespace.pop(seq.name, None)
                namespace.pop(objecttools.classname(seq), None)
            namespace.pop(subseqs.name, None)
            namespace.pop(objecttools.classname(subseqs), None)
        for name in ('parameters', 'sequences', 'model',
                     'Parameters', 'Sequences', 'Model',
                     'cythonizer', 'cymodel', 'cythonmodule'):
            namespace.pop(name, None)
        for key in list(namespace.keys()):
            try:
                if namespace[key].__module__ == model.__module__:
                    del namespace[key]
            except AttributeError:
                pass


def prepare_model(module, timestep=None):
    """Prepare and return the model of the given module.

    In usual HydPy projects, each hydrological model instance is prepared
    in an individual control file.  This allows for "polluting" the
    namespace with different model attributes.  There is no danger of
    name conflicts, as long as no other (wildcard) imports are performed.

    However, there are situations when different models are to be loaded
    into the same namespace.  Then it is advisable to use function
    |prepare_model|, which just returns a reference to the model
    and nothing else.

    See the documentation of :mod:`~hydpy.models.dam_v001` on how to apply
    function |prepare_model| properly.
    """
    from hydpy.core import parametertools
    if timestep is not None:
        parametertools.Parameter.parameterstep(timetools.Period(timestep))
    model = module.Model()
    if pub.options.usecython and hasattr(module, 'cythonizer'):
        cymodule = module.cythonizer.cymodule
        cymodel = cymodule.Model()
        cymodel.parameters = cymodule.Parameters()
        cymodel.sequences = cymodule.Sequences()
        model.cymodel = cymodel
        for numpars_name in ('NumConsts', 'NumVars'):
            if hasattr(cymodule, numpars_name):
                numpars_new = getattr(cymodule, numpars_name)()
                numpars_old = getattr(model, numpars_name.lower())
                for (name_numpar, numpar) in vars(numpars_old).items():
                    setattr(numpars_new, name_numpar, numpar)
                setattr(cymodel, numpars_name.lower(), numpars_new)
        for name in dir(cymodel):
            if (not name.startswith('_')) and hasattr(model, name):
                setattr(model, name, getattr(cymodel, name))
        dict_ = {'cythonmodule': cymodule,
                 'cymodel': cymodel}
    else:
        dict_ = {}
    dict_.update(vars(module))
    dict_['model'] = model
    if hasattr(module, 'Parameters'):
        model.parameters = module.Parameters(dict_)
    else:
        model.parameters = parametertools.Parameters(dict_)
    if hasattr(module, 'Sequences'):
        model.sequences = module.Sequences(**dict_)
    else:
        model.sequences = sequencetools.Sequences(**dict_)
    return model


def simulationstep(timestep):
    """
    Define a simulation time step size for testing purposes within a
    parameter control file.

    Using |simulationstep| only affects the values of time dependent
    parameters, when `pub.timegrids.stepsize` is not defined.  It thus has
    no influence on usual hydpy simulations at all.  Use it just to check
    your parameter control files.  Write it in a line immediately behind
    the one calling |parameterstep|.
    """
    from hydpy.core import parametertools
    if pub.options.warnsimulationstep:
        warnings.warn(
            'Note that the applied function `simulationstep` is inteded for '
            'testing purposes only.  When doing a hydpy simulation, parameter '
            'values are initialized based on the actual simulation time step '
            'as defined under `pub.timegrids.stepsize` and the value given '
            'to `simulationstep` is ignored.')
    parametertools.Parameter.simulationstep(timetools.Period(timestep))


def controlcheck(controldir='default', projectdir=None, controlfile=None):
    from hydpy.core import filetools
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        if not controlfile:
            controlfile = os.path.split(namespace['__file__'])[-1]
        os.chdir('..')
        os.chdir('..')
        controlmanager = filetools.ControlManager()
        if projectdir:
            controlmanager.projectdir = projectdir
        else:
            controlmanager.projectdir = os.path.split(os.getcwd())[-1]
        controlmanager.currentdir = controldir
        os.chdir('..')
        model = controlmanager.load_file(filename=controlfile)['model']
        model.parameters.update()
        namespace['model'] = model
        for name in ('states', 'logs'):
            subseqs = getattr(model.sequences, name, None)
            if subseqs is not None:
                for seq in subseqs:
                    namespace[seq.name] = seq


def zip_longest(*iterables, **kwargs):
    """Return the iterator defined by `zip_longest` or `izip_longest` of
    module :mod:`itertools` under Python 2 and 3 respectively."""
    # pylint: disable=no-member
    if pub.pyversion < 3:
        return itertools.izip_longest(*iterables, **kwargs)
    return itertools.zip_longest(*iterables, **kwargs)


@wrapt.decorator
def print_progress(wrapped, instance, args, kwargs):
    """Decorate a function with printing information when its execution
    starts and ends."""
    pub._printprogress_indentation += 4
    blanks = ' ' * pub._printprogress_indentation
    try:
        if pub.options.printprogress:
            with PrintStyle(color=34, font=1):
                print('\n%smethod %s...'
                      % (blanks, wrapped.__name__))
                print('%s    ...started at %s.'
                      % (' '*pub._printprogress_indentation,
                         time.strftime('%X')))
            sys.stdout.flush()
        wrapped(*args, **kwargs)
        if pub.options.printprogress:
            with PrintStyle(color=34, font=1):
                print('%s    ...ended at %s.'
                      % (blanks, time.strftime('%X')))
            sys.stdout.flush()
    finally:
        pub._printprogress_indentation -= 4


def progressbar(iterable, length=23):
    """Print a simple progress bar while processing the given iterable.

    Function |progressbar| does print the progress bar when option
    `printprogress` is activted:

    >>> from hydpy import pub
    >>> pub.options.printprogress = True

    You can pass an iterable object.  Say you want to calculate the the sum
    of all integer values from 1 to 100 and print the progress of the
    calculation.  Using function :func:`range` (which returns a list in
    Python 2 and an iterator in Python3, but both are fine), one just has
    to  interpose function |progressbar|:

    >>> from hydpy.core.magictools import progressbar
    >>> x_sum = 0
    >>> for x in progressbar(range(1, 101)):
    ...     x_sum += x
        |---------------------|
        ***********************
    >>> x_sum
    5050

    To prevent possible interim print commands from dismembering the status
    bar, they are delayed until the status bar is complete.  For intermediate
    print outs of each fiftieth calculation, the result looks as follows:

    >>> x_sum = 0
    >>> for x in progressbar(range(1, 101)):
    ...     x_sum += x
    ...     if not x % 50:
    ...         print(x, x_sum)
        |---------------------|
        ***********************
    50 1275
    100 5050


    The number of characters of the progress bar can be changed:

    >>> for i in progressbar(range(100), length=50):
    ...     continue
        |------------------------------------------------|
        **************************************************

    But its maximum number of characters is restricted by the length of the
    given iterable:

    >>> for i in progressbar(range(10), length=50):
    ...     continue
        |--------|
        **********

    The smallest possible progress bar has two characters:

    >>> for i in progressbar(range(2)):
    ...     continue
        ||
        **

    For iterables of length one or zero, no progress bar is plottet:


    >>> for i in progressbar(range(1)):
    ...     continue


    The same is True when the `printprogress` option is inactivated:

    >>> pub.options.printprogress = False
    >>> for i in progressbar(range(100)):
    ...     continue
    """
    if pub.options.printprogress and (len(iterable) > 1):
        temp_name = os.path.join(tempfile.gettempdir(),
                                 'HydPy_progressbar_stdout')
        temp_stdout = open(temp_name, 'w')
        real_stdout = sys.stdout
        try:
            sys.stdout = temp_stdout
            nmbstars = min(len(iterable), length)
            nmbcounts = len(iterable)/nmbstars
            indentation = ' '*max(pub._printprogress_indentation, 0)
            with PrintStyle(color=36, font=1, file=real_stdout):
                print('    %s|%s|\n%s    ' % (indentation,
                                              '-'*(nmbstars-2),
                                              indentation),
                      end='',
                      file=real_stdout)
                counts = 1.
                for next_ in iterable:
                    counts += 1.
                    if counts >= nmbcounts:
                        print(end='*', file=real_stdout)
                        counts -= nmbcounts
                    yield next_
        finally:
            try:
                temp_stdout.close()
            except BaseException:
                pass
            sys.stdout = real_stdout
            print()
            with open(temp_name, 'r') as temp_stdout:
                sys.stdout.write(temp_stdout.read())
            sys.stdout.flush()
    else:
        for next_ in iterable:
            yield next_


autodoctools.autodoc_module()
