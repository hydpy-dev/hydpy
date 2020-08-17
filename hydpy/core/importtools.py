# -*- coding: utf-8 -*-
"""This module implements features related to importing models.

The implemented tools are primarily designed for hiding model initialisation
routines from model users and for allowing writing readable doctests.
"""
# import...
# ...from standard library
import os
import importlib
import inspect
import types
import warnings
from typing import *
# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *


def parameterstep(timestep: Optional[timetools.PeriodConstrArg] = None) -> None:
    """Define a parameter time step size within a parameter control file.

    Function |parameterstep| should usually be applied in a line
    immediately behind the model import.  Defining the step size of
    time-dependent parameters is a prerequisite to access any
    model-specific parameter.

    Note that |parameterstep| implements some namespace magic utilizing
    the module |inspect|, which makes things a little complicated for
    framework developers, but it eases the definition of parameter
    control files for framework users.
    """
    if timestep is not None:
        parametertools.Parameter.parameterstep(timestep)
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        model = namespace['Model']()
        namespace['model'] = model
        if hydpy.pub.options.usecython and 'cythonizer' in namespace:
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
        model.parameters = prepare_parameters(namespace)
        model.sequences = prepare_sequences(namespace)
        namespace['parameters'] = model.parameters
        for pars in model.parameters:
            namespace[pars.name] = pars
        namespace['sequences'] = model.sequences
        for seqs in model.sequences:
            namespace[seqs.name] = seqs
        if 'Masks' in namespace:
            model.masks = namespace['Masks'](model)
            namespace['masks'] = model.masks
        for submodelclass in namespace['Model'].SUBMODELS:
            submodel = submodelclass(model)
            setattr(model, submodel.name, submodel)
    try:
        namespace.update(namespace['CONSTANTS'])
    except KeyError:
        pass
    focus = namespace.get('focus')
    for par in model.parameters.control:
        if (focus is None) or (par is focus):
            namespace[par.name] = par
        else:
            namespace[par.name] = lambda *args, **kwargs: None


def prepare_parameters(dict_: Dict[str, Any]) -> parametertools.Parameters:
    """Prepare a |Parameters| object based on the given dictionary
    information and return it."""
    cls_parameters = dict_.get('Parameters', parametertools.Parameters)
    return cls_parameters(dict_)


def prepare_sequences(dict_: Dict[str, Any]) -> sequencetools.Sequences:
    """Prepare a |Sequences| object based on the given dictionary
    information and return it."""
    cls_sequences = dict_.get('Sequences', sequencetools.Sequences)
    return cls_sequences(
        model=dict_.get('model'),
        cls_inlets=dict_.get('InletSequences'),
        cls_receivers=dict_.get('ReceiverSequences'),
        cls_inputs=dict_.get('InputSequences'),
        cls_fluxes=dict_.get('FluxSequences'),
        cls_states=dict_.get('StateSequences'),
        cls_logs=dict_.get('LogSequences'),
        cls_aides=dict_.get('AideSequences'),
        cls_outlets=dict_.get('OutletSequences'),
        cls_senders=dict_.get('SenderSequences'),
        cymodel=dict_.get('cymodel'),
        cythonmodule=dict_.get('cythonmodule')
    )


