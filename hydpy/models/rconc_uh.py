"""|rconc_uh| is a submodel that supports its main model by calculating runoff
concentration using the unit hydrograph approach. It allows for different unit
hydrograph shapes, which can be configured based on specific geometries or wholly
customised. One example of a specific geometry is the isosceles triangle of HBV96
:cite:p:`ref-Lindstrom1997HBV96`. See the documentation on parameter |UH| for further
information. Also, see the integration tests of application model |hland_96|, which
use |rconc_uh| as a submodel.
"""

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import rconcinterfaces
from hydpy.models.rconc import rconc_model
from hydpy.core.typingtools import *


class Model(rconc_model.Sub_RConcModel, rconcinterfaces.RConcModel_V1):
    """|rconc_uh.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Rconc-UH",
        description=(
            "Unit Hydrograph runoff concentration, compatible with HBV96 and GR4J"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        rconc_model.Set_Inflow_V1,
        rconc_model.Determine_Outflow_V1,
        rconc_model.Get_Outflow_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Return the water balance after the submodel has been executed."""

        waterbalance = self.sequences.logs.quh - initial_conditions["logs"]["quh"]

        return float(numpy.sum(waterbalance))


tester = Tester()
cythonizer = Cythonizer()
