# -*- coding: utf-8 -*-
"""This module implements features related to importing models.

The implemented tools are primarily designed for hiding model initialisation routines
from model users and for allowing writing readable doctests.
"""
# import...
# ...from standard library
from __future__ import annotations
import contextlib
import os
import importlib
import inspect
import types
import warnings

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import masktools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *

TM = TypeVar("TM", bound="modeltools.Model")
TI = TypeVar("TI", bound="modeltools.SubmodelInterface")

__HYDPY_MODEL_LOCALS__ = "__hydpy_model_locals__"


def parameterstep(timestep: Optional[timetools.PeriodConstrArg] = None) -> None:
    """Define a parameter time step size within a parameter control file.

    Function |parameterstep| should usually be applied in a line immediately behind the
    model import or behind calling |simulationstep|.  Defining the step size of
    time-dependent parameters is a prerequisite to accessing any model-specific
    parameter.

    Note that |parameterstep| implements some namespace magic utilising the module
    |inspect|, which complicates things for framework developers.  Still, it eases the
    definition of parameter control files for framework users.
    """
    if timestep is not None:
        hydpy.pub.options.parameterstep = timestep
    frame = inspect.currentframe()
    assert (frame is not None) and (frame.f_back is not None)
    namespace = frame.f_back.f_locals
    model = namespace.get("model")
    if model is None:
        model = namespace["Model"]()
        namespace["model"] = model
        if hydpy.pub.options.usecython and "cythonizer" in namespace:
            cythonizer = namespace["cythonizer"]
            namespace["cythonmodule"] = cythonizer.cymodule
            model.cymodel = cythonizer.cymodule.Model()
            namespace["cymodel"] = model.cymodel
            if hasattr(cythonizer.cymodule, "Parameters"):
                model.cymodel.parameters = cythonizer.cymodule.Parameters()
            model.cymodel.sequences = cythonizer.cymodule.Sequences()
            for numpars_name in ("NumConsts", "NumVars"):
                if hasattr(cythonizer.cymodule, numpars_name):
                    numpars_new = getattr(cythonizer.cymodule, numpars_name)()
                    numpars_old = getattr(model, numpars_name.lower())
                    for name_numpar, numpar in vars(numpars_old).items():
                        setattr(numpars_new, name_numpar, numpar)
                    setattr(model.cymodel, numpars_name.lower(), numpars_new)
            for name in dir(model.cymodel):
                if (not name.startswith("_")) and hasattr(model, name):
                    setattr(model, name, getattr(model.cymodel, name))
        model.parameters = prepare_parameters(namespace)
        model.sequences = prepare_sequences(namespace)
        namespace.pop("cymodel", None)
        namespace.pop("cythonmodule", None)
        if "Masks" in namespace:
            model.masks = namespace["Masks"]()
        else:
            model.masks = masktools.Masks()
        for submodelclass in namespace["Model"].SUBMODELS:
            submodel = submodelclass(model)
            setattr(model, submodel.name, submodel)
        del namespace["model"]
    _add_locals_to_namespace(model=model, namespace=namespace)


def _add_locals_to_namespace(
    model: modeltools.Model, namespace: Dict[str, Any]
) -> None:
    new_locals: Dict[str, Any] = namespace.get("CONSTANTS", {}).copy()
    new_locals["model"] = model
    new_locals["parameters"] = model.parameters
    for pars in model.parameters:
        new_locals[pars.name] = pars
    new_locals["sequences"] = model.sequences
    for seqs in model.sequences:
        new_locals[seqs.name] = seqs
    new_locals["masks"] = model.masks
    focus = namespace.get("focus")
    for par in model.parameters.control:
        if (focus is None) or (par is focus):
            new_locals[par.name] = par
        else:
            new_locals[par.name] = lambda *args, **kwargs: None
    namespace[__HYDPY_MODEL_LOCALS__] = new_locals
    namespace.update(new_locals)


def prepare_parameters(dict_: Dict[str, Any]) -> parametertools.Parameters:
    """Prepare a |Parameters| object based on the given dictionary
    information and return it."""
    cls_parameters = dict_.get("Parameters", parametertools.Parameters)
    return cls_parameters(dict_)


