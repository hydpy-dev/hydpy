.. _HydPy-Meteo:

HydPy-Meteo
===========

The `HydPy-Meteo` model family provides models that calculate meteorological factors.
One example is |meteo_glob_fao56|, which calculates global and clear sky solar
radiation.  Application models of other model families, for example, |evap_ret_fao56|,
require such factors as input.  Users can either prepare the complete time series of
these factors during preprocessing and let |evap_ret_fao56| read them from files before
or during a simulation or couple |meteo_glob_fao56| and |evap_ret_fao56| to calculate
global and clear sky radiation "on the fly".

Available models:

.. toctree::
   :maxdepth: 1

   meteo
   meteo_glob_io
   meteo_clear_glob_io
   meteo_psun_sun_glob_io
   meteo_temp_io
   meteo_precip_io
   meteo_glob_fao56
   meteo_glob_morsim
   meteo_sun_fao56
   meteo_sun_morsim
