
.. _project_structure:

Project structure
=================

This section describes the typical file structure of HydPy :ref:`projects <project>`,
comprising :ref:`network files <network_files>`, :ref:`control files <control_files>`,
:ref:`condition files <condition_files>`, and :ref:`series files <series_files>`.  We
refer to the :ref:`HydPy-H-Lahn` example project to illustrate our explanations, which
has the following file structure:

.. project_structure:: HydPy-H-Lahn

All project files are in the project's sub-subdirectories.  Except for conditions,
these sub-subdirectories are usually named `default`.  You can add directories with
different names to, for example, hold the parameter values of multiple calibrations in
one project.

HydPy offers functionalities for reading and writing project files.  Besides time
series files, all project files are usually Python files (ending with ".py").  HydPy
writes them so that they appear like "normal" configuration files.  From the
programmer's perspective, this requires some tricks, which we mention in the respective
subsections.  One main advantage is that you can copy individual configuration
fragments into a Python console to check precisely how they work.  We frequently use
this feature throughout the documentation.

HydPy allows users to deviate from the default file structure and, due to its design as
a Python library, even to set up projects directly via scripts or define alternative
file formats, but these are more advanced topics left for the :ref:`reference manual
<reference_manual>`.

.. _network_files:

Network files
_____________

`Network files` define a HydPy project's :ref:`network` by introducing and coupling
:ref:`elements <element>` and :ref:`nodes <node>`.  Consider the following minimal
example of a network file's content:

>>> from hydpy import Node, Element
>>> _ = Node("n", variable="Q")
>>> _ = Element("e1", outlets="n")
>>> _ = Element("e2", inlets="n")

Node `n` connects element `e1` with element `e2`, so we have a network of three
:ref:`devices <device>`.  From the perspective of `e1`, `n` is an outlet node, and from
the perspective of `e2`, an inlet node:

>>> assert Element("e1").outlets.n is Element("e2").inlets.n

Given the curt names, we cannot safely guess the purposes of `e1` and `e2` because
network files are model-agnostic.  The only thing for sure is that the model of `e1`
must be able to route discharge to a downstream node, and the model of `e2` must be
able to receive discharge from an upstream node.  Hence, we could use this network file
for various model-type combinations.

The names of elements and nodes serve as their identifiers, which means you never
make two node or two element instances with the same name.  If it looks like you create
a new instance, you actually just get a reference to an already existing one (possibly
with already set up node connections):

>>> Element("e1")
Element("e1",
        outlets="n")

Each network file corresponds to one :ref:`selection`.  The :ref:`HydPy-H-Lahn` project
defines three selections: one for all :ref:`stream models <stream_models>` and two for
the :ref:`land models <land_models>` in the headwater and non-headwater subbasins.  The
combination of all individual selections gives a selection named "complete", which is
always available and activated after loading a network.

The described "name as identifier" mechanism allows us to define the same device in
multiple network files of the same project.  So, one can create an arbitrary number of
selections to structure the same network after different criteria.  The only
(self-evident) requisite is the consistency of all individual definitions.  You cannot,
for example, add an inlet node to an element if it is already the same element's outlet
node:

>>> Element("e1", inlets="n")
Traceback (most recent call last):
...
ValueError: For element `e1`, the given inlet node `n` is already defined as a(n) outlet node, which is not allowed.

Besides these standards, the :ref:`reference manual <reference_manual>` covers many
features which help to organise HydPy projects (see, for example, the :ref:`keyword`
features of class |Device| and its collection type |Devices|) or to build more complex
networks, for example, those that pass on different types of data (configurable by the
|Node.variable| attribute of class |Node|).

.. _control_files:

Control files
_____________

`Control files` select :ref:`model types <model>`, prepare model :ref:`instances
<instance>`, and set :ref:`parameter` values.  Each :ref:`element` defined in the
:ref:`network files <network_files>` requires one control file, which sets up its
:ref:`main_model`, including all :ref:`submodels <submodel>`.

The :ref:`HydPy-H-Lahn` project relies on two main model types: the :ref:`land model
<land_models>` |hland_96| and the :ref:`stream model <stream_models>` |musk_classic|.
The control file "stream_dill_assl_lahn2.py", for example, selects the latter for routing
the outflow of the subbasin Dill to a location in the river Lahn.  The control file is
short because |musk_classic| is relatively simple.  The first (Python-code) line
selects the model type by a so-called "wildcard import", making all relevant
information directly available:

>>> from hydpy.models.musk_classic import *

The following line defines a simulation time step size of one hour:

>>> simulationstep("1h")

Note that the |simulationstep| line is optional.  It allows for adjusting parameter
values that depend on the simulation time step size, so one can set up a model for
testing purposes without embedding it in a complete project.  However, when executing
the file within the context of a project, the project's simulation step counts (HydPy
then ignores the control file's specification) so that the same control file works for
different simulation time step sizes.

