# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
.. _`issue 91`: https://github.com/hydpy-dev/hydpy/issues/91

|ga_garto_submodel1| satisfies the |SoilModel_V1| interface and works like the
stand-alone model |ga_garto|, although slight deviations are possible depending on
how the main model calls the different interface methods.  |ga_garto_submodel1| is the
first submodel implemented into the *HydPy* framework.  Hence, we discussed its
development extensively in `issue 91`.  For concrete application examples and further
information, see the documentation of method |lland_model.Calc_BoWa_SoilModel_V1| and
the integration tests :ref:`lland_dd_acker_garto` of application model |lland_dd| and
:ref:`lland_knauf_acker_heavy_garto_daily` of application model |lland_knauf|.
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *

# ...from ga
from hydpy.models.ga import ga_control
from hydpy.models.ga import ga_model


ADDITIONAL_CONTROLPARAMETERS = (ga_control.NmbSoils,)


class Model(ga_model.Base_SoilModel_V1):
    """|ga_garto_submodel1.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="GA-GARTO-Sub1",
        description=(
            "submodel for calculating the Green-Ampt / Talbot-Ogden infiltration with "
            "redistribution"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        ga_model.Set_InitialSurfaceWater_V1,
        ga_model.Set_ActualSurfaceWater_V1,
        ga_model.Set_SoilWaterSupply_V1,
        ga_model.Set_SoilWaterDemand_V1,
        ga_model.Execute_Infiltration_V1,
        ga_model.Add_SoilWater_V1,
        ga_model.Remove_SoilWater_V1,
        ga_model.Get_Percolation_V1,
        ga_model.Get_Infiltration_V1,
        ga_model.Get_SoilWaterAddition_V1,
        ga_model.Get_SoilWaterRemoval_V1,
        ga_model.Get_SoilWaterContent_V1,
    )
    ADD_METHODS = (
        ga_model.Return_RelativeMoisture_V1,
        ga_model.Return_Conductivity_V1,
        ga_model.Return_CapillaryDrive_V1,
        ga_model.Return_DryDepth_V1,
        ga_model.Return_LastActiveBin_V1,
        ga_model.Active_Bin_V1,
        ga_model.Percolate_FilledBin_V1,
        ga_model.Shift_Front_V1,
        ga_model.Redistribute_Front_V1,
        ga_model.Infiltrate_WettingFrontBins_V1,
        ga_model.Merge_FrontDepthOvershootings_V1,
        ga_model.Merge_SoilDepthOvershootings_V1,
        ga_model.Water_AllBins_V1,
        ga_model.Withdraw_AllBins_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
