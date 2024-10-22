"""This module implements masking features to define which entries of |Parameter| or
|Sequence_| arrays are relevant and which are not."""

# import...
# ...from standard library
from __future__ import annotations
import inspect

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools

# from hydpy.core import parametertools    actual import below
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import variabletools
    from hydpy.core import parametertools


class BaseMask(NDArrayBool):
    """Base class for defining |CustomMask| and |DefaultMask| classes."""

    name: str

    def __new__(cls, array=None, doc: Optional[str] = None, **kwargs) -> Self:
        self = cls.array2mask(array, **kwargs)
        self.__doc__ = doc
        return self

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.lower()

    @classmethod
    def array2mask(cls, array=None, **kwargs) -> Self:
        """Create a new mask object based on the given |numpy.ndarray| and return it."""
        kwargs["dtype"] = bool
        if array is None:
            return numpy.ndarray.__new__(cls, 0, **kwargs)
        return numpy.asarray(array, **kwargs).view(cls)

    def __repr__(self) -> str:  # ToDo: required?
        return numpy.ndarray.__repr__(self).replace(", dtype=bool", "")


class CustomMask(BaseMask):
    """Mask that awaits one sets all |bool| values manually.

    Class |CustomMask| is the most basic applicable mask and provides no special
    features except for allowing its |bool| values to be defined manually.  Use it
    when you require a masking behaviour not captured by an available mask.

    Like the more advanced masks, |CustomMask| can work via Python's descriptor
    protocol, but it is primarily thought to be applied directly:

    >>> from hydpy.core.masktools import CustomMask
    >>> mask1 = CustomMask([[True, False, False],
    ...                     [True, False, False]])

    Note that calling any mask object (not only those of type |CustomMask|) returns a
    new mask without changing the existing one.

    >>> mask2 = mask1([[False, True, False],
    ...                [False, True, False]])
    >>> mask1
    CustomMask([[ True, False, False],
                [ True, False, False]])
    >>> mask2
    CustomMask([[False,  True, False],
                [False,  True, False]])

    All masks stem from |numpy.ndarray|.  Here are some useful examples of working with
    them:

    >>> mask3 = mask1 + mask2
    >>> mask3
    CustomMask([[ True,  True, False],
                [ True,  True, False]])
    >>> mask3 ^ mask1
    CustomMask([[False,  True, False],
                [False,  True, False]])
    >>> ~mask3
    CustomMask([[False, False,  True],
                [False, False,  True]])
    >>> mask1 & mask2
    CustomMask([[False, False, False],
                [False, False, False]])

    Use the `in` operator to check if a mask defines a subset of another:

    >>> mask1 in mask3
    True
    >>> mask3 in mask1
    False
    """

    def __call__(
        self, bools: Union[VectorInputBool, MatrixInputBool, TensorInputBool]
    ) -> Self:
        return type(self)(bools)

    def __contains__(
        self, other: Union[VectorInputBool, MatrixInputBool, TensorInputBool]
    ) -> bool:
        return bool(numpy.all(self[other]))


class DefaultMask(BaseMask):
    """A mask with all entries being |True| of the same shape as its master |Variable|
    object.

    See the documentation on class |CustomMask| for the basic usage of class
    |DefaultMask|.

    The following example shows how to apply |DefaultMask| via Python's descriptor
    protocol, which should be the common situation:

    >>> from hydpy.core.parametertools import Parameter
    >>> from hydpy.core.masktools import DefaultMask
    >>> class Par1(Parameter):
    ...     shape = (2, 3)
    ...     defaultmask = DefaultMask()
    >>> Par1(None).defaultmask
    DefaultMask([[ True,  True,  True],
                 [ True,  True,  True]])

    Alternatively, you can directly connect a |DefaultMask| with a |Variable| object:

    >>> class Par2(Parameter):
    ...     shape = (2,)
    >>> mask = DefaultMask(Par2(None))
    >>> mask
    DefaultMask([ True,  True])
    """

    variable: Optional[variabletools.Variable]

    def __new__(
        cls,
        variable: Optional[variabletools.Variable] = None,
        doc: Optional[str] = None,
        **kwargs,
    ) -> Self:
        if variable is None:
            self = super().__new__(cls)
        else:
            self = cls.new(variable, **kwargs)
        self.__doc__ = doc
        self.variable = variable
        return self

    def __get__(
        self,
        obj: Optional[variabletools.Variable],
        type_: Optional[type[variabletools.Variable]],
    ) -> Self:
        if (obj is None) or (self.variable is not None):
            return self
        return type(self)(obj)

    def __call__(self, **kwargs) -> Self:
        return type(self)(self.variable, **kwargs)

    def __contains__(self, other) -> bool:
        return bool(numpy.all(self()[other]))

    @classmethod
    def new(cls, variable: variabletools.Variable, **kwargs) -> Self:
        """Return a new |DefaultMask| object associated with the given |Variable|
        object."""
        return cls.array2mask(numpy.full(variable.shape, True), **kwargs)


