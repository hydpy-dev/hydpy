
.. _HydPy-H-Stream:

HydPy-H-Stream
==============

The HydPy-H-Stream model is an very simple routing approach.  More 
precisely, it is a simplification of the Muskingum approach, which 
itself can be seen as a naive finite difference solution of the 
routing problem.
	
Model
-----

.. autoclass:: hydpy.models.hstream.Model
    :members:
    :show-inheritance:
    
Parameters
----------

.. autoclass:: hydpy.models.hstream.Parameters
    :members:
    :show-inheritance:
    
Control parameters
..................

.. autoclass:: hydpy.models.hstream.Lag
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.Damp
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.ControlParameters
    :members:
    :show-inheritance:
    
Derived parameters
..................

.. autoclass:: hydpy.models.hstream.NmbSegments
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.C1
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.C2
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.C3
    :members:
    :show-inheritance:
    
.. autoclass:: hydpy.models.hstream.DerivedParameters
    :members:
    :show-inheritance:
 
Sequences
---------
.. autoclass:: hydpy.models.hstream.Sequences
    :members:
    :show-inheritance:

State sequences
...............

.. autoclass:: hydpy.models.hstream.QJoints
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.StateSequences
    :members:
    :show-inheritance:

Link sequences
..............

.. autoclass:: hydpy.models.hstream.Q
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.InletSequences
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hstream.OutletSequences
    :members:
    :show-inheritance: