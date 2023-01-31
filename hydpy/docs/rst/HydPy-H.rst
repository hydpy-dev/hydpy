
.. _HydPy-H:

HydPy-H (HBV)
=============

*HydPy* implements a very close emulation of the central routines of the famous
HBV96 model, introduced by :cite:t:`ref-Lindstrom1997HBV96`.  As discussed by
:cite:t:`ref-Tyralla2013`, the results of version 1 application models of
HydPy-H and the IHMS-HBV96 implementation of the Swedish Meteorological and
Hydrological Institute agree very well for the tested river basins. This
documentation focusses on technical aspects of HydPy-H and tries to be as
precise as possible regarding the implementation of the process equations.  The
background of the scientifical development of the HBV96 model is more
thoroughly covered in :cite:t:`ref-Lindstrom1997HBV96`.

HydPy-H is divided into two base models, which can be used to compile different
application models:

.. toctree::
   :maxdepth: 1

   hland (HydPy-H-Land) <hland>
   hbranch (HydPy-H-Branch) <hbranch>

So far the following application models are compiled:

.. toctree::
   :maxdepth: 1

   hland_v1 (HBV96) <hland_v1>
   hland_v2 (HBV96-SC) <hland_v2>
   hland_v3 (HBV96-SC/PREVAH) <hland_v3>
   hland_v4 (HBV96-SC/COSERO) <hland_v4>
   hbranch_v1 (HBV96) <hbranch_v1>

All these application models are stand-alone models, which can be combined
freely with all other models implemented in *HydPy*.
