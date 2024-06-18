.. _HydPy-Conv:

HydPy-Conv
==========

HydPy-Conv models are no real hydrological models.  Instead, they serve as converters
that allow connecting different kinds of models providing output and requiring input
that does not fit immediately.  The most typical use case is interpolating data, which
is implemented by the application model |conv_nn| using the nearest-neighbour, by
application model |conv_idw| using the inverse distance weighted approach, and by
application model |conv_idw_ed| combining inverse distance weighting with linear
regression.

Available models:

.. toctree::
   :maxdepth: 1

   conv
   conv_nn
   conv_idw
   conv_idw_ed
