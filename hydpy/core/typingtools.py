"""This module implements some "types" to be used for static (and eventually dynamical)
typing."""

from __future__ import annotations
from collections.abc import (
    Callable,
    Collection,
    Generator,
    Hashable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Sized,
    Sequence,
    ValuesView,
)
from contextlib import AbstractContextManager
from typing import (
    Any,
    cast,
    ClassVar,
    Concatenate,
    Final,
    Generic,
    get_type_hints,
    Literal,
    NamedTuple,
    NewType,
    NoReturn,
    Optional,
    overload,
    Protocol,
    TextIO,
    TypeAlias,
    TypedDict,
    TypeVar,
    TYPE_CHECKING,
    Union,
)
from typing_extensions import assert_never, Never, ParamSpec, Self, Unpack

import numpy
from numpy.typing import NDArray

if TYPE_CHECKING:
    from hydpy.core import modeltools
    from hydpy.core import parametertools

T_inv = TypeVar("T_inv")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

P_ = ParamSpec("P_")

Name = NewType("Name", str)
Name.__doc__ = """Type for strings that represent names."""


Mayberable1: TypeAlias = Union[T_inv, Iterable[T_inv]]
Mayberable2: TypeAlias = Union[T1, T2, Iterable[T1 | T2]]
Mayberable3: TypeAlias = Union[T1, T2, T3, Iterable[T1 | T2 | T3]]
MayNonerable1: TypeAlias = Optional[Union[T_inv, Iterable[T_inv]]]
MayNonerable2: TypeAlias = Optional[Union[T1, T2, Iterable[T1 | T2]]]
MayNonerable3: TypeAlias = Optional[Union[T1, T2, T3, Iterable[T1 | T2 | T3]]]

Collection1: TypeAlias = Union[T_inv, Collection[T_inv]]
Collection2: TypeAlias = Union[T1, T2, Collection[T1 | T2]]
Collection3: TypeAlias = Union[T1, T2, T3, Collection[T1 | T2 | T3]]

Sequence1: TypeAlias = Union[T_inv, Sequence[T_inv]]
Sequence2: TypeAlias = Union[T1, T2, Sequence[T1 | T2]]
Sequence3: TypeAlias = Union[T1, T2, T3, Sequence[T1 | T2 | T3]]

Float = TypeVar("Float", bound=float)

Scalar = TypeVar(
    "Scalar",
    numpy.dtype[numpy.float64],
    numpy.dtype[numpy.int64],
    numpy.dtype[numpy.bool_],
    numpy.dtype[numpy.generic],
    numpy.dtype[numpy.bytes_],
)

NDVector: TypeAlias = numpy.ndarray[tuple[int], Scalar]
NDMatrix: TypeAlias = numpy.ndarray[tuple[int, int], Scalar]
NDTensor: TypeAlias = numpy.ndarray[tuple[int, int, int], Scalar]

NDArrayObject: TypeAlias = NDArray[numpy.generic]
NDArrayFloat: TypeAlias = NDArray[numpy.float64]
NDArrayInt: TypeAlias = NDArray[numpy.int64]
NDArrayBool: TypeAlias = NDArray[numpy.bool_]

ScalarInputFloat: TypeAlias = Union[
    float, numpy.floating[Any], numpy.integer[Any], numpy.bool_
]
ScalarInputInt: TypeAlias = Union[int, numpy.integer[Any], numpy.bool_]
ScalarInputBool: TypeAlias = Union[bool, numpy.bool_]
_DTypeInputFloat: TypeAlias = numpy.dtype[
    numpy.floating[Any] | numpy.integer[Any] | numpy.bool_
]
_DTypeInputInt: TypeAlias = numpy.dtype[numpy.integer[Any] | numpy.bool_]
_DTypeInputBool: TypeAlias = numpy.dtype[numpy.bool_]

