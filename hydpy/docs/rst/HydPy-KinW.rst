
.. _`LARSIM`: http://www.larsim.de/en/the-model/

.. _HydPy-KinW:

HydPy-KinW
==========

The HydPy-KinW model family provides storage-based routing methods that rely on the
simplifying kinematic wave assumption.  Currently, all its members follow routing
methods applied by the `LARSIM`_ model.

For reasons of consistency with the original LARSIM implementation, the names of all
parameter and sequence classes are German terms and abbreviations.  Additionally, the
documentation on each parameter or sequence contains an English translation.

.. warning::

   We might change the implemented application models soon.  Backward-incompatible
   changes might include switching to English variable names, improving numerical
   performance, or supporting more channel profile geometries.  It is also possbile we
   drop HydPy-KinW entirely if, for example, alternative routing methods like
   |musk_mct| prove superior in every respect.

Available models:

.. toctree::
   :maxdepth: 1

   kinw
   kinw_williams
   kinw_williams_ext
