
.. _model_overview:

Model overview
==============

This section briefly introduces in HydPy's model collection, separating it into the
available :ref:`main models <main_models>` and :ref:`submodels <submodels>`. Beginners
should first become familiar with the main models, which open up various ways of
targeting general processes or process groups (click :ref:`here <main_model>` for more
details).  Submodels, in contrast, are a means of configuring specific subprocesses or
subprocess aspects (click :ref:`here <submodel>` for more information).

The following subsections group the available :ref:`model families <model_family>` by
their purpose and briefly outline exemplary :ref:`application models
<application_model>`.  For a thorough explanation of all available models, see the
reference guide's :ref:`model_families` section.

When planning the first more complex HydPy projects, we advise looking at the submodel
graph which attempts to list all sensible main and submodel combinations:

.. submodel_graph::

.. _main_models:

Main models
___________

In HydPy, many main models represent hydrological processes, but there are also those
serving more technical tasks.

.. _land_models:

Land models
-----------

Our `land models` simulate processes like runoff generation and concentration.  You can
choose different land models for different subbasins, which helps to more closely
approximate the processes of large catchments that extend over several natural areas.
Usually, land models support the further distribution of a subbasin in hydrological
response units, snow classes, or the like.

There are currently four land model families.

:ref:`HydPy-H` follows the ideas and terminology of the wordwide applied HBV model.
Besides |hland_96|, which implements the original HBV96 model
:cite:p:`ref-Lindstrom1997HBV96`, :ref:`HydPy-H` provides combination models.
|hland_96p| contains components of the HBV-like model PREVAH
:cite:p:`ref-Viviroli2009PREVAH`, and |hland_96c| of the HBV-like model COSERO
:cite:p:`ref-Kling2005,ref-Kling2006`.

:ref:`HydPy-L` provides replicas of the LARSIM model :cite:p:`ref-LARSIM`, which many
European flood forecasting services use.  While application model |lland_dd| relies on
the simple day-degree method, |lland_knauf| uses more complex energy balance
calculations for simulating snow processes.

:ref:`HydPy-W` closely emulates the WALRUS model :cite:p:`ref-Brauer2014`, designed to
simulate surface water fluxes in lowland catchments influenced by near-surface
groundwater.  Application model |wland_wag| extends the original WALRUS concept by
providing additional options regarding the spatial distribution of processes and the
handling of mildly hilly terrain.

:ref:`HydPy-G` provides members of the very simple and handy `modèle due Génie Rural`
model series, of which GR4J is likely the most prominent.  Our application models
|gland_gr4|, |gland_gr5|, and |gland_gr6| closely emulate and slightly extend the GR4J
:cite:p:`ref-Perrin2003`, GR5J :cite:p:`ref-Moine2008`, and GR6J
:cite:t:`ref-Pushpalatha2011` implementations of the R package airGR
:cite:p:`ref-airGR2017`.

:ref:`HydPy-WHMod` is the primary implementation of the SVAT model WHMod
:cite:p:`ref-Probst2002`.  It stands out from the other model families by focusing more
on water balance and groundwater recharge aspects of individual sites than on
simulating the discharge of entire river basins.  The application model |whmod_rural|
is designed to perform water balance analyses for rural areas, while |whmod_urban| also
considers water management measures relevant to urban areas.

.. _stream_models:

Stream models
-------------

The `stream models` simulate water and wave movement through rivers and channels.  They
might consider overbank flow in a simplified manner but generally implement
1-dimensional hydrological or hydrodynamical routing methods.  You can choose the
stream model type independently from the preferred land model type and combine
different stream model types in one :ref:`project`.

There are currently four stream model families.

:ref:`HydPy-Musk` makes several Muskingum routing methods available.  |musk_classic|
implements the original three-parameter approach of :cite:t:`ref-McCarthy1940` and also
provides options for emulating the simplified two-parameter approach of HBV96
:cite:p:`ref-Lindstrom1997HBV96`.  In contrast, |musk_mct| does not rely on calibration
parameters but calculates the required coefficients dynamically based on the channel
properties following the Muskingum-Cunge approach as modified by
:cite:t:`ref-Todini2007`.

:ref:`HydPy-ARMA` provides the second traditional branch of hydrological routing
methods, which approximate the nonlinear routing processes by equation sets that follow
the moving average approach (MA) or mixtures of autoregressive and moving average
approaches (ARMA).  |arma_rimorido| allows defining distinct equation sets for
different discharge rates to better cope with nonlinearities related to processes like
overbank flow.  One can determine the required coefficients manually or use widely
applied response functions like the |TranslationDiffusionEquation| or the
|LinearStorageCascade|.

