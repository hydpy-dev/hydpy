# -*- coding: utf-8 -*-
"""This module implements features related to importing models.

The implemented tools are primarily designed hiding model initialization
routines from model users and for allowing writing readable doctests.
"""
# import...
# ...from the Python standard library
from __future__ import division, print_function
import os
import inspect
import warnings
# ...from HydPy
from hydpy import pub
from hydpy.core import filetools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import timetools


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
    if pub.options.warnsimulationstep:
        warnings.warn(
            'Note that the applied function `simulationstep` is inteded for '
            'testing purposes only.  When doing a hydpy simulation, parameter '
            'values are initialized based on the actual simulation time step '
            'as defined under `pub.timegrids.stepsize` and the value given '
            'to `simulationstep` is ignored.')
    parametertools.Parameter.simulationstep(timetools.Period(timestep))


def controlcheck(controldir='default', projectdir=None, controlfile=None):
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
