.. _HydPy-Evap:

HydPy-Evap
==========

The "HydPy-Evap" model family aims to calculate potential evapotranspiration
(PET).  While application models like |lland_v1| calculate potential
evaporation on their own, it seems preferable to separate the PET calculations
from the more model-specific process equations to increase flexibility.  This
strategy allows, for example, to combine the "LARSIM" process equations of
application model |lland_v2| with different types of PET calculatable by the
available |evap| models.

As a start, we provide the application model |evap_fao56| for calculating the
FAO reference evapotranspiration.

Base model:

.. toctree::
   :maxdepth: 1

   evap

Application model:

.. toctree::

   evap_fao56 (FAO) <evap_fao>