def reverse_model_wildcard_import() -> None:
    """Clear the local namespace from a model wildcard import.

    Calling this method should remove the critical imports into the local
    namespace due to the last wildcard import of a particular application
    model. In this manner, it secures the repeated preparation of different
    types of models via wildcard imports.  See the following example, on
    how it can be applied.

    >>> from hydpy import reverse_model_wildcard_import

    Assume you import the first version of HydPy-L-Land (|lland_v1|):

    >>> from hydpy.models.lland_v1 import *

    This import adds, for example, the collection class for handling control
    parameters of `lland_v1` into the local namespace:

    >>> print(ControlParameters(None).name)
    control

    Calling function |parameterstep| prepares, for example, the control
    parameter object of class |lland_control.NHRU|:

    >>> parameterstep('1d')
    >>> nhru
    nhru(?)

    Calling function |reverse_model_wildcard_import| tries to give its
    best to clear the local namespace (even from unexpected classes as
    the one we define now):

    >>> class Test:
    ...     __module__ = 'hydpy.models.lland_v1'
    >>> test = Test()

    >>> reverse_model_wildcard_import()

    >>> ControlParameters
    Traceback (most recent call last):
    ...
    NameError: name 'ControlParameters' is not defined

    >>> nhru
    Traceback (most recent call last):
    ...
    NameError: name 'nhru' is not defined

    >>> Test
    Traceback (most recent call last):
    ...
    NameError: name 'Test' is not defined

    >>> test
    Traceback (most recent call last):
    ...
    NameError: name 'test' is not defined
    """
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is not None:
        for subpars in model.parameters:
            for par in subpars:
                namespace.pop(par.name, None)
                namespace.pop(type(par).__name__, None)
            namespace.pop(subpars.name, None)
            namespace.pop(type(subpars).__name__, None)
        for subseqs in model.sequences:
            for seq in subseqs:
                namespace.pop(seq.name, None)
                namespace.pop(type(seq).__name__, None)
            namespace.pop(subseqs.name, None)
            namespace.pop(type(subseqs).__name__, None)
        for name in ('parameters', 'sequences', 'masks', 'model',
                     'Parameters', 'Sequences', 'Masks', 'Model',
                     'cythonizer', 'cymodel', 'cythonmodule'):
            namespace.pop(name, None)
        for key in list(namespace.keys()):
            try:
                if namespace[key].__module__ == model.__module__:
                    del namespace[key]
            except AttributeError:
                pass


def prepare_model(module: Union[types.ModuleType, str],
                  timestep: Optional[timetools.PeriodConstrArg] = None):
    """Prepare and return the model of the given module.

    In usual *HydPy* projects, each control file prepares an individual
    model instance only, which allows for "polluting" the namespace with
    different model attributes.   There is no danger of name conflicts,
    as long as we do not perform other (wildcard) imports.

    However, there are situations where we need to load different models
    into the same namespace.  Then it is advisable to use function
    |prepare_model|, which returns a reference to the model
    and nothing else.

    See the documentation of |dam_v001| on how to apply function
    |prepare_model| properly.
    """
    if timestep is not None:
        parametertools.Parameter.parameterstep(timetools.Period(timestep))
    try:
        model = module.Model()
    except AttributeError:
        module = importlib.import_module(f'hydpy.models.{module}')
        model = module.Model()
    if hydpy.pub.options.usecython and hasattr(module, 'cythonizer'):
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
    model.parameters = prepare_parameters(dict_)
    model.sequences = prepare_sequences(dict_)
    if hasattr(module, 'Masks'):
        model.masks = module.Masks(model)
    for submodelclass in module.Model.SUBMODELS:
        submodel = submodelclass(model)
        setattr(model, submodel.name, submodel)
    return model


def simulationstep(timestep) -> None:
    """ Define a simulation time step size for testing purposes within a
    parameter control file.

    Using |simulationstep| only affects the values of time-dependent
    parameters, when `pub.timegrids.stepsize` is not defined.  It thus
    does not influence usual hydpy simulations at all.  Use it to check
    your parameter control files.  Write it in a line immediately behind
    the line calling function |parameterstep|.

    To clarify its purpose, function |simulationstep| raises a warning
    when executed from within a control file:

    .. testsetup::

        >>> from hydpy import pub
        >>> del pub.timegrids

    >>> from hydpy import pub
    >>> with pub.options.warnsimulationstep(True):
    ...     from hydpy.models.hland_v1 import *
    ...     parameterstep('1d')
    ...     simulationstep('1h')
    Traceback (most recent call last):
    ...
    UserWarning: Note that the applied function `simulationstep` is intended \
for testing purposes only.  When doing a HydPy simulation, parameter values \
are initialised based on the actual simulation time step as defined under \
`pub.timegrids.stepsize` and the value given to `simulationstep` is ignored.
    >>> k4.simulationstep
    Period('1h')
    """
    if hydpy.pub.options.warnsimulationstep:
        warnings.warn(
            'Note that the applied function `simulationstep` is intended for '
            'testing purposes only.  When doing a HydPy simulation, parameter '
            'values are initialised based on the actual simulation time step '
            'as defined under `pub.timegrids.stepsize` and the value given '
            'to `simulationstep` is ignored.')
    parametertools.Parameter.simulationstep(timestep)


