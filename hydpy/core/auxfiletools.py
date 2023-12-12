# -*- coding: utf-8 -*-
"""This module supports writing auxiliary files.

In *HydPy*, parameter values are usually not shared between different model objects
handled by different elements, even if the model objects are of the same type (e.g.
|lland_v1|).  This approach offers flexibility in applying different parameterisation
schemes.  However, often modellers prefer to use a minimal amount of values for
specific parameters  (at least within hydrologically homogeneous regions).  Hence, the
downside of this flexibility is that the same parameter values might appear in hundreds
or even thousands of parameter control files (one file for each model/element).

To decrease this redundancy, *HydPy* allows for passing names of auxiliary control
files to parameters defined within regular control files.  *HydPy* then reads the
actual parameter values from the auxiliary files, each one possibly referenced within a
large number of control files.

Reading parameters from regular and from auxiliary control files is straightforward.
However, storing some parameters in a large number of regular control files and some
other parameters in a small number of auxiliary files can be complicated.  The features
implemented in module |auxfiletools| are a means to perform such actions in a
semi-automated manner (other means are the selection mechanism implemented in module
|selectiontools|).
"""
# import...
# ...from standard library
from __future__ import annotations
import copy
import itertools
import types
import warnings

# ...from HydPy
import hydpy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import timetools


Reference = Union[parametertools.Parameter, parametertools.KeywordArguments]