The |parameterstep| line is similar but mandatory.  It defines the time unit of the
subsequently specified values of time-dependent parameters.  The given example
selects a parameter time step size of one day:

>>> parameterstep("1d")

.. note::

    A note for programmers: Function |parameterstep| prepares a suitable model instance
    and makes it and its main components directly available in the local namespace.
    This trick allows for the simple further model preparation steps.

As in nearly all cases, the discussed control file only sets the required values of
control parameters and does not modify the predefined values of other parameter groups.
The parameter value specifications are not conducted via "assignment expressions" but
"bracket expressions", like when calling a regular function:

>>> nmbsegments(lag=0.417)
>>> coefficients(damp=0.0)

Here, the parameter values are not set directly via positional arguments but by
parameter-specific keyword arguments unique to the classes |musk_control.NmbSegments|
and |musk_control.Coefficients|.  Note that the `lag` argument is time-dependent and
so, according to the specified parameter step size, is given in days, while the "true"
value of the |musk_control.NmbSegments| instance refers to the simulation step size of
one hour:

>>> nmbsegments.value == round(24.0 * 0.417)
True

Due to the higher complexity of |hland_96|, the control file "land_dill_assl.py" is much
longer.  We focus on a few aspects not relevant to |musk_mct|.  Therefore, we must
first clear the local namespace (one could also just start a fresh Python process):

>>> from hydpy import reverse_model_wildcard_import
>>> reverse_model_wildcard_import()

|hland_96| requires submodels and the control file must select them.  It does so by
importing the main model (|hland_96|) by a wildcard import but all submodels
(|evap_aet_hbv96|, |evap_pet_hbv96|, and |rconc_uh|) by a module import:

>>> from hydpy.models.hland_96 import *
>>> from hydpy.models import evap_aet_hbv96
>>> from hydpy.models import evap_pet_hbv96
>>> from hydpy.models import rconc_uh

The time step-related lines work as described above:

>>> simulationstep("1h")
>>> parameterstep("1d")

The subbasin's area is set via a positional argument:

>>> area(692.3)

The parameter |hland_control.NmbZones| is notable, as it requires integer values and,
more importantly, modifies the shape of other parameters.  After setting its value, you
can prepare parameters with zone-specific values like |hland_control.ZoneArea|:

>>> zonearea.shape
Traceback (most recent call last):
...
hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable `zonearea` can only be retrieved after it has been defined.

>>> nmbzones(12)
>>> assert nmbzones == zonearea.shape[0]
>>> zonearea(14.41, 7.06, 70.83, 84.36, 70.97, 198.0, 27.75, 130.0, 27.28,
...          56.94, 1.09, 3.61)

Strictly speaking, |hland_control.NmbZones| is specific to the
|hland.Model.DOCNAME.family| model family.  Still, there are many models which rely on
hydrological response units, stream segments, or different forms of (spatial)
subdivisions and use the same logic of a control parameter defining the number of
subdivisions and many parameters or sequences shaped as vectors or matrixes to handle
different values for individual (spatial) units.

Another example of a |hland.Model.DOCNAME.family|-speciality, which also follows a
general HydPy design principle, is the definition of "spatial types" (mostly land use
types) via constants.  |hland.Model.DOCNAME.family| provides such constants for
defining the types of the individual zones:

>>> zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD,
...          FOREST, FIELD, FOREST)


When preparing zone-specific parameters, you can decide between defining individual,
land type-specific, and subbasin-wide values:

>>> zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0)
>>> cfmax(field=4.55853, forest=2.735118)
>>> fc(278.0)

Often, one does not wish to define individual values for each control file but more
general ones.  HydPy supports this via "auxiliary files".  In the discussed control
file, the parameter |hland_control.PCorr| instance takes its value from the auxiliary
file "land.py" (to get this working in a doctest requires changing the working
directory):

.. testsetup::

    >>> import os
    >>> workingdir = os.getcwd()

>>> import os
>>> from hydpy import data
>>> os.chdir(os.path.join(data.__path__[0], "HydPy-H-Lahn", "control", "default"))
>>> pcorr(auxfile="land")
>>> pcorr
pcorr(1.0)

All submodels are generally added at a control file's end because they might expect
some main model parameters to be already prepared.  Each main model provides a suitable
method for adding specific submodel types.  Such methods should be applied after a
`with statement`.  Within the subsequent `with block`, one can directly set the
submodel's parameters as explained above.  The discussed control file uses the
|hland_model.Main_RConcModel_V1.add_rconcmodel_v1| method to add a |rconc_uh|
instance (and configures its Unit Hydrograph ordinates in a triangle shape):

