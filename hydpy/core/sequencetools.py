# -*- coding: utf-8 -*-
"""This module implements tools for defining and handling different kinds of the
sequences (time-series) of hydrological models."""
# import...
# ...from standard library
import abc
import copy
import os
import runpy
import struct
import sys
import types
import warnings
from typing import *
from typing import IO

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import variabletools
from hydpy.cythons.autogen import pointerutils
from hydpy.cythons.autogen import sequenceutils
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import modeltools
    from hydpy.core import timetools


InOutSequence = Union[
    "InputSequence",
    "OutputSequence",
]
TypesInOutSequence = Union[
    Type["InputSequence"],
    Type["OutputSequence"],
]

SequencesType = TypeVar(
    "SequencesType",
    "Sequences",
    "devicetools.Node",
)

SubSequencesType = TypeVar(
    "SubSequencesType",
    bound="SubSequences",
)
SequenceType = TypeVar(
    "SequenceType",
    bound="Sequence_",
)

IOSequencesType = TypeVar(
    "IOSequencesType",
    bound="IOSequences",
)
IOSequenceType = TypeVar(
    "IOSequenceType",
    bound="IOSequence",
)
FastAccessIOSequenceType = TypeVar(
    "FastAccessIOSequenceType",
    bound="FastAccessIOSequence",
)

ModelSequencesType = TypeVar(
    "ModelSequencesType",
    bound="ModelSequences",
)
ModelSequenceType = TypeVar(
    "ModelSequenceType",
    bound="ModelSequence",
)

ModelIOSequencesType = TypeVar(
    "ModelIOSequencesType",
    bound="ModelIOSequences",
)
ModelIOSequenceType = TypeVar(
    "ModelIOSequenceType",
    bound="ModelIOSequence",
)

OutputSequencesType = TypeVar(
    "OutputSequencesType",
    bound="OutputSequences",
)
OutputSequenceType = TypeVar(
    "OutputSequenceType",
    bound="OutputSequence",
)

LinkSequencesType = TypeVar(
    "LinkSequencesType",
    bound="LinkSequences",
)
LinkSequenceType = TypeVar(
    "LinkSequenceType",
    bound="LinkSequence",
)


class FastAccessIOSequence(variabletools.FastAccess):
    """Provides fast access to the values of the sequences of a sequence
    subgroup and supports the handling of internal data series during
    simulations.

    The following details are of relevance for *HydPy* developers only.

    |sequencetools.FastAccessIOSequence| is applied in Python mode only.
    In Cython mode it is replaced by model-specific Cython extension
    classes, which are computationally more efficient.  For compatibility
    with these extension classes, |sequencetools.FastAccessIOSequence|
    objects work with dynamically set instance members.  Suppose there
    is a sequence named `seq1` which is 2-dimensional, then its associated
    attributes are:

      * seq1 (|numpy.ndarray|): The actual sequence values.
      * _seq1_ndim (|int|): Number of dimensions.
      * _seq1_length_0 (|int|): Length in the first dimension.
      * _seq1_length_1 (|int|): Length in the second dimension.
      * _seq1_ramflag (|bool|): Handle internal data in RAM?
      * _seq1_diskflag (|bool|): Handle internal data on disk?
      * _seq1_path (|str|): Path of the internal data file.
      * _seq1_file (|io.open|): Object handling the internal data file.

    Note that the respective |SubSequences| and |Sequence_| objects
    initialise, change, and apply these dynamical attributes.  To
    handle them directly is error-prone and thus not recommended.
    """

    def open_files(self, idx: int) -> None:
        """Open all files with an activated disk flag and seek the position
        indicated by the given index."""
        for name in self:
            if self._get_attribute(name, "diskflag"):
                file_ = open(self._get_attribute(name, "path"), "rb+")
                position = 8 * idx
                for idim in range(self._get_attribute(name, "ndim")):
                    position *= self._get_attribute(name, f"length_{idim}")
                file_.seek(position)
                self._set_attribute(name, "file", file_)

    def close_files(self) -> None:
        """Close the internal data files of all handled sequences with
        an activated |IOSequence.diskflag|."""
        for name in self:
            if self._get_attribute(name, "diskflag"):
                self._get_attribute(name, "file").close()

    def load_data(self, idx: int) -> None:
        """Load the internal data of all sequences with an activated
        |IOSequence.memoryflag|.

        Read from a file if the corresponding disk flag is activated; read
        from working memory if the corresponding ram flag is activated.
        """
        for name in self:
            ndim = self._get_attribute(name, "ndim")
            diskflag = self._get_attribute(name, "diskflag")
            ramflag = self._get_attribute(name, "ramflag")
            inputflag = self._get_attribute(name, "inputflag", False)
            if diskflag or ramflag or inputflag:
                if inputflag:
                    values = self._get_attribute(name, "inputpointer")[0]
                elif diskflag:
                    length_tot = 1
                    shape = []
                    for jdx in range(ndim):
                        length = self._get_attribute(name, f"length_{jdx}")
                        length_tot *= length
                        shape.append(length)
                    raw = self._get_attribute(name, "file").read(length_tot * 8)
                    values = struct.unpack(length_tot * "d", raw)
                    if ndim:
                        values = numpy.array(values).reshape(shape)
                    else:
                        values = values[0]
                else:
                    values = self._get_attribute(name, "array")[idx]
                if ndim == 0:
                    setattr(self, name, values)
                else:
                    getattr(self, name)[:] = values

    def save_data(self, idx: int) -> None:
        """Save the internal data of all sequences with an activated flag.

        Write to a file if the corresponding disk flag is activated; write
        to working memory if the corresponding ram flag is activated."""
        for name in self:
            if not self._get_attribute(name, "inputflag", True):
                continue
            actual = getattr(self, name)
            if self._get_attribute(name, "diskflag"):
                ndim = self._get_attribute(name, "ndim")
                length_tot = 1
                for jdx in range(ndim):
                    length = self._get_attribute(name, f"length_{jdx}")
                    length_tot *= length
                if ndim:
                    raw = struct.pack(length_tot * "d", *actual.flatten())
                else:
                    raw = struct.pack("d", actual)
                self._get_attribute(name, "file").write(raw)
            elif self._get_attribute(name, "ramflag"):
                self._get_attribute(name, "array")[idx] = actual


class FastAccessInputSequence(FastAccessIOSequence):
    """|FastAccessIOSequence| subclass specialised for input sequences."""

    def set_pointerinput(
        self,
        name: str,
        pdouble: "pointerutils.PDouble",
    ) -> None:
        """Use the given |PDouble| object as the pointer for the
        0-dimensional |InputSequence| object with the given name."""
        setattr(self, f"_{name}_inputpointer", pdouble)


class FastAccessOutputSequence(FastAccessIOSequence):
    """|FastAccessIOSequence| subclass specialised for output sequences."""

    def set_pointeroutput(
        self,
        name: str,
        pdouble: "pointerutils.PDouble",
    ) -> None:
        """Use the given |PDouble| object as the pointer for the
        0-dimensional |OutputSequence| object with the given name."""
        setattr(self, f"_{name}_outputpointer", pdouble)

    def update_outputs(self):
        """Pass the internal data of all sequences with activated output flag."""
        for name in self:
            outputflag = self._get_attribute(name, "outputflag", False)
            if outputflag:
                actual = getattr(self, name)
                self._get_attribute(name, "outputpointer")[0] = actual


class FastAccessLinkSequence(variabletools.FastAccess):
    """|FastAccessIOSequence| subclass specialised for link sequences."""

    def alloc(self, name: str, length: int) -> None:
        """Allocate enough memory for the given vector length for the
        |LinkSequence| with the given name.

        Cython extension classes need to define |FastAccessLinkSequence.alloc|
        if there is at least one 1-dimensional |LinkSequence| subclasses.
        """
        getattr(self, name).shape = length

    def dealloc(
        self,
        name: str,
    ) -> None:
        """Free the previously allocated memory of the |LinkSequence| with
        the given name.

        Cython extension classes need to define |FastAccessLinkSequence.alloc|
        if there is at least one 1-dimensional |LinkSequence| subclasses.
        """

    def set_pointer0d(
        self,
        name: str,
        value: "pointerutils.Double",
    ):
        """Use the given |PDouble| object as the pointer of the
        0-dimensional |LinkSequence| object with the given name.

        Cython extension classes need to define
        |FastAccessLinkSequence.set_pointer0d| if there is at least one
        0-dimensional |LinkSequence| subclasses.
        """
        setattr(self, name, pointerutils.PDouble(value))

    def set_pointer1d(
        self,
        name: str,
        value: "pointerutils.Double",
        idx: int,
    ):
        """Use the given |PDouble| object as one of the pointers of the
        1-dimensional |LinkSequence| object with the given name.

        The given index defines the vector position of the pointer.

        Cython extension classes need to define
        |FastAccessLinkSequence.set_pointer0d| if there is at least one
        1-dimensional |LinkSequence| subclasses.
        """
        ppdouble: pointerutils.PPDouble = getattr(self, name)
        ppdouble.set_pointer(value, idx)

    def get_value(
        self,
        name: str,
    ) -> Union[float, numpy.ndarray]:
        """Return the actual value(s) the |LinkSequence| object with
        the given name is pointing to."""
        value = getattr(self, name)[:]
        if self._get_attribute(name, "ndim"):
            return numpy.asarray(value, dtype=float)
        return float(value)

    def set_value(
        self,
        name: str,
        value: Mayberable1[float],
    ) -> None:
        """Change the actual value(s) the |LinkSequence| object with
        the given name is pointing to."""
        getattr(self, name)[:] = value


class FastAccessNodeSequence(FastAccessIOSequence):
    """|sequencetools.FastAccessIOSequence| subclass specialised for
    |Node| objects.

    In contrast to other |FastAccessIOSequence| subclasses,
    |sequencetools.FastAccessNodeSequence| only needs to handle a fixed
    number of sequences, |Sim| and |Obs|. It thus can define the related
    attributes explicitly.
    """

    sim: pointerutils.Double
    obs: pointerutils.Double
    _sim_array: numpy.array
    _obs_array: numpy.array
    _sim_ramflag: bool
    _obs_ramflag: bool
    _sim_diskflag: bool
    _obs_diskflag: bool
    _sim_file: IO
    _obs_file: IO

    def load_simdata(self, idx: int) -> None:
        """Load the next sim sequence value (of the given index)."""
        if self._sim_ramflag:
            self.sim[0] = self._sim_array[idx]
        elif self._sim_diskflag:
            raw = self._sim_file.read(8)
            self.sim[0] = struct.unpack("d", raw)[0]

    def save_simdata(self, idx: int) -> None:
        """Save the last sim sequence value (of the given index)."""
        if self._sim_ramflag:
            self._sim_array[idx] = self.sim[0]
        elif self._sim_diskflag:
            raw = struct.pack("d", self.sim[0])
            self._sim_file.write(raw)

    def load_obsdata(self, idx: int) -> None:
        """Load the next obs sequence value (of the given index)."""
        if self._obs_ramflag:
            self.obs[0] = self._obs_array[idx]
        elif self._obs_diskflag:
            raw = self._obs_file.read(8)
            self.obs[0] = struct.unpack("d", raw)[0]

    def load_data(self, idx: int) -> None:
        """Call both method |sequencetools.FastAccessNodeSequence.load_simdata|
        and method |sequencetools.FastAccessNodeSequence.load_obsdata|."""
        self.load_simdata(idx)
        self.load_obsdata(idx)

    def save_data(self, idx: int) -> None:
        """Alias for method |sequencetools.FastAccessNodeSequence.save_simdata|."""
        self.save_simdata(idx)

    def reset(self, idx: int = 0) -> None:
        # pylint: disable=unused-argument
        # required for consistincy with the other reset methods.
        """Reset the actual value of the simulation sequence to zero."""
        self.sim[0] = 0.0

    def fill_obsdata(self, idx: int = 0) -> None:
        """Use the current sim value for the current obs value if obs is
        |numpy.nan|."""
        # pylint: disable=unused-argument
        # required for consistincy with the other reset methods.
        if numpy.isnan(self.obs[0]):
            self.obs[0] = self.sim[0]


