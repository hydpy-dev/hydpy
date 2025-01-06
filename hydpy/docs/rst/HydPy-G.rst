.. _HydPy-G:

HydPy-G (GR)
============

The HydPy-G model family (modèle due Génie Rural) comprises daily lumped hydrological
models that differ in their amount of parameters, in their calculation of groundwater
exchange, and partly in their calculation of runoff concentration.  Compared to the
other main models provided by HydPy, they are limited to the bare essentials.  For
example, you can apply them only "lumped", meaning there is no way to distinguish
between different types of land covers within one subcatchment.

Generally, all models follow the implementations of the R package airGR
:cite:p:`ref-airGR2017`.  However, while airGR provides models for specific simulation
time steps (e.g. GR4J for daily and GR4H for hourly steps), all members of HydPy-G are
(in principle) applicable to arbitrary simulation time steps.  Additionally, in air GR,
only some, but in HydPy-G, all models allow for configuring the interception capacity.

None of the available application models contains a snow module.  Still, you can use
the models of the members of the HydPy-Snow model family to modify precipitation
accordingly before giving it to a HydPy-G model.  (Admittedly, this is a little
cumbersome.  For more comfort, we will turn all snow models into "real" submodels in a
later HydPy version.)


Base model:

.. toctree::
   :maxdepth: 1

   gland

Application models:

.. toctree::
   :maxdepth: 1

   gland_gr4
   gland_gr5
   gland_gr6
