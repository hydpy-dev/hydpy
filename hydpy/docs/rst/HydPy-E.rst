.. _HydPy-E:

HydPy-E (Evap)
==============

The purpose of `HydPy-E` model family is to calculate potential
evapotranspiration (PET).  While application models like |lland_v1|
calculate potential evaporation on their own, it seems preferable to
separate the PET calculations from the more model-specific process
equations to increase flexibility.  This strategy  allows, for example,
to combine the "LARSIM" process equations of application model |lland_v2|
with different types of PET calculatable by the available |evap| models.

As a start, we provide application model |evap_v001| for calculating the
FAO reference evapotranspiration.

Base model:

.. toctree::
   :maxdepth: 1

   evap

Application model:

.. toctree::

   evap_v001
