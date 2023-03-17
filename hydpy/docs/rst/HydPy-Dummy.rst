
.. _`LARSIM`: http://www.larsim.de/en/the-model/

.. _HydPy-Dummy:

HydPy-Dummy
===========

`HydPy-Dummy` models do not apply any process equations.  Instead, they serve
as simple placeholders which forward their input without modifications.

In *HydPy*, it is fairly easy to introduce additional |Element| objects and
thus to bring new models of arbitrary types into existing network structures.
Hence, there is typically no need to define dummy elements or models in
anticipation of possible future changes.  However, application models like
|dummy_v1| can help to more closely reflect the actual network structures of
other model systems as `LARSIM`_, which are more restrictive regarding future
changes and network complexity.

Base model:

.. toctree::
   :maxdepth: 1

   dummy

Application model:

.. toctree::
   :maxdepth: 1

   dummy_v1
