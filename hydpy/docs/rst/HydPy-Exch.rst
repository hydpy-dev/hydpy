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
Application model |exch_weir_hbv96|, for example, simulates a weir.  Conceptionally, it
enables a bidirectional water exchange between two lakes, where the flow direction
depends on the difference of the lakes' water levels.  Technically, we can combine
|exch_weir_hbv96| with all model types, calculating (something like) water level
information and accepting an additional inlet that can supply positive and negative
values.  Due to this flexible approach, we do not need to implement the weir formula to
different |dam| models.  On the downside, this looser coupling often comes with some
limitations.  One example is numerical accuracy, which might be suboptimal due to
solving the interconnected differential equations of different model instances
sequentially (we might improve this later).

Besides such explanation requiring models, HydPy-Exch also provides straightforward
models like |exch_branch_hbv96|, which distributes its inflow to multiple locations.

Available models:

.. toctree::
   :maxdepth: 1

   exch
   exch_branch_hbv96
   exch_weir_hbv96
   exch_waterlevel
