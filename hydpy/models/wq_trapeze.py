# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""Submodel for calculating discharge and related properties at a river cross-section
based on an arbitrary number of stacket, symmetric trapezes and the Manning-Strickler
equation.

|wq_trapeze| is a stateless submodel that requires information on the current water
level or depth from its main model (usually a routing model).  It returns the
corresponding discharge and related properties, such as the kinematic wave celerity.
See the documentation on the application model |musk_mct|, which shows how to use
|wq_trapeze| in practice.  Here, we only aim to visualise how |wq_trapeze| combines
multiple trapezes to a single cross-section profile via method |wq_trapeze.Model.plot|.

The following test function helps us to use method |wq_trapeze.Model.plot| repeatedly
and insert the generated figures into the online documentation:

>>> from matplotlib import pyplot
>>> from hydpy.core.testtools import save_autofig
>>> def plot(example=None, save=True, add_x_y=None, **kwargs):
...     derived.trapezeheights.update()
...     derived.slopewidths.update()
...     figure = model.plot(**kwargs)
...     if add_x_y is not None:
...         x, y = add_x_y
...         pyplot.plot([x, x], [y, 5.0], color=kwargs.get("color"), linestyle=":")
...         pyplot.plot([-x, -x], [y, 5.0], color=kwargs.get("color"), linestyle=":")
...     if example is not None:
...         save_autofig(f"wq_trapeze_{example}.png", figure=figure)

We start with a single trapeze:

>>> from hydpy.models.wq_trapeze import *
>>> parameterstep()
>>> nmbtrapezes(1)

Parameter |BottomLevels| does not affect the profile's shape for a single trapeze.  We
set its value to one meter arbitrarily:

>>> bottomlevels(1.0)

With parameter |BottomWidths| larger than zero and parameter |SideSlopes| being zero,
the single trapeze becomes a simple, infinitely high rectangle:

>>> bottomwidths(2.0)
>>> sideslopes(0.0)
>>> plot("rectangle")

    .. image:: wq_trapeze_rectangle.png

Conversely, the single trapeze becomes a simple, infinitely high triangle:

>>> bottomwidths(0.0)
>>> sideslopes(2.0)
>>> plot("triangle")

    .. image:: wq_trapeze_triangle.png

Set both values larger than zero to gain a "complete" trapeze:

>>> bottomwidths(2.0)
>>> sideslopes(2.0)
>>> plot("one_trapeze")

    .. image:: wq_trapeze_one_trapeze.png

Next, we want to construct a more complex profile consisting of three trapezes:

>>> nmbtrapezes(3)

We must assign them increasing bottom levels (the bottom level of an upper trapeze
defines the height of its lower neighbour):

>>> bottomlevels(1.0, 3.0, 4.0)

The following profile combines the three previously defined geometries:

>>> bottomwidths(2.0, 0.0, 2.0)
>>> sideslopes(0.0, 2.0, 2.0)
>>> plot("three_trapezes")

    .. image:: wq_trapeze_three_trapezes.png

Note that each upper trapeze is stretched according to the width of its lower
neighbour.  The following example illustrates this more clearly by plotting each
trapeze in a different colour:

>>> nmbtrapezes(1)
>>> bottomlevels(1.0)
>>> bottomwidths(2.0)
>>> sideslopes(0.0)
>>> plot(add_x_y=(1.0, 3.0), ymax=3.0, color="green", label="trapeze 1")
>>> bottomlevels(3.0)
>>> bottomwidths(2.0)
>>> sideslopes(2.0)
>>> plot(add_x_y=(3.0, 4.0), ymax=4.0, color="yellow", label="trapeze 2")
>>> bottomlevels(4.0)
>>> bottomwidths(8.0)
>>> sideslopes(2.0)
>>> plot("config_1", ymax=5.0, color="red", label="trapeze 3")

    .. image:: wq_trapeze_config_1.png

In addition to the configuration options shown in the last example, one can pass |True|
to the keyword argument `label`. Then, |wq_trapeze.Model.plot| tries to include the
responsible element's name into the legend, which is impossible in this example, so
that "?" serves as a spare:

