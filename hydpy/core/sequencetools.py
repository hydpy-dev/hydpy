# -*- coding: utf-8 -*-
"""This module implements tools for defining and handling different kinds of sequences
(time-series) of hydrological models."""
# import...
# ...from standard library
from __future__ import annotations
import abc
import copy
import os
import runpy
import sys
import types
import warnings
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import modeltools
    from hydpy.core import timetools
    from hydpy.cythons import pointerutils
    from hydpy.cythons import sequenceutils
else:
    # from hydpy.core import modeltools    actual import below
    from hydpy.cythons.autogen import pointerutils
    from hydpy.cythons.autogen import sequenceutils


TypeSequences = TypeVar("TypeSequences", "Sequences", "devicetools.Node")

TypeModelSequences = TypeVar(
    "TypeModelSequences",
    bound="ModelSequences[ModelSequence, variabletools.FastAccess]",
)

TypeSequence_co = TypeVar("TypeSequence_co", bound="Sequence_", covariant=True)
TypeIOSequence_co = TypeVar("TypeIOSequence_co", bound="IOSequence", covariant=True)
TypeModelSequence_co = TypeVar(
    "TypeModelSequence_co", bound="ModelSequence", covariant=True
)
TypeModelIOSequence_co = TypeVar(
    "TypeModelIOSequence_co", bound="ModelIOSequence", covariant=True
)
TypeOutputSequence_co = TypeVar(
    "TypeOutputSequence_co", bound="OutputSequence", covariant=True
)
TypeLinkSequence_co = TypeVar(
    "TypeLinkSequence_co", bound="LinkSequence", covariant=True
)

TypeFastAccessIOSequence_co = TypeVar(
    "TypeFastAccessIOSequence_co", bound="FastAccessIOSequence", covariant=True
)

ModelSequencesSubypes = Union[
    "InputSequences",
    "FactorSequences",
    "FluxSequences",
    "StateSequences",
    "LogSequences",
    "AideSequences",
    "InletSequences",
    "OutletSequences",
    "ReceiverSequences",
    "SenderSequences",
]
ModelIOSequencesSubtypes = Union[
    "InputSequences", "FactorSequences", "FluxSequences", "StateSequences"
]

InOutSequence = Union["InputSequence", "OutputSequence"]
InOutSequenceTypes = Union[Type["InputSequence"], Type["OutputSequence"]]

Aggregation = Optional[Literal["unmodified", "mean"]]


class FastAccessIOSequence(variabletools.FastAccess):
    """Provides fast access to the values of the |IOSequence| objects of a specific
    subgroup and supports handling time-series data during simulations.

    The following details are of relevance for *HydPy* developers only.

    |sequencetools.FastAccessIOSequence| is applied in Python mode only.  When working
    in Cython mode, it is replaced by model-specific Cython extension classes, which
    are computationally more efficient.  For compatibility with these extension classes,
    |sequencetools.FastAccessIOSequence| objects work with dynamically set instance
    members.  For example, suppose there is a sequence named `seq1`, which is
    2-dimensional, then its associated attributes are:

      * seq1 (|NDArrayFloat|): The actual sequence value(s).
      * _seq1_ndim (|int|): The number of dimensions.
      * _seq1_length_0 (|int|): Length in the first dimension.
      * _seq1_length_1 (|int|): Length in the second dimension.
      * _seq1_ramflag (|bool|): Handle time-series data in RAM?
      * _seq1_array (|NDArrayFloat|): Time-series data (when handled in RAM).
      * _seq1_diskflag_reading (|bool|): Read data from a NetCDF file during simulation?
      * _seq1_diskflag_writing (|bool|): Write data to a NetCDF file during simulation?
      * _seq1_ncarray (|NDArrayFloat|): An array connected with the data slice of the
        NetCDF file relevant for `seq1`.

    Note that the respective |IOSequences| and |IOSequence| objects initialise, change,
    and apply these dynamical attributes.  To handle them directly is error-prone and
    thus not recommended.
    """

    def load_data(self, idx: int) -> None:
        """Load the data of certain sequences from the defined sources.

        The following flags specify the data source (listed in the order of their
        priority):

         * inputflag (|bool|): Take the data from an "input node".
         * diskflag_reading (|bool|): Read the data "on the fly" from a NetCDF file
           during a simulation run.
         * ramflag (|bool|): Take the data from the time-series handled by the
           |IOSequence.series| attribute of the respective |IOSequence| object.

        If, for example, `diskflag_reading` and `ramflag` are both activated,
        |FastAccessIOSequence.load_data| prefers the data available within the NetCDF
        file.
        """
        for name in self:
            ndim = self._get_attribute(name, "ndim")
            inputflag = self._get_attribute(name, "inputflag", False)
            diskflag = self._get_attribute(name, "diskflag_reading")
            ramflag = self._get_attribute(name, "ramflag")
            if inputflag or diskflag or ramflag:
                if inputflag:
                    actual = self._get_attribute(name, "inputpointer")[0]
                elif diskflag:
                    actual = self._get_attribute(name, "ncarray")[0]
                else:
                    actual = self._get_attribute(name, "array")[idx]
                if ndim == 0:
                    setattr(self, name, actual)
                else:
                    getattr(self, name)[:] = actual

    def save_data(self, idx: int) -> None:
        """Save the data of certain sequences to the defined sources.

        The following flags the data targets:

         * diskflag_writing (|bool|): Write the data "on the fly" to a NetCDF file
           during a simulation run.
         * ramflag (|bool|): Give the data to the time-series handled by the
           |IOSequence.series| attribute of the respective |IOSequence| object.

        It is possible to write data to a NetCDF file and pass it to |IOSequence.series|
        simultaneously.
        """
        for name in self:
            actual = getattr(self, name)
            if self._get_attribute(name, "diskflag_writing"):
                try:
                    self._get_attribute(name, "ncarray")[:] = actual.flatten()
                except AttributeError:
                    self._get_attribute(name, "ncarray")[:] = actual
            if self._get_attribute(name, "ramflag"):
                self._get_attribute(name, "array")[idx] = actual


class FastAccessInputSequence(FastAccessIOSequence):
    """|FastAccessIOSequence| subclass specialised for input sequences."""

    def set_pointerinput(self, name: str, pdouble: pointerutils.PDouble) -> None:
        """Use the given |PDouble| object as the pointer for the 0-dimensional
        |InputSequence| object with the given name."""
        setattr(self, f"_{name}_inputpointer", pdouble)


class FastAccessOutputSequence(FastAccessIOSequence):
    """|FastAccessIOSequence| subclass specialised for output sequences."""

    def set_pointeroutput(self, name: str, pdouble: pointerutils.PDouble) -> None:
        """Use the given |PDouble| object as the pointer for the 0-dimensional
        |OutputSequence| object with the given name."""
        self._set_attribute(name, "outputpointer", pdouble)

    def update_outputs(self) -> None:
        """Pass the data of all sequences with an activated output flag."""
        for name in self:
            if self._get_attribute(name, "outputflag", False):
                self._get_attribute(name, "outputpointer")[0] = getattr(self, name)


class FastAccessLinkSequence(variabletools.FastAccess):
    """|FastAccessIOSequence| subclass specialised for link sequences."""

    def alloc(self, name: str, length: int) -> None:
        """Allocate enough memory for the given vector length of the |LinkSequence|
        object with the given name.

        Cython extension classes need to define |FastAccessLinkSequence.alloc| if the
        model handles at least one 1-dimensional |LinkSequence| subclass.
        """
        getattr(self, name).shape = length

    def dealloc(self, name: str) -> None:
        """Free the previously allocated memory of the |LinkSequence| object with the
        given name.

        Cython extension classes need to define |FastAccessLinkSequence.dealloc| if the
        model handles at least one 1-dimensional |LinkSequence| subclass.
        """

    def set_pointer0d(self, name: str, value: pointerutils.Double) -> None:
        """Define a pointer referencing the given |Double| object for the 0-dimensional
        |LinkSequence| object with the given name.

        Cython extension classes need to define |FastAccessLinkSequence.set_pointer0d|
        if the model handles at least one 0-dimensional |LinkSequence| subclasses.
        """
        setattr(self, name, pointerutils.PDouble(value))

    def set_pointer1d(self, name: str, value: pointerutils.Double, idx: int) -> None:
        """Define a pointer referencing the given |Double| object for the 1-dimensional
        |LinkSequence| object with the given name.

        The given index defines the vector position of the defined pointer.

        Cython extension classes need to define |FastAccessLinkSequence.set_pointer1d|
        if the model handles at least one 1-dimensional |LinkSequence| subclasses.
        """
        ppdouble: pointerutils.PPDouble = getattr(self, name)
        ppdouble.set_pointer(value, idx)

    def get_value(self, name: str) -> Union[float, NDArrayFloat]:
        """Return the actual value(s) referenced by the pointer(s) of the
        |LinkSequence| object with the given name."""
        value = getattr(self, name)[:]
        if self._get_attribute(name, "ndim"):
            return numpy.asarray(value, dtype=float)
        return float(value)

    def set_value(self, name: str, value: Mayberable1[float]) -> None:
        """Set the actual value(s) referenced by the pointer(s) of the
        |LinkSequence| object with the given name."""
        getattr(self, name)[:] = value


class FastAccessNodeSequence(FastAccessIOSequence):
    """|sequencetools.FastAccessIOSequence| subclass specialised for |Node| objects.

    In contrast to other |FastAccessIOSequence| subclasses,
    |sequencetools.FastAccessNodeSequence| only needs to handle a fixed number of
    sequences, |Sim| and |Obs|. It thus can define the related attributes explicitly.
    """

    sim: pointerutils.Double
    obs: pointerutils.Double
    _sim_ramflag: bool
    _obs_ramflag: bool
    _sim_array: NDArrayFloat
    _obs_array: NDArrayFloat
    _sim_diskflag_reading: bool
    _sim_diskflag_writing: bool
    _obs_diskflag_reading: bool
    _obs_diskflag_writing: bool
    _sim_ncarray: NDArrayFloat
    _obs_ncarray: NDArrayFloat
    _reset_obsdata: bool

    def load_simdata(self, idx: int) -> None:
        """Load the next sim sequence value from a NetCDF file or, with second priority,
        from the |IOSequence.series| attribute of the current |Sim| object."""
        if self._sim_diskflag_reading:
            self.sim[0] = self._sim_ncarray[0]
        elif self._sim_ramflag:
            self.sim[0] = self._sim_array[idx]

    def save_simdata(self, idx: int) -> None:
        """Save the next sim sequence value to a NetCDF file and/or to the
        |IOSequence.series| attribute of the |Sim| object."""
        if self._sim_diskflag_writing:
            self._sim_ncarray[0] = self.sim[0]
        if self._sim_ramflag:
            self._sim_array[idx] = self.sim[0]

    def load_obsdata(self, idx: int) -> None:
        """Load the next sim sequence value from a NetCDF file or, with second priority,
        from the |IOSequence.series| attribute of the |Obs| object."""
        if self._obs_diskflag_reading:
            self.obs[0] = self._obs_ncarray[0]
        elif self._obs_ramflag:
            self.obs[0] = self._obs_array[idx]

    def save_obsdata(self, idx: int) -> None:
        """Save the next sim sequence value to a NetCDF file and/or to the
        |IOSequence.series| attribute of the |Obs| object."""
        if self._obs_diskflag_writing:
            self._obs_ncarray[0] = self.obs[0]
        if self._obs_ramflag:
            self._obs_array[idx] = self.obs[0]

    def load_data(self, idx: int) -> None:
        """Call both method |sequencetools.FastAccessNodeSequence.load_simdata| and
        method |sequencetools.FastAccessNodeSequence.load_obsdata|."""
        self.load_simdata(idx)
        self.load_obsdata(idx)

    def save_data(self, idx: int) -> None:
        """Call both method |sequencetools.FastAccessNodeSequence.save_simdata| and
        method |sequencetools.FastAccessNodeSequence.save_obsdata|."""
        self.save_simdata(idx)
        self.save_obsdata(idx)

    def reset(self, idx: int = 0) -> None:
        # pylint: disable=unused-argument
        # required for consistincy with the other reset methods.
        """Set the actual value of the simulation sequence to zero."""
        self.sim[0] = 0.0

    def fill_obsdata(self, idx: int = 0) -> None:
        """Use the current sim value for the current `obs` value if obs is
        |numpy.nan|."""
        # pylint: disable=unused-argument
        # required for consistincy with the other reset methods.
        if numpy.isnan(self.obs[0]):
            self._reset_obsdata = True
            self.obs[0] = self.sim[0]

    def reset_obsdata(self, idx: int = 0) -> None:
        """Reset the current `obs` value to |numpy.nan| if modified beforehand by
        method |FastAccessNodeSequence.fill_obsdata|."""
        # pylint: disable=unused-argument
        # required for consistincy with the other reset methods.
        if self._reset_obsdata:
            self.obs[0] = numpy.nan
            self._reset_obsdata = False


class InfoArray(NDArrayFloat):
    """|numpy| |numpy.ndarray| subclass with an additional attribute describing the
    (potential) aggregation of the handled data.

    >>> from hydpy.core.sequencetools import InfoArray
    >>> array = InfoArray([1.0, 2.0], aggregation="mean")
    >>> array
    InfoArray([1., 2.])
    >>> array.aggregation
    'mean'
    >>> subarray = array[:1]
    >>> subarray
    InfoArray([1.])
    >>> subarray.aggregation
    'mean'
    """

    aggregation: Aggregation

    def __new__(cls, array: NDArrayFloat, aggregation: Aggregation = None) -> InfoArray:
        obj = numpy.asarray(array).view(cls)
        obj.aggregation = aggregation
        return obj

    def __array_finalize__(self, obj: NDArrayFloat) -> None:
        if isinstance(obj, InfoArray):
            self.aggregation = obj.aggregation
        else:
            self.aggregation = None