class IndexMask(DefaultMask):
    """A mask that depends on a referenced index parameter.

    |IndexMask| must be subclassed.  See the masks |hland_masks.Complete| and
    |hland_masks.Soil| of base model |hland| for two concrete example classes, which
    are members of the parameter classes |hland_parameters.ParameterComplete| and
    |hland_parameters.ParameterSoil|.  The documentation on these parameter classes
    provides some application examples.  Further, see the documentation on class
    |CustomMask| for the basic usage of class |DefaultMask|.
    """

    relevant: tuple[int, ...]
    """The integer values that are relevant to the referenced index parameter."""
    variable: variabletools.Variable
    """The variable for which |IndexMask| determines the relevant entries."""

    @classmethod
    def new(cls, variable: variabletools.Variable, **kwargs) -> Self:
        """Return a new |IndexMask| object of the same shape as the parameter
        referenced by |property| |IndexMask.refindices|.

        Entries are only |True| if the integer values of the respective entries of the
        referenced index parameter are members of the class attribute tuple
        |IndexMask.relevant|.

        Before calling new (explicitly or implicitly), one must prepare the variable
        returned by property |IndexMask.refindices|:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> states.sm.mask
        Traceback (most recent call last):
        ...
        RuntimeError: The mask of parameter `sm` of element `?` cannot be determined \
as long as parameter `zonetype` is not prepared properly.

        >>> nmbzones(4)
        >>> zonetype(FIELD, FOREST, ILAKE, GLACIER)
        >>> states.sm.mask
        Soil([ True,  True, False, False])

        If the shape of the |IndexMask.refindices| parameter is zero (which is not
        allowed for |hland|), the returned mask is empty:

        >>> zonetype.shape = 0
        >>> states.shape = 0
        >>> states.sm.mask
        Soil([])
        """
        indices = cls.get_refindices(variable)
        values = exceptiontools.getattr_(indices, "values", None)
        if (values is None) or ((len(values) > 0) and (numpy.min(values) < 1)):
            raise RuntimeError(
                f"The mask of parameter {objecttools.elementphrase(variable)} cannot "
                f"be determined as long as parameter `{indices.name}` is not prepared "
                f"properly."
            )
        if isinstance(variable, parametertools.ZipParameter) and (
            variable.relevant is not None
        ):
            relevant = variable.relevant  # ToDo: add an hland evap_hbv example
        else:
            relevant = cls.relevant
        mask = cls.array2mask(numpy.isin(indices.values, relevant), **kwargs)
        if (refinement := cls.get_refinement(variable)) is not None:
            mask[~refinement.values] = False
        return mask

    @classmethod
    def get_refindices(
        cls, variable: variabletools.Variable
    ) -> parametertools.NameParameter:
        """Return the |Parameter| object to determine which entries of |IndexMask|
        must be |True| and which |False|.

        The given `variable` must be the concrete |Variable| object the |IndexMask| is
        responsible for.

        Needs to be overwritten by subclasses:

        >>> from hydpy.core.parametertools import Parameter
        >>> from hydpy.core.masktools import IndexMask
        >>> class Par(Parameter):
        ...     mask = IndexMask()
        >>> Par(None).mask
        Traceback (most recent call last):
        ...
        NotImplementedError: Method `get_refindices` of class `IndexMask` must be \
overridden, which is not the case for class `IndexMask`.
        """
        raise NotImplementedError(
            f"Method `get_refindices` of class `IndexMask` must be overridden, which "
            f"is not the case for class `{cls.__name__}`."
        )

    @property
    def refindices(self) -> parametertools.NameParameter:
        """|Parameter| object for determining which entries of |IndexMask| are |True|
        and which |False|."""
        return self.get_refindices(self.variable)

    @staticmethod
    def get_refinement(
        variable: variabletools.Variable,  # pylint: disable=unused-argument
    ) -> Optional[variabletools.Variable]:
        """If available, return a boolean variable for selecting only the relevant
        entries of the considered variable."""
        return None

    @property
    def refinement(self) -> Optional[variabletools.Variable]:
        """If available, a boolean variable for selecting only the relevant entries of
        the considered variable."""
        return self.get_refinement(self.variable)

    def narrow_relevant(self, relevant: Optional[tuple[int, ...]] = None) -> set[int]:
        """Return a |set| of all currently relevant constants."""
        if relevant is None:
            relevant = self.relevant
        values = self.refindices.values
        if (refinement := self.refinement) is not None:
            values = values[refinement.values]
        return set(values).intersection(relevant)