def prepare_sequences(dict_: Dict[str, Any]) -> sequencetools.Sequences:
    """Prepare a |Sequences| object based on the given dictionary
    information and return it."""
    cls_sequences = dict_.get("Sequences", sequencetools.Sequences)
    return cls_sequences(
        model=dict_.get("model"),
        cls_inlets=dict_.get("InletSequences"),
        cls_receivers=dict_.get("ReceiverSequences"),
        cls_inputs=dict_.get("InputSequences"),
        cls_factors=dict_.get("FactorSequences"),
        cls_fluxes=dict_.get("FluxSequences"),
        cls_states=dict_.get("StateSequences"),
        cls_logs=dict_.get("LogSequences"),
        cls_aides=dict_.get("AideSequences"),
        cls_outlets=dict_.get("OutletSequences"),
        cls_senders=dict_.get("SenderSequences"),
        cymodel=dict_.get("cymodel"),
        cythonmodule=dict_.get("cythonmodule"),
    )


def reverse_model_wildcard_import() -> None:
    """Clear the local namespace from a model wildcard import.

    This method should remove the critical imports into the local namespace due to the
    last wildcard import of a particular application model. In this manner, it secures
    the repeated preparation of different types of models via wildcard imports.  See
    the following example of to apply it.

    >>> from hydpy import reverse_model_wildcard_import

    Assume you import the first version of HydPy-L-Land (|lland_v1|):

    >>> from hydpy.models.lland_v1 import *

    This import adds, for example, the collection class for handling control parameters
    of `lland_v1` into the local namespace:

    >>> print(ControlParameters(None).name)
    control

    Function |parameterstep| prepares, for example, the control parameter object of
    class |lland_control.NHRU|:

    >>> parameterstep("1d")
    >>> nhru
    nhru(?)

    Function |reverse_model_wildcard_import| tries to clear the local namespace (even
    from unexpected classes like the one we define now):

    >>> class Test:
    ...     __module__ = "hydpy.models.lland_v1"
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
    frame = inspect.currentframe()
    assert (frame is not None) and (frame.f_back is not None)
    namespace = frame.f_back.f_locals
    model = namespace.get("model")
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
        for name in (
            "parameters",
            "sequences",
            "masks",
            "model",
            "Parameters",
            "Sequences",
            "Masks",
            "Model",
            "cythonizer",
            "cymodel",
            "cythonmodule",
        ):
            namespace.pop(name, None)
        for key in tuple(namespace):
            try:
                if namespace[key].__module__ == model.__module__:
                    del namespace[key]
            except AttributeError:
                pass
        namespace[__HYDPY_MODEL_LOCALS__] = {}


def prepare_model(
    module: Union[types.ModuleType, str],
    timestep: Optional[timetools.PeriodConstrArg] = None,
) -> modeltools.Model:
    """Prepare and return the model of the given module.

    In usual *HydPy* projects, each control file only prepares an individual model
    instance, which allows for "polluting" the namespace with different model
    attributes.  There is no danger of name conflicts as long as we do not perform
    other (wildcard) imports.

    However, there are situations where we need to load different models into the same
    namespace.  Then it is advisable to use function |prepare_model|, which returns a
    reference to the model and nothing else.

    See the documentation of |dam_v001| on how to apply function |prepare_model|
    properly.
    """
    if timestep is not None:
        hydpy.pub.options.parameterstep = timetools.Period(timestep)
    if isinstance(module, str):
        module = importlib.import_module(f"hydpy.models.{module}")
    model = module.Model()
    assert isinstance(model, modeltools.Model)
    if hydpy.pub.options.usecython and hasattr(module, "cythonizer"):
        cymodule = module.cythonizer.cymodule
        cymodel = cymodule.Model()
        if hasattr(cymodule, "Parameters"):
            cymodel.parameters = cymodule.Parameters()
        cymodel.sequences = cymodule.Sequences()
        model.cymodel = cymodel
        for numpars_name in ("NumConsts", "NumVars"):
            if hasattr(cymodule, numpars_name):
                numpars_new = getattr(cymodule, numpars_name)()
                numpars_old = getattr(model, numpars_name.lower())
                for name_numpar, numpar in vars(numpars_old).items():
                    setattr(numpars_new, name_numpar, numpar)
                setattr(cymodel, numpars_name.lower(), numpars_new)
        for name in dir(cymodel):
            if (not name.startswith("_")) and hasattr(model, name):
                setattr(model, name, getattr(cymodel, name))
        dict_ = {"cythonmodule": cymodule, "cymodel": cymodel}
    else:
        dict_ = {}
    dict_.update(vars(module))
    dict_["model"] = model
    model.parameters = prepare_parameters(dict_)
    model.sequences = prepare_sequences(dict_)
    if hasattr(module, "Masks"):
        model.masks = module.Masks()
    else:
        model.masks = masktools.Masks()
    for submodelclass in module.Model.SUBMODELS:
        submodel = submodelclass(model)
        setattr(model, submodel.name, submodel)
    return model


class _DoctestAdder:
    wrapped: object

    def __set_name__(self, objtype: Type[modeltools.Model], name: str) -> None:
        assert (module := inspect.getmodule(objtype)) is not None
        test = getattr(module, "__test__", {})
        test[f"{objtype.__name__}.{self.wrapped.__name__}"] = self.__doc__
        module.__dict__["__test__"] = test


def prepare_submodel(
    submodelinterface: Type[TI],
    *methods: Callable[[NoReturn, NoReturn], None],
    landtype_constants: Optional[parametertools.Constants] = None,
    soiltype_constants: Optional[parametertools.Constants] = None,
    landtype_refindices: Optional[Type[parametertools.NameParameter]] = None,
    soiltype_refindices: Optional[Type[parametertools.NameParameter]] = None,
    refweights: Optional[Type[parametertools.Parameter]] = None,
) -> Callable[[Callable[[TM, TI], None]], SubmodelAdder[TM, TI]]:
    """Wrap a model-specific method for preparing a submodel into a |SubmodelAdder|
    instance."""

    def _prepare_submodel(wrapped: Callable[[TM, TI], None]) -> SubmodelAdder[TM, TI]:
        return SubmodelAdder[TM, TI](
            wrapped=wrapped,
            submodelinterface=submodelinterface,
            methods=methods,
            landtype_constants=landtype_constants,
            soiltype_constants=soiltype_constants,
            landtype_refindices=landtype_refindices,
            soiltype_refindices=soiltype_refindices,
            refweights=refweights,
        )

    return _prepare_submodel


class SubmodelAdder(_DoctestAdder, Generic[TM, TI]):
    """Wrapper that extends the functionality of model-specific methods for preparing
    submodels.

    |SubmodelAdder| offers the user-relevant feature of preparing submodels with the
    `with` statement.  When entering the `with` block, |SubmodelAdder| uses the given
    string or module to initialise the desired application model and hands it as a
    submodel to the model-specific method, which usually sets some control parameters
    based on the main model's configuration.  Next, |SubmodelAdder| makes many
    attributes of the submodel directly available, most importantly, the instances of
    the remaining control parameter, so that users can set their values as conveniently
    as the ones of the main model ones.  As long as no name conflicts occur, all main
    model parameter instances are also accessible:

    >>> from hydpy.models.lland_v1 import *
    >>> parameterstep()
    >>> nhru(2)
    >>> ft(10.0)
    >>> fhru(0.2, 0.8)
    >>> lnk(ACKER, MISCHW)
    >>> with model.add_petmodel_v1("evap_tw2002"):
    ...     nhru
    ...     nmbhru
    ...     hruarea
    ...     altitude
    nhru(2)
    nmbhru(2)
    hruarea(2.0, 8.0)
    altitude(?)

    After leaving the `with` block, the submodel's parameters are no longer available:

    >>> nhru
    nhru(2)
    >>> nmbhru
    Traceback (most recent call last):
    ...
    NameError: name 'nmbhru' is not defined

    Additionally, |SubmodelAdder| checks if the selected application model follows the
    appropriate interface:

    >>> with model.add_petmodel_v1("ga_garto_submodel1"):
    ...     ...
    Traceback (most recent call last):
    ...
    TypeError: While trying to add a submodule to the main model `lland_v1`, the \
