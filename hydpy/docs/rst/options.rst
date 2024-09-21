
.. _options:

Options
=======

HydPy offers infinite configuration possibilities for those familiar with Python.  But
even without programming skills, one has a lot of options, and this section lists the
most relevant ones, explains how to set them, and points to the places of the
:ref:`reference manual <reference_manual>` containing further information.

All options discussed here work for the framework in general or apply to all (or at
least many) models and are accessible from both Python scripts and XML files.  Refer to
the reference manuals' :ref:`model documentation <model_families>` for more
model-specific questions like: What options do I have to set the capillary rise when
using |lland_dd|?).

Class |Options| provides many of the most general options.  Note that the default
values of some of its options are suitable for real projects but less for testing
purposes.  Hence, the various code examples of this documentation rely on settings that
deviate from these defaults, and you need to adjust these options to be able to
reproduce all examples exactly.

The documentation of the individual |Options| members explains their purposes and
mentions possible deviations of default and testing values.  All these options are
configurable when working with XML files, and any changes apply to the entire XML-based
workflow.  In contrast, when defining workflows with Python scripts, you can change all
options multiple times.

Take the |Options.reprdigits| option as an example, which determines the maximum number
of digits of floating point numbers shown in HydPy's string representations.   Its
default is -1, which means printing in the highest available precision.  However, HydPy
sets it to 6 during testing, compromising preciseness and readability.

You can access and modify this and the other mentioned options via the singleton
instance of class |Options| available in the |pub| module, which stores this and other
public project data:

You can access and modify this and the other mentioned options via the singleton
instance of class |Options| available in the |pub| module (|pub| stores this and other
public configuration data):

>>> from hydpy import pub, round_
>>> pub.options.reprdigits
6
>>> round_(1.0 / 3.0)
0.333333

Use a simple assignment statement to change the printed precision permanently:

>>> pub.options.reprdigits = 4
>>> round_(1.0 / 3.0)
0.3333

For temporary changes, we encourage using the `with` syntax.  Then, the modification
only applies inside the `with` block (even when an error occurs):

>>> with pub.options.reprdigits(2):
...     round_(1.0 / 3.0)
0.33
>>> round_(1.0 / 3.0)
0.3333

Many options are "bool-like" but not actually of type |bool|.  Hence, you cannot rely
on identity checks via `is` when writing Python scripts:

>>> pub.options.timestampleft
TRUE
>>> assert pub.options.timestampleft  # fine
>>> pub.options.timestampleft == True  # fine
True
>>> pub.options.timestampleft is True  # buggy
False

The second group of options worth mentioning here is provided by multiple "file
managers", which also are singleton objects and members of the |pub| module.
|NetworkManager|, |ControlManager|, |ConditionManager|, and |SequenceManager| manage,
as their names suggest, reading and writing :ref:`network <network_files>`,
:ref:`control <control_files>`, :ref:`condition <condition_files>`, and :ref:`time
series <series_files>` files.  The instances are named after their classes but, as
usual, in lower-case letters.  They become available after starting a HydPy project via
initialising class |HydPy|:

>>> from hydpy import HydPy
>>> hp = HydPy("my_project")
>>> assert hasattr(pub, "networkmanager")

All these file managers offer the |FileManager.currentdir| property (which so far does
not support the `with` syntax) to change the directory selected for reading or writing
data.  By default, the |FileManager.currentdir| is within the base directory defined by
the respective file manager:

>>> assert pub.networkmanager.BASEDIR == "network"
>>> assert pub.controlmanager.BASEDIR == "control"
>>> assert pub.conditionmanager.BASEDIR == "conditions"
>>> assert pub.sequencemanager.BASEDIR == "series"

The only file managers providing other user-relevant options (which do support the
`with` syntax) are |ConditionManager| and |SequenceManager|.  One example is option
|SequenceManager.filetype| for choosing between the ASCII, NetCDF, and Numpy file
formats.

When working with XML files, HydPy offers more flexibility for the file managers'
options than for those of class |Options|.  When setting each option once and for all,
one could not, for example, read meteorological input data from NetCDF files of one
directory and write discharge data to ASCII files in another directory. Therefore,
HydPy's XML support offers two exceptions, which are both illustrated, for example, by
the `single_run.xml` file supplied with the :ref:`HydPy-H-Lahn` example project.
First, the XML element `conditions_io` allows for specifying separate directories for
reading and writing condition files.  Second, the XML element `serios_io` can contain
multiple `readers` and `writers`, and one can specify individual option values for
each.

The option `mode` is specific to XML files. It allows reading and writing time series
data "just in time" during simulation runs (in contrast to handling the complete time
series data in RAM).  When working with Python scripts, the counterpart to `mode` is
the function argument `jit` (provided, for example, by method
|HydPy.prepare_allseries|).  The documentation on class |HydPy| explains its usage in
detail.