>>> with model.add_rconcmodel_v1(rconc_uh):
...    uh("triangle", tb=0.36728)
>>> from hydpy import print_vector
>>> print_vector(model.rconcmodel.parameters.control.uh.values)
0.02574, 0.077221, 0.128701, 0.180182, 0.213581, 0.170644, 0.119163,
0.067682, 0.017086

Adding a sub-submodel to a submodel works via nested `with blocks`:

>>> with model.add_aetmodel_v1(evap_aet_hbv96):
...     temperaturethresholdice(nan)
...     soilmoisturelimit(0.9)
...     excessreduction(0.0)
...     with model.add_petmodel_v1(evap_pet_hbv96):
...         airtemperaturefactor(0.1)
...         altitudefactor(0.0)
...         precipitationfactor(0.02)
...         evapotranspirationfactor(1.0)

The last example covers two new cases.  First, |numpy.nan| serves to mark "missing" or
"not required" values.  Parameter |evap_control.TemperatureThresholdIce| requires no
values because it only applies to |hland_constants.ILAKE| zones, while the Dill
subbasin only consists of |hland_constants.FIELD| and |hland_constants.FOREST| zones.
Second, main models often transmit some parameter values to their submodels, which
helps to avoid duplicate and potentially inconsistent definitions.  In the discussed
control file, this applies, for example, to the parameter pairs
|hland_control.NmbZones| and |evap_control.NmbHRU| and |hland_control.FC| and
|evap_control.MaxSoilWater|:

>>> assert nmbzones == model.aetmodel.parameters.control.nmbhru
>>> assert fc == model.aetmodel.parameters.control.maxsoilwater

Before writing a control file, one should read the documentation of the relevant
application models in the :ref:`reference manual <reference_manual>`, which provides
complete lists of the control parameters that need configuration, detailed application
examples, and much more.

.. _condition_files:

Condition files
_______________

`Condition files` represent model states and logged data at a particular time point.
They are usually written at the end of a simulation run and later read before
simulating another period that starts where the old one has ended.  Instead, their
names usually include the prefix  `init` (for initial conditions) and a suffix
indicating the relevant date, using underscores as separators.  Each :ref:`element`
defined in the :ref:`network files <network_files>` requires one condition file, and so
each condition file corresponds to one main model and one control file.

Condition files are similar to control files but almost always shorter and simpler.  We
take the condition file of the Dill subbasin for 1 January 1996 as an example, which,
like the discussed control file, starts with a wildcard import that selects the
relevant main model:

>>> from hydpy.models.hland_96 import *

Opposed to the control file, importing the relevant submodels is unnecessary, as they
must already be available before reading the condition file.

The following call of function |controlcheck| is optional when working with a complete
HydPy project but required when executing a condition file independently for testing
(for the following doctests to work, we must not only remove the old wildcard import
artifacts but also fake to be "inside" a condition file by taking its name on):

>>> reverse_model_wildcard_import()
>>> temp = __file__
>>> __file__ = "land_dill_assl.py"
>>> controlcheck(projectdir=r"HydPy-H-Lahn", controldir="default", firstdate="1996-01-01", stepsize="1d")
>>> __file__ = temp

This step builds a connection to the corresponding control file.  We need this
connection for interactive testing because, for example, the shape of some condition
sequences depends on the control parameter |hland_control.NmbZones|:

>>> assert model.parameters.control.nmbzones == ic.shape[0]

The name |controlcheck| reflects that the function enables checking whether a condition
file is consistent with the corresponding control file.

.. note::

  A note for programmers: Behind the scenes, |controlcheck| operates like the control
  file function |parameterstep| to simplify the appearance of condition files.

Setting their values works like for control parameters with "bracket expressions" but
without land type-specific options because condition sequences usually contain
calculated values that tend to be dissimilar for all zones:

>>> sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
...    222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)
>>> uz(7.25228)

Setting the conditions of submodels requires writing the complete paths to the
respective sequences (we might add a more convenient syntax based on the `with
statement` later):

>>> model.rconcmodel.sequences.logs.quh(0.0)

.. _series_files:

Series files
____________

HydPy currently supports three different time `series file` formats, of which the ASCII
and the NetCDF-CF format should be the right choice in almost all applications.

HydPy's ASCII format (file ending ".asc") is simpler but less efficient.  Each file
stores the time series of one sequence type for one element.  By default, the filename
follows a strict pattern.  "land_dill_assl_hland_96_input_p.asc", for example, starts with
the element's name, continues with the relevant model type, and ends with the sequences
group and name.

Internally, each ASCII file starts with information about the covered data period and
the temporal resolution, described via a |Timegrid| instance.  Consider the following
example:

>>> from hydpy import Timegrid
>>> timegrid = Timegrid("1996-01-01", "1996-01-05", "1d")