following error occurred: Submodel `ga_garto_submodel1` does not comply with the \
`PETModel_V1` interface.

    Each |SubmodelAdder| instance provides access to the appropriate interface and the
    interface methods the wrapped method uses (this information helps framework
    developers figure out which parameters the submodel prepares on its own):

    >>> model.add_petmodel_v1.submodelinterface.__name__
    'PETModel_V1'
    >>> for method in model.add_petmodel_v1.methods:
    ...     method.__name__
    'prepare_nmbzones'
    'prepare_zonetypes'
    'prepare_subareas'
    """

    wrapped: Callable[[TM, TI], None]
    """The wrapped, model-specific method for preparing some control parameters 
    automatically."""
    submodelinterface: Type[TI]
    """The relevant submodel interface."""
    methods: Tuple[Callable[[NoReturn, NoReturn], None], ...]
    """The submodel interface methods the wrapped method uses."""
    landtype_refindices: Optional[Type[parametertools.NameParameter]]
    soiltype_refindices: Optional[Type[parametertools.NameParameter]]
    refweights: Optional[Type[parametertools.Parameter]]

    _sharable_configuration: SharableConfiguration

    _model: Optional[TM]

    def __init__(
        self,
        wrapped: Callable[[TM, TI], None],
        submodelinterface: Type[TI],
        methods: Iterable[Callable[[NoReturn, NoReturn], None]],
        landtype_constants: Optional[parametertools.Constants],
        soiltype_constants: Optional[parametertools.Constants],
        landtype_refindices: Optional[Type[parametertools.NameParameter]],
        soiltype_refindices: Optional[Type[parametertools.NameParameter]],
        refweights: Optional[Type[parametertools.Parameter]],
    ) -> None:
        self.wrapped = wrapped
        self.submodelinterface = submodelinterface
        self.methods = tuple(methods)
        self._sharable_configuration = {
            "landtype_constants": landtype_constants,
            "soiltype_constants": soiltype_constants,
            "landtype_refindices": None,
            "soiltype_refindices": None,
            "refweights": None,
        }
        self._landtype_refindices = landtype_refindices
        self._soiltype_refindices = soiltype_refindices
        self._refweights = refweights
        self._model = None
        self.__doc__ = wrapped.__doc__

    def __get__(
        self, obj: Optional[TM], type_: Type[modeltools.Model]
    ) -> SubmodelAdder[TM, TI]:
        if obj is not None:
            self._model = obj
        return self

    @contextlib.contextmanager
    def __call__(
        self, module: Union[types.ModuleType, str], update: bool = True
    ) -> Generator[None, None, None]:
        try:
            if isinstance(module, str):
                module = importlib.import_module(f"hydpy.models.{module}")
            if not issubclass(submodeltype := module.Model, self.submodelinterface):
                raise TypeError(
                    f"Submodel `{module.__name__.rpartition('.')[2]}` does not comply "
                    f"with the `{self.submodelinterface.__name__}` interface."
                )
            shared = self._sharable_configuration
            assert (model := self._model) is not None
            control = model.parameters.control
            if (ltr := self._landtype_refindices) is not None:
                shared["landtype_refindices"] = getattr(control, ltr.name)
            if (str_ := self._soiltype_refindices) is not None:
                shared["landtype_refindices"] = getattr(control, str_.name)
            if (rw := self._refweights) is not None:
                shared["refweights"] = getattr(control, rw.name)
            with submodeltype.share_configuration(shared):
                submodel = prepare_model(module)
                assert isinstance(submodel, self.submodelinterface)
                self.wrapped(model, submodel)
                assert (
                    ((frame1 := inspect.currentframe()) is not None)
                    and ((frame2 := frame1.f_back) is not None)
                    and ((frame3 := frame2.f_back) is not None)
                )
                namespace = frame3.f_locals
                old_locals = namespace.get(__HYDPY_MODEL_LOCALS__, {})
                try:
                    _add_locals_to_namespace(submodel, namespace)
                    yield
                    if update:
                        submodel.parameters.update()
                finally:
                    new_locals = namespace[__HYDPY_MODEL_LOCALS__]
                    for name in new_locals:
                        namespace.pop(name, None)
                    namespace.update(old_locals)
                    namespace[__HYDPY_MODEL_LOCALS__] = old_locals
        except BaseException:
            assert (model := self._model) is not None
            objecttools.augment_excmessage(
                f"While trying to add a submodule to the main model `{model.name}`"
            )


def define_targetparameter(
    parameter: Type[parametertools.Parameter],
) -> Callable[[Callable[Concatenate[TM, P], None]], TargetParameterUpdater[TM, P]]:
    """Wrap a submodel-specific method that allows the main model to set the value
    of a single control parameter of the submodel into a |TargetParameterUpdater|
    instance."""

    def _select_parameter(
        wrapped: Callable[Concatenate[TM, P], None]
    ) -> TargetParameterUpdater[TM, P]:
        return TargetParameterUpdater[TM, P](wrapped, parameter)

    return _select_parameter


class TargetParameterUpdater(_DoctestAdder, Generic[TM, P]):
    """Wrapper that extends the functionality of a submodel-specific method that allows
    the main model to set the value of a single control parameter of the submodel.

    When calling a |TargetParameterUpdater| instance, it calls the wrapped method with
    unmodified arguments, so that model users might not even realise the
    |TargetParameterUpdater| instance exists:

    >>> from hydpy import prepare_model
    >>> model = prepare_model("evap_tw2002")
    >>> model.prepare_nmbzones(3)
    >>> model.parameters.control.nmbhru
    nmbhru(3)

    However, each |TargetParameterUpdater| instance provides other framework functions
    access to the target control parameter type (the one the wrapped method prepares):

    >>> model.prepare_nmbzones.targetparameter.__name__
    'NmbHRU'
    """

    wrapped: Callable[Concatenate[TM, P], None]
    """The wrapped, submodel-specific method for setting the value of a single control 
    parameter."""
    targetparameter: Type[parametertools.Parameter]
    """The control parameter the wrapped method modifies."""

    _model: Optional[TM]

    def __init__(
        self,
        wrapped: Callable[Concatenate[TM, P], None],
        targetparameter: Type[parametertools.Parameter],
    ) -> None:
        self.wrapped = wrapped
        self.targetparameter = targetparameter
        self.__doc__ = wrapped.__doc__

    def __get__(
        self, obj: Optional[TM], type_: Type[modeltools.Model]
    ) -> TargetParameterUpdater[TM, P]:
        if obj is not None:
            self._model = obj
        return self

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        assert (model := self._model) is not None
        self.wrapped(model, *args, **kwargs)


def simulationstep(timestep: timetools.PeriodConstrArg) -> None:
    """Define a simulation time step size within a parameter control file for testing
    purposes.

    Using |simulationstep| only affects the values of time-dependent parameters when
    `pub.timegrids.stepsize` is not defined.  It thus does not influence usual *HydPy*
    simulations at all.  Use it to check your parameter control files.  Write it in a
    line immediately behind the model import.

    To clarify its purpose, function |simulationstep| raises a warning when executed
    from within a control file:

    .. testsetup::

        >>> from hydpy import pub
        >>> del pub.timegrids

    >>> from hydpy import pub
    >>> with pub.options.warnsimulationstep(True):
    ...     from hydpy.models.hland_v1 import *
    ...     simulationstep("1h")
    ...     parameterstep("1d")
    Traceback (most recent call last):
    ...
    UserWarning: Note that the applied function `simulationstep` is intended \