class Sequences:
    """Base class for handling all sequences of a specific model.

    |Sequences| objects handle nine sequence subgroups as attributes such as the
    `inlets` and  the `receivers` subsequences:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> sequences = hp.elements.land_dill.model.sequences
    >>> bool(sequences.inlets)
    False
    >>> bool(sequences.fluxes)
    True

    Iteration makes only the non-empty subgroups available that handle |Sequence_|
    objects:

    >>> for subseqs in sequences:
    ...     print(subseqs.name)
    inputs
    factors
    fluxes
    states
    logs
    aides
    outlets
    >>> len(sequences)
    7

    Keyword access provides a type-safe way to query a subgroup via a string:

    >>> type(sequences["inputs"]).__name__
    'InputSequences'
    >>> type(sequences["wrong"])
    Traceback (most recent call last):
    ...
    TypeError: There is no sequence subgroup named `wrong`.
    >>> sequences["model"]
    Traceback (most recent call last):
    ...
    TypeError: Attribute `model` is of type `Model`, which is not a subtype of class \
`SubSequences`.

    Class |Sequences| provides some methods related to reading and writing time-series
    data, which (directly or indirectly) call the corresponding methods of the handled
    |IOSequence| objects.  In most cases, users should prefer to use the related
    methods of class |HydPy|, but using the ones of class |Sequences| can be more
    convenient when analysing a specific model in-depth.

    To introduce these methods, we first change two IO-related settings:

    >>> from hydpy import round_
    >>> pub.options.checkseries = False
    >>> pub.sequencemanager.overwrite = True

    Method |Sequences.prepare_series| can both enable and disable the handling of
    time-series in rapid access memory (RAM), and both enable and disable the reading
    of input data from NetCDF files and the writing of NetCDF files "on the fly"
    during simulation runs:

    >>> from hydpy import attrready
    >>> sequences.prepare_series(allocate_ram=False, jit=False)
    >>> sequences.inputs.t.ramflag
    False
    >>> attrready(sequences.inputs.t, "series")
    False
    >>> sequences.inputs.t.diskflag
    False
    >>> sequences.inputs.t.diskflag_reading
    False
    >>> sequences.states.sm.diskflag_writing
    False

    >>> sequences.prepare_series()
    >>> sequences.inputs.t.ramflag
    True
    >>> attrready(sequences.inputs.t, "series")
    True
    >>> sequences.inputs.t.diskflag
    False
    >>> sequences.inputs.t.diskflag_reading
    False
    >>> sequences.states.sm.diskflag_writing
    False

    >>> sequences.prepare_series(allocate_ram=False, jit=True)
    >>> sequences.inputs.t.ramflag
    False
    >>> attrready(sequences.inputs.t, "series")
    False
    >>> sequences.inputs.t.diskflag
    True
    >>> sequences.inputs.t.diskflag_reading
    True
    >>> sequences.states.sm.diskflag_writing
    True

    After applying |Sequences.prepare_series|, you can use the methods
    |Sequences.load_series| and |Sequences.save_series| to read or write the time
    series of the relevant |InputSequence|, |FactorSequence|, |FluxSequence|, and
    |StateSequence| object, as the following technical test suggests.  The
    documentation on class |IOSequence| explains the underlying functionalities of in
    more detail.

    >>> from unittest.mock import patch
    >>> template = "hydpy.core.sequencetools.%s.load_series"
    >>> with patch(template % "InputSequences") as inputs, \
patch(template % "FactorSequences") as factors, \
patch(template % "FluxSequences") as fluxes, \
patch(template % "StateSequences") as states:
    ...     sequences.load_series()
    ...     inputs.assert_called_with()
    ...     factors.assert_called_with()
    ...     fluxes.assert_called_with()
    ...     states.assert_called_with()

    >>> template = "hydpy.core.sequencetools.%s.save_series"
    >>> with patch(template % "InputSequences") as inputs, \
patch(template % "FactorSequences") as factors, \
patch(template % "FluxSequences") as fluxes, \
patch(template % "StateSequences") as states:
    ...     sequences.save_series()
    ...     inputs.assert_called_with()
    ...     factors.assert_called_with()
    ...     fluxes.assert_called_with()
    ...     states.assert_called_with()

    .. testsetup::

        >>> from hydpy import Node, Element
        >>> Node.clear_all()
        >>> Element.clear_all()
        >>> pub.options.checkseries = True
        >>> pub.sequencemanager.overwrite = False
    """

    model: modeltools.Model
    inlets: InletSequences
    receivers: ReceiverSequences
    inputs: InputSequences
    factors: FactorSequences
    fluxes: FluxSequences
    states: StateSequences
    logs: LogSequences
    aides: AideSequences
    outlets: OutletSequences
    senders: SenderSequences

    def __init__(
        self,
        model: modeltools.Model,
        cls_inlets: Optional[Type[InletSequences]] = None,
        cls_receivers: Optional[Type[ReceiverSequences]] = None,
        cls_inputs: Optional[Type[InputSequences]] = None,
        cls_factors: Optional[Type[FactorSequences]] = None,
        cls_fluxes: Optional[Type[FluxSequences]] = None,
        cls_states: Optional[Type[StateSequences]] = None,
        cls_logs: Optional[Type[LogSequences]] = None,
        cls_aides: Optional[Type[AideSequences]] = None,
        cls_outlets: Optional[Type[OutletSequences]] = None,
        cls_senders: Optional[Type[SenderSequences]] = None,
        cymodel: Optional[CyModelProtocol] = None,
        cythonmodule: Optional[types.ModuleType] = None,
    ) -> None:
        self.model = model
        self.inlets = self.__prepare_subseqs(
            InletSequences, cls_inlets, cymodel, cythonmodule
        )
        self.receivers = self.__prepare_subseqs(
            ReceiverSequences, cls_receivers, cymodel, cythonmodule
        )
        self.inputs = self.__prepare_subseqs(
            InputSequences, cls_inputs, cymodel, cythonmodule
        )
        self.factors = self.__prepare_subseqs(
            FactorSequences, cls_factors, cymodel, cythonmodule
        )
        self.fluxes = self.__prepare_subseqs(
            FluxSequences, cls_fluxes, cymodel, cythonmodule
        )
        self.states = self.__prepare_subseqs(
            StateSequences, cls_states, cymodel, cythonmodule
        )
        self.logs = self.__prepare_subseqs(
            LogSequences, cls_logs, cymodel, cythonmodule
        )
        self.aides = self.__prepare_subseqs(
            AideSequences, cls_aides, cymodel, cythonmodule
        )
        self.outlets = self.__prepare_subseqs(
            OutletSequences, cls_outlets, cymodel, cythonmodule
        )
        self.senders = self.__prepare_subseqs(
            SenderSequences, cls_senders, cymodel, cythonmodule
        )

    def __prepare_subseqs(
        self,
        default: Type[TypeModelSequences],
        class_: Optional[Type[TypeModelSequences]],
        cymodel,
        cythonmodule,
    ) -> TypeModelSequences:
        name = default.__name__
        if class_ is None:
            class_ = copy.copy(default)
            setattr(class_, "CLASSES", ())
        return class_(self, getattr(cythonmodule, name, None), cymodel)

    @property
    def iosubsequences(self) -> Iterator[ModelIOSequencesSubtypes]:
        """Yield all relevant |IOSequences| objects handled by the current |Sequences|
        object.

        The currently available IO-subgroups are `inputs`, `factors`, `fluxes`, and
        `states`.

        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_v1", "1d")
        >>> for subseqs in model.sequences.iosubsequences:
        ...     print(subseqs.name)
        inputs
        factors
        fluxes
        states

        However, not all models implement sequences for all these subgroups.  Therefore,
        the |Sequences.iosubsequences| property only yields those subgroups which are
        non-empty:

        >>> model = prepare_model("musk_classic", "1d")
        >>> for subseqs in model.sequences.iosubsequences:
        ...     print(subseqs.name)
        fluxes
        states
        """
        if self.inputs:
            yield self.inputs
        if self.factors:
            yield self.factors
        if self.fluxes:
            yield self.fluxes
        if self.states:
            yield self.states

    def prepare_series(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |IOSequences.prepare_series| of attribute |Sequences.inputs|
        with `read_jit=jit` and of attributes |Sequences.factors|, |Sequences.fluxes|,
        and |Sequences.states| with `write_jit=jit`."""
        self.inputs.prepare_series(allocate_ram=allocate_ram, read_jit=jit)
        self.factors.prepare_series(allocate_ram=allocate_ram, write_jit=jit)
        self.fluxes.prepare_series(allocate_ram=allocate_ram, write_jit=jit)
        self.states.prepare_series(allocate_ram=allocate_ram, write_jit=jit)

    def load_series(self):
        """Call method |IOSequences.load_series| of all handled |IOSequences|
        objects."""
        for subseqs in self.iosubsequences:
            subseqs.load_series()

    def save_series(self):
        """Call method |IOSequence.save_series| of all handled |IOSequences|
        objects."""
        for subseqs in self.iosubsequences:
            subseqs.save_series()

    def load_data(self, idx: int) -> None:
        """Call method |ModelIOSequences.load_data| of the handled
        |sequencetools.InputSequences| object."""
        self.inputs.load_data(idx)

    def save_data(self, idx: int) -> None:
        """Call method |ModelIOSequences.save_data| of the handled
        |sequencetools.InputSequences|, |sequencetools.FactorSequences|,
        |sequencetools.FluxSequences|, and |sequencetools.StateSequences| objects."""
        self.inputs.save_data(idx)
        self.factors.save_data(idx)
        self.fluxes.save_data(idx)
        self.states.save_data(idx)

    def update_outputs(self) -> None:
        """Call the method |OutputSequences.update_outputs| of the subattributes
        |Sequences.factors|, |Sequences.fluxes|, and |Sequences.states|.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.factors.update_outputs()
        self.fluxes.update_outputs()
        self.states.update_outputs()

    def reset(self) -> None:
        """Call method |ConditionSequence.reset| of all handled |ConditionSequence|
        objects."""
        self.states.reset()
        self.logs.reset()

    @property
    def conditionsequences(self) -> Iterator[ConditionSequence]:
        """Generator object yielding all conditions (|StateSequence| and |LogSequence|
        objects).
        """
        for state in self.states:
            yield state
        for log in self.logs:
            yield log

    @property
    def conditions(self) -> Dict[str, Dict[str, Union[float, NDArrayFloat]]]:
        """A nested dictionary that contains the values of all condition sequences.

        See the documentation on property |HydPy.conditions| for further information.
        """
        conditions: Dict[str, Dict[str, Union[float, NDArrayFloat]]] = {}
        for seq in self.conditionsequences:
            subconditions = conditions.get(seq.subseqs.name, {})
            subconditions[seq.name] = copy.deepcopy(seq.values)
            conditions[seq.subseqs.name] = subconditions
        return conditions

    @conditions.setter
    def conditions(self, conditions):
        with hydpy.pub.options.trimvariables(False):
            for subname, subconditions in conditions.items():
                subseqs = getattr(self, subname)
                for seqname, values in subconditions.items():
                    getattr(subseqs, seqname)(values)
        for seq in reversed(tuple(self.conditionsequences)):
            seq.trim()

    def load_conditions(self, filename: Optional[str] = None) -> None:
        """Read the initial conditions from a file and assign them to the respective
        |StateSequence| and |LogSequence| objects handled by the actual |Sequences|
        object.

        The documentation on method |HydPy.load_conditions| of class |HydPy| explains
        how to read and write condition values for complete *HydPy* projects in the
        most convenient manner.  However, using the underlying methods
        |Sequences.load_conditions| and |Sequences.save_conditions| directly offers the
        advantage to specify alternative filenames.  We demonstrate this through using
        the `land_dill` |Element| object of the `LahnH` example project and focussing
        on the values of state sequence |hland_states.SM|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> sequences = hp.elements.land_dill.model.sequences
        >>> sequences.states.sm
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)

        We work in the freshly created condition directory `test`:

        >>> with TestIO():
        ...     pub.conditionmanager.currentdir = "test"

        We set all soil moisture values to zero and write the updated values to the
        file `cold_start.py`:

        >>> sequences.states.sm(0.0)
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     sequences.save_conditions("cold_start.py")

        Trying to reload from the written file (after changing the soil moisture values
        again) without passing the file name fails due to the wrong assumption that the
        element's name serves as the file name base:

        >>> sequences.states.sm(100.0)
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     sequences.load_conditions()
        Traceback (most recent call last):
        ...
        FileNotFoundError: While trying to load the initial conditions of element \
`land_dill`, the following error occurred: [Errno 2] No such file or directory: \
'...land_dill.py'

        One does not need to state the file extensions (`.py`) explicitly:

        >>> with TestIO():
        ...     sequences.load_conditions("cold_start")
        >>> sequences.states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        Note that determining the file name automatically requires a proper reference
        to the related |Element| object:

        >>> del sequences.model.element
        >>> with TestIO():
        ...     sequences.save_conditions()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to save the actual conditions of element `?`, the \
following error occurred: To load or save the conditions of a model from or to a file, \
its filename must be known.  This can be done, by passing filename to method \
`load_conditions` or `save_conditions` directly.  But in complete HydPy applications, \
it is usally assumed to be consistent with the name of the element handling the \
model.  Actually, neither a filename is given nor does the model know its master \
element.

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        if self.states or self.logs:
            try:
                dict_ = locals()
                for seq in self.conditionsequences:
                    dict_[seq.name] = seq
                dict_["model"] = self
                filepath = os.path.join(
                    hydpy.pub.conditionmanager.inputpath,
                    self.__prepare_filename(filename),
                )
                runpy.run_path(filepath, init_globals=dict_)
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to load the initial conditions of element "
                    f"`{objecttools.devicename(self)}`"
                )

    def save_conditions(self, filename: Optional[str] = None) -> None:
        """Query the actual conditions of the |StateSequence| and |LogSequence| objects
        handled by the current |Sequences| object and write them into an initial
        condition file.

        See the documentation on method |Sequences.load_conditions| for further
        information.
        """
        try:
            if self.states or self.logs:
                con = hydpy.pub.controlmanager
                lines = [
                    "# -*- coding: utf-8 -*-\n\n",
                    f"from hydpy.models.{self.model} import *\n\n",
                    f'controlcheck(projectdir=r"{con.projectdir}", '
                    f'controldir="{con.currentdir}", '
                    f'stepsize="{hydpy.pub.timegrids.stepsize}")\n\n',
                ]
                for seq in self.conditionsequences:
                    lines.append(repr(seq) + "\n")
                filepath = os.path.join(
                    hydpy.pub.conditionmanager.outputpath,
                    self.__prepare_filename(filename),
                )
                with open(filepath, "w", encoding="utf-8") as file_:
                    file_.writelines(lines)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to save the actual conditions of element "
                f"`{objecttools.devicename(self)}`"
            )

    def __prepare_filename(self, filename: Optional[str]) -> str:
        if filename is None:
            filename = objecttools.devicename(self)
            if filename == "?":
                raise RuntimeError(
                    "To load or save the conditions of a model from or to a file, its "
                    "filename must be known.  This can be done, by passing filename "
                    "to method `load_conditions` or `save_conditions` directly.  But "
                    "in complete HydPy applications, it is usally assumed to be "
                    "consistent with the name of the element handling the model.  "
                    "Actually, neither a filename is given nor does the model know "
                    "its master element."
                )
        if not filename.endswith(".py"):
            filename += ".py"
        return filename

    def trim_conditions(self) -> None:
        """Call method |trim| of each handled |ConditionSequence|.

        |Sequences.trim_conditions| is just a convenience function for calling method
        |trim| of all |StateSequence| and |LogSequence| objects returned by property
        |Sequences.conditionsequences|.  We demonstrate its functionality by preparing
        an instance of application model |lland_v1|, using its available default
        values, and defining out-of-bound values of the soil moisture state sequence
        |lland_states.BoWa|:

        >>> from hydpy import prepare_model, pub
        >>> pub.timegrids = "2000-01-01", "2000-01-10", "1d"
        >>> with pub.options.usedefaultvalues(True):
        ...     model = prepare_model("lland_v1", "1d")
        ...     model.parameters.control.nhru(2)
        >>> model.sequences.states.bowa = -100.0
        >>> model.sequences.trim_conditions()
        >>> model.sequences.states.bowa
        bowa(0.0, 0.0)
        """
        for seq in self.conditionsequences:
            seq.trim()

    def __getitem__(
        self, item: str
    ) -> SubSequences[TypeSequences, Sequence_, variabletools.FastAccess]:
        try:
            subseqs = getattr(self, item)
        except AttributeError:
            raise TypeError(f"There is no sequence subgroup named `{item}`.") from None
        if isinstance(subseqs, SubSequences):
            return subseqs
        raise TypeError(
            f"Attribute `{item}` is of type `{type(subseqs).__name__}`, which is not "
            f"a subtype of class `SubSequences`."
        )

    def __iter__(self) -> Iterator[ModelSequencesSubypes]:
        if self.inlets:
            yield self.inlets
        if self.receivers:
            yield self.receivers
        if self.inputs:
            yield self.inputs
        if self.factors:
            yield self.factors
        if self.fluxes:
            yield self.fluxes
        if self.states:
            yield self.states
        if self.logs:
            yield self.logs
        if self.aides:
            yield self.aides
        if self.outlets:
            yield self.outlets
        if self.senders:
            yield self.senders

    def __len__(self) -> int:
        return sum(1 for _ in self)


class SubSequences(
    variabletools.SubVariables[
        TypeSequences, TypeSequence_co, variabletools.TypeFastAccess_co
    ],
):
    """Base class for handling subgroups of sequences.

    Each |SubSequences| object has a `fastaccess` attribute, which is an instance of (a
    subclass of) class |FastAccess| when working in pure Python mode:

    >>> from hydpy import classname, Node, prepare_model, pub
    >>> with pub.options.usecython(False):
    ...     model = prepare_model("lland_v1")
    >>> classname(model.sequences.logs.fastaccess)
    'FastAccess'
    >>> classname(model.sequences.inputs.fastaccess)
    'FastAccessInputSequence'
    >>> from hydpy.core.sequencetools import FastAccessNodeSequence
    >>> with pub.options.usecython(False):
    ...     node = Node("test1")
    >>> isinstance(node.sequences.fastaccess, FastAccessNodeSequence)
    True

    When working in Cython mode (the default and much faster than the pure Python mode),
    `fastaccess` is an object of the Cython extension class `FastAccessNodeSequence` of
    module `sequenceutils` or a Cython extension class specialised for the respective
    model and sequence group:

    >>> with pub.options.usecython(True):
    ...     model = prepare_model("lland_v1")
    >>> classname(model.sequences.inputs.fastaccess)
    'InputSequences'
    >>> from hydpy.cythons.sequenceutils import FastAccessNodeSequence
    >>> with pub.options.usecython(True):
    ...     node = Node("test2")
    >>> isinstance(Node("test2").sequences.fastaccess, FastAccessNodeSequence)
    True

    See the documentation of similar class |SubParameters| for further information.
    However, note the difference that model developers should not subclass
    |SubSequences| directly but specialised subclasses like
    |sequencetools.FluxSequences| or |sequencetools.StateSequences| instead.

    .. testsetup::

        >>> Node.clear_all()
    """

    @property
    def name(self) -> str:
        """The class name in lower case letters omitting the last eight characters
        ("equences").

        >>> from hydpy.core.sequencetools import StateSequences
        >>> class StateSequences(StateSequences):
        ...     CLASSES = ()
        >>> StateSequences(None).name
        'states'
        """
        return type(self).__name__[:-8].lower()


class ModelSequences(
    SubSequences[Sequences, TypeModelSequence_co, variabletools.TypeFastAccess_co],
):
    """Base class for handling model-related subgroups of sequences."""

    seqs: Sequences
    _cymodel: Optional[CyModelProtocol]

    def __init__(
        self,
        master: Sequences,
        cls_fastaccess: Optional[Type[variabletools.TypeFastAccess_co]] = None,
        cymodel: Optional[CyModelProtocol] = None,
    ) -> None:
        self.seqs = master
        self._cymodel = cymodel
        super().__init__(
            master=master,
            cls_fastaccess=cls_fastaccess,
        )

    def __hydpy__initialise_fastaccess__(self) -> None:
        super().__hydpy__initialise_fastaccess__()
        if self._cls_fastaccess and self._cymodel:
            setattr(self._cymodel.sequences, self.name, self.fastaccess)


class IOSequences(
    SubSequences[TypeSequences, TypeIOSequence_co, TypeFastAccessIOSequence_co],
):
    """Subclass of |SubSequences|, specialised for handling |IOSequence| objects."""

    def prepare_series(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all handled |IOSequence|
        objects."""
        for seq in self:
            seq.prepare_series(
                allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
            )

    def load_series(self) -> None:
        """Call method |IOSequence.load_series| of all handled |IOSequence| objects
        with an activated |IOSequence.ramflag|."""
        for seq in self:
            if seq.ramflag:
                seq.load_series()

    def save_series(self) -> None:
        """Call method |IOSequence.save_series| of all handled |IOSequence| objects
        with an activated |IOSequence.ramflag|."""
        for seq in self:
            if seq.ramflag:
                seq.save_series()


class ModelIOSequences(
    IOSequences[Sequences, TypeModelIOSequence_co, TypeFastAccessIOSequence_co],
    ModelSequences[TypeModelIOSequence_co, TypeFastAccessIOSequence_co],
):
    """Base class for handling model-related subgroups of |IOSequence| objects."""

    def load_data(self, idx: int) -> None:
        """Call method |FastAccessIOSequence.load_data| of the |FastAccessIOSequence|
        object handled as attribute `fastaccess`."""
        self.fastaccess.load_data(idx)

    def save_data(self, idx: int) -> None:
        """Call method |FastAccessIOSequence.save_data| of the |FastAccessIOSequence|
        object handled as attribute `fastaccess`."""
        self.fastaccess.save_data(idx)


class InputSequences(
    ModelIOSequences["InputSequence", FastAccessInputSequence],
):
    """Base class for handling |InputSequence| objects."""

    _CLS_FASTACCESS_PYTHON = FastAccessInputSequence


class OutputSequences(
    ModelIOSequences[TypeOutputSequence_co, FastAccessOutputSequence]
):
    """Base class for handling |OutputSequence| objects."""

    _CLS_FASTACCESS_PYTHON = FastAccessOutputSequence

    def update_outputs(self) -> None:
        """Call method |FastAccessOutputSequence.update_outputs| of the
        |FastAccessOutputSequence| object handled as attribute `fastaccess`."""
        if self:
            self.fastaccess.update_outputs()

    @property
    def numericsequences(self) -> Iterator[TypeOutputSequence_co]:
        """Iterator for "numerical" sequences.

        "numerical" means that the |Sequence_.NUMERIC| class attribute of the actual
        sequence is |True|:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("dam_v001")
        >>> len(model.sequences.fluxes)
        14
        >>> for seq in model.sequences.fluxes.numericsequences:
        ...     print(seq)
        adjustedprecipitation(nan)
        actualevaporation(nan)
        inflow(nan)
        actualrelease(nan)
        flooddischarge(nan)
        outflow(nan)
        """
        for flux in self:
            if flux.NUMERIC:
                yield flux


class FactorSequences(OutputSequences["FactorSequence"]):
    """Base class for handling |FactorSequence| objects."""


class FluxSequences(OutputSequences["FluxSequence"]):
    """Base class for handling |FluxSequence| objects."""

    @property
    def name(self) -> str:
        """Always return the string "fluxes"."""
        return "fluxes"


class StateSequences(OutputSequences["StateSequence"]):
    """Base class for handling |StateSequence| objects."""

    fastaccess_new: FastAccessOutputSequence
    fastaccess_old: variabletools.FastAccess

    def __hydpy__initialise_fastaccess__(self) -> None:
        super().__hydpy__initialise_fastaccess__()
        self.fastaccess_new = self.fastaccess
        if (self._cls_fastaccess is None) or (self._cymodel is None):
            self.fastaccess_old = variabletools.FastAccess()
        else:
            setattr(self._cymodel.sequences, "new_states", self.fastaccess)
            self.fastaccess_old = self._cls_fastaccess()
            setattr(self._cymodel.sequences, "old_states", self.fastaccess_old)

    def new2old(self) -> None:
        """Call method |StateSequence.new2old| of all handled |StateSequence|
        objects."""
        for seq in self:
            seq.new2old()

    def reset(self) -> None:
        """Call method |ConditionSequence.reset| of all handled |StateSequence|
        objects."""
        for seq in self:
            seq.reset()


class LogSequences(ModelSequences["LogSequence", variabletools.FastAccess]):
    """Base class for handling |LogSequence| objects."""

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess

    def reset(self) -> None:
        """Call method |ConditionSequence.reset| of all handled |LogSequence|
        objects."""
        for seq in self:
            seq.reset()


class AideSequences(ModelSequences["AideSequence", variabletools.FastAccess]):
    """Base class for handling |AideSequence| objects."""

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess


class LinkSequences(ModelSequences[TypeLinkSequence_co, FastAccessLinkSequence]):
    """Base class for handling |LinkSequence| objects."""

    _CLS_FASTACCESS_PYTHON = FastAccessLinkSequence


class InletSequences(LinkSequences["InletSequence"]):
    """Base class for handling "inlet" |LinkSequence| objects."""


class OutletSequences(LinkSequences["OutletSequence"]):
    """Base class for handling "outlet" |LinkSequence| objects."""


class ReceiverSequences(LinkSequences["ReceiverSequence"]):
    """Base class for handling "receiver" |LinkSequence| objects."""


class SenderSequences(LinkSequences["SenderSequence"]):
    """Base class for handling "sender" |LinkSequence| objects."""


class Sequence_(variabletools.Variable):
    """Base class for defining different kinds of sequences.

    Note that model developers should not derive their model-specific sequence classes
    from |Sequence_| directly but from the "final" subclasses provided in module
    |sequencetools| (e.g. |FluxSequence|).

    From the model developer perspective and especially from the user perspective,
    |Sequence_| is only a small extension of its base class |Variable|.  One relevant
    extension is that (only the) 0-dimensional sequence objects come with a predefined
    shape:

    >>> from hydpy import prepare_model
    >>> model = prepare_model("lland_v1", "1d")
    >>> model.sequences.fluxes.qa.shape
    ()
    >>> evpo = model.sequences.fluxes.evpo
    >>> evpo.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable \
`evpo` can only be retrieved after it has been defined.

    For consistency with the usage of |Parameter| subclasses, |Sequence_| objects are
    also "callable" for setting their values (but in a much less and flexible manner):

    >>> evpo.shape = 3
    >>> evpo(2.0)
    >>> evpo
    evpo(2.0, 2.0, 2.0)

    Under the hood, class |Sequence_| also prepares some attributes of its |FastAccess|
    object, used for performing the actual simulation calculations.   Framework
    developers should note that the respective `fastaccess` attributes contain both the
    name of the sequence and the name of the original attribute in lower case letters.
    We take `NDIM` as an example:

    >>> evpo.fastaccess._evpo_ndim
    1

    Some of these attributes require updating in some situations.  For example, other
    sequences than |AideSequence| objects require a "length" attribute, which needs
    updating each time the sequence's shape changes:

    >>> evpo.fastaccess._evpo_length
    3
    """

    TYPE: Type[float] = float
    INIT: float = 0.0
    NUMERIC: bool

    subvars: Union[
        SubSequences[Sequences, Sequence_, variabletools.FastAccess],
        SubSequences[devicetools.Node, Sequence_, variabletools.FastAccess],
    ]
    """The subgroup to which the sequence belongs."""
    subseqs: Union[
        SubSequences[Sequences, Sequence_, variabletools.FastAccess],
        SubSequences[devicetools.Node, Sequence_, variabletools.FastAccess],
    ]
    """Alias for |Sequence_.subvars|."""
    strict_valuehandling: bool = False

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._set_fastaccessattribute("ndim", self.NDIM)
        self._set_fastaccessattribute("length", 0)
        for idx in range(self.NDIM):
            self._set_fastaccessattribute(f"length_{idx}", 0)

    def _get_fastaccessattribute(self, suffix: str, default: object = None) -> Any:
        return getattr(self.fastaccess, f"_{self.name}_{suffix}", default)

    def _set_fastaccessattribute(self, suffix: str, value: Any) -> None:
        setattr(self.fastaccess, f"_{self.name}_{suffix}", value)

    def _finalise_connections(self) -> None:
        """A hook method, called at the end of method
        `__hydpy__connect_variable2subgroup__` for initialising values and some
        attributes."""
        if not self.NDIM:
            self.shape = ()

    @property
    def initinfo(self) -> Tuple[Union[float, pointerutils.Double], bool]:
        """A |tuple| containing the initial value and |True| or a missing value and
        |False|, depending on the actual |Sequence_| subclass and the actual value of
        option |Options.usedefaultvalues|.

        In the following, we do not explain property |Sequence_.initinfo| itself but
        show how it affects initialising new |Sequence_| objects.  Therefore, let us
        define a sequence test class and prepare a function for initialising it and
        connecting the resulting instance to a |ModelSequences| object:

        >>> from hydpy.core.sequencetools import Sequence_, ModelSequences
        >>> from hydpy.core.variabletools import FastAccess
        >>> class Test(Sequence_):
        ...     NDIM = 0
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> class SubGroup(ModelSequences):
        ...     CLASSES = (Test,)
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> def prepare():
        ...     subseqs = SubGroup(None)
        ...     test = Test(subseqs)
        ...     test.__hydpy__connect_variable2subgroup__()
        ...     return test

        By default, making use of the `INIT` attribute is disabled:

        >>> prepare()
        test(nan)

        Enable it by setting |Options.usedefaultvalues| to |True|:

        >>> from hydpy import pub
        >>> with pub.options.usedefaultvalues(True):
        ...     prepare()
        test(0.0)

        Attribute `INIT` of class |Sequence_| comes with the value `0.0` by default,
        which should be reasonable for most |Sequence_| subclasses.  However,
        subclasses can define other values.  Most importantly, note the possibility to
        set `INIT` to `None` for sequences that do not allow specifying a reasonabe
        initial value for all possible situations:

        >>> Test.INIT = None
        >>> prepare()
        test(nan)
        >>> with pub.options.usedefaultvalues(True):
        ...     prepare()
        test(nan)
        """
        if hydpy.pub.options.usedefaultvalues and self.INIT is not None:
            return self.INIT, True
        return numpy.nan, False

    def __repr__(self) -> str:
        brackets = (self.NDIM == 2) and (self.shape[0] != 1)
        return variabletools.to_repr(self, self.value, brackets)


class IOSequence(Sequence_):
    """Base class for sequences with input/output functionalities.

    The documentation on modules |filetools| and |netcdftools| in some detail explains
    how to read and write time series files.  However, due to efficiency, reading and
    writing time series files are disabled by default.  Therefore, you must first
    prepare the |IOSequence.series| attribute of the relevant |IOSequence| objects.
    Typically, you call methods like |HydPy.prepare_inputseries| of class |HydPy|.
    Here, we instead use the related features of the |IOSequence| class itself.

    We use the `LahnH` example project and focus on the `input`, `factor`, `fluxes`,
    and `state` sequences:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> inputs = hp.elements.land_lahn_1.model.sequences.inputs
    >>> factors = hp.elements.land_lahn_1.model.sequences.factors
    >>> fluxes = hp.elements.land_lahn_1.model.sequences.fluxes
    >>> states = hp.elements.land_lahn_1.model.sequences.states

    Each |IOSequence| object comes four flags, answering the following questions:

     * |IOSequence.ramflag|: can its time-series can be available in RAM?
     * |IOSequence.diskflag_reading|: read its values "on the fly" from a NetCDF file
       during simulation runs?
     * |IOSequence.diskflag_writing|:write its values "on the fly" to a NetCDF file
       during simulation runs?
     * |IOSequence.diskflag|: is |IOSequence.diskflag_reading| and/or
       |IOSequence.diskflag_writing| activated?

    For input sequences as |hland_inputs.T|, it is common to store their time-series
    data (required for any simulation run) in RAM, which is much faster than
    (repeatedly) reading data "on the fly" and should be preferred, as long as limited
    available RAM is not an issue.  For convenience, function |prepare_full_example_2|
    prepared |hland_inputs.T| (and the other input sequences) accordingly:

    >>> inputs.t.ramflag
    True
    >>> inputs.t.diskflag_reading
    False
    >>> inputs.t.diskflag_writing
    False
    >>> inputs.t.diskflag
    False
    >>> from hydpy import round_
    >>> round_(inputs.t.series)
    -0.705395, -1.505553, -4.221268, -7.446349

    |prepare_full_example_2| also activated the |IOSequence.ramflag| of all factor,
    flux, and state sequences, which is unnecessary to perform a successful simulation.
    However, it is required to directly access the complete time series of simulated
    values afterwards (otherwise, only the last computed value(s) were available in
    RAM after a simulation run):

    >>> factors.tc.ramflag
    True
    >>> factors.tc.diskflag
    False
    >>> round_(factors.tc.series[:, 0])
    nan, nan, nan, nan

    Use |IOSequence.prepare_series| to force a sequence to handle time-series data in
    RAM or to read or write it on the fly.  We now activate the reading functionality
    of input sequence |hland_inputs.T| (while still keeping its time-series in RAM,
    which we set to zero beforehand) and the writing feature of the factor sequences
    |hland_factors.TMean| and |hland_factors.TC| (without handling their data in RAM)
    and the writing feature of the state sequences |hland_states.SM| and
    |hland_states.SP| (while handling their data in RAM simultaneously):

    >>> inputs.t.series = 0.0
    >>> inputs.t.prepare_series(allocate_ram=True, read_jit=True)
    >>> factors.tmean.prepare_series(allocate_ram=False, write_jit=True)
    >>> factors.tc.prepare_series(allocate_ram=False, write_jit=True)
    >>> states.sm.prepare_series(allocate_ram=True, write_jit=True)
    >>> states.sp.prepare_series(allocate_ram=True, write_jit=True)

    Use the properties |IOSequence.ramflag|, |IOSequence.diskflag_reading|,
    |IOSequence.diskflag_writing|, and |IOSequence.diskflag| for querying the current
    configuration of individual |IOSequence| objects:

    >>> inputs.t.ramflag
    True
    >>> inputs.t.diskflag_reading
    True
    >>> inputs.t.diskflag_writing
    False
    >>> inputs.t.diskflag
    True
    >>> round_(inputs.t.series)
    0.0, 0.0, 0.0, 0.0

    >>> factors.tmean.ramflag
    False
    >>> factors.tmean.diskflag_reading
    False
    >>> factors.tmean.diskflag_writing
    True
    >>> factors.tmean.diskflag
    True
    >>> factors.tmean.series
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Sequence `tmean` of element \
`land_lahn_1` is not requested to make any time-series data available.

    >>> states.sm.ramflag
    True
    >>> states.sm.diskflag_reading
    False
    >>> states.sm.diskflag_writing
    True
    >>> states.sm.diskflag
    True
    >>> round_(states.sm.series[:, 0])
    nan, nan, nan, nan

    Now we perform a simulation run.  Note that we need to change the current working
    directory to the `iotesting` directory temporarily (by using class |TestIO|)
    because the relevant NetCDF files are now read and written on the fly:

    >>> with TestIO():
    ...     hp.simulate()

    After the simulation run, the read (|hland_inputs.T|) and calculated
    (|hland_states.SM| and |hland_states.SP|) time-series of the sequences with an
    activated |IOSequence.ramflag| are directly available:

    >>> round_(inputs.t.series)
    -0.705395, -1.505553, -4.221268, -7.446349
    >>> round_(states.sm.series[:, 0])
    99.134954, 98.919762, 98.76352, 98.574428
    >>> round_(states.sp.series[:, 0, 0])
    0.0, 0.0, 0.0, 0.0

    To inspect the time series of |hland_factors.TMean| and |hland_factors.TC|, you
    must first activate their |IOSequence.ramflag| and then load their data manually
    with method |IOSequence.load_series|.  The latter requires some additional
    configuration effort (see the documentation on module |netcdftools| for further
    information):

    >>> factors.tmean.prepare_series()
    >>> factors.tc.prepare_series()
    >>> pub.sequencemanager.filetype = "nc"
    >>> with TestIO():
    ...     pub.sequencemanager.open_netcdfreader()
    ...     factors.tmean.load_series()
    ...     factors.tc.load_series()
    ...     pub.sequencemanager.close_netcdfreader()
    >>> round_(factors.tmean.series)
    -0.988481, -1.788639, -4.504354, -7.729436
    >>> round_(factors.tc.series[:, 0])
    0.164605, -0.635553, -3.351268, -6.576349

    We also load time series of |hland_states.SM| and |hland_states.SP| to demonstrate
    that the data written to the respective NetCDF files are identical with the data
    directly stored in RAM:

    >>> with TestIO():
    ...     pub.sequencemanager.open_netcdfreader()
    ...     states.sm.load_series()
    ...     states.sp.load_series()
    ...     pub.sequencemanager.close_netcdfreader()
    >>> round_(states.sm.series[:, 0])
    99.134954, 98.919762, 98.76352, 98.574428
    >>> round_(states.sp.series[:, 0, 0])
    0.0, 0.0, 0.0, 0.0

    Writing the time series of input sequences on the fly is supported but not
    simultaneously with reading them (at best, one would overwrite the same file with
    the same data; at worst, one could corrupt it):

    >>> inputs.t.prepare_series(read_jit=True, write_jit=True)
    Traceback (most recent call last):
    ...
    ValueError: Reading from and writing into the same NetCDF file "just in time" \
during a simulation run is not supported but tried for sequence `t` of element \
`land_lahn_1`.

    For simplifying the following examples, we now handle all model time series in RAM:

    >>> pub.sequencemanager.filetype = "asc"
    >>> hp.prepare_modelseries()
    >>> with TestIO():
    ...     hp.load_inputseries()

    You cannot only access the time-series data of individual |IOSequence| objects, but
    you can also modify it.  See, for example, the simulated time series for flux
    sequence |hland_fluxes.PC| (adjusted precipitation), which is zero because the
    values of input sequence |hland_inputs.P| (given precipitation) are also zero:

    >>> round_(fluxes.pc.series[:, 0])
    0.0, 0.0, 0.0, 0.0

    We can assign different values to attribute |IOSequence.series| of sequence
    |hland_inputs.P|, perform a new simulation run, and see that the newly calculated
    time series of sequence |hland_fluxes.PC| reflects our data modification:

    >>> inputs.p.series = 10.0
    >>> hp.simulate()
    >>> round_(fluxes.pc.series[:, 0])
    10.22607, 11.288565, 11.288565, 11.288565

    Another convenience property is |IOSequence.seriesshape|, which combines the length
    of the simulation period with the shape of the individual |IOSequence| object:

    >>> inputs.p.seriesshape
    (4,)
    >>> fluxes.pc.seriesshape
    (4, 13)

    Note that resetting the |IOSequence.shape| of an |IOSequence| object does not
    change how it handles its internal time-series data but results in a loss of
    current information:

    >>> factors.tc.seriesshape
    (4, 13)
    >>> factors.fastaccess._tc_length
    13
    >>> round_(factors.tc.series[:, 0], 1)
    0.2, -0.6, -3.4, -6.6

    >>> factors.tc.shape = 2,
    >>> factors.tc.seriesshape
    (4, 2)
    >>> factors.fastaccess._tc_length
    2
    >>> round_(factors.tc.series[:, 0])
    nan, nan, nan, nan

    Resetting the |IOSequence.shape| of |IOSequence| objects with a deactivated
    |IOSequence.ramflag| data works likewise:

    >>> fluxes.pc.prepare_series(allocate_ram=False)

    >>> fluxes.pc.seriesshape
    (4, 13)
    >>> fluxes.fastaccess._pc_length
    13
    >>> fluxes.pc.series
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Sequence `pc` of element \
`land_lahn_1` is not requested to make any time-series data available.

    >>> fluxes.pc.shape = (2,)
    >>> fluxes.pc.seriesshape
    (4, 2)
    >>> fluxes.fastaccess._pc_length
    2
    >>> fluxes.pc.series = 1.0
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Sequence `pc` of element \
`land_lahn_1` is not requested to make any time-series data available.

    .. testsetup::

        >>> from hydpy import Node, Element
        >>> Node.clear_all()
        >>> Element.clear_all()
    """

    subvars: Union[
        SubSequences[Sequences, IOSequence, FastAccessIOSequence],
        SubSequences[devicetools.Node, IOSequence, FastAccessIOSequence],
    ]
    """The subgroup to which the IO sequence belongs."""
    subseqs: Union[
        SubSequences[Sequences, IOSequence, FastAccessIOSequence],
        SubSequences[devicetools.Node, IOSequence, FastAccessIOSequence],
    ]
    """Alias for |IOSequence.subvars|."""
    fastaccess: FastAccessIOSequence
    """Object for accessing the IO sequence's data with little overhead."""

    def _finalise_connections(self) -> None:
        self._set_fastaccessattribute("ramflag", False)
        self._set_fastaccessattribute("diskflag_reading", False)
        self._set_fastaccessattribute("diskflag_writing", False)
        super()._finalise_connections()

    @propertytools.DefaultPropertySeriesFileType
    def filetype(self) -> SeriesFileType:
        """"Ending of the time-series data file.

        Usually, |IOSequence| objects query the current file type from the
        |SequenceManager| object available in the global |pub| module:

        >>> from hydpy import pub
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        >>> from hydpy.core.sequencetools import InputSequence
        >>> inputsequence = InputSequence(None)
        >>> inputsequence.filetype
        'asc'

        Alternatively, you can specify the file type for each |IOSequence| object
        individually:

        >>> inputsequence.filetype = "npy"
        >>> inputsequence.filetype
        'npy'
        >>> inputsequence.filetype = "nc"
        >>> inputsequence.filetype
        'nc'

        Use the `del` statement to reset the object-specific setting:

        >>> del inputsequence.filetype
        >>> inputsequence.filetype
        'asc'

        If neither a specific definition nor a |SequenceManager| object is available,
        property |IOSequence.filetype| raises the following error:

        >>> del pub.sequencemanager
        >>> inputsequence.filetype
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Sequence `inputsequence` does \
not know its file type.  Either set it manually or prepare `pub.sequencemanager` \
correctly.
        """
        try:
            return hydpy.pub.sequencemanager.filetype
        except exceptiontools.AttributeNotReady:
            raise exceptiontools.AttributeNotReady(
                f"Sequence {objecttools.devicephrase(self)} does not know its file "
                f"type.  Either set it manually or prepare `pub.sequencemanager` "
                f"correctly."
            ) from None

    @propertytools.DefaultPropertySeriesAggregationType
    def aggregation(self) -> SeriesAggregationType:
        """Type of aggregation for writing the time-series to a data file.

        Usually, |IOSequence| objects query the current aggregation mode from the
        |SequenceManager| object available in the global |pub| module:

        >>> from hydpy import pub
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        >>> from hydpy.core.sequencetools import FluxSequence
        >>> fluxsequence = FluxSequence(None)
        >>> fluxsequence.aggregation
        'none'

        Alternatively, you can specify the aggregation for each |IOSequence| object
        individually:

        >>> fluxsequence.aggregation = "mean"
        >>> fluxsequence.aggregation
        'mean'

        Use the `del` statement to reset the object-specific setting:

        >>> del fluxsequence.aggregation
        >>> fluxsequence.aggregation
        'none'

        If neither a specific definition nor a |SequenceManager| object is available,
        property |IOSequence.aggregation| raises the following error:

        >>> del pub.sequencemanager
        >>> fluxsequence.aggregation
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Sequence `fluxsequence` does not \
know its aggregation mode.  Either set it manually or prepare `pub.sequencemanager` \
correctly.
        """
        try:
            return hydpy.pub.sequencemanager.aggregation
        except exceptiontools.AttributeNotReady:
            raise exceptiontools.AttributeNotReady(
                f"Sequence {objecttools.devicephrase(self)} does not know its "
                f"aggregation mode.  Either set it manually or prepare "
                f"`pub.sequencemanager` correctly."
            ) from None

    @propertytools.DefaultPropertyBool
    def overwrite(self) -> bool:
        """True/False flag indicating if overwriting an existing data file is allowed
        or not.

        Usually, |IOSequence| objects query the current overwrite flag from the
        |SequenceManager| object available in the global |pub| module:

        >>> from hydpy import pub
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        >>> from hydpy.core.sequencetools import FluxSequence
        >>> fluxsequence = FluxSequence(None)
        >>> fluxsequence.overwrite
        0

        Alternatively, you can specify the overwrite flag for each |IOSequence| object
        individually:

        >>> fluxsequence.overwrite = True
        >>> fluxsequence.overwrite
        1

        Use the `del` statement to reset the object-specific setting:

        >>> del fluxsequence.overwrite
        >>> fluxsequence.overwrite
        0

        If neither a specific definition nor a |SequenceManager| object is available,
        property |IOSequence.overwrite| raises the following error:

        >>> del pub.sequencemanager
        >>> fluxsequence.overwrite
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Sequence `fluxsequence` does not \
know its overwrite flag.  Either set it manually or prepare `pub.sequencemanager` \
correctly.
        """
        try:
            return hydpy.pub.sequencemanager.overwrite
        except exceptiontools.AttributeNotReady:
            raise exceptiontools.AttributeNotReady(
                f"Sequence {objecttools.devicephrase(self)} does not know its "
                f"overwrite flag.  Either set it manually or prepare "
                f"`pub.sequencemanager` correctly."
            ) from None

    @propertytools.DefaultPropertyStr
    def filename(self) -> str:  # ToDo: special handling for NetCDF files
        """The filename of the relevant time series file.

        By default, the filename consists of |IOSequence.descr_device|,
        |IOSequence.descr_sequence|, and |IOSequence.filetype|:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> class S(StateSequence):
        ...     descr_device = "dev"
        ...     descr_sequence = "seq"
        ...     filetype = "npy"
        >>> S(None).filename
        'dev_seq.npy'
        """
        return f"{self.descr_device}_{self.descr_sequence}.{self.filetype}"

    @propertytools.DefaultPropertyStr
    def dirpath(self) -> str:
        """The absolute path to the time series directory.

        As long as not overwritten, |IOSequence.dirpath| is identical with the
        attribute |FileManager.currentpath| of the |SequenceManager| object
        available in module |pub|:

        >>> from hydpy import pub, repr_
        >>> from hydpy.core.filetools import SequenceManager
        >>> class SM(SequenceManager):
        ...     currentpath = "temp"
        >>> pub.sequencemanager = SM()
        >>> from hydpy.core.sequencetools import StateSequence
        >>> repr_(StateSequence(None).dirpath)
        'temp'
        """
        return hydpy.pub.sequencemanager.currentpath

    @propertytools.DefaultPropertyStr
    def filepath(self) -> str:
        """The absolute path to the time series file.

        The path pointing to the file consists of |IOSequence.dirpath| and
        |IOSequence.filename|:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> seq = StateSequence(None)
        >>> seq.dirpath = "path"
        >>> seq.filename = "file.npy"
        >>> from hydpy import repr_
        >>> repr_(seq.filepath)
        'path/file.npy'
        """
        return os.path.join(self.dirpath, self.filename)

    def update_fastaccess(self) -> None:
        """Update the |FastAccessIOSequence| object handled by the actual |IOSequence|
        object.

        Users do not need to apply the method |IOSequence.update_fastaccess| directly.
        The following information should be relevant for framework developers only.

        The main documentation on class |Sequence_| mentions that the
        |FastAccessIOSequence| attribute handles some information about its sequences,
        but it needs to be kept up-to-date by the sequences themselves.  This updating
        is the task of method |IOSequence.update_fastaccess|, being called by some
        other methods class |IOSequence| call.  We show this via the hidden attribute
        `length`, which is 0 after initialisation, and automatically set to another
        value when assigning it to property |IOSequence.shape| of |IOSequence|
        subclasses as |lland_fluxes.NKor|:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("lland_v1")
        >>> nkor = model.sequences.fluxes.nkor
        >>> nkor.fastaccess._nkor_length
        0
        >>> nkor.shape = (3,)
        >>> nkor.fastaccess._nkor_length
        3
        """
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
            self._set_fastaccessattribute(f"length_{idx}", self.shape[idx])
        self._set_fastaccessattribute("length", length)

    def connect_netcdf(self, ncarray: NDArrayFloat) -> None:
        """Connect the current |IOSequence| object to the given buffer array for
        reading from or writing to a NetCDF file on the fly during a simulation run."""
        self._set_fastaccessattribute("ncarray", ncarray)

    def prepare_series(
        self,
        allocate_ram: Optional[bool] = True,
        read_jit: Optional[bool] = False,
        write_jit: Optional[bool] = False,
    ) -> None:
        """Define how to handle the time-series data of the current |IOSequence| object.

        See the main documentation on class |IOSequence| for general information on
        method |IOSequence.prepare_series|.  Here, we only discuss the special case of
        passing |None| to it to preserve predefined settings.

        When leaving out certain arguments, |IOSequence.prepare_series| takes their
        boolean defaults.  That means subsequent calls overwrite previous ones:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> t = hp.elements.land_lahn_1.model.sequences.inputs.t
        >>> t.prepare_series(allocate_ram=False, read_jit=True)
        >>> t.ramflag, t.diskflag_reading, t.diskflag_writing
        (False, True, False)
        >>> t.prepare_series(write_jit=True)
        >>> t.ramflag, t.diskflag_reading, t.diskflag_writing
        (True, False, True)

        If you want to change one setting without modifying the others, pass |None| to
        the latter:

        >>> t.prepare_series(allocate_ram=False, read_jit=None, write_jit=None)
        >>> t.ramflag, t.diskflag_reading, t.diskflag_writing
        (False, False, True)
        >>> t.prepare_series(allocate_ram=None, read_jit=True, write_jit=False)
        >>> t.ramflag, t.diskflag_reading, t.diskflag_writing
        (False, True, False)
        >>> t.prepare_series(allocate_ram=None, read_jit=None, write_jit=None)
        >>> t.ramflag, t.diskflag_reading, t.diskflag_writing
        (False, True, False)

        The check for configurations attempting to both read and write "just in time"
        takes predefined flags into account:

        >>> t.prepare_series(read_jit=None, write_jit=True)
        Traceback (most recent call last):
        ...
        ValueError: Reading from and writing into the same NetCDF file "just in time" \
during a simulation run is not supported but tried for sequence `t` of element \
`land_lahn_1`.

        >>> t.prepare_series(read_jit=False, write_jit=True)
        >>> t.prepare_series(read_jit=True, write_jit=None)
        Traceback (most recent call last):
        ...
        ValueError: Reading from and writing into the same NetCDF file "just in time" \
during a simulation run is not supported but tried for sequence `t` of element \
`land_lahn_1`.
        """
        readflag = read_jit or ((read_jit is None) and self.diskflag_reading)
        writeflag = write_jit or ((write_jit is None) and self.diskflag_writing)
        if readflag and writeflag:
            raise ValueError(
                f'Reading from and writing into the same NetCDF file "just in time" '
                f"during a simulation run is not supported but tried for sequence "
                f"{objecttools.devicephrase(self)}."
            )
        if allocate_ram is not None:
            ramflag = self.ramflag
            if allocate_ram and not ramflag:
                self.__set_array(numpy.full(self.seriesshape, numpy.nan, dtype=float))
            if ramflag and not allocate_ram:
                del self.series
            self._set_fastaccessattribute("ramflag", allocate_ram)
        if read_jit is not None:
            inflag = self._get_fastaccessattribute("inputflag", False)
            self._set_fastaccessattribute("diskflag_reading", read_jit and not inflag)
        if write_jit is not None:
            self._set_fastaccessattribute("diskflag_writing", write_jit)
        self.update_fastaccess()

    @property
    def ramflag(self) -> bool:
        """A flag telling if the actual |IOSequence| object makes its time-series data
        directly available in RAM.

        See the main documentation on class |IOSequence| for further information.
        """
        return self._get_fastaccessattribute("ramflag")

    @property
    def diskflag_reading(self) -> bool:
        """A flag telling if the actual |IOSequence| reads its time-series data on the
        fly from a NetCDF file during a simulation run.

        See the main documentation on class |IOSequence| for further information.
        """
        return self._get_fastaccessattribute("diskflag_reading")

    @property
    def diskflag_writing(self) -> bool:
        """A flag telling if the actual |IOSequence| writes its time-series data on the
        fly to a NetCDF file during a simulation run.

        See the main documentation on class |IOSequence| for further information.
        """
        return self._get_fastaccessattribute("diskflag_writing")

    @property
    def diskflag(self) -> bool:
        """A flag telling if |IOSequence.diskflag_reading| and/or
        |IOSequence.diskflag_writing| of the current |IOSequence| object is |True|:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> for reading in (False, True):
        ...     for writing in (False, True):
        ...         class S(StateSequence):
        ...             diskflag_reading = reading
        ...             diskflag_writing = writing
        ...         print(reading, writing, S(None).diskflag)
        False False False
        False True True
        True False True
        True True True
        """
        return self.diskflag_reading or self.diskflag_writing

    @property
    def memoryflag(self) -> bool:
        """A flag telling if either |IOSequence.ramflag| and/or |IOSequence.diskflag|
        of the current |IOSequence| object is |True|:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> for ram in (False, True):
        ...     for disk in (False, True):
        ...         class S(StateSequence):
        ...             ramflag = ram
        ...             diskflag = disk
        ...         print(ram, disk, S(None).memoryflag)
        False False False
        False True True
        True False True
        True True True
        """
        return self.ramflag or self.diskflag

    def __set_array(self, values):
        values = numpy.array(values, dtype=float)
        self._set_fastaccessattribute("array", values)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        When setting a new |IOSequence.shape| of an |IOSequence| object, one
        automatically calls method |IOSequence.update_fastaccess| and, if necessary,
        prepares the new internal |IOSequence.series| array.

        See the main documentation on class |IOSequence| for further information.
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]):
        super().__hydpy__set_shape__(shape)
        if self.ramflag:
            values = numpy.full(self.seriesshape, numpy.nan, dtype=float)
            self.__set_array(values)
        self.update_fastaccess()

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)

    @property
    def seriesshape(self) -> Tuple[int, ...]:
        """The shape of the whole time-series (time being the first dimension)."""
        seriesshape = [len(hydpy.pub.timegrids.init)]
        seriesshape.extend(self.shape)
        return tuple(seriesshape)

    def _get_series(self) -> InfoArray:
        """The complete time-series data of the current |IOSequence| object within an
        |InfoArray| covering the whole initialisation period (defined by the
        |Timegrids.init| |Timegrid| of the global |Timegrids| object available in
        module |pub|)."""
        if self.ramflag:
            array = numpy.asarray(self._get_fastaccessattribute("array"))
            return InfoArray(array, aggregation="unmodified")
        raise exceptiontools.AttributeNotReady(
            f"Sequence {objecttools.devicephrase(self)} is not requested to make any "
            f"time-series data available."
        )

    def _set_series(self, values) -> None:
        if self.ramflag:
            self.__set_array(numpy.full(self.seriesshape, values, dtype=float))
            self.check_completeness()
        else:
            raise exceptiontools.AttributeNotReady(
                f"Sequence {objecttools.devicephrase(self)} is not requested to make "
                f"any time-series data available."
            )

    def _del_series(self) -> None:
        if self.ramflag:
            self._set_fastaccessattribute("array", None)
            self._set_fastaccessattribute("ramflag", False)

    series = property(_get_series, _set_series, _del_series)

    def _get_simseries(self) -> InfoArray:
        """Read and write access to the subset of the data of property
        |IOSequence.series| covering the actual simulation period (defined by the
        |Timegrids.sim| |Timegrid| of the global |Timegrids| object available in module
        |pub|).

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> t = hp.elements.land_lahn_1.model.sequences.inputs.t
        >>> pub.timegrids.sim.dates = "1996-01-02", "1996-01-04"
        >>> from hydpy import print_values
        >>> print_values(t.series)
        -0.705395, -1.505553, -4.221268, -7.446349
        >>> print_values(t.simseries)
        -1.505553, -4.221268
        >>> t.simseries = 1.0, 2.0
        >>> print_values(t.series)
        -0.705395, 1.0, 2.0, -7.446349

        .. testsetup::

            >>> from hydpy import Element, Node
            >>> Element.clear_all()
            >>> Node.clear_all()
        """
        idx0, idx1 = hydpy.pub.timegrids.simindices
        return self.series[idx0:idx1]

    def _set_simseries(self, values) -> None:
        idx0, idx1 = hydpy.pub.timegrids.simindices
        self.series[idx0:idx1] = values

    simseries = property(_get_simseries, _set_simseries)

    def _get_evalseries(self) -> InfoArray:
        """Read and write access to the subset of the data of property |
        IOSequence.series| covering the actual evaluation period (defined by the
        |Timegrids.eval_| |Timegrid| of the global |Timegrids| object available in
        module |pub|).

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> t = hp.elements.land_lahn_1.model.sequences.inputs.t
        >>> pub.timegrids.eval_.dates = "1996-01-02", "1996-01-04"
        >>> from hydpy import print_values
        >>> print_values(t.series)
        -0.705395, -1.505553, -4.221268, -7.446349
        >>> print_values(t.evalseries)
        -1.505553, -4.221268
        >>> t.evalseries = 1.0, 2.0
        >>> print_values(t.series)
        -0.705395, 1.0, 2.0, -7.446349

        .. testsetup::

            >>> from hydpy import Element, Node
            >>> Element.clear_all()
            >>> Node.clear_all()
        """
        idx0, idx1 = hydpy.pub.timegrids.evalindices
        return self.series[idx0:idx1]

    def _set_evalseries(self, values) -> None:
        idx0, idx1 = hydpy.pub.timegrids.evalindices
        self.series[idx0:idx1] = values

    evalseries = property(_get_evalseries, _set_evalseries)

    def load_series(self) -> None:
        """Read time-series data from a file.

        Method |IOSequence.load_series| only calls method |SequenceManager.load_file|
        of class |SequenceManager| passing itself as the only argument.  Hence, see the
        documentation on the class |SequenceManager| for further information.  The
        following example only shows the error messages when |SequenceManager.load_file|
        is missing due to incomplete project configurations:

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.sequencemanager

        >>> from hydpy.core.sequencetools import StateSequence
        >>> StateSequence(None).load_series()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to load the \
time-series data of `statesequence`, the following error occurred: Attribute \
sequencemanager of module `pub` is not defined at the moment.
        """
        try:
            sequencemanager = hydpy.pub.sequencemanager
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to load the time-series data of "
                f"{objecttools.devicephrase(self)}"
            )
        sequencemanager.load_file(self)

    def adjust_series(
        self, timegrid_data: timetools.Timegrid, values: NDArrayFloat
    ) -> NDArrayFloat:
        """Adjust a time-series to the current initialisation period.

        Note that, in most *HydPy* applications, method |IOSequence.adjust_series| is
        called by other methods related to reading data from files and does not need to
        be called by the user directly.  However, if  you want to call it directly for
        some reason, you need to make sure that the shape of the given |numpy|
        |numpy.ndarray| fits the given |Timegrid| object.

        Often, time-series data available in data files cover a longer period than
        required for an actual simulation run.  Method |IOSequence.adjust_series|
        selects the relevant data by comparing the initialisation |Timegrid| available
        in module |pub| and the given "data" |Timegrid| object.  We explain this
        behaviour by using the `LahnH` example project and focussing on the |Obs|
        sequence of |Node| `dill`:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> obs = hp.nodes.dill.sequences.obs

        With identical initialisation and data time grids, method
        |IOSequence.adjust_series| returns the given data completely:

        >>> from hydpy import Timegrid
        >>> import numpy
        >>> with TestIO(), pub.options.checkseries(False):
        ...     obs.adjust_series(Timegrid("1996-01-01", "1996-01-05", "1d"),
        ...                       numpy.arange(4, dtype=float))
        array([0., 1., 2., 3.])

        For "too long" data, it only returns the relevant one:

        >>> with TestIO(), pub.options.checkseries(False):
        ...     obs.adjust_series(Timegrid("1995-12-31", "1996-01-07", "1d"),
        ...                       numpy.arange(7, dtype=float))
        array([1., 2., 3., 4.])

        For "too short" data, the behaviour differs depending on option
        |Options.checkseries|.  With |Options.checkseries| being enabled, method
        |IOSequence.adjust_series| raises a |RuntimeError|.  With |Options.checkseries|
        being disabled, it extends the given array with |numpy.nan| values (using
        method |IOSequence.adjust_short_series|):

        >>> with TestIO(), pub.options.checkseries(True):
        ...     obs.adjust_series(Timegrid("1996-01-02", "1996-01-04", "1d"),
        ...                       numpy.zeros((3,)))   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: For sequence `obs` of node `dill` the initialisation time grid \
(Timegrid("1996-01-01 00:00:00", "1996-01-05 00:00:00", "1d")) does not define a \
subset of the time grid of the data file `...dill_obs_q.asc` \
(Timegrid("1996-01-02 00:00:00", "1996-01-04 00:00:00", "1d")).

        >>> with TestIO(), pub.options.checkseries(False):
        ...     obs.adjust_series(Timegrid("1996-01-02", "1996-01-04", "1d"),
        ...                       numpy.zeros((2,)))
        array([nan,  0.,  0., nan])

        Additional checks raise errors in case of non-matching shapes or time
        information:

        >>> with TestIO():
        ...     obs.adjust_series(Timegrid("1996-01-01", "1996-01-05", "1d"),
        ...                       numpy.zeros((5, 2)))   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The shape of sequence `obs` of node `dill` is `()` but \
according to the data file `...dill_obs_q.asc` it should be `(2,)`.

        >>> with TestIO():
        ...     obs.adjust_series(Timegrid("1996-01-01", "1996-01-05", "1h"),
        ...                       numpy.zeros((24*5,)))   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: According to data file `...dill_obs_q.asc`, the date time step \
of sequence `obs` of node `dill` is `1h` but the actual simulation time step is `1d`.

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        if self.shape != values.shape[1:]:
            raise RuntimeError(
                f"The shape of sequence {objecttools.devicephrase(self)} is "
                f"`{self.shape}` but according to the data file `{self.filepath}` it "
                f"should be `{values.shape[1:]}`."
            )
        if hydpy.pub.timegrids.init.stepsize != timegrid_data.stepsize:
            raise RuntimeError(
                f"According to data file `{self.filepath}`, the date time step of "
                f"sequence {objecttools.devicephrase(self)} is "
                f"`{timegrid_data.stepsize}` but the actual simulation time step is "
                f"`{hydpy.pub.timegrids.init.stepsize}`."
            )
        if hydpy.pub.timegrids.init not in timegrid_data:
            if hydpy.pub.options.checkseries:
                raise RuntimeError(
                    f"For sequence {objecttools.devicephrase(self)} the initialisation "
                    f"time grid ({hydpy.pub.timegrids.init}) does not define a subset "
                    f"of the time grid of the data file `{self.filepath}` "
                    f"({timegrid_data})."
                )
            return self.adjust_short_series(timegrid_data, values)
        idx1 = timegrid_data[hydpy.pub.timegrids.init.firstdate]
        idx2 = timegrid_data[hydpy.pub.timegrids.init.lastdate]
        return values[idx1:idx2]

    def adjust_short_series(
        self, timegrid: timetools.Timegrid, values: NDArrayFloat
    ) -> NDArrayFloat:
        """Adjust a short time-series to a longer time grid.

        Mostly, time-series data to be read from files should span (at least) the whole
        initialisation period of a *HydPy* project.  However, incomplete time series
        might also be helpful for some variables used only for comparison (e.g.
        observed runoff used for calibration).  Method |IOSequence.adjust_short_series|
        adjusts such incomplete series to the public initialisation time grid stored in
        module |pub|.  It is automatically called in method |IOSequence.adjust_series|
        when necessary, provided that the option |Options.checkseries| is disabled.

        Assume the initialisation period of a HydPy project spans five days:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000.01.10", "2000.01.15", "1d"

        Prepare a node series object for observational data:

        >>> from hydpy.core.sequencetools import Obs
        >>> obs = Obs(None)

        Prepare a test function that expects the time grid of the data and the data
        itself, which returns the adjusted array through invoking the method
        |IOSequence.adjust_short_series|:

        >>> import numpy
        >>> def test(timegrid):
        ...     values = numpy.ones(len(timegrid))
        ...     return obs.adjust_short_series(timegrid, values)

        The following calls to the test function show the arrays returned for different
        kinds of misalignments:

        >>> from hydpy import Timegrid
        >>> test(Timegrid("2000.01.05", "2000.01.20", "1d"))
        array([1., 1., 1., 1., 1.])
        >>> test(Timegrid("2000.01.12", "2000.01.15", "1d"))
        array([nan, nan,  1.,  1.,  1.])
        >>> test(Timegrid("2000.01.12", "2000.01.17", "1d"))
        array([nan, nan,  1.,  1.,  1.])
        >>> test(Timegrid("2000.01.10", "2000.01.13", "1d"))
        array([ 1.,  1.,  1., nan, nan])
        >>> test(Timegrid("2000.01.08", "2000.01.13", "1d"))
        array([ 1.,  1.,  1., nan, nan])
        >>> test(Timegrid("2000.01.12", "2000.01.13", "1d"))
        array([nan, nan,  1., nan, nan])
        >>> test(Timegrid("2000.01.05", "2000.01.10", "1d"))
        array([nan, nan, nan, nan, nan])
        >>> test(Timegrid("2000.01.05", "2000.01.08", "1d"))
        array([nan, nan, nan, nan, nan])
        >>> test(Timegrid("2000.01.15", "2000.01.18", "1d"))
        array([nan, nan, nan, nan, nan])
        >>> test(Timegrid("2000.01.16", "2000.01.18", "1d"))
        array([nan, nan, nan, nan, nan])

        After enabling option |Options.usedefaultvalues|, the missing values are
        initialised with zero instead of nan:

        >>> with pub.options.usedefaultvalues(True):
        ...     test(Timegrid("2000.01.12", "2000.01.17", "1d"))
        array([0., 0., 1., 1., 1.])
        """
        idxs = [
            timegrid[hydpy.pub.timegrids.init.firstdate],
            timegrid[hydpy.pub.timegrids.init.lastdate],
        ]
        valcopy = values
        values = numpy.full(self.seriesshape, float(self.initinfo[0]))
        len_ = len(valcopy)
        jdxs = []
        for idx in idxs:
            if idx < 0:
                jdxs.append(0)
            elif idx <= len_:
                jdxs.append(idx)
            else:
                jdxs.append(len_)
        valcopy = valcopy[jdxs[0] : jdxs[1]]
        zdx1 = max(-idxs[0], 0)
        zdx2 = zdx1 + jdxs[1] - jdxs[0]
        values[zdx1:zdx2] = valcopy
        return values

    def check_completeness(self) -> None:
        """Raise a |RuntimeError| if the |IOSequence.series| contains at least one
        |numpy.nan| value and if the option |Options.checkseries| is enabled.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-11", "1d"
        >>> from hydpy.core.sequencetools import StateSequence, StateSequences
        >>> class Seq(StateSequence):
        ...     NDIM = 0
        ...     NUMERIC = False
        >>> class StateSequences(StateSequences):
        ...     CLASSES = (Seq,)
        >>> seq = Seq(StateSequences(None))
        >>> seq.__hydpy__connect_variable2subgroup__()
        >>> seq.prepare_series()
        >>> seq.check_completeness()
        Traceback (most recent call last):
        ...
        RuntimeError: The series array of sequence `seq` contains 10 nan values.

        >>> seq.series = 1.0
        >>> seq.check_completeness()

        >>> seq.series[3] = numpy.nan
        >>> seq.check_completeness()
        Traceback (most recent call last):
        ...
        RuntimeError: The series array of sequence `seq` contains 1 nan value.

        >>> with pub.options.checkseries(False):
        ...     seq.check_completeness()
        """
        if hydpy.pub.options.checkseries:
            isnan = numpy.isnan(self.series)
            if numpy.any(isnan):
                nmb = numpy.sum(isnan)
                valuestring = "value" if nmb == 1 else "values"
                raise RuntimeError(
                    f"The series array of sequence {objecttools.devicephrase(self)} "
                    f"contains {nmb} nan {valuestring}."
                )

    def save_series(self) -> None:
        """Write the time-series data of the current |IOSequence| object to a file.

        Method |IOSequence.save_series| only calls method |SequenceManager.save_file|
        of class |SequenceManager|, passing itself as the only argument.  Hence, see
        the documentation on class the |SequenceManager| for further information.  The
        following example only shows the error messages when |SequenceManager.save_file|
        is missing due to incomplete project configurations:

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.sequencemanager

        >>> from hydpy.core.sequencetools import StateSequence
        >>> StateSequence(None).save_series()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to save the \