The two dates define the start of the first and the end of the last data interval.
Hence, the example |Timegrid| instance would be suitable for a time series file
containing, for example, the precipitation sums of four days:

>>> assert len(timegrid) == 4

The data section after the |Timegrid| header contains no time stamps.  So, temporal
equidistance is strictly required, with missing values marked as |numpy.nan|.  The
individual time series of non-scalar sequences are placed in tab-separated columns.

HydPy's NetCDF-CF file format (file ending ".nc") is much more compact, usually times
faster, and supports reading and writing data "just in time" during simulation runs.
On the downside, it is more opaque and hard to handle because it stores all data in
binary form.  It follows the `NetCDF Climate and Forecast (CF) Metadata Conventions
<http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html>`_
and is, for example, compatible with `Delft-FEWS
<https://oss.deltares.nl/web/delft-fews>`_.

You can use function |summarise_ncfile| to gain insights into HydPy-compatible NetCDF
files. Here, we let it show the structure of the NetCDF precipitation input file of
the :ref:`HydPy-L-Lahn` example project:

>>> filepath = os.path.join(
...     data.__path__[0], "HydPy-H-Lahn", "series", "default", "hland_96_input_p.nc"
... )
>>> from hydpy import repr_, summarise_ncfile
>>> print(repr_(summarise_ncfile(filepath)))  # doctest: +ELLIPSIS
GENERAL
    file path = ...data/HydPy-H-Lahn/series/default/hland_96_input_p.nc
    file format = NETCDF4
    disk format = HDF5
    Attributes
        timereference = left interval boundary
DIMENSIONS
    time = 4018
    stations = 4
    char_leng_name = 11
VARIABLES
    time
        dimensions = time
        shape = 4018
        data type = float64
        Attributes
            _FillValue = -999.0
            units = hours since 1996-01-01 00:00:00 +01:00
    station_id
        dimensions = stations, char_leng_name
        shape = 4, 11
        data type = |S1
    hland_96_input_p
        dimensions = time, stations
        shape = 4018, 4
        data type = float64
        Attributes
            _FillValue = -999.0

The time series of all sequences of the same type are stored in one file.  So, by
default, a NetCDF filename is shorter than an ASCII filename as it does not need a
device-specific prefix (for example, `hland_96_input_p.nc` instead of
`land_dill_assl_hland_96_input_p.asc`).  The device names are instead managed by a
file-internal NetCDF variable named `station_id`, whose shape is determined by the
NetCDF dimensions `stations` (usually the number of devices, but see below) and
`char_leng_name` (usually the longest device name, but see below).

The second NetCDF variable used for describing the data layout is named `time`, whose
shape is determined by a NetCDF dimension also named `time`.  This variable contains
floating point numbers representing, for example, the elapsed days between a reference
date and the actual date (see method |Date.to_cfunits| of class |Date| for some
examples).

As far as we know, the NetCDF-CF convention does not clarify if these time points
define the start or the end time points of data measurement intervals (left timestep vs
right timestamp).  As a surrogate, HydPy inserts an attribute named `timereference`
when writing a NetCDF file, with the possible values `left interval boundary` and
`right interval boundary` for "interval data" and `current time` for "time point data".
We advise also adding this attribute when using other tools for writing NetCDF files to
be read by HydPy.

The time series are aligned in a (2-dimensional) matrix, with the first axis reflecting
the time and the second axis reflecting the location.  There are additional columns for
multi-dimensional sequences that address sublocations (for example, hydrological
response units).  The `station_id` variable distinguishes them by suffixing their
indexes to the device name.

See the documentation on module |netcdftools|, which uses many examples to explain the
NetCDF-CF format in more detail.

The third supported time series file format relies on the Numpy format (file ending
".npy").  It resembles the ASCII format but saves data in binary form.  We only
recommend if if one requires a more efficient alternative to the ASCII format and a
less complex alternative to the NetCDF format.

All time series files can specify dates with or without time zone information.  Without
time zone information, HydPy usually assumes the currently selected
|Options.utcoffset|, which defaults to +60 minutes.  The only exception is for NetCDF
files, where it always assumes UTC+00 in compliance with the NetCDF-CF conventions.

A new HydPy feature, applicable for all file formats but only realised for the group of
input sequences so far, is the alternative usage of standard names.  Class
|StandardInputNames| lists these standard names, and the input sequences of all model
types reference one of them.  When switching the time series naming
|SequenceManager.convention| from `model-specific` to `HydPy`, the filename
"land_dill_assl_hland_96_input_p.asc" becomes "land_dill_assl_precipitation.asc" and
"hland_96_input_p.nc" becomes "precipitation.nc".  Such a standardisation often means a
relevant simplification when dealing with multiple model types.

.. testsetup::

    >>> os.chdir(workingdir)