class Auxfiler:
    """Structures auxiliary file information.

    For writing some parameter information to auxiliary files, it is advisable to
    prepare (only) one |Auxfiler| object:

    >>> from hydpy import Auxfiler
    >>> auxfiler = Auxfiler()

    Each |Auxfiler| object is capable of handling parameter information for different
    kinds of models and performs some plausibility checks on added data.  Assume we
    want to store the control files of a "LARSIM type" HydPy project involving the
    application models |lland_v1|, |lland_v3| and |lstream_v001|.  The following
    example shows how we add these models to the |Auxfiler| object by passing through
    module (|lland_v1|), a working model object (|lland_v3|) or their name
    (|lstream_v001|):

    >>> from hydpy import prepare_model
    >>> from hydpy.models import lland_v1 as module
    >>> model = prepare_model("lland_v3")
    >>> string = "lstream_v001"

    You can add all model types individually or in groups:

    >>> auxfiler.add_models(module)
    >>> auxfiler.add_models(model, string)
    >>> auxfiler
    Auxfiler("lland_v1", "lland_v3", "lstream_v001")

    Alternatively, you can pass the models directly to the constructor:

    >>> Auxfiler(model, string, module)
    Auxfiler("lland_v1", "lland_v3", "lstream_v001")

    Wrong model specifications result in errors like the following:

    >>> auxfiler.add_models("asdf")
    Traceback (most recent call last):
    ...
    ModuleNotFoundError: While trying to add one ore more models to the actual \
`Auxfiler` object, the following error occurred: No module named 'hydpy.models.asdf'

    The |Auxfiler| object allocates a separate |SubAuxfiler| object to each model type.
    These are available via keyword and attribute access:

    >>> auxfiler["lland_v1"]
    SubAuxfiler()
    >>> auxfiler.lland_v3
    SubAuxfiler()

    Adding new and deleting existing |SubAuxfiler| objects via attribute access is
    disabled for safety purposes:

    >>> auxfiler.lland_v3 = auxfiler.lland_v1
    Traceback (most recent call last):
    ...
    AttributeError: Class `Auxfiler` does not support adding `SubAuxfiler` objects \
via attribute access.  Use method `add_models` to register additional models.

    >>> del auxfiler.lland_v1
    Traceback (most recent call last):
    ...
    AttributeError: Class `Auxfiler` does not support deleting `SubAuxfiler` objects \
via attribute access.  Use method `remove_models` to remove registered models.

    As stated by the last error message, you should remove models and their
    |SubAuxfiler| objects via method |Auxfiler.remove_models|:

    >>> auxfiler.remove_models(module, string)
    >>> auxfiler
    Auxfiler("lland_v3")

    >>> auxfiler.remove_models(module, string)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to remove one or more models from the actual \
`Auxfiler` object, the following error occurred: Model `lland_v1` is currently not \
registered.

    >>> auxfiler.lland_v1
    Traceback (most recent call last):
    ...
    AttributeError: The actual `Auxfiler` object does neither have a normal \
attribute nor does it handle a model named `lland_v1`.

    >>> auxfiler["lland_v1"]
    Traceback (most recent call last):
    ...
    KeyError: 'The actual `Auxfiler` object does not handle a model named `lland_v1`.'

    For other types, attribute access works as usual:

    >>> auxfiler.test = 123
    >>> hasattr(auxfiler, "test")
    True
    >>> del auxfiler.test
    >>> hasattr(auxfiler, "test")
    False
    """

    _model2subauxfiler: Dict[str, SubAuxfiler]

    def __init__(self, *models: Union[str, types.ModuleType, modeltools.Model]) -> None:
        self._model2subauxfiler = {}
        self.add_models(*models)

    def add_models(
        self, *models: Union[str, types.ModuleType, modeltools.Model]
    ) -> None:
        """Register an arbitrary number of |Model| types.

        For further information, see the main documentation on class |Auxfiler|.
        """
        try:
            for model in models:
                model_ = self._get_model(model)
                self._model2subauxfiler[str(model_)] = SubAuxfiler(
                    master=self, model=self._get_model(model_)
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to add one ore more models to the actual "
                f"`{type(self).__name__}` object"
            )

    def remove_models(
        self, *models: Union[str, types.ModuleType, modeltools.Model]
    ) -> None:
        """Unregister an arbitrary number of |Model| classes.

        For further information, see the main documentation on class |Auxfiler|.
        """
        try:
            for model in models:
                model_ = self._get_model(model)
                try:
                    del self._model2subauxfiler[str(model_)]
                except KeyError:
                    raise RuntimeError(
                        f"Model `{model_}` is currently not registered."
                    ) from None
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to remove one or more models from the actual "
                f"`{type(self).__name__}` object"
            )

    @staticmethod
    def _get_model(
        value: Union[str, types.ModuleType, modeltools.Model]
    ) -> modeltools.Model:
        if isinstance(value, modeltools.Model):
            return value
        return importtools.prepare_model(value)

    def get(self, model: Union[str, modeltools.Model]) -> Optional[SubAuxfiler]:
        """Get the |SubAuxfiler| object related to the given |Model| type.

        In contrast to attribute and keyword access, method |Auxfiler.get| returns
        |None| when it does not handle the requested |SubAuxfiler| object:

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler("lland_v1")
        >>> auxfiler.get("lland_v1")
        SubAuxfiler()
        >>> auxfiler.get("lland_v3")
        """
        return self._model2subauxfiler.get(str(model))

    def __getitem__(self, item: str) -> SubAuxfiler:
        try:
            return self._model2subauxfiler[item]
        except KeyError:
            raise KeyError(
                f"The actual `{type(self).__name__}` object does not handle a model "
                f"named `{item}`."
            ) from None

    @property
    def modelnames(self) -> Tuple[str, ...]:
        """A sorted |tuple| of all names of the handled models.

        >>> from hydpy import Auxfiler
        >>> Auxfiler("lland_v3", "lstream_v001", "lland_v1").modelnames
        ('lland_v1', 'lland_v3', 'lstream_v001')
        """
        return tuple(sorted(self._model2subauxfiler.keys()))

    def write(
        self,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        simulationstep: Optional[timetools.PeriodConstrArg] = None,
    ) -> None:
        """Write all defined auxiliary control files.

        Before being able to write parameter information into auxiliary files, you need
        to know how to add this information to your |Auxfiler| object.  Hence, please
        read the documentation on method |SubAuxfiler.add_parameter| of class
        |SubAuxfiler| first, from which we borrow the following (slightly modified)
        test-setting:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqd1(200.0)
        >>> eqd2(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler("lland_v1", "lland_v3")
        >>> auxfiler.lland_v1.add_parameter(eqd1, filename="file1")
        >>> auxfiler.lland_v1.add_parameter(parameter=tgr,
        ...                                 filename="file1",
        ...                                 keywordarguments=tgr.keywordarguments)
        >>> auxfiler.lland_v3.add_parameters(eqd1, eqd2, filename="file2")

        Class |Auxfiler| takes the target path from the |ControlManager| object stored
        in the global |pub| object.  For testing, we initialise one and override its
        |property| |FileManager.currentpath| with a simple |str| object defining the
        test target path:

        >>> from hydpy import pub
        >>> pub.projectname = "test"
        >>> from hydpy.core.filetools import ControlManager
        >>> class Test(ControlManager):
        ...     currentpath = "test_directory"
        >>> pub.controlmanager = Test()

        Usually, |Auxfiler| objects write control files to disk, of course.  But to
        show (and to test) the results in the following test, we redirected file
        writing via class |Open|:

        >>> from hydpy import Open
        >>> with Open():
        ...     auxfiler.write(parameterstep="1d", simulationstep="12h")
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        test_directory/file1.py
        -----------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.lland_v1 import *
        <BLANKLINE>
        simulationstep("12h")
        parameterstep("1d")
        <BLANKLINE>
        tgr(acker=2.0, laubw=1.0)
        eqd1(200.0)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        test_directory/file2.py
        -----------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.lland_v3 import *
        <BLANKLINE>
        simulationstep("12h")
        parameterstep("1d")
        <BLANKLINE>
        eqd1(200.0)
        eqd2(100.0)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """
        options = hydpy.pub.options
        for modelname, subauxfiler in self:
            for filename in subauxfiler.get_filenames():
                with options.parameterstep(parameterstep), options.simulationstep(
                    simulationstep
                ):
                    model = importtools.prepare_model(modelname)
                    header = model.get_controlfileheader(
                        import_submodels=False,
                        parameterstep=parameterstep,
                        simulationstep=simulationstep,
                    )
                    body = "\n".join(
                        subauxfiler.get_parameterstrings(filename=filename)
                    )
                hydpy.pub.controlmanager.save_file(
                    filename=filename, text="".join((header, body, "\n"))
                )

    def __getattr__(self, name: str) -> SubAuxfiler:
        try:
            return self._model2subauxfiler[name]
        except KeyError:
            raise AttributeError(
                f"The actual `{type(self).__name__}` object does neither have a "
                f"normal attribute nor does it handle a model named `{name}`."
            ) from None

    def __setattr__(self, name: str, value: object) -> None:
        if isinstance(value, SubAuxfiler):
            raise AttributeError(
                f"Class `{type(self).__name__}` does not support adding `SubAuxfiler` "
                f"objects via attribute access.  Use method `add_models` to register "
                f"additional models."
            )
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        if name in self._model2subauxfiler:
            raise AttributeError(
                f"Class `{type(self).__name__}` does not support deleting "
                f"`SubAuxfiler` objects via attribute access.  Use method "
                f"`remove_models` to remove registered models."
            )
        super().__delattr__(name)

    def __iter__(self) -> Iterator[Tuple[str, SubAuxfiler]]:
        for item in sorted(self._model2subauxfiler.items()):
            yield item

    def __repr__(self) -> str:
        return objecttools.apply_black(
            type(self).__name__, *sorted(f"{name}" for name in self.modelnames)
        )

    def __dir__(self) -> List[str]:
        """
        >>> aux = Auxfiler()
        >>> aux.add_models("llake_v1", "lland_v1", "lstream_v001")
        >>> sorted(set(dir(aux)) - set(object.__dir__(aux)))
        ['llake_v1', 'lland_v1', 'lstream_v001']
        """
        return cast(List[str], super().__dir__()) + list(self.modelnames)


