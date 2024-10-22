"""This module implements some "types" to be used for static (and eventually dynamical)
typing."""

# import...
# ...from standard library
from __future__ import annotations
from collections.abc import (
    Callable,
    Collection,
    Generator,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    Sized,
    Sequence,
)
from contextlib import AbstractContextManager
from typing import (
    Any,
    cast,
    ClassVar,
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
    TypedDict,
    TypeVar,
    TYPE_CHECKING,
    Union,
)
from typing_extensions import (
    assert_never,
    Concatenate,
    Never,
    ParamSpec,
    Self,
    TypeAlias,
    Unpack,
)

# ...from site-packages
import numpy
from numpy.typing import NDArray

# ...from hydpy
if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import hydpytools
    from hydpy.core import parametertools
    from hydpy.cythons import pointerutils

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

P = ParamSpec("P")

Name = NewType("Name", str)
Name.__doc__ = """Type for strings that represent names."""


Mayberable1 = Union[T, Iterable[T]]
Mayberable2 = Union[T1, T2, Iterable[Union[T1, T2]]]
Mayberable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]]]
MayNonerable1 = Union[T, Iterable[T], None]
MayNonerable2 = Union[T1, T2, Iterable[Union[T1, T2]], None]
MayNonerable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]], None]

Collection1 = Union[T, Collection[T]]
Collection2 = Union[T1, T2, Collection[Union[T1, T2]]]
Collection3 = Union[T1, T2, T3, Collection[Union[T1, T2, T3]]]

Sequence1 = Union[T, Sequence[T]]
Sequence2 = Union[T1, T2, Sequence[Union[T1, T2]]]
Sequence3 = Union[T1, T2, T3, Sequence[Union[T1, T2, T3]]]

Float_co = TypeVar("Float_co", covariant=True)
Float1 = TypeVar("Float1", bound=float)
Float2 = TypeVar("Float2", bound=float)

NDArrayObject = NDArray[numpy.generic]
NDArrayFloat = NDArray[numpy.float64]
NDArrayInt = NDArray[numpy.int64]
NDArrayBool = NDArray[numpy.bool_]

Vector = NDArray[T]
VectorObject = NDArray[numpy.generic]
VectorFloat = NDArray[numpy.float64]
VectorInt = NDArray[numpy.int64]
VectorBool = NDArray[numpy.bool_]
VectorInput = Union[Sequence[T], Vector[T]]
VectorInputObject = Union[Sequence[object], VectorObject]
VectorInputFloat = Union[Sequence[float], VectorFloat]
VectorInputInt = Union[Sequence[int], VectorInt]
VectorInputBool = Union[Sequence[bool], VectorBool]

Matrix = NDArray[T]
MatrixObject = NDArray[numpy.generic]
MatrixFloat = NDArray[numpy.float64]
MatrixInt = NDArray[numpy.int64]
MatrixBool = NDArray[numpy.bool_]
MatrixBytes = NDArray[numpy.bytes_]
MatrixInput = Union[Sequence[Sequence[T]], Matrix[T]]
MatrixInputObject = Union[Sequence[VectorInputObject], MatrixObject]
MatrixInputFloat = Union[Sequence[VectorInputFloat], MatrixFloat]
MatrixInputInt = Union[Sequence[VectorInputInt], MatrixInt]
MatrixInputBool = Union[Sequence[VectorBool], MatrixBool]


Tensor = NDArray[T]
TensorObject = NDArray[numpy.generic]
TensorFloat = NDArray[numpy.float64]
TensorInt = NDArray[numpy.int64]
TensorBool = NDArray[numpy.bool_]
TensorInput = Union[Sequence[Sequence[Sequence[T]]], Tensor[T]]
TensorInputObject = Union[Sequence[MatrixInputObject], TensorObject]
TensorInputFloat = Union[Sequence[MatrixInputFloat], TensorFloat]
TensorInputInt = Union[Sequence[MatrixInputInt], TensorInt]
TensorInputBool = Union[Sequence[MatrixInputBool], TensorBool]


NestedFloat: TypeAlias = Union[
    float, NDArrayFloat, Mapping[str, "NestedFloat"], Sequence["NestedFloat"]
]

ArrayFloat = TypeVar(
    "ArrayFloat", float, VectorFloat, MatrixFloat, Union[float, VectorFloat]
)

ConditionsSubmodel = dict[str, dict[str, Union[float, NDArrayFloat]]]
ConditionsModel = dict[str, ConditionsSubmodel]
Conditions = dict[str, ConditionsModel]


class SharableConfiguration(TypedDict):
    """Specification of the configuration data that main models can share with their
    submodels."""

    landtype_constants: Optional[parametertools.Constants]
    """Land cover type-related constants."""
    soiltype_constants: Optional[parametertools.Constants]
    """Soil type-related constants."""
    landtype_refindices: Optional[parametertools.NameParameter]
    """Reference to a land cover type-related index parameter."""
    soiltype_refindices: Optional[parametertools.NameParameter]
    """Reference to a soil type-related index parameter."""
    refweights: Optional[parametertools.Parameter]
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
]
LineStyle = Literal["-", "--", "-.", ":", "solid", "dashed", "dashdot", "dotted"]
StepSize = Literal["daily", "d", "monthly", "m"]


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

l1: Literal[1] = 1

MethodGroup = Literal[
    "RECEIVER_METHODS",
    "INLET_METHODS",
    "RUN_METHODS",
    "PART_ODE_METHODS",
    "FULL_ODE_METHODS",
    "ADD_METHODS",
    "INTERFACE_METHODS",
    "OUTLET_METHODS",
    "SENDER_METHODS",
]

__all__ = [
    "AbstractContextManager",
    "Any",
    "ArrayFloat",
    "assert_never",
    "Callable",
    "cast",
    "Concatenate",
    "ClassVar",
    "Collection",
    "Conditions",
    "ConditionsModel",
    "ConditionsSubmodel",
    "CyModelProtocol",
    "CySubstepModelProtocol",
    "Collection1",
    "Collection2",
    "Collection3",
    "DeployMode",
    "Final",
    "Generator",
    "Generic",
    "get_type_hints",
    "Hashable",
    "Iterable",
    "Iterator",
    "LineStyle",
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
    "P",
    "ParamSpec",
    "Protocol",
    "Self",
    "SeriesAggregationType",
    "SeriesConventionType",
    "SeriesFileType",
    "Sequence",
    "Sequence1",
    "Sequence2",
    "Sequence3",
    "SharableConfiguration",
    "Sized",
    "StepSize",
    "T",
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
    "TypeAlias",
    "TypeVar",
    "TypedDict",
    "TYPE_CHECKING",
    "Union",
    "Unpack",
    "Vector",
    "VectorBool",
    "VectorFloat",
    "VectorInput",
    "VectorInputBool",
    "VectorInputFloat",
    "VectorInputInt",
    "VectorInputObject",
    "VectorInt",
]