for testing purposes only.  When doing a HydPy simulation, parameter values \
are initialised based on the actual simulation time step as defined under \
`pub.timegrids.stepsize` and the value given to `simulationstep` is ignored.

    >>> pub.options.simulationstep
    Period("1h")
    """
    if hydpy.pub.options.warnsimulationstep:
        warnings.warn(
            "Note that the applied function `simulationstep` is intended for "
            "testing purposes only.  When doing a HydPy simulation, parameter "
            "values are initialised based on the actual simulation time step "
            "as defined under `pub.timegrids.stepsize` and the value given "
            "to `simulationstep` is ignored."
        )
    hydpy.pub.options.simulationstep = timestep


def controlcheck(
    controldir: str = "default",
    projectdir: Optional[str] = None,
    controlfile: Optional[str] = None,
    firstdate: Optional[timetools.DateConstrArg] = None,
    stepsize: Optional[timetools.PeriodConstrArg] = None,
) -> None:
    """Define the corresponding control file within a condition file.

    Function |controlcheck| serves similar purposes as function |parameterstep|.  It is
    why one can interactively access the state and the log sequences within condition
    files as `land_dill.py` of the example project `LahnH`.  It is called
    `controlcheck` due to its feature to check for possible inconsistencies between
    control and condition files.  The following test, where we write several soil
    moisture values (|hland_states.SM|) into condition file `land_dill.py`, which does
    not agree with the number of hydrological response units (|hland_control.NmbZones|)
    defined in control file `land_dill.py`, verifies that this works within a separate
    Python process:

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> import os
    >>> from hydpy import run_subprocess, TestIO
    >>> cwd = os.path.join("LahnH", "conditions", "init_1996_01_01_00_00_00")
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.chdir(cwd)
    ...     with open("land_dill.py") as file_:
    ...         lines = file_.readlines()
    ...     lines[10:12] = "sm(185.13164, 181.18755)", ""
    ...     with open("land_dill.py", "w") as file_:
    ...         _ = file_.write("\\n".join(lines))
    ...     print()
    ...     result = run_subprocess("hyd.py exec_script land_dill.py")
    <BLANKLINE>
    ...
    While trying to set the value(s) of variable `sm`, the following error occurred: \