time-series data of `statesequence`, the following error occurred: Attribute \
sequencemanager of module `pub` is not defined at the moment.
        """
        try:
            sequencemanager = hydpy.pub.sequencemanager
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to save the time-series data of "
                f"{objecttools.devicephrase(self)}"
            )
        sequencemanager.save_file(self)

    def save_mean(self, *args, **kwargs) -> None:
        """Average the time-series data with method |IOSequence.average_series| of
        class |IOSequence| and write the result to file using method
        |SequenceManager.save_file| of class |SequenceManager|.

        The main documentation on class |SequenceManager| provides some examples.
        """
        array = InfoArray(self.average_series(*args, **kwargs), aggregation="mean")
        hydpy.pub.sequencemanager.save_file(self, array=array)

    @property
    def seriesmatrix(self) -> Matrix[float]:
        """The actual |IOSequence| object's time series, arranged in a 2-dimensional
        matrix.

        For a 1-dimensional sequence object, property |IOSequence.seriesmatrix| returns
        the original values without modification:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"
        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(2)
        >>> fluxes.pc.prepare_series()
        >>> fluxes.pc.series = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        >>> from hydpy import print_values
        >>> for values in fluxes.pc.seriesmatrix:
        ...     print_values(values)
        1.0, 2.0
        3.0, 4.0
        5.0, 6.0

        For all other sequences, |IOSequence.seriesmatrix| raises the following error
        by default:

        >>> inputs.p.seriesmatrix
        Traceback (most recent call last):
        ...
        NotImplementedError: Sequence `p` does not implement a method for converting \