class InfoArray(numpy.ndarray):
    """|numpy| |numpy.ndarray| subclass that stores and tries to keep
    an additional `info` attribute.

    >>> from hydpy.core.sequencetools import InfoArray
    >>> array = InfoArray([1.0, 2.0], info="this array is short")
    >>> array
    InfoArray([1., 2.])
    >>> array.info
    'this array is short'
    >>> subarray = array[:1]
    >>> subarray
    InfoArray([1.])
    >>> subarray.info
    'this array is short'
    """

    def __new__(cls, array, info=None):
        obj = numpy.asarray(array).view(cls)
        obj.info = info
        return obj

    def __array_finalize__(self, obj: "InfoArray") -> None:
        self.info = getattr(obj, "info", None)


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

    Iteration makes only the non-empty subgroups available which are handling
    |Sequence_| objects:

    >>> for subseqs in sequences:
    ...     print(subseqs.name)
    inputs
    factors
    fluxes
    states
    logs
    outlets
    >>> len(sequences)
    6

    Class |Sequences| provides some methods related to reading and writing time-series
    data, which (directly or indirectly) call the corresponding methods of the handled
    |IOSequence| objects.  In most cases, users should prefer to use the related
    methods of class |HydPy| but using the ones of class |Sequences| can be more
    convenient when analysing a specific model in-depth.

    To introduce these methods, we first change two IO-related settings:

    >>> from hydpy import round_
    >>> pub.options.checkseries = False
    >>> pub.sequencemanager.generaloverwrite = True

    Method |Sequences.activate_ram| and method |Sequences.deactivate_ram|
    enables/disables handling time-series in rapid access memory and
    method |Sequences.save_series| writes time-series to files:

    >>> sequences.activate_ram()
    >>> sequences.inputs.t.ramflag
    True
    >>> sequences.inputs.t.series = 1.0, 2.0, 3.0, 4.0
    >>> with TestIO():
    ...     sequences.save_series()
    >>> sequences.deactivate_ram()
    >>> sequences.inputs.t.ramflag
    False
    >>> sequences.inputs.t.series
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `t` of element `land_dill` is not requested \
to make any internal data available.

    Method |Sequences.activate_disk| and |Sequences.deactivate_disk|
    enables/disables handling time-series on disk and method
    |Sequences.load_series| reads time-series from files:

    >>> with TestIO():
    ...     sequences.activate_disk()
    >>> sequences.inputs.t.diskflag
    True
    >>> with TestIO():
    ...     sequences.load_series()
    ...     round_(sequences.inputs.t.series)
    1.0, 2.0, 3.0, 4.0
    >>> with TestIO():
    ...     sequences.deactivate_disk()
    >>> sequences.inputs.t.diskflag
    False
    >>> hasattr(sequences.inputs.t, "series")
    False

    Methods |Sequences.ram2disk| and |Sequences.disk2ram| allow moving
    data from RAM to disk and from disk to RAM, respectively:

    >>> sequences.activate_ram()
    >>> sequences.inputs.t.ramflag
    True
    >>> sequences.inputs.t.series = 1.0, 2.0, 3.0, 4.0
    >>> with TestIO():
    ...     sequences.ram2disk()
    >>> sequences.inputs.t.diskflag
    True
    >>> with TestIO():
    ...     round_(sequences.inputs.t.series)
    1.0, 2.0, 3.0, 4.0
    >>> with TestIO():
    ...     sequences.disk2ram()
    >>> round_(sequences.inputs.t.series)
    1.0, 2.0, 3.0, 4.0

    The documentation on class |IOSequence| explains the underlying
    functionalities of class |IOSequence| in more detail.

    >>> pub.options.checkseries = True
    >>> pub.sequencemanager.generaloverwrite = False

    .. testsetup::

        >>> from hydpy import Node, Element
        >>> Node.clear_all()
        >>> Element.clear_all()
    """

    model: "modeltools.Model"
    inlets: "InletSequences"
    receivers: "ReceiverSequences"
    inputs: "InputSequences"
    factors: "FactorSequences"
    fluxes: "FluxSequences"
    states: "StateSequences"
    logs: "LogSequences"
    aides: "AideSequences"
    outlets: "OutletSequences"
    senders: "SenderSequences"

    def __init__(
        self,
        model: "modeltools.Model",
        cls_inlets: Optional[Type["InletSequences"]] = None,
        cls_receivers: Optional[Type["ReceiverSequences"]] = None,
        cls_inputs: Optional[Type["InputSequences"]] = None,
        cls_factors: Optional[Type["FactorSequences"]] = None,
        cls_fluxes: Optional[Type["FluxSequences"]] = None,
        cls_states: Optional[Type["StateSequences"]] = None,
        cls_logs: Optional[Type["LogSequences"]] = None,
        cls_aides: Optional[Type["AideSequences"]] = None,
        cls_outlets: Optional[Type["OutletSequences"]] = None,
        cls_senders: Optional[Type["SenderSequences"]] = None,
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
        default: Type[ModelSequencesType],
        class_: Optional[Type[ModelSequencesType]],
        cymodel,
        cythonmodule,
    ) -> ModelSequencesType:
        name = default.__name__
        if class_ is None:
            class_ = copy.copy(default)
            setattr(class_, "CLASSES", ())
        return class_(self, getattr(cythonmodule, name, None), cymodel)

    @property
    def iosubsequences(self) -> Iterator["ModelIOSequences"]:
        """Yield all relevant |IOSequences| objects handled by the current
        |Sequences| object.

        The currently available IO-subgroups are `inputs`, `fluxes`,
        and `states`.

        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_v1", "1d")
        >>> for subseqs in model.sequences.iosubsequences:
        ...     print(subseqs.name)
        inputs
        factors
        fluxes
        states

        However, not all models implement sequences for all these
        subgroups.  Property |Sequences.iosubsequences| only yields
        those subgroups which are non-empty:

        >>> model = prepare_model("hstream_v1", "1d")
        >>> for subseqs in model.sequences.iosubsequences:
        ...     print(subseqs.name)
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

    def activate_disk(self) -> None:
        """Call method |IOSequences.activate_disk| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.activate_disk()

    def deactivate_disk(self) -> None:
        """Call method |IOSequences.deactivate_disk| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.deactivate_disk()

    def activate_ram(self) -> None:
        """Call method |IOSequences.activate_ram| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.activate_ram()

    def deactivate_ram(self) -> None:
        """Call method |IOSequences.deactivate_ram| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.deactivate_ram()

    def ram2disk(self):
        """Call method |IOSequences.ram2disk| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.ram2disk()

    def disk2ram(self):
        """Call method |IOSequence.disk2ram| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.disk2ram()

    def load_series(self):
        """Call method |IOSequences.load_series| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.load_series()

    def save_series(self):
        """Call method |IOSequence.save_ext| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.save_series()

    def open_files(self, idx: int = 0) -> None:
        """Call method |IOSequences.open_files| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.open_files(idx)

    def close_files(self) -> None:
        """Call method |IOSequences.close_files| of all handled
        |IOSequences| objects."""
        for subseqs in self.iosubsequences:
            subseqs.close_files()

    def load_data(self, idx: int) -> None:
        """Call method |ModelIOSequences.load_data| of the handled
        |sequencetools.InputSequences| object."""
        self.inputs.load_data(idx)

    def save_data(self, idx: int) -> None:
        """Call method |ModelIOSequences.save_data| of the handled
        |sequencetools.FluxSequences| and |sequencetools.StateSequences|
        objects."""
        self.inputs.save_data(idx)
        self.factors.save_data(idx)
        self.fluxes.save_data(idx)
        self.states.save_data(idx)

    def reset(self) -> None:
        """Call method |ConditionSequence.reset| of all handled
        |ConditionSequence| objects."""
        self.states.reset()
        self.logs.reset()

    @property
    def conditionsequences(self) -> Iterator["ConditionSequence"]:
        """Generator object yielding all conditions (|StateSequence| and |LogSequence|
        objects).
        """
        for state in self.states:
            yield state
        for log in self.logs:
            yield log

    @property
    def conditions(self) -> Dict[str, Dict[str, Union[float, numpy.ndarray]]]:
        """A nested dictionary which contains the values of all condition
        sequences.

        See the documentation on property |HydPy.conditions| for further
        information.
        """
        conditions: Dict[str, Dict[str, Union[float, numpy.ndarray]]] = {}
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
        """Read the initial conditions from a file and assign them to the
        respective |StateSequence| and |LogSequence| objects handled by
        the actual |Sequences| object.

        The documentation on method |HydPy.load_conditions| of class
        |HydPy| explains how to read and write condition values for
        complete *HydPy* projects in the most convenient manner.
        However, using the underlying methods |Sequences.load_conditions|
        and |Sequences.save_conditions| directly offers the advantage to
        specify alternative filenames.  We demonstrate this through
        using the `land_dill` |Element| object of the `LahnH` example
        project and focussing on the values of state sequence
        |hland_states.SM|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> sequences = hp.elements.land_dill.model.sequences
        >>> sequences.states.sm
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)

        From now on, we work in the freshly created condition
        directory `test`:

        >>> with TestIO():
        ...     pub.conditionmanager.currentdir = "test"

        We set all soil moisture values to zero and write the updated
        values to the file `cold_start.py`:

        >>> sequences.states.sm(0.0)

        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     sequences.save_conditions("cold_start.py")

        Trying to reload from the written file (after changing the
        soil moisture values again) without passing the file name
        fails due to assuming the elements name as file
        name base:

        >>> sequences.states.sm(100.0)
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     sequences.load_conditions()
        Traceback (most recent call last):
        ...
        FileNotFoundError: While trying to load the initial conditions \
of element `land_dill`, the following error occurred: [Errno 2] No such \
file or directory: '...land_dill.py'

        One does not need to state the file extensions (`.py`)  explicitly:

        >>> with TestIO():
        ...     sequences.load_conditions("cold_start")
        >>> sequences.states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        Note that determining the file name automatically requires a
        proper reference to the related |Element| object:

        >>> del sequences.model.element
        >>> with TestIO():
        ...     sequences.save_conditions()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to save the actual conditions of \
element `?`, the following error occurred: To load or save the conditions \
of a model from or to a file, its filename must be known.  This can be \
done, by passing filename to method `load_conditions` or `save_conditions` \
directly.  But in complete HydPy applications, it is usally assumed to be \
consistent with the name of the element handling the model.  Actually, \
neither a filename is given nor does the model know its master element.

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
                    f"While trying to load the initial conditions of "
                    f"element `{objecttools.devicename(self)}`"
                )

    def save_conditions(self, filename: Optional[str] = None) -> None:
        """Query the actual conditions of the |StateSequence| and
        |LogSequence| objects handled by the actual |Sequences| object
        and write them into an initial condition file.

        See the documentation on method |Sequences.load_conditions| for
        further information.
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
                f"While trying to save the actual conditions of "
                f"element `{objecttools.devicename(self)}`"
            )

    def __prepare_filename(self, filename: Optional[str]) -> str:
        if filename is None:
            filename = objecttools.devicename(self)
            if filename == "?":
                raise RuntimeError(
                    "To load or save the conditions of a model from or to a "
                    "file, its filename must be known.  This can be done, "
                    "by passing filename to method `load_conditions` or "
                    "`save_conditions` directly.  But in complete HydPy "
                    "applications, it is usally assumed to be consistent "
                    "with the name of the element handling the model. "
                    " Actually, neither a filename is given nor does the "
                    "model know its master element."
                )
        if not filename.endswith(".py"):
            filename += ".py"
        return filename

    def trim_conditions(self) -> None:
        """Call method |trim| of each handled |ConditionSequence|.

        |Sequences.trim_conditions| is just a convenience function for
        calling method |trim| of all |StateSequence| and |LogSequence|
        objects returned by property |Sequences.conditionsequences|.
        We demonstrate its functionality by preparing an instance of
        application model |lland_v1|, using its available default
        values, and defining out-of-bound values of the soil moisture
        state sequence |lland_states.BoWa|:

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

    def update_outputs(self) -> None:
        """Call the method |OutputSequences.update_outputs| of the subattributes
        |Sequences.factors|, |Sequences.states|, and |Sequences.fluxes|.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.factors.update_outputs()
        self.fluxes.update_outputs()
        self.states.update_outputs()

    def __iter__(self) -> Iterator["ModelSequences"]:
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

    def __len__(self):
        return sum(1 for _ in self)

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_v1", "1d")
        >>> dir(model.sequences)
        ['activate_disk', 'activate_ram', 'aides', 'close_files', 'conditions', \
'conditionsequences', 'deactivate_disk', 'deactivate_ram', 'disk2ram', 'factors', \
'fluxes', 'inlets', 'inputs', 'iosubsequences', 'load_conditions', 'load_data', \
'load_series', 'logs', 'model', 'open_files', 'outlets', 'ram2disk', 'receivers', \
'reset', 'save_conditions', 'save_data', 'save_series', 'senders', 'states', \
'trim_conditions', 'update_outputs']
        """
        return objecttools.dir_(self)


class SubSequences(
    variabletools.SubVariables[
        SequencesType,
        SequenceType,
        variabletools.FastAccessType,
    ],
):
    """Base class for handling subgroups of sequences.

    Each |SubSequences| object has a `fastaccess` attribute.  When
    working in pure Python mode, this is an instance either of (a
    subclass of) class |FastAccess|:

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

    When working in Cython mode (which is the default mode and much
    faster), `fastaccess` is an object of Cython extension class
    `FastAccessNodeSequence` of module `sequenceutils` or of a Cython
    extension class specialised for the respective model and sequence group:

    >>> with pub.options.usecython(True):
    ...     model = prepare_model("lland_v1")
    >>> classname(model.sequences.inputs.fastaccess)
    'InputSequences'
    >>> from hydpy.cythons.sequenceutils import FastAccessNodeSequence
    >>> with pub.options.usecython(True):
    ...     node = Node("test2")
    >>> isinstance(Node("test2").sequences.fastaccess, FastAccessNodeSequence)
    True

    See the documentation of similar class |SubParameters| for further
    information.  However, note the difference that model developers
    should not subclass |SubSequences| directly but specialised subclasses
    like |sequencetools.FluxSequences| or |sequencetools.StateSequences|
    instead.

    .. testsetup::

        >>> Node.clear_all()
    """

    @property
    def name(self) -> str:
        """The class name in lower case letters omitting the last
        eight characters ("equences").

        >>> from hydpy.core.sequencetools import StateSequences
        >>> class StateSequences(StateSequences):
        ...     CLASSES = ()
        >>> StateSequences(None).name
        'states'
        """
        return type(self).__name__[:-8].lower()


