
.. _submodel_interfaces:

Submodel Interfaces
===================

Submodel interfaces are contracts between main models and submodels.  If both of them
agree with one contract, they are compatible.  We say a submodel "follows" or "complies
with" an interface if it supplies all the interface's required methods (and is derived
from it).  On the other side, we speak of a main model's "port" of a specific interface
if a main model can use all submodels that follow that interface.

This subsection lists all currently available submodel interfaces.  We hope this
information to be relevant only for framework and model developers.  Users should be
able to easier query the information about possible couplings between main models and
submodels via submodel graphs.  See, for example, the "complete" submodel graph,
available in the :ref:`model_overview` section, which covers all user-relevant models.


.. toctree::
   :hidden:

   aetinterfaces
   dischargeinterfaces
   petinterfaces
   precipinterfaces
   radiationinterfaces
   rconcinterfaces
   routinginterfaces
   soilinterfaces
   stateinterfaces
   tempinterfaces