its series to a 2-dimensional matrix.
        """
        if self.NDIM == 1:
            return self.series
        raise NotImplementedError(
            f"Sequence {objecttools.devicephrase(self)} does not implement a method "
            f"for converting its series to a 2-dimensional matrix."
        )

    def average_series(self, *args, **kwargs) -> InfoArray:
        """Average the actual time-series of the |IOSequence| object for all time
        points.

        Method |IOSequence.average_series| works similarly to method
        |Variable.average_values| of class |Variable|, from which we borrow some
        examples. However, we must first prepare a |Timegrids| object to define the
        |IOSequence.series| length:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

        As shown for method |Variable.average_values|, for 0-dimensional |IOSequence|
        objects, the result of method |IOSequence.average_series| equals
        |IOSequence.series| itself:

        >>> from hydpy.core.sequencetools import StateSequence, StateSequences
        >>> class SoilMoisture(StateSequence):
        ...     NDIM = 0
        ...     NUMERIC = False
        >>> class StateSequences(StateSequences):
        ...     CLASSES = (SoilMoisture,)
        >>> sm = SoilMoisture(StateSequences(None))
        >>> sm.__hydpy__connect_variable2subgroup__()
        >>> sm.prepare_series()
        >>> import numpy
        >>> sm.series = numpy.array([190.0, 200.0, 210.0])
        >>> sm.average_series()
        InfoArray([190., 200., 210.])

        We require a weighting parameter for |IOSequence| objects with an increased
        dimensionality:

        >>> SoilMoisture.NDIM = 1
        >>> sm.shape = 3
        >>> sm.prepare_series()
        >>> sm.series = ([190.0, 390.0, 490.0],
        ...              [200.0, 400.0, 500.0],
        ...              [210.0, 410.0, 510.0])
        >>> from hydpy.core.parametertools import Parameter
        >>> class Area(Parameter):
        ...     NDIM = 1
        ...     shape = (3,)
        ...     value = numpy.array([1.0, 1.0, 2.0])
        >>> area = Area(None)
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> sm.average_series()
        InfoArray([390., 400., 410.])

        The documentation on method |Variable.average_values| provides many examples of
        using different masks in different ways.  Here, we only show the results of
        method |IOSequence.average_series| for a mask selecting the first two entries,
        for a mask selecting no entry at all, and for an ill-defined mask:

        >>> from hydpy.core.masktools import DefaultMask
        >>> class Soil(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask(maskvalues)
        >>> SoilMoisture.mask = Soil()

        >>> maskvalues = [True, True, False]
        >>> sm.average_series()
        InfoArray([290., 300., 310.])

        >>> maskvalues = [False, False, False]
        >>> sm.average_series()
        InfoArray([nan, nan, nan])

        >>> maskvalues = [True, True]
        >>> sm.average_series()
        Traceback (most recent call last):
        ...
        IndexError: While trying to calculate the mean value of the internal \
time-series of sequence `soilmoisture`, the following error occurred: While trying to \
access the value(s) of variable `area` with key `[ True  True]`, the following error \
occurred: boolean index did not match indexed array along dimension 0; dimension is 3 \
but corresponding boolean dimension is 2
        """
        try:
            if not self.NDIM:
                array = self.series
            else:
                mask = self.get_submask(*args, **kwargs)
                if numpy.any(mask):
                    weights = self.refweights[mask]
                    weights /= numpy.sum(weights)
                    series = self.seriesmatrix[:, mask]
                    array = numpy.sum(weights * series, axis=1)
                else:
                    array = numpy.full(len(self.series), numpy.nan, dtype=float)
            return InfoArray(array, aggregation="mean")
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to calculate the mean value of the internal "
                f"time-series of sequence {objecttools.devicephrase(self)}"
            )

    def aggregate_series(self, *args, **kwargs) -> InfoArray:
        """Aggregate the time-series data based on the actual |IOSequence.aggregation|
        attribute of the current |IOSequence| object.

        We prepare some nodes and elements with the help of method
        |prepare_io_example_1| and select a 1-dimensional flux sequence of type
        |lland_fluxes.NKor|:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> seq = elements.element3.model.sequences.fluxes.nkor

        If |IOSequence.aggregation| is `none`, the original time-series values are
        returned:

        >>> seq.aggregation
        'none'
        >>> seq.aggregate_series()
        InfoArray([[24., 25., 26.],
                   [27., 28., 29.],
                   [30., 31., 32.],
                   [33., 34., 35.]])

        If |IOSequence.aggregation| is `mean`, method |IOSequence.aggregate_series| is
        called:

        >>> seq.aggregation = "mean"
        >>> seq.aggregate_series()
        InfoArray([25., 28., 31., 34.])

        In case the state of the sequence is invalid:

        >>> seq.aggregation = "nonexistent"
        >>> seq.aggregate_series()
        Traceback (most recent call last):
        ...
        RuntimeError: Unknown aggregation mode `nonexistent` for sequence `nkor` of \
element `element3`.

        The following technical test confirms the propr passing of all potential
        positional and keyword arguments:

        >>> seq.aggregation = "mean"
        >>> from unittest import mock
        >>> seq.average_series = mock.MagicMock()
        >>> _ = seq.aggregate_series(1, x=2)
        >>> seq.average_series.assert_called_with(1, x=2)
        """
        mode = self.aggregation
        if mode == "none":  # pylint: disable=comparison-with-callable
            return self.series
        if mode == "mean":  # pylint: disable=comparison-with-callable
            return self.average_series(*args, **kwargs)
        raise RuntimeError(
            f"Unknown aggregation mode `{mode}` for sequence "
            f"{objecttools.devicephrase(self)}."
        )

    @property
    @abc.abstractmethod
    def descr_sequence(self) -> str:
        """Description of the |IOSequence| object and its context."""

    @property
    @abc.abstractmethod
    def descr_device(self) -> str:
        """Description of the |Device| object the |IOSequence| object belongs to."""


class ModelSequence(Sequence_):
    """Base class for sequences to be handled by |Model| objects."""

    subvars: ModelSequences[ModelSequence, variabletools.FastAccess]
    """The subgroup to which the model sequence belongs."""
    subseqs: ModelSequences[ModelSequence, variabletools.FastAccess]
    """Alias for |ModelSequence.subvars|."""

    def __init__(
        self, subvars: ModelSequences[ModelSequence, variabletools.FastAccess]
    ) -> None:
        super().__init__(subvars)
        self.subseqs = subvars

    @property
    def descr_sequence(self) -> str:
        """Description of the |ModelSequence| object itself and the |SubSequences|
        group it belongs to.

        >>> from hydpy import prepare_model
        >>> from hydpy.models import test_v1
        >>> model = prepare_model(test_v1)
        >>> model.sequences.fluxes.q.descr_sequence
        'flux_q'
        """
        return f"{type(self.subseqs).__name__[:-9].lower()}_{self.name}"

    @property
    def descr_model(self) -> str:
        """Description of the |Model| the |ModelSequence| object belongs to.

        >>> from hydpy import prepare_model
        >>> from hydpy.models import test, test_v1
        >>> model = prepare_model(test)
        >>> model.sequences.fluxes.q.descr_model
        'test'
        >>> model = prepare_model(test_v1)
        >>> model.sequences.fluxes.q.descr_model
        'test_v1'
        """
        return self.subseqs.seqs.model.__module__.split(".")[2]

    @property
    def descr_device(self) -> str:
        """Description of the |Element| object the |ModelSequence| object belongs to.

        >>> from hydpy import prepare_model, Element
        >>> element = Element("test_element_1")
        >>> from hydpy.models import test_v1
        >>> model = prepare_model(test_v1)
        >>> model.sequences.fluxes.q.descr_device
        '?'
        >>> element.model = model
        >>> model.sequences.fluxes.q.descr_device
        'test_element_1'
        """
        element = self.subseqs.seqs.model.element
        if element:
            return element.name
        return "?"

    @property
    def numericshape(self) -> Tuple[int, ...]:
        """The shape of the array of temporary values required for the relevant
        numerical solver.

        The class |ELSModel|, being the base of the "dam" model, uses the "Explicit
        Lobatto Sequence" for solving differential equations and therefore requires up
        to eleven array fields for storing temporary values.  Hence, the
        |ModelSequence.numericshape| of the 0-dimensional sequence |dam_fluxes.Inflow|
        is eleven:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("dam")
        >>> model.sequences.fluxes.inflow.numericshape
        (11,)

        Changing the |IOSequence.shape| through a little trick (just for demonstration
        purposes) shows that there are eleven entries for each "normal"
        |dam_fluxes.Inflow| value:

        >>> from hydpy.models.dam.dam_fluxes import Inflow
        >>> shape = Inflow.shape
        >>> Inflow.shape = (2,)
        >>> model.sequences.fluxes.inflow.numericshape
        (11, 2)
        >>> Inflow.shape = shape

        Erroneous configurations result in the following error:

        >>> del model.numconsts
        >>> model.sequences.fluxes.inflow.numericshape
        Traceback (most recent call last):
        ...
        AttributeError: The `numericshape` of a sequence like `inflow` depends on the \
configuration of the actual integration algorithm.  While trying to query the \
required configuration data `nmb_stages` of the model associated with element `?`, \
the following error occurred: 'Model' object has no attribute 'numconsts'
        """
        from hydpy.core import modeltools  # pylint: disable=import-outside-toplevel

        try:
            model = self.subseqs.seqs.model
            assert isinstance(model, modeltools.ELSModel)  # ToDo
            numericshape = [model.numconsts.nmb_stages]
        except AttributeError:
            objecttools.augment_excmessage(
                f"The `numericshape` of a sequence like `{self.name}` depends on the "
                f"configuration of the actual integration algorithm.  While trying to "
                f"query the required configuration data `nmb_stages` of the model "
                f"associated with element `{objecttools.devicename(self)}`"
            )
        numericshape.extend(self.shape)
        return tuple(numericshape)


class ModelIOSequence(ModelSequence, IOSequence):
    """Base class for sequences with time-series functionalities to be handled by
    |Model| objects."""

    subvars: ModelIOSequences[ModelIOSequence, FastAccessIOSequence]
    """The subgroup to which the model IO sequence belongs."""
    subseqs: ModelIOSequences[ModelIOSequence, FastAccessIOSequence]
    """Alias for |ModelIOSequence.subvars|."""


class InputSequence(ModelIOSequence):
    """Base class for input sequences of |Model| objects.

    |InputSequence| objects provide their master model with input data, which is
    possible in two ways: either by providing their individually managed data (usually
    read from file) or data shared with an input node (usually calculated by another
    model).  This flexibility allows, for example, to let application model |hland_v1|
    read already preprocessed precipitation time-series or to couple it with
    application models like |conv_v001|, which interpolates precipitation during the
    simulation run.

    The second mechanism (coupling |InputSequence| objects with input nodes) is
    relatively new, and we might adjust the relevant interfaces in the future.  As soon
    as we finally settle things, we will improve the following example and place it
    more prominently.  In short, it shows that working with both types of input data
    sources at the same time works well and that the different |Node.deploymode|
    options are supported:

    >>> from hydpy import Element, FusedVariable, HydPy, Node, print_values, pub, TestIO
    >>> from hydpy.inputs import  hland_T, hland_P
    >>> hp = HydPy("LahnH")
    >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
    >>> node_t = Node("node_t", variable=hland_T)
    >>> node_p = Node("node_p", variable=FusedVariable("Precip", hland_P))
    >>> node_q = Node("node_q")
    >>> land_dill = Element("land_dill",
    ...                     inputs=[node_t, node_p],
    ...                     outlets=node_q)

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> import os
    >>> with TestIO():
    ...     os.chdir("LahnH/control/default")
    ...     with open("land_dill.py") as controlfile:
    ...         exec(controlfile.read(), {}, locals())
    ...     parameters.update()
    ...     land_dill.model = model

    >>> model.sequences.inputs.t.inputflag
    True
    >>> model.sequences.inputs.p.inputflag
    True
    >>> model.sequences.inputs.epn.inputflag
    False

    >>> hp.update_devices(nodes=[node_t, node_p, node_q], elements=land_dill)
    >>> hp.prepare_inputseries()
    >>> hp.prepare_factorseries()
    >>> hp.prepare_fluxseries()
    >>> with TestIO():
    ...     hp.load_inputseries()

    >>> hp.nodes.prepare_allseries()
    >>> node_t.deploymode = "oldsim"
    >>> node_t.sequences.sim.series = 1.0, 2.0, 3.0, 4.0, 5.0
    >>> node_p.deploymode = "obs"
    >>> node_p.sequences.obs.series = 0.0, 4.0, 0.0, 8.0, 0.0

    >>> hp.simulate()

    >>> print_values(model.sequences.inputs.t.series)
    1.0, 2.0, 3.0, 4.0, 5.0
    >>> print_values(model.sequences.factors.tc.series[:, 0])
    2.05, 3.05, 4.05, 5.05, 6.05
    >>> print_values(model.sequences.inputs.p.series)
    0.0, 4.0, 0.0, 8.0, 0.0
    >>> print_values(model.sequences.fluxes.pc.series[:, 0])
    0.0, 3.441339, 0.0, 6.882678, 0.0
    >>> print_values(model.sequences.inputs.epn.series)
    0.285483, 0.448182, 0.302786, 0.401946, 0.315023
    >>> print_values(model.sequences.fluxes.epc.series[:, 0])
    0.314763, 0.524569, 0.46086, 0.689852, 0.630047

    .. testsetup::

        >>> Element.clear_all()
        >>> Node.clear_all()
        >>> FusedVariable.clear_registry()
    """

    subvars: InputSequences
    """The subgroup to which the input sequence belongs."""
    subseqs: InputSequences
    """Alias for |InputSequence.subvars|."""
    fastaccess: FastAccessInputSequence
    """Object for accessing the input sequence's data with little overhead."""

    _CLS_FASTACCESS_PYTHON = FastAccessInputSequence

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._set_fastaccessattribute("inputflag", False)

    def set_pointer(self, double: pointerutils.Double) -> None:
        """Prepare a pointer referencing the given |Double| object.

        Method |InputSequence.set_pointer| should be relevant for framework developers
        and eventually for some model developers only.
        """
        pdouble = pointerutils.PDouble(double)
        self.fastaccess.set_pointerinput(self.name, pdouble)
        self._set_fastaccessattribute("inputflag", True)
        self._set_fastaccessattribute("diskflag_reading", False)
        self._set_fastaccessattribute("diskflag_writing", False)

    @property
    def inputflag(self) -> bool:
        """A flag telling if the actual |InputSequence| object queries its data from an
        input node (|True|) or uses individually managed data, usually read from a data
        file (|False|).

        See the main documentation on class |InputSequence| for further information.
        """
        return self._get_fastaccessattribute("inputflag")


class OutputSequence(ModelIOSequence):
    """Base class for |FactorSequence|, |FluxSequence| and |StateSequence|.

    |OutputSequence| subclasses implement an optional output mechanism.  Generally, as
    all instances of |ModelSequence| subclasses, output sequences handle values
    calculated within a simulation time step.  With an activated
    |OutputSequence.outputflag|, they also pass their internal values to an output node
    (see the documentation on class |Element|), which makes them accessible to other
    models.

    This output mechanism (coupling |OutputSequence| objects with output nodes) is
    relatively new, and we might adjust the relevant interfaces in the future.
    Additionally, it works for 0-dimensional output sequences only so far.  As soon as
    we finally settle things, we will improve the following example and place it more
    prominently.  In short, it shows that everything works well for the different
    |Node.deploymode| options:

    >>> from hydpy import Element, HydPy, Node, print_values, pub, Selection, TestIO
    >>> from hydpy.outputs import hland_Perc, hland_Q0, hland_Q1, hland_UZ
    >>> hp = HydPy("LahnH")
    >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
    >>> node_q0 = Node("node_q0", variable=hland_Q0)
    >>> node_q1 = Node("node_q1", variable=hland_Q1)
    >>> node_perc = Node("node_perc", variable=hland_Perc)
    >>> node_uz = Node("node_uz", variable=hland_UZ)
    >>> node_q = Node("node_q")
    >>> land_dill = Element("land_dill",
    ...                     outlets=node_q,
    ...                     outputs=[node_q0, node_q1, node_perc, node_uz])

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> import os
    >>> with TestIO():
    ...     os.chdir("LahnH/control/default")
    ...     with open("land_dill.py") as controlfile:
    ...         exec(controlfile.read(), {}, locals())
    ...     parameters.update()
    ...     land_dill.model = model

    >>> model.sequences.fluxes.q0.outputflag
    True
    >>> model.sequences.fluxes.q1.outputflag
    True
    >>> model.sequences.fluxes.perc.outputflag
    True
    >>> model.sequences.fluxes.qt.outputflag
    False
    >>> model.sequences.states.uz.outputflag
    True
    >>> model.sequences.states.lz.outputflag
    False

    >>> hp.update_devices(nodes=[node_q0, node_q1, node_perc, node_uz],
    ...                   elements=land_dill)
    >>> with TestIO():
    ...     hp.load_conditions()

    >>> hp.prepare_inputseries()
    >>> with TestIO():
    ...     hp.load_inputseries()
    >>> hp.prepare_fluxseries()
    >>> hp.prepare_stateseries()
    >>> hp.nodes.prepare_allseries()

    >>> node_q0.deploymode = "oldsim"
    >>> node_q0.sequences.sim.series = 1.0
    >>> node_q0.sequences.obs.series = 2.0
    >>> node_q1.deploymode = "obs"
    >>> node_q1.sequences.obs.series = 3.0
    >>> node_perc.deploymode = "newsim"
    >>> node_perc.sequences.obs.series = 4.0
    >>> node_uz.sequences.obs.series = 5.0

    >>> hp.simulate()

    >>> print_values(node_q0.sequences.sim.series)
    1.0, 1.0, 1.0, 1.0, 1.0
    >>> print_values(node_q0.sequences.obs.series)
    2.0, 2.0, 2.0, 2.0, 2.0

    >>> print_values(model.sequences.fluxes.q1.series)
    0.530696, 0.539661, 0.548003, 0.555721, 0.562883
    >>> print_values(node_q1.sequences.sim.series)
    0.530696, 0.539661, 0.548003, 0.555721, 0.562883
    >>> print_values(node_q1.sequences.obs.series)
    3.0, 3.0, 3.0, 3.0, 3.0

    >>> print_values(model.sequences.fluxes.perc.series)
    0.692545, 0.689484, 0.687425, 0.684699, 0.682571
    >>> print_values(node_perc.sequences.sim.series)
    0.692545, 0.689484, 0.687425, 0.684699, 0.682571
    >>> print_values(node_perc.sequences.obs.series)
    4.0, 4.0, 4.0, 4.0, 4.0

    >>> print_values(model.sequences.states.uz.series)
    5.620222, 4.359519, 3.33013, 2.450124, 1.66734
    >>> print_values(node_uz.sequences.sim.series)
    5.620222, 4.359519, 3.33013, 2.450124, 1.66734
    >>> print_values(node_uz.sequences.obs.series)
    5.0, 5.0, 5.0, 5.0, 5.0

    .. testsetup::

        >>> Element.clear_all()
        >>> Node.clear_all()
    """

    subvars: OutputSequences[OutputSequence]
    """The subgroup to which the output sequence belongs."""
    subseqs: OutputSequences[OutputSequence]
    """Alias for |OutputSequence.subvars|."""
    fastaccess: FastAccessOutputSequence
    """Object for accessing the output sequence's data with little overhead."""

    _CLS_FASTACCESS_PYTHON = FastAccessOutputSequence

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._set_fastaccessattribute("outputflag", False)

    def set_pointer(self, double: pointerutils.Double) -> None:
        """Prepare a pointer referencing the given |Double| object.

        Method |OutputSequence.set_pointer| should be relevant for framework developers
        and eventually for some model developers only.
        """
        pdouble = pointerutils.PDouble(double)
        self.fastaccess.set_pointeroutput(self.name, pdouble)
        self._set_fastaccessattribute("outputflag", True)

    @property
    def outputflag(self) -> bool:
        """A flag telling if the actual |OutputSequence| object passes its data to an
        output node (|True|) or not (|False|).

        See the main documentation on class |OutputSequence| for further information.
        """
        return self._get_fastaccessattribute("outputflag")


class DependentSequence(OutputSequence):
    """Base class for |FactorSequence| and |FluxSequence|."""

    def _finalise_connections(self) -> None:
        super()._finalise_connections()
        if self.NUMERIC:
            value = None if self.NDIM else numpy.zeros(self.numericshape)
            self._set_fastaccessattribute("points", value)
            self._set_fastaccessattribute("integrals", copy.copy(value))
            self._set_fastaccessattribute("results", copy.copy(value))
            value = None if self.NDIM else 0.0
            self._set_fastaccessattribute("sum", value)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        |FactorSequence| and |FluxSequence| objects come with some additional
        `fastaccess` attributes, which should only be of interest to framework
        developers.  One such attribute is the `results` array, handling the
        (intermediate or final) calculation results for factor and flux sequences, as
        shown in the following example for the 0-dimensional flux sequence
        |wland_fluxes.RH| of the |wland| model:

        >>> from hydpy import prepare_model, print_values, pub
        >>> model = prepare_model("wland_v001")
        >>> print_values(model.sequences.fluxes.rh.fastaccess._rh_results)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        For 1-dimensional numerical factor and flux sequences, the `results` attribute
        is |None| initially, as property |ModelSequence.numericshape| is unknown.
        Setting the |DependentSequence.shape| attribute of the respective
        |FactorSequence| or |FluxSequence| object (we select |wland_fluxes.EI| as an
        example) prepares all "fastaccess attributes" automatically:

        >>> ei = model.sequences.fluxes.ei
        >>> ei.fastaccess._ei_results

        >>> ei.shape = (2,)
        >>> ei.shape
        (2,)
        >>> ei.fastaccess._ei_results.shape
        (11, 2)
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]) -> None:
        super().__hydpy__set_shape__(shape)
        if self.NDIM and self.NUMERIC:
            self._set_fastaccessattribute("points", numpy.zeros(self.numericshape))
            self._set_fastaccessattribute("integrals", numpy.zeros(self.numericshape))
            self._set_fastaccessattribute("results", numpy.zeros(self.numericshape))
            self._set_fastaccessattribute("sum", numpy.zeros(self.shape))

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)