class ModelSequences(
    SubSequences[
        Sequences,
        ModelSequenceType,
        variabletools.FastAccessType,
    ],
):
    """Base class for handling model-related subgroups of sequences."""

    seqs: Sequences
    _cymodel: Optional[CyModelProtocol]

    def __init__(
        self,
        master: Sequences,
        cls_fastaccess: Optional[Type[variabletools.FastAccessType]] = None,
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
    SubSequences[
        SequencesType,
        IOSequenceType,
        FastAccessIOSequenceType,
    ],
):
    """Subclass of |SubSequences|, specialised for handling |IOSequence|
    objects."""

    def activate_ram(self):
        """Call method |IOSequence.activate_ram| of all handled
        |IOSequence| objects."""
        for seq in self:
            seq.activate_ram()

    def deactivate_ram(self):
        """Call method |IOSequence.deactivate_ram| of all handled
        |IOSequence| objects."""
        for seq in self:
            seq.deactivate_ram()

    def activate_disk(self):
        """Call method |IOSequence.activate_disk| of all handled
        |IOSequence| objects."""
        for seq in self:
            seq.activate_disk()

    def deactivate_disk(self):
        """Call method |IOSequence.deactivate_disk| of all handled
        |IOSequence| objects."""
        for seq in self:
            seq.deactivate_disk()

    def ram2disk(self):
        """Call method |IOSequence.ram2disk| of all handled
        |IOSequence| objects."""
        for seq in self:
            seq.ram2disk()

    def disk2ram(self):
        """Call method |IOSequence.disk2ram| of all handled
        |IOSequence| objects."""
        for seq in self:
            seq.disk2ram()

    def load_series(self):
        """Call method |IOSequence.load_ext| of all handled
        |IOSequence| objects."""
        for seq in self:
            if seq.memoryflag:
                seq.load_ext()

    def save_series(self):
        """Call method |IOSequence.save_ext| of all handled
        |IOSequence| objects."""
        for seq in self:
            if seq.memoryflag:
                seq.save_ext()

    def open_files(self, idx: int = 0) -> None:
        """Call method |FastAccessIOSequence.open_files| of the
        |FastAccessIOSequence| object handled as attribute `fastaccess`."""
        self.fastaccess.open_files(idx)

    def close_files(self):
        """Call method |FastAccessIOSequence.close_files| of the
        |FastAccessIOSequence| object handled as attribute `fastaccess`."""
        self.fastaccess.close_files()


class ModelIOSequences(
    IOSequences[
        Sequences,
        ModelIOSequenceType,
        FastAccessIOSequenceType,
    ],
    ModelSequences[
        ModelIOSequenceType,
        FastAccessIOSequenceType,
    ],
):
    """Base class for handling model-related subgroups of |IOSequence| objects."""

    def load_data(self, idx: int) -> None:
        """Call method |FastAccessIOSequence.load_data| of the
        |FastAccessIOSequence| object handled as attribute `fastaccess`."""
        self.fastaccess.load_data(idx)

    def save_data(self, idx: int) -> None:
        """Call method |FastAccessIOSequence.save_data| of the
        |FastAccessIOSequence| object handled as attribute `fastaccess`."""
        self.fastaccess.save_data(idx)


class InputSequences(
    ModelIOSequences[
        "InputSequence",
        FastAccessInputSequence,
    ],
):
    """Base class for handling |InputSequence| objects."""

    _CLS_FASTACCESS_PYTHON = FastAccessInputSequence


class OutputSequences(
    ModelIOSequences[
        OutputSequenceType,
        FastAccessOutputSequence,
    ],
):
    """Base class for handling |OutputSequence| objects."""

    _CLS_FASTACCESS_PYTHON = FastAccessOutputSequence

    def update_outputs(self) -> None:
        """Call method |FastAccessOutputSequence.update_outputs| of the
        |FastAccessOutputSequence| object handled as attribute `fastaccess`."""
        if self:
            self.fastaccess.update_outputs()

    @property
    def numericsequences(self) -> Iterator["FluxSequence"]:
        """Iterator for "numerical" sequences.

        "numerical" means that the |Sequence_.NUMERIC| class attribute of the actual
        sequence is `True`:

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


class FactorSequences(
    OutputSequences[
        "FactorSequence",
    ],
):
    """Base class for handling |FactorSequence| objects."""


class FluxSequences(
    OutputSequences[
        "FluxSequence",
    ],
):
    """Base class for handling |FluxSequence| objects."""

    @property
    def name(self) -> str:
        """Always return the string "fluxes"."""
        return "fluxes"


class StateSequences(
    OutputSequences[
        "StateSequence",
    ],
):
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
        """Call method |StateSequence.new2old| of all handled
        |StateSequence| objects."""
        for seq in self:
            seq.new2old()

    def reset(self) -> None:
        """Call method |ConditionSequence.reset| of all handled
        |StateSequence| objects."""
        for seq in self:
            seq.reset()


class LogSequences(
    ModelSequences[
        "LogSequence",
        variabletools.FastAccess,
    ],
):
    """Base class for handling |LogSequence| objects."""

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess

    def reset(self) -> None:
        """Call method |ConditionSequence.reset| of all handled
        |LogSequence| objects."""
        for seq in self:
            seq.reset()


class AideSequences(
    ModelSequences[
        "AideSequence",
        variabletools.FastAccess,
    ],
):
    """Base class for handling |AideSequence| objects."""

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess


class LinkSequences(
    ModelSequences[
        LinkSequenceType,
        FastAccessLinkSequence,
    ],
):
    """Base class for handling |LinkSequence| objects."""

    _CLS_FASTACCESS_PYTHON = FastAccessLinkSequence


class InletSequences(
    LinkSequences[
        "InletSequence",
    ],
):
    """Base class for handling "inlet" |LinkSequence| objects."""


class OutletSequences(
    LinkSequences[
        "OutletSequence",
    ],
):
    """Base class for handling "outlet" |LinkSequence| objects."""


class ReceiverSequences(
    LinkSequences[
        "ReceiverSequence",
    ],
):
    """Base class for handling "receiver" |LinkSequence| objects."""


class SenderSequences(
    LinkSequences[
        "SenderSequence",
    ],
):
    """Base class for handling "sender" |LinkSequence| objects."""


class Sequence_(
    variabletools.Variable[
        SubSequencesType,
        variabletools.FastAccessType,
    ],
):
    """Base class for defining different kinds of sequences.

    Note that model developers should not derive their model-specific
    sequence classes from |Sequence_| directly but from the "final"
    subclasses provided in module |sequencetools| (e.g. |FluxSequence|).

    From the model developer perspective and especially from the user
    perspective, |Sequence_| is only a small extension of its base class
    |Variable|.  One relevant extension is that (only the) 0-dimensional
    sequence objects come with a predefined shape:

    >>> from hydpy import prepare_model
    >>> model = prepare_model("lland_v1", "1d")
    >>> model.sequences.fluxes.qa.shape
    ()
    >>> evpo = model.sequences.fluxes.evpo
    >>> evpo.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for \
variable `evpo` can only be retrieved after it has been defined.

    For high numbers of entries, the string representation puts the
    names of the constants within a list (to make the string representations
    executable under Python 3.6; this behaviour changes as soon
    as Python 3.7 becomes the oldest supported version):

    >>> evpo.shape = (255,)
    >>> evpo    # doctest: +ELLIPSIS
    evpo(nan, nan, ..., nan, nan)
    >>> evpo.shape = (256,)
    >>> evpo    # doctest: +ELLIPSIS
    evpo([nan, nan, ..., nan, nan])

    For consistency with the usage of |Parameter| subclasses, |Sequence_|
    objects are also "callable" for setting their values (but in a much
    less and flexible manner):

    >>> evpo(2.0)
    >>> evpo    # doctest: +ELLIPSIS
    evpo([2.0, 2.0, ..., 2.0, 2.0])

    Under the hood, class |Sequence_| also prepares some attributes
    of its |FastAccess| object, used for performing the actual simulation
    calculations.   Framework developers should note that the respective
    `fastaccess` attributes contain both the name of the sequence and the
    name of the original attribute in lower case letters.  We take `NDIM`
    as an example:

    >>> evpo.fastaccess._evpo_ndim
    1

    Some of these attributes require updating under some situations.
    For example, other sequences than |AideSequence| objects require
    a "length" attribute, which needs to be updated each time the
    sequence's shape changes:

    >>> evpo.fastaccess._evpo_length
    256
    """

    TYPE: Type[float] = float
    INIT: float = 0.0
    NUMERIC: bool

    strict_valuehandling: bool = False

    @property
    def subseqs(self) -> SubSequencesType:
        """Alias for attribute `subvars`."""
        return self.subvars

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._set_fastaccessattribute("ndim", self.NDIM)
        self._set_fastaccessattribute("length", 0)
        for idx in range(self.NDIM):
            self._set_fastaccessattribute(f"length_{idx}", 0)
        self._finalise_connections()

    def _get_fastaccessattribute(self, suffix: str) -> Any:
        return getattr(self.fastaccess, f"_{self.name}_{suffix}")

    def _set_fastaccessattribute(self, suffix: str, value: Any) -> None:
        setattr(self.fastaccess, f"_{self.name}_{suffix}", value)

    def _finalise_connections(self) -> None:
        """A hook method, called at the end of method
        `__hydpy__connect_variable2subgroup__` for initialising
        values and some related attributes, eventually."""
        if not self.NDIM:
            self.shape = ()

    @property
    def initinfo(self) -> Tuple[Union[float, "pointerutils.Double"], bool]:
        """A |tuple| containing the initial value and |True| or a missing
        value and |False|, depending on the actual |Sequence_| subclass and
        the actual value of option |Options.usedefaultvalues|.

        In the following, we do not explain property |Sequence_.initinfo|
        itself but show how it affects initialising new |Sequence_| objects.
        Therefore, let us define a sequence test class and prepare a
        function for initialising it and connecting the resulting instance
        to a |ModelSequences| object:

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

        Enable it through setting |Options.usedefaultvalues| to |True|:

        >>> from hydpy import pub
        >>> with pub.options.usedefaultvalues(True):
        ...     prepare()
        test(0.0)

        Attribute `INIT` of class |Sequence_| comes with the value `0.0`
        by default, which should be reasonable for most |Sequence_|
        subclasses.  However, subclasses can define other values.
        Most importantly, note the possibility to set `INIT` to `None`
        for sequences that do not allow defining a reasonabe initial
        value for all possible situations:

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
        islong = len(self) > 255
        return variabletools.to_repr(self, self.value, islong)

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy.core.sequencetools import FluxSequence
        >>> sequence = FluxSequence(None)
        >>> from hydpy import print_values
        >>> print_values(dir(sequence))
        INIT, NOT_DEEPCOPYABLE_MEMBERS, SPAN, TYPE, activate_disk,
        activate_ram, adjust_series, adjust_short_series, aggregate_series,
        aggregation_ext, availablemasks, average_series, average_values,
        check_completeness, commentrepr, deactivate_disk, deactivate_ram,
        descr_device, descr_model, descr_sequence, dirpath_ext, dirpath_int,
        disk2ram, diskflag, evalseries, fastaccess, filename_ext,
        filename_int, filepath_ext, filepath_int, filetype_ext, get_submask,
        initinfo, load_ext, mask, memoryflag, name, numericshape, outputflag,
        overwrite_ext, ram2disk, ramflag, rawfilename, refweights, save_ext,
        save_mean, series, seriesshape, set_pointer, shape, simseries,
        strict_valuehandling, subseqs, subvars, unit, update_fastaccess,
        value, values, verify
        """
        return objecttools.dir_(self)


class _IOProperty(
    propertytools.DefaultProperty[
        propertytools.InputType,
        propertytools.OutputType,
    ]
):

    DOCSTRING: ClassVar[str]

    def __init__(self) -> None:
        super().__init__(fget=self.__fget)

    def __set_name__(self, objtype: Type, name: str) -> None:
        super().__set_name__(objtype, name)
        attr_seq = self.name
        cls = self.objtype.__name__
        attr_man = f"{cls.lower()[:-8]}{self.name.split('_')[0]}"
        self.__attr_manager = attr_man
        self.set_doc(
            f"""
            {self.DOCSTRING}

        Attribute {attr_seq} is connected with attribute {attr_man} of 
        class |SequenceManager|, as shown by the following technical 
        example (see the documentation on class |IOSequence| for some 
        explanations on the usage of this and similar properties of 
        |IOSequence| subclasses):

        >>> from hydpy.core.filetools import SequenceManager
        >>> temp = SequenceManager.{attr_man}
        >>> SequenceManager.{attr_man} = "global"
        >>> from hydpy import pub
        >>> pub.sequencemanager = SequenceManager()
        >>> from hydpy.core.sequencetools import {cls}
        >>> sequence = {cls}(None)
        >>> sequence.{attr_seq}
        'global'
        >>> sequence.{attr_seq} = "local"
        >>> sequence.{attr_seq}
        'local'
        >>> del sequence.{attr_seq}
        >>> sequence.{attr_seq}
        'global'
        >>> SequenceManager.{attr_man} = temp
        """
        )

    def __fget(self, obj):
        try:
            manager = hydpy.pub.sequencemanager
        except RuntimeError:
            raise RuntimeError(
                f"For sequence {objecttools.devicephrase(obj)} attribute "
                f"{self.name} cannot be determined.  Either set it manually "
                "or prepare `pub.sequencemanager` correctly."
            ) from None
        return getattr(manager, self.__attr_manager)


class _FileType(_IOProperty[str, str]):

    DOCSTRING = "Ending of the external data file."


class _DirPathProperty(_IOProperty[str, str]):

    DOCSTRING = "Absolute path of the directory of the external data file."


class _AggregationProperty(_IOProperty[str, str]):

    DOCSTRING = (
        "Type of aggregation performed when writing the "
        "time-series data to an external data file."
    )


class _OverwriteProperty(_IOProperty[bool, bool]):

    DOCSTRING = (
        "True/False flag indicating if overwriting an existing "
        "data file is allowed or not."
    )


class IOSequence(
    Sequence_[
        IOSequencesType,
        FastAccessIOSequenceType,
    ],
):
    """Base class for sequences with input/output functionalities.

    The |IOSequence| subclasses |InputSequence|, |FluxSequence|,
    |StateSequence|, and |NodeSequence| all implement similar
    special properties, which configure the processes of reading
    and writing time-series files.  In the following, property
    `filetype_ext` is taken as an example to explain how to
    handle them:

    Usually, each sequence queries its current "external" file type
    from the |SequenceManager| object stored in module |pub|:

    >>> from hydpy import pub
    >>> from hydpy.core.filetools import SequenceManager
    >>> pub.sequencemanager = SequenceManager()

    Depending if the actual sequence stems from |InputSequence|,
    |FluxSequence|,  |StateSequence|, or |NodeSequence|, either
    |SequenceManager.inputfiletype|, |SequenceManager.fluxfiletype|,
    |SequenceManager.statefiletype|, or |SequenceManager.nodefiletype|
    are queried:

    >>> pub.sequencemanager.inputfiletype = "npy"
    >>> pub.sequencemanager.fluxfiletype = "asc"
    >>> pub.sequencemanager.nodefiletype = "nc"
    >>> from hydpy.core import sequencetools as st
    >>> st.InputSequence(None).filetype_ext
    'npy'
    >>> st.FluxSequence(None).filetype_ext
    'asc'
    >>> st.NodeSequence(None).filetype_ext
    'nc'

    Alternatively, you can specify `filetype_ext` for each sequence
    object individually:

    >>> seq = st.InputSequence(None)
    >>> seq.filetype_ext
    'npy'
    >>> seq.filetype_ext = "nc"
    >>> seq.filetype_ext
    'nc'
    >>> del seq.filetype_ext
    >>> seq.filetype_ext
    'npy'

    If neither a specific definition nor a |SequenceManager| object
    is available, property `filetype_ext` raises the following error:

    >>> del pub.sequencemanager
    >>> seq.filetype_ext
    Traceback (most recent call last):
    ...
    RuntimeError: For sequence `inputsequence` attribute filetype_ext \
