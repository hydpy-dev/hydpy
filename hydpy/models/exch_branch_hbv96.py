# pylint: disable=line-too-long, unused-wildcard-import
"""
.. deprecated:: 6.5

   |exch_branch_hbv96| will be removed in HydPy 8.0.  Please use |exch_branch_rules|
   instead.  Method |exch_branch_hbv96.Model.convert_2_exch_branch_rules| helps to
   convert existing configurations.

|exch_branch_hbv96| allows branching the summed input from some inlet nodes to an
arbitrary number of outlet nodes. The original HBV96 implementation is supposed to
split inflowing discharge, but |exch_branch_hbv96| is suitable for splitting arbitrary
variables. Calculations are performed for each branch individually by linear
interpolation (or extrapolation) following tabulated supporting points.  Additionally,
|exch_branch_hbv96| allows adjusting the input data with differences that can vary
monthly.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "01.01.2000 00:00", "01.01.2000 11:00", "1h"

|exch_branch_hbv96| has no parameters whose values on the simulation step size, which
is why we can pass anything (or nothing) to function |parameterstep| without changing
the following results (note the deprecation warning):

>>> from hydpy.core.testtools import warn_later
>>> from hydpy.models.exch_branch_hbv96 import *
>>> with warn_later():
...     parameterstep()
HydPyDeprecationWarning: Application model `exch_branch_hbv96` is deprecated and will \
be removed in HydPy 8.0.  Please use `exch_branch_rules` instead (method \
`convert_2_exch_branch_rules` of `exch_branch_hbv96` helps to convert existing \
configurations).

|exch_branch_hbv96| queries inflow from two inlet |Node| objects and passes the
branched outflow to three outlet |Node| objects.  Thus, In contrast to most other
application models, we need to define the parameter values before connecting the
model to its |Element| object, called `branch`:

>>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
>>> branch = Element("branch",
...                  inlets=["input1", "input2"],
...                  outlets=["output1", "output2", "output3"])
>>> delta(-1.0)
>>> minimum(-1.0)
>>> xpoints(0.0, 2.0, 4.0, 6.0)
>>> ypoints(output1=[0.0, 1.0, 2.0, 3.0],
...         output2=[0.0, 1.0, 0.0, 0.0],
...         output3=[0.0, 0.0, 2.0, 6.0])
>>> branch.model = model

We do not have to define any initial values in the test settings because the
|exch_branch_hbv96| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%H:%M"

The (identical) values of the inlet nodes `input1` and `input2` define no realistic
inflow series.  Instead, they serve to show the behaviour of |exch_branch_hbv96| within
and outside the current range defined by parameter |XPoints|:

>>> import numpy
>>> nodes.input1.sequences.sim.series = numpy.arange(-1.0, 10.0)/2
>>> nodes.input2.sequences.sim.series = numpy.arange(-1.0, 10.0)/2

`output1` shows linear continuations below and above the current range of parameter
|XPoints|. `output2` points out that inverse relationships are allowed. `output3` shows
that |exch_branch_hbv96| does not enforce equality between the total sum of input and
output values:

.. integration-test::

    >>> test("exch_branch_hbv96_ex1")
    |  date | originalinput | adjustedinput |             outputs | input1 | input2 | output1 | output2 | output3 |
    ---------------------------------------------------------------------------------------------------------------
    | 00:00 |          -1.0 |          -1.0 | -0.5  -0.5      0.0 |   -0.5 |   -0.5 |    -0.5 |    -0.5 |     0.0 |
    | 01:00 |           0.0 |          -1.0 | -0.5  -0.5      0.0 |    0.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 02:00 |           1.0 |           0.0 |  0.0   0.0      0.0 |    0.5 |    0.5 |     0.0 |     0.0 |     0.0 |
    | 03:00 |           2.0 |           1.0 |  0.5   0.5      0.0 |    1.0 |    1.0 |     0.5 |     0.5 |     0.0 |
    | 04:00 |           3.0 |           2.0 |  1.0   1.0      0.0 |    1.5 |    1.5 |     1.0 |     1.0 |     0.0 |
    | 05:00 |           4.0 |           3.0 |  1.5   0.5      1.0 |    2.0 |    2.0 |     1.5 |     0.5 |     1.0 |
    | 06:00 |           5.0 |           4.0 |  2.0   0.0      2.0 |    2.5 |    2.5 |     2.0 |     0.0 |     2.0 |
    | 07:00 |           6.0 |           5.0 |  2.5   0.0      4.0 |    3.0 |    3.0 |     2.5 |     0.0 |     4.0 |
    | 08:00 |           7.0 |           6.0 |  3.0   0.0      6.0 |    3.5 |    3.5 |     3.0 |     0.0 |     6.0 |
    | 09:00 |           8.0 |           7.0 |  3.5   0.0      8.0 |    4.0 |    4.0 |     3.5 |     0.0 |     8.0 |
    | 10:00 |           9.0 |           8.0 |  4.0   0.0     10.0 |    4.5 |    4.5 |     4.0 |     0.0 |    10.0 |
"""

