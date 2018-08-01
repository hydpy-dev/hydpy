
.. _core:

Core Modules
============

The core subpackage of :ref:`HydPy` essentially defines how models can
and should be programmed, documented and applied.  As can be seen in
the side-bar, the list of modules contained in the core subpackage
is quite large.  The following paragraphs try to give some hints to
novices, which basic aspects of using :ref:`HydPy` are related with
which module.

Module |hydpytools| provides the |HydPy| class.  The main purpose
of this class is to help users accomplish possibly complex things via
a simple interface.  Very often, you will only need to initialize an
|HydPy| object and to call its methods in order to e.g. load all input
data, perform a simulation run, and to store the relevant results.
So trying to get an overview of the methods of class |HydPy| is generally
a good idea.

The documentation on module |filetools| describes the standard
directory structure of :ref:`HydPy` projects.  Module |filetools|
offers some flexibility in adjusting this project structure to your
needs.  Also, it is responsible for many aspects of loading data from
files and storing data to files.  It is supplemented by module
|netcdftools| for reading data from and storing data to NetCDF files.

:ref:`HydPy` represents the network of a river basin via connected
objects of the classes |Node| and |Element|.  These are defined in module
|devicetools|. It is often helpful to define subsets of networks, which
is provided by module |selectiontools|.  In this context, reading the
documentation on module |networktools| could also be of interest, as it
implements strategies to define :ref:`HydPy` networks in large basins.

The actual data to run a certain model is handled in `control files`
(containing parameter values), `condition files` (containing state
conditions) and `sequence files` (containing input or output time
series).  Modules |parametertools| and |sequencetools| provide
features to handle these different kinds of data.

Module |timetools| provides the |Timegrids| class, of which an object
needs to be stored in the "global information" module |pub|.  Use this
|Timegrids| object to define the time period for  which data shall be
initialized and the time period for which one simulation (or multiple
simulations) shall be performed.

The other modules serve more special purposes.  If you are thinking
about adding new code to :ref:`HydPy` or changing existing one, you
should read the documentation of some other modules as well.
|autodoctools| provides features for automatically generating this
online documentation.  Modules |testtools| and |dummytools| provide
features for testing new code (or old code, that has not been covered
by the existing tests so far).  Module |objecttools| (need to be
refactored) provides very different kinds of features to simplify and
standardize writing :ref:`HydPy` code.


.. toctree::
   :hidden:

   abctools
   autodoctools
   auxfiletools
   connectiontools
   devicetools
   dummytools
   exceptiontools
   filetools
   hydpytools
   importtools
   indextools
   masktools
   modelimports
   modeltools
   netcdftools
   objecttools
   optiontools
   parametertools
   printtools
   selectiontools
   sequencetools
   testtools
   texttools
   timetools
   variabletools