While trying to convert the value(s) `(185.13164, 181.18755)` to a numpy ndarray with \
shape `(12,)` and type `float`, the following error occurred: could not broadcast \
input array from shape (2...) into shape (12...)
    ...

    With a little trick, we can fake to be "inside" condition file `land_dill.py`.
    Calling |controlcheck| then, for example, prepares the shape of sequence
    |hland_states.Ic| as specified by the value of parameter |hland_control.NmbZones|
    given in the corresponding control file:

    >>> from hydpy.models.hland_v1 import *
    >>> __file__ = "land_dill.py"
    >>> with TestIO():
    ...     os.chdir(cwd)
    ...     controlcheck(firstdate="1996-01-01", stepsize="1d")
    >>> ic.shape
    (12,)

    In the above example, we use the default names for the project directory (the one
    containing the executed condition file) and the control directory (`default`).  The
    following example shows how to change them:

    >>> del model
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.chdir(cwd)
    ...     controlcheck(projectdir="somewhere", controldir="nowhere")
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to load the control file `land_dill.py` \
from directory `...hydpy/tests/iotesting/somewhere/control/nowhere`, \
the following error occurred: ...

    For some models, the appropriate states may depend on the initialisation date.  One
    example is the interception storage (|lland_states.Inzp|) of application model
    |lland_v1|, which should not exceed the interception capacity
    (|lland_derived.KInz|).  However, |lland_derived.KInz| depends on the leaf
    area index parameter |lland_control.LAI|, which offers different values depending
    on land-use type and month.  Hence, one can assign higher values to state
    |lland_states.Inzp| during periods with high leaf area indices than during periods
    with small leaf area indices.

    To show the related functionalities, we first replace the |hland_v1| application
    model of element `land_dill` with a |lland_v1| model object, define some of its
    parameter values, and write its control and condition files.  Note that the
    |lland_control.LAI| value of the only relevant land use the
    (|lland_constants.ACKER|) is 0.5 during January and 5.0 during July:

    >>> from hydpy import HydPy, prepare_model, pub
    >>> from hydpy.models.lland_v1 import ACKER
    >>> pub.timegrids = "2000-06-01", "2000-07-01", "1d"
    >>> with TestIO():
    ...     hp = HydPy("LahnH")
    ...     hp.prepare_network()
    ...     land_dill = hp.elements["land_dill"]
    ...     with pub.options.usedefaultvalues(True):
    ...         land_dill.model = prepare_model("lland_v1")
    ...         control = land_dill.model.parameters.control
    ...         control.nhru(2)
    ...         control.ft(1.0)
    ...         control.fhru(0.5)
    ...         control.lnk(ACKER)
    ...         control.lai.acker_jan = 0.5
    ...         control.lai.acker_jul = 5.0
    ...         land_dill.model.parameters.update()
    ...         land_dill.model.sequences.states.inzp(1.0)
    ...     land_dill.model.parameters.save_controls()
    ...     land_dill.model.sequences.save_conditions()

    Unfortunately, state |lland_states.Inzp| does not define a |trim| method taking the
    actual value of parameter |lland_derived.KInz| into account (due to compatibility
    with the original LARSIM model).  As an auxiliary solution, we define such a
    function within the `land_dill.py` condition file (and modify some warning settings
    in favour of the next examples):

    >>> cwd = os.path.join("LahnH", "conditions", "init_2000_07_01_00_00_00")
    >>> with TestIO():
    ...     os.chdir(cwd)
    ...     with open("land_dill.py") as file_:
    ...         lines = file_.readlines()
    ...     with open("land_dill.py", "w") as file_:
    ...         file_.writelines([
    ...             "from hydpy import pub\\n",
    ...             "pub.options.warnsimulationstep = False\\n",
    ...             "import warnings\\n",
    ...             'warnings.filterwarnings("error", message="For variable")\\n'])
    ...         file_.writelines(lines[:5])
    ...         file_.writelines([
    ...             "from hydpy.core.variabletools import trim as trim_\\n",
    ...             "def trim(self, lower=None, upper=None):\\n",
    ...             "    der = self.subseqs.seqs.model.parameters.derived\\n",
    ...             "    trim_(self, 0.0, der.kinz.acker[der.moy[0]])\\n",
    ...             "type(inzp).trim = trim\\n"])
    ...         file_.writelines(lines[5:])

    Now, executing the condition file (and thereby calling function |controlcheck|)
    does not raise any warnings due to extracting the initialisation date from the name
    of the condition directory:

    >>> with TestIO():
    ...     os.chdir(cwd)
    ...     result = run_subprocess("hyd.py exec_script land_dill.py")

    If the directory name does imply the initialisation date to be within January 2000
    instead of July 2000, we correctly get the following warning:

    >>> cwd_old = cwd
    >>> cwd_new = os.path.join("LahnH", "conditions", "init_2000_01_01")
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.rename(cwd_old, cwd_new)
    ...     os.chdir(cwd_new)
    ...     result = run_subprocess("hyd.py exec_script land_dill.py")
    Invoking hyd.py with arguments `exec_script, land_dill.py` resulted in the \
