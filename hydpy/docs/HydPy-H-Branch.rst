
.. _HydPy-H-Branch:

HydPy-H-Branch
==============

The HydPy-H-Branch model allows for branching the input from a
single inlet :class:`~hydpy.core.devicetools.Node` instance to
an arbitrary number of outlet :class:`~hydpy.core.devicetools.Node`
instances.  In the original  HBV96 implementation, it is supposed to
seperate inflowing discharge, but in :ref:`HydPy` it can be used for
arbitrary variables.  Calculations are performed for each branch
individually by linear interpolation (or extrapolation) in accordance
with tabulated supporting points.

Model
-----

.. autoclass:: hydpy.models.hbranch.Model
    :members:
    :show-inheritance:

Parameters
----------

.. autoclass:: hydpy.models.hbranch.Parameters
    :members:
    :show-inheritance:

Control parameters
..................

.. autoclass:: hydpy.models.hbranch.XPoints
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.YPoints
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.ControlParameters
    :members:
    :show-inheritance:

Derived parameters
..................

.. autoclass:: hydpy.models.hbranch.NmbBranches
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.NmbPoints
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.DerivedParameters
    :members:
    :show-inheritance:

Sequences
---------
.. autoclass:: hydpy.models.hbranch.Sequences
    :members:
    :show-inheritance:

Flux sequences
..............

.. autoclass:: hydpy.models.hbranch.Input
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.Outputs
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.FluxSequences
    :members:
    :show-inheritance:

Link sequences
..............

.. autoclass:: hydpy.models.hbranch.Total
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.InletSequences
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.Branched
    :members:
    :show-inheritance:

.. autoclass:: hydpy.models.hbranch.OutletSequences
    :members:
    :show-inheritance: