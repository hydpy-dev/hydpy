.. _HydPy-C:

HydPy-C (Conv)
==============

`HydPy-C` models are no real hydrological models.  Instead, they serve as
converters that allow connecting different kinds of models providing output
and requiring input that does not fit immediately.  The most typical use
case is interpolating data, which is implemented by the application model
|conv_v001| using the nearest-neighbour, by application model |conv_v002|
using the inverse distance weighted approach, and by application model
|conv_v003| combining inverse distance weighting with linear regression.

Base model:

.. toctree::
   :maxdepth: 1

   conv

Application model:

.. toctree::
   :maxdepth: 1

   conv_v001
   conv_v002
   conv_v003