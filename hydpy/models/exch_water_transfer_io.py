# pylint: disable=unused-wildcard-import
"""
.. _`LARSIM`: http://www.larsim.de/en/the-model/

|exch_water_transfer_io| is a submodel that adds a water transfer feature to
"storage-type" main models like |dam_llake| and |dam_lreservoir|.  These transfers can
be positive (withdrawal from the storage) or negative (supply to the storage).

|exch_water_transfer_io|'s design agrees with `LARSIM`_'s storage branching routine
VSPE.  It takes the requested transfer from the input sequence
|exch_inputs.RequestedTransfer| or, when no such external request is available
(indicated preferably by |numpy.inf| or alternatively by |numpy.nan|), from
volume-dependent interpolation rules defined by parameter |VolTransferRules|.  All
withdrawals, whether externally requested or rule-based, are restricted to a
dynamically updated maximum discharge, which for |dam_llake| and |dam_lreservoir|
follows from the allowed water level drop.  Externally requested withdrawals and
supplies are also limited by the water volume thresholds |MinVol| and |MaxVol|,
respectively.  |VolTransferRules|, |MinVol|, and |MaxVol| (and |VolTol|, see below) can
vary seasonally.

|exch_water_transfer_io| connects to its own outlet node, to which it passes the
determined water transfer.  If parameter |KeepWaterBalance| is |True|, this water
transfer always reflects the actual, storage-effective transfer.  However, if
|KeepWaterBalance| is |False|, |exch_water_transfer_io| passes available external
requests unmodified, even if real withdrawal from or supply to the main model had to
be reduced (justified by regarding them as measured and thus more certain than
simulation results).

Note the tolerance parameters |VolTol| and |QTol|, which let |exch_water_transfer_io|
react smoothly to the volume- and discharge-based restrictions mentioned above.  This
can make simulation results more realistic and the numerical solving of the main
model's ordinary differential equations more efficient (explained in more detail in
the :ref:`dam_v001_smooth_near_minimum` example of |dam_v001|).

The :ref:`dam_llake_water_transfer` example of |dam_llake| and the
:ref:`dam_lreservoir_water_transfer` example of |dam_lreservoir| show how to apply
|exch_water_transfer_io|.
"""

from hydpy.exe.modelimports import *
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.core import modeltools
from hydpy.interfaces import transferinterfaces
from hydpy.models.exch import exch_model


class Model(modeltools.AdHocModel, transferinterfaces.TransferModel_V1):
    """|exch_water_transfer_io.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Water-Transfer-IO",
        description=(
            "submodel for transferring water based on external requests or "
            "volume-dependent rules"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        exch_model.Determine_Transfer_V1,
        exch_model.Get_Transfer_V1,
        exch_model.Set_Transfer_V1,
    )
    ADD_METHODS = (exch_model.Return_AllowedTransfer_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
