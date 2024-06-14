# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""Submodel for calculating discharge-related geometries at a river cross-section based
on an arbitrary number of stacket, symmetric trapezes.

|wq_trapeze| is a stateless "two-way" submodel.  It supports calculating properties
like the wetted area for a given water depth and properties like the water depth for a
given wetted area.  See the documentation on the application model |sw1d_channel|,
which shows the usage of "both ways" in practice.  Here, we only aim to visualise how
|wq_trapeze| combines multiple trapezes to a single cross-section profile via method
|TrapezeModel.plot|.

The following test function helps us to use method |TrapezeModel.plot| repeatedly and
insert the generated figures into the online documentation:

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
   :width: 400

Conversely, the single trapeze becomes a simple, infinitely high triangle:

>>> bottomwidths(0.0)
>>> sideslopes(2.0)
>>> plot("triangle")

.. image:: wq_trapeze_triangle.png
   :width: 400

Set both values larger than zero to gain a "complete" trapeze:

>>> bottomwidths(2.0)
>>> sideslopes(2.0)
>>> plot("one_trapeze")

.. image:: wq_trapeze_one_trapeze.png
   :width: 400

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
   :width: 400

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
   :width: 400

In addition to the configuration options shown in the last example, one can pass |True|
to the keyword argument `label`. Then, |TrapezeModel.plot| tries to include the
responsible element's name into the legend, which is impossible in this example, so
that "?" serves as a spare:

>>> plot("config_2", ymax=3.0, label=True)

.. image:: wq_trapeze_config_2.png
   :width: 400

(Upon closer inspection, the last example also shows that |TrapezeModel.plot| ignores
too low `ymax`  values silently.)
"""
# import...

# ...from HydPy
from hydpy.interfaces import routinginterfaces
from hydpy.exe.modelimports import *

# ...from wq
from hydpy.models.wq import wq_model


class Model(wq_model.TrapezeModel, routinginterfaces.CrossSectionModel_V2):
    """Multi-trapeze channel profile version of HydPy-WQ."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        wq_model.Use_WaterDepth_V2,
        wq_model.Use_WaterLevel_V2,
        wq_model.Use_WettedArea_V1,
        wq_model.Get_WaterDepth_V1,
        wq_model.Get_WaterLevel_V1,
        wq_model.Get_WettedArea_V1,
        wq_model.Get_WettedPerimeter_V1,
    )
    ADD_METHODS = (
        wq_model.Set_WaterDepth_V1,
        wq_model.Set_WaterLevel_V1,
        wq_model.Set_WettedArea_V1,
        wq_model.Calc_WaterDepth_V1,
        wq_model.Calc_WaterDepth_V2,
        wq_model.Calc_WaterLevel_V1,
        wq_model.Calc_WettedAreas_V1,
        wq_model.Calc_WettedArea_V1,
        wq_model.Calc_WettedPerimeters_V1,
        wq_model.Calc_WettedPerimeter_V1,
        wq_model.Calc_WettedPerimeterDerivatives_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