from __future__ import annotations
import typing_extensions

import hydpy
from hydpy.auxs import ppolytools
from hydpy.core import exceptiontools
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core.typingtools import *
from hydpy.exe.modelimports import *
from hydpy.models.exch import exch_model
from hydpy.models import exch_branch_rules


@typing_extensions.deprecated(
    "Application model `exch_branch_hbv96` is deprecated and will be removed in "
    "HydPy 8.0.  Please use `exch_branch_rules` instead (method "
    "`convert_2_exch_branch_rules` of `exch_branch_hbv96` helps to convert existing "
    "configurations).",
    category=exceptiontools.HydPyDeprecationWarning,
)
class Model(modeltools.AdHocModel):
    """|exch_branch_hbv96.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Branch-HBV96", description="branch model adopted from IHMS-HBV96"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (exch_model.Pick_OriginalInput_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (exch_model.Calc_AdjustedInput_V1, exch_model.Calc_Outputs_V1)
    ADD_METHODS = ()
    OUTLET_METHODS = (exch_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    nodenames: list[str]
    """Names of the output nodes."""

    def __init__(self) -> None:
        super().__init__()
        self.nodenames = []

    def connect(self) -> None:
        """Connect the |LinkSequence| instances handled by the actual model to the
        |NodeSequence| instances handled by one inlet node and multiple outlet nodes.

        |exch_branch_hbv96| passes multiple output values to different outlet nodes,
        which requires additional information regarding the "direction" of each output
        value.  Therefore, it uses node names as keywords.  Assume the discharge values
        of both nodes `inflow1` and `inflow2`  shall be  branched to nodes `outflow1`
        and `outflow2` via element `branch`:

        >>> from hydpy import Element, pub
        >>> branch = Element("mybranch",
        ...                  inlets=["inflow1", "inflow2"],
        ...                  outlets=["outflow1", "outflow2"])

        Then, parameter |YPoints| relates different supporting points via keyword
        arguments to the respective nodes:

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.core.exceptiontools import ignore_deprecations
        >>> from hydpy.models.exch_branch_hbv96 import *
        >>> with ignore_deprecations():
        ...     parameterstep()
        >>> delta(0.0)
        >>> xpoints(0.0, 3.0)
        >>> ypoints(outflow1=[0.0, 1.0], outflow2=[0.0, 2.0])
        >>> parameters.update()

        After connecting the model with its element, the total discharge value of nodes
        `inflow1` and `inflow2` can be adequately divided:

        >>> branch.model = model
        >>> branch.inlets.inflow1.sequences.sim = 1.0
        >>> branch.inlets.inflow2.sequences.sim = 5.0
        >>> model.simulate(0)
        >>> branch.outlets.outflow1.sequences.sim
        sim(2.0)
        >>> branch.outlets.outflow2.sequences.sim
        sim(4.0)

        The following error is raised in case of missing (or misspelt) outlet nodes:

        >>> branch.outlets.remove_device(branch.outlets.outflow1, force=True)
        >>> parameters.update()
        >>> model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: Model `exch_branch_hbv96` of element `mybranch` tried to \
