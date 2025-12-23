# pylint: disable=unused-wildcard-import
"""
|wq_trapeze_strickler| is a stateless submodel that requires information on the current
water level or depth from its main model (usually a routing model).  It returns the
corresponding discharge and related properties, such as the kinematic wave celerity.
See the documentation on the application model |musk_mct|, which shows how to use
|wq_trapeze_strickler| in practice.  Also, please see the documentation on the related
application model |wq_trapeze|, which also relies on stacket and symmetric trapezes but
does not include discharge calculations.

|wq_trapeze| and |wq_trapeze_strickler| offer the same plotting functionalities.  To
avoid redundancies, we give a single example for |wq_trapeze_strickler| and refer you
to the documentation on |wq_trapeze| for further details:

>>> from hydpy.core.testtools import save_autofig
>>> from hydpy.models.wq_trapeze_strickler import *
>>> parameterstep()
>>> nmbtrapezes(3)
>>> bottomlevels(1.0, 3.0, 4.0)
>>> bottomwidths(2.0, 0.0, 2.0)
>>> sideslopes(0.0, 2.0, 2.0)
>>> derived.trapezeheights.update()
>>> derived.slopewidths.update()
>>> figure = model.plot()
>>> save_autofig(f"wq_trapeze_strickler_three_trapezes.png", figure=figure)

.. image:: wq_trapeze_strickler_three_trapezes.png
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


class Model(wq_model.TrapezeModel, routinginterfaces.CrossSectionModel_V1):
    """|wq_trapeze_strickler.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="WQ-Trapeze-Strickler",
        description=(
            "multi-trapeze river profile submodel including Strickler-based "
            "calculations"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        wq_model.Use_WaterDepth_V1,
        wq_model.Use_WaterLevel_V1,
        wq_model.Get_WettedArea_V1,
        wq_model.Get_SurfaceWidth_V1,
        wq_model.Get_Discharge_V1,
        wq_model.Get_Celerity_V1,
    )
    ADD_METHODS = (
        wq_model.Set_WaterDepth_V1,
        wq_model.Set_WaterLevel_V1,
        wq_model.Calc_WaterDepth_V1,
        wq_model.Calc_WaterLevel_V1,
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

    @importtools.define_targetparameter(wq_control.BottomSlope)
    def prepare_bottomslope(self, bottomslope: float) -> None:
        """Set the bottom's slope (in the longitudinal direction) [-].

        >>> from hydpy.models.wq_trapeze_strickler import *
        >>> parameterstep()
        >>> model.prepare_bottomslope(0.01)
        >>> bottomslope
        bottomslope(0.01)
        """
        self.parameters.control.bottomslope(bottomslope)


tester = Tester()
cythonizer = Cythonizer()
