
.. _core:

Core Tools
==========

The `core` subpackage of HydPy essentially defines how models can and should be
programmed, documented and applied.  As can be seen in the sidebar, the list of modules
contained in the core subpackage is quite extensive.  The following paragraphs explain
which central aspects of using HydPy are related to which module.

Module |hydpytools| provides the |HydPy| class.  This class aims to help users
accomplish complex things via a simple interface.  Very often, you will only need to
initialise an |HydPy| object and call its methods to, for example, load all input data,
perform a simulation run, and store the relevant results.  So, getting an overview of
the methods of class |HydPy| is generally a good idea.

Module |filetools| defines the standard directory structure of HydPy projects and its
possible modifications.  Also, it is responsible for many aspects of loading data from
files and storing data in files.  It is supplemented by module |netcdftools| for
reading data from and storing data to NetCDF files.

HydPy represents the network of a river basin via connected objects of the classes
|Node| and |Element|, defined in module |devicetools|.  It is often helpful to create
subsets of networks named "selections", for which module |selectiontools| provides some
convenient features.  (In this context, reading the documentation on module
|networktools| might also be interesting, as this module implements strategies to
derive networks for large basins.)

The modules |modeltools|, |parametertools|, and |sequencetools| form the basis for
programming models.  While |modeltools| focuses on the more general aspects,
|parametertools|, and |sequencetools| cover the more specific topics of implementing
model parameters and sequences.


Module |timetools| provides multiple classes that wrap the "date and time"
functionalities of the Python standard library to simplify and standardise the related
operations (which are prone to hard-to-detect errors) in workflow scripts.

If you are thinking about contributing to HydPy's source code, you should also read the
documentation of some other modules.  Then, essential are |autodoctools| (deals with
automatised generation of this online documentation), |testtools| (provides features
for automatised testing via doctests), |objecttools| (contains different kinds of
features to simplify and standardise writing HydPy code), and |typingtools| (makes
general and HydPy-specific type hint features available).

.. toctree::
   :hidden:

   aliastools
   autodoctools
   auxfiletools
   devicetools
   exceptiontools
   filetools
   hydpytools
   importtools
   indextools
   itemtools
   masktools
   modeltools
   netcdftools
   objecttools
   optiontools
   parametertools
   printtools
   propertytools
   pubtools
   selectiontools
   sequencetools
   seriestools
   testtools
   threadingtools
   timetools
   typingtools
   variabletools
