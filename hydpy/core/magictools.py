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
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import filetools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import devicetools
from hydpy.core import autodoctools


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
        else:
            return [self.filepath]

    @property
    def modulenames(self):
        return [os.path.split(fn)[-1].split('.')[0] for fn in self.filenames
                if (fn.endswith('.py') and not fn.startswith('_'))]

    def doit(self):
        usedefaultvalues = pub.options.usedefaultvalues
        pub.options.usedefaultvalues = False
        printprogress = pub.options.printprogress
        pub.options.printprogress = False
        warnsimulationstep = pub.options.warnsimulationstep
        pub.options.warnsimulationstep = False
        timegrids = pub.timegrids
        pub.timegrids = None
        _simulationstep = parametertools.Parameter._simulationstep
        parametertools.Parameter._simulationstep = None
        dirverbose = pub.options.dirverbose
        reprcomments = pub.options.reprcomments
        pub.options.reprcomments = False
        reprdigits = pub.options.reprdigits
        pub.options.reprdigits = 6
        warntrim = pub.options.warntrim
        pub.options.warntrim = False
        nodes = devicetools.Node._registry.copy()
        elements = devicetools.Element._registry.copy()
        devicetools.Node.clearregistry()
        devicetools.Element.clearregistry()
        try:
            color = 34 if pub.options.usecython else 36
            with PrintStyle(color=color, font=4):
                print(
                  'Test %s %s in %sython mode.'
                  % ('package' if self.ispackage else 'module',
                     self.package if self.ispackage else self.modulenames[0],
                     'C' if pub.options.usecython else 'P'))
            with PrintStyle(color=color, font=2):
                for name in self.modulenames:
                    print('    * %s:' % name, )
                    with StdOutErr(indent=8):
                        modulename = '.'.join((self.package, name))
                        module = importlib.import_module(modulename)
                        warnings.filterwarnings('error', module=modulename)
                        warnings.filterwarnings('ignore',
                                                category=ImportWarning)
                        doctest.testmod(module, extraglobs={'testing': True},
                                        optionflags=doctest.ELLIPSIS)
                        warnings.resetwarnings()
        finally:
            pub.options.usedefaultvalues = usedefaultvalues
            pub.options.printprogress = printprogress
            pub.options.warnsimulationstep = warnsimulationstep
            pub.timegrids = timegrids
            parametertools.Parameter._simulationstep = _simulationstep
            pub.options.dirverbose = dirverbose
            pub.options.reprcomments = reprcomments
            pub.options.reprdigits = reprdigits
            pub.options.warntrim = warntrim
            devicetools.Node.clearregistry()
            devicetools.Element.clearregistry()
            devicetools.Node._registry = nodes
            devicetools.Element._registry = elements


class PrintStyle(object):

    def __init__(self, color, font):
        self.color = color
        self.font = font

    def __enter__(self):
        print('\x1B[%d;30;%dm' % (self.font, self.color))

    def __exit__(self, exception, message, traceback_):
        print('\x1B[0m')
        if exception:
            objecttools.augmentexcmessage()


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
            objecttools.augmentexcmessage()

    def write(self, text):
        self.texts.extend(text.split('\n'))

    def print_(self, text):
        if text.strip():
            self.stdout.write(self.indent*' ' + text + '\n')

    def flush(self):
        pass


def parameterstep(timestep=None):
    """
    Define a parameter time step size within a parameter control file.

    Argument:
      * timestep(:class:`~hydpy.core.timetools.Period`): Time step size.

    Function :func:`parameterstep` should usually be be applied in a line
    immediately behind the model import.  Defining the step size of time
    dependent parameters is a prerequisite to access any model specific
    parameter.

    Note that :func:`parameterstep` implements some namespace magic by
    means of the module :mod:`inspect`.  This makes things a little
    complicated for framework developers, but it eases the definition of
    parameter control files for framework users.
    """
    if timestep is not None:
        parametertools.Parameter._parameterstep = timetools.Period(timestep)
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        model = namespace['Model']()
        namespace['model'] = model
        element = namespace.get('element', None)
        if isinstance(element, devicetools.Element):
            element.model = model
            model.element = element
        if pub.options.usecython and 'cythonizer' in namespace:
            cythonizer = namespace['cythonizer']
            namespace['cythonmodule'] = cythonizer.cymodule
            model.cymodel = cythonizer.cymodule.Model()
            namespace['cymodel'] = model.cymodel
            for (name, func) in cythonizer.pyxwriter.listofmodeluserfunctions:
                setattr(model, name, getattr(model.cymodel, name))
            for func in ('doit', 'new2old', 'openfiles', 'closefiles',
                         'loaddata', 'savedata'):
                if hasattr(model.cymodel, func):
                    setattr(model, func, getattr(model.cymodel, func))
        if 'Parameters' not in namespace:
            namespace['Parameters'] = parametertools.Parameters
        model.parameters = namespace['Parameters'](namespace)
        if 'Sequences' not in namespace:
            namespace['Sequences'] = sequencetools.Sequences
        model.sequences = namespace['Sequences'](namespace)
        namespace['parameters'] = model.parameters
        for (name, pars) in model.parameters:
            namespace[name] = pars
        namespace['sequences'] = model.sequences
        for (name, seqs) in model.sequences:
            namespace[name] = seqs
    try:
        namespace.update(namespace['CONSTANTS'])
    except KeyError:
        pass
    focus = namespace.get('focus')
    for (name, par) in model.parameters.control:
        try:
            if (focus is None) or (par is focus):
                namespace[par.name] = par
            else:
                namespace[par.name] = lambda *args, **kwargs: None
        except AttributeError:
            pass