cannot be determined.  Either set it manually or prepare \
`pub.sequencemanager` correctly.

    How to read and write time-series files is explained in the
    documentation on modules |filetools| and |netcdftools| in some
    detail.  However, reading and writing time-series files is
    disabled by default, due to reasons of efficiency.  You first
    need to prepare the |IOSequence.series| attribute of the
    relevant |IOSequence| objects.  Typically, you do this by calling
    methods like |HydPy.prepare_inputseries| of class |HydPy|.
    Here, we use the related features the |IOSequence| class itself,
    which is a little more complicated but also more flexible when
    scripting complex workflows.

    We use the `LahnH` example project and focus on the `input`, `factor`, and `flux`
    sequences:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> inputs = hp.elements.land_lahn_1.model.sequences.inputs
    >>> factors = hp.elements.land_lahn_1.model.sequences.factors
    >>> fluxes = hp.elements.land_lahn_1.model.sequences.fluxes

    |IOSequence| objects come with the properties |IOSequence.ramflag|
    and |IOSequence.diskflag|, telling if the respective time-series is
    available in RAM, on disk, or not available at all.  Input sequences
    are the only ones who need to have one flag activated. Otherwise,
    the input series would not be available during simulation runs.
    For example, input sequence |hland_inputs.T| stores its time-series
    data in RAM internally, which is the much faster approach and should
    be preferred, as long as limited storage is not an issue:

    >>> inputs.t.ramflag
    True
    >>> inputs.t.diskflag
    False
    >>> from hydpy import repr_, round_
    >>> round_(inputs.t.series, 1)
    -0.7, -1.5, -4.2, -7.4

    Convenience function |prepare_full_example_2| also activates the
    |IOSequence.ramflag| of all factor and flux sequences, which is not necessary to
    perform a successful simulation but is required to query the complete time-series
    of simulated values afterwards (otherwise, only the last simulated value would
    available after a simulation run):

    >>> factors.tc.ramflag
    True
    >>> round_(factors.tc.series[:, 0])
    nan, nan, nan, nan

    Use |IOSequence.activate_ram| or |IOSequence.activate_disk| to force a sequence to
    handle time-series data in RAM or on disk, respectively.  We now activate the
    |IOSequence.diskflag| of factor sequence |hland_factors.TMean| (which automatically
    disables the |IOSequence.ramflag|).  Note that we need to change the current
    working directory to the `iotesting` directory temporarily (by using class |TestIO|)
    to make sure to create that the related file in the correct directory:

    >>> with TestIO():
    ...     factors.tmean.activate_disk()
    ...     repr_(factors.tmean.filepath_int)    # doctest: +ELLIPSIS
    '...iotesting/LahnH/series/temp/land_lahn_1_factor_tmean.bin'

    The user can access the time-series data in the same manner as if being handled in
    RAM:

    >>> factors.tmean.ramflag
    False
    >>> factors.tmean.diskflag
    True
    >>> with TestIO():
    ...     round_(factors.tmean.series)
    nan, nan, nan, nan

    For completeness of testing, we also activate the |IOSequence.diskflag|
    of a 1-dimensional sequence:

    >>> from pprint import pprint
    >>> with TestIO():
    ...     factors.fracrain.activate_disk()
    ...     pprint(sorted(os.listdir("LahnH/series/temp")))
    ['land_lahn_1_factor_fracrain.bin', 'land_lahn_1_factor_tmean.bin']

    Apply methods |IOSequence.deactivate_ram| or |IOSequence.deactivate_disk|
    for sequences that do not provide data relevant for your analysis:

    >>> fluxes.ep.deactivate_ram()
    >>> fluxes.ep.ramflag
    False
    >>> fluxes.ep.diskflag
    False
    >>> fluxes.ep.series
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `ep` of element `land_lahn_1` is not \
requested to make any internal data available.

    After a simulation run, the |IOSequence.series| of flux sequence
    |hland_fluxes.EP| is still not available but the time-series data
    of the other discussed series with either true |IOSequence.ramflag|
    or |IOSequence.diskflag| values are:

    >>> with TestIO():
    ...     hp.simulate()

    >>> fluxes.ep.series = 1.0
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `ep` of element `land_lahn_1` is not \
requested to make any internal data available.

    >>> round_(fluxes.q1.series, 1)
    0.4, 0.4, 0.4, 0.4
    >>> round_(factors.tc.series[:, 0], 1)
    0.2, -0.6, -3.4, -6.6
    >>> with TestIO():
    ...     round_(factors.tmean.series, 1)
    -1.0, -1.8, -4.5, -7.7
    >>> with TestIO():
    ...     round_(factors.fracrain.series[:, 0], 1)
    0.3, 0.0, 0.0, 0.0

    You cannot only access the time-series data of individual |IOSequence|
    objects, but you can also modify it.  See, for example, the simulated time
    series for flux sequence |hland_fluxes.PC| (adjusted precipitation),
    which is zero, because the values of input sequence |hland_inputs.P|
    (given precipitation) are also zero:

    >>> round_(fluxes.pc.series[:, 0], 1)
    0.0, 0.0, 0.0, 0.0

    We can assign different values to attribute |IOSequence.series| of
    sequence |hland_inputs.P|, perform a new simulation run, and see that
    the newly calculated time-series of sequence |hland_fluxes.PC|
    reflects our data modification:

    >>> inputs.p.ramflag
    True
    >>> inputs.p.series = 10.0
    >>> with TestIO():
    ...     hp.simulate()
    >>> round_(fluxes.pc.series[:, 0], 1)
    10.2, 11.3, 11.3, 11.3

    Next, we show that the same feature works for time-series data
    handled on disk.  Therefore, we first call method |IOSequence.ram2disk|,
    which disables |IOSequence.ramflag| and enables |IOSequence.diskflag|
    without any loss of information:

    >>> with TestIO():
    ...     inputs.p.ram2disk()
    ...     pprint(sorted(os.listdir("LahnH/series/temp")))
    ['land_lahn_1_factor_fracrain.bin',
     'land_lahn_1_factor_tmean.bin',
     'land_lahn_1_input_p.bin']
    >>> inputs.p.ramflag
    False
    >>> inputs.p.diskflag
    True
    >>> with TestIO():
    ...     round_(inputs.p.series, 1)
    10.0, 10.0, 10.0, 10.0

    Data modifications still influence simulation runs as to be expected:

    >>> with TestIO():
    ...     inputs.p.series = 20.0
    ...     hp.simulate()
    ...     round_(fluxes.pc.series[:, 0], 1)
    20.5, 22.6, 22.6, 22.6

    Method |IOSequence.disk2ram| is the counterpart to |IOSequence.ram2disk|:

    >>> with TestIO():
    ...     inputs.p.disk2ram()
    ...     pprint(sorted(os.listdir("LahnH/series/temp")))
    ['land_lahn_1_factor_fracrain.bin', 'land_lahn_1_factor_tmean.bin']
    >>> inputs.p.ramflag
    True
    >>> inputs.p.diskflag
    False
    >>> round_(inputs.p.series, 1)
    20.0, 20.0, 20.0, 20.0

    Method |IOSequence.deactivate_disk| works analogue to
    |IOSequence.deactivate_ram|:

    >>> with TestIO():
    ...     factors.fracrain.deactivate_disk()
    ...     pprint(sorted(os.listdir("LahnH/series/temp")))
    ['land_lahn_1_factor_tmean.bin']
    >>> factors.fracrain.ramflag
    False
    >>> factors.fracrain.diskflag
    False

    Both methods |IOSequence.deactivate_ram| and |IOSequence.deactivate_disk|
    do nothing in case the respective flag is |False| already:

    >>> fluxes.pc.deactivate_ram()
    >>> with TestIO():
    ...     factors.fracrain.deactivate_disk()

    You can query property |IOSequence.memoryflag|, if you are only
    interested to know if a sequence handles stores its time-series
    data, but not how:

    >>> fluxes.pc.memoryflag
    False
    >>> factors.tmean.memoryflag
    True
    >>> inputs.p.memoryflag
    True

    Another convenience property is |IOSequence.seriesshape|, which
    combines the length of the simulation period with the shape of
    the individual |IOSequence| object:

    >>> inputs.p.seriesshape
    (4,)
    >>> fluxes.pc.seriesshape
    (4, 13)

    Note that resetting the |IOSequence.shape| of am |IOSequence| object
    does not change how it handles its internal time-series data, but
    results in a loss of current information:

    >>> factors.tc.seriesshape
    (4, 13)
    >>> factors.fastaccess._tc_length
    13
    >>> round_(factors.tc.series[:, 0], 1)
    0.2, -0.6, -3.4, -6.6

    >>> factors.tc.shape = (2,)
    >>> factors.tc.seriesshape
    (4, 2)
    >>> factors.fastaccess._tc_length
    2
    >>> round_(factors.tc.series[:, 0], 1)
    nan, nan, nan, nan

    Resetting the |IOSequence.shape| of |IOSequence| objects which
    are not storing their internal time-series data works too:

    >>> fluxes.pc.seriesshape
    (4, 13)
    >>> fluxes.fastaccess._pc_length
    13
    >>> round_(fluxes.pc.series[:, 0], 1)
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `pc` of element `land_lahn_1` is not \
requested to make any internal data available.

    >>> fluxes.pc.shape = (2,)
    >>> fluxes.pc.seriesshape
    (4, 2)
    >>> fluxes.fastaccess._pc_length
    2
    >>> round_(fluxes.pc.series[:, 0], 1)
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `pc` of element `land_lahn_1` is not \
requested to make any internal data available.

    .. testsetup::

        >>> from hydpy import Node, Element
        >>> Node.clear_all()
        >>> Element.clear_all()
    """

    filetype_ext: _FileType
    dirpath_ext: _DirPathProperty
    aggregation_ext: _AggregationProperty
    overwrite_ext: _OverwriteProperty

    def _finalise_connections(self) -> None:
        self._set_fastaccessattribute("ramflag", False)
        self._set_fastaccessattribute("diskflag", False)
        try:
            self._set_fastaccessattribute("file", "")
        except AttributeError:
            pass
        super()._finalise_connections()

    @propertytools.DefaultPropertyStr
    def rawfilename(self) -> str:
        """|DefaultProperty| handling the filename without ending for
        external and internal data files.

        >>> from hydpy.core.sequencetools import StateSequence
        >>> class Test(StateSequence):
        ...     descr_device = "node1"
        ...     descr_sequence = "subgroup_test"
        >>> Test(None).rawfilename
        'node1_subgroup_test'
        """
        return f"{self.descr_device}_{self.descr_sequence}"

    @propertytools.DefaultPropertyStr
    def filename_ext(self) -> str:
        """The full filename of the external data file.

        The "external" filename consists of |IOSequence.rawfilename| and
        of |FluxSequence.filetype_ext|.  For simplicity, we add the
        attribute `rawfilename` to the initialised sequence object
        in the following example:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> seq = StateSequence(None)
        >>> seq.rawfilename = "test"
        >>> seq.filetype_ext = "nc"
        >>> seq.filename_ext
        'test.nc'
        """
        return ".".join((self.rawfilename, self.filetype_ext))

    @property
    def filename_int(self) -> str:
        """The full filename of the internal data file.

        The "internal" filename consists of |IOSequence.rawfilename|
        and the file ending `.bin`.  For simplicity, we add the
        attribute `rawfilename` to the initialised sequence object
        in the following example:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> seq = StateSequence(None)
        >>> seq.rawfilename = "test"
        >>> seq.filename_int
        'test.bin'
        """
        return self.rawfilename + ".bin"

    @propertytools.DefaultPropertyStr
    def dirpath_int(self) -> str:
        """The absolute path of the directory of the internal data file.

        Usually, each sequence queries its current "internal" directory
        path from the |SequenceManager| object stored in module |pub|:

        >>> from hydpy import pub, repr_, TestIO
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        We overwrite |FileManager.basepath| and prepare a folder in the
        `iotesting` directory to simplify the following examples:

        >>> basepath = SequenceManager.basepath
        >>> SequenceManager.basepath = "test"
        >>> TestIO.clear()
        >>> import os
        >>> with TestIO():
        ...     os.makedirs("test/temp")

        Generally, property |IOSequence.dirpath_int| queries
        property |SequenceManager.tempdirpath|:

        >>> from hydpy.core import sequencetools as st
        >>> seq = st.InputSequence(None)
        >>> with TestIO():
        ...     repr_(seq.dirpath_int)
        'test/temp'

        Alternatively, you can specify |IOSequence.dirpath_int| for each
        sequence object individually:

        >>> seq.dirpath_int = "path"
        >>> os.path.split(seq.dirpath_int)
        ('', 'path')
        >>> del seq.dirpath_int
        >>> with TestIO():
        ...     os.path.split(seq.dirpath_int)
        ('test', 'temp')

        If neither a specific definition nor a |SequenceManager| object
        is, property `dirpath_int` raises the following error:

        >>> del pub.sequencemanager
        >>> seq.dirpath_int
        Traceback (most recent call last):
        ...
        RuntimeError: For sequence `inputsequence` the directory of \