class SubAuxfiler:
    """Map different |Parameter| objects to the names of auxiliary files.

    Usually, |SubAuxfiler| objects are not initialised by the user explicitly but made
    available by their master |Auxfiler| object.  After that, users can access them and
    subsequently register different |Parameter| objects.  See the documentation on
    method |SubAuxfiler.add_parameter| for further information.
    """

    _master: Optional[Auxfiler]
    _model: Optional[modeltools.Model]
    _type2filename2reference: Dict[Type[parametertools.Parameter], Dict[str, Reference]]

    def __init__(
        self,
        master: Optional[Auxfiler] = None,
        model: Optional[modeltools.Model] = None,
    ) -> None:
        self._master = master
        self._model = model
        self._type2filename2reference = {}

    def add_parameter(
        self,
        parameter: parametertools.Parameter,
        filename: str,
        keywordarguments: Optional[parametertools.KeywordArguments[T]] = None,
    ) -> None:
        """Add a single |Parameter| to the actual |SubAuxfiler| object.

        To show how |SubAuxfiler| works, we first prepare an instance of application
        model |lland_v1| and define the values of some of its parameters:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqi2(1000.0)
        >>> eqd1(100.0)
        >>> eqd2(50.0)

        Next, we initialise an |Auxfiler| object handling a single |SubAuxfiler|
        object.  The purpose of the |SubAuxfiler| object is to allocate the above
        parameters to two auxiliary files named `file1` and `file2`:

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)

        Auxiliary file `file1` shall contain the actual values of parameters
        |lland_control.EQB|, |lland_control.EQI1|, and |lland_control.EQI2|:

        >>> auxfiler.lland_v1.add_parameters(eqb, eqi1, eqi2, filename="file1")
        >>> auxfiler.lland_v1.file1
        (eqb(5000.0), eqi1(2000.0), eqi2(1000.0))

        Auxiliary file `file2` shall contain the actual values of parameters
        |lland_control.EQD1|, |lland_control.EQD2|, and (also!) of parameter
        |lland_control.EQB|:

        >>> auxfiler.lland_v1.add_parameters(eqd1, eqd2, filename="file2")
        >>> auxfiler.lland_v1.add_parameter(eqb, filename="file2")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to extend the range of parameters handled by the \
actual `SubAuxfiler` object, the following error occurred: You tried to allocate \
parameter `eqb(5000.0)` to filename `file2`, but an equal `EQB` object has already \
been allocated to filename `file1`.

        >>> auxfiler.lland_v1.file2
        (eqd1(100.0), eqd2(50.0))

        As explained by the error message, allocating the same parameter type with
        equal values to two different auxiliary files is not allowed.  Nevertheless,
        after changing the value of parameter |lland_control.EQB|, it can be allocated
        to filename `file2`:

        >>> eqb *= 2
        >>> auxfiler.lland_v1.add_parameter(eqb, filename="file2")
        >>> auxfiler.lland_v1.file2
        (eqb(10000.0), eqd1(100.0), eqd2(50.0))

        The following example shows that parameter |lland_control.EQB| already
        allocated to `file1` has still the same value (we implemented this safety
        mechanism via deep copying) and that one can view all registered parameters by
        using their names as attribute names:

        >>> auxfiler.lland_v1.eqb
        (eqb(10000.0), eqb(5000.0))

        During adding parameters method |SubAuxfiler.add_parameter| performs some
        additional plausibility checks.  First, it prevents from using the same
        filename twice:

        >>> auxfiler.add_models("lstream_v001")
        >>> auxfiler.lstream_v001.add_parameter(tgr, filename="file1")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to extend the range of parameters handled by the \
actual `SubAuxfiler` object, the following error occurred: Filename `file1` is \
already allocated to another `SubAuxfiler` object.

        Second, it checks that an assigned parameter belongs to the corresponding
        model:

        >>> auxfiler.lstream_v001.add_parameter(tgr, filename="file3")
        Traceback (most recent call last):
        ...
        TypeError: While trying to extend the range of parameters handled by the \
actual `SubAuxfiler` object, the following error occurred: Variable type `TGr` is not \
handled by model `lstream_v001`.

        The examples above deal with simple 0-dimensional |Parameter| subclasses where
        there is no question in how to define equality.  However, for multidimensional
        |Parameter| subclasses requiring that the shape and all values are equal might
        often be too strict.

        The auxiliary file functionalities of *HydPy* allow using the
        |Parameter.keywordarguments| property of a parameter to check for equality
        instead (put more concretely, method |SubAuxfiler.get_parameterstrings| uses
        method |KeywordArguments.subset_of| of class |KeywordArguments| for
        comparisons). If we want to apply this feature for the instances of the
        |ZipParameter| subclass |lland_control.TGr|, we need to additionally pass a
        |KeywordArguments| object to method |SubAuxfiler.add_parameter|:

        >>> auxfiler.lland_v1.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> auxfiler.lland_v1.tgr
        (KeywordArguments(acker=2.0, laubw=1.0),)

        Alternatively, we can also pass a manually defined |KeywordArguments| object
        (for which we perform similar plausibility checks as discussed above):

        >>> from hydpy import KeywordArguments
        >>> auxfiler.lland_v1.add_parameter(
        ...     tgr, filename="file2",
        ...     keywordarguments=KeywordArguments(acker=2.0, laubw=1.0))
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to extend the range of parameters handled by the \
actual `SubAuxfiler` object, the following error occurred: You tried to allocate \
parameter `tgr(acker=2.0, laubw=1.0)` with keyword arguments \
`KeywordArguments(acker=2.0, laubw=1.0)` to filename `file2`, but an `TGr` with equal \
keyword arguments has already been allocated to filename `file1`.

        Often, we want such a manually defined |KeywordArguments| object to be more
        general so that it covers as many actual parameter objects as possible:

        >>> auxfiler.lland_v1.add_parameter(
        ...     tgr, filename="file2",
        ...     keywordarguments=KeywordArguments(acker=2.0, laubw=1.0, nadelw=0.0))
        >>> auxfiler.lland_v1.tgr
        (KeywordArguments(acker=2.0, laubw=1.0), \
KeywordArguments(acker=2.0, laubw=1.0, nadelw=0.0))

        Note that due to the current implementation of method
        |SubAuxfiler.get_parameterstrings| the final state of the |Auxfiler| object
        results in some ambiguity (see the documentation on method
        |SubAuxfiler.get_parameterstrings| for further information).  Hence, we might
        add more detailed plausibility checks regarding equality of |KeywordArguments|
        objects in the future.

        Unfortunately, the string representations of |SubAuxfiler| objects are not
        executable at the moment:

        >>> auxfiler.lland_v1
        SubAuxfiler(file1, file2)

        Erroneous attribute access results in the following error:

        >>> auxfiler.lland_v1.wrong
        Traceback (most recent call last):
        ...
        AttributeError: `wrong` is neither a filename nor a name of a parameter \
handled by the actual `SubAuxfiler` object.
        """
        try:
            self._check_filename(filename=filename)
            self._check_parameter(parameter=parameter)
            filename2reference = self._type2filename2reference.get(type(parameter), {})
            self._check_duplicate(
                filename2reference=filename2reference,
                parameter=parameter,
                filename=filename,
                keywordarguments=keywordarguments,
            )
            if keywordarguments is None:
                filename2reference[filename] = copy.deepcopy(parameter)
            else:
                filename2reference[filename] = copy.deepcopy(keywordarguments)
            self._type2filename2reference[type(parameter)] = filename2reference
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to extend the range of parameters handled by the "
                f"actual `{type(self).__name__}` object"
            )

    def _check_filename(self, filename: str) -> None:
        objecttools.valid_variable_identifier(filename)
        if self._master is not None:
            for _, subauxf in self._master:
                if (subauxf is not self) and (filename in subauxf.get_filenames()):
                    raise RuntimeError(
                        f"Filename `{filename}` is already allocated to another "
                        f"`{type(self).__name__}` object."
                    )

    def _check_parameter(self, parameter: parametertools.Parameter) -> None:
        if self._model and not isinstance(
            parameter, self._model.parameters.control.CLASSES
        ):
            raise TypeError(
                f"Variable type `{type(parameter).__name__}` is not handled by model "
                f"`{self._model}`."
            )

    @staticmethod
    def _check_duplicate(
        filename2reference: Dict[str, Reference],
        parameter: parametertools.Parameter,
        filename: str,
        keywordarguments: Optional[parametertools.KeywordArguments[T]],
    ) -> None:
        for fn, ref in filename2reference.items():
            if fn != filename:
                if (keywordarguments is None) and (ref == parameter):
                    raise RuntimeError(
                        f"You tried to allocate parameter `{repr(parameter)}` to "
                        f"filename `{filename}`, but an equal "
                        f"`{type(parameter).__name__}` object has already been "
                        f"allocated to filename `{fn}`."
                    )
                if (keywordarguments is not None) and (ref == keywordarguments):
                    raise RuntimeError(
                        f"You tried to allocate parameter `{repr(parameter)}` with "
                        f"keyword arguments `{keywordarguments}` to filename "
                        f"`{filename}`, but an `{type(parameter).__name__}` with "
                        f"equal keyword arguments has already been allocated to "
                        f"filename `{fn}`."
                    )

    def add_parameters(
        self, *parameters: parametertools.Parameter, filename: str
    ) -> None:
        """Add an arbitrary number of |Parameter| objects to the actual |SubAuxfiler|
        object.

        Method |SubAuxfiler.add_parameters| works like method
        |SubAuxfiler.add_parameter| but allows to add multiple parameters at once.  On
        the downside, it does not allow to define alternative keyword arguments.
        """
        for parameter in parameters:
            self.add_parameter(filename=filename, parameter=parameter)

    def remove_parameters(
        self,
        parametertype: Optional[Type[parametertools.Parameter]] = None,
        filename: Optional[str] = None,
    ) -> None:
        """Remove the registered |Parameter| objects of the given type related to the
        given filename.

        The following (slightly modified) test-setting stems from the documentation
        on method |SubAuxfiler.add_parameter|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        >>> subauxfiler.file1
        (KeywordArguments(acker=2.0, laubw=1.0), eqb(5000.0), eqi1(2000.0))
        >>> subauxfiler.file2
        (eqb(10000.0), eqd1(100.0))

        To be able to start from this setting repeatedly, we make a deep copy
        of an internal dictionary:

        >>> from copy import deepcopy
        >>> copy = deepcopy(subauxfiler._type2filename2reference)

        First, you can remove all parameters related to a specific filename:

        >>> subauxfiler.remove_parameters(filename="file1")
        >>> subauxfiler.get_filenames()
        ('file2',)
        >>> subauxfiler.file2
        (eqb(10000.0), eqd1(100.0))

        Second, you can remove all parameters of a specific type:

        >>> subauxfiler._type2filename2reference = deepcopy(copy)
        >>> subauxfiler.remove_parameters(parametertype=type(eqb))
        >>> subauxfiler.file1
        (KeywordArguments(acker=2.0, laubw=1.0), eqi1(2000.0))
        >>> subauxfiler.file2
        (eqd1(100.0),)

        Third, you can remove a specific parameter object by defining both its time and
        its filename:

        >>> subauxfiler._type2filename2reference = deepcopy(copy)
        >>> subauxfiler.remove_parameters(parametertype=type(eqb), filename="file1")
        >>> subauxfiler.file1
        (KeywordArguments(acker=2.0, laubw=1.0), eqi1(2000.0))
        >>> subauxfiler.file2
        (eqb(10000.0), eqd1(100.0))

        Fourth, you can remove all parameters at once:

        >>> subauxfiler._type2filename2reference = deepcopy(copy)
        >>> subauxfiler.remove_parameters()
        >>> subauxfiler.get_filenames()
        ()

        Each combination of arguments comes with a particular error message:

        >>> subauxfiler.remove_parameters(filename="file2")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to remove the parameter object(s) allocated to \
filename `file2`, the following error occurred: No such parameter object(s) available.

        >>> subauxfiler.remove_parameters(parametertype=type(eqd2))
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to remove the parameter object(s) of type `EQD2`, \
the following error occurred: No such parameter object(s) available.

        >>> subauxfiler.remove_parameters(parametertype=type(eqd2), filename="file2")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to remove a parameter object of type `EQD2` \
allocated to filename `file2`, the following error occurred: No such parameter \
object(s) available.

        >>> subauxfiler._type2filename2reference = None
        >>> subauxfiler.remove_parameters()
        Traceback (most recent call last):
        ...
        AttributeError: While trying to remove all parameter objects, the following \
error occurred: 'NoneType' object has no attribute 'items'
        """
        try:
            deleted_something = False
            for type_, fn2ref in tuple(self._type2filename2reference.items()):
                for filename_ in tuple(fn2ref):
                    if parametertype in (None, type_) and (
                        filename in (None, filename_)
                    ):
                        del fn2ref[filename_]
                        deleted_something = True
                if not fn2ref:
                    del self._type2filename2reference[type_]
            if not deleted_something:
                raise RuntimeError("No such parameter object(s) available.")
        except BaseException:
            if (parametertype is None) and (filename is None):
                objecttools.augment_excmessage(
                    "While trying to remove all parameter objects"
                )
            if parametertype is None:
                objecttools.augment_excmessage(
                    f"While trying to remove the parameter object(s) allocated to "
                    f"filename `{filename}`"
                )
            if filename is None:
                objecttools.augment_excmessage(
                    f"While trying to remove the parameter object(s) of type "
                    f"`{parametertype.__name__}`"
                )
            objecttools.augment_excmessage(
                f"While trying to remove a parameter object of type "
                f"`{parametertype.__name__}` allocated to filename `{filename}`"
            )

    def get_filenames(
        self, parametertype: Optional[Type[parametertools.Parameter]] = None
    ) -> Tuple[str, ...]:
        """Return a |tuple| of all or a selection of the handled auxiliary file names.

        The following (slightly modified) test-setting stems from the documentation on
        method |SubAuxfiler.add_parameter|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        Without an argument, method |SubAuxfiler.get_filenames| returns all auxiliary
        filenames:

        >>> subauxfiler.get_filenames()
        ('file1', 'file2')

        For a given parameter type, method |SubAuxfiler.get_filenames| returns only the
        auxiliary filenames allocating such a type:

        >>> subauxfiler.get_filenames(parametertype=type(eqi1))
        ('file1',)
        """
        filenames: Set[str] = set()
        for type_, filename2reference in self._type2filename2reference.items():
            if (parametertype is None) or issubclass(parametertype, type_):
                filenames.update(filename2reference)
        return tuple(sorted(filenames))

    def get_parametertypes(
        self, filename: Optional[str] = None
    ) -> Tuple[Type[parametertools.Parameter], ...]:
        """Return a |tuple| of all or a selection of the handled parameter types.

        The following (slightly modified) test-setting stems from the documentation on
        method |SubAuxfiler.add_parameter|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        Without an argument, method |SubAuxfiler.get_parametertypes| returns all
        registered parameter types:

        >>> for parametertype in subauxfiler.get_parametertypes():
        ...     print(parametertype.__name__)
        TGr
        EQB
        EQI1
        EQD1

        For a given filename, method |SubAuxfiler.get_parametertypes| returns only the
        registered parameter types allocated for this filename:

        >>> for parametertype in subauxfiler.get_parametertypes(filename="file1"):
        ...     print(parametertype.__name__)
        TGr
        EQB
        EQI1
        """
        return variabletools.sort_variables(
            type_
            for type_, filename2reference in self._type2filename2reference.items()
            if (filename is None) or (filename in filename2reference)
        )

    def get_parameterstrings(
        self,
        filename: Optional[str] = None,
        parametertype: Optional[Type[parametertools.Parameter]] = None,
    ) -> Tuple[str, ...]:
        """Return a |tuple| of string representations of all or a selection of the
        handled parameter objects.

        The following (slightly modified) test-setting stems from the documentation on
        method |SubAuxfiler.add_parameter|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        Without an argument, method |SubAuxfiler.get_parameterstrings| returns the
        string representations of all registered parameter objects:

        >>> for string in subauxfiler.get_parameterstrings():
        ...     print(string)
        tgr(acker=2.0, laubw=1.0)
        eqb(5000.0)
        eqb(10000.0)
        eqi1(2000.0)
        eqd1(100.0)

        For a given filename, method |SubAuxfiler.get_parameterstrings| returns only
        the string representations of the registered parameter objects allocated for
        this filename:

        >>> for string in subauxfiler.get_parameterstrings(filename="file1"):
        ...     print(string)
        tgr(acker=2.0, laubw=1.0)
        eqb(5000.0)
        eqi1(2000.0)

        For a given parameter type, method |SubAuxfiler.get_parameterstrings| returns
        only the string representations of the registered parameter objects of such a
        type:

        >>> for string in subauxfiler.get_parameterstrings(parametertype=type(eqb)):
        ...     print(string)
        eqb(5000.0)
        eqb(10000.0)

        For a given filename and a given parameter type, method
        |SubAuxfiler.get_parameterstrings| returns only the string representation of
        the registered parameter object of such a type allocated by such a filename:

        >>> subauxfiler.get_parameterstrings(filename="file1", parametertype=type(eqb))
        ('eqb(5000.0)',)
        """
        strings: List[str] = []
        for type_, fn2ref in variabletools.sort_variables(
            self._type2filename2reference.items()
        ):
            for fn, ref in sorted(fn2ref.items()):
                if parametertype in (None, type_) and filename in (None, fn):
                    if isinstance(ref, parametertools.KeywordArguments):
                        strings.append(
                            objecttools.apply_black(type_.__name__.lower(), **dict(ref))
                        )
                    else:
                        strings.append(repr(ref))
        return tuple(strings)

    def get_references(
        self,
        filename: Optional[str] = None,
        parametertype: Optional[Type[parametertools.Parameter]] = None,
    ) -> Tuple[Reference, ...]:
        """Return a |tuple| of all or a selection of the reference parameter objects
        or their related reference keyword arguments.

        The following (slightly modified) test-setting stems from the documentation on
        method |SubAuxfiler.add_parameter|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        Despite returning the reference objects instead of parameter string
        representations, method |SubAuxfiler.get_references| works precisely like
        method |SubAuxfiler.get_parameterstrings|:

        >>> for reference in subauxfiler.get_references():
        ...     print(reference)
        KeywordArguments(acker=2.0, laubw=1.0)
        eqb(5000.0)
        eqb(10000.0)
        eqi1(2000.0)
        eqd1(100.0)

        >>> for reference in subauxfiler.get_references(filename="file1"):
        ...     print(reference)
        KeywordArguments(acker=2.0, laubw=1.0)
        eqb(5000.0)
        eqi1(2000.0)

        >>> for reference in subauxfiler.get_references(parametertype=type(eqb)):
        ...     print(reference)
        eqb(5000.0)
        eqb(10000.0)

        >>> subauxfiler.get_references(filename="file1", parametertype=type(eqb))
        (eqb(5000.0),)
        """
        references: List[Reference] = []
        for type_, fn2ref in variabletools.sort_variables(
            self._type2filename2reference.items()
        ):
            for fn, ref in sorted(fn2ref.items()):
                if parametertype in (None, type_) and filename in (None, fn):
                    references.append(ref)
        return tuple(references)

    def get_filename(self, parameter: parametertools.Parameter) -> Optional[str]:
        """If possible, return an auxiliary filename suitable for the given parameter
        object.

        The following (slightly modified) test-setting stems from the documentation on
        method |SubAuxfiler.add_parameter|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        In simple cases, method |SubAuxfiler.get_filename| searches for an equal
        reference parameter object and returns the related auxiliary filename:

        >>> subauxfiler.get_filename(eqb)
        'file2'
        >>> eqb /= 2.0
        >>> subauxfiler.get_filename(eqb)
        'file1'

        If it cannot find an equal reference parameter, it returns |None|:

        >>> eqb /= 2.0
        >>> subauxfiler.get_filename(eqb)

        If a registered parameter object is associated with a |KeywordArguments| object
        (see the documentation on method |SubAuxfiler.add_parameter| on how to do this),
        |SubAuxfiler.get_filename| does not check for equality.  Instead,  it uses
        method |KeywordArguments.subset_of| to check if the keyword arguments of the
        given parameter are a subset of keyword arguments of the registered parameter:

        >>> subauxfiler.get_filename(tgr)
        'file1'
        >>> tgr(acker=2.0, laubw=0.0)
        >>> subauxfiler.get_filename(tgr)

        As a result, auxiliary file `file1` is also considered suitable for a
        |lland_control.TGr| object related to land-use type |lland_constants.ACKER|
        (acre) only:

        >>> lnk(ACKER)
        >>> tgr(acker=3.0)
        >>> subauxfiler.get_filename(tgr)
        >>> tgr(acker=2.0)
        >>> subauxfiler.get_filename(tgr)
        'file1'

        The above mechanism is convenient (and possibly even necessary to make writing
        auxiliary files feasible for many parameter types) but can lead to ambiguous
        situations.  To demonstrate this, we register the currently relevant keyword
        arguments of parameter |lland_control.TGr|:

        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file2", keywordarguments=tgr.keywordarguments)

        Now, the keyword arguments of |lland_control.TGr| are a subset of both
        registered |KeywordArguments| objects:

        >>> tgr.keywordarguments
        KeywordArguments(acker=2.0)
        >>> kwargs = subauxfiler.get_references(
        ...     parametertype=type(tgr), filename="file1")[0]
        >>> kwargs
        KeywordArguments(acker=2.0, laubw=1.0)
        >>> tgr.keywordarguments.subset_of(kwargs)
        True
        >>> kwargs = subauxfiler.get_references(
        ...     parametertype=type(tgr), filename="file2")[0]
        >>> kwargs
        KeywordArguments(acker=2.0)
        >>> tgr.keywordarguments.subset_of(kwargs)
        True

        Method |SubAuxfiler.get_filename| emits a warning when it finds multiple
        suitable auxiliary files:

        >>> subauxfiler.get_filename(tgr)
        Traceback (most recent call last):
        ...
        UserWarning: Parameter `tgr(2.0)` matches several auxiliary files: file1 and \
file2

        Nevertheless, it returns the first match (which might be confusing due to its
        arbitrariness but at least results in a working project configuration):

        >>> import warnings
        >>> with warnings.catch_warnings() :
        ...     warnings.filterwarnings("ignore")
        ...     subauxfiler.get_filename(tgr)
        'file1'
        """
        filenames = []
        filename2reference = self._type2filename2reference.get(type(parameter), {})
        for filename, reference in filename2reference.items():
            if (
                isinstance(reference, parametertools.KeywordArguments)
                and parameter.keywordarguments.subset_of(reference)
            ) or (parameter == reference):
                filenames.append(filename)
        if not filenames:
            return None
        if len(filenames) > 1:
            warnings.warn(
                f"Parameter `{parameter}` matches several auxiliary files: "
                f"{objecttools.enumeration(filenames)}"
            )
        return filenames[0]

    def __getattr__(self, name: str) -> Tuple[Reference, ...]:
        type2ref = {}
        for type_, fn2ref in self._type2filename2reference.items():
            if name == type_.name:
                return tuple(sorted(fn2ref.values(), key=str))
            if name in fn2ref:
                type2ref[type_] = fn2ref[name]
        if type2ref:
            return tuple(
                ref for type_, ref in variabletools.sort_variables(type2ref.items())
            )
        raise AttributeError(
            f"`{name}` is neither a filename nor a name of a parameter handled by the "
            f"actual `{type(self).__name__}` object."
        )

    def __repr__(self) -> str:
        repr_ = objecttools.assignrepr_values(
            values=self.get_filenames(), prefix=f"{type(self).__name__}(", width=70
        )
        return f"{repr_})"

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)
        >>> tgr(acker=2.0, laubw=1.0)
        >>> eqb(5000.0)
        >>> eqi1(2000.0)
        >>> eqd1(100.0)

        >>> from hydpy import Auxfiler
        >>> auxfiler = Auxfiler(model)
        >>> subauxfiler = auxfiler.lland_v1
        >>> subauxfiler.add_parameters(eqb, eqi1, filename="file1")
        >>> subauxfiler.add_parameter(
        ...     tgr, filename="file1", keywordarguments=tgr.keywordarguments)
        >>> eqb *= 2.0
        >>> subauxfiler.add_parameters(eqb, eqd1, filename="file2")

        >>> sorted(set(dir(subauxfiler)) - set(object.__dir__(subauxfiler)))
        ['eqb', 'eqd1', 'eqi1', 'file1', 'file2', 'tgr']
        """
        names = itertools.chain(
            cast(List[str], super().__dir__()),
            self.get_filenames(),
            (type_.__name__.lower() for type_ in self.get_parametertypes()),
        )
        return list(names)
