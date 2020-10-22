
.. _Landeshochwasserzentrum (LHWZ): https://www.umwelt.sachsen.de/umwelt/wasser/72.htm
.. _LARSIM: http://www.larsim.de/das-modell/
.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN

.. _HydPy-D:

HydPy-D (DAM)
=============

The HydPy-D model family implements dams and similar natural and
anthropogenic flow barriers.

At the current state of development, all its application models rely
on an adaptive explicit Runge-Kutta method. This integration method
allows for performing simulations with adjustable numerical precision.
However, it works best for continuous differential equations. Hence,
most process equations of base model |dam| are either continuous by nature
or are "regularisable", meaning one can smooth their discontinuities by
a degree one considers useful.

Each application model provides a different combination of control
capabilities.. Many take "remote locations" into account, for example,
to release additional water to the downstream river channel to increase
water stages at remote gauges.

All application models are tested and ready for use.  However, please note
that some improvements in style and structure (e.g. changes in some
variable names) might be necessary for the future. At the moment, it is a
little hard to pick the correct application model.  We will have to find
a way to prevent selecting the right model becoming too hard when the
set of application models grows.  For the moment, the following overview
over the first five application models might be helpful:

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

These five application models are independent implementations, developed
for the forecasting system of the German federal state of Saxony and run
by the `Landeshochwasserzentrum (LHWZ)`_.  More recently, we added the
application models |dam_v006|, |dam_v007|, and |dam_v008| on behalf of
the `German Federal Institute of Hydrology (BfG)`_.  Conceptionally, these
*HydPy* models correspond the `LARSIM`_ models "SEEG" (controlled lake),
"RUEC" (retention basin) and "TALS" (reservoir).

|dam_v001| has been the starting point for the development of the
other application models. Hence its documentation is very comprehensive,
and it seems to be a good starting point to become acquainted with any
of the application models prepared so far.

Base model:

.. toctree::
   :maxdepth: 1

   dam

Application model:

.. toctree::
   :maxdepth: 1

   dam_v001
   dam_v002
   dam_v003
   dam_v004
   dam_v005
   dam_v006 (controlled lake) <dam_v006>
   dam_v007 (retention basin) <dam_v007>
   dam_v008 (reservoir) <dam_v008>
