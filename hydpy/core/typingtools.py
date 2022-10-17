# -*- coding: utf-8 -*-
"""This module implements some "types" to be used for static (and
eventually dynamical) typing."""
# import...
# ...from standard library
from __future__ import annotations
from typing import *
from typing_extensions import Literal  # type: ignore[misc]
from typing_extensions import Protocol  # type: ignore[misc]

# ...from site-packages
import numpy
import numpy.typing

# ...from hydpy
if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import hydpytools
    from hydpy.cythons import pointerutils

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

Name = NewType("Name", str)

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

NDArrayFloat = numpy.typing.NDArray[numpy.float_]
NDMatrixBytes = numpy.typing.NDArray[bytes]  # type: ignore[type-var]

DeployMode = Literal["newsim", "oldsim", "obs", "obs_newsim", "obs_oldsim"]
LineStyle = Literal["-", "--", "-.", ":", "solid", "dashed", "dashdot", "dotted"]
StepSize = Literal["daily", "d", "monthly", "m"]


class VectorInput(Protocol[Float_co]):
    """Protocol class for providing input to "mathematical", 1-dimensional arrays."""

    @overload
    def __getitem__(
        self,
        item: int,
    ) -> Float_co:
        ...

    @overload
    def __getitem__(
        self,
        item: slice,
    ) -> "VectorInput[Float_co]":
        ...

    def __getitem__(
        self,
        item: Union[int, slice],
    ) -> Union[Float_co, "VectorInput[Float_co]"]:
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Iterator[Float_co]:
        ...


MatrixInput = VectorInput[VectorInput[Float_co]]

VectorSlice = Union[slice, VectorInput[int]]