def simulationstep(timestep):
    """
    Define a simulation time step size for testing purposes within a
    parameter control file.

    Argument:
        * timestep(:class:`~hydpy.core.timetools.Period`): Time step size.

    Using :func:`simulationstep` only affects the values of time dependent
    parameters, when `pub.timegrids.stepsize` is not defined.  It thus has
    no influence on usual hydpy simulations at all.  Use it just to check
    your parameter control files.  Write it in a line immediately behind
    the one calling :func:`parameterstep`.
    """
    if pub.options.warnsimulationstep:
        warnings.warn('Note that the applied function `simulationstep` is '
                      'inteded for testing purposes only.  When doing a '
                      'hydpy simulation, parameter values are initialized '
                      'based on the actual simulation time step as defined '
                      'under `pub.timegrids.stepsize` and the value given '
                      'to `simulationstep` is ignored.')
    parametertools.Parameter._simulationstep = timetools.Period(timestep)


def controlcheck(controldir='default', projectdir=None, controlfile=None):
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        if projectdir is None:
            projectdir = os.path.dirname(os.path.abspath(os.curdir))
            projectdir = os.path.split(projectdir)[-1]
        os.chdir(os.path.join('..', '..', '..'))
        controlpath = os.path.abspath(os.path.join('control',
                                                   projectdir,
                                                   controldir))
        initfile = os.path.split(namespace['__file__'])[-1]
        if controlfile is None:
            controlfile = initfile
        filepath = os.path.join(controlpath, controlfile)
        if not os.path.exists(filepath):
            raise IOError('The check of consistency between the control '
                          'parameter file %s and the initial condition file '
                          '%s failed.  The control parameter file does not '
                          'exist in directory %s.'
                          % (controlfile, initfile, controlpath))
        controlmanager = filetools.ControlManager()
        controlmanager.projectdirectory = projectdir
        controlmanager.selecteddirectory = controldir
        model = controlmanager.loadfile(controlfile)['model']
        model.parameters.update()
        namespace['model'] = model
        for name1 in ('states', 'logs'):
            subseqs = getattr(model.sequences, name1, None)
            if subseqs is not None:
                for (name2, seq) in subseqs:
                    namespace[name2] = seq


def printprogress_wrapper_generalized(*args, **kwargs):
    """Wrapper for HydPy methods to print when they start when they end.

    The wrapper is general in its function arguments.  When one uses the
    decorator :func:`printprogress`, the general arguments are replaced
    by the specific ones of the method to be wrapped.
    """
    import sys
    import time
    from hydpy import pub
    from hydpy.core.magictools import PrintStyle
    pub._printprogress_indentation += 4
    try:
        if pub.options.printprogress:
            with PrintStyle(color=34, font=1):
                print('\n%sHydPy method %s...'
                      % (' '*pub._printprogress_indentation,
                         printprogress_wrapped.__name__))
                print("%s    ...started at %s."
                      % (' '*pub._printprogress_indentation,
                         time.strftime("%X")))
        printprogress_wrapped(*args, **kwargs)
        if pub.options.printprogress:
            with PrintStyle(color=34, font=1):
                print("%s    ...ended at %s."
                      % (' '*pub._printprogress_indentation,
                         time.strftime("%X")))
    finally:
        pub._printprogress_indentation -= 4


def printprogress(printprogress_wrapped):
    """Decorator for wrapping HydPy methods with
    :func:`printprogress_wrapper_generalized`.

    Hopefully, all relevant attributes of the wrapped method are maintained.
    """
    signature = inspect.signature(printprogress_wrapped)
    lines = inspect.getsourcelines(printprogress_wrapper_generalized)[0]
    lines[0] = lines[0].replace('generalized', 'specialized')
    lines = [line.replace('(*args, **kwargs)', str(signature))
             for line in lines]
    exec(''.join(lines), locals(), globals())
    functools.update_wrapper(printprogress_wrapper_specialized,
                             printprogress_wrapped)
    return printprogress_wrapper_specialized


autodoctools.autodoc_module()