connect to an outlet node named `outflow1`, which is not an available outlet node of \
element `mybranch`.
        """

        inlets = self.element.inlets
        total = self.sequences.inlets.total
        if exceptiontools.getattr_(total, "shape", None) != (len(inlets),):
            total.node2idx = {}
        total.shape = len(inlets)
        for idx, node in enumerate(inlets):
            double = node.get_double("inlets")
            total.set_pointer(double, idx)
            total.node2idx[node] = idx

        branched = self.sequences.outlets.branched
        branched.node2idx = {}
        for idx, name in enumerate(self.nodenames):
            try:
                outlet = getattr(self.element.outlets, name)
            except AttributeError:
                raise RuntimeError(
                    f"Model {objecttools.elementphrase(self)} tried to connect to an "
                    f"outlet node named `{name}`, which is not an available outlet "
                    f"node of element `{self.element.name}`."
                ) from None
            double = outlet.get_double("outlets")
            branched.set_pointer(double, idx)
            branched.node2idx[outlet] = idx

    def convert_2_exch_branch_rules(self) -> exch_branch_rules.Model:
        """Return an |exch_branch_rules| model whose parameter |Rules| yields the same
        results as the current values of |Delta|, |Minimum|, |XPoints|, and |YPoints|.

        |exch_branch_hbv96| applies its interpolation rules to an input adjusted by
        |Delta| and |Minimum|.  |Model.convert_2_exch_branch_rules| integrates both
        adjustments into the supporting points of the |PPoly| instances handled by the
        |Rules| parameter of |exch_branch_rules| (see the
        :ref:`exch_branch_rules_input_modifying_rules` example for further
        information).

        We prepare a configuration of |exch_branch_hbv96| that resembles a weir that
        directs all (adjusted) input up to a capacity of 2.0 to `branch1` and the
        excess to `branch2`:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> from hydpy.core.exceptiontools import ignore_deprecations
        >>> from hydpy.models.exch_branch_hbv96 import *
        >>> with ignore_deprecations():
        ...     parameterstep()
        >>> xpoints(0.0, 2.0, 4.0)
        >>> ypoints(branch1=[0.0, 2.0, 2.0], branch2=[0.0, 0.0, 2.0])

        We start with a time constant value for |Delta| of 1 and set |Minimum| to 0.5:

        >>> delta(1.0)
        >>> minimum(0.5)

        For each branch, the conversion shifts the x values of the supporting points by
        -|Delta|, removes the smallest one, and adds two supporting points with
        identical y values that cover |Minimum| (the first one is placed arbitrarily
        one unit to the left):

        >>> rulesmodel = model.convert_2_exch_branch_rules()
        >>> rulesmodel.parameters.control.rules
        rules(
            PPolys(
                branch1=PPoly(
                    xs=[-1.5, -0.5, 1.0, 3.0],
                    ys=[0.5, 0.5, 2.0, 2.0],
                ),
                branch2=PPoly(
                    xs=[-1.5, -0.5, 1.0, 3.0],
                    ys=[0.0, 0.0, 0.0, 2.0],
                ),
            )
        )

        To verify the conversion, we prepare a function that applies both models across
        all simulation steps of the initialisation period, covering a leap year and a
        non-leap year, and over a range of input values, and prints the largest
        absolute difference between their outputs:

        >>> from hydpy import round_
        >>> def check():
        ...     derived.moy.update()
        ...     derived.nmbbranches.update()
        ...     derived.nmbpoints.update()
        ...     rulesmodel.parameters.derived.toy.update()
        ...     branched = rulesmodel.sequences.outlets.branched
        ...     branched.shape = 2
        ...     maxdiff = 0.0
        ...     for idx in range(len(pub.timegrids.init)):
        ...         model.idx_sim = idx
        ...         rulesmodel.idx_sim = idx
        ...         for x in numpy.linspace(-5.0, 10.0, 31):
        ...             fluxes.originalinput = x
        ...             model.calc_adjustedinput_v1()
        ...             model.calc_outputs_v1()
        ...             rulesmodel.sequences.fluxes.input_ = x
        ...             rulesmodel.pass_branched_v1()
        ...             diff = numpy.abs(fluxes.outputs.values - branched.values)
        ...             maxdiff = max(maxdiff, numpy.max(diff))
        ...     round_(maxdiff)

        Both models give identical results:

        >>> check()
        0.0

        For monthly varying |Delta| values, the conversion defines one rule for the
        centre of the last simulation step of a month and another one for the centre
        of the first simulation step of the following month whenever |Delta| changes
        between both months.  Hence, |Rules| never interpolates between the rules of
        different months (note that the last step of February always refers to February
        29, which also works for non-leap years, and that the resulting rules are only
        correct for the simulation step size defined at the time of conversion):

        >>> delta(jan=1.0, feb=1.0, mar=-1.0, apr=-1.0, may=-1.0, jun=-1.0, jul=-1.0,
        ...       aug=-1.0, sep=-1.0, oct=-1.0, nov=1.0, dec=1.0)
        >>> rulesmodel = model.convert_2_exch_branch_rules()
        >>> rules = rulesmodel.parameters.control.rules
        >>> for toy, ppolys in rules:
        ...     print(toy, ppolys["branch1"].x0s[0])
        toy_2_29_12_0_0 -1.5
        toy_3_1_12_0_0 0.5
        toy_10_31_12_0_0 0.5
        toy_11_1_12_0_0 -1.5
        >>> check()
        0.0

        The same holds for other simulation step sizes:

        >>> pub.timegrids = "2000-01-01", "2002-01-01", "6h"
        >>> rulesmodel = model.convert_2_exch_branch_rules()
        >>> for toy, ppolys in rulesmodel.parameters.control.rules:
        ...     print(toy, ppolys["branch1"].x0s[0])
        toy_2_29_21_0_0 -1.5
        toy_3_1_3_0_0 0.5
        toy_10_31_21_0_0 0.5
        toy_11_1_3_0_0 -1.5
        >>> check()
        0.0

        If |Minimum| is -|numpy.inf|, the conversion only shifts the supporting points:

        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> minimum(-inf)
        >>> rulesmodel = model.convert_2_exch_branch_rules()
        >>> rulesmodel.parameters.control.rules.toy_2_29_12_0_0
        PPolys(
            branch1=PPoly(
                xs=[-1.0, 1.0, 3.0],
                ys=[0.0, 2.0, 2.0],
            ),
            branch2=PPoly(
                xs=[-1.0, 1.0, 3.0],
                ys=[0.0, 0.0, 2.0],
            ),
        )
        >>> check()
        0.0

        If |Minimum| lies to the right of all (shifted) supporting points, the
        conversion adds a supporting point that preserves the slope of the right
        extrapolation:

        >>> xpoints(0.0, 2.0, 4.0)
        >>> ypoints(branch1=[0.0, 2.0, 2.0], branch2=[0.0, 0.0, 2.0])
        >>> minimum(5.0)
        >>> rulesmodel = model.convert_2_exch_branch_rules()
        >>> rulesmodel.parameters.control.rules.toy_2_29_12_0_0
        PPolys(
            branch1=PPoly(
                xs=[3.0, 4.0, 5.0],
                ys=[2.0, 2.0, 2.0],
            ),
            branch2=PPoly(
                xs=[3.0, 4.0, 5.0],
                ys=[3.0, 3.0, 4.0],
            ),
        )
        >>> check()
        0.0

        The "toy strategy" for modelling seasonal patterns can cover monthly-varying
        values accurately only if the simulation step size is an integer divisor of one
        day (with an even number of seconds, so that the step centres coincide with
        full seconds).  For other simulation step sizes,
        |Model.convert_2_exch_branch_rules| raises the following error:

        >>> pub.timegrids = "2000-01-01", "2000-01-08", "7h"
        >>> model.convert_2_exch_branch_rules()
        Traceback (most recent call last):
        ...
        ValueError: While trying to convert model `exch_branch_hbv96` of element `?` \