class Vector(VectorInput[Float1]):
    """Protocol class for defining "mathematical", 1-dimensional sequences."""

    @overload
    def __getitem__(
        self,
        item: int,
    ) -> Float1:
        ...

    @overload
    def __getitem__(
        self,
        item: VectorSlice,
    ) -> "Vector[Float1]":
        ...

    def __getitem__(
        self,
        item: Union[int, slice, VectorInput[int]],
    ) -> Union[Float1, "Vector[Float1]"]:
        ...

    @overload
    def __setitem__(
        self,
        item: int,
        value: float,
    ) -> None:
        ...

    @overload
    def __setitem__(
        self,
        item: VectorSlice,
        value: Union[float, VectorInput[float]],
    ) -> None:
        ...

    def __setitem__(
        self,
        item: Union[int, VectorSlice],
        value: Union[float, VectorInput[float]],
    ) -> None:
        ...

    def __invert__(self) -> "Vector[Float1]":
        ...

    def __add__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __radd__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __sub__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __rsub__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __mul__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __rmul__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __truediv__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __rtruediv__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __pow__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __rpow__(
        self: "Vector[Float1]",
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[Union[Float1, Float2]]":
        ...

    def __lt__(
        self,
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[bool]":
        ...

    def __le__(
        self,
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[bool]":
        ...

    def __eq__(  # type: ignore[override]
        self,
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[bool]":
        ...

    def __ne__(  # type: ignore[override]
        self,
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[bool]":
        ...

    def __ge__(
        self,
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[bool]":
        ...

    def __gt__(
        self,
        other: Union[Float2, "Vector[Float2]"],
    ) -> "Vector[bool]":
        ...

    def shape(self) -> Tuple[int]:
        """Length of the vector."""


class Matrix(MatrixInput[Float1]):
    """Protocol class for providing input to "mathematical", 2-dimensional arrays."""

    @overload
    def __getitem__(
        self,
        item: Tuple[int, int],
    ) -> Float1:
        ...

    @overload
    def __getitem__(
        self,
        item: Union[
            int,
            Tuple[int, VectorSlice],
            Tuple[VectorSlice, int],
        ],
    ) -> Vector[Float1]:
        ...

    @overload
    def __getitem__(
        self,
        item: Union[slice, Tuple[VectorSlice, VectorSlice]],
    ) -> Matrix[Float1]:
        ...

    def __getitem__(
        self,
        item: Union[
            Tuple[int, int],
            int,
            Tuple[int, VectorSlice],
            Tuple[VectorSlice, int],
            slice,
            Tuple[VectorSlice, VectorSlice],
        ],
    ) -> Union[Float1, Vector[Float1], Matrix[Float1]]:
        ...

    @overload
    def __setitem__(self, item: Tuple[int, int], value: float) -> None:
        ...

    @overload
    def __setitem__(
        self,
        item: Union[int, Tuple[int, VectorSlice], Tuple[VectorSlice, int]],
        value: Union[float, VectorInput[float]],
    ) -> None:
        ...

    @overload
    def __setitem__(
        self,
        item: Union[slice, Tuple[VectorSlice, VectorSlice]],
        value: Union[float, MatrixInput[float]],
    ) -> None:
        ...

    def __setitem__(
        self,
        item: Union[
            int,
            Tuple[int, int],
            Tuple[int, VectorSlice],
            Tuple[VectorSlice, int],
            slice,
            Tuple[VectorSlice, VectorSlice],
        ],
        value: Union[float, VectorInput[float], MatrixInput[float]],
    ) -> None:
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Iterator[Vector[Float1]]:
        ...

    def __invert__(self) -> Matrix[Float1]:
        ...

    def __add__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __radd__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __sub__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __rsub__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __mul__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __rmul__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __truediv__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __rtruediv__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __pow__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __rpow__(
        self: Matrix[Float1],
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[Union[Float1, Float2]]:
        ...

    def __lt__(
        self,
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[bool]:
        ...

    def __le__(
        self,
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[bool]:
        ...

    def __eq__(  # type: ignore[override]
        self,
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[bool]:
        ...

    def __ne__(  # type: ignore[override]
        self,
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[bool]:
        ...

    def __ge__(
        self,
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[bool]:
        ...

    def __gt__(
        self,
        other: Union[Float2, Vector[Float2], Matrix[Float2]],
    ) -> Matrix[bool]:
        ...

    @property
    def shape(self) -> Tuple[int, int]:
        """Length of both matrix axes."""


ArrayFloat = TypeVar(
    "ArrayFloat",
    float,
    Vector[float],
    Matrix[float],
)


class VariableProtocol(Protocol):
    """Protocol to identify objects as "variables"."""

    name: str

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """To be called by the |SubVariables| object when preparing a
        new |Variable| object."""


class CyParametersProtocol(Protocol):
    """The protocol for the `parameters` attribute of Cython extension classes.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """


class CySequencesProtocol(Protocol):
    """The protocol for the `sequences` attribute of Cython extension classes.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """


class CyModelProtocol(Protocol):
    """The protocol of Cython extension classes for defining
    efficient model implementations.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """

    idx_sim: int
    parameters: CyParametersProtocol
    sequences: CySequencesProtocol


class ScriptFunction(Protocol):
    """Callback protocol for functions to be executed from the command line
    (see the documentation on function |execute_scriptfunction| and module
    |hyd| for further information).
    """

    def __call__(self, *args: str, **kwargs: str) -> Optional[int]:
        ...


SeriesFileType = Literal["npy", "asc", "nc"]
SeriesAggregationType = Literal["none", "mean"]

__all__ = [
    "ArrayFloat",
    "CyModelProtocol",
    "Collection1",
    "Collection2",
    "Collection3",
    "DeployMode",
    "LineStyle",
    "MatrixInput",
    "Matrix",
    "Mayberable1",
    "Mayberable2",
    "Mayberable3",
    "MayNonerable1",
    "MayNonerable2",
    "MayNonerable3",
    "Name",
    "NDArrayFloat",
    "NDMatrixBytes",
    "ScriptFunction",
    "SeriesAggregationType",
    "SeriesFileType",
    "Sequence1",
    "Sequence2",
    "Sequence3",
    "StepSize",
    "T",
    "T1",
    "T2",
    "T3",
    "VariableProtocol",
    "VectorInput",
    "Vector",
]
