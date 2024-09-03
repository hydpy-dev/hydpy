
.. _framework_tools:

Framework Tools
===============

The HydPy framework provides many general functionalities for programming, documenting,
and using hydrological models in more or less complex workflows.  This section explains
these general functionalities in multiple subsections, each corresponding to another
subpackage of the hydpy package.

>>> from hydpy import core

The `core` subpackage, documented by the :ref:`core` subsection, is HydPy's backbone.
It contains features for creating networks, defining models, reading time series, and
much more.

>>> from hydpy import cythons

The `cythons` subpackage, documented by the :ref:`cythons` subsection, deals mainly
with programming details related to computational efficiency and is only for framework
developers (and eventually some model developers) important.

>>> from hydpy import auxs

The `auxs` subpackage, documented by the :ref:`auxiliaries` subsection, covers
additional features which are not required when using HydPy in general but can help
program new models or write elaborated workflow scripts.

>>> from hydpy import exe

The `exe` subpackage, documented by the "Execution Tools" subsection, mainly enables
HydPy to be used from the command line and in server mode.

Nearly all names of these subpackages' modules end with "tools".  The exceptions are
the modules of the `cythons` subpackage, whose names end with "utils".  We adhere to
this convention to avoid potential name conflicts and to make these modules easily
distinguishable from other HydPy objects within Python scripts and doctests.

We do not try to prevent you from importing highly specialised functionality from any
module.  In contrast, we even encourage it for learning and testing HydPy.  However,
when writing stable workflow scripts, you are well advised to rely only on the
available top-level imports to avoid the risk of needing to rework your scripts after
we refactored some HydPy modules:

>>> from hydpy.core.timetools import Date  # bad
>>> from hydpy import Date  # good


.. toctree::
   :hidden:

   core
   execution
   cythons
   auxiliaries
