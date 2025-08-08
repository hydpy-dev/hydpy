# pylint: disable=line-too-long, unused-wildcard-import
"""

>>> from matplotlib import pyplot
>>> from hydpy.core.testtools import save_autofig
>>> def plot(example=None, save=True, add_x_y=None, **kwargs):
...     figure = model.plot(**kwargs)
...     if add_x_y is not None:
...         x, y = add_x_y
...         pyplot.plot([x, x], [y, 5.0], color=kwargs.get("color"), linestyle=":")
...         pyplot.plot([-x, -x], [y, 5.0], color=kwargs.get("color"), linestyle=":")
...     if example is not None:
...         save_autofig(f"wq_widths_{example}.png", figure=figure)

>>> from hydpy.models.wq_widths import *
>>> parameterstep()
>>> nmbwidths(2)
>>> nmbsectors(1)
>>> heights(1.0, 2.0)
>>> flowwidths(2.0, 2.0)
>>> totalwidths(3.0, 3.0)
>>> plot("rectangle")

.. image:: wq_widths_rectangle.png
   :width: 400

>>> flowwidths(0.0, 4.0)
>>> totalwidths(0.0, 6.0)
>>> plot("triangle")

.. image:: wq_widths_triangle.png
   :width: 400

>>> flowwidths(2.0, 6.0)
>>> totalwidths(2.0, 8.0)
>>> plot("one_trapeze")

.. image:: wq_widths_one_trapeze.png
   :width: 400

>>> nmbwidths(5)
>>> nmbsectors(3)
>>> heights(1.0, 3.0, 4.0, 4.0, 5.0)
>>> flowwidths(2.0, 2.0, 6.0, 8.0, 12.0)
>>> totalwidths(2.0, 2.0, 6.0, 10.0, 14.0)
>>> transitions(2, 3)
>>> plot("three_trapezes")

.. image:: wq_widths_three_trapezes.png
   :width: 400

"""

# import...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.interfaces import routinginterfaces
from hydpy.exe.modelimports import *

# ...from wq
from hydpy.models.wq import wq_control
from hydpy.models.wq import wq_model


class Model(wq_model.WidthsModel, routinginterfaces.CrossSectionModel_V1):
    """|wq_trapeze.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="WQ-Widths-Strickler",
        description=(
            "tabulated widths river profile submodel including Strickler-based "
            "calculations"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        wq_model.Use_WaterDepth_V3,
        wq_model.Use_WaterLevel_V3,
        wq_model.Get_WettedArea_V2,
        wq_model.Get_SurfaceWidth_V2,
        wq_model.Get_Discharge_V1,
        wq_model.Get_Celerity_V1,
    )
    ADD_METHODS = (
        wq_model.Set_WaterDepth_V1,
        wq_model.Set_WaterLevel_V1,
        wq_model.Calc_WaterDepth_V3,
        wq_model.Calc_WaterLevel_V2,
        wq_model.Calc_Index_Excess_Weight_V1,
        wq_model.Calc_FlowWidths_V1,
        wq_model.Calc_TotalWidths_V1,
        wq_model.Calc_TotalWidth_V1,
        wq_model.Calc_FlowAreas_V1,
        wq_model.Calc_TotalAreas_V1,
        wq_model.Calc_FlowPerimeters_V1,
        wq_model.Calc_FlowPerimeterDerivatives_V1,
        wq_model.Calc_FlowArea_V1,
        wq_model.Calc_TotalArea_V1,
        wq_model.Calc_Discharges_V2,
        wq_model.Calc_Discharge_V3,
        wq_model.Calc_DischargeDerivatives_V2,
        wq_model.Calc_DischargeDerivative_V2,
        wq_model.Calc_Celerity_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    @importtools.define_targetparameter(wq_control.BottomSlope)
    def prepare_bottomslope(self, bottomslope: float) -> None:
        """Set the bottom's slope (in the longitudinal direction) [-].

        >>> from hydpy.models.wq_widths_strickler import *
        >>> parameterstep()
        >>> model.prepare_bottomslope(0.01)
        >>> bottomslope
        bottomslope(0.01)
        """
        self.parameters.control.bottomslope(bottomslope)


tester = Tester()
cythonizer = Cythonizer()
