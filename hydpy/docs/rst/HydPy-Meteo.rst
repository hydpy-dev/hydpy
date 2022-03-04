.. _HydPy-Meteo:

HydPy-Meteo
===========

The `HydPy-Meteo` model family provides models that calculate meteorological
factors.  One example is |meteo_v001|, which calculates global and clear sky
solar radiation.  Application models of other model families, for example,
|evap_v001|, require such factors as input.  Users can either prepare the
complete time series of these factors during preprocessing and let |evap_v001|
read them from files before or during a simulation, or couple |meteo_v001| and
|evap_v001| to calculate global and clear sky radiation "on the fly".

Base model:

.. toctree::
   :maxdepth: 1

   meteo

Application models:

.. toctree::

   meteo_v001 (global radiation, :cite:`ref-Allen1998`) <meteo_v001>
   meteo_v002 (sunshine duration, :cite:`ref-Allen1998`) <meteo_v002>