class FactorSequence(DependentSequence):
    """Base class for factor sequences of |Model| objects."""

    subvars: FactorSequences
    """The subgroup to which the factor sequence belongs."""
    subseqs: FactorSequences
    """Alias for |FactorSequence.subvars|."""

    NUMERIC = False  # Changing this requires implementing the related functionalites
    # in modules `modeltools` and `modeltutils`.


class FluxSequence(DependentSequence):
    """Base class for flux sequences of |Model| objects."""

    subvars: FluxSequences
    """The subgroup to which the flux sequence belongs."""
    subseqs: FluxSequences
    """Alias for |FluxSequence.subvars|."""


class ConditionSequence(ModelSequence):
    """Base class for |StateSequence| and |LogSequence|.

    Class |ConditionSequence| should not be subclassed by model developers directly.
    Inherit from |StateSequence| or |LogSequence| instead.
    """

    _oldargs: Optional[Tuple[Any, ...]] = None

    def __call__(self, *args) -> None:
        """The prefered way to pass values to |Sequence_| instances within initial
        condition files."""
        super().__call__(*args)
        self.trim()
        self._oldargs = copy.deepcopy(args)

    def trim(self, lower=None, upper=None):
        """Apply |trim| of module |variabletools|."""
        variabletools.trim(self, lower, upper)

    def reset(self):
        """Reset the value of the actual |StateSequence| or |LogSequence| object to the
        last value defined by "calling" the object.

        We use the |lland_v2| application model, which handles sequences derived from
        |StateSequence| (taking |lland_states.Inzp| as an example) and from
        |LogSequence| (taking |lland_logs.WET0| as an example):

        >>> from hydpy import prepare_model, pub
        >>> model = prepare_model("lland_v2")

        After defining their shapes, both sequences contain |numpy.nan|
        values:

        >>> inzp = model.sequences.states.inzp
        >>> inzp.shape = (2,)
        >>> inzp
        inzp(nan, nan)
        >>> wet0 = model.sequences.logs.wet0
        >>> wet0.shape = 2
        >>> wet0
        wet0(nan, nan)

        Before "calling" the sequences method |ConditionSequence.reset| does nothing:

        >>> inzp.values = 0.0
        >>> inzp.reset()
        >>> inzp
        inzp(0.0, 0.0)
        >>> wet0.values = 0.0
        >>> wet0.reset()
        >>> wet0
        wet0(0.0, 0.0)

        After "calling" the sequences method |ConditionSequence.reset| reuses the
        respective arguments:

        >>> with pub.options.warntrim(False):
        ...     inzp(0.0, 1.0)
        >>> inzp.values = 0.0
        >>> inzp
        inzp(0.0, 0.0)
        >>> with pub.options.warntrim(False):
        ...     inzp.reset()
        >>> inzp
        inzp(0.0, 1.0)
        >>> wet0(1.0, 2.0)
        >>> wet0.values = 3.0
        >>> wet0
        wet0(3.0, 3.0)
        >>> wet0.reset()
        >>> wet0
        wet0(1.0, 2.0)
        """
        if self._oldargs:
            self(*self._oldargs)


