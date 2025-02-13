
.. _LARSIM: http://www.larsim.info/1/the-model/

.. _model_families:

Model Families
==============

HydPy divides all models into "families" as :ref:`HydPy-L`.  Each model family consists
of one base model (e.g. |lland|) and several application models (e.g. |lland_dd|).  The
base models offer basic features like model parameter classes (e.g.
|lland_control.KG|), sequence classes (e.g. |lland_fluxes.NKor|) and process equation
methods (e.g. |lland_model.Calc_NKor_V1|) but cannot perform an actual simulation run.
This is the task of the application models, which select different parameters,
sequences, and process equations in a meaningful combination and order.


Unless otherwise stated, you can freely combine all models and apply them with
arbitrary simulation time steps.  It is, for example, possible to simulate "land
processes" with |hland_96|, "stream processes" with |musk_mct|, and "lake processes"
with |dam_llake| in either a daily or hourly time step.

Base models often offer different versions of a method to calculate the value of the
same variable.  For example, base model |evap| has two methods for estimating reference
evapotranspiration: |evap_model.Calc_ReferenceEvapotranspiration_V1| and
|evap_model.Calc_ReferenceEvapotranspiration_V2|.  Each application model that wants to
calculate reference evapotranspiration has to choose. In this case, |evap_ret_fao56|
selects |evap_model.Calc_ReferenceEvapotranspiration_V1| to follow
:cite:t:`ref-Allen1998` and  |evap_ret_tw2002| selects
|evap_model.Calc_ReferenceEvapotranspiration_V2| to follow :cite:t:`ref-DVWK`:

>>> from hydpy.models.evap_ret_tw2002 import *
>>> parameterstep("1d")
>>> assert hasattr(model, "calc_referenceevapotranspiration_v2")
>>> assert not hasattr(model, "calc_referenceevapotranspiration_v1")

For simplicity, the selected method is also accessible without the version suffix (as
long as the model does not choose multiple versions of the same method, which is a
HydPy convention only seldom broken by application models):

>>> assert hasattr(model, 'calc_referenceevapotranspiration_v2')

Methods define their parameter and sequence requirements.  Due to choosing
|evap_model.Calc_ReferenceEvapotranspiration_V2|, application model |evap_ret_tw2002|
possesses, for example, the flux sequence |evap_fluxes.ReferenceEvapotranspiration|:

>>> assert hasattr(model.sequences.fluxes, 'referenceevapotranspiration')

Due to this selection mechanism, it is relatively easy to compose new models based on
existing or alternative methods.  However, such compositions are restricted to using
methods of only one base model or model family.  To overcome this limitation, HydPy
also implements the so-called "submodel concept", which brings another kind of
flexibility by coupling main models (of one model family) with submodels (of the same
or another model family).  This section describes both the main and the submodels.  See
the :ref:`model_overview` section, which clarifies this distinction more clearly.


.. toctree::
   :hidden:

   HydPy-ARMA
   HydPy-Conv
   HydPy-Exch
   HydPy-Evap
   HydPy-Dam
   HydPy-Dummy
   HydPy-G
   HydPy-GA
   HydPy-H
   HydPy-KinW
   HydPy-L
   HydPy-Meteo
   HydPy-Musk
   HydPy-Rconc
   HydPy-SW1D
   HydPy-Test
   HydPy-W
   HydPy-WQ
