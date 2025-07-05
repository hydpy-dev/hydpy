
.. _`LARSIM`: http://www.larsim.de/en/the-model/

.. _HydPy-KinW:

HydPy-KinW
==========

The HydPy-KinW model family offers storage-based routing methods that rely on the
simplifying kinematic wave assumption.  Its initial members, |kinw_williams| and
|kinw_williams_ext|, follow routing methods applied by the `LARSIM model`_.  Their
parameters and sequences are, for consistency with the original LARSIM implementation,
German terms and abbreviations.  Additionally, the documentation on each parameter or
sequence contains an English translation.

We might change the |kinw_williams| and |kinw_williams_ext|  in the future.
Backwards-incompatible changes may include switching to English variable names,
improving numerical performance, or supporting additional channel profile geometries.
It is also possible we drop them completely in case newer models like |kinw_impl_euler|
(which is already "more English", more performant, and more flexible but has no adaptive
error control) prove highly superior.

Available models:

.. toctree::
   :maxdepth: 1

   kinw
   kinw_impl_euler
   kinw_williams
   kinw_williams_ext