class StateSequence(OutputSequence, ConditionSequence):
    """Base class for state sequences of |Model| objects.

    Each |StateSequence| object can handle states at two different "time points": at
    the beginning of a simulation step via property |StateSequence.old| and the end of
    a simulation step via property |StateSequence.new|.  These properties are reflected
    by two different `fastaccess` attributes.  `fastaccess_new` is an alias for the
    standard `fastaccess` attribute storing the customary information. `fastaccess_old`
    is an additional feature for keeping the supplemental information.

    We demonstrate the above explanations using state sequence |hland_states.SM| of the
    base model |hland_v1| with a shape of two:

    >>> from hydpy import prepare_model
    >>> model = prepare_model("hland", "1d")
    >>> model.parameters.control.fc.shape = (2,)
    >>> model.parameters.control.fc = 100.0
    >>> sm = model.sequences.states.sm
    >>> sm.shape = (2,)

    Initially, no values are available at all:

    >>> sm
    sm(nan, nan)
    >>> sm.values
    array([nan, nan])
    >>> sm.new
    array([nan, nan])
    >>> sm.old
    array([nan, nan])

    The typical way to define state values, especially within condition files, is to
    "call" state sequence objects, which sets both the "old" and the "new" states to
    the given value(s):

    >>> sm(1.0)
    >>> sm.values
    array([1., 1.])
    >>> sm.new
    array([1., 1.])
    >>> sm.old
    array([1., 1.])

    Alternatively, one can assign values to property |StateSequence.new| or property
    |StateSequence.old| (note that using |StateSequence.new|  is identical with using
    the |Variable.value| property):

    >>> sm.new = 2.0, 3.0
    >>> sm
    sm(2.0, 3.0)
    >>> sm.values
    array([2., 3.])
    >>> sm.new
    array([2., 3.])
    >>> sm.old
    array([1., 1.])

    >>> sm.old = 200.0
    >>> sm
    sm(2.0, 3.0)
    >>> sm.values
    array([2., 3.])
    >>> sm.new
    array([2., 3.])
    >>> sm.old
    array([200., 200.])

    If you assign problematic values to property |StateSequence.old|, it raises similar
    error messages as property |Variable.value|:

    >>> sm.old = 1.0, 2.0, 3.0
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the old value(s) of state sequence `sm`, the \
following error occurred: While trying to convert the value(s) `(1.0, 2.0, 3.0)` to a \
numpy ndarray with shape `(2,)` and type `float`, the following error occurred: could \
not broadcast input array from shape (3,) into shape (2,)

    Just for completeness:  Method |StateSequence.new2old| effectively takes the new
    values as old ones, but more efficiently than using the properties
    |StateSequence.new| and |StateSequence.old| (the Python method
    |StateSequence.new2old| is usually replaced by model-specific, cythonized version
    when working in Cython mode):

    >>> sm.new2old()
    >>> sm.values
    array([2., 3.])
    >>> sm.new
    array([2., 3.])
    >>> sm.old
    array([2., 3.])
    """

    NOT_DEEPCOPYABLE_MEMBERS = "subseqs", "fastaccess_old", "fastaccess_new"

    subvars: StateSequences
    """The subgroup to which the state sequence belongs."""
    subseqs: StateSequences
    """Alias for |StateSequence.subvars|."""
    fastaccess_new: FastAccessOutputSequence
    fastaccess_old: variabletools.FastAccess

    def __call__(self, *args) -> None:
        """The prefered way to pass values to |Sequence_| instances within initial
        condition files."""
        super().__call__(*args)
        self.new2old()

    def _finalise_connections(self) -> None:
        super()._finalise_connections()
        if self.NUMERIC:
            value = None if self.NDIM else numpy.zeros(self.numericshape)
            self._set_fastaccessattribute("points", value)
            self._set_fastaccessattribute("results", copy.copy(value))
        self.fastaccess_old = self.subseqs.fastaccess_old
        self.fastaccess_new = self.subseqs.fastaccess_new
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, None)
        else:
            setattr(self.fastaccess_old, self.name, 0.0)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        |StateSequence| objects come with some additional `fastaccess` attributes,
        which should only be of interest to framework developers.  One such attribute
        is the `results` array, handling the (intermediate or final) calculation
        results for state sequence, as shown in the following example for the
        0-dimensional sequence |wland_states.HS| of the |wland| model:

        >>> from hydpy import prepare_model, print_values, pub
        >>> model = prepare_model("wland_v001")
        >>> print_values(model.sequences.states.hs.fastaccess._hs_results)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        For 1-dimensional numerical state sequences, the `results` attribute is |None|
        initially, as property |ModelSequence.numericshape| is unknown.  Setting the
        |StateSequence.shape| attribute of the respective |StateSequence| object (we
        select |wland_states.IC| as an example) prepares all  "fastaccess attributes"
        automatically:

        >>> ic = model.sequences.states.ic
        >>> ic.fastaccess._ic_results

        >>> ic.shape = (2,)
        >>> ic.shape
        (2,)
        >>> ic.fastaccess._ic_results.shape
        (11, 2)
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]):
        super().__hydpy__set_shape__(shape)
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, self.new.copy())
            if self.NUMERIC:
                self._set_fastaccessattribute("points", numpy.zeros(self.numericshape))
                self._set_fastaccessattribute("results", numpy.zeros(self.numericshape))

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)

    @property
    def new(self):
        """State(s) after calling a |Model| calculation method. (Alias for property
        |Variable.value|).

        Property |StateSequence.new| handles, in contrast to property
        |StateSequence.old|, the newly calculated state values during each simulation
        step.  It supports testing and debugging of individual |Model| methods but is
        typically irrelevant when scripting *HydPy* workflows.
        """
        return super().__hydpy__get_value__()

    @new.setter
    def new(self, value):
        super().__hydpy__set_value__(value)

    @property
    def old(self):
        """State(s) before calling a |Model| calculation method.

        Note the similarity to property |StateSequence.new|. However, property
        |StateSequence.old| references the initial states of the respective simulation
        step, which should not be changed by |Model| calculation methods.
        """
        return self._prepare_getvalue(
            True, getattr(self.fastaccess_old, self.name, None)
        )

    @old.setter
    def old(self, value):
        try:
            setattr(self.fastaccess_old, self.name, self._prepare_setvalue(value))
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the old value(s) of state sequence "
                f"{objecttools.devicephrase(self)}"
            )

    def new2old(self) -> None:
        """Assign the |StateSequence.new| state values to the |StateSequence.old|
        values.

        See the main documentation on class |StateSequence| for further information.

        Note that method |StateSequence.new2old| is replaced by a model-specific,
        cythonized method when working in Cython mode.
        """
        if self.NDIM:
            self.old[:] = self.new[:]
        else:
            self.old = self.new