following error:
    For variable `inzp` at least one value needed to be trimmed.  The old and the new \
value(s) are `1.0, 1.0` and `0.1, 0.1`, respectively.
    ...

    One can define an alternative initialisation date via argument `firstdate`:

    >>> text_old = ('controlcheck(projectdir=r"LahnH", '
    ...             'controldir="default", stepsize="1d")')
    >>> text_new = ('controlcheck(projectdir=r"LahnH", controldir="default", '
    ...             'firstdate="2100-07-15", stepsize="1d")')
    >>> with TestIO():
    ...     os.chdir(cwd_new)
    ...     with open("land_dill.py") as file_:
    ...         text = file_.read()
    ...     text = text.replace(text_old, text_new)
    ...     with open("land_dill.py", "w") as file_:
    ...         _ = file_.write(text)
    ...     result = run_subprocess("hyd.py exec_script land_dill.py")

    Default condition directory names do not contain information about the simulation
    step size.  Hence, one needs to define it explicitly for all application models
    relying on the functionalities of class |Indexer|:

    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.chdir(cwd_new)
    ...     with open("land_dill.py") as file_:
    ...         text = file_.read()
    ...     text = text.replace('stepsize="1d"', "")
    ...     with open("land_dill.py", "w") as file_:
    ...         _ = file_.write(text)
    ...     result = run_subprocess("hyd.py exec_script land_dill.py")
    Invoking hyd.py with arguments `exec_script, land_dill.py` resulted in the \
