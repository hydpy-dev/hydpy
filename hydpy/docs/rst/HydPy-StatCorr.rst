
.. _HydPy-StatCorr:

HydPy-StatCorr
==============

All HydPy-StatCorr models deal with the statistical correction of discharge
forecasts.  The base model |statcorr| reads the simulated discharge from its inlet
node(s), passes it through one or more submodels complying with the
|OutputCorrModel_V1| interface, and delivers the corrected discharge to the outlet
node.  |statcorr_arima010| is such a submodel; it estimates the correction from an
ARIMA(0,1,0) error model, following the LARSIM approach.

Available models:

.. toctree::
   :maxdepth: 1

   statcorr
   statcorr_main
   statcorr_arima010