class LogSequence(ConditionSequence):
    """Base class for logging values required for later calculations.

    Class |LogSequence| serves similar purposes as |StateSequence|  but is less strict
    in its assumptions.  While |StateSequence| objects always handle two states (the
    |StateSequence.old| and the |StateSequence.new| one), |LogSequence| objects are
    supposed to remember an arbitrary or sequence-specific number of values, which can
    be state values but, for example, also flux values.  A typical use case is to store
    "old" values of effective precipitation to calculate "new" values of direct
    discharge using the unit hydrograph concept in later simulation steps.

    It is up to the model developer to ensure that a |LogSequence| subclass has the
    correct dimensionality and shape to store the required information.  By convention,
    the "memory" of each |LogSequence| should be placed on the first axis for
    non-scalar properties.

    As |StateSequence| objects, |LogSequence| objects store relevant information to
    start a new simulation run where another one has ended and are thus written into
    and read from condition files.
    """

    subvars: LogSequences
    """The subgroup to which the log sequence belongs."""
    subseqs: LogSequences
    """Alias for |LogSequence.subvars|."""

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess


class LogSequenceFixed(LogSequence):
    """Base class for log sequences with a fixed shape."""

    NDIM = 1
    SHAPE: int

    def _finalise_connections(self):
        self.shape = (self.SHAPE,)

    def __hydpy__get_shape__(self):
        """Sequences derived from |LogSequenceFixed| initialise themselves with a
        predefined shape.

        We take parameter |dam_logs.LoggedRequiredRemoteRelease| of base model |dam| as
        an example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedrequiredremoterelease.shape
        (1,)

        Property |LogSequenceFixed.shape| results in the following exception when you
        try to set a new shape:

        >>> logs.loggedrequiredremoterelease.shape = 2
        Traceback (most recent call last):
        ...
        AttributeError: The shape of sequence `loggedrequiredremoterelease` cannot be \
changed, but this was attempted for element `?`.

        See the documentation on property |Variable.shape| of class |Variable| for
        further information.
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape):
        if exceptiontools.attrready(self, "shape"):
            raise AttributeError(
                f"The shape of sequence `{self.name}` cannot be changed, but this was "
                f"attempted for element `{objecttools.devicename(self)}`."
            )
        super().__hydpy__set_shape__(shape)

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)


class AideSequence(ModelSequence):
    """Base class for aide sequences of |Model| objects.

    Aide sequences store data only relevant for calculating an individual simulation
    time step but must be shared between different calculation methods of a |Model|
    object.
    """

    subvars: AideSequences
    """The subgroup to which the aide sequence belongs."""
    subseqs: AideSequences
    """Alias for |AideSequence.subvars|."""

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess


class LinkSequence(ModelSequence):
    """Base class for link sequences of |Model| objects.

    |LinkSequence| objects do not handle values themselves.  Instead, they point to the
    values handled by |NodeSequence| objects, using the functionalities provided by the
    Cython module |pointerutils|.  Multiple |LinkSequence| objects of different
    application models can query and modify the same |NodeSequence| values, allowing
    different |Model| objects to share information and interact with each other.

    A note for developers: |LinkSequence| subclasses must be either 0-dimensional or
    1-dimensional.

    Users might encounter the following exception that is a safety measure to prevent
    segmentation faults, as the error message suggests:

    >>> from hydpy.core.sequencetools import LinkSequence
    >>> seq = LinkSequence(None)
    >>> seq
    linksequence(?)
    >>> seq.value
    Traceback (most recent call last):
    ...
    AttributeError: While trying to query the value(s) of link sequence `linksequence` \