the internal data file cannot be determined.  Either set it manually \
or prepare `pub.sequencemanager` correctly.

        Remove the `basepath` mock:

        >>> SequenceManager.basepath = basepath
        """
        try:
            return hydpy.pub.sequencemanager.tempdirpath
        except RuntimeError:
            raise RuntimeError(
                f"For sequence {objecttools.devicephrase(self)} "
                f"the directory of the internal data file cannot "
                f"be determined.  Either set it manually or prepare "
                f"`pub.sequencemanager` correctly."
            ) from None

    @propertytools.DefaultPropertyStr
    def filepath_ext(self) -> str:
        """The absolute path to the external data file.

        The path pointing to the "external" file consists of
        |FluxSequence.dirpath_ext| and |IOSequence.filename_ext|.  For
        simplicity, we define both manually in the following example:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> seq = StateSequence(None)
        >>> seq.dirpath_ext = "path"
        >>> seq.filename_ext = "file.npy"
        >>> from hydpy import repr_
        >>> repr_(seq.filepath_ext)
        'path/file.npy'
        """
        return os.path.join(self.dirpath_ext, self.filename_ext)

    @propertytools.DefaultPropertyStr
    def filepath_int(self) -> str:
        """The absolute path to the internal data file.

        The path pointing to the "internal" file consists of
        |IOSequence.dirpath_int| and |IOSequence.filename_int|, which
        itself is defined by `rawfilename`.  For simplicity, we define
        both manually in the following example:

        >>> from hydpy.core.sequencetools import StateSequence
        >>> seq = StateSequence(None)
        >>> seq.dirpath_int = "path"
        >>> seq.rawfilename = "file"
        >>> from hydpy import repr_
        >>> repr_(seq.filepath_int)
        'path/file.bin'
        """
        return os.path.join(self.dirpath_int, self.filename_int)

    def update_fastaccess(self) -> None:
        """Update the |FastAccessIOSequence| object handled by the actual
        |IOSequence| object.

        Users do not need to apply the method |IOSequence.update_fastaccess|
        directly.  The following information should be relevant for
        framework developers only.

        The main documentation on class |Sequence_| mentions that the
        |FastAccessIOSequence| attribute handles some information about
        its sequences, but this information needs to be kept up-to-date
        by the sequences themselves.  This updating is the task of method
        |IOSequence.update_fastaccess|, which some other methods of class
        |IOSequence| call.  We show this via the hidden attribute `length`,
        which is 0 after initialisation, and automatically set to another
        value when assigning it to property |IOSequence.shape| of
        |IOSequence| subclasses as |lland_fluxes.NKor|:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("lland_v1")
        >>> nkor = model.sequences.fluxes.nkor
        >>> nkor.fastaccess._nkor_length
        0
        >>> nkor.shape = (3,)
        >>> nkor.fastaccess._nkor_length
        3
        """
        path: Optional[str]
        if self.diskflag:
            path = self.filepath_int
        else:
            path = None
        self._set_fastaccessattribute("path", path)
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
            self._set_fastaccessattribute(f"length_{idx}", self.shape[idx])
        self._set_fastaccessattribute("length", length)

    def activate_ram(self) -> None:
        """Demand reading/writing internal data from/to RAM.

        See the main documentation on class |IOSequence| for further
        information.
        """
        self.deactivate_disk()
        self._set_fastaccessattribute("ramflag", True)
        self._activate()

    def activate_disk(self) -> None:
        """Demand reading/writing internal data from/to hard disk.

        See the main documentation on class |IOSequence| for further
        information.
        """
        self.deactivate_ram()
        self._set_fastaccessattribute("diskflag", True)
        self._activate()

    def _activate(self) -> None:
        values = numpy.full(self.seriesshape, numpy.nan, dtype=float)
        if self.ramflag:
            self.__set_array(values)
        else:
            self._save_int(values)
        self.update_fastaccess()

    def deactivate_ram(self) -> None:
        """Prevent from reading/writing internal data from/to hard disk.

        See the main documentation on class |IOSequence| for further
        information.
        """
        if self.ramflag:
            del self.series
            self._set_fastaccessattribute("ramflag", False)

    def deactivate_disk(self) -> None:
        """Prevent from reading/writing internal data from/to hard disk.

        See the main documentation on class |IOSequence| for further
        information.
        """
        if self.diskflag:
            del self.series
            self._set_fastaccessattribute("diskflag", False)

    def ram2disk(self) -> None:
        """Move internal data from RAM to disk.

        See the main documentation on class |IOSequence| for further
        information.
        """
        values = self.series
        self.deactivate_ram()
        self._set_fastaccessattribute("diskflag", True)
        self._save_int(values)
        self.update_fastaccess()

    def disk2ram(self) -> None:
        """Move internal data from disk to RAM.

        See the main documentation on class |IOSequence| for further
        information.
        """
        values = self.series
        self.deactivate_disk()
        self._set_fastaccessattribute("ramflag", True)
        self.__set_array(values)
        self.update_fastaccess()

    @property
    def ramflag(self) -> bool:
        """A flag telling if the actual |IOSequence| object makes
        its internal time-series data available using RAM space.

        See the main documentation on class |IOSequence| for further
        information.
        """
        return self._get_fastaccessattribute("ramflag")

    @property
    def diskflag(self) -> bool:
        """A flag telling if the actual |IOSequence| object makes
        its internal time-series data available using disk space.

        See the main documentation on class |IOSequence| for further
        information.
        """
        return self._get_fastaccessattribute("diskflag")

    @property
    def memoryflag(self) -> bool:
        """A flag telling if the actual |IOSequence| object makes
        its internal time-series data available somehow.

        See the main documentation on class |IOSequence| for further
        information.
        """
        return self.ramflag or self.diskflag

    def __set_array(self, values):
        values = numpy.array(values, dtype=float)
        self._set_fastaccessattribute("array", values)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        When setting a new |IOSequence.shape| of an |IOSequence| object,
        one automatically calls method |IOSequence.update_fastaccess|
        and, if necessary, prepares the new internal |IOSequence.series|
        array.

        See the main documentation on class |IOSequence| for further
        information.
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]):
        super().__hydpy__set_shape__(shape)
        if self.memoryflag:
            self._activate()
        else:
            self.update_fastaccess()

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)

    @property
    def seriesshape(self) -> Tuple[int, ...]:
        """The shape of the whole time-series (time being the first
        dimension)."""
        seriesshape = [len(hydpy.pub.timegrids.init)]
        seriesshape.extend(self.shape)
        return tuple(seriesshape)

    @property
    def numericshape(self) -> Tuple[int, ...]:
        """The shape of the array of temporary values required for the
        relevant numerical solver.

        The class |ELSModel|, being the base of the "dam" model, uses
        the "Explicit Lobatto Sequence" for solving differential equations
        and therefore requires up to eleven array fields for storing
        temporary values.  Hence, the |IOSequence.numericshape| of the
        0-dimensional sequence |dam_fluxes.Inflow| is eleven:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("dam")
        >>> model.sequences.fluxes.inflow.numericshape
        (11,)

        Changing the |IOSequence.shape| through a little trick (just for
        demonstration purposes) shows that there are eleven entries for
        each "normal" |dam_fluxes.Inflow| value:

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
        AttributeError: The `numericshape` of a sequence like `inflow` \
depends on the configuration of the actual integration algorithm.  \
While trying to query the required configuration data `nmb_stages` of \
the model associated with element `?`, the following error occurred: \
'Model' object has no attribute 'numconsts'
        """
        try:
            numericshape = [self.subseqs.seqs.model.numconsts.nmb_stages]
        except AttributeError:
            objecttools.augment_excmessage(
                f"The `numericshape` of a sequence like `{self.name}` depends "
                f"on the configuration of the actual integration algorithm.  "
                f"While trying to query the required configuration data "
                f"`nmb_stages` of the model associated with element "
                f"`{objecttools.devicename(self)}`"
            )
        numericshape.extend(self.shape)
        return tuple(numericshape)

    def _get_series(self) -> InfoArray:
        """Internal time-series data within an |InfoArray| covering the whole
        initialisation period (defined by the |Timegrids.sim| |Timegrid| of
        the global |Timegrids| object available in module |pub|)."""
        if self.diskflag:
            array = self._load_int()
        elif self.ramflag:
            array = numpy.asarray(self._get_fastaccessattribute("array"))
        else:
            raise AttributeError(
                f"Sequence {objecttools.devicephrase(self)} is not "
                f"requested to make any internal data available."
            )
        return InfoArray(array, info={"type": "unmodified"})

    def _set_series(self, values) -> None:
        series = numpy.full(self.seriesshape, values, dtype=float)
        if self.diskflag:
            self._save_int(series)
        elif self.ramflag:
            self.__set_array(series)
        else:
            raise AttributeError(
                f"Sequence {objecttools.devicephrase(self)} is not "
                f"requested to make any internal data available."
            )
        self.check_completeness()

    def _del_series(self) -> None:
        if self.diskflag:
            os.remove(self.filepath_int)
        elif self.ramflag:
            self._set_fastaccessattribute("array", None)

    series = property(_get_series, _set_series, _del_series)

    def _get_simseries(self) -> InfoArray:
        """Read and write access to the data of property |IOSequence.series| for
        the actual simulation period (defined by the |Timegrids.sim| |Timegrid|
        of the global |Timegrids| object available in module |pub|).

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
        """Read and write access to the data of property |IOSequence.series| for
        the actual evaluation period (defined by the |Timegrids.eval_| |Timegrid|
        of the global |Timegrids| object available in module |pub|).

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

    def load_ext(self) -> None:
        """Read the internal data from an external data file.

        Method |IOSequence.load_ext| only calls method
        |SequenceManager.load_file| of class |SequenceManager|
        passing itself as the only argument.  Hence, see the
        documentation on the class |SequenceManager| for further
        information.  The following example only shows the error
        messages when |SequenceManager.load_file| is missing
        due to incomplete project configurations:

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.sequencemanager

        >>> from hydpy.core.sequencetools import StateSequence
        >>> StateSequence(None).load_ext()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to load the \
external time-series data of `statesequence`, the following error occurred: \
Attribute sequencemanager of module `pub` is not defined at the moment.
        """
        try:
            sequencemanager = hydpy.pub.sequencemanager
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to load the external time-series "
                f"data of {objecttools.devicephrase(self)}"
            )
        sequencemanager.load_file(self)

    def adjust_series(
        self,
        timegrid_data: "timetools.Timegrid",
        values: numpy.ndarray,
    ) -> numpy.ndarray:
        """Adjust a time-series to the current initialisation period.

        Note that, in most *HydPy* applications, method
        |IOSequence.adjust_series| is called by other methods related
        to reading data from files and does not need to be called by
        the user directly.  If you want to call it directly for some
        reasons, you need to make sure that the shape of the given
        |numpy| |numpy.ndarray| fits the given |Timegrid| object.

        Often, time-series data available in (external) data files
        cover a longer period than required for an actual simulation
        run.  Method |IOSequence.adjust_series| selects the relevant
        data by comparing the initialisation |Timegrid| available in
        module |pub| and the given "data" |Timegrid| object.  We
        explain this behaviour by using the `LahnH` example project
        and focussing on the |Obs| sequence of |Node| `dill`:

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

        For "too long" available data, it only returns the relevant one:

        >>> with TestIO(), pub.options.checkseries(False):
        ...     obs.adjust_series(Timegrid("1995-12-31", "1996-01-07", "1d"),
        ...                       numpy.arange(7, dtype=float))
        array([1., 2., 3., 4.])

        For "too short" available data, the behaviour differs depending
        on option |Options.checkseries|.  With |Options.checkseries| being
        enabled, method |IOSequence.adjust_series| raises a |RuntimeError|.
        With |Options.checkseries| being disabled, it extends the given
        array with |numpy.nan| values (using method
        |IOSequence.adjust_short_series|):

        >>> with TestIO(), pub.options.checkseries(True):
        ...     obs.adjust_series(Timegrid("1996-01-02", "1996-01-04", "1d"),
        ...                       numpy.zeros((3,)))   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: For sequence `obs` of node `dill` the initialisation \
time grid (Timegrid("1996-01-01 00:00:00", "1996-01-05 00:00:00", "1d")) \
does not define a subset of the time grid of the external \
data file `...dill_obs_q.asc` \
(Timegrid("1996-01-02 00:00:00", "1996-01-04 00:00:00", "1d")).

        >>> with TestIO(), pub.options.checkseries(False):
        ...     obs.adjust_series(Timegrid("1996-01-02", "1996-01-04", "1d"),
        ...                       numpy.zeros((2,)))
        array([nan,  0.,  0., nan])

        Additional checks raise errors in case of non-matching shapes
        or time information:

        >>> with TestIO():
        ...     obs.adjust_series(Timegrid("1996-01-01", "1996-01-05", "1d"),
        ...                       numpy.zeros((5, 2)))   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The shape of sequence `obs` of node `dill` is `()` but \
according to the external data file `...dill_obs_q.asc` it should be `(2,)`.

        >>> with TestIO():
        ...     obs.adjust_series(Timegrid("1996-01-01", "1996-01-05", "1h"),
        ...                       numpy.zeros((24*5,)))   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: According to external data file `...dill_obs_q.asc`, \
