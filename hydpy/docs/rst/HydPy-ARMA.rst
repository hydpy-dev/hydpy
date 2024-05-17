
.. _HydPy-ARMA:

HydPy-ARMA
==========

Many hydrologists use linear system approaches to solve flood routing problems
approximately.  Famous examples are the Unit Hydrograph approach and the Muskingum
flood routing method.  One can understand the Unit Hydrograph approach as a moving
average process (MA), and the Muskingum method as a mixed autoregressive and moving
average process (ARMA).  Unit Hydrographs consist of an arbitrary number of MA
coefficients.  The Muskingum method defines three parameters, exactly two MA
coefficients associated with the "new" and the "old" flow into the channel, and one AR
coefficient associated with the "old" flow out of the channel.

The HydPy-ARMA base model supports implementing such methods in a generalised manner.
Consider using one of its application models when you require a robust, computationally
efficient, easily calibratable approach.  However, taking nonlinear rating curves or
backwater effects into account can be cumbersome or even impossible.

Base model:

.. toctree::
   :maxdepth: 1

   arma

Application model:

.. toctree::
   :maxdepth: 1

   arma_v1