of element `?`, the following error occurred: Proper connections are missing (which \
could result in segmentation faults when using it, so please be careful).
    """

    subvars: LinkSequences[LinkSequence]
    """The subgroup to which the link sequence belongs."""
    subseqs: LinkSequences[LinkSequence]
    """Alias for |LinkSequence.subvars|."""
    fastaccess: FastAccessLinkSequence
    """Object for accessing the link sequence's data with little overhead."""

    _CLS_FASTACCESS_PYTHON = FastAccessLinkSequence

    __isready: bool = False

    def set_pointer(self, double: pointerutils.Double, idx: int = 0) -> None:
        """Prepare a pointer referencing the given |Double| object.

        For 1-dimensional sequence objects, one also needs to specify the relevant
        index position of the pointer via argument `idx`.

        Method |LinkSequence.set_pointer| should be relevant for framework developers
        and eventually for some model developers only.
        """
        if self.NDIM == 0:
            self.fastaccess.set_pointer0d(self.name, double)
        elif self.NDIM == 1:
            self.fastaccess.set_pointer1d(self.name, double, idx)
        self.__isready = True

    def _finalise_connections(self) -> None:
        value = pointerutils.PPDouble() if self.NDIM else None
        try:
            setattr(self.fastaccess, self.name, value)
        except AttributeError:
            pass

    def __hydpy__get_value__(self):
        """The actual value(s) the |LinkSequence| object is pointing at.

        Changing a |LinkSequence.value| of a |LinkSequence| object seems very much like
        changing a |LinkSequence.value| of any other |Variable| object.  However, be
        aware that you are changing a value handled by a |NodeSequence| object.  We
        demonstrate this by using the `LahnH` example project through invoking function
        |prepare_full_example_2|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        We focus on the |musk_classic| application model `stream_lahn_1_lahn_2` routing
        inflow from node `lahn_1` to node `lahn_2`:

        >>> model = hp.elements.stream_lahn_1_lahn_2.model

        The first example shows that the 0-dimensional outlet sequence |musk_outlets.Q|
        points to the |Sim| sequence of node `lahn_2`:

        >>> model.sequences.outlets.q
        q(0.0)
        >>> hp.nodes.lahn_2.sequences.sim = 1.0
        >>> model.sequences.outlets.q
        q(1.0)
        >>> model.sequences.outlets.q(2.0)
        >>> hp.nodes.lahn_2.sequences.sim
        sim(2.0)

        The second example shows that the 1-dimensional inlet sequence |musk_inlets.Q|
        points to the |Sim| sequence of node `lahn_1`:

        >>> model.sequences.inlets.q
        q(0.0)
        >>> hp.nodes.lahn_1.sequences.sim = 1.0
        >>> model.sequences.inlets.q
        q(1.0)
        >>> model.sequences.inlets.q(2.0)
        >>> hp.nodes.lahn_1.sequences.sim
        sim(2.0)

        Direct querying the values of both link sequences shows that the value of the
        0-dimensional outlet sequence is scalar, of course, and that the value of the
        1-dimensional inlet sequence is one entry of a vector:

        >>> model.sequences.outlets.q.value
        2.0
        >>> model.sequences.inlets.q.values
        array([2.])

        Assigning incorrect data leads to the usual error messages:

        >>> model.sequences.outlets.q.value = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to assign the value(s) (1.0, 2.0) to link sequence \
`q` of element `stream_lahn_1_lahn_2`, the following error occurred: 2 values are \
assigned to the scalar variable `q` of element `stream_lahn_1_lahn_2`.
        >>> model.sequences.inlets.q.values = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to assign the value(s) (1.0, 2.0) to link sequence \
`q` of element `stream_lahn_1_lahn_2`, the following error occurred: While trying to \
convert the value(s) `(1.0, 2.0)` to a numpy ndarray with shape `(1,)` and type \
`float`, the following error occurred: could not broadcast input array from shape \
(2,) into shape (1,)

        In the example above, the 1-dimensional inlet sequence |musk_inlets.Q| only
        points a single |NodeSequence| value.  We now prepare a |hbranch_v1|
        application model instance to show what happens when connecting a 1-dimensional
        |LinkSequence| object (|hbranch_outlets.Branched|) with three |NodeSequence|
        objects (see the documentation of application model |hbranch_v1| for more
        details):

        >>> from hydpy import Element, Nodes, prepare_model
        >>> model = prepare_model("hbranch_v1")
        >>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
        >>> branch = Element("branch",
        ...                  inlets=["input1", "input2"],
        ...                  outlets=["output1", "output2", "output3"])
        >>> model.parameters.control.xpoints(
        ...     0.0, 2.0, 4.0, 6.0)
        >>> model.parameters.control.ypoints(
        ...     output1=[0.0, 1.0, 2.0, 3.0],
        ...     output2=[0.0, 1.0, 0.0, 0.0],
        ...     output3=[0.0, 0.0, 2.0, 6.0])
        >>> branch.model = model

        Our third example demonstrates that each field of the values of a 1-dimensional
        |LinkSequence| objects points to another |NodeSequence| object:

        >>> nodes.output1.sequences.sim = 1.0
        >>> nodes.output2.sequences.sim = 2.0
        >>> nodes.output3.sequences.sim = 3.0
        >>> model.sequences.outlets.branched
        branched(1.0, 2.0, 3.0)
        >>> model.sequences.outlets.branched = 4.0, 5.0, 6.0
        >>> nodes.output1.sequences.sim
        sim(4.0)
        >>> nodes.output2.sequences.sim
        sim(5.0)
        >>> nodes.output3.sequences.sim
        sim(6.0)

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        try:
            if not self.__isready:
                raise AttributeError(
                    "Proper connections are missing (which could result in "
                    "segmentation faults when using it, so please be careful)."
                )
            return self.fastaccess.get_value(self.name)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to query the value(s) of link sequence "
                f"{objecttools.elementphrase(self)}"
            )

    def __hydpy__set_value__(self, value):
        try:
            self.fastaccess.set_value(
                self.name,
                self._prepare_setvalue(value),
            )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to assign the value(s) {value} to link sequence "
                f"{objecttools.elementphrase(self)}"
            )

    value = property(fget=__hydpy__get_value__, fset=__hydpy__set_value__)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        Property |LinkSequence.shape| of class |LinkSequence| works similarly as the
        general |Variable.shape| property of class |Variable|. Still, you need to be
        extra careful due to the pointer mechanism underlying class |LinkSequence|.
        Change the shape of a link sequence for good reasons only.  Please read the
        documentation on property |LinkSequence.value| first and then see the following
        examples, which are, again, based on the `LahnH` example project and
        application model |musk_classic|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> model = hp.elements.stream_lahn_1_lahn_2.model

        The default mechanisms of *HydPy* prepare both 0-dimensional and 1-dimensional
        link sequences with a proper shape (which, for inlet sequence |
        musk_inlets.Q|, depends on the number of connected |Node| objects):

        >>> model.sequences.outlets.q.shape
        ()
        >>> model.sequences.inlets.q.shape
        (1,)

        Attempting to set the only possible shape of 0-dimensional link sequences or
        any different shape results in the standard behaviour:

        >>> model.sequences.outlets.q.shape = ()
        >>> model.sequences.outlets.q.shape = (1,)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the shape of link sequence`q` of element \
`stream_lahn_1_lahn_2`, the following error occurred: The shape information of \
0-dimensional variables as `q` of element `stream_lahn_1_lahn_2` can only be `()`, \
but `(1,)` is given.

        Changing the shape of 1-dimensional link sequences is supported but destroys
        the connection to the |NodeSequence| values of the respective nodes.
        Therefore, he following exception prevents segmentation faults until proper
        connections are available:

        >>> model.sequences.inlets.q.shape = (2,)
        >>> model.sequences.inlets.q.shape
        (2,)
        >>> model.sequences.inlets.q.shape = 1
        >>> model.sequences.inlets.q.shape
        (1,)
        >>> model.sequences.inlets.q
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to query the value(s) of link sequence `q` of \
element `stream_lahn_1_lahn_2`, the following error occurred: The pointer of the \
actual `PPDouble` instance at index `0` requested, but not prepared yet via \
`set_pointer`.

        >>> model.sequences.inlets.q(1.0)
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to assign the value(s) 1.0 to link sequence `q` of \
element `stream_lahn_1_lahn_2`, the following error occurred: The pointer of the \
actual `PPDouble` instance at index `0` requested, but not prepared yet via \
`set_pointer`.

        Querying the shape of a link sequence should rarely result in errors.  However,
        if we enforce it by deleting the `fastaccess` attribute, we get an error
        message:

        >>> del model.sequences.inlets.q.fastaccess
        >>> model.sequences.inlets.q.shape
        Traceback (most recent call last):
        ...
        AttributeError: While trying to query the shape of link sequence`q` of \
element `stream_lahn_1_lahn_2`, the following error occurred: 'Q' object has no \
attribute 'fastaccess'

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        try:
            if self.NDIM == 0:
                return ()
            try:
                return getattr(self.fastaccess, self.name).shape
            except AttributeError:
                return (self._get_fastaccessattribute("length_0"),)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to query the shape of link sequence"
                f"{objecttools.elementphrase(self)}"
            )

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]):
        try:
            if (self.NDIM == 0) and shape:
                self._raise_wrongshape(shape)
            elif self.NDIM == 1:
                if isinstance(shape, Iterable):
                    shape = list(shape)[0]
                self.fastaccess.dealloc(self.name)
                self.fastaccess.alloc(self.name, shape)
                setattr(self.fastaccess, "len_" + self.name, self.shape[0])
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the shape of link sequence"
                f"{objecttools.elementphrase(self)}"
            )

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)

    def __repr__(self):
        if self.__isready:
            return super().__repr__()
        return f"{self.name}(?)"


class InletSequence(LinkSequence):
    """Base class for inlet link sequences of |Model| objects."""

    subvars: InletSequences
    """The subgroup to which the inlet sequence belongs."""
    subseqs: InletSequences
    """Alias for |InletSequence.subvars|."""


class OutletSequence(LinkSequence):
    """Base class for outlet link sequences of |Model| objects."""

    subvars: OutletSequences
    """The subgroup to which the outlet sequence belongs."""
    subseqs: OutletSequences
    """Alias for |OutletSequence.subvars|."""


class ReceiverSequence(LinkSequence):
    """Base class for receiver link sequences of |Model| objects."""

    subvars: ReceiverSequences
    """The subgroup to which the receiver sequence belongs."""
    subseqs: ReceiverSequences
    """Alias for |ReceiverSequence.subvars|."""


class SenderSequence(LinkSequence):
    """Base class for sender link sequences of |Model| objects."""

    subvars: SenderSequences
    """The subgroup to which the sender sequence belongs."""
    subseqs: SenderSequences
    """Alias for |SenderSequence.subvars|."""


class NodeSequence(IOSequence):
    """Base class for all sequences to be handled by |Node| objects."""

    subvars: NodeSequences
    """The subgroup to which the node sequence belongs."""
    subseqs: NodeSequences
    """Alias for |NodeSequence.subvars|."""
    fastaccess: FastAccessNodeSequence
    """Object for accessing the node sequence's data with little overhead."""

    NDIM: int = 0
    NUMERIC: bool = False

    _CLS_FASTACCESS_PYTHON = FastAccessNodeSequence

    def __init__(self, subvars: NodeSequences) -> None:
        super().__init__(subvars)
        self.subseqs = subvars

    @property
    def initinfo(self) -> Tuple[pointerutils.Double, bool]:
        """Return a |Double| instead of a |float| object as the first tuple entry."""
        if hydpy.pub.options.usedefaultvalues:
            return pointerutils.Double(0.0), True
        return pointerutils.Double(numpy.nan), False

    @property
    def descr_sequence(self) -> str:
        """Description of the |NodeSequence| object, including the |Node.variable| to
        be represented.

        >>> from hydpy import Node
        >>> Node("test_node_1", "T").sequences.sim.descr_sequence
        'sim_t'

        >>> from hydpy import FusedVariable
        >>> from hydpy.inputs import hland_T, lland_TemL
        >>> Temp = FusedVariable("Temp", hland_T, lland_TemL)
        >>> Node("test_node_2", Temp).sequences.sim.descr_sequence
        'sim_temp'

        .. testsetup::

            >>> Node.clear_all()
        """
        return f"{self.name}_{str(self.subseqs.node.variable).lower()}"

    @property
    def descr_device(self) -> str:
        """Description of the |Node| object the |NodeSequence| object belongs to.

        >>> from hydpy import Node
        >>> Node("test_node_2").sequences.sim.descr_device
        'test_node_2'

        .. testsetup::

            >>> Node.clear_all()
        """
        return self.subseqs.node.name

    def _finalise_connections(self) -> None:
        super()._finalise_connections()
        setattr(self.fastaccess, self.name, pointerutils.Double(0.0))
        setattr(self.fastaccess, "_reset_obsdata", False)

    def __hydpy__get_value__(self):
        """The actual sequence value.

        For framework users, the property |NodeSequence.value| of class |NodeSequence|
        works as usual (explained in the documentation on property |Variable.shape| of
        class |Variable|).  However, framework developers should note that
        |NodeSequence| objects use |Double| objects for storing their values and making
        them accessible to |PDouble| and |PPDouble| objects as explained in detail in
        the documentation on class |LinkSequence|.  This mechanism is hidden for
        framework users via conversions to type |float| for safety reasons:

        .. testsetup::

            >>> from hydpy import Node
            >>> Node.clear_all()

        >>> from hydpy import Node
        >>> sim = Node("node").sequences.sim
        >>> sim(1.0)
        >>> sim
        sim(1.0)
        >>> sim.value
        1.0
        >>> sim.fastaccess.sim
        Double(1.0)

        >>> sim.value = 2.0
        >>> sim
        sim(2.0)

        Node sequences return errors like the following if they receive misspecified
        values or ill-configured:

        >>> sim.value = 1.0, 2.0   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: While trying to assign the value `(1.0, 2.0)` to sequence `sim` of \
node `node`, the following error occurred: float() argument must be a string or a... \
number, not 'tuple'

        >>> del sim.fastaccess
        >>> sim.value
        Traceback (most recent call last):
        ...
        AttributeError: While trying to query the value of sequence `sim` of node \
`node`, the following error occurred: 'Sim' object has no attribute 'fastaccess'

        .. testsetup::

            >>> Node.clear_all()
        """
        try:
            return getattr(self.fastaccess, self.name)[0]
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to query the value of sequence "
                f"{objecttools.nodephrase(self)}"
            )

    def __hydpy__set_value__(self, value):
        try:
            getattr(self.fastaccess, self.name)[0] = float(value)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to assign the value `{value}` to sequence "
                f"{objecttools.nodephrase(self)}"
            )

    value = property(fget=__hydpy__get_value__, fset=__hydpy__set_value__)

    @property
    def seriescomplete(self) -> bool:
        """True/False flag indicating whether simulated or observed data is fully
        available or not.

        We use the observation series of node `dill` of the `LahnH` project:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> obs = hp.nodes.dill.sequences.obs

        When the sequence does not handle any time-series data,
        |NodeSequence.seriescomplete| is |False|:

        >>> obs.prepare_series(allocate_ram=False)
        >>> obs.series
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Sequence `obs` of node `dill` is \
not requested to make any time-series data available.
        >>> obs.seriescomplete
        False

        As long as any time-series data is missing, |NodeSequence.seriescomplete| is
        still |False|:

        >>> obs.prepare_series()
        >>> obs.series[:-1] = 1.0
        >>> obs.series
        InfoArray([ 1.,  1.,  1., nan])
        >>> obs.seriescomplete
        False

        Only with all data being not |numpy.nan|, |NodeSequence.seriescomplete| is
        |True|:

        >>> obs.series[-1] = 1.0
        >>> obs.seriescomplete
        True

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        return self.memoryflag and not numpy.any(numpy.isnan(self.series))


class Sim(NodeSequence):
    """Class for handling those values of |Node| objects that are "simulated", meaning
    calculated by hydrological models."""

    def load_series(self) -> None:
        """Read time-series data like method |IOSequence.load_series| of class
        |IOSequence| but with special handling of missing data.

        The method's "special handling" is to convert errors to warnings.  We explain
        the reasons in the documentation on method |Obs.load_series| of class |Obs|,
        from which we borrow the following examples.  The only differences are that
        method |Sim.load_series| of class |Sim| does not disable property
        |IOSequence.memoryflag| and uses the option |Options.warnmissingsimfile|
        instead of |Options.warnmissingobsfile|:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     hp.prepare_simseries()
        >>> sim = hp.nodes.dill.sequences.sim
        >>> with TestIO():
        ...     sim.load_series()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        UserWarning: While trying to load the time-series data of sequence `sim` of \
node `dill`, the following error occurred: [Errno 2] No such file or directory: \
'...dill_sim_q.asc'
        >>> sim.series
        InfoArray([nan, nan, nan, nan, nan])

        >>> sim.series = 1.0
        >>> with TestIO():
        ...     sim.save_series()
        >>> sim.series = 0.0
        >>> with TestIO():
        ...     sim.load_series()
        >>> sim.series
        InfoArray([1., 1., 1., 1., 1.])

        >>> import numpy
        >>> sim.series[2] = numpy.nan
        >>> with TestIO(), pub.sequencemanager.overwrite(True):
        ...     sim.save_series()
        >>> with TestIO():
        ...     sim.load_series()
        Traceback (most recent call last):
        ...
        UserWarning: While trying to load the time-series data of sequence `sim` of \
node `dill`, the following error occurred: The series array of sequence `sim` of node \
`dill` contains 1 nan value.
        >>> sim.series
        InfoArray([ 1.,  1., nan,  1.,  1.])

        >>> sim.series = 0.0
        >>> with TestIO(), pub.options.warnmissingsimfile(False):
        ...         sim.load_series()
        >>> sim.series
        InfoArray([ 1.,  1., nan,  1.,  1.])

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        try:
            super().load_series()
        except BaseException:
            if hydpy.pub.options.warnmissingsimfile:
                warnings.warn(str(sys.exc_info()[1]))


class Obs(NodeSequence):
    """Class for handling those values of |Node| objects that are observed, meaning
    read from data files."""

    def load_series(self) -> None:
        """Read time-series data like method |IOSequence.load_series| of class
        |IOSequence| but with special handling of missing data.

        When reading incomplete time-series data, *HydPy* usually raises a
        |RuntimeError| to prevent from performing erroneous calculations.  This
        functionality makes sense for meteorological input data that is a strict
        requirement for hydrological simulations.  However, the same often does not
        hold for the time-series of |Obs| sequences, e.g. representing measured
        discharge. Measured discharge is often an optional input or only used for
        comparison purposes.

        According to this reasoning, *HydPy* raises (at most) a |UserWarning| in case
        of missing or incomplete external time-series data of |Obs| sequences.  The
        following examples show this based on the `LahnH` project, mainly focussing on
        the |Obs| sequence of node `dill`, which is ready for handling time-series data
        at the end of the following steps:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     hp.prepare_obsseries()
        >>> obs = hp.nodes.dill.sequences.obs
        >>> obs.ramflag
        True

        Trying to read non-existing data raises the following warning and disables the
        sequence's ability to handle time-series data:

        >>> with TestIO():
        ...     hp.load_obsseries()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        UserWarning: The `memory flag` of sequence `obs` of node `dill` had to be set \
to `False` due to the following problem: While trying to load the time-series data of \
sequence `obs` of node `dill`, the following error occurred: [Errno 2] No such file \
or directory: '...dill_obs_q.asc'
        >>> obs.ramflag
        False

        After writing a complete data file, everything works fine:

        >>> obs.prepare_series()
        >>> obs.series = 1.0
        >>> with TestIO():
        ...     obs.save_series()
        >>> obs.series = 0.0
        >>> with TestIO():
        ...     obs.load_series()
        >>> obs.series
        InfoArray([1., 1., 1., 1., 1.])

        Reading incomplete data also results in a warning message, but does not disable
        the |IOSequence.memoryflag|:

        >>> import numpy
        >>> obs.series[2] = numpy.nan
        >>> with TestIO(), pub.sequencemanager.overwrite(True):
        ...     obs.save_series()
        >>> with TestIO():
        ...     obs.load_series()
        Traceback (most recent call last):
        ...
        UserWarning: While trying to load the time-series data of sequence `obs` of \
node `dill`, the following error occurred: The series array of sequence `obs` of node \
`dill` contains 1 nan value.
        >>> obs.memoryflag
        True

        Option |Options.warnmissingobsfile| allows disabling the warning messages
        without altering the functionalities described above:

        >>> hp.prepare_obsseries()
        >>> with TestIO():
        ...     with pub.options.warnmissingobsfile(False):
        ...         hp.load_obsseries()
        >>> obs.series
        InfoArray([ 1.,  1., nan,  1.,  1.])
        >>> hp.nodes.lahn_1.sequences.obs.memoryflag
        False

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        try:
            super().load_series()
        except OSError:
            self._set_fastaccessattribute("ramflag", False)
            self._set_fastaccessattribute("diskflag_reading", False)
            if hydpy.pub.options.warnmissingobsfile:
                warnings.warn(
                    f"The `memory flag` of sequence {objecttools.nodephrase(self)} had "
                    f"to be set to `False` due to the following problem: "
                    f"{sys.exc_info()[1]}"
                )
        except BaseException:
            if hydpy.pub.options.warnmissingobsfile:
                warnings.warn(str(sys.exc_info()[1]))


class NodeSequences(
    IOSequences["devicetools.Node", NodeSequence, FastAccessNodeSequence]
):
    """Base class for handling |Sim| and |Obs| sequence objects.

    Basically, |NodeSequences| works like the different |ModelSequences|  subclasses
    used for handling |ModelSequence| objects.  The main difference is that they do not
    reference a |Sequences| object (which is only handled by |Element| objects but not
    by |Node| objects).  Instead, they directly reference their master |Node| object
    via the attribute |NodeSequences.node|:

    >>> from hydpy import Node
    >>> node = Node("node")
    >>> node.sequences.node
    Node("node", variable="Q")

    The implemented methods just call the same method of the underlying `fastaccess`
    attribute, which is an instance of (a Cython extension class of) the Python class
    |sequencetools.FastAccessNodeSequence|.

    .. testsetup::

        >>> Node.clear_all()
    """

    CLASSES = (Sim, Obs)

    node: "devicetools.Node"
    sim: Sim
    obs: Obs
    _cymodel: Optional[CyModelProtocol]
    _CLS_FASTACCESS_PYTHON = FastAccessNodeSequence

    def __init__(
        self,
        master: devicetools.Node,
        cls_fastaccess: Optional[Type[FastAccessNodeSequence]] = None,
        cymodel: Optional[CyModelProtocol] = None,
    ) -> None:
        self.node = master
        self._cls_fastaccess = cls_fastaccess
        self._cymodel = cymodel
        super().__init__(master)

    def __hydpy__initialise_fastaccess__(self) -> None:
        if hydpy.pub.options.usecython:
            self.fastaccess = (
                sequenceutils.FastAccessNodeSequence()  # pylint: disable=used-before-assignment
            )
        else:
            self.fastaccess = self._CLS_FASTACCESS_PYTHON()

    def load_data(self, idx: int) -> None:
        """Call method |sequencetools.FastAccessNodeSequence.load_data| of the current
        `fastaccess` attribute.

        >>> from hydpy import Node, pub
        >>> with pub.options.usecython(False):
        ...     node = Node("node")
        >>> from unittest import mock
        >>> method = "hydpy.core.sequencetools.FastAccessNodeSequence.load_data"
        >>> with mock.patch(method) as mocked:
        ...     node.sequences.load_data(5)
        >>> mocked.call_args_list
        [call(5)]

        .. testsetup::

            >>> Node.clear_all()
        """
        self.fastaccess.load_data(idx)

    def load_simdata(self, idx: int) -> None:
        """Call method |sequencetools.FastAccessNodeSequence.load_simdata| of the
        current `fastaccess` attribute.

        >>> from hydpy import Node, pub
        >>> with pub.options.usecython(False):
        ...     node = Node("node")
        >>> from unittest import mock
        >>> method = "hydpy.core.sequencetools.FastAccessNodeSequence.load_simdata"
        >>> with mock.patch(method) as mocked:
        ...     node.sequences.load_simdata(5)
        >>> mocked.call_args_list
        [call(5)]

        .. testsetup::

            >>> Node.clear_all()
        """
        self.fastaccess.load_simdata(idx)

    def load_obsdata(self, idx: int) -> None:
        """Call method |sequencetools.FastAccessNodeSequence.load_obsdata| of the
        current `fastaccess` attribute.

        >>> from hydpy import Node, pub
        >>> with pub.options.usecython(False):
        ...     node = Node("node")
        >>> from unittest import mock
        >>> method = "hydpy.core.sequencetools.FastAccessNodeSequence.load_obsdata"
        >>> with mock.patch(method) as mocked:
        ...     node.sequences.load_obsdata(5)
        >>> mocked.call_args_list
        [call(5)]

        .. testsetup::

            >>> Node.clear_all()
        """
        self.fastaccess.load_obsdata(idx)

    def save_data(self, idx: int) -> None:
        """Call method |sequencetools.FastAccessNodeSequence.save_data| of the current
        `fastaccess` attribute.

        >>> from hydpy import Node, pub
        >>> with pub.options.usecython(False):
        ...     node = Node("node")
        >>> from unittest import mock
        >>> method = "hydpy.core.sequencetools.FastAccessNodeSequence.save_data"
        >>> with mock.patch(method) as mocked:
        ...     node.sequences.save_data(5)
        >>> mocked.call_args_list
        [call(5)]

        .. testsetup::

            >>> Node.clear_all()
        """
        self.fastaccess.save_data(idx)

    def save_simdata(self, idx: int) -> None:
        """Call method |sequencetools.FastAccessNodeSequence.save_simdata|  of the
        current `fastaccess` attribute.

        >>> from hydpy import Node, pub
        >>> with pub.options.usecython(False):
        ...     node = Node('node')
        >>> from unittest import mock
        >>> method = "hydpy.core.sequencetools.FastAccessNodeSequence.save_simdata"
        >>> with mock.patch(method) as mocked:
        ...     node.sequences.save_simdata(5)
        >>> mocked.call_args_list
        [call(5)]

        .. testsetup::

            >>> Node.clear_all()
        """
        self.fastaccess.save_simdata(idx)
