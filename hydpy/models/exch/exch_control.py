# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools


class CrestHeight(parametertools.Parameter):
    """Crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestWidth(parametertools.Parameter):
    """Crest width [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class FlowCoefficient(parametertools.Parameter):
    """Flow coefficient [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.62


class FlowExponent(parametertools.Parameter):
    """Flow exponent [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5


class AllowedExchange(parametertools.Parameter):
    """The highest water exchange allowed [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5


class Delta(parametertools.MonthParameter):
    """Monthly varying difference for increasing or decreasing the input [e.g. m³/s]."""

    TYPE, TIME, SPAN = float, None, (None, None)
    INIT = 0.0


class Minimum(parametertools.Parameter):
    """The allowed minimum value of the adjusted input [e.g. m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 0.0


class XPoints(parametertools.Parameter):
    """Supporting points for the independent input variable [e.g. m³/s].

    There must be at least two supporting points, and they must be strictly monotonous.
    If not, |XPoints| raises the following errors:

    >>> from hydpy.models.exch_branch_hbv96 import *
    >>> parameterstep()
    >>> xpoints(1.0, 2.0)
    >>> xpoints
    xpoints(1.0, 2.0)

    >>> xpoints(1.0)
    Traceback (most recent call last):
    ...
    ValueError: Branching via linear interpolation requires at least two supporting \
points, but parameter `xpoints` of element `?` received 1 value(s).

    >>> xpoints(1.0, 2.0, 2.0, 3.0)
    Traceback (most recent call last):
    ...
    ValueError: The values of parameter `xpoints` of element `?` must be arranged \
strictly monotonously, which is not the case for the given values `1.0, 2.0, 2.0, and \
3.0`.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def __call__(self, *args, **kwargs) -> None:
        self._set_shape(len(args))
        if (shape := self._get_shape()[0]) < 2:
            raise ValueError(
                f"Branching via linear interpolation requires at least two supporting "
                f"points, but parameter {objecttools.elementphrase(self)} received "
                f"{shape} value(s)."
            )
        super().__call__(*args, **kwargs)
        if min(numpy.diff(self._get_value())) <= 0.0:
            raise ValueError(
                f"The values of parameter {objecttools.elementphrase(self)} must be "
                f"arranged strictly monotonously, which is not the case for the given "
                f"values `{objecttools.enumeration(self._get_value())}`."
            )


class YPoints(parametertools.Parameter):
    """Supporting points for the dependent output variables [e.g. m³/s].

    Preparing parameter |YPoints| requires consistency with parameter |XPoints| and the
    currently available |Node| objects.

    .. testsetup::

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()

    >>> from hydpy.models.exch_branch_hbv96 import *
    >>> parameterstep("1d")
    >>> ypoints
    ypoints(?)

    You need to prepare parameter |XPoints| first:

    >>> ypoints(1.0, 2.0)
    Traceback (most recent call last):
    ...
    RuntimeError: The shape of parameter `ypoints` of element `?` depends on the \
shape of parameter `xpoints`, which is not defined so far.

    >>> xpoints(1.0, 2.0, 3.0)

    Supply the names of the output |Node| objects as keyword arguments:

    >>> ypoints(1.0, 2.0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `ypoints` of element `?`, no branches are defined.  Do \
this via keyword arguments, as explained in the documentation.

    The number of x and y supporting points must be identical for all branches.:

    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2=[2.0, 4.0])
    Traceback (most recent call last):
    ...
    ValueError: Each branch requires the same number of supporting points as given \
for parameter `xpoints`, which is 3, but for branch `branch1` of parameter `ypoints` \
of element `?`, 2 values are provided.

    >>> xpoints(1.0, 2.0)

    When working on an actual project (indicated by a predefined project name), each
    branch name must correspond to a |Node| name:

    >>> from hydpy import pub, Nodes
    >>> pub.projectname = "test"
    >>> nodes = Nodes("branch1")
    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2=[2.0, 4.0])
    Traceback (most recent call last):
    ...
    RuntimeError: Parameter `ypoints` of element `?` is supposed to branch to node \
`branch2`, but such a node is not available.

    We use the following general exception message for some unexpected errors:

    >>> nodes = Nodes("branch1", "branch2")
    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2="xy")
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values for branch `branch2` of parameter \
`ypoints` of element `?`, the following error occurred: could not convert string to \
float: 'xy'

    Changing the number of branches during runtime might result in erroneous
    connections to the |Node| objects:

    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2=[2.0, 4.0])
    >>> ypoints
    ypoints(branch1=[1.0, 2.0],
            branch2=[2.0, 4.0])
    >>> ypoints(branch1=[1.0, 2.0])
    Traceback (most recent call last):
    ...
    RuntimeError: The number of branches of the exch model should not be changed \
during run time.  If you really need to do this, first initialise a new "branched" \
sequence and connect it to the respective outlet nodes properly.
    """

    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)

    def __call__(self, *args, **kwargs) -> None:
        try:
            shape = (len(kwargs), self.subpars.xpoints.shape[0])
        except exceptiontools.AttributeNotReady:
            raise RuntimeError(
                f"The shape of parameter {objecttools.elementphrase(self)} depends on "
                f"the shape of parameter `xpoints`, which is not defined so far."
            ) from None
        if shape[0] == 0:
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, no branches are "
                f"defined.  Do this via keyword arguments, as explained in the "
                f"documentation."
            )
        branched = self.subpars.pars.model.sequences.outlets.branched
        if (branched.shape[0] != 0) and (branched.shape[0] != shape[0]):
            raise RuntimeError(
                "The number of branches of the exch model should not be changed "
                "during run time.  If you really need to do this, first initialise a "
                'new "branched" sequence and connect it to the respective outlet '
                "nodes properly."
            )
        self.shape = shape
        self.values = numpy.nan
        for idx, (key, value) in enumerate(sorted(kwargs.items())):
            if key not in devicetools.Node.query_all():
                if exceptiontools.attrready(hydpy.pub, "projectname"):
                    raise RuntimeError(
                        f"Parameter {objecttools.elementphrase(self)} is supposed to "
                        f"branch to node `{key}`, but such a node is not available."
                    )
            try:
                self.values[idx] = value  # type: ignore[index]
            except BaseException:
                if shape[1] != len(value):
                    raise ValueError(
                        f"Each branch requires the same number of supporting points "
                        f"as given for parameter `xpoints`, which is {shape[1]}, but "
                        f"for branch `{key}` of parameter "
                        f"{objecttools.elementphrase(self)}, {len(value)} values are "
                        f"provided."
                    ) from None
                objecttools.augment_excmessage(
                    f"While trying to set the values for branch `{key}` of parameter "
                    f"{objecttools.elementphrase(self)}"
                )
        if branched.shape == (0,):
            branched.shape = shape[0]
        self.subpars.pars.model.sequences.fluxes.outputs.shape = shape[0]
        self.subpars.pars.model.nodenames.clear()
        for idx, key in enumerate(sorted(kwargs.keys())):
            setattr(self, key, self.values[idx])  # type: ignore[index]
            self.subpars.pars.model.nodenames.append(key)

    def __repr__(self) -> str:
        try:
            names = self.subpars.pars.model.nodenames
            lines = []
            for idx, (name, values) in enumerate(zip(names, self._get_value())):
                line = f"{name}={objecttools.repr_list(values)},"
                if not idx:
                    lines.append(f"ypoints({line}")
                else:
                    lines.append(f"        {line}")
            lines[-1] = f"{lines[-1][:-1]})"
            return "\n".join(lines)
        except BaseException:
            return "ypoints(?)"