>>> plot("config_2", ymax=3.0, label=True)

    .. image:: wq_trapeze_config_2.png

(Upon closer inspection, the last example also shows that |wq_trapeze.Model.plot|
ignores too low `ymax`  values silently.)
"""
# import...
# ...from site-packages
from matplotlib import pyplot

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.interfaces import routinginterfaces
from hydpy.exe.modelimports import *

# ...from ga
from hydpy.models.wq import wq_control
from hydpy.models.wq import wq_model


class Model(modeltools.AdHocModel, routinginterfaces.CrossSectionModel_V1):
    """Multi-trapeze channel profile version of HydPy-WQ."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        wq_model.Set_WaterDepth_V1,
        wq_model.Set_WaterLevel_V1,
        wq_model.Process_V1,
        wq_model.Get_WettedArea_V1,
        wq_model.Get_SurfaceWidth_V1,
        wq_model.Get_Discharge_V1,
        wq_model.Get_Celerity_V1,
    )
    ADD_METHODS = (
        wq_model.Calc_WettedAreas_V1,
        wq_model.Calc_WettedArea_V1,
        wq_model.Calc_WettedPerimeters_V1,
        wq_model.Calc_WettedPerimeterDerivatives_V1,
        wq_model.Calc_SurfaceWidths_V1,
        wq_model.Calc_SurfaceWidth_V1,
        wq_model.Calc_Discharges_V1,
        wq_model.Calc_Discharge_V2,
        wq_model.Calc_DischargeDerivatives_V1,
        wq_model.Calc_DischargeDerivative_V1,
        wq_model.Calc_Celerity_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    def plot(
        self,
        *,
        ymax: Optional[float] = None,
        color: Optional[str] = None,
        label: Union[bool, str] = False
    ) -> pyplot.Figure:
        """Plot the channel profile.

        See the main documentation of application model |wq_trapeze| for more
        information.
        """
        con = self.parameters.control
        der = self.parameters.derived
        n = con.nmbtrapezes.value
        bl = con.bottomlevels.values
        bw = con.bottomwidths.values
        ss = con.sideslopes.values
        sw = der.slopewidths.values
        th = der.trapezeheights.values

        xs = [0.0]
        ys = [bl[0]]

        def _add(dx: float, dy: float) -> None:
            xs.append(xs[-1] + dx)
            ys.append(ys[-1] + dy)
            xs.insert(0, -xs[-1])
            ys.insert(0, ys[-1])

        for i in range(n):
            _add(dx=bw[i] / 2.0, dy=0.0)
            if i < n - 1:
                _add(dx=sw[i] / 2.0, dy=th[i])

        if (ymax is None) or (ymax <= ys[-1]):
            if n == 1:
                ymax = bl[0] + (bw[0] / 2.0 if bw[0] > 0.0 else 1.0)
            else:
                ymax = bl[0] + (bl[-1] - bl[0]) / n * (n + 1)

        dy_ = ymax - bl[-1]
        dx_ = dy_ * ss[-1]
        _add(dx=dx_, dy=dy_)

        pyplot.xlabel("distance from centre [m]")
        pyplot.ylabel("elevation [m]")
        if isinstance(label, bool) and label:
            label = objecttools.devicename(self)
        if isinstance(label, str):
            pyplot.plot(xs, ys, color=color, label=label)
            pyplot.legend()
        else:
            pyplot.plot(xs, ys, color=color)

        return pyplot.gcf()

    @importtools.define_targetparameter(wq_control.BottomSlope)
    def prepare_bottomslope(self, bottomslope: float) -> None:
        """Set the bottom's slope (in the longitudinal direction) [-].

        >>> from hydpy.models.wq_trapeze import *
        >>> parameterstep()
        >>> model.prepare_bottomslope(0.01)
        >>> bottomslope
        bottomslope(0.01)
        """
        self.parameters.control.bottomslope(bottomslope)


tester = Tester()
cythonizer = Cythonizer()
