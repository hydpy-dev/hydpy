
.. _HydPy-H:

HydPy-H (HBV)
=============

HydPy implements a very close emulation of the central routines of
the famous HBV96 model, introduced by Lindstroem et al
:cite:`ref-LINDSTROM1997272`.
As discussed in :cite:`ref-Tyralla2013`, the results of
version 1 application models of HydPy-H and the IHMS-HBV96
implementation of the Swedish Meteorological and Hydrological Institute
agree very well for the majority of the tested river basins [#f1]_.
This documentation focusses on technical aspects of HydPy-H and tries
to be as precise as possible regarding the implementation of the
process equations.  The background of the scientifical development of
the HBV96 model is more thoroughly covered in Lindstroem et al
:cite:`ref-LINDSTROM1997272`.

HydPy-H is divided into three base models, which can be used to compile
different application models:

.. toctree::
   :maxdepth: 1

   hland (HydPy-H-Land) <hland>
   hstream (HydPy-H-Stream) <hstream>
   hbranch (HydPy-H-Branch) <hbranch>

So far the following application models are compiled:

.. toctree::

   hland_v1 (HBV96 version of HydPy-H-Land) <hland_v1>
   hstream_v1 (HBV96 version of HydPy-H-Stream) <hstream_v1>
   hbranch_v1 (HBV96 version of HydPy-H-Branch) <hbranch_v1>

All these application models are stand-alone models, which can be
combined freely with all other models implemented in HydPy.

.. rubric:: Footnotes

.. [#f1] Unfortunately, the report :cite:`ref-Tyralla2013`
  is only available in German so far.  But inspecting pictures 2.2 to 2.11
  should be instructive nonetheless. The simulated runoff values are
  virtuelly identical for catchments in high and low mountain ranges as
  well as in lowland areas (pictures 2.2 to 2.5).  The same is true for
  all internal states, beginning with the interception storage (picture 2.6)
  and ending with the lower groundwater storage (picture 2.11).  Table 2.5
  evaluates the aggreement between the results of HydPy-H and the IHMS-HBV96
  implementation of the SMHI for the whole Rhine river basin, using the
  Nash-Sutcliffe efficiency.  Relevant differences occur only within the
  Main river basin.  These differences result from implausible evaporation
  values calculated by the IHMS software.  If these is due to a bug of the
  IHMS software or due to an incorrect configuration of the HBV forecasting
  model of the German Federal Institute for Hydrology could not be clarified
  so far.