Vector: TypeAlias = NDVector[T_inv]
VectorObject: TypeAlias = NDVector[numpy.dtype[numpy.generic]]
VectorFloat: TypeAlias = NDVector[numpy.dtype[numpy.float64]]
VectorInt: TypeAlias = NDVector[numpy.dtype[numpy.int64]]
VectorBool: TypeAlias = NDVector[numpy.dtype[numpy.bool_]]
VectorInput: TypeAlias = Union[Sequence[T_inv], Vector[T_inv]]
VectorInputObject: TypeAlias = Union[Sequence[object], VectorObject]
VectorInputFloat: TypeAlias = Union[
    Sequence[ScalarInputFloat], numpy.ndarray[tuple[int], _DTypeInputFloat]
]
VectorInputInt: TypeAlias = Union[
    Sequence[ScalarInputInt], numpy.ndarray[tuple[int], _DTypeInputInt]
]
VectorInputBool: TypeAlias = Union[
    Sequence[ScalarInputBool], numpy.ndarray[tuple[int], _DTypeInputBool]
]
VectorInputCompleteObject: TypeAlias = Union[object, VectorInputObject]
VectorInputCompleteFloat: TypeAlias = Union[ScalarInputFloat, VectorInputFloat]
VectorInputCompleteInt: TypeAlias = Union[ScalarInputInt, VectorInputInt]
VectorInputCompleteBool: TypeAlias = Union[ScalarInputBool, VectorInputBool]

Matrix: TypeAlias = NDMatrix[T_inv]
MatrixObject: TypeAlias = NDMatrix[numpy.dtype[numpy.generic]]
MatrixFloat: TypeAlias = NDMatrix[numpy.dtype[numpy.float64]]
MatrixInt: TypeAlias = NDMatrix[numpy.dtype[numpy.int64]]
MatrixBool: TypeAlias = NDMatrix[numpy.dtype[numpy.bool_]]
MatrixBytes: TypeAlias = NDMatrix[numpy.dtype[numpy.bytes_]]
MatrixInput: TypeAlias = Union[Sequence[Sequence[T_inv]], Matrix[T_inv]]
MatrixInputObject: TypeAlias = Union[Sequence[VectorInputObject], MatrixObject]
MatrixInputFloat: TypeAlias = Union[
    Sequence[VectorInputFloat], numpy.ndarray[tuple[int, int], _DTypeInputFloat]
]
MatrixInputInt: TypeAlias = Union[
    Sequence[VectorInputInt], numpy.ndarray[tuple[int, int], _DTypeInputInt]
]
MatrixInputBool: TypeAlias = Union[
    Sequence[VectorInputBool], numpy.ndarray[tuple[int, int], _DTypeInputBool]
]
MatrixInputCompleteObject: TypeAlias = Union[object, MatrixInputObject]
MatrixInputCompleteFloat: TypeAlias = Union[ScalarInputFloat, MatrixInputFloat]
MatrixInputCompleteInt: TypeAlias = Union[ScalarInputInt, MatrixInputInt]
MatrixInputCompleteBool: TypeAlias = Union[ScalarInputBool, MatrixInputBool]

Tensor: TypeAlias = NDTensor[T_inv]
TensorObject: TypeAlias = NDTensor[numpy.dtype[numpy.generic]]
TensorFloat: TypeAlias = NDTensor[numpy.dtype[numpy.float64]]
TensorInt: TypeAlias = NDTensor[numpy.dtype[numpy.int64]]
TensorBool: TypeAlias = NDTensor[numpy.dtype[numpy.bool_]]
TensorInput: TypeAlias = Union[Sequence[Sequence[Sequence[T_inv]]], Tensor[T_inv]]
TensorInputObject: TypeAlias = Union[Sequence[MatrixInputObject], TensorObject]
TensorInputFloat: TypeAlias = Union[
    Sequence[MatrixInputFloat], numpy.ndarray[tuple[int, int, int], _DTypeInputFloat]
]
TensorInputInt: TypeAlias = Union[
    Sequence[MatrixInputInt], numpy.ndarray[tuple[int, int, int], _DTypeInputInt]
]
TensorInputBool: TypeAlias = Union[
    Sequence[MatrixInputBool], numpy.ndarray[tuple[int, int, int], _DTypeInputBool]
]
TensorInputCompleteObject: TypeAlias = Union[object, TensorInputObject]
TensorInputCompleteFloat: TypeAlias = Union[ScalarInputFloat, TensorInputFloat]
TensorInputCompleteInt: TypeAlias = Union[ScalarInputInt, TensorInputInt]
TensorInputCompleteBool: TypeAlias = Union[ScalarInputBool, TensorInputBool]

NestedFloat: TypeAlias = Union[
    ScalarInputFloat, NDArrayFloat, Mapping[str, "NestedFloat"], Sequence["NestedFloat"]
]