the date time step of sequence `obs` of node `dill` is `1h` but the actual \
simulation time step is `1d`.

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        if self.shape != values.shape[1:]:
            raise RuntimeError(
                f"The shape of sequence {objecttools.devicephrase(self)} "
                f"is `{self.shape}` but according to the external data file "
                f"`{self.filepath_ext}` it should be `{values.shape[1:]}`."
            )
        if hydpy.pub.timegrids.init.stepsize != timegrid_data.stepsize:
            raise RuntimeError(
                f"According to external data file `{self.filepath_ext}`, "
                f"the date time step of sequence "
                f"{objecttools.devicephrase(self)} is "
                f"`{timegrid_data.stepsize}` but the actual simulation "
                f"time step is `{hydpy.pub.timegrids.init.stepsize}`."
            )
        if hydpy.pub.timegrids.init not in timegrid_data:
            if hydpy.pub.options.checkseries:
                raise RuntimeError(
                    f"For sequence {objecttools.devicephrase(self)} the "
                    f"initialisation time grid ({hydpy.pub.timegrids.init}) "
                    f"does not define a subset of the time grid of the "
                    f"external data file `{self.filepath_ext}` "
                    f"({timegrid_data})."
                )
            return self.adjust_short_series(timegrid_data, values)
        idx1 = timegrid_data[hydpy.pub.timegrids.init.firstdate]
        idx2 = timegrid_data[hydpy.pub.timegrids.init.lastdate]
        return values[idx1:idx2]

    def adjust_short_series(
        self,
        timegrid: "timetools.Timegrid",
        values: numpy.ndarray,
    ) -> numpy.ndarray:
        """Adjust a short time-series to a longer time grid.

        Mostly, time-series data to be read from external data files
        should span (at least) the whole initialisation period of a
        *HydPy* project.  However, for some variables which are only used
        for comparison (e.g. observed runoff used for calibration),
        incomplete time-series might also be helpful.  Method
        |IOSequence.adjust_short_series| adjusts such incomplete series
        to the public initialisation time grid stored in module |pub|.
        It is automatically called in method |IOSequence.adjust_series|
        when necessary provided that the option |Options.checkseries|
        is disabled.

        Assume the initialisation period of a HydPy project spans five days:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000.01.10", "2000.01.15", "1d"

        Prepare a node series object for observational data:

        >>> from hydpy.core.sequencetools import Obs
        >>> obs = Obs(None)

        Prepare a test function that expects the time grid of the
        data and the data itself, which returns the adjusted array
        through calling method |IOSequence.adjust_short_series|:

        >>> import numpy
        >>> def test(timegrid):
        ...     values = numpy.ones(len(timegrid))
        ...     return obs.adjust_short_series(timegrid, values)

        The following calls to the test function show the arrays
        returned for different kinds of misalignments:

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

        After enabling option |Options.usedefaultvalues|, the missing
        values are initialised with zero instead of nan:

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
        """Raise a |RuntimeError| if the |IOSequence.series| contains at
        least one |numpy.nan| value and if the option |Options.checkseries|
        is enabled.

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
        >>> seq.activate_ram()
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
                    f"The series array of sequence "
                    f"{objecttools.devicephrase(self)} contains "
                    f"{nmb} nan {valuestring}."
                )

    def save_ext(self) -> None:
        """Write the internal data into an external data file.

        Method |IOSequence.save_ext| only calls method
        |SequenceManager.save_file| of class |SequenceManager|
        passing itself as the only argument.  Hence, see the
        documentation on class the |SequenceManager| for further
        information.  The following example only shows the error
        messages when |SequenceManager.save_file| is missing
        due to incomplete project configurations:

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.sequencemanager

        >>> from hydpy.core.sequencetools import StateSequence
        >>> StateSequence(None).save_ext()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to save the \
external time-series data of `statesequence`, the following error occurred: \
Attribute sequencemanager of module `pub` is not defined at the moment.
        """
        try:
            sequencemanager = hydpy.pub.sequencemanager
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to save the external time-series "
                f"data of {objecttools.devicephrase(self)}"
            )
        sequencemanager.save_file(self)

    def save_mean(self, *args, **kwargs) -> None:
        """Average the time-series date with method |IOSequence.average_series|
        of class |IOSequence| and write the result to file using method
        |SequenceManager.save_file| of class |SequenceManager|.

        The main documentation on class |SequenceManager| provides some
        examples.
        """
        array = InfoArray(
            self.average_series(*args, **kwargs),
            info={"type": "mean", "args": args, "kwargs": kwargs},
        )
        hydpy.pub.sequencemanager.save_file(self, array=array)

    def _load_int(self) -> numpy.ndarray:
        """Load internal data from a file and return it."""
        values = numpy.fromfile(self.filepath_int)
        if self.NDIM > 0:
            values = values.reshape(self.seriesshape)
        return values

    def _save_int(self, values: numpy.ndarray) -> None:
        values.tofile(self.filepath_int)

    def average_series(self, *args, **kwargs) -> InfoArray:
        """Average the actual time-series of the |Variable| object for all
        time points.

        Method |IOSequence.average_series| works similarly as method
        |Variable.average_values| of class |Variable|, from which we
        borrow some examples. However, firstly, we have to prepare a
        |Timegrids| object to define the |IOSequence.series| length:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

        As shown for method |Variable.average_values|, for 0-dimensional
        |IOSequence| objects the result of method |IOSequence.average_series|
        equals |IOSequence.series| itself:

        >>> from hydpy.core.sequencetools import StateSequence, StateSequences
        >>> class SoilMoisture(StateSequence):
        ...     NDIM = 0
        ...     NUMERIC = False
        >>> class StateSequences(StateSequences):
        ...     CLASSES = (SoilMoisture,)
        >>> sm = SoilMoisture(StateSequences(None))
        >>> sm.__hydpy__connect_variable2subgroup__()
        >>> sm.activate_ram()
        >>> import numpy
        >>> sm.series = numpy.array([190.0, 200.0, 210.0])
        >>> sm.average_series()
        InfoArray([190., 200., 210.])

        For |IOSequence| objects with an increased dimensionality, we
        require a weighting parameter:

        >>> SoilMoisture.NDIM = 1
        >>> sm.shape = 3
        >>> sm.activate_ram()
        >>> sm.series = (
        ...     [190.0, 390.0, 490.0],
        ...     [200.0, 400.0, 500.0],
        ...     [210.0, 410.0, 510.0])
        >>> from hydpy.core.parametertools import Parameter
        >>> class Area(Parameter):
        ...     NDIM = 1
        ...     shape = (3,)
        ...     value = numpy.array([1.0, 1.0, 2.0])
        >>> area = Area(None)
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> sm.average_series()
        InfoArray([390., 400., 410.])

        The documentation on method |Variable.average_values| provides
        many examples of how to use different masks in different ways.
        Here, we only show the results of method |IOSequence.average_series|
        for a mask selecting the first two entries, for a mask selecting
        no entry at all, and for an ill-defined mask:

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
        nan

        >>> maskvalues = [True, True]
        >>> sm.average_series()
        Traceback (most recent call last):
        ...
        IndexError: While trying to calculate the mean value of the internal \
time-series of sequence `soilmoisture`, the following error occurred: \
While trying to access the value(s) of variable `area` with key \
`[ True  True]`, the following error occurred: \
boolean index did not match indexed array along dimension 0; \
dimension is 3 but corresponding boolean dimension is 2
        """
        try:
            if not self.NDIM:
                array = self.series
            else:
                mask = self.get_submask(*args, **kwargs)
                if numpy.any(mask):
                    weights = self.refweights[mask]
                    weights /= numpy.sum(weights)
                    series = self.series[:, mask]
                    axes = tuple(range(1, self.NDIM + 1))
                    array = numpy.sum(weights * series, axis=axes)
                else:
                    return numpy.nan
            return InfoArray(array, info={"type": "mean"})
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to calculate the mean value of the internal "
                f"time-series of sequence {objecttools.devicephrase(self)}"
            )

    def aggregate_series(self, *args, **kwargs) -> InfoArray:
        """Aggregate time-series data based on the actual
        |FluxSequence.aggregation_ext| attribute of |IOSequence|
        subclasses.

        We prepare some nodes and elements with the help of
        method |prepare_io_example_1| and select a 1-dimensional
        flux sequence of type |lland_fluxes.NKor| as an example:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> seq = elements.element3.model.sequences.fluxes.nkor

        If |FluxSequence.aggregation_ext| is `none`, the
        original time-series values are returned:

        >>> seq.aggregation_ext
        'none'
        >>> seq.aggregate_series()
        InfoArray([[24., 25., 26.],
                   [27., 28., 29.],
                   [30., 31., 32.],
                   [33., 34., 35.]])

        If |FluxSequence.aggregation_ext| is `mean`, method
        |IOSequence.aggregate_series| is called:

        >>> seq.aggregation_ext = "mean"
        >>> seq.aggregate_series()
        InfoArray([25., 28., 31., 34.])

        In case the state of the sequence is invalid:

        >>> seq.aggregation_ext = "nonexistent"
        >>> seq.aggregate_series()
        Traceback (most recent call last):
        ...
        RuntimeError: Unknown aggregation mode `nonexistent` for \
sequence `nkor` of element `element3`.

        The following technical test confirms the propr passing of
        all potential positional and keyword arguments

        >>> seq.aggregation_ext = "mean"
        >>> from unittest import mock
        >>> seq.average_series = mock.MagicMock()
        >>> _ = seq.aggregate_series(1, x=2)
        >>> seq.average_series.assert_called_with(1, x=2)
        """
        mode = self.aggregation_ext
        if mode == "none":
            return self.series
        if mode == "mean":
            return self.average_series(*args, **kwargs)
        raise RuntimeError(
            f"Unknown aggregation mode `{mode}` for "
            f"sequence {objecttools.devicephrase(self)}."
        )

    @property
    @abc.abstractmethod
    def descr_sequence(self) -> str:
        """Description of the |Sequence_| object and its context."""

    @property
    @abc.abstractmethod
    def descr_device(self) -> str:
        """Description of the |Device| object the |Sequence_| object
        belongs to."""


class ModelSequence(
    Sequence_[
        ModelSequencesType,
        variabletools.FastAccessType,
    ],
):
    """Base class for sequences to be handled by |Model| objects."""

    @property
    def descr_sequence(self) -> str:
        """Description of the |ModelSequence| object itself and the
        |SubSequences| group it belongs to.

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
        """Description of the |Element| object the |ModelSequence| object
        belongs to.

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


class ModelIOSequence(
    ModelSequence[
        ModelIOSequencesType,
        FastAccessIOSequenceType,
    ],
    IOSequence[
        ModelIOSequencesType,
        FastAccessIOSequenceType,
    ],
):
    """Base class for sequences with input/output functionalities
    to be handled by |Model| objects."""


class InputSequence(
    ModelIOSequence[
        InputSequences,
        FastAccessInputSequence,
    ],
):
    """Base class for input sequences of |Model| objects.

    |InputSequence| objects provide their master model with input data,
    which is possible in two ways: either by providing their individually
    managed data (usually read from file) or data shared with an input
    node (usually calculated by another model).  This flexibility allows,
    for example, to let application model |hland_v1| read already
    preprocessed precipitation time-series or to couple it with application
    model |conv_v001|, which interpolates precipitation during the
    simulation run.

    The second mechanism (coupling |InputSequence| objects with input nodes)
    is rather new, and we might adjust the relevant interfaces in the future.
    As soon as we finally settled things, we improve the following example
    and place it more prominently.  In short, it shows that working with
    both types of input data sources at the same time works well and that
    the different |Node.deploymode| options are supported:

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

    _CLS_FASTACCESS_PYTHON = FastAccessInputSequence

    filetype_ext = _FileType()
    dirpath_ext = _DirPathProperty()
    aggregation_ext = _AggregationProperty()
    overwrite_ext = _OverwriteProperty()

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._set_fastaccessattribute("inputflag", False)

    def set_pointer(self, double: pointerutils.Double) -> None:
        """Prepare a pointer referencing the given |Double| object.

        Method |InputSequence.set_pointer| should be of relevance for
        framework developers and eventually for some model developers
        only.
        """
        pdouble = pointerutils.PDouble(double)
        self.fastaccess.set_pointerinput(self.name, pdouble)
        self._set_fastaccessattribute("inputflag", True)

    @property
    def inputflag(self) -> bool:
        """A flag telling if the actual |InputSequence| object queries
        its data from an input node (|True|) or uses individually managed
        data, usually read from a data file (|False|).

        See the main documentation on class |InputSequence| for further
        information.
        """
        return self._get_fastaccessattribute("inputflag")


class OutputSequence(
    ModelIOSequence[
        OutputSequencesType,
        FastAccessOutputSequence,
    ],
):
    """Base class for |FactorSequence|, |FluxSequence| and |StateSequence|.

    |OutputSequence| subclasses implement an optional output mechanism.
    Generally, as all instances of |ModelSequence| subclasses, output
    sequences handle values calculated within a simulation time step.
    With an activated |OutputSequence.outputflag|, they also pass their
    internal values to an output node (see the documentation on class
    |Element|), which makes them accessible to other models.

    This output mechanism (coupling |OutputSequence| objects with output nodes)
    is rather new, and we might adjust the relevant interfaces in the future.
    Additionally, it works for 0-dimensional output sequences only so far.
    As soon as we finally settled things, we improve the following example
    and place it more prominently.  In short, it shows that everything works
    well for the different |Node.deploymode| options:

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

    _CLS_FASTACCESS_PYTHON = FastAccessOutputSequence

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._set_fastaccessattribute("outputflag", False)

    def set_pointer(self, double: pointerutils.Double) -> None:
        """Prepare a pointer referencing the given |Double| object.

        Method |OutputSequence.set_pointer| should be of relevance for
        framework developers and eventually for some model developers
        only.
        """
        pdouble = pointerutils.PDouble(double)
        self.fastaccess.set_pointeroutput(self.name, pdouble)
        self._set_fastaccessattribute("outputflag", True)

    @property
    def outputflag(self) -> bool:
        """A flag telling if the actual |OutputSequence| object passes its
        data to an output node (|True|) or not (|False|).

        See the main documentation on class |OutputSequence| for further
        information.
        """
        return self._get_fastaccessattribute("outputflag")


