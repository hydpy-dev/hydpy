
.. _HydPy-Musk:

HydPy-Musk (Muskingum)
======================

The `HydPy-Musk` model family provides models that solve the routing problem
like the classic Muskingum method or its derivatives.  One can understand all
application models as non-adaptive finite-difference approximations of
(extremely) simplified versions of the Saint-Vernant equations.  Hence, they
are more limited than hydrodynamical approaches but are simpler to handle and
much more efficient regarding computation times.

Base model:

.. toctree::
   :maxdepth: 1

   musk

Application models:

.. toctree::
   :maxdepth: 1

   musk_classic
   musk_mct
