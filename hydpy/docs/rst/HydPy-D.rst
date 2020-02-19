
.. _HydPy-D:

HydPy-D (DAM)
=============

The HydPy-D is intended for modelling dams and similar natural and
anthropogenic flow barriers.  It is the first model family of HydPy
that is not a re-implementation of an existing model.

At the current state of development, all dam application models rely
on an adaptive explicit Runge-Kutta method. This integration method
allows for performing simulations with adjustable numerical precision.
However, it works best for continuous differential equations, which is
why the process equations can (and often should) be parametrised in a
way avoiding discontinuities.

Each application model provides a different combination of control
capabilities that takes “remote locations” into account, e.g. to
release additional water to the downstream river channel to increase
water stages at remote gauges.

All application models are tested and ready for use.  However, please note
that some improvements in style and structure (e.g. changes in some
variable names) might be necessary for the future. At the moment, it is a
little hard to pick the correct application model.  We will have to find
a way to prevent selecting the right model becoming too hard when the
set of application models grows.  For the moment, the following overview
might be helpful:

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

   dam_v001
   dam_v002
   dam_v003
   dam_v004
   dam_v005
   dam_v006
   dam_v007
   dam_v008
