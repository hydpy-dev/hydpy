# pylint: disable=missing-module-docstring

import inflect
import numpy

import hydpy
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.auxs import interptools
from hydpy.auxs import ppolytools


class CrestHeight(parametertools.Parameter):
    """Crest height [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class CrestWidth(parametertools.Parameter):
    """Crest width [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class FlowCoefficient(parametertools.Parameter):
    """Flow coefficient [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.62


class FlowExponent(parametertools.Parameter):
    """Flow exponent [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.5


class AllowedExchange(parametertools.Parameter):
    """The highest water exchange allowed [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.5


class Delta(parametertools.MonthParameter):
    """Monthly varying difference for increasing or decreasing the input [e.g. m³/s]."""

    TYPE: Final = float
    INIT = 0.0


class Minimum(parametertools.Parameter):
    """The allowed minimum value of the adjusted input [e.g. m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    INIT = 0.0


class XPoints(parametertools.Parameter):
    """Supporting points for the independent input variable [e.g. m³/s].

    There must be at least two supporting points, and they must be strictly monotonic.
    If not, |XPoints| raises the following errors:

    >>> from hydpy.core.exceptiontools import ignore_deprecations
    >>> from hydpy.models.exch_branch_hbv96 import *
    >>> with ignore_deprecations():
    ...     parameterstep()
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

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float

    def __call__(self, *args, **kwargs) -> None:
        self.shape = len(args)
        if (shape := self.shape[0]) < 2:
            raise ValueError(
                f"Branching via linear interpolation requires at least two supporting "
                f"points, but parameter {objecttools.elementphrase(self)} received "
                f"{shape} value(s)."
            )
        super().__call__(*args, **kwargs)
        if min(numpy.diff(self.value)) <= 0.0:
            raise ValueError(
                f"The values of parameter {objecttools.elementphrase(self)} must be "
                f"arranged strictly monotonously, which is not the case for the given "
                f"values `{objecttools.enumeration(self.value)}`."
            )


class YPoints(parametertools.Parameter):
    """Supporting points for the dependent output variables [e.g. m³/s].

    Preparing parameter |YPoints| requires consistency with parameter |XPoints| and the
    currently available |Node| objects.

    .. testsetup::

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()

    >>> from hydpy.core.exceptiontools import ignore_deprecations
    >>> from hydpy.models.exch_branch_hbv96 import *
    >>> with ignore_deprecations():
    ...     parameterstep("1d")
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
during runtime.  If you really need to do this, first initialise a new "branched" \
sequence and connect it to the respective outlet nodes properly.
    """

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float

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
        if exceptiontools.getattr_(branched, "shape", shape)[0] != shape[0]:
            raise RuntimeError(
                "The number of branches of the exch model should not be changed "
                "during runtime.  If you really need to do this, first initialise a "
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
                self.values[idx] = value
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
        if not exceptiontools.attrready(branched, "shape"):
            branched.shape = shape[0]
        self.subpars.pars.model.sequences.fluxes.outputs.shape = shape[0]
        self.subpars.pars.model.nodenames.clear()
        for idx, key in enumerate(sorted(kwargs.keys())):
            setattr(self, key, self.values[idx])
            self.subpars.pars.model.nodenames.append(key)

    def __repr__(self) -> str:
        try:
            names = self.subpars.pars.model.nodenames
            lines = []
            for idx, (name, values) in enumerate(zip(names, self.value)):
                line = f"{name}={objecttools.repr_list(values)},"
                if not idx:
                    lines.append(f"ypoints({line}")
                else:
                    lines.append(f"        {line}")
            lines[-1] = f"{lines[-1][:-1]})"
            return "\n".join(lines)
        except BaseException:
            return "ypoints(?)"


class Targets(parametertools.NmbParameter):
    """Target nodes.

    |Targets| is an integer parameter with the only allowed value of two.  It serves to
    define the names of both target nodes, which is necessary for creating the required
    connections.  "stream" refers to the node reflecting the main riverbed; "transfer"
    refers to the node to which some of the water is branched (or supplied from):

    >>> from hydpy.models.exch_branch_io import *
    >>> parameterstep()
    >>> targets
    targets(?)
    >>> targets(stream="river", transfer="diversion")
    >>> targets
    targets(stream="river", transfer="diversion")
    >>> targets.value
    2

    Both target nodes must have different names:

    >>> targets(stream="river", transfer="river")
    Traceback (most recent call last):
    ...
    ValueError: You must not assign the same target node name (`river`) to both the \
keyword arguments `stream` and `transfer` of parameter `targets` of element `?` \
(remember that node names serve as unique identifiers).

    >>> targets
    targets(stream="river", transfer="diversion")
    """

    SPAN = (2, 2)

    def __call__(self, stream: str, transfer: str) -> None:
        if stream == transfer:
            raise ValueError(
                f"You must not assign the same target node name (`{stream}`) to both "
                f"the keyword arguments `stream` and `transfer` of parameter "
                f"{objecttools.elementphrase(self)} (remember that node names serve "
                f"as unique identifiers)."
            )
        super().__call__(2)
        self.subpars.pars.model.__hydpy__targetnames__ = (stream, transfer)

    def __repr__(self) -> str:
        try:
            ns = self.subpars.pars.model.targetnames
        except RuntimeError:
            return f"{self.name}(?)"
        return f'{self.name}(stream="{ns[0]}", transfer="{ns[1]}")'


class MinStream(parametertools.Parameter):
    """Minimum stream outflow that externally requested withdrawals must not undercut
    [m³/s].

    |MinStream| only restricts positive values of |RequestedTransfer| (withdrawals).
    It neither affects the transfers calculated by the fallback parameter
    |FlowTransferRules| nor triggers supplies when the inflow is already below
    |MinStream|.  Set it to minus |numpy.inf| to allow arbitrary withdrawals.  See the
    documentation on method |Pass_ActualTransfer_StreamOutflow_V1| and parameter
    |KeepWaterBalance| for further information.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (-numpy.inf, numpy.inf)
    INIT = 0.0

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim upper values in accordance with :math:`MinStream \leq MaxStream`.

        >>> from hydpy.models.exch_branch_io import *
        >>> parameterstep()
        >>> maxstream.value = 2.0
        >>> minstream(1.0)
        >>> minstream
        minstream(1.0)
        >>> minstream(2.0)
        >>> minstream
        minstream(2.0)
        >>> minstream(3.0)
        >>> minstream
        minstream(2.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.maxstream, "value", None)
        return super().trim(lower, upper)


class MaxStream(parametertools.Parameter):
    """Maximum stream outflow that externally requested supplies must not exceed
    [m³/s].

    |MaxStream| only restricts negative values of |RequestedTransfer| (supplies).  It
    neither affects the transfers calculated by the fallback parameter
    |FlowTransferRules| nor triggers withdrawals when the inflow is already above
    |MaxStream|.  Set it to |numpy.inf| to allow arbitrary supplies.  See the
    documentation on method |Pass_ActualTransfer_StreamOutflow_V1| and parameter
    |KeepWaterBalance| for further information.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (-numpy.inf, numpy.inf)
    INIT = numpy.inf

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim lower values in accordance with :math:`MinStream \leq MaxStream`.

        >>> from hydpy.models.exch_branch_io import *
        >>> parameterstep()
        >>> minstream.value = 2.0
        >>> maxstream(3.0)
        >>> maxstream
        maxstream(3.0)
        >>> maxstream(2.0)
        >>> maxstream
        maxstream(2.0)
        >>> maxstream(1.0)
        >>> maxstream
        maxstream(2.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.minstream, "value", None)
        return super().trim(lower, upper)


class KeepWaterBalance(parametertools.Parameter):
    """Flag to indicate if too-high requested transfers should be reduced [-].

    There are two lines of reasoning:

     * If the requested water transfer is 2 m³/s (withdrawal) but only 1 m³/s is
       available, one must reduce the transfer to 1 m³/s: set |KeepWaterBalance| to
       |True|.
     * The requested water transfer is measured and thus very certain and should always
       be maintained: set |KeepWaterBalance| to |False| (at the cost of violating the
       water balance).

    The same thoughts apply to negative water transfers (supplies) that exceed a given
    threshold.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
    SPAN = (False, True)
    INIT = True


class FlowTransferRules(interptools.SeasonalInterpolator):
    """Seasonally varying interpolation rules for branching the (adjusted) inflow [-].

    |FlowTransferRules| is a fallback parameter that is only relevant for periods
    without available |RequestedTransfer| time series data.

    Please prepare parameter |Targets| before configuring parameter
    |FlowTransferRules|:

    >>> from hydpy import ANN, PPoly, PPolys, pub
    >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"
    >>> from hydpy.models.exch_branch_io import *
    >>> parameterstep()
    >>> flowtransferrules(PPoly(xs=[0.0, 1.0], ys=[0.0, 2.0]))
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to set the interpolation rules of parameter \
`flowtransferrules` of element `?`, the following error occurred: The names of the \
target nodes are still unknown.  Please define them via parameter `targets` first.

    If there is no seasonality, assign a single |PPoly| instance that interpolates
    water transfer based on the (adjusted) inflow:

    >>> targets(stream="river", transfer="diversion")
    >>> flowtransferrules(PPoly(xs=[0.0, 2.0], ys=[0.0, 1.0]))
    >>> flowtransferrules
    flowtransferrules(
        PPoly(
            xs=[0.0, 2.0],
            ys=[0.0, 1.0],
        )
    )

    Behind the scenes, parameter |FlowTransferRules| converts this |PPoly| instance to
    a |PPolys| instance that applies the given interpolation rule to calculate the
    water transfer and leaves the rest for the main stream (note that |PPolys| sorts
    the target nodes alphabetically, which is why derived parameter |StreamIndex| is
    required to identify the main stream's outflow):

    >>> flowtransferrules.toy_01_01_00_00
    PPolys(
        diversion=PPoly(
            xs=[0.0, 2.0],
            ys=[0.0, 1.0],
        ),
        river=PPolys.REST,
    )

    The same mechanism applies when passing multiple |PPoly| instances to introduce
    seasonal patterns:

    >>> flowtransferrules(
    ...     toy_01_01_12=PPoly(xs=[0.0, 2.0], ys=[0.0, 1.0]),
    ...     toy_01_03_12=PPoly(xs=[0.0], ys=[0.0]),
    ... )
    >>> flowtransferrules
    flowtransferrules(
        toy_1_1_12_0_0=PPoly(
            xs=[0.0, 2.0],
            ys=[0.0, 1.0],
        ),
        toy_1_3_12_0_0=PPoly(
            xs=[0.0],
            ys=[0.0],
        ),
    )
    >>> flowtransferrules.toy_01_01_12_00
    PPolys(
        diversion=PPoly(
            xs=[0.0, 2.0],
            ys=[0.0, 1.0],
        ),
        river=PPolys.REST,
    )

    You are allowed to interpolate the water transfer and rest flow independently by
    directly assigning one or multiple |PPolys| instances, which requires explicit
    mentioning of the respective target nodes' names (note that this changes the water
    balance, and so is only useful if you are aware of certain water losses or gains
    bound to specific flow regimes):

    >>> flowtransferrules(
    ...     PPolys(
    ...         river=PPoly(xs=[0.0, 2.0], ys=[0.0, 1.0]),
    ...         diversion=PPoly(xs=[0.0, 2.0], ys=[0.0, 2.0]),
    ...     )
    ... )
    >>> flowtransferrules
    flowtransferrules(
        PPolys(
            diversion=PPoly(
                xs=[0.0, 2.0],
                ys=[0.0, 2.0],
            ),
            river=PPoly(
                xs=[0.0, 2.0],
                ys=[0.0, 1.0],
            ),
        )
    )

    Using wrong target names results in the following error:

    >>> flowtransferrules(
    ...     PPolys(
    ...         stream=PPoly(xs=[0.0, 2.0], ys=[0.0, 1.0]),
    ...         diversion=PPoly(xs=[0.0, 2.0], ys=[0.0, 2.0]),
    ...     )
    ... )
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the interpolation rules of parameter \
`flowtransferrules` of element `?`, the following error occurred: When defining the \
node-specific interpolation rules of parameter `PPolys` manually, you must use the \
target nodes' names defined by parameter `Targets`, which are `river and diversion` \
instead of `diversion and stream`.

    Configuring parameter |FlowTransferRules| based on other interpolation methods is
    currently not supported:

    >>> flowtransferrules(ANN(nmb_inputs=1, nmb_outputs=2, nmb_neurons=(10,)))
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the interpolation rules of parameter \
`flowtransferrules` of element `?`, the following error occurred: Parameter \
`flowtransferrules` currently only supports interpolation via `PPolys` instances.  \
Best practice is to configure them indirectly via `PPoly` instances (see the \
documentation).
    """

    XLABEL = "inflow [m³/s]"
    YLABEL = "outflow [m³/s]"

    def __call__(self, *args, **kwargs) -> None:

        def _ppoly2ppolys(p: interptools.InterpAlgorithm) -> object:
            if isinstance(p, ppolytools.PPoly):
                ppolys: dict[str, ppolytools.PPoly | ppolytools.PPolysOptions] = {
                    targetnames[0]: ppolytools.PPolysOptions.REST,
                    targetnames[1]: p,
                }
                return ppolytools.PPolys(**ppolys)
            return p

        try:
            targetnames = self.subpars.pars.model.targetnames
            args = tuple(_ppoly2ppolys(a) for a in args)
            kwargs = {k: _ppoly2ppolys(a) for k, a in kwargs.items()}
            super().__call__(*args, **kwargs)
            for algorithm in self.algorithms:
                if not isinstance(algorithm, ppolytools.PPolys):
                    raise TypeError(
                        f"Parameter `{self.name}` currently only supports "
                        f"interpolation via `{ppolytools.PPolys.__name__}` "
                        f"instances.  Best practice is to configure them indirectly "
                        f"via `{ppolytools.PPoly.__name__}` instances (see the "
                        f"documentation)."
                    )
                if sorted(algorithm.piecewisepolynomials) != sorted(targetnames):
                    enum_ = objecttools.enumeration
                    raise ValueError(
                        f"When defining the node-specific interpolation rules of "
                        f"parameter `{ppolytools.PPolys.__name__}` manually, you must "
                        f"use the target nodes' names defined by parameter "
                        f"`{Targets.__name__}`, which are `{enum_(targetnames)}` "
                        f"instead of `{enum_(algorithm.piecewisepolynomials)}`."
                    )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the interpolation rules of parameter "
                f"{objecttools.elementphrase(self)}"
            )

    def __repr__(self, simplify: interptools.SimplifyInterpAlgorithm = None) -> str:

        class _Simplify:
            _names: list[str]

            def __init__(self, names: list[str], /) -> None:
                self._names = names

            def __call__(
                self, algorithm: interptools.InterpAlgorithm, /
            ) -> interptools.InterpAlgorithm:
                if (
                    isinstance(algorithm, ppolytools.PPolys)
                    and (len(names := self._names) == 2)
                    and (len(ps := algorithm.piecewisepolynomials) == 2)
                    and (ps.get(names[0]) == algorithm.REST)
                    and (isinstance(transfer := ps.get(names[1]), ppolytools.PPoly))
                ):
                    return transfer
                return algorithm

        return super().__repr__(_Simplify(self.subpars.pars.model.targetnames))


class Rules(interptools.SeasonalInterpolator):
    """Seasonally varying interpolation rules for branching the input [-].

    |Rules| accepts one or multiple |PPolys| instances, which must all address the
    same target nodes:

    >>> from hydpy import ANN, PPoly, PPolys, pub
    >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"
    >>> from hydpy.models.exch_branch_rules import *
    >>> parameterstep()
    >>> rules(
    ...     toy_01_01_12=PPolys(
    ...         river=PPolys.REST,
    ...         diversion=PPoly(xs=[0.0], ys=[1.0]),
    ...     ),
    ...     toy_01_03_12=PPolys(
    ...         diversion=PPoly(xs=[0.0], ys=[2.0]),
    ...         river=PPolys.REST,
    ...     ),
    ... )

    |PPolys| sorts its interpolation functions by the target nodes' names, so each
    output always belongs to the same target node, regardless of the order of the
    keyword arguments:

    >>> model.targetnames
    ('diversion', 'river')
    >>> rules
    rules(
        toy_1_1_12_0_0=PPolys(
            diversion=PPoly(
                xs=[0.0],
                ys=[1.0],
            ),
            river=PPolys.REST,
        ),
        toy_1_3_12_0_0=PPolys(
            diversion=PPoly(
                xs=[0.0],
                ys=[2.0],
            ),
            river=PPolys.REST,
        ),
    )

    Using different target names for different seasons results in the following
    error:

    >>> rules(
    ...     toy_01_01_12=PPolys(river=PPolys.REST, diversion=PPoly(xs=[0.0], ys=[1.0])),
    ...     toy_01_03_12=PPolys(river=PPolys.REST, channel=PPoly(xs=[0.0], ys=[2.0])),
    ... )
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the interpolation rules of parameter `rules` of \
element `?`, the following error occurred: All `PPolys` instances must address the \
same target nodes, but `channel and river` differs from `diversion and river`.

    Configuring parameter |Rules| based on other interpolation methods is currently
    not supported:

    >>> rules(ANN(nmb_inputs=1, nmb_outputs=2, nmb_neurons=(10,)))
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the interpolation rules of parameter `rules` of \
element `?`, the following error occurred: Parameter `rules` currently only supports \
interpolation via `PPolys` instances.

    .. testsetup::

        >>> del pub.timegrids
    """

    XLABEL = "input [e.g. m³/s]"
    YLABEL = "outputs [e.g. m³/s]"

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
            targetnames: list[str] = []
            for algorithm in self.algorithms:
                if not isinstance(algorithm, ppolytools.PPolys):
                    raise TypeError(
                        f"Parameter `{self.name}` currently only supports "
                        f"interpolation via `{ppolytools.PPolys.__name__}` "
                        f"instances."
                    )
                names = list(algorithm.piecewisepolynomials)
                if not targetnames:
                    targetnames = names
                elif names != targetnames:
                    enum_ = objecttools.enumeration
                    raise ValueError(
                        f"All `{ppolytools.PPolys.__name__}` instances must address "
                        f"the same target nodes, but `{enum_(names)}` differs from "
                        f"`{enum_(targetnames)}`."
                    )
            self.subpars.pars.model.__hydpy__targetnames__ = tuple(targetnames)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the interpolation rules of parameter "
                f"{objecttools.elementphrase(self)}"
            )


class ObserverNodes(parametertools.Parameter):
    """The number of the considered observer nodes [-].

    Parameter |ObserverNodes| requires the names of all observer nodes that need
    consideration:

    >>> from hydpy.models.exch_interp import *
    >>> parameterstep()
    >>> observernodes(2)
    Traceback (most recent call last):
    ...
    ValueError: Parameter `observernodes` of element `?` requires the names of all \
relevant observation nodes, but the first given value is of type `int`.

    >>> observernodes
    observernodes(?)

    When receiving this information, it automatically prepares the observer sequence
    |exch_observers.X|:

    >>> observernodes("node_1", "node_2")
    >>> observers.x.shape
    (2,)
    >>> observers.x.observernodes
    ('node_1', 'node_2')

    >>> observernodes
    observernodes("node_1", "node_2")
    >>> observernodes.value
    2
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)

    def __call__(self, *observernodes: str) -> None:
        for i, node in enumerate(observernodes):
            if not isinstance(node, str):
                p = inflect.engine()  # type: ignore[unreachable]
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} requires the names "
                    f"of all relevant observation nodes, but the "
                    f"{p.number_to_words(p.ordinal(i + 1))} given value is of type "
                    f"`{type(node).__name__}`."
                )
        self.value = len(observernodes)
        x = self.subpars.pars.model.sequences.observers.x
        x.shape = self.value
        x.observernodes = observernodes

    def __repr__(self) -> str:
        if self._valueready:
            x = self.subpars.pars.model.sequences.observers.x
            names = tuple(f'"{name}"' for name in x.observernodes)
            return objecttools.assignrepr_tuple(names, self.name, 84)
        return super().__repr__()


class X2Y(interptools.SimpleInterpolator):
    """An interpolation function describing the relationship between arbitrary
    properties [-]."""

    XLABEL = "X"
    YLABEL = "Y"
