.. _HydPy-Manager:

HydPy-Manager
=============

The HydPy-Manager model family's purpose is, as the name suggests, not to provide models
that work on their own but to coordinate other models, enabling them to achieve goals
they could not reach when acting independently.  To this end, manager models send some
information to and usually also need to receive information from the models they
coordinate.

The idea of adding the Manager family to HydPy is quite new, and the low-water-control
model |manager_lwc| is our first experiment in this direction.  Depending on its success
in real applications and further demands, we might add more application models later.

Available models:

.. toctree::
   :maxdepth: 1

   manager
   manager_lwc