:ref:`HydPy-SW1D` solves the 1-dimensional shallow water equations more
hydrodynamically, which increases complexity and computation time but allows backwater
effects to be taken into account.  So, you may consider it when working in a lowland
region.  The main model |sw1d_channel| and its companion |sw1d_network| are highly
configurable by adding submodels, which are also members of :ref:`HydPy-SW1D` (see
below).

:ref:`HydPy-KinW` contains storage-based routing methods that rely on simplifying
kinematic wave assumptions.  |kinw_williams| and |kinw_williams_ext| are both related
to the :cite:t:`ref-Williams1969` method in the sense of its implementation in the
LARSIM model :cite:p:`ref-LARSIM` but differ in |kinw_williams| using explicit channel
geometries and |kinw_williams_ext| using preprocessed storage-discharge relationships.
Before deciding to use any of its members, please read the current development status
of :ref:`HydPy-KinW`, as we are likely to introduce some breaking changes soon.

.. _lake_models:

Lake models
-----------

`Lake model` instances are often interposed between two `stream model` instances to
simulate the damping effects lakes impose on the propagation of flood waves.  Moreover,
the various lake model types provide flow regulation and water transfer
functionalities.

:ref:`HydPy-Dam` implements all available `lake models`. The application models
|dam_llake|, |dam_lretention|, and |dam_lreservoir| agree with the LARSIM options
"SEEG", "RUEC", and "TALS" for simulating controlled lakes, retention basins, and
reservoirs :cite:p:`ref-LARSIM`. |dam_pump|, |dam_sluice|, and |dam_pump_sluice| serve
to simulate the drainage of lowlands via active pumping and sluice-controlled free
flow.  The applications models |dam_v001| to |dam_v005| (which we might replace with a
single, more flexible model type in the future) cover more complex dam and reservoir
functionalities, including water transfers between model instances.

.. _exchange_models:

Exchange models
---------------

Our `exchange models` enable flexible (material and informational) data exchanges
between model instances of other types and are often helpful to simulate water
management measures.

:ref:`HydPy-Exch` implements all available `exchange models`.  |exch_branch_hbv96| and
|exch_weir_hbv96| both closely emulate functionalities of HBV96
:cite:p:`ref-Lindstrom1997HBV96`.  |exch_branch_hbv96| takes inflow (for example, from
a single upstream `stream model` instance) and distributes it to multiple locations
downstream (for example, to two downstream `stream model` instances).
|exch_weir_hbv96| is a highly specialised model which allows for bidirectional flow
between two other model instances (usually lake model instances) depending on the
current water level gradient.

Note that :ref:`HydPy-Exch` also provides submodels like
|exch_waterlevel| (see below).

.. _interpolation_models:

Interpolation models
--------------------

Users can decide whether to provide preprocessed meteorological input time series for
all individual subbasins or to interpolate station data to subbasin geometries "on the
fly" during simulation runs.  HydPy supplies different types of `interpolation models`
for the latter case.

:ref:`HydPy-Conv` implements three interpolation methods: nearest-neighbour
(|conv_nn|), inverse distance weighting (|conv_idw|), and a combination of inverse
distance weighting and linear regression, somehow similar to External Drift Kriging
(|conv_idw_ed|).

.. _submodels:

Submodels
_________

Submodels allow users to include additional subprocesses, select among different
subprocess descriptions, or modify their main models' behaviour in other ways.

Meteorological models
---------------------

Some submodels (especially those concerned with calculating evapotranspiration) require
meteorological input data and can take it from different sources: from their main
models (if provided), from a sub-submodel that reads it from files, or from a
sub-submodel that calculates it on demand.  The `meteorology models` cover the two
latter cases.

:ref:`HydPy-Meteo` provides all these submodels.  For the second case, there are those
"io submodels" that handle individual factors like |meteo_temp_io| (air temperature),
|meteo_precip_io| (precipitation), and |meteo_glob_io| (global radiation), and those
submodels that supply a group of related factors like |meteo_clear_glob_io| (clear sky
solar radiation and global radiation) and |meteo_psun_sun_glob_io| (potential sunshine
duration, actual sunshine duration, and global radiation).  For the third case, there
are those "real submodels" like |meteo_glob_fao56|, |meteo_sun_fao56|,
|meteo_glob_morsim|, and |meteo_sun_morsim| that calculate global radiation and
sunshine duration (and related properties) following different methodologies.

Evapotranspiration models
-------------------------

HydPy's `evapotranspiration models` are all submodels, although some also work as
special-purpose main models.  We divide them into those calculating and reference
evapotranspiration (RET), potential evapotranspiration (PET), and actual
evapotranspiration (AET).

