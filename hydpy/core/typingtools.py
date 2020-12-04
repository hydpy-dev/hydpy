# -*- coding: utf-8 -*-
"""This module implements some "types" to be used for static (and
eventually dynamical) typing."""
# import...
# ...from standard library
import abc
from typing import *
from typing_extensions import Protocol  # type: ignore[misc]

# ...from hydpy
if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import hydpytools
    from hydpy.cythons.autogen import pointerutils

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

Mayberable1 = Union[T, Iterable[T]]
Mayberable2 = Union[T1, T2, Iterable[Union[T1, T2]]]
Mayberable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]]]
MayNonerable1 = Union[T, Iterable[T], None]
MayNonerable2 = Union[T1, T2, Iterable[Union[T1, T2]], None]
MayNonerable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]], None]

Sequence1 = Union[T, Sequence[T]]
Sequence2 = Union[T1, T2, Sequence[Union[T1, T2]]]
Sequence3 = Union[T1, T2, T3, Sequence[Union[T1, T2, T3]]]

VectorInputType = TypeVar("VectorInputType")
VectorType = TypeVar("VectorType", bound="Vector")
DataTypeCov = TypeVar("DataTypeCov", covariant=True)
DataType = TypeVar("DataType")


class VectorInput(Protocol[DataTypeCov]):
    """Protocol class for providing input to "mathematical", 1-dimensional sequences."""

    @overload
    def __getitem__(self, item: int) -> DataTypeCov:
        ...

    @overload
    def __getitem__(self: VectorInputType, item: slice) -> VectorInputType:
        ...

    def __getitem__(
        self: VectorInputType, item: Union[int, slice]
    ) -> Union[DataTypeCov, VectorInputType]:
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Iterator[DataTypeCov]:
        ...


class Vector(Protocol[DataType]):
    """Protocol class for defining "mathematical", 1-dimensional sequences."""

    @overload
    def __getitem__(self, item: int) -> DataType:
        ...

    @overload
    def __getitem__(self: VectorType, item: slice) -> VectorType:
        ...

    @overload
    def __getitem__(self: VectorType, item: VectorInput[int]) -> VectorType:
        ...

    def __getitem__(
        self: VectorType, item: Union[int, slice, VectorInput[int]]
    ) -> Union[DataType, VectorType]:
        ...

    @overload
    def __setitem__(self, item: int, value: DataType) -> None:
        ...

    @overload
    def __setitem__(
        self, item: slice, value: Union[DataType, VectorInput[DataType]]
    ) -> None:
        ...

    @overload
    def __setitem__(
        self, item: VectorInput[int], value: Union[DataType, VectorInput[DataType]]
    ) -> None:
        ...

    def __setitem__(
        self,
        item: Union[int, slice, VectorInput[int]],
        value: Union[DataType, VectorInput[DataType]],
    ) -> None:
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Iterator[DataType]:
        ...

    def __add__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __radd__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __sub__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __rsub__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __mul__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __rmul__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __truediv__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __rtruediv__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __pow__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __rpow__(self, other: Union[DataType, VectorType]) -> VectorType:
        ...

    def __lt__(self, other: Union[DataType, VectorType]) -> "Vector[int]":
        ...

    def __le__(self, other: Union[DataType, VectorType]) -> "Vector[int]":
        ...

    def __eq__(self, other: Union[DataType, VectorType]) -> "Vector[int]":  # type: ignore[override] # pylint: disable=line-too-long
        ...

    def __ne__(self, other: Union[DataType, VectorType]) -> "Vector[int]":  # type: ignore[override] # pylint: disable=line-too-long
        ...

    def __ge__(self, other: Union[DataType, VectorType]) -> "Vector[int]":
        ...

    def __gt__(self, other: Union[DataType, VectorType]) -> "Vector[int]":
        ...

    def shape(self) -> Tuple[int]:
        """Shape of the vector."""


class IterableNonString(abc.ABC):
    """Abstract base class for checking if an object is iterable but not a
    string.

    >>> from hydpy.core.typingtools import IterableNonString
    >>> isinstance("asdf", IterableNonString)
    False
    >>> isinstance(["asdf"], IterableNonString)
    True
    >>> issubclass(str, IterableNonString)
    False
    >>> issubclass(list, IterableNonString)
    True
    >>>
    """

    @classmethod
    def __subclasshook__(cls, subclass: Type) -> bool:
        return hasattr(subclass, "__iter__") and not (
            isinstance(subclass, str) or issubclass(subclass, str)
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


__all__ = [
    "IterableNonString",
    "Mayberable1",
    "Mayberable2",
    "Mayberable3",
    "MayNonerable1",
    "MayNonerable2",
    "MayNonerable3",
    "Vector",
    "VariableProtocol",
    "CyModelProtocol",
]