class DependentSequence(
    OutputSequence[
        OutputSequencesType,
    ],
):
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
        is |None| initially, as property |IOSequence.numericshape| is unknown.  Setting
        the |DependentSequence.shape| attribute of the respective |FactorSequence| or
        |FluxSequence| object (we select |wland_fluxes.EI| as an example) prepares all
        "fastaccess attributes" automatically:

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


class FactorSequence(
    DependentSequence[
        FactorSequences,
    ],
):
    """Base class for factor sequences of |Model| objects."""

    NUMERIC = False  # Changing this requires implementing the related functionalites
    # in modules `modeltools` and `modeltutils`.

    filetype_ext = _FileType()
    dirpath_ext = _DirPathProperty()
    aggregation_ext = _AggregationProperty()
    overwrite_ext = _OverwriteProperty()


class FluxSequence(
    DependentSequence[
        FluxSequences,
    ],
):
    """Base class for flux sequences of |Model| objects."""

    filetype_ext = _FileType()
    dirpath_ext = _DirPathProperty()
    aggregation_ext = _AggregationProperty()
    overwrite_ext = _OverwriteProperty()


class ConditionSequence(
    ModelSequence[
        ModelSequencesType,
        variabletools.FastAccessType,
    ],
):
    """Base class for |StateSequence| and |LogSequence|.

    Class |ConditionSequence| should not be subclassed by model
    developers directly.  Inherit from |StateSequence| or
    |LogSequence| instead.
    """

    _oldargs: Optional[Tuple[Any, ...]] = None

    def __call__(self, *args) -> None:
        """The prefered way to pass values to |Sequence_| instances within
        initial condition files."""
        super().__call__(*args)
        self.trim()
        self._oldargs = copy.deepcopy(args)

    def trim(self, lower=None, upper=None):
        """Apply |trim| of module |variabletools|."""
        variabletools.trim(self, lower, upper)

    def reset(self):
        """Reset the value of the actual |StateSequence| or |LogSequence|
        object to the last value defined by "calling" the object.

        We use the |lland_v2| application model, which handles sequences
        derived from |StateSequence| (taking |lland_states.Inzp| as an
        example) and from |LogSequence| (taking |lland_logs.WET0| as an
        example):

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
        wet0([[nan, nan]])

        Before "calling" the sequences, method |ConditionSequence.reset|
        does nothing:

        >>> inzp.values = 0.0
        >>> inzp.reset()
        >>> inzp
        inzp(0.0, 0.0)
        >>> wet0.values = 0.0
        >>> wet0.reset()
        >>> wet0
        wet0([[0.0, 0.0]])

        After "calling" the sequences, method |ConditionSequence.reset|
        reuses the respective arguments:

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
        wet0([[3.0, 3.0]])
        >>> wet0.reset()
        >>> wet0
        wet0([[1.0, 2.0]])
        """
        if self._oldargs:
            self(*self._oldargs)


class StateSequence(
    OutputSequence[
        StateSequences,
    ],
    ConditionSequence[
        StateSequences,
        FastAccessOutputSequence,
    ],
):
    """Base class for state sequences of |Model| objects.

    Each |StateSequence| object is capable in handling states at two
    different "time points": at the beginning of a simulation step via
    property |StateSequence.old| and the end of a simulation step
    via property |StateSequence.new|.  These properties are reflected
    by two different `fastaccess` attributes.  `fastaccess_new` is
    an alias for the standard `fastaccess` attribute storing the
    customary information. `fastaccess_old` is an additional feature
    for storing the supplemental information.

    We demonstrate the above explanations using state sequence
    |hland_states.SM| of base model |hland_v1| with a shape of two:

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

    The typical way to define state values, especially within condition
    files, is to "call" state sequence objects, which sets both the
    "old" and the "new" states to the given value(s):

    >>> sm(1.0)
    >>> sm.values
    array([1., 1.])
    >>> sm.new
    array([1., 1.])
    >>> sm.old
    array([1., 1.])

    Alternatively, one can assign values to property |StateSequence.new|
    or property |StateSequence.old| (note that using |StateSequence.new|
    is identical with using the |Variable.value| property):

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

    Assigning problematic values to property |StateSequence.old| results
    in very similar error messages as assigning problematic values to
    property |Variable.value|:

    >>> sm.old = 1.0, 2.0, 3.0
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the old value(s) of state sequence `sm`, \
the following error occurred: While trying to convert the value(s) \
`(1.0, 2.0, 3.0)` to a numpy ndarray with shape `(2,)` and type `float`, \
the following error occurred: could not broadcast input array from \
shape (3,) into shape (2,)

    Just for completeness:  Method |StateSequence.new2old| effectively
    takes the new values as old ones, but more efficiently than using
    the properties |StateSequence.new| and |StateSequence.old|,  as it
    used during simulation runs (in fact, the Python method
    |StateSequence.new2old| is usually replaced by model-specific,
    cythonized version when working in Cython mode):

    >>> sm.new2old()
    >>> sm.values
    array([2., 3.])
    >>> sm.new
    array([2., 3.])
    >>> sm.old
    array([2., 3.])
    """

    NOT_DEEPCOPYABLE_MEMBERS = ("subseqs", "fastaccess_old", "fastaccess_new")
    filetype_ext = _FileType()
    dirpath_ext = _DirPathProperty()
    aggregation_ext = _AggregationProperty()
    overwrite_ext = _OverwriteProperty()

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
        initially, as property |IOSequence.numericshape| is unknown.  Setting the
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
        """State(s) after calling a |Model| calculation method. (Alias
        for property |Variable.value|).

        Property |StateSequence.new| handles, in contrast to property
        |StateSequence.old|, the newly calculated state values during
        each simulation step.  It supports testing and debugging of
        individual |Model| methods but istypically irrelevant when
        scripting *HydPy* workflows.
        """
        return super().__hydpy__get_value__()

    @new.setter
    def new(self, value):
        super().__hydpy__set_value__(value)

    @property
    def old(self):
        """State(s) before calling a |Model| calculation method.

        Note the similarity to property |StateSequence.new|. However,
        property |StateSequence.old| references the initial states
        of the respective simulation step, which should not be changed
        by |Model| calculation methods.
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
        """Assign the |StateSequence.new| state values to the
        |StateSequence.old| values.

        See the main documentation on class |StateSequence| for further
        information.

        Note that method |StateSequence.new2old| is replaced by a
        model-specific, cythonized method when working in Cython mode.
        """
        if self.NDIM:
            self.old[:] = self.new[:]
        else:
            self.old = self.new


class LogSequence(
    ConditionSequence[
        LogSequences,
        variabletools.FastAccess,
    ],
):
    """Base class for logging sequences of |Model| objects.

    Class |LogSequence| serves similar purposes as class |StateSequence|,
    but is less strict in its assumptions.  While |StateSequence| objects
    always handle two states (the |StateSequence.old| and the
    |StateSequence.new| one), |LogSequence| objects are supposed to
    remember an arbitrary or sequence-specific number of values, which
    can be state values but for example also flux values.  A typical
    use case is to store "old" values of effective precipitation to
    calculate "new" values of direct discharge using the unit hydrograph
    concept in later simulation steps.

    It is up to the model developer to make sure that a |LogSequence|
    subclass has the right dimensionality and shape to store the required
    information.  By convention, the "memory" of each |LogSequence|
    should be placed on the first axis for non-scalar properties.

    As |StateSequence| objects, |LogSequence| objects store relevant
    information to start a new simulation run where another one has
    ended, and are thus written into and read from condition files.
    """

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess


class LogSequenceFixed(LogSequence):
    """Base class for log sequences with a fixed shape."""

    NDIM = 1
    SHAPE: int

    def _finalise_connections(self):
        self.shape = (self.SHAPE,)

    def __hydpy__get_shape__(self):
        """Parameter derived from |LogSequenceFixed| are generally initialised with a
        fixed shape.

        We take parameter |dam_logs.LoggedRequiredRemoteRelease| of base model |dam| as
        an example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedrequiredremoterelease.shape
        (1,)

        Trying to set a new shape results in the following exceptions:

        >>> logs.loggedrequiredremoterelease.shape = 2
        Traceback (most recent call last):
        ...
        AttributeError: The shape of parameter `loggedrequiredremoterelease` cannot \
be changed, but this was attempted for element `?`.

        See the documentation on property |Variable.shape| of class |Variable| for
        further information.
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape):
        if exceptiontools.attrready(self, "shape"):
            raise AttributeError(
                f"The shape of parameter `{self.name}` cannot be changed, but this "
                f"was attempted for element `{objecttools.devicename(self)}`."
            )
        super().__hydpy__set_shape__(shape)

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)


class AideSequence(
    ModelSequence[
        AideSequences,
        variabletools.FastAccess,
    ],
):
    """Base class for aide sequences of |Model| objects.

    Aide sequences store data that is of importance only temporarily but
    must be shared by different calculation methods of a |Model| object.
    """

    _CLS_FASTACCESS_PYTHON = variabletools.FastAccess


