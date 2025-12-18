.. _HydPy-Snow:

HydPy-Snow
==========

The HydPy-Snow model family aims to calculate snow-related processes.  It is still in
its early stages and currently only provides CemaNeige models.  These must be applied
in a stand-alone manner, and their output can be passed (a little inconveniently via
nodes) to hydrological models that lack a built-in snow module (those of the HydPy-G
model family).  We plan to turn the existing members of HydPy-Snow into "real"
submodels in HydPy 7 and also extract the existing snow modules of other main models
(HydPy-H, HydPy-L, and HydPy-WHMod) into HydPy-Snow.  If everything works well, HydPy
7 will provide the same flexibility regarding combining main models with snow submodels
as HydPy 6 does for combining main models with evapotranspiration submodels.

Base model:

.. toctree::
   :maxdepth: 1

   snow


Application models:

.. toctree::
   :maxdepth: 1

   snow_cn
   snow_cn_minmax
