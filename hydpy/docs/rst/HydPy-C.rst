.. _HydPy-C:

HydPy-C (Conv)
==============

`HydPy-C` models are no real hydrological models.  Instead, they serve as
converters that allow connecting different kinds of models providing output
and requiring input that does not fit immediately.  The most typical use
case is interpolating data, which is implemented by the application model
|conv_v001| using the nearest-neighbour and by application model |conv_v002|
using the inverse distance weighted approach.

Base model:

.. toctree::
   :maxdepth: 1

   conv

Application model:

.. toctree::

   conv_v001
   conv_v002