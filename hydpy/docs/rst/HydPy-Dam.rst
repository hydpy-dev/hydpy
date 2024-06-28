
.. _Landeshochwasserzentrum (LHWZ): https://www.umwelt.sachsen.de/umwelt/wasser/72.htm
.. _LARSIM: http://www.larsim.de/das-modell/
.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN

.. _HydPy-Dam:

HydPy-Dam
=========

The HydPy-Dam model family implements dams and similar natural and anthropogenic flow
barriers.

At the current state of development, all its application models rely on an adaptive
explicit Runge-Kutta method. This integration method allows for performing simulations
with adjustable numerical precision. However, it works best for continuous differential
equations. Hence, most process equations of base model |dam| are either continuous by
nature or "regularisable", meaning one can smooth their discontinuities by a degree one
considers useful.

Each application model provides a different combination of control capabilities.  Many
take "remote locations" into account, for example, to release additional water to the
downstream river channel to increase water stages at remote gauges.

All application models are tested and ready for use.  However, please note that some
improvements in style and structure (e.g. changes in some variable names) might be
necessary in the future. At the moment, it is a little hard to pick the correct
application model.  We will have to find a way to prevent selecting a suitable model
from becoming too hard when the collection of application models grows.  For the
moment, the following overview of the first five application models might be helpful:

================================================================= ==== ==== ==== ==== ====
Does the dam model…                                               v001 v002 v003 v004 v005
================================================================= ==== ==== ==== ==== ====
…calculate the demand at a remote location itself?                yes  no   no   no   yes

…lie in a river upstream of the remote location?                  yes  yes  no   no   yes

…tell another model if it cannot supply the remote demand?        no   no   no   no   yes

…discharge to another remote location for flood protection?       no   no   no   yes  no

…ask for additional water supply from a remote location?          no   no   no   no   yes

…allow for discharge from a remote location for flood protection? no   no   no   no   yes
================================================================= ==== ==== ==== ==== ====

These five application models are independent implementations, developed for the
forecasting system of the German federal state of Saxony and run by the
`Landeshochwasserzentrum (LHWZ)`_.  Later, we added the application models |dam_llake|,
|dam_lretention|, and |dam_lreservoir| on behalf of the `German Federal Institute of
Hydrology (BfG)`_.  Conceptionally, these *HydPy* models correspond to the `LARSIM`_
models "SEEG" (controlled lake), "RUEC" (retention basin) and "TALS" (reservoir).  Most
recently, we developed |dam_pump|, |dam_sluice|, and |dam_pump_sluice| for improving
simulations in low-land areas, where the draining of land areas via pumps and sluices
often plays a more relevant role than gravity-driven runoff.

|dam_v001| has been the starting point for the development of the other application
models. Hence its documentation is very comprehensive, and it seems to be a good
starting point for becomimg acquainted with any of the application models prepared so
far.

Available models:

.. toctree::
   :maxdepth: 1

   dam
   dam_v001
   dam_v002
   dam_v003
   dam_v004
   dam_v005
   dam_llake
   dam_lretention
   dam_lreservoir
   dam_pump
   dam_sluice
   dam_pump_sluice
