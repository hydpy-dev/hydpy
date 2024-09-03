
.. _reference_manual:

Reference Manual
================

This reference manual provides in-depth information about all general :ref:`framework
functionalities <framework_tools>` and :ref:`models <model_families>` HydPy offers.
Also, it lists all :ref:`submodel interfaces <submodel_interfaces>`, which are
standardised connections for coupling main models and submodels.

HydPy has a so-called complete (line-based) test coverage, meaning automatised test
bots analyse each HydPy build thoroughly.  We achieved this desirable goal by writing
an extremely high number of doctests, which are "normal" unit or integration tests
visible in the documentation.  As a result, reading this reference manual takes some
time (and we advise not only to read but also repeat the tests in a Python shell), but
it covers all details and edge cases we thought to be relevant (for example, tests of
expected user errors).  Therefore, please refrain from reading this reference manual
from front to back.  You will likely benefit more from working through the
:ref:`quickstart` section and the :ref:`user_guide` and, afterwards, from searching
for more specific information in this reference manual.


.. toctree::
   :hidden:

   framework_tools
   model_families
   submodel_interfaces
