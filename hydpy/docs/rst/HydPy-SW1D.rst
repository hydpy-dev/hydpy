
.. _HydPy-SW1d:

HydPy-SW1D (Shallow Water 1D)
=============================

All models of the `HydPy-SW1D` model family serve to solve the 1-dimensional shallow
water equations.  Opposed to models like |musk_mct|, they do so in a more
`hydrodynamical` manner, which extends their scope to situations where traditional
`hydrological` flood routing approaches fail.  Most importantly, they can account for
backwater effects.  However, this additional functionality comes at the cost of
increased complexity, as less stable numerical schemes are used, and the different
parts of a channel network must be coupled more tightly.  The application model
|sw1d_channel| documentation discusses the first and the application model
|sw1d_network| documentation discusses the second topic.

The available application models are responsible for different tasks. sw1d_channel is a
"normal" main model that is associated with |Element| object as usual.  The
particularity is that one usually does not apply |sw1d_channel| to perform simulations.
Behind the scenes, *HydPy* couples all |sw1d_channel| models (or, more precisely, the
involved submodels) belonging to the same |Element.collective| and delegates the actual
simulation work to an automatically generated |sw1d_network| instance.

By themself, |sw1d_channel| and |sw1d_network| provide little "hydrodynamical"
functionality.  Instead, they rely on submodels compatible with a finite volume
staggered grid discretisation.  First, they need submodels following the
|StorageModel_V1| interface (as |sw1d_storage|) for keeping track of the amount of
water stored in a channel segment.  Second, they need submodels for providing the
inflow into the upper segments (like |sw1d_q_in|, which follows the |RoutingModel_V1|
interface), for calculating the flow between channel segments (like |sw1d_lias|, which
follows the |RoutingModel_V2| interface), and for removing water from the lower
segments (like |sw1d_weir_out|, which follows the |RoutingModel_V3| interface).

Base model:

.. toctree::
   :maxdepth: 1

   sw1d

Application models:

.. toctree::
   :maxdepth: 1

   sw1d_channel (HydPy-SW1D-Channel) <sw1d_channel>
   sw1d_network (HydPy-SW1D-Network) <sw1d_network>
   sw1d_storage (HydPy-SW1D-Storage) <sw1d_storage>
   sw1d_q_in (HydPy-SW1D-Q-In) <sw1d_q_in>
   sw1d_lias (HydPy-SW1D-LIAS) <sw1d_lias>
   sw1d_lias_sluice (HydPy-SW1D-LIAS/Sluice) <sw1d_lias_sluice>
   sw1d_q_out (HydPy-SW1D-Q-Out) <sw1d_q_out>
   sw1d_weir_out (HydPy-SW1D-Weir-Out) <sw1d_weir_out>
   sw1d_gate_out (HydPy-SW1D-Gate-Out) <sw1d_gate_out>