Note there is a strict technical separation between the AET on the one side and the RET
and PET models on the other, but only a lax nominal separation between the RET and PET
models.  This means it is always clear if a main model requires an AET submodel, but a
RET model like |evap_ret_io| technically also works for a main model requiring a PET
submodel.  It is up to the user to check if a contemplated combination makes sense from
the hydrological perspective.

:ref:`HydPy-Evap` provides all available `evapotranspiration models`.

|evap_ret_io| supplies its main model with externally processed reference (or, as
discussed above, potential) evapotranspiration estimates.  |evap_ret_fao56| and
|evap_ret_tw2002|, on the other hand, calculate the reference evapotranspiration
autonomously following :cite:t:`ref-Allen1998` and :cite:t:`ref-DVWK`, respectively.

There are two groups of PET models.  |evap_pet_hbv96| and |evap_pet_ambav1| calculate
the potential evapotranspiration in agreement with the HBV96 model
:cite:p:`ref-Lindstrom1997HBV96` and version 1.0 of the AMBAV model
:cite:p:`ref-Löpmeier2014`, whereas |evap_pet_m| and |evap_pet_mlc| require reference
evapotranspiration estimates of a RET sub-submodel and adjust them according the
current month and, in the case of |evap_pet_mlc|, also to the land cover of the
respective hydrological response units.

There are also two groups of AET models.  |evap_aet_morsim| calculates the actual
evapotranspiration autonomously based on the LARSIM implementation :cite:p:`ref-LARSIM`
of the MORECS model :cite:p:`ref-Thompson1981`, while |evap_aet_hbv96| and
|evap_aet_minhas| adjust potential evapotranspiration estimates, provided by a
sub-submodel, to the catchment's wetness as suggested by
:cite:t:`ref-Lindstrom1997HBV96` and :cite:t:`ref-Minhas1974`.

Infiltration models
-------------------

HydPy's features for modifying infiltration processes via submodels are still in their
infancy.  So far, there is only the `infiltration model` |ga_garto_submodel1| of the
model family :ref:`HydPy-GA`, which works in combination with |lland_dd| and
|lland_knauf| to extend the volume-based infiltration method of LARSIM, taken from the
Xinaniang model :cite:p:`ref-zhao1977flood`, with an intensity-based infiltration
method, a modern version of the Green-Ampt method :cite:p:`ref-Lai2015`, to improve the
simulation of runoff generation during high-intensity rainfall.  |ga_garto_submodel1|
is well-tested and works as desired.  Still, we might improve its coupling to the
mentioned main models later (and eventually allow its coupling to other `land models`
afterwards).

Runoff concentration models
---------------------------

All `runoff concentration models` deal with the time delay between the generation of
fast runoff within a subbasin and its occurrence at the subbasin's outlet (in other
words, the conversion of effective precipitation to direct runoff).

:ref:`HydPy-Rconc` provides two submodels that allow configuring runoff concentration
in different ways.  |rconc_nash| implements the Nash cascade and relies on explicitly
modelled storage contents.  |rconc_uh|, on the other hand, implements the Unit
Hydrograph approach, which ordinates that can be set freely or, more convenience,
following the simplifying assumptions of HBV96 :cite:p:`ref-Lindstrom1997HBV96` and
GR4J :cite:p:`ref-Perrin2007`.

Routing models
--------------

All `routing models` provide means to fine-tune the water movement within rivers and
channels.  As to be expected, many are potential `stream model` submodels.  Others fit
to  `land models` and control the routing of a subbasin's discharge into the stream
network.

The submodels of :ref:`HydPy-SW1D` are specially designed to be used by |sw1d_channel|
and |sw1d_network| (see above).  |sw1d_lias| can be viewed as the core routing model,
which implements the "local inertial approximation of the shallow water equations"
:cite:p:`ref-Bates2010`, whereas |sw1d_storage| generally serves to update the water
balance of individual stream sections.  Most of the other submodels serve to include
hydraulic structures like sluices |sw1d_lias_sluice|, pumping stations |sw1d_pump|,
weirs |sw1d_weir_out|, and gates |sw1d_gate_out|.

:ref:`HydPy-WQ` provides more general "function-like" submodels that calculate
discharge or related factors based on water level information or the other way round.
|wq_trapeze| and |wq_trapeze_strickler| are channel profile models that approximate a
real channel geometry by an arbitrary number of trapezes, with |wq_trapeze_strickler|
providing additional variables based on the Manning-Strickler equation.  |wq_walrus|,
however, determines a subbasin's discharge over a weir into a stream network in
agreement with the WALRUS model :cite:p:`ref-Brauer2014`.
