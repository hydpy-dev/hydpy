
.. _LARSIM: http://www.larsim.info/1/the-model/

.. _model_families:

Model Families
==============

In *HydPy*, we divide all models into "families" as :ref:`HydPy-L`.  Each model family
consists of one base model (e.g. |lland|) and several application models (e.g.
|lland_dd|).  The base models offer basic features like model parameter classes (e.g.
|lland_control.KG|), sequence classes (e.g. |lland_fluxes.NKor|) and process equation
methods (e.g. |lland_model.Calc_NKor_V1|) but cannot perform an actual simulation run.
This is the task of the application models, which select different parameters,
sequences, and process equations in a meaningful combination and order.

If not stated otherwise, all models can be freely combined and applied
on arbitrary simulation time steps.  It is, for example, possible to
simulate the "land processes" with |hland_96|, the "stream processes"
with |arma_rimorido|, the "dam processes" with |dam_v001| in either a
daily or hourly time step.

Often base models offer different versions of a method to calculate the
value of the same variable.  For example, base model |dam| offers two
methods for picking its |dam_fluxes.Inflow|: |dam_model.Pic_Inflow_V1|
and |dam_model.Pic_Inflow_V2|.  Each application model has to select a
specific version of the method.  Exemples here are application model
|dam_v001| selecting |dam_model.Pic_Inflow_V1| and application model
|dam_v005| selecting |dam_model.Pic_Inflow_V2|.  The following example
shows this for application model |dam_v005|:

>>> from hydpy.models.dam_v005 import *
>>> parameterstep('1d')
>>> hasattr(model, 'pic_inflow_v2')
True
>>> hasattr(model, 'pic_inflow_v1')
False

For simplicity, you can skip the version number when trying to access
a certain method of an application model:

>>> hasattr(model, 'pic_inflow')
True

Note that this way to construct different application models is very
different from the usual design of hydrological models, where only
one model exists.  Here it is the responsibility of the user to combine
different possible methods in a meaningful combination, usually via
setting some options in configuration files.

In the light of experience that model users are often overstrained with
such decisions when using complex models and that it is often very hard to
communicate (and remember) all selected settings, we favour the more
reliable "application model" approach.  This allows the model developer to
carefully check the combination of methods he selected by himself
in thorough integration tests.  And it allows him to document how he
thinks the application model should actually be used.  On the downside,
eventually many application models must be compiled in order to support
different combinations of methods.  To keep this problem small, newly
implemented models should be kept small.  But this also depends on
other design decisions (e.g. how process equations are numerically solved)
and will have to be discussed later.

.. toctree::
   :hidden:

   HydPy-ARMA
   HydPy-Conv
   HydPy-Exch
   HydPy-Evap
   HydPy-Dam
   HydPy-Dummy
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
