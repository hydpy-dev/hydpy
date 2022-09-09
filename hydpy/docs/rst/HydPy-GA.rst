.. _HydPy-GA:

HydPy-GA (Green-Ampt)
=====================

The members of `HydPy-GA` calculate surface water infiltration into soils based on the
simplifying Green-Ampt assumption of "piston-like" wetting fronts.  Opposed to purely
volume-based approaches, they consider the influence of rainfall intensity on
infiltration and, thus, the potential generation of surface runoff.  Hence, one might
prefer them when dealing with short but intensive (often convective) rainfall events.
However, Green-Ampt methods are also usually more demanding regarding computational
effort and the required geodata and are more sensitive to data uncertainties.  Compared
with numerical approximations of the Richards equation, they are less flexible (e.g.
because of neglecting soil heterogeneities) but more stable and efficient (as they rely
on relatively simple ordinary instead of highly-stiff partial differential equations).

So far, |ga_garto| is the only `HydPy-GA` member usable as a stand-alone model.  It
implements GARTO, a "Green-Ampt infiltration with Redistribution" model that
"incorporates features from the Talbot-Ogden infiltration and redistribution method"
:cite:p:`ref-Lai2015`.  It should outperform simpler Green-Ampt approaches when
simulating complex rainfall events that include significant low-intensity subperiods.

Hydrologically, |ga_garto_submodel1| works like |ga_garto|, Technically, it is a
submodel that can hook into larger main models like |lland_v1| to include (additional)
surface runoff due to infiltration excess into simulations.

Base model:

.. toctree::
   :maxdepth: 1

   ga

Main models:

.. toctree::
   :maxdepth: 1

   ga_garto (GARTO) <ga_garto>

Submodels:

.. toctree::
   :maxdepth: 1

   ga_garto_submodel1 (GARTO/SoilModel_V1) <ga_garto_submodel1>