class LinkSequence(
    ModelSequence[
        LinkSequencesType,
        FastAccessLinkSequence,
    ],
):
    """Base class for link sequences of |Model| objects.

    |LinkSequence| objects do not handle values themselves.
    Instead, they point to the values handled |NodeSequence| objects,
    using the functionalities provided by the Cython module
    |pointerutils|.  Multiple |LinkSequence| objects of different
    application models can query and modify the same |NodeSequence|
    values, allowing different |Model| objects to share information
    and interact with each other.

    A note for developers: |LinkSequence| subclasses must be either
    0-dimensional or 1-dimensional.

    Users might encounter the following exception, which is a safety
    measure to --- as the error message suggests --- prevent from
    segmentation faults:

    >>> from hydpy.core.sequencetools import LinkSequence
    >>> seq = LinkSequence(None)
    >>> seq
    linksequence(?)
    >>> seq.value
    Traceback (most recent call last):
    ...
    AttributeError: While trying to query the value(s) of link sequence \
`linksequence` of element `?`, the following error occurred: \
Proper connections are missing (which could result in segmentation faults \
when using it, so please be careful).
    """

    _CLS_FASTACCESS_PYTHON = FastAccessLinkSequence

    __isready: bool = False

    def set_pointer(self, double: pointerutils.Double, idx: int = 0) -> None:
        """Prepare a pointer referencing the given |Double| object.

        For 1-dimensional sequence objects, one also needs to specify
        the relevant index position of the pointer via argument `idx`.

        Method |LinkSequence.set_pointer| should be of relevance for
        framework developers and eventually for some model developers
        only.
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

        Changing a |LinkSequence.value| of a |LinkSequence| object seems
        very much like changing a |LinkSequence.value| of any other
        |Variable| object.  However, be aware that you are changing a
        value that is handled by a |NodeSequence| object.  We demonstrate
        this by using the `LahnH` example project through invoking
        function |prepare_full_example_2|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        We focus on the |hstream_v1| application model `stream_lahn_1_lahn_2`
        routing inflow from node `lahn_1` to node `lahn_2`:

        >>> model = hp.elements.stream_lahn_1_lahn_2.model

        The first example shows that the 0-dimensional outlet sequence
        |hstream_outlets.Q| points to the |Sim| sequence of node `lahn_2`:

        >>> model.sequences.outlets.q
        q(0.0)
        >>> hp.nodes.lahn_2.sequences.sim = 1.0
        >>> model.sequences.outlets.q
        q(1.0)
        >>> model.sequences.outlets.q(2.0)
        >>> hp.nodes.lahn_2.sequences.sim
        sim(2.0)

        The second example shows that the 1-dimensional inlet sequence
        |hstream_inlets.Q| points to the |Sim| sequence of node `lahn_1`:

        >>> model.sequences.inlets.q
        q(0.0)
        >>> hp.nodes.lahn_1.sequences.sim = 1.0
        >>> model.sequences.inlets.q
        q(1.0)
        >>> model.sequences.inlets.q(2.0)
        >>> hp.nodes.lahn_1.sequences.sim
        sim(2.0)

        Direct querying the values of both link sequences shows that the
        value of the 0-dimensional outlet sequence is scalar, of course,
        and that the value of the 1-dimensional inlet sequence is one
        entry of a vector:

        >>> model.sequences.outlets.q.value
        2.0
        >>> model.sequences.inlets.q.values
        array([2.])

        Assigning bad data results in the standard error messages:

        >>> model.sequences.outlets.q.value = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to assign the value(s) (1.0, 2.0) to link \
sequence `q` of element `stream_lahn_1_lahn_2`, the following error occurred: \
2 values are assigned to the scalar variable `q` of element \
`stream_lahn_1_lahn_2`.
        >>> model.sequences.inlets.q.values = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to assign the value(s) (1.0, 2.0) to link \
sequence `q` of element `stream_lahn_1_lahn_2`, the following error occurred: \
While trying to convert the value(s) `(1.0, 2.0)` to a numpy ndarray with \
shape `(1,)` and type `float`, the following error occurred: could not \
broadcast input array from shape (2,) into shape (1,)

        In the example above, the 1-dimensional inlet sequence
        |hstream_inlets.Q| points to the value of a single |NodeSequence|
        value only.  We now prepare a |hbranch_v1| application model
        instance to show what happens when connecting a 1-dimensional
        |LinkSequence| object (|hbranch_outlets.Branched|) with three
        |NodeSequence| objects (see the documentation of application
        model |hbranch_v1| for more details):

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

        Our third example demonstrates that each field of the values of a
        1-dimensional |LinkSequence| objects points to another |NodeSequence|
        object:

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
                    "Proper connections are missing (which could "
                    "result in segmentation faults when using it, "
                    "so please be careful)."
                )
            return self.fastaccess.get_value(self.name)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to query the value(s) of link "
                f"sequence {objecttools.elementphrase(self)}"
            )

    def __hydpy__set_value__(self, value):
        try:
            self.fastaccess.set_value(
                self.name,
                self._prepare_setvalue(value),
            )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to assign the value(s) {value} to "
                f"link sequence {objecttools.elementphrase(self)}"
            )

    value = property(fget=__hydpy__get_value__, fset=__hydpy__set_value__)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        Property |LinkSequence.shape| of class |LinkSequence| works
        similarly as the general |Variable.shape| property of class
        |Variable| but you need to be extra careful due to the pointer
        mechanism underlying class |LinkSequence|.  Change the shape
        of a link sequence for good reasons only.  Please read the
        documentation on property |LinkSequence.value| first and then
        see the following examples which are, again, based on the
        `LahnH` example project and application model |hstream_v1|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> model = hp.elements.stream_lahn_1_lahn_2.model

        The default mechanisms of *HydPy* prepare both 0-dimensional
        and 1-dimensional link sequences with a proper shape (which,
        for inlet sequence |hstream_inlets.Q|, depends on the number
        of connected |Node| objects):

        >>> model.sequences.outlets.q.shape
        ()
        >>> model.sequences.inlets.q.shape
        (1,)

        Trying to set the only possible shape of 0-dimensional link
        sequences or to set any different shape results in the
        standard behaviour:

        >>> model.sequences.outlets.q.shape = ()
        >>> model.sequences.outlets.q.shape = (1,)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the shape of link sequence`q` \
of element `stream_lahn_1_lahn_2`, the following error occurred: \
The shape information of 0-dimensional variables as `q` of element \
`stream_lahn_1_lahn_2` can only be `()`, but `(1,)` is given.

        Changing the shape of 1-dimensional link sequences is supported
        but results in losing the connection to the |NodeSequence| values
        of the respective nodes.  The following exception is raised to
        prevent segmentation faults until proper connections are available:

        >>> model.sequences.inlets.q.shape = (2,)
        >>> model.sequences.inlets.q.shape
        (2,)
        >>> model.sequences.inlets.q.shape = 1
        >>> model.sequences.inlets.q.shape
        (1,)
        >>> model.sequences.inlets.q
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to query the value(s) of link sequence \
`q` of element `stream_lahn_1_lahn_2`, the following error occurred: \
The pointer of the actual `PPDouble` instance at index `0` requested, \
but not prepared yet via `set_pointer`.

        >>> model.sequences.inlets.q(1.0)
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to assign the value(s) 1.0 to link \
sequence `q` of element `stream_lahn_1_lahn_2`, the following error occurred: \
The pointer of the actual `PPDouble` instance at index `0` requested, \
but not prepared yet via `set_pointer`.

        Querying the shape of a link sequence should rarely result in
        errors.  However, if we enforce it by deleting the `fastaccess`
        attribute, we get an error message like the following:

        >>> del model.sequences.inlets.q.fastaccess
        >>> model.sequences.inlets.q.shape
        Traceback (most recent call last):
        ...
        AttributeError: While trying to query the shape of link sequence`q` \
of element `stream_lahn_1_lahn_2`, the following error occurred: \
'Q' object has no attribute 'fastaccess'

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


class InletSequence(
    LinkSequence[
        InletSequences,
    ],
):
    """Base class for inlet link sequences of |Model| objects."""


class OutletSequence(
    LinkSequence[
        OutletSequences,
    ],
):
    """Base class for outlet link sequences of |Model| objects."""


class ReceiverSequence(
    LinkSequence[
        ReceiverSequences,
    ],
):
    """Base class for receiver link sequences of |Model| objects."""


class SenderSequence(
    LinkSequence[
        SenderSequences,
    ],
):
    """Base class for sender link sequences of |Model| objects."""


class NodeSequence(
    IOSequence[
        "NodeSequences",
        FastAccessNodeSequence,
    ],
):
    """Base class for all sequences to be handled by |Node| objects."""

    NDIM: int = 0
    NUMERIC: bool = False

    _CLS_FASTACCESS_PYTHON = FastAccessNodeSequence

    filetype_ext = _FileType()
    dirpath_ext = _DirPathProperty()
    aggregation_ext = _AggregationProperty()
    overwrite_ext = _OverwriteProperty()

    @property
    def initinfo(self) -> Tuple[pointerutils.Double, bool]:
        """Return a |Double| instead of a |float| object as the first tuple
        entry."""
        if hydpy.pub.options.usedefaultvalues:
            return pointerutils.Double(0.0), True
        return pointerutils.Double(numpy.nan), False

    @property
    def descr_sequence(self) -> str:
        """Description of the |NodeSequence| object including the
        |Node.variable| to be represented.

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
        """Description of the |Node| object the |NodeSequence| object
        belongs to.

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

    def __hydpy__get_value__(self):
        """The actual sequence value.

        For framework users, property |NodeSequence.value| of class
        |NodeSequence| works as usual and explained in the documentation
        on property |Variable.shape| of class |Variable|.  However,
        framework developers should note that |NodeSequence| objects use
        |Double| objects for storing their values and making them
        accessible to |PDouble| and |PPDouble| objects as explained
        in detail in the documentation on class |LinkSequence|.
        For safety reasons, this mechanism is hidden for framework
        users via conversions to type |float|:

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

        Node sequences return errors like the following in case they
        receive misspecified values or ill-configured:

        >>> sim.value = 1.0, 2.0
        Traceback (most recent call last):
        ...
        TypeError: While trying to assign the value `(1.0, 2.0)` to \
sequence `sim` of node `node`, the following error occurred: \
float() argument must be a string or a number, not 'tuple'

        >>> del sim.fastaccess
        >>> sim.value
        Traceback (most recent call last):
        ...
        AttributeError: While trying to query the value of sequence `sim` \
of node `node`, the following error occurred: \
'Sim' object has no attribute 'fastaccess'

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
                f"While trying to assign the value `{value}` to "
                f"sequence {objecttools.nodephrase(self)}"
            )

    value = property(fget=__hydpy__get_value__, fset=__hydpy__set_value__)

    @property
    def seriescomplete(self) -> bool:
        """True/False flag indicating whether simulated or observed data
        is fully available or not.

        We use the observation series of node `dill` of the `LahnH`
        project as an example:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> obs = hp.nodes.dill.sequences.obs

        When the sequence does not handle any time-series data,
        |NodeSequence.seriescomplete| is |False|:

        >>> obs.deactivate_ram()
        >>> obs.series
        Traceback (most recent call last):
        ...
        AttributeError: Sequence `obs` of node `dill` is not requested \
to make any internal data available.
        >>> obs.seriescomplete
        False

        As long as any time-series data is missing,
        |NodeSequence.seriescomplete| is still |False|:

        >>> obs.activate_ram()
        >>> obs.series[:-1] = 1.0
        >>> obs.series
        InfoArray([ 1.,  1.,  1., nan])
        >>> obs.seriescomplete
        False

        Only with all data being not |numpy.nan|,
        |NodeSequence.seriescomplete| is |True|:

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
    """Class for handling those values of |Node| objects that are "simulated",
    meaning calculated by hydrological models."""

    def load_ext(self) -> None:
        """Read time-series data like method |IOSequence.load_ext| of class
        |IOSequence| but with special handling of missing data.

        The method's "special handling" is to convert errors to warnings.
        We explain the reasons in the documentation on method |Obs.load_ext|
        of class |Obs|, from which we borrow the following examples.
        The only differences are that method |Sim.load_ext| of class |Sim|
        does not disable property |IOSequence.memoryflag| and uses the option
        |Options.warnmissingsimfile| instead of |Options.warnmissingobsfile|:

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
        ...     sim.load_ext()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        UserWarning: While trying to load the external data of sequence \
`sim` of node `dill`, the following error occurred: [Errno 2] No such file \
or directory: '...dill_sim_q.asc'
        >>> sim.series
        InfoArray([nan, nan, nan, nan, nan])

        >>> sim.series = 1.0
        >>> with TestIO():
        ...     sim.save_ext()
        >>> sim.series = 0.0
        >>> with TestIO():
        ...     sim.load_ext()
        >>> sim.series
        InfoArray([1., 1., 1., 1., 1.])

        >>> import numpy
        >>> sim.series[2] = numpy.nan
        >>> with TestIO():
        ...     pub.sequencemanager.nodeoverwrite = True
        ...     sim.save_ext()
        >>> with TestIO():
        ...     sim.load_ext()
        Traceback (most recent call last):
        ...
        UserWarning: While trying to load the external data of sequence `sim` \
of node `dill`, the following error occurred: The series array of sequence \
`sim` of node `dill` contains 1 nan value.
        >>> sim.series
        InfoArray([ 1.,  1., nan,  1.,  1.])

        >>> sim.series = 0.0
        >>> with TestIO():
        ...     with pub.options.warnmissingsimfile(False):
        ...         sim.load_ext()
        >>> sim.series
        InfoArray([ 1.,  1., nan,  1.,  1.])

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        try:
            super().load_ext()
        except BaseException:
            if hydpy.pub.options.warnmissingsimfile:
                warnings.warn(str(sys.exc_info()[1]))


class Obs(NodeSequence):
    """Class for handling those values of |Node| objects that are observed,
    meaning read from data files."""

    def load_ext(self) -> None:
        """Read time-series data like method |IOSequence.load_ext| of class
        |IOSequence| but with special handling of missing data.

        When reading incomplete time-series data, *HydPy* usually raises
        a |RuntimeError| to prevent from performing erroneous calculations.
        For instance, this makes sense for meteorological input data, being
        a strict requirement for hydrological simulations.  However, the
        same often does not hold for the time-series of |Obs| sequences,
        e.g. representing measured discharge. Measured discharge is often
        handled as an optional input value, or even used for comparison
        purposes only.

        According to this reasoning, *HydPy* raises (at most) a |UserWarning|
        in case of missing or incomplete external time-series data of |Obs|
        sequences.  The following examples show this based on the `LahnH`
        project, mainly focussing on the |Obs| sequence of node `dill`,
        which is ready for handling time-series data at the end of the
        following steps:

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

        Trying to read non-existing data raises the following warning
        and disables the sequence's ability to handle time-series data:

        >>> with TestIO():
        ...     hp.load_obsseries()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        UserWarning: The `memory flag` of sequence `obs` of node `dill` had \
to be set to `False` due to the following problem: While trying to load the \
external data of sequence `obs` of node `dill`, the following error occurred: \
[Errno 2] No such file or directory: '...dill_obs_q.asc'
        >>> obs.ramflag
        False

        After writing a complete external data file, everything works fine:

        >>> obs.activate_ram()
        >>> obs.series = 1.0
        >>> with TestIO():
        ...     obs.save_ext()
        >>> obs.series = 0.0
        >>> with TestIO():
        ...     obs.load_ext()
        >>> obs.series
        InfoArray([1., 1., 1., 1., 1.])

        Reading incomplete data also results in a warning message, but does
        not disable the |IOSequence.memoryflag|:

        >>> import numpy
        >>> obs.series[2] = numpy.nan
        >>> with TestIO():
        ...     pub.sequencemanager.nodeoverwrite = True
        ...     obs.save_ext()
        >>> with TestIO():
        ...     obs.load_ext()
        Traceback (most recent call last):
        ...
        UserWarning: While trying to load the external data of sequence `obs` \
of node `dill`, the following error occurred: The series array of sequence \
`obs` of node `dill` contains 1 nan value.
        >>> obs.memoryflag
        True

        Option |Options.warnmissingobsfile| allows disabling the warning
        messages without altering the functionalities described above:

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
            super().load_ext()
        except OSError:
            self._set_fastaccessattribute("ramflag", False)
            self._set_fastaccessattribute("diskflag", False)
            if hydpy.pub.options.warnmissingobsfile:
                warnings.warn(
                    f"The `memory flag` of sequence "
                    f"{objecttools.nodephrase(self)} had to be set to `False` "
                    f"due to the following problem: {sys.exc_info()[1]}"
                )
        except BaseException:
            if hydpy.pub.options.warnmissingobsfile:
                warnings.warn(str(sys.exc_info()[1]))


class NodeSequences(
    IOSequences[
        "devicetools.Node",
        NodeSequence,
        FastAccessNodeSequence,
    ]
):
    """Base class for handling |Sim| and |Obs| sequence objects.

    Basically, |NodeSequences| works like the different |ModelSequences|
    subclasses used for handling |ModelSequence| objects.  The main
    difference is that they do not reference a |Sequences| object (which
    is only handled by |Element| objects but not by |Node| objects).
    Instead, they reference their master |Node| object via the attribute
    `node` directly:

    >>> from hydpy import Node
    >>> node = Node("node")
    >>> node.sequences.node
    Node("node", variable="Q")

    The implemented methods just call the same method of the underlying
    `fastaccess` attribute, which is an instance of (a Cython extension
    class of) the Python class |sequencetools.FastAccessNodeSequence|.

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
        master: "devicetools.Node",
        cls_fastaccess: Optional[Type[FastAccessNodeSequence]] = None,
        cymodel: Optional[CyModelProtocol] = None,
    ) -> None:
        self.node = master
        self._cls_fastaccess = cls_fastaccess
        self._cymodel = cymodel
        super().__init__(master)

    def __hydpy__initialise_fastaccess__(self) -> None:
        if hydpy.pub.options.usecython:
            self.fastaccess = sequenceutils.FastAccessNodeSequence()
        else:
            self.fastaccess = self._CLS_FASTACCESS_PYTHON()

    def load_data(self, idx: int) -> None:
        """Call method |sequencetools.FastAccessNodeSequence.load_data|
        of the current `fastaccess` attribute.

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
        """Call method |sequencetools.FastAccessNodeSequence.load_simdata|
        of the current `fastaccess` attribute.

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
        """Call method |sequencetools.FastAccessNodeSequence.load_obsdata|
        of the current `fastaccess` attribute.

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
        """Call method |sequencetools.FastAccessNodeSequence.save_data|
        of the current `fastaccess` attribute.

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
        """Call method |sequencetools.FastAccessNodeSequence.save_simdata|
        of the current `fastaccess` attribute.

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
