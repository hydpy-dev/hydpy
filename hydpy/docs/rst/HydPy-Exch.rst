.. _HydPy-Exch:

HydPy-Exch
==========

The HydPy-Exch model family enables instances of other model types to exchange data
more flexibly.

Usually, model instances eventually receive inflow and pass outflow to other models
without knowing anything about them.  One exception is the highly specialised
application model |dam_v004|, which calculates its discharge to a |dam_v005| instance
based on some knowledge of the other model's internal state.  One purpose of HydPy-Exch
is to facilitate similar exchanges between different model instances more modularly.
Application model |exch_weir_hbv96|, for example, simulates a weir.  Conceptually, it
enables a bidirectional water exchange between two lakes, where the flow direction
depends on the difference of the lakes' water levels.  Technically, we can combine
|exch_weir_hbv96| with all model types, calculating (something like) water level
information and accepting an additional inlet that can supply positive and negative
values.  Due to this flexible approach, we do not need to implement the weir formula
for different |dam| models.  On the downside, this looser coupling often comes with
some limitations.  One example is numerical accuracy, which might be suboptimal due to
solving the interconnected differential equations of different model instances
sequentially (we might improve this later).

Besides such explanation-requiring models, HydPy-Exch also provides more
straightforward models.  |exch_branch_rules| distributes its inflow to multiple
locations, |exch_branch_io| withdraws water from or supplies water to a stream, and
the submodel |exch_water_transfer_io| does the same for lake models like |dam_llake|
and |dam_lreservoir|.  The latter two exchange models follow requested water transfers (for
example, read from files) and fall back on interpolation rules where requests are
missing.  |exch_branch_hbv96| is deprecated and will be removed in HydPy 8.0 (please
use |exch_branch_rules| instead; you can convert existing models with method
|exch_branch_hbv96.Model.convert_2_exch_branch_rules|).

Available models:

.. toctree::
   :maxdepth: 1

   exch
   exch_branch_hbv96
   exch_branch_io
   exch_branch_rules
   exch_interp
   exch_water_transfer_io
   exch_waterlevel
   exch_weir_hbv96
