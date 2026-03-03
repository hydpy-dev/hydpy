# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import inflect
import numpy

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *

# ...from managers
from hydpy.models.manager import manager_model
from hydpy.models.manager import manager_control


class ParameterSource(parametertools.Parameter):
    """Base class for parameters that handle individual values for all sources.

    We take the parameter |Active| as an example, which requires (as all subclasses of
    |ParameterSource|) the relevant sources to be defined beforehand:

    >>> from hydpy.models.manager import *
    >>> parameterstep()
    >>> active(c=True, a=False, b=True)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to set the values of parameter `active` of element \
`?`, the following error occurred: Parameter `sources` of element `?` does not know \
the names of the relevant sources so far.

    As soon as the source names are known, you can assign their individual values via
    keyword arguments:

    >>> sources("c", "a", "b")
    >>> active
    active(?)
    >>> active(c=True, a=False, b=True)
    >>> active
    active(a=False, b=True, c=True)
    >>> from hydpy import print_vector
    >>> print_vector(active.values)
    False, True, True

    You can also provide a single general value for all sources.:

    >>> active(True)
    >>> active
    active(True)
    >>> print_vector(active.values)
    True, True, True

    Passing a vector of values as a positional argument also works (but may be prone
    to misallocations):

    >>> active([False, True, True])
    >>> active
    active(a=False, b=True, c=True)
    >>> print_vector(active.values)
    False, True, True

    >>> active(True, False, False)
    >>> active
    active(a=True, b=False, c=False)
    >>> print_vector(active.values)
    True, False, False

    If you mix one positional argument with multiple keywords, the positional argument
    serves as a default value:

    >>> active(True, a=False)
    >>> active
    active(a=False, b=True, c=True)
    >>> active(True, a=False, b=True, c=False)
    >>> active
    active(a=False, b=True, c=False)

    There can be only one default value:

    >>> active(True, False, True, b=True)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `active` of element `?`, \
the following error occurred: Providing keyword arguments and more than one \
positional argument simultaneously is not supported.

    Missing or unknown source names are reported as follows:

    >>> active(c=True, a=False)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `active` of element `?`, \
the following error occurred: For the following source, no value is given: b
    >>> active(c=True)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `active` of element `?`, \
the following error occurred: For the following sources, no values are given: a and b

    >>> active(c=True, a=False, b=True, d=True)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `active` of element `?`, \
the following error occurred: The following source is unknown: d
    >>> active(c=True, a=False, b=True, d=True, e=False)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `active` of element `?`, \
the following error occurred: The following sources are unknown: d and e
    """

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, manager_control.Sources):
            self.__hydpy__change_shape_if_necessary__((p.value,))

    def __call__(self, *args, **kwargs) -> None:
        try:
            if (
                args
                and kwargs
                and not ((len(kwargs) == 1) and (tuple(kwargs)[0] == "auxfile"))
            ):
                raise NotImplementedError
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            try:
                if len(args) > 1 and kwargs:
                    raise ValueError(
                        "Providing keyword arguments and more than one positional "
                        "argument simultaneously is not supported."
                    ) from None
                model = cast(manager_model.Model, self.subpars.pars.model)
                sourcenames = model.parameters.control.sources.sourcenames
                required_names = set(sourcenames)
                given_names = set(kwargs)
                if (len(args) == 0) and (diff := required_names - given_names):
                    p = inflect.engine().plural
                    n = len(diff)
                    raise ValueError(
                        f"For the following {p('source', n)}, no {p('value', n)} "
                        f"{p('is', n)} given: {objecttools.enumeration(sorted(diff))}"
                    ) from None
                if diff := given_names - required_names:
                    p = inflect.engine().plural
                    n = len(diff)
                    raise ValueError(
                        f"The following {p('source', n)} {p('is', n)} unknown: "
                        f"{objecttools.enumeration(sorted(diff))}"
                    ) from None
                if len(args) == 1:
                    default = args[0]
                else:
                    default = None
                values = numpy.empty(self.shape, dtype=self.TYPE)
                for i, name in enumerate(sourcenames):
                    values[i] = kwargs.pop(name, default)
                super().__call__(values)
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to set the values of parameter "
                    f"{objecttools.elementphrase(self)}"
                )

    def __repr__(self) -> str:
        if self._valueready and (len(numpy.unique_values(self.values))) > 1:
            model = cast(manager_model.Model, self.subpars.pars.model)
            sourcenames = model.parameters.control.sources.sourcenames
            n2v = tuple(f"{n}={v}" for n, v in zip(sourcenames, self.values))
            return objecttools.assignrepr_values(n2v, f"{self.name}(") + ")"
        return super().__repr__()