def controlcheck(
        controldir: str = 'default',
        projectdir: Optional[str] = None,
        controlfile: Optional[str] = None,
        firstdate: Optional[timetools.DateConstrArg] = None,
        stepsize: Optional[timetools.PeriodConstrArg] = None) -> None:
    """Define the corresponding control file within a condition file.

    Function |controlcheck| serves similar purposes as function
    |parameterstep|.  It is the reason why one can interactively
    access the state and the log sequences within condition files
    as `land_dill.py` of the example project `LahnH`.  It is called
    `controlcheck` due to its feature to check for possible inconsistencies
    between control and condition files.  The following test, where we
    write a number of soil moisture values (|hland_states.SM|) into
    condition file `land_dill.py`, which does not agree with the number
    of hydrological response units (|hland_control.NmbZones|) defined in
    control file `land_dill.py`, verifies that this, in fact, works within
    a separate Python process:

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> import os
    >>> from hydpy import run_subprocess, TestIO
    >>> cwd = os.path.join('LahnH', 'conditions', 'init_1996_01_01_00_00_00')
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.chdir(cwd)
    ...     with open('land_dill.py') as file_:
    ...         lines = file_.readlines()
    ...     lines[10:12] = 'sm(185.13164, 181.18755)', ''
    ...     with open('land_dill.py', 'w') as file_:
    ...         _ = file_.write('\\n'.join(lines))
    ...     print()
    ...     result = run_subprocess('hyd.py exec_script land_dill.py')
    <BLANKLINE>
    ...
    While trying to set the value(s) of variable `sm`, the following error \
occurred: While trying to convert the value(s) `(185.13164, 181.18755)` to \
a numpy ndarray with shape `(12,)` and type `float`, the following error \
occurred: could not broadcast input array from shape (2) into shape (12)
    ...

    With a little trick, we can fake to be "inside" condition file
    `land_dill.py`.  Calling |controlcheck| then, for example, prepares the
    shape of sequence |hland_states.Ic| as specified by the value of parameter
    |hland_control.NmbZones| given in the corresponding control file:

    >>> from hydpy.models.hland_v1 import *
    >>> __file__ = 'land_dill.py'
    >>> with TestIO():
    ...     os.chdir(cwd)
    ...     controlcheck()
    >>> ic.shape
    (12,)

    In the above example, we use the default names for the project directory
    (the one containing the executed condition file) and the control
    directory (`default`).  The following example shows how to change them:

    >>> del model
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.chdir(cwd)
    ...     controlcheck(projectdir='somewhere', controldir='nowhere')
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to load the control file `land_dill.py` \
from directory `...hydpy/tests/iotesting/somewhere/control/nowhere`, \
the following error occurred: ...

    For some models, the suitable states may depend on the initialisation
    date.  One example is the interception storage (|lland_states.Inzp|) of
    application model |lland_v1|, which should not exceed the interception
    capacity (|lland_derived.KInz|).  However, |lland_derived.KInz| itself
    depends on the leaf area index parameter |lland_control.LAI|, which
    offers varying values both for different land-use types and months.
    Hence, one can assign higher values to state |lland_states.Inzp| during
    periods with high leaf area indices than during periods with small
    leaf area indices.

    To show the related functionalities, we first replace the |hland_v1|
    application model of element `land_dill` with a |lland_v1| model object,
    define some of its parameter values, and write its control and condition
    files.  Note that the
    |lland_control.LAI| value of the only relevant land-use
    (|lland_constants.ACKER|) is 0.5 during January and 5.0 during July:

    >>> from hydpy import HydPy, prepare_model, pub
    >>> from hydpy.models.lland_v1 import ACKER
    >>> pub.timegrids = '2000-06-01', '2000-07-01', '1d'
    >>> with TestIO():
    ...     hp = HydPy('LahnH')
    ...     hp.prepare_network()
    ...     land_dill = hp.elements['land_dill']
    ...     with pub.options.usedefaultvalues(True):
    ...         land_dill.model = prepare_model('lland_v1')
    ...         control = land_dill.model.parameters.control
    ...         control.nhru(2)
    ...         control.ft(1.0)
    ...         control.fhru(0.5)
    ...         control.hnn(100.0)
    ...         control.lnk(ACKER)
    ...         control.lai.acker_jan = 0.5
    ...         control.lai.acker_jul = 5.0
    ...         land_dill.model.parameters.update()
    ...         land_dill.model.sequences.states.inzp(1.0)
    ...     land_dill.model.parameters.save_controls()
    ...     land_dill.model.sequences.save_conditions()

    Unfortunately, state |lland_states.Inzp| does not define a |trim| method
    taking the actual value of parameter |lland_derived.KInz| into account
    (due to compatibility with the original LARSIM model).  As an auxiliary
    solution, we define such a function within the `land_dill.py` condition
    file (and additionally modify some warning settings in favour of the
    next examples):

    >>> cwd = os.path.join('LahnH', 'conditions', 'init_2000_07_01_00_00_00')
    >>> with TestIO():
    ...     os.chdir(cwd)
    ...     with open('land_dill.py') as file_:
    ...         lines = file_.readlines()
    ...     with open('land_dill.py', 'w') as file_:
    ...         file_.writelines([
    ...             'from hydpy import pub\\n',
    ...             'pub.options.warnsimulationstep = False\\n',
    ...             'import warnings\\n',
    ...             'warnings.filterwarnings('
    ...                 '"error", message="For variable")\\n'])
    ...         file_.writelines(lines[:5])
    ...         file_.writelines([
    ...             'from hydpy.core.variabletools import trim as trim_\\n',
    ...             'def trim(self, lower=None, upper=None):\\n',
    ...             '    der = self.subseqs.seqs.model.parameters.derived\\n',
    ...             '    trim_(self, 0.0, der.kinz.acker[der.moy[0]])\\n',
    ...             'type(inzp).trim = trim\\n'])
    ...         file_.writelines(lines[5:])

    Now, executing the condition file (and thereby calling function
    |controlcheck|) does not raise any warnings due to extracting the
    initialisation date from the name of the condition directory:

    >>> with TestIO():
    ...     os.chdir(cwd)
    ...     result = run_subprocess('hyd.py exec_script land_dill.py')

    If the directory name does imply the initialisation date to be within
    January 2000 instead of July 2000, we correctly get the following warning:

    >>> cwd_old = cwd
    >>> cwd_new = os.path.join('LahnH', 'conditions', 'init_2000_01_01')
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.rename(cwd_old, cwd_new)
    ...     os.chdir(cwd_new)
    ...     result = run_subprocess('hyd.py exec_script land_dill.py')
    Invoking hyd.py with arguments `exec_script, land_dill.py` resulted \
in the following error:
    For variable `inzp` at least one value needed to be trimmed.  \
The old and the new value(s) are `1.0, 1.0` and `0.1, 0.1`, respectively.
    ...

    One can define an alternative initialisation date via argument
    `firstdate`:

    >>> text_old = ('controlcheck(projectdir="LahnH", '
    ...             'controldir="default", stepsize="1d")')
    >>> text_new = ('controlcheck(projectdir="LahnH", controldir="default", '
    ...             'firstdate="2100-07-15", stepsize="1d")')
    >>> with TestIO():
    ...     os.chdir(cwd_new)
    ...     with open('land_dill.py') as file_:
    ...         text = file_.read()
    ...     text = text.replace(text_old, text_new)
    ...     with open('land_dill.py', 'w') as file_:
    ...         _ = file_.write(text)
    ...     result = run_subprocess('hyd.py exec_script land_dill.py')

    Default condition directory names do not contain any information about
    the simulation step size.  Hence, one needs to define it explicitly for
    all application modelsrelying on the functionalities of class |Indexer|:

    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.chdir(cwd_new)
    ...     with open('land_dill.py') as file_:
    ...         text = file_.read()
    ...     text = text.replace('stepsize="1d"', '')
    ...     with open('land_dill.py', 'w') as file_:
    ...         _ = file_.write(text)
    ...     result = run_subprocess('hyd.py exec_script land_dill.py')
    Invoking hyd.py with arguments `exec_script, land_dill.py` resulted \
in the following error:
    To apply function `controlcheck` requires time information for some \
model types.  Please define the `Timegrids` object of module `pub` manually \
or pass the required information (`stepsize` and eventually `firstdate`) \
as function arguments.
    ...

    The same error occurs we do not use the argument `firstdate` to define
    the initialisation time point, and method |controlcheck| cannot
    extract it from the directory name:

    >>> cwd_old = cwd_new
    >>> cwd_new = os.path.join('LahnH', 'conditions', 'init')
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.rename(cwd_old, cwd_new)
    ...     os.chdir(cwd_new)
    ...     with open('land_dill.py') as file_:
    ...         text = file_.read()
    ...     text = text.replace('firstdate="2100-07-15"', 'stepsize="1d"')
    ...     with open('land_dill.py', 'w') as file_:
    ...         _ = file_.write(text)
    ...     result = run_subprocess('hyd.py exec_script land_dill.py')
    Invoking hyd.py with arguments `exec_script, land_dill.py` resulted \
in the following error:
    To apply function `controlcheck` requires time information for some \
model types.  Please define the `Timegrids` object of module `pub` manually \
or pass the required information (`stepsize` and eventually `firstdate`) \
as function arguments.
    ...

    Note that the functionalities of function |controlcheck| do not come
    into action if there is a `model` variable in the namespace, which is
    the case when a condition file is executed within the context of a
    complete *HydPy* project.
    """
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        if not controlfile:
            controlfile = os.path.split(namespace['__file__'])[-1]
        if projectdir is None:
            projectdir = (
                os.path.split(
                    os.path.split(
                        os.path.split(os.getcwd())[0])[0])[-1])
        dirpath = os.path.abspath(os.path.join(
            '..', '..', '..', projectdir, 'control', controldir))
        if hydpy.pub.get('timegrids') is None and stepsize is not None:
            if firstdate is None:
                try:
                    firstdate = timetools.Date.from_string(
                        os.path.split(os.getcwd())[-1].partition('_')[-1])
                except (ValueError, TypeError):
                    pass
            else:
                firstdate = timetools.Date(firstdate)
            if firstdate is not None:
                stepsize = timetools.Period(stepsize)
                hydpy.pub.timegrids = (
                    firstdate, firstdate + 1000 * stepsize, stepsize)

        class CM(filetools.ControlManager):
            """Tempory |ControlManager| class."""
            currentpath = dirpath

        cwd = os.getcwd()
        try:
            os.chdir(dirpath)
            model = CM().load_file(filename=controlfile)['model']
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to load the control file `{controlfile}` '
                f'from directory `{objecttools.repr_(dirpath)}`')
        finally:
            os.chdir(cwd)
        try:
            model.parameters.update()
        except exceptiontools.AttributeNotReady:
            raise RuntimeError(
                'To apply function `controlcheck` requires time '
                'information for some model types.  Please define '
                'the `Timegrids` object of module `pub` manually '
                'or pass the required information (`stepsize` and '
                'eventually `firstdate`) as function arguments.')

        namespace['model'] = model
        for name in ('states', 'logs'):
            subseqs = getattr(model.sequences, name, None)
            if subseqs is not None:
                for seq in subseqs:
                    namespace[seq.name] = seq