ArrayFloat = TypeVar("ArrayFloat", float, VectorFloat, MatrixFloat, TensorFloat)
ArrayFloatFlex = TypeVar(
    "ArrayFloatFlex",
    float,
    VectorFloat,
    MatrixFloat,
    TensorFloat,
    Union[float, VectorFloat],
    Union[float, MatrixFloat],
    Union[float, TensorFloat],
)
VectorFloatFlex = TypeVar("VectorFloatFlex", float, VectorFloat)

TM_co = TypeVar("TM_co", bound="modeltools.Model", covariant=True)
TOM_co = TypeVar("TOM_co", bound="modeltools.Model | None", covariant=True)
TG_co = TypeVar("TG_co", bound=str, covariant=True)  # G -> sequence group

ConditionValue: TypeAlias = float | NDArrayFloat


class FastAccessVector(Protocol[T_inv]):
    """A 1-dimensional array handled by a `fastaccess` object.

    HydPy's Mypy plugin applies this protocol to all 1-dimensional variables.  In
    contrast to Numpy's type stubs, indexing with an integer returns a scalar of the
    array's value type.
    """

    def __getitem__(self, index: int, /) -> T_inv: ...

    def __setitem__(self, index: int, value: T_inv, /) -> None: ...

    def __len__(self) -> int: ...


class FastAccessMatrix(Protocol[T_inv]):
    """A 2-dimensional array handled by a `fastaccess` object.

    HydPy's Mypy plugin applies this protocol to all 2-dimensional variables.  In
    contrast to Numpy's type stubs, indexing with a tuple of two integers returns a
    scalar of the array's value type, and indexing with a single integer returns a
    |FastAccessVector|.
    """

    @overload
    def __getitem__(self, index: tuple[int, int], /) -> T_inv: ...

    @overload
    def __getitem__(self, index: int, /) -> FastAccessVector[T_inv]: ...

    def __getitem__(
        self, index: tuple[int, int] | int, /
    ) -> T_inv | FastAccessVector[T_inv]: ...

    @overload
    def __setitem__(self, index: tuple[int, int], value: T_inv, /) -> None: ...

    @overload
    def __setitem__(self, index: int, value: FastAccessVector[T_inv], /) -> None: ...

    def __setitem__(
        self, index: tuple[int, int] | int, value: T_inv | FastAccessVector[T_inv], /
    ) -> None: ...

    def __len__(self) -> int: ...


class FastAccessTensor(Protocol[T_inv]):
    """A 3-dimensional array handled by a `fastaccess` object or a Cython extension
    class.

    Indexing with a tuple of three integers returns a scalar of the array's value type,
    and indexing with a single integer returns a |FastAccessMatrix|.
    """

    @overload
    def __getitem__(self, index: tuple[int, int, int], /) -> T_inv: ...

    @overload
    def __getitem__(self, index: int, /) -> FastAccessMatrix[T_inv]: ...

    def __getitem__(
        self, index: tuple[int, int, int] | int, /
    ) -> T_inv | FastAccessMatrix[T_inv]: ...

    @overload
    def __setitem__(self, index: tuple[int, int, int], value: T_inv, /) -> None: ...

    @overload
    def __setitem__(self, index: int, value: FastAccessMatrix[T_inv], /) -> None: ...

    def __setitem__(
        self,
        index: tuple[int, int, int] | int,
        value: T_inv | FastAccessMatrix[T_inv],
        /,
    ) -> None: ...

    def __len__(self) -> int: ...


class ConditionsGroup(Protocol[TM_co, TG_co]):
    """The values of all condition sequences of a specific group (e.g. `states`) of a
    specific model instance, accessible via the sequences' names.

    The type parameters (the model type and the group name) only serve to allow HydPy's
    Mypy plugin to determine the actual type of each condition value.
    """

    def __getitem__(self, key: str, /) -> ConditionValue: ...

    def __setitem__(self, key: str, value: ConditionValue, /) -> None: ...

    def __iter__(self) -> Iterator[str]: ...

    def __len__(self) -> int: ...

    def __contains__(self, key: object, /) -> bool: ...

    def keys(self) -> KeysView[str]:
        """Return the names of all entries."""

    def values(self) -> ValuesView[ConditionValue]:
        """Return all entries."""

    def items(self) -> ItemsView[str, ConditionValue]:
        """Return all (name, entry) pairs."""