following error:
    To apply function `controlcheck` requires time information for some model types.  \
Please define the `Timegrids` object of module `pub` manually or pass the required \
information (`stepsize` and eventually `firstdate`) as function arguments.
    ...

    The same error occurs we do not use the argument `firstdate` to define the
    initialisation time point, and method |controlcheck| cannot extract it from the
    directory name:

    >>> cwd_old = cwd_new
    >>> cwd_new = os.path.join("LahnH", "conditions", "init")
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     os.rename(cwd_old, cwd_new)
    ...     os.chdir(cwd_new)
    ...     with open("land_dill.py") as file_:
    ...         text = file_.read()
    ...     text = text.replace('firstdate="2100-07-15"', 'stepsize="1d"')
    ...     with open("land_dill.py", "w") as file_:
    ...         _ = file_.write(text)
    ...     result = run_subprocess("hyd.py exec_script land_dill.py")
    Invoking hyd.py with arguments `exec_script, land_dill.py` resulted in the \
following error:
    To apply function `controlcheck` requires time information for some model types.  \
Please define the `Timegrids` object of module `pub` manually or pass the required \
information (`stepsize` and eventually `firstdate`) as function arguments.
    ...

    Note that the functionalities of function |controlcheck| do not come into action if
    there is a `model` variable in the namespace, which is the case when a condition
    file is executed within the context of a complete *HydPy* project.
    """
    frame = inspect.currentframe()
    assert (frame is not None) and (frame.f_back is not None)
    namespace = frame.f_back.f_locals
    model = namespace.get("model")
    if model is None:
        if not controlfile:
            controlfile = os.path.split(namespace["__file__"])[-1]
        if projectdir is None:
            projectdir = os.path.split(os.path.split(os.path.split(os.getcwd())[0])[0])[
                -1
            ]
        dirpath = os.path.abspath(
            os.path.join("..", "..", "..", projectdir, "control", controldir)
        )
        if not (exceptiontools.attrready(hydpy.pub, "timegrids") or (stepsize is None)):
            if firstdate is None:
                try:
                    firstdate = timetools.Date.from_string(
                        os.path.split(os.getcwd())[-1].partition("_")[-1]
                    )
                except (ValueError, TypeError):
                    pass
            else:
                firstdate = timetools.Date(firstdate)
            if firstdate is not None:
                stepsize = timetools.Period(stepsize)
                hydpy.pub.timegrids = (firstdate, firstdate + 1000 * stepsize, stepsize)

        class CM(filetools.ControlManager):
            """Temporary |ControlManager| class."""

            currentpath = dirpath

        cwd = os.getcwd()
        try:
            os.chdir(dirpath)
            model = CM().load_file(filename=controlfile)["model"]
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to load the control file `{controlfile}` from "
                f"directory `{objecttools.repr_(dirpath)}`"
            )
        finally:
            os.chdir(cwd)
        try:
            model.parameters.update()
        except exceptiontools.AttributeNotReady as exc:
            raise RuntimeError(
                "To apply function `controlcheck` requires time information for some "
                "model types.  Please define the `Timegrids` object of module `pub` "
                "manually or pass the required information (`stepsize` and eventually "
                "`firstdate`) as function arguments."
            ) from exc

        namespace["model"] = model
        for name in ("states", "logs"):
            subseqs = getattr(model.sequences, name, None)
            if subseqs is not None:
                for seq in subseqs:
                    namespace[seq.name] = seq