class SubmodelIndexMask(IndexMask):
    """A mask that depends on a referenced index parameter of another model."""

    @classmethod
    def get_refindices(
        cls, variable: variabletools.Variable
    ) -> parametertools.NameParameter:
        """Return the |Parameter| object to determine which entries of
        |SubmodelIndexMask| must be |True| and which |False|.

        |SubmodelIndexMask| works only for given |ZipParameter| instances and tries to
        return the currently handled |ZipParameter.refindices| parameter instance.
        """
        assert isinstance(variable, parametertools.ZipParameter)
        if (refindices := variable.refindices) is None:  # ToDo: hbv-based example
            raise RuntimeError(
                f"Variable {objecttools.elementphrase(variable)} does currently not "
                f"reference an instance-specific index parameter."
            )
        return refindices


class Masks:
    """Base class for handling groups of masks.

    |Masks| subclasses are basically just containers, which are defined similar as
    |SubParameters| and |SubSequences| subclasses:

    >>> from hydpy.core.masktools import Masks
    >>> from hydpy.core.masktools import IndexMask, DefaultMask, CustomMask
    >>> class Masks(Masks):
    ...     CLASSES = (IndexMask, DefaultMask)
    >>> masks = Masks()

    The contained mask classes are available via attribute access in lower case letters:

    >>> masks
    indexmask of module hydpy.core.masktools
    defaultmask of module hydpy.core.masktools
    >>> masks.indexmask is IndexMask
    True
    >>> "indexmask" in dir(masks)
    True

    The `in` operator is supported:

    >>> IndexMask in masks
    True
    >>> CustomMask in masks
    False
    >>> "mask" in masks
    Traceback (most recent call last):
    ...
    TypeError: The given value `mask` of type `str` is neither a Mask class nor a \
Mask instance.

    Using item access, strings (in whatever case), mask classes, and mask objects are
    accepted:

    >>> masks["IndexMask"] is IndexMask
    True
    >>> masks["indexmask"] is IndexMask
    True
    >>> masks[IndexMask] is IndexMask
    True
    >>> masks[CustomMask()]
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to retrieve a mask based on key `CustomMask([])`, the \
following error occurred: The key does not define an available mask.
    >>> masks["test"]
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to retrieve a mask based on key `'test'`, the following \
error occurred: The key does not define an available mask.
    >>> masks[1]
    Traceback (most recent call last):
    ...
    TypeError: While trying to retrieve a mask based on key `1`, the following error \
occurred: The given key is neither a `string` a `mask` type.
    """

    CLASSES: tuple[type[BaseMask], ...] = ()

    def __init__(self) -> None:
        for cls in self.CLASSES:
            setattr(self, cls.__name__.lower(), cls)

    @property
    def name(self) -> Literal["masks"]:
        """`masks`

        >>> from hydpy.core.masktools import Masks
        >>> Masks().name
        'masks'
        """
        return "masks"

    def __iter__(self) -> Iterator[type[BaseMask]]:
        for cls in self.CLASSES:
            yield getattr(self, cls.__name__.lower())

    def __contains__(self, mask: Union[BaseMask, type[BaseMask]]) -> bool:
        if isinstance(mask, BaseMask):
            mask = type(mask)
        if mask in self.CLASSES:
            return True
        try:
            if issubclass(mask, BaseMask):
                return False
        except TypeError:
            pass
        raise TypeError(
            f"The given {objecttools.value_of_type(mask)} is neither a Mask class nor "
            f"a Mask instance."
        )

    def __getitem__(self, key: Union[str, BaseMask, type[BaseMask]]) -> BaseMask:
        _key = key
        try:
            if inspect.isclass(key):
                if issubclass(key, BaseMask):
                    key = key.__name__.lower()
            elif isinstance(key, BaseMask):
                if key in self:
                    return key
                raise RuntimeError("The key does not define an available mask.")
            if isinstance(key, str):
                try:
                    return getattr(self, key.lower())
                except AttributeError:
                    raise RuntimeError(
                        "The key does not define an available mask."
                    ) from None
            raise TypeError("The given key is neither a `string` a `mask` type.")
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to retrieve a mask based on key `{repr(_key)}`"
            )

    def __repr__(self) -> str:
        lines = []
        for mask in self:
            lines.append(f"{mask.__name__.lower()} of module {mask.__module__}")
        return "\n".join(lines)


class NodeMasks(Masks):
    """|Masks| subclass for class |Node|.

    At the moment, the purpose of class |NodeMasks| is to make the implementation of
    |ModelSequence| and |NodeSequence| more similar.  It will become relevant for
    applications as soon as we support 1-dimensional node sequences.
    """

    CLASSES = (DefaultMask,)


from hydpy.core import parametertools  # pylint: disable=(wrong-import-position