class ConditionsSubmodel(Protocol[TM_co]):
    """The values of all condition sequences of a specific model instance, accessible
    via the sequence groups' names (e.g. `states`).

    The type parameter (the model type) only serves to allow HydPy's Mypy plugin to
    determine the actual type of each condition value.
    """

    def __getitem__(self, key: str, /) -> ConditionsGroup[TM_co, str]: ...

    def __iter__(self) -> Iterator[str]: ...

    def __len__(self) -> int: ...

    def __contains__(self, key: object, /) -> bool: ...

    def keys(self) -> KeysView[str]:
        """Return the names of all entries."""

    def values(self) -> ValuesView[ConditionsGroup[TM_co, str]]:
        """Return all entries."""

    def items(self) -> ItemsView[str, ConditionsGroup[TM_co, str]]:
        """Return all (name, entry) pairs."""


class ConditionsModel(Protocol[TM_co]):
    """The values of all condition sequences of a specific main model instance and its
    submodels, accessible via the submodels' (dotted) names (e.g. `model` or
    `model.rconcmodel`).

    The type parameter (the main model type) only serves to allow HydPy's Mypy plugin
    to determine the actual type of each condition value.
    """

    def __getitem__(self, key: str, /) -> ConditionsSubmodel[modeltools.Model]: ...

    def __iter__(self) -> Iterator[str]: ...

    def __len__(self) -> int: ...

    def __contains__(self, key: object, /) -> bool: ...

    def keys(self) -> KeysView[str]:
        """Return the names of all entries."""

    def values(self) -> ValuesView[ConditionsSubmodel[modeltools.Model]]:
        """Return all entries."""

    def items(self) -> ItemsView[str, ConditionsSubmodel[modeltools.Model]]:
        """Return all (name, entry) pairs."""


Conditions: TypeAlias = dict[str, "ConditionsModel[modeltools.Model]"]

TypeNDIM: TypeAlias = int
TypeTYPE: TypeAlias = type[float | int | bool]  # ToDo: is still `str` in some cases
TypeSPAN: TypeAlias = tuple[int | float | bool | None, int | float | bool | None]
TypeINIT: TypeAlias = int | float | bool | None
TypeTIME: TypeAlias = bool | None
TypeNUMERIC: TypeAlias = bool

# The following type aliases are broad placeholders for typing different aspects of
# |Variable| subclasses, which different hooks of HydPy's Mypy plugin narrow:
GeneralHook: TypeAlias = Any
ShapeHookGet: TypeAlias = tuple[int, ...]
ShapeHookSet: TypeAlias = int | tuple[int, ...]
CallHook: TypeAlias = Union[
    ScalarInputFloat, VectorInputFloat, MatrixInputFloat, TensorInputFloat
]
TrimHook: TypeAlias = Union[CallHook, None]
ArrayHook: TypeAlias = NDArray[Any]


class SharableConfiguration(TypedDict):
    """Specification of the configuration data that main models can share with their
    submodels."""

    landtype_constants: parametertools.Constants | None
    """Land cover type-related constants."""
    soiltype_constants: parametertools.Constants | None
    """Soil type-related constants."""
    landtype_refindices: parametertools.NameParameter | None
    """Reference to a land cover type-related index parameter."""
    soiltype_refindices: parametertools.NameParameter | None
    """Reference to a soil type-related index parameter."""
    refweights: parametertools.Parameter | None
    """Reference to a weighting parameter (probably handling the size of some 
    computational subunits like the area of hydrological response units)."""


DeployMode = Literal[
    "newsim",
    "oldsim",
    "obs",
    "obs_newsim",
    "obs_oldsim",
    "oldsim_bi",
    "obs_bi",
    "obs_oldsim_bi",
    "newsim_update",
    "obs_newsim_update",
]
LineStyle = Literal["-", "--", "-.", ":", "solid", "dashed", "dashdot", "dotted"]
StepSize = Literal["daily", "d", "monthly", "m", "yearly", "y"]


class CyParametersProtocol(Protocol):
    """The protocol for the `parameters` attribute of Cython extension classes.

    Class |Cythonizer| generates the actual, model-specific implementations
    automatically.
    """


class CySequencesProtocol(Protocol):
    """The protocol for the `sequences` attribute of Cython extension classes.

    Class |Cythonizer| generates the actual, model-specific implementations
    automatically.
    """


class CyModelProtocol(Protocol):
    """The protocol of Cython extension classes for defining efficient model
    implementations.

    Class |Cythonizer| generates the actual, model-specific implementations
    automatically.
    """

    idx_sim: int
    parameters: CyParametersProtocol
    sequences: CySequencesProtocol