to an `exch_branch_rules` model, the following error occurred: The conversion of \
monthly varying `delta` values requires a simulation step size that divides one day \
into steps with an even number of seconds each, but the actual step size is `7h`.

        .. testsetup::

            >>> del pub.timegrids
        """

        def _interpolate(x: float, xs: VectorFloat, ys: VectorFloat) -> float:
            # same algorithm as in method `Calc_Outputs_V1`
            for i in range(1, len(xs)):
                if xs[i] > x:
                    break
            x0, y0 = xs[i - 1], ys[i - 1]
            dx, dy = xs[i] - x0, ys[i] - y0
            return (x - x0) * dy / dx + y0

        def _get_ppolys(delta: float) -> ppolytools.PPolys:
            name2ppoly: dict[str, ppolytools.PPoly] = {}
            for name, ys in zip(self.nodenames, ypoints):
                if numpy.isneginf(minimum):
                    xs_new, ys_new = list(xs - delta), list(ys)
                else:
                    x_min, y_min = minimum - delta, _interpolate(minimum, xs, ys)
                    xs_new, ys_new = [x_min - 1.0, x_min], [y_min, y_min]
                    for x, y in zip(xs - delta, ys):
                        if x > x_min:
                            xs_new.append(x)
                            ys_new.append(y)
                    if len(xs_new) == 2:
                        xs_new.append(x_min + 1.0)
                        ys_new.append(_interpolate(minimum + 1.0, xs, ys))
                name2ppoly[name] = ppolytools.PPoly(xs=xs_new, ys=ys_new)
            return ppolytools.PPolys(**name2ppoly)

        try:
            con = self.parameters.control
            xs, ypoints = con.xpoints.values, con.ypoints.values
            minimum, deltas = con.minimum.value, con.delta.values
            rulesmodel = importtools.prepare_model("exch_branch_rules")
            rules = rulesmodel.parameters.control.rules
            if numpy.all(deltas == deltas[0]):
                rules(_get_ppolys(deltas[0]))
                return rulesmodel
            stepsize = hydpy.pub.timegrids.stepsize
            seconds = stepsize.seconds
            if (86400 % seconds) or (seconds % 2):
                raise ValueError(
                    f"The conversion of monthly varying `{con.delta.name}` values "
                    f"requires a simulation step size that divides one day into "
                    f"steps with an even number of seconds each, but the actual step "
                    f"size is `{stepsize}`."
                )
            toy2ppolys: dict[str, ppolytools.PPolys] = {}
            for idx, delta in enumerate(deltas):
                if delta != (delta_old := deltas[idx - 1]):
                    date = timetools.Date(f"2000-{idx + 1:02d}-01")
                    toy_old = timetools.TOY(date - stepsize / 2)
                    toy_new = timetools.TOY(date + stepsize / 2)
                    toy2ppolys[str(toy_old)] = _get_ppolys(delta_old)
                    toy2ppolys[str(toy_new)] = _get_ppolys(delta)
            rules(**toy2ppolys)
            return rulesmodel
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to convert model {objecttools.elementphrase(self)} to "
                f"an `exch_branch_rules` model"
            )


tester = Tester()
cythonizer = Cythonizer()
