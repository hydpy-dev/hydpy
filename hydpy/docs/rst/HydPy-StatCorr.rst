.. _HydPy-StatCorr:

HydPy-StatCorr
==============

All HydPy-StatCorr models deal with the statistical correction of simulated values
based on observed values, for example, to improve forecasts.  The models are
designed for different kinds of variables, and the submodels complying with the
|OutputCorrModel_V1| interface are not restricted to a specific variable.  However,
the currently available application model |statcorr_main| focuses on discharge: it
reads the simulated discharge from its inlet node(s), passes it through one or more
|OutputCorrModel_V1| submodels, and delivers the corrected discharge to its outlet
node.  |statcorr_arima010| is such a submodel; it estimates the correction from an
ARIMA(0,1,0) error model, following the LARSIM approach.

Available models:

.. toctree::
   :maxdepth: 1

   statcorr
   statcorr_main
   statcorr_arima010