class CySubstepModelProtocol(CyModelProtocol):
    """The protocol of Cython extension classes for defining efficient model
    implementations compatible with class |SubstepModel|.

    Class |Cythonizer| generates the actual, model-specific implementations
    automatically.
    """

    timeleft: float
    """The time left within the current simulation step [s]."""


SeriesFileType = Literal["npy", "asc", "nc"]
SeriesAggregationType = Literal["none", "mean"]
SeriesConventionType = Literal["model-specific", "HydPy"]
SimulationModeType = Literal["historical", "forecast"]

l1: Literal[1] = 1

MethodGroup = Literal[
    "RECEIVER_METHODS",
    "INLET_METHODS",
    "OBSERVER_METHODS",
    "RUN_METHODS",
    "PART_ODE_METHODS",
    "FULL_ODE_METHODS",
    "POST_ODE_METHODS",
    "ADD_METHODS",
    "INTERFACE_METHODS",
    "OUTLET_METHODS",
    "SENDER_METHODS",
]

LinkInputOutputSequenceGroup = Literal[
    "inlets", "outlets", "observers", "receivers", "senders", "inputs", "outputs"
]

LinkInputSequenceGroup = Literal[
    "inlets", "outlets", "observers", "receivers", "senders", "inputs"
]

__all__ = [
    "AbstractContextManager",
    "Any",
    "ArrayFloat",
    "ArrayFloatFlex",
    "ArrayHook",
    "assert_never",
    "Callable",
    "CallHook",
    "cast",
    "Concatenate",
    "ClassVar",
    "Collection",
    "Conditions",
    "ConditionsGroup",
    "ConditionsModel",
    "ConditionsSubmodel",
    "ConditionValue",
    "CyModelProtocol",
    "CySubstepModelProtocol",
    "Collection1",
    "Collection2",
    "Collection3",
    "DeployMode",
    "FastAccessMatrix",
    "FastAccessTensor",
    "FastAccessVector",
    "Final",
    "Float",
    "GeneralHook",
    "Generator",
    "Generic",
    "get_type_hints",
    "Hashable",
    "Iterable",
    "Iterator",
    "LineStyle",
    "LinkInputOutputSequenceGroup",
    "LinkInputSequenceGroup",
    "Literal",
    "l1",
    "Mapping",
    "Matrix",
    "MatrixBool",
    "MatrixBytes",
    "MatrixFloat",
    "MatrixInput",
    "MatrixInputBool",
    "MatrixInputFloat",
    "MatrixInputInt",
    "MatrixInputObject",
    "MatrixInt",
    "Mayberable1",
    "Mayberable2",
    "Mayberable3",
    "MayNonerable1",
    "MayNonerable2",
    "MayNonerable3",
    "MethodGroup",
    "Name",
    "NamedTuple",
    "NDArray",
    "NDArrayBool",
    "NDArrayFloat",
    "NDArrayInt",
    "NDArrayObject",
    "NestedFloat",
    "Never",
    "NewType",
    "NoReturn",
    "Optional",
    "overload",
    "P_",
    "ParamSpec",
    "Protocol",
    "ScalarInputBool",
    "ScalarInputFloat",
    "ScalarInputInt",
    "ShapeHookGet",
    "ShapeHookSet",
    "Self",
    "SeriesAggregationType",
    "SeriesConventionType",
    "SeriesFileType",
    "Sequence",
    "Sequence1",
    "Sequence2",
    "Sequence3",
    "SharableConfiguration",
    "SimulationModeType",
    "Sized",
    "StepSize",
    "T_inv",
    "T_co",
    "T_contra",
    "T1",
    "T2",
    "T3",
    "Tensor",
    "TensorBool",
    "TensorFloat",
    "TensorInput",
    "TensorInputBool",
    "TensorInputFloat",
    "TensorInputInt",
    "TensorInputObject",
    "TensorInt",
    "TextIO",
    "TM_co",
    "TOM_co",
    "TrimHook",
    "TypeAlias",
    "TypeINIT",
    "TypeNDIM",
    "TypeNUMERIC",
    "TypeSPAN",
    "TypeTIME",
    "TypeTYPE",
    "TypeVar",
    "TypedDict",
    "TYPE_CHECKING",
    "Union",
    "Unpack",
    "Vector",
    "VectorBool",
    "VectorFloat",
    "VectorFloatFlex",
    "VectorInput",
    "VectorInputBool",
    "VectorInputFloat",
    "VectorInputInt",
    "VectorInputObject",
    "VectorInt",
]
