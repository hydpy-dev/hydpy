.. _HydPy-Meteo:

HydPy-Meteo
===========

The `HydPy-Meteo` model family provides models that calculate meteorological factors.
One example is |meteo_v001|, which calculates global and clear sky solar radiation.
Application models of other model families, for example, |evap_fao56|, require such
factors as input.  Users can either prepare the complete time series of these factors
during preprocessing and let |evap_fao56| read them from files before or during a
simulation or couple |meteo_v001| and |evap_fao56| to calculate global and clear sky
radiation "on the fly".

Base model:

.. toctree::
   :maxdepth: 1

   meteo

Application models:

.. toctree::

   meteo_v001 (global radiation, FAO) <meteo_v001>
   meteo_v002 (sunshine duration, FAO) <meteo_v002>
   meteo_v003 (global radiation, LARSIM) <meteo_v003>
   meteo_v004 (sunshine duration, LARSIM) <meteo_v004>
   Meteo-Temp-IO <meteo_temp_io>
   Meteo-Precip-IO <meteo_precip_io>
