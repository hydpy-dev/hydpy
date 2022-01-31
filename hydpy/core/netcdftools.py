# -*- coding: utf-8 -*-
"""
This module extends the features of module |filetools| for loading data from and
storing data to netCDF4 files, consistent with the `NetCDF Climate and Forecast (CF)
Metadata Conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/
cf-conventions.html>`_.

Usually, we apply the features implemented in this module only indirectly in three
steps:

  1. Call either method |SequenceManager.open_netcdfreader| or method
     |SequenceManager.open_netcdfwriter| of the |SequenceManager| object available in
     module |pub| to prepare a |NetCDFInterface| object for reading or writing.
  2. Call either the usual reading or writing methods of other HydPy classes like
     method |HydPy.load_fluxseries| of class |HydPy| or method
     |Elements.save_stateseries| of class |Elements|.  The prepared |NetCDFInterface|
     object collects all requests of those sequences one wants to read from or write to
     NetCDF files.
  3. Finalise reading or writing by calling either method
     |SequenceManager.close_netcdfreader| or |SequenceManager.close_netcdfwriter|.

Step 2 is a logging process only, telling the |NetCDFInterface| object which data needs
to be read or written.  The actual reading from or writing to NetCDF files is triggered
by step 3.

During step 2, the |NetCDFInterface| object and its subobjects are accessible, allowing
to inspect their current state or modify their behaviour.

The following real code examples show how to perform these three steps both for reading
and writing data, based on the example configuration defined by function
|prepare_io_example_1|:

>>> from hydpy.examples import prepare_io_example_1
>>> nodes, elements = prepare_io_example_1()

(1) We prepare a |NetCDFInterface| object for writing data by calling method
|SequenceManager.open_netcdfwriter|:

>>> from hydpy import pub
>>> pub.sequencemanager.open_netcdfwriter()

(2) We tell the |SequenceManager| to read and write all the time-series data from and
to NetCDF files placed within a folder called `example` (In real cases, you would not
write the `with TestIO():` line.  This code block makes sure we pollute the IO testing
directory instead of our current working directory):

>>> pub.sequencemanager.generalfiletype = "nc"
>>> from hydpy import TestIO
>>> with TestIO():
...     pub.sequencemanager.generaldirpath = "example"

(3) We store all the time-series handled by the |Node| and |Element| objects of the
example dataset by calling |Nodes.save_allseries| of class |Nodes| and
|Elements.save_allseries| of class |Elements|:

>>> nodes.save_allseries()
>>> elements.save_allseries()

(4) We again log all sequences, but this time after telling the |SequenceManager| to
average each time series spatially:

>>> pub.sequencemanager.generalaggregation = "mean"
>>> nodes.save_allseries()
>>> elements.save_allseries()

(5) We can now navigate into the details of the logged time series data via the
|NetCDFInterface| object and its subobjects.  For example, we can query the logged flux
sequence objects of type |lland_fluxes.NKor| belonging to application model |lland_v1|
(those of elements `element1` and `element2`; the trailing numbers are the indices of
the relevant hydrological response units):


>>> writer = pub.sequencemanager.netcdfwriter
>>> writer.lland_v1.flux_nkor.subdevicenames
('element1_0', 'element2_0', 'element2_1')

(6) In the example discussed here, all sequences are stored within the same folder
(`example`).  Storing sequences in separate folders goes hand in hand with storing them
in separate NetCDF files, of course.  In such cases, you have to include the folder
into the attribute name:

>>> writer.foldernames
('example',)
>>> writer.example_lland_v1.flux_nkor.subdevicenames
('element1_0', 'element2_0', 'element2_1')

(7) We close the |NetCDFInterface| object, which is the moment where the writing
process happens.  After that, the interface object is not available anymore:

>>> with TestIO():
...     pub.sequencemanager.close_netcdfwriter()
>>> pub.sequencemanager.netcdfwriter
Traceback (most recent call last):
...
hydpy.core.exceptiontools.AttributeNotReady: The sequence file manager does currently \
handle no NetCDF writer object.

(8) We set the time series values of two test sequences to zero, which serves the
purpose to demonstrate that reading the data back in actually works:

>>> nodes.node2.sequences.sim.series = 0.0
>>> elements.element2.model.sequences.fluxes.nkor.series = 0.0

(9) We move up a gear and and prepare a |NetCDFInterface| object for reading data, log
all |NodeSequence| and |ModelSequence| objects, and read their time series data from
the created NetCDF file.  Note that we disable the |Options.checkseries| option
temporarily to prevent raising an exception when reading incomplete data from file:

>>> pub.sequencemanager.open_netcdfreader()
>>> nodes.load_simseries()
>>> elements.load_allseries()
>>> with TestIO():
...     with pub.options.checkseries(False):
...         pub.sequencemanager.close_netcdfreader()

(10) We check if the data is available via the test sequences again:

>>> nodes.node2.sequences.sim.series
InfoArray([64., 65., 66., 67.])
>>> elements.element2.model.sequences.fluxes.nkor.series
InfoArray([[16., 17.],
           [18., 19.],
           [20., 21.],
           [22., 23.]])
>>> pub.sequencemanager.netcdfreader
Traceback (most recent call last):
...
RuntimeError: The sequence file manager does currently handle no NetCDF reader object.

(11) We cannot invert spatial aggregation.  Hence reading averaged time series is left
for postprocessing tools.  To show that writing the averaged series worked, we access
both relevant NetCDF files more directly using the underlying NetCDF4 library (note
that averaging 1-dimensional time series as those of node sequence |Sim| is allowed for
the sake of consistency):

>>> from hydpy.core.netcdftools import netcdf4
>>> from numpy import array
>>> with TestIO():
...     with netcdf4.Dataset("example/node.nc") as ncfile:
...         array(ncfile["sim_q_mean"][:])
array([[60.],
       [61.],
       [62.],
       [63.]])
>>> with TestIO():
...     with netcdf4.Dataset("example/lland_v1.nc") as ncfile:
...         array(ncfile["flux_nkor_mean"][:])[:, 1]
array([16.5, 18.5, 20.5, 22.5])

Besides the testing related specialities, the described workflow is more or less
standard but allows for different modifications.  We illustrate them in the
documentation of the other features implemented in module |netcdftools|, but also in
the documentation on class |SequenceManager| of module |filetools| and class
|IOSequence| of module |sequencetools|.

The examples above give little insight into the NetCDF files' resulting/required
structure. One should at least be aware of the optional argument `isolate`.  When
"isolating" data, all |IOSequence| objects of a specific subclass belong to a single
NetCDF file.  When reading a NetCDF file, one has to choose the same option used for
writing.

Using the NetCDF format allows reading or writing data "just in time" during simulation
runs.  The documentation of class "HydPy" explains how to select and set the relevant
|IOSequence| objects for this option.  See the documentation on method
|NetCDFInterface.provide_jitaccess| of class |NetCDFInterface| for more in-depth
information.
"""
# import...
# ...from standard library
from __future__ import annotations
import abc
import collections
import contextlib
import itertools
import os
from typing import *

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    import netCDF4 as netcdf4
else:
    netcdf4 = exceptiontools.OptionalImport("netcdf4", ["netCDF4"], locals())

dimmapping = {
    "nmb_timepoints": "time",
    "nmb_subdevices": "stations",
    "nmb_characters": "char_leng_name",
}
"""Dimension related terms within NetCDF files.

You can change this mapping if it does not suit your requirements.  For example, change 
the value of the keyword "nmb_subdevices" if you prefer to call this dimension 
"location" instead of "stations" within NetCDF files:

>>> from hydpy.core.netcdftools import dimmapping
>>> dimmapping["nmb_subdevices"] = "location"
"""

varmapping = {"timepoints": "time", "subdevices": "station_id"}
"""Variable related terms within NetCDF files.

You can change this mapping if it does not suit your requirements.  For example, change 
the value of the keyword "timepoints" if you prefer to call this variable "period" 
instead of "time" within NetCDF files:

>>> from hydpy.core.netcdftools import varmapping
>>> varmapping["timepoints"] = "period"
"""

fillvalue = numpy.nan
"""Default fill value for writing NetCDF files.

You can set another |float| value before writing a NetCDF file:

>>> from hydpy.core import netcdftools
>>> netcdftools.fillvalue = -777.0
"""


NetCDFVariable = Union["NetCDFVariableFlat", "NetCDFVariableAgg"]


def str2chars(strings: Sequence[str]) -> NDArrayFloat:
    """Return a |numpy.ndarray| object containing the byte characters (second axis) of
    all given strings (first axis).

    >>> from hydpy.core.netcdftools import str2chars
    >>> str2chars(["zeros", "ones"])
    array([[b'z', b'e', b'r', b'o', b's'],
           [b'o', b'n', b'e', b's', b'']], dtype='|S1')

    >>> str2chars([])
    array([], shape=(0, 0), dtype='|S1')
    """
    maxlen = 0
    for name in strings:
        maxlen = max(maxlen, len(name))
    chars = numpy.full((len(strings), maxlen), b"", dtype="|S1")
    for idx, name in enumerate(strings):
        for jdx, char in enumerate(name):
            chars[idx, jdx] = char.encode("utf-8")
    return chars


def chars2str(chars: Sequence[Sequence[bytes]]) -> List[str]:
    """Inversion function of |str2chars|.

    >>> from hydpy.core.netcdftools import chars2str

    >>> chars2str([[b"z", b"e", b"r", b"o", b"s"],
    ...            [b"o", b"n", b"e", b"s", b""]])
    ['zeros', 'ones']

    >>> chars2str([])
    []
    """
    strings: Deque[str] = collections.deque()
    for subchars in chars:
        substrings: Deque[str] = collections.deque()
        for char in subchars:
            if char:
                substrings.append(char.decode("utf-8"))
            else:
                substrings.append("")
        strings.append("".join(substrings))
    return list(strings)


def create_dimension(ncfile: netcdf4.Dataset, name: str, length: int) -> None:
    """Add a new dimension with the given name and length to the given NetCDF file.

    Essentially, |create_dimension| only calls the equally named method of the NetCDF
    library but adds information to possible error messages:

    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("test.nc", "w")
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, "dim1", 5)
    >>> dim = ncfile.dimensions["dim1"]
    >>> dim.size if hasattr(dim, "size") else dim
    5

    >>> try:
    ...     create_dimension(ncfile, "dim1", 5)
    ... except BaseException as exc:
    ...     print(exc)    # doctest: +ELLIPSIS
    While trying to add dimension `dim1` with length `5` to the NetCDF file `test.nc`, \
the following error occurred: ...

    >>> ncfile.close()
    """
    try:
        ncfile.createDimension(name, length)
    except BaseException:
        objecttools.augment_excmessage(
            f"While trying to add dimension `{name}` with length `{length}` to the "
            f"NetCDF file `{get_filepath(ncfile)}`"
        )


def create_variable(
    ncfile: netcdf4.Dataset,
    name: str,
    datatype: str,
    dimensions: Sequence[str],
) -> None:
    """Add a new variable with the given name, datatype, and dimensions to the given
    NetCDF file.

    Essentially, |create_variable| only calls the equally named method of the NetCDF
    library but adds information to possible error messages:

    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("test.nc", "w")
    >>> from hydpy.core.netcdftools import create_variable
    >>> try:
    ...     create_variable(ncfile, "var1", "f8", ("dim1",))
    ... except BaseException as exc:
    ...     print(str(exc).strip('"'))    # doctest: +ELLIPSIS
    While trying to add variable `var1` with datatype `f8` and dimensions `('dim1',)` \
to the NetCDF file `test.nc`, the following error occurred: ...

    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, "dim1", 5)
    >>> create_variable(ncfile, "var1", "f8", ("dim1",))
    >>> import numpy
    >>> numpy.array(ncfile["var1"][:])
    array([nan, nan, nan, nan, nan])

    >>> ncfile.close()
    """
    default = fillvalue if (datatype == "f8") else None
    try:
        ncfile.createVariable(name, datatype, dimensions=dimensions, fill_value=default)
        ncfile[name].long_name = name
    except BaseException:
        objecttools.augment_excmessage(
            f"While trying to add variable `{name}` with datatype `{datatype}` and "
            f"dimensions `{dimensions}` to the NetCDF file `{get_filepath(ncfile)}`"
        )


def query_variable(ncfile: netcdf4.Dataset, name: str) -> netcdf4.Variable:
    """Return the variable with the given name from the given NetCDF file.

    Essentially, |query_variable| only queries the variable via keyword access using
    the NetCDF library but adds information to possible error messages:

    >>> from hydpy.core.netcdftools import query_variable
    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> with TestIO():
    ...     file_ = netcdf4.Dataset("model.nc", "w")
    >>> query_variable(file_, "flux_prec")
    Traceback (most recent call last):
    ...
    RuntimeError: NetCDF file `model.nc` does not contain variable `flux_prec`.

    >>> from hydpy.core.netcdftools import create_variable
    >>> create_variable(file_, "flux_prec", "f8", ())
    >>> isinstance(query_variable(file_, "flux_prec"), netcdf4.Variable)
    True

    >>> file_.close()
    """
    try:
        return ncfile[name]
    except (IndexError, KeyError):
        raise RuntimeError(
            f"NetCDF file `{get_filepath(ncfile)}` does not contain variable `{name}`."
        ) from None


def query_timegrid(ncfile: netcdf4.Dataset) -> timetools.Timegrid:
    """Return the |Timegrid| defined by the given NetCDF file.

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> from hydpy.core.netcdftools import query_timegrid
    >>> filepath = "LahnH/series/input/hland_v1_input_t.nc"
    >>> with TestIO():
    ...     with netcdf4.Dataset(filepath) as ncfile:
    ...         query_timegrid(ncfile)
    Timegrid("1996-01-01 00:00:00",
             "2007-01-01 00:00:00",
             "1d")
    """
    timepoints = ncfile[varmapping["timepoints"]]
    refdate = timetools.Date.from_cfunits(timepoints.units)
    return timetools.Timegrid.from_timepoints(
        timepoints=timepoints[:],
        refdate=refdate,
        unit=timepoints.units.strip().split()[0],
    )


def query_array(ncfile: netcdf4.Dataset, name: str) -> NDArrayFloat:
    """Return the data of the variable with the given name from the given NetCDF file.

    The following example shows that |query_array| returns |numpy.nan| entries to
    represent missing values even when the respective NetCDF variable defines a
    different fill value:

    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> from hydpy.core import netcdftools
    >>> netcdftools.fillvalue = -999.0
    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         netcdftools.create_dimension(ncfile, "dim1", 5)
    ...         netcdftools.create_variable(ncfile, "var1", "f8", ("dim1",))
    ...     ncfile = netcdf4.Dataset("test.nc", "r")
    >>> netcdftools.query_variable(ncfile, "var1")[:].data
    array([-999., -999., -999., -999., -999.])
    >>> netcdftools.query_array(ncfile, "var1")
    array([nan, nan, nan, nan, nan])
    >>> import numpy
    >>> netcdftools.fillvalue = numpy.nan
    >>> ncfile.close()
    """
    variable = query_variable(ncfile, name)
    maskedarray = variable[:]
    fillvalue_ = getattr(variable, "_FillValue", numpy.nan)
    if not numpy.isnan(fillvalue_):
        maskedarray[maskedarray.mask] = numpy.nan
    return cast(NDArrayFloat, maskedarray.data)


def get_filepath(ncfile: netcdf4.Dataset) -> str:
    """Return the path of the given NetCDF file.

    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> from hydpy.core.netcdftools import get_filepath
    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         get_filepath(ncfile)
    'test.nc'
    """
    filepath = ncfile.filepath() if hasattr(ncfile, "filepath") else ncfile.filename
    return cast(str, filepath)


class JITAccessInfo(NamedTuple):
    """Helper class for structuring reading from or writing to a NetCDF file "just in
    time" during a simulation run for a specific |NetCDFVariableFlat| object."""

    ncvariable: netcdf4.Variable
    """Variable for the direct access to the relevant section of the NetCDF file."""
    timedelta: int
    """Difference between the relevant row of the NetCDF file and the current 
    simulation index (as defined by |Idx_Sim|)."""
    columns: Tuple[int, ...]
    """Indices of the relevant columns of the NetCDF file correctly ordered with 
    respect to |JITAccessInfo.data|."""
    data: NDArrayFloat
    """Bridge to transfer data between the NetCDF file and the (cythonized) 
    hydrological models."""


class JITAccessHandler(NamedTuple):
    """Handler used by the |SequenceManager| object available in module |pub| for
    reading data from and/or writing data to NetCDF files at each step of a simulation
    run."""

    readers: Tuple[JITAccessInfo, ...]
    """All |JITAccessInfo| objects responsible for reading data during the simulation 
    run."""
    writers: Tuple[JITAccessInfo, ...]
    """All |JITAccessInfo| objects responsible for writing data during the simulation 
    run."""

    def read_slices(self, idx: int) -> None:
        """Read the time slice relevant for the current simulation step from each
        NetCDF file selected for reading."""
        for reader in self.readers:
            reader.data[:] = reader.ncvariable[idx + reader.timedelta, reader.columns]

    def write_slices(self, idx: int) -> None:
        """Write the time slice relevant for the current simulation step from each
        NetCDF file selected for writing."""
        for writer in self.writers:
            writer.ncvariable[idx + writer.timedelta, writer.columns] = writer.data


class NetCDFInterface:
    """Interface between |SequenceManager| and multiple NetCDF files.

    The core task of class |NetCDFInterface| is to distribute different |IOSequence|
    objects on multiple instances of class |NetCDFFile|.

    (1) We prepare a |SequenceManager| object and some devices handling different
    sequences by applying function |prepare_io_example_1|:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    (2) We collect all sequences used in the following examples:

    >>> sequences = []
    >>> for node in nodes:
    ...     sequences.append(node.sequences.sim)
    >>> for element in elements:
    ...     if element.model.name == "hland_v1":
    ...         sequences.append(element.model.sequences.states.sp)
    ...     else:
    ...         sequences.append(element.model.sequences.inputs.nied)
    ...         sequences.append(element.model.sequences.fluxes.nkor)

    (3) We prepare a |NetCDFInterface| object and log and write all test sequences.
    Due to setting `isolate` to |False|, |NetCDFInterface| initialises one |NetCDFFile|
    object for the |NodeSequence| objects, two |NetCDFFile| objects for the
    |InputSequence| objects of application models |lland_v1| and |lland_v2|, two
    |NetCDFFile| objects for the |FluxSequence| objects of application models |lland_v1|
    and |lland_v2|, and one |NetCDFFile| object for the |StateSequence| of |hland_v1|.
    To avoid name conflicts, we always store time series of nodes and different model
    types in separate NetCDF files  Principally, you can keep |InputSequence| and
    |FluxSequence| data in the same NetCDF file, but we stick to the default and store
    them in different folders.  The above assertions should become more transparent
    when looking at the following attempts to query the |NetCDFFile| objects related
    to |lland_v2|:

    >>> from hydpy.core.netcdftools import NetCDFInterface
    >>> interface = NetCDFInterface(isolate=False)
    >>> len(interface)
    0
    >>> for sequence in sequences:
    ...     _ = interface.log(sequence, sequence.series)
    ...     _ = interface.log(sequence, sequence.average_series())
    >>> len(interface)
    6
    >>> interface.filenames
    ('hland_v1', 'lland_v1', 'lland_v2', 'node')
    >>> interface.node.variablenames
    ('sim_q', 'sim_q_mean', 'sim_t', 'sim_t_mean')
    >>> interface.node == interface.nodepath_node
    True
    >>> interface.lland_v2
    Traceback (most recent call last):
    ...
    AttributeError: The current NetCDFInterface object does handle multiple NetCDFFile \
objects named `lland_v2`.  Please be more specific.
    >>> hasattr(interface, "outputpath_lland_v2")
    True
    >>> "outputpath_lland_v2" in dir(interface)
    True
    >>> interface.lland_v3
    Traceback (most recent call last):
    ...
    AttributeError: The current NetCDFInterface object does neither handle a \
NetCDFFile object named `lland_v3` nor does it define a member named `lland_v3`.

    (4) We store all NetCDF files into the `inputpath`, `outputpath`, and `nodepath`
    folders of the testing directory, defined by |prepare_io_example_1|:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     interface.write()

    (5) We define a shorter initialisation period and re-activate the time series of
    the test sequences:

    >>> from hydpy import pub
    >>> pub.timegrids = "02.01.2000", "04.01.2000", "1d"
    >>> for sequence in sequences:
    ...     sequence.prepare_series(allocate_ram=False)
    ...     sequence.prepare_series(allocate_ram=True)

    (6) We again initialise class |NetCDFInterface|, log all test sequences, and read
    the test data of the defined subperiod:

    >>> from hydpy.core.netcdftools import NetCDFInterface
    >>> interface = NetCDFInterface(isolate=False)
    >>> for sequence in sequences:
    ...     _ = interface.log(sequence, None)

    >>> with TestIO():
    ...     interface.read()
    >>> nodes.node1.sequences.sim.series
    InfoArray([61., 62.])
    >>> elements.element2.model.sequences.fluxes.nkor.series
    InfoArray([[18., 19.],
               [20., 21.]])
    >>> elements.element4.model.sequences.states.sp.series
    InfoArray([[[74., 75., 76.],
                [77., 78., 79.]],
    <BLANKLINE>
               [[80., 81., 82.],
                [83., 84., 85.]]])

    (7) We repeat the above steps, except setting isolate` to |True|.  The relevant
    difference is that |NetCDFInterface| now initialises a new |NetCDFFile| object for
    each sequence type, resulting in a larger number of separate NetCDF files, each one
    containing only one NetCDF variable:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    >>> sequences = []
    >>> for node in nodes:
    ...     sequences.append(node.sequences.sim)
    >>> for element in elements:
    ...     if element.model.name == "hland_v1":
    ...         sequences.append(element.model.sequences.states.sp)
    ...     else:
    ...         sequences.append(element.model.sequences.inputs.nied)
    ...         sequences.append(element.model.sequences.fluxes.nkor)

    >>> interface = NetCDFInterface(isolate=True)
    >>> for sequence in sequences:
    ...     _ = interface.log(sequence, sequence.series)
    ...     _ = interface.log(sequence, sequence.average_series())
    >>> from pprint import pprint
    >>> pprint(interface.filenames)
    ('hland_v1_state_sp',
     'hland_v1_state_sp_mean',
     'lland_v1_flux_nkor',
     'lland_v1_flux_nkor_mean',
     'lland_v1_input_nied',
     'lland_v1_input_nied_mean',
     'lland_v2_flux_nkor',
     'lland_v2_flux_nkor_mean',
     'lland_v2_input_nied',
     'lland_v2_input_nied_mean',
     'node_sim_q',
     'node_sim_q_mean',
     'node_sim_t',
     'node_sim_t_mean')
    >>> interface.lland_v1_input_nied_mean.variablenames
    ('input_nied_mean',)

    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.outputpath = ""
    ...     interface.write()

    >>> from hydpy import pub
    >>> pub.timegrids = "02.01.2000", "04.01.2000", "1d"
    >>> for sequence in sequences:
    ...     sequence.prepare_series()

    >>> interface = NetCDFInterface(isolate=True)
    >>> for sequence in sequences:
    ...     _ = interface.log(sequence, None)
    >>> with TestIO():
    ...     interface.read()
    >>> nodes.node1.sequences.sim.series
    InfoArray([61., 62.])
    >>> elements.element2.model.sequences.fluxes.nkor.series
    InfoArray([[18., 19.],
               [20., 21.]])
    >>> elements.element4.model.sequences.states.sp.series
    InfoArray([[[74., 75., 76.],
                [77., 78., 79.]],
    <BLANKLINE>
               [[80., 81., 82.],
                [83., 84., 85.]]])

    (8) We technically confirm that |NetCDFInterface| passes the `isolate`  argument
    correctly to the constructor of class |NetCDFFile|:

    >>> from unittest.mock import patch
    >>> with patch("hydpy.core.netcdftools.NetCDFFile") as mock:
    ...     interface = NetCDFInterface(isolate=True)
    ...     _ = interface.log(sequences[0], sequences[0].series)
    ...     mock.assert_called_once_with(
    ...         name="node_sim_q", isolate=True, dirpath="nodepath")
    >>> with patch("hydpy.core.netcdftools.NetCDFFile") as mock:
    ...     interface = NetCDFInterface(isolate=False)
    ...     _ = interface.log(sequences[0], sequences[0].series)
    ...     mock.assert_called_once_with(name="node", isolate=False, dirpath="nodepath")
    """

    folders: Dict[str, Dict[str, NetCDFFile]]
    _isolate: bool

    def __init__(self, isolate: bool) -> None:
        self._isolate = isolate
        self.folders = {}

    def log(
        self,
        sequence: sequencetools.IOSequence[Any, Any],
        infoarray: Optional[sequencetools.InfoArray] = None,
    ) -> Tuple[NetCDFFile, NetCDFVariable]:
        """Prepare a |NetCDFFile| object suitable for the given |IOSequence| object,
        when necessary, and pass the given arguments to its |NetCDFFile.log| method."""
        if isinstance(sequence, sequencetools.ModelSequence):
            descr = sequence.descr_model
        else:
            descr = "node"
        if self._isolate:
            descr = f"{descr}_{sequence.descr_sequence}"
            if (infoarray is not None) and (infoarray.info["type"] != "unmodified"):
                descr = f"{descr}_{infoarray.info['type']}"
        dirpath = sequence.dirpath
        try:
            files: Dict[str, NetCDFFile] = self.folders[dirpath]
        except KeyError:
            files = {}
            self.folders[dirpath] = files
        try:
            file_ = files[descr]
        except KeyError:
            file_ = NetCDFFile(name=descr, isolate=self._isolate, dirpath=dirpath)
            files[descr] = file_
        return file_, file_.log(sequence, infoarray)

    def read(self) -> None:
        """Call method |NetCDFFile.read| of all handled |NetCDFFile| objects."""
        for ncfile_ in self:
            ncfile_.read()

    def write(self) -> None:
        """Call method |NetCDFFile.write| of all handled |NetCDFFile| objects."""
        if self.folders:
            init = hydpy.pub.timegrids.init
            timeunits = init.firstdate.to_cfunits("hours")
            timepoints = init.to_timepoints("hours")
            for ncfile in self:
                ncfile.write(timeunits, timepoints)

    @staticmethod
    def _yield_disksequences(
        deviceorder: Iterable[Union[devicetools.Node, devicetools.Element]]
    ) -> Iterator[sequencetools.IOSequence[Any, Any]]:
        for device in deviceorder:
            if isinstance(device, devicetools.Node):
                for sequence in device.sequences:
                    yield sequence
            else:
                for subseqs in device.model.sequences.iosubsequences:
                    for sequence in subseqs:
                        yield sequence

    @contextlib.contextmanager
    def provide_jitaccess(
        self, deviceorder: Iterable[Union[devicetools.Node, devicetools.Element]]
    ) -> Iterator[JITAccessHandler]:
        """Allow method |HydPy.simulate| of class |HydPy| to read data from or write
        data to NetCDF files "just in time" during simulation runs.

        We consider it unlikely users need ever to call the method
        |NetCDFInterface.provide_jitaccess| directly.  See the documentation on class
        |HydPy| on applying it indirectly.  However, the following explanations might
        give some additional insights on options and limitations of the the related
        functionalities.

        You can only either read from or write to each NetCDF file.  We think this
        should rarely be a limitation for the anticipated workflows.  One particular
        situation where one could eventually try to read and write simultaneously is
        when trying to overwrite some of the available input data.  The following
        example tries to read the input data for all "headwater" catchments from
        specific NetCDF files but defines zero input values for all "non-headwater"
        catchments and tries to write them into the same files:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, print_values, pub, TestIO
        >>> with TestIO():
        ...     hp = HydPy("LahnH")
        ...     pub.timegrids = "1996-01-01", "1996-01-05", "1d"
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     hp.load_conditions()
        ...     headwaters = pub.selections["headwaters"].elements
        ...     nonheadwaters = pub.selections["nonheadwaters"].elements
        ...     headwaters.prepare_inputseries(allocate_ram=False, read_jit=True)
        ...     nonheadwaters.prepare_inputseries(allocate_ram=True, write_jit=True)
        ...     for element in nonheadwaters:
        ...         for sequence in element.model.sequences.inputs:
        ...             sequence.series = 0.0
        ...     hp.simulate()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
For a specific NetCDF file, you can either read or write data during a simulation run \
but for file `hland_v1_input_p` both is requested.

        Clearly, each NetCDF file we want to read data from needs to span the current
        simulation period:

        >>> with TestIO():
        ...     pub.timegrids.init.firstdate = "1990-01-01"
        ...     pub.timegrids.sim.firstdate = "1995-01-01"
        ...     hp.prepare_inputseries(allocate_ram=False, read_jit=True)
        ...     hp.simulate()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
The data of the NetCDF `hland_v1_input_p` \
(Timegrid("1996-01-01 00:00:00", "2007-01-01 00:00:00", "1d")) does not correctly \
cover the current simulation period \
(Timegrid("1995-01-01 00:00:00", "1996-01-05 00:00:00", "1d")).

        However, be aware that each NetCDF file selected for writing must also cover
        the complete initialisation period.  If there is no adequately named NetCDF
        file, |NetCDFInterface.provide_jitaccess| creates a new one for the current
        initialisation period.  If an adequately named file exists,
        |NetCDFInterface.provide_jitaccess| uses it without any attempt to extend it
        temporally or spatially.  The following example shows the insertion of the
        output data of two subsequent simulation runs into the same NetCDF files:

        >>> with TestIO():
        ...     pub.timegrids = "1996-01-01", "1996-01-05", "1d"
        ...     hp.prepare_inputseries(allocate_ram=False, read_jit=True)
        ...     hp.prepare_factorseries(allocate_ram=True, write_jit=True)
        ...     pub.timegrids.sim.lastdate = "1996-01-03"
        ...     hp.simulate()
        ...     pub.timegrids.sim.firstdate = "1996-01-03"
        ...     pub.timegrids.sim.lastdate = "1996-01-05"
        ...     hp.simulate()
        >>> print_values(hp.elements["land_dill"].model.sequences.factors.tmean.series)
        -0.572053, -1.084746, -2.767055, -6.242055
        >>> from hydpy.core.netcdftools import netcdf4
        >>> filepath = "LahnH/series/output/hland_v1_factor_tmean.nc"
        >>> with TestIO():
        ...     with netcdf4.Dataset(filepath, "r") as ncfile:
        ...         print_values(ncfile["factor_tmean"][:, 0])
        -0.572053, -1.084746, -2.767055, -6.242055

        If we try to write the output of a third simulation run beyond the original
        initial initialisation period into the same files,
        |NetCDFInterface.provide_jitaccess| raises an equal error as above:

        >>> with TestIO():
        ...     pub.timegrids = "1996-01-05", "1996-01-10", "1d"
        ...     hp.prepare_inputseries(allocate_ram=True, read_jit=False)
        ...     hp.prepare_factorseries(allocate_ram=True, write_jit=True)
        ...     hp.simulate()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
The data of the NetCDF `hland_v1_factor_tmean` \
(Timegrid("1996-01-01 00:00:00", "1996-01-05 00:00:00", "1d")) does not correctly \
cover the current simulation period \
(Timegrid("1996-01-05 00:00:00", "1996-01-10 00:00:00", "1d")).

        >>> hp.prepare_factorseries(allocate_ram=False, write_jit=False)

        Regarding the spatial dimension, things are similar.  You can write data for
        different sequences in subsequent simulation runs, but you need to ensure all
        required data columns are available right from the start.  Hence, relying on
        the automatic file generation of |NetCDFInterface.provide_jitaccess| fails in
        the following example:

        >>> with TestIO():
        ...     pub.timegrids = "1996-01-01", "1996-01-05", "1d"
        ...     hp.prepare_inputseries(allocate_ram=False, read_jit=True)
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.simulate()
        ...     nonheadwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
No data for sequence `flux_pc` and (sub)device `land_lahn_2_0` in NetCDF file \
`...hland_v1_flux_pc.nc` available.

        One way to prepare complete NetCDF files that are *HydPy* compatible is to work
        with an ordinary NetCDF writer object via |SequenceManager.open_netcdfwriter|:

        >>> with TestIO():
        ...     hp.prepare_fluxseries(allocate_ram=False, write_jit=False)
        ...     hp.prepare_fluxseries(allocate_ram=True, write_jit=False)
        ...     pub.sequencemanager.fluxfiletype = "nc"
        ...     pub.sequencemanager.open_netcdfwriter(isolate=True)
        ...     hp.save_fluxseries()
        ...     pub.sequencemanager.close_netcdfwriter()
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for element in hp.elements.search_keywords("catchment"):
        ...     print_values(element.model.sequences.fluxes.qt.series)
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        20.58932, 8.66144, 7.281198, 6.402232
        11.674045, 10.110371, 8.991987, 8.212314
        >>> filepath_qt = "LahnH/series/output/hland_v1_flux_qt.nc"
        >>> with TestIO():
        ...     with netcdf4.Dataset(filepath_qt, "r") as ncfile:
        ...         for jdx in range(4):
        ...             print_values(ncfile["flux_qt"][:, jdx])
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        0.0, 0.0, 0.0, 0.0
        0.0, 0.0, 0.0, 0.0
        >>> with TestIO():
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=False)
        ...     nonheadwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> with TestIO():
        ...     with netcdf4.Dataset(filepath_qt, "r") as ncfile:
        ...         for jdx in range(4):
        ...             print_values(ncfile["flux_qt"][:, jdx])
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        20.58932, 8.66144, 7.281198, 6.402232
        11.674045, 10.110371, 8.991987, 8.212314

        >>> hp.prepare_fluxseries(allocate_ram=False, write_jit=False)

        There should be no limitation for reading data "just in time" and using
        different |Node.deploymode| options.  For demonstration, we first calculate the
        time series of the |Sim| sequences of all nodes, assign them to the
        corresponding |Obs| sequences afterwards, and then start another simulation to
        (again) write both the simulated and the observed values to NetCDF files:

        >>> with TestIO():
        ...     hp.prepare_simseries(allocate_ram=True, write_jit=True)
        ...     hp.prepare_obsseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        ...     for idx, node in enumerate(hp.nodes):
        ...         node.sequences.obs.series = node.sequences.sim.series
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for node in hp.nodes:
        ...     print_values(node.sequences.sim.series)
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        42.3697, 27.210443, 22.930066, 20.20133
        54.043745, 37.320814, 31.922053, 28.413644
        >>> for node in hp.nodes:
        ...     print_values(node.sequences.obs.series)
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        42.3697, 27.210443, 22.930066, 20.20133
        54.043745, 37.320814, 31.922053, 28.413644
        >>> filepath_sim = "LahnH/series/node/node_sim_q.nc"
        >>> with TestIO():
        ...     with netcdf4.Dataset(filepath_sim, "r") as ncfile:
        ...         for jdx in range(4):
        ...             print_values(ncfile["sim_q"][:, jdx])
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        42.3697, 27.210443, 22.930066, 20.20133
        54.043745, 37.320814, 31.922053, 28.413644
        >>> filepath_obs = "LahnH/series/node/node_obs_q.nc"
        >>> with TestIO():
        ...     with netcdf4.Dataset(filepath_obs, "r") as ncfile:
        ...         for jdx in range(4):
        ...             print_values(ncfile["obs_q"][:, jdx])
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        42.3697, 27.210443, 22.930066, 20.20133
        54.043745, 37.320814, 31.922053, 28.413644

        Now we stop all sequences from writing to NetCDF files, remove the two
        headwater elements from the currently active selection, and start another
        simulation run.  The time series of both headwater nodes are zero due to the
        missing inflow from their inlet headwater sub-catchments.  The non-headwater
        nodes only receive inflow from the two non-headwater sub-catchments:

        >>> with TestIO():
        ...     hp.prepare_simseries(allocate_ram=True, write_jit=False)
        ...     hp.prepare_obsseries(allocate_ram=True, write_jit=False)
        ...     hp.update_devices(nodes=hp.nodes, elements=hp.elements - headwaters)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for node in hp.nodes:
        ...     print_values(node.sequences.sim.series)
        0.0, 0.0, 0.0, 0.0
        0.0, 0.0, 0.0, 0.0
        30.58932, 8.66144, 7.281198, 6.402232
        42.263365, 18.771811, 16.273185, 14.614546

        Finally, we set the |Node.deploymode| of the headwater nodes `dill` and
        `lahn_1` to `oldsim` and `obs`, respectively, and read their previously written
        time series "just in time".  As expected, the values of the two non-headwater
        nodes are identical to those of our initial example:

        >>> with TestIO():
        ...     hp.nodes["dill"].prepare_simseries(allocate_ram=True, read_jit=True)
        ...     hp.nodes["dill"].deploymode = "oldsim"
        ...     hp.nodes["lahn_1"].prepare_obsseries(allocate_ram=True, read_jit=True)
        ...     hp.nodes["lahn_1"].deploymode = "obs"
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for node in hp.nodes:
        ...     print_values(node.sequences.sim.series)
        11.78038, 8.901179, 7.131072, 6.017787
        0.0, 0.0, 0.0, 0.0
        42.3697, 27.210443, 22.930066, 20.20133
        54.043745, 37.320814, 31.922053, 28.413644
        """

        readers: List[JITAccessInfo] = []
        writers: List[JITAccessInfo] = []
        file2readmode: Dict[NetCDFFile, bool] = {}
        variable2ncfile: Dict[NetCDFVariableFlat, NetCDFFile] = {}
        variable2infos: Dict[NetCDFVariableFlat, List[JITAccessInfo]] = {}
        variable2sequences: DefaultDict[
            NetCDFVariableFlat, List[sequencetools.IOSequence[Any, Any]]
        ] = collections.defaultdict(lambda: [])

        try:
            # collect the relevant sequences:
            log = self.log
            for sequence in self._yield_disksequences(deviceorder):
                if sequence.diskflag:
                    file_, variable = log(sequence)
                    assert isinstance(variable, NetCDFVariableFlat)
                    readmode = sequence.diskflag_reading
                    file2readmode.setdefault(file_, readmode)
                    if file2readmode[file_] != readmode:
                        raise RuntimeError(
                            f"For a specific NetCDF file, you can either read or "
                            f"write data during a simulation run but for file "
                            f"`{file_.name}` both is requested."
                        )
                    variable2ncfile[variable] = file_
                    variable2infos[variable] = readers if readmode else writers
                    variable2sequences[variable].append(sequence)

            if variable2sequences:
                # prepare NetCDF files:
                file2timedelta: Dict[NetCDFFile, int] = {}
                tg_init = hydpy.pub.timegrids.init
                tg_sim = hydpy.pub.timegrids.sim
                timeunit = tg_init.firstdate.to_cfunits("hours")
                timepoints = tg_init.to_timepoints("hours")
                for file_, readmode in file2readmode.items():
                    if not os.path.exists(file_.filepath):
                        file_.write(timeunit, timepoints)
                    ncfile = netcdf4.Dataset(file_.filepath, "r+")
                    file_.ncfile = ncfile
                    tg_ncfile = query_timegrid(ncfile)
                    if tg_sim not in tg_ncfile:
                        raise RuntimeError(
                            f"The data of the NetCDF `{file_.name}` ({tg_ncfile}) "
                            f"does not correctly cover the current simulation period "
                            f"({tg_sim})."
                        )
                    file2timedelta[file_] = tg_init[tg_ncfile.firstdate]

                # make information for reading and writing temporarily available:
                for variable, sequences in variable2sequences.items():
                    file_ = variable2ncfile[variable]
                    ncfile = file_.ncfile
                    assert ncfile is not None
                    get = variable.query_subdevice2index(ncfile).get_index
                    data: NDArrayFloat = numpy.full(
                        variable.shape[1], numpy.nan, dtype=float
                    )
                    variable2infos[variable].append(
                        JITAccessInfo(
                            ncvariable=ncfile[variable.name],
                            timedelta=file2timedelta[file_],
                            columns=tuple(get(n) for n in variable.subdevicenames),
                            data=data,
                        )
                    )
                    idx0 = 0
                    for sequence in sequences:
                        idx1 = idx0 + int(numpy.product(sequence.shape))
                        sequence.connect_netcdf(ncarray=data[idx0:idx1])
                        idx0 = idx1
                yield JITAccessHandler(readers=tuple(readers), writers=tuple(writers))

            else:
                # return without useless efforts:
                yield JITAccessHandler(readers=(), writers=())

        except BaseException:
            objecttools.augment_excmessage(
                "While trying to prepare NetCDF files for reading or writing data "
                '"just in time" during the current simulation run'
            )
        finally:
            # close NetCDF files:
            for file_ in file2readmode:
                ncfile = file_.ncfile
                if ncfile is not None:
                    ncfile.close()

    @property
    def foldernames(self) -> Tuple[str, ...]:
        """The names of all folders the sequences shall be read from or written to."""
        return tuple(self.folders.keys())

    @property
    def filenames(self) -> Tuple[str, ...]:
        """The names of all handled |NetCDFFile| objects."""
        return tuple(
            sorted(set(itertools.chain(*(_.keys() for _ in self.folders.values()))))
        )

    def __getattr__(self, name: str) -> NetCDFFile:
        counter = 0
        memory = None
        for foldername, folder in self.folders.items():
            for filename, file_ in folder.items():
                if name == f"{foldername}_{filename}":
                    return file_
                if name == filename:
                    counter += 1
                    memory = file_
        if counter == 1:
            assert memory is not None
            return memory
        if counter > 1:
            raise AttributeError(
                f"The current NetCDFInterface object does handle multiple NetCDFFile "
                f"objects named `{name}`.  Please be more specific."
            )
        raise AttributeError(
            f"The current NetCDFInterface object does neither handle a NetCDFFile "
            f"object named `{name}` nor does it define a member named `{name}`."
        )

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __len__(self) -> int:
        return len(tuple(ncfiles for ncfiles in self))

    def __iter__(self) -> Iterator[NetCDFFile]:
        for ncfiles in self.folders.values():
            for ncfile in ncfiles.values():
                yield ncfile

    def __dir__(self) -> List[str]:
        adds_long = []
        counter: DefaultDict[str, int] = collections.defaultdict(lambda: 0)
        for foldername, folder in self.folders.items():
            for filename in folder.keys():
                adds_long.append(f"{foldername}_{filename}")
                counter[filename] += 1
        adds_short = [name for name, nmb in counter.items() if nmb == 1]
        return cast(List[str], super().__dir__()) + adds_long + adds_short


class NetCDFFile:
    """Handles a single NetCDF file.

    The core task of class |NetCDFFile| is to distribute different |IOSequence| objects
    on multiple instances of |NetCDFVariableBase| subclasses.  The documentation on the
    method |NetCDFFile.log| explains this in detail.  Here we focus on how a
    |NetCDFFile| object triggers its subobjects' reading and writing functionalities.

    (1) We prepare a |SequenceManager| object and some devices handling different
    sequences by applying the function |prepare_io_example_1|:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()

    (2) We define two shortcuts for the sequences used in the following examples:

    >>> nied = element1.model.sequences.inputs.nied
    >>> nkor = element1.model.sequences.fluxes.nkor

    (3) We prepare a |NetCDFFile| object and log the |lland_inputs.Nied| sequence:

    >>> from hydpy.core.netcdftools import NetCDFFile
    >>> ncfile = NetCDFFile("model", isolate=False, dirpath="")
    >>> len(ncfile)
    0
    >>> _ = ncfile.log(nied, nied.series)
    >>> len(ncfile)
    1

    (4) We store the NetCDF file directly into the testing directory:

    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     init = pub.timegrids.init
    ...     ncfile.write(timeunit=init.firstdate.to_cfunits("hours"),
    ...                  timepoints=init.to_timepoints("hours"))

    (5) We set the time-series values of the test sequence to zero, log the sequence to
    a new |NetCDFFile| instance, read the data from the NetCDF file, and check that
    test sequence `nied` in fact contains the read data:

    >>> nied.series = 0.0
    >>> ncfile = NetCDFFile("model", isolate=False, dirpath="")
    >>> _ = ncfile.log(nied, nied.series)
    >>> with TestIO():
    ...     ncfile.read()
    >>> nied.series
    InfoArray([0., 1., 2., 3.])

    (6) We show that IO errors and faulty variable access should result in clear error
    messages:

    >>> _ = ncfile.log(nkor, nkor.series)
    >>> with TestIO():
    ...     ncfile.read()
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to read data from NetCDF file `model.nc`, the following \
error occurred: NetCDF file `model.nc` does not contain variable `flux_nkor`.

    >>> "flux_nkor" in dir(ncfile)
    True
    >>> ncfile.flux_nkor.name
    'flux_nkor'
    >>> 'state_bowa' in dir(ncfile)
    False
    >>> ncfile.state_bowa
    Traceback (most recent call last):
    ...
    AttributeError: The NetCDFFile object `model` does neither handle a NetCDF \
variable named `state_bowa` nor does it define a member named `state_bowa`.
    """

    name: str
    variables: Dict[str, NetCDFVariable]
    ncfile: Optional[netcdf4.Dataset]
    _isolate: bool
    _dirpath: str

    def __init__(self, name: str, isolate: bool, dirpath: str) -> None:
        self.name = name
        self._isolate = isolate
        self._dirpath = dirpath
        self.ncfile = None
        self.variables = {}

    def log(
        self,
        sequence: sequencetools.IOSequence[Any, Any],
        infoarray: Optional[sequencetools.InfoArray],
    ) -> NetCDFVariable:
        """Pass the given |IoSequence| to a suitable instance of a |NetCDFVariableBase|
        subclass.

        When writing data, the second argument should be an |InfoArray|.  When reading
        data, this argument is irrelevant. Pass |None|.

        (1) We prepare some devices handling some sequences by applying the function
        |prepare_io_example_1|.  We limit our attention to the returned elements, which
        handle the more diverse sequences:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()

        (2) We define some shortcuts for the sequences used in the following examples:

        >>> nied1 = element1.model.sequences.inputs.nied
        >>> nied2 = element2.model.sequences.inputs.nied
        >>> nkor2 = element2.model.sequences.fluxes.nkor
        >>> nkor3 = element3.model.sequences.fluxes.nkor
        >>> sp4 = element4.model.sequences.states.sp

        (3) We define a function that logs these example sequences to a given
        |NetCDFFile| object and prints the resulting object structure information.
        Note that we log sequences `nkor2` and `sp4` twice, the first time with their
        original time series data and the second time with averaged values:

        >>> from hydpy import classname
        >>> def test(ncfile):
        ...     ncfile.log(nied1, nied1.series)
        ...     ncfile.log(nied2, nied2.series)
        ...     ncfile.log(nkor2, nkor2.series)
        ...     ncfile.log(sp4, sp4.series)
        ...     ncfile.log(nkor2, nkor2.average_series())
        ...     ncfile.log(sp4, sp4.average_series())
        ...     ncfile.log(nkor3, nkor3.average_series())
        ...     for name, variable in ncfile.variables.items():
        ...         print(name, classname(variable), variable.subdevicenames)

        (4) We prepare a |NetCDFFile| object with the option `isolate` disabled:

        >>> from hydpy.core.netcdftools import NetCDFFile
        >>> ncfile = NetCDFFile("model", isolate=False, dirpath="")

        (5) Logging all test sequences results in three |NetCDFVariableFlat| and two
        |NetCDFVariableAgg| objects.  To keep the NetCDF variables related to
        |lland_fluxes.NKor| and |hland_states.SP| distinguishable, their names
        `flux_nkor_mean` and `state_sp_mean` include information about the kind of
        aggregation performed:

        >>> test(ncfile)
        input_nied NetCDFVariableFlat ('element1', 'element2')
        flux_nkor NetCDFVariableFlat ('element2_0', 'element2_1')
        state_sp NetCDFVariableFlat ('element4_0_0', 'element4_0_1', 'element4_0_2', \
'element4_1_0', 'element4_1_1', 'element4_1_2')
        flux_nkor_mean NetCDFVariableAgg ('element2', 'element3')
        state_sp_mean NetCDFVariableAgg ('element4',)

        (6) We confirm that the |NetCDFVariableBase| objects received the required
        information:

        >>> ncfile.flux_nkor.element2.sequence.descr_device
        'element2'
        >>> ncfile.flux_nkor.element2.array
        InfoArray([[16., 17.],
                   [18., 19.],
                   [20., 21.],
                   [22., 23.]])
        >>> ncfile.flux_nkor_mean.element2.sequence.descr_device
        'element2'
        >>> ncfile.flux_nkor_mean.element2.array
        InfoArray([16.5, 18.5, 20.5, 22.5])

        (7) We technically confirm that |NetCDFFile| passes the `isolate` argument
        correctly to the constructor of subclasses of |NetCDFVariableBase|:

        >>> from unittest.mock import patch
        >>> with patch("hydpy.core.netcdftools.NetCDFVariableFlat") as mock:
        ...     ncfile = NetCDFFile("model", isolate=True, dirpath="")
        ...     _ = ncfile.log(nied1, nied1.series)
        ...     mock.assert_called_once_with(name="input_nied", isolate=True)
        >>> with patch("hydpy.core.netcdftools.NetCDFVariableFlat") as mock:
        ...     ncfile = NetCDFFile("model", isolate=False, dirpath="")
        ...     _ = ncfile.log(nied1, nied1.series)
        ...     mock.assert_called_once_with(name="input_nied", isolate=False)
        """
        descr = sequence.descr_sequence
        if (infoarray is not None) and (infoarray.info["type"] != "unmodified"):
            aggregated = True
            descr = "_".join([descr, infoarray.info["type"]])
        else:
            aggregated = False
        if descr in self.variables:
            var_ = self.variables[descr]
        else:
            cls: Type[NetCDFVariable]
            if aggregated:
                cls = NetCDFVariableAgg
            else:
                cls = NetCDFVariableFlat
            var_ = cls(name=descr, isolate=self._isolate)
            self.variables[descr] = var_
        var_.log(sequence, infoarray)
        return var_

    @property
    def filepath(self) -> str:
        """The NetCDF file path."""
        return os.path.join(self._dirpath, self.name + ".nc")

    def read(self) -> None:
        """Open an existing NetCDF file temporarily and call method
        |NetCDFVariableBase.read| of all handled |NetCDFVariableBase| objects."""
        try:
            with netcdf4.Dataset(self.filepath, "r") as ncfile:
                timegrid = query_timegrid(ncfile)
                for variable in self:
                    variable.read(ncfile, timegrid)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to read data from NetCDF file `{self.filepath}`"
            )

    def write(self, timeunit: str, timepoints: NDArrayFloat) -> None:
        """Open a new NetCDF file temporarily and call method |NetCDFVariableBase.write|
        of all handled |NetCDFVariableBase| objects."""
        with netcdf4.Dataset(self.filepath, "w") as ncfile:
            ncfile.Conventions = "CF-1.6"
            self._insert_timepoints(ncfile, timepoints, timeunit)
            for variable in self:
                variable.write(ncfile)

    @staticmethod
    def _insert_timepoints(
        ncfile: netcdf4.Dataset, timepoints: NDArrayFloat, timeunit: str
    ) -> None:
        dim_name = dimmapping["nmb_timepoints"]
        var_name = varmapping["timepoints"]
        create_dimension(ncfile, dim_name, len(timepoints))
        create_variable(ncfile, var_name, "f8", (dim_name,))
        var_ = ncfile[var_name]
        var_[:] = timepoints
        var_.units = timeunit
        var_.standard_name = var_name
        var_.calendar = "standard"
        var_.delncattr("_FillValue")

    @property
    def variablenames(self) -> Tuple[str, ...]:
        """The names of all handled |IOSequence| objects."""
        return tuple(self.variables.keys())

    def __getattr__(self, name: str) -> NetCDFVariable:
        try:
            return self.variables[name]
        except KeyError:
            raise AttributeError(
                f"The NetCDFFile object `{self.name}` does neither handle a NetCDF "
                f"variable named `{name}` nor does it define a member named `{name}`."
            ) from None

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __len__(self) -> int:
        return len(self.variables)

    def __iter__(self) -> Iterator[NetCDFVariable]:
        for variable in self.variables.values():
            yield variable

    def __dir__(self) -> List[str]:
        return cast(List[str], super().__dir__()) + list(self.variablenames)


_NetCDFVariableInfo = collections.namedtuple(
    "_NetCDFVariableInfo", ["sequence", "array"]
)


class Subdevice2Index:
    """Return type of method |NetCDFVariableBase.query_subdevice2index|."""

    dict_: Dict[str, int]
    name_sequence: str
    name_ncfile: str

    def __init__(
        self, dict_: Dict[str, int], name_sequence: str, name_ncfile: str
    ) -> None:
        self.dict_ = dict_
        self.name_sequence = name_sequence
        self.name_ncfile = name_ncfile

    def get_index(self, name_subdevice: str) -> int:
        """Item access to the wrapped |dict| object with a specialised error message."""
        try:
            return self.dict_[name_subdevice]
        except KeyError:
            raise RuntimeError(
                f"No data for sequence `{self.name_sequence}` and (sub)device "
                f"`{name_subdevice}` in NetCDF file `{self.name_ncfile}` available."
            ) from None


class NetCDFVariableBase(abc.ABC):
    """Base class for |NetCDFVariableAgg| and |NetCDFVariableFlat|."""

    name: str
    sequences: Dict[str, sequencetools.IOSequence[Any, Any]]
    arrays: Dict[str, Optional[sequencetools.InfoArray]]

    _isolate: bool

    def __init__(
        self,
        name: str,
        isolate: bool,
    ) -> None:
        self.name = name
        self._isolate = isolate
        self.sequences = {}
        self.arrays = {}

    def log(
        self,
        sequence: sequencetools.IOSequence[Any, Any],
        infoarray: Optional[sequencetools.InfoArray],
    ) -> None:
        """Log the given |IOSequence| object either for reading or writing data.

        The optional `array` argument allows for passing alternative data in an
        |InfoArray| object for replacing the original series of the |IOSequence| object,
        which is helpful for writing modified (e.g. spatially averaged) time series.

        The logged time-series data is available via attribute access:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable
        >>> NCVar = make_abc_testable(NetCDFVariableBase)
        >>> ncvar = NCVar("flux_nkor", isolate=True)
        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> nkor = elements.element1.model.sequences.fluxes.nkor
        >>> ncvar.log(nkor, nkor.series)
        >>> "element1" in dir(ncvar)
        True
        >>> ncvar.element1.sequence is nkor
        True
        >>> "element2" in dir(ncvar)
        False
        >>> ncvar.element2
        Traceback (most recent call last):
        ...
        AttributeError: The NetCDFVariable object `flux_nkor` does neither handle time \
series data under the (sub)device name `element2` nor does it define a member named \
`element2`.
        """
        descr_device = sequence.descr_device
        self.sequences[descr_device] = sequence
        self.arrays[descr_device] = infoarray

    @property
    @abc.abstractmethod
    def subdevicenames(self) -> Tuple[str, ...]:
        """The names of all relevant (sub)devices."""

    @property
    def dimensions(self) -> Tuple[str, ...]:
        """The dimension names of the NetCDF variable.

        Usually, the string defined by property |IOSequence.descr_sequence| prefixes
        the dimension names related to location, allowing storing different sequence
        types in one NetCDF file:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> ncvar = NetCDFVariableAgg("flux_nkor", isolate=False)
        >>> ncvar.log(elements.element1.model.sequences.fluxes.nkor, None)
        >>> ncvar.dimensions
        ('time', 'flux_nkor_stations')

        However, we can omit the variable-specific suffix when isolating variables into
        separate NetCDF files:

        >>> ncvar = NetCDFVariableAgg("flux_nkor", isolate=True)
        >>> ncvar.log(elements.element1.model.sequences.fluxes.nkor, None)
        >>> ncvar.dimensions
        ('time', 'stations')
        """
        return (
            dimmapping["nmb_timepoints"],
            f"{self.prefix}{dimmapping['nmb_subdevices']}",
        )

    @property
    @abc.abstractmethod
    def array(self) -> NDArrayFloat:
        """A |numpy.ndarray| containing the values of all logged sequences."""

    @property
    def prefix(self) -> str:
        """A prefix for the names of dimensions and associated variables.

        "Isolated" variables do not require a prefix:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable
        >>> NetCDFVariableBase_ = make_abc_testable(NetCDFVariableBase)
        >>> NetCDFVariableBase_("name", isolate=True).prefix
        ''

        There is a risk of name conflicts when storing different sequence types in the
        same NetCDF file.  We solve this by using the variables name as a prefix:

        >>> NetCDFVariableBase_("name", isolate=False).prefix
        'name_'
        """
        return "" if self._isolate else f"{self.name}_"

    def insert_subdevices(self, ncfile: netcdf4.Dataset) -> None:
        """Insert a variable of the names of the (sub)devices of the logged sequences
        into the given NetCDF file.

        (1) We prepare a |NetCDFVariableBase| subclass with fixed (sub)device names:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase, chars2str
        >>> from hydpy import make_abc_testable, TestIO
        >>> from hydpy.core.netcdftools import netcdf4
        >>> Var = make_abc_testable(NetCDFVariableBase)
        >>> Var.subdevicenames = "element1", "element_2"

        (2) Without isolating variables, |NetCDFVariableBase.insert_subdevices|
        prefixes the name of the |NetCDFVariableBase| object to the name of the
        inserted variable and its dimensions.  The first dimension corresponds to the
        number of (sub)devices, the second dimension to the number of characters of the
        longest (sub)device name:

        >>> var1 = Var("var1", isolate=False)
        >>> with TestIO():
        ...     file1 = netcdf4.Dataset("model1.nc", "w")
        >>> var1.insert_subdevices(file1)
        >>> file1["var1_station_id"].dimensions
        ('var1_stations', 'var1_char_leng_name')
        >>> file1["var1_station_id"].shape
        (2, 9)
        >>> chars2str(file1["var1_station_id"][:])
        ['element1', 'element_2']
        >>> file1.close()

        (3) When isolating variables, we omit the prefix:

        >>> var2 = Var("var2", isolate=True)
        >>> with TestIO():
        ...     file2 = netcdf4.Dataset("model2.nc", "w")
        >>> var2.insert_subdevices(file2)
        >>> file2["station_id"].dimensions
        ('stations', 'char_leng_name')
        >>> file2["station_id"].shape
        (2, 9)
        >>> chars2str(file2["station_id"][:])
        ['element1', 'element_2']
        >>> file2.close()
        """
        prefix = self.prefix
        nmb_subdevices = f"{prefix}{dimmapping['nmb_subdevices']}"
        nmb_characters = f"{prefix}{dimmapping['nmb_characters']}"
        subdevices = f"{prefix}{varmapping['subdevices']}"
        statchars = str2chars(self.subdevicenames)
        create_dimension(ncfile, nmb_subdevices, statchars.shape[0])
        create_dimension(ncfile, nmb_characters, statchars.shape[1])
        create_variable(ncfile, subdevices, "S1", (nmb_subdevices, nmb_characters))
        ncfile[subdevices][:, :] = statchars

    def query_subdevices(self, ncfile: netcdf4.Dataset) -> List[str]:
        """Query the names of the (sub)devices of the logged sequences from the given
        NetCDF file.

        (1) We apply the function |NetCDFVariableBase.query_subdevices| on an empty
        NetCDF file.  The error message shows that the method tries to query the
        (sub)device names both under the assumption that variables have been isolated
        or not:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable, TestIO
        >>> from hydpy.core.netcdftools import netcdf4
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("model.nc", "w")
        >>> Var = make_abc_testable(NetCDFVariableBase)
        >>> Var.subdevicenames = "element1", "element_2"
        >>> var = Var("flux_prec", isolate=False)
        >>> var.query_subdevices(ncfile)
        Traceback (most recent call last):
        ...
        RuntimeError: NetCDF file `model.nc` does neither contain a variable named \
`flux_prec_station_id` nor `station_id` for defining the coordinate locations of \
variable `flux_prec`.

        (2) After inserting the (sub)device names, they can be queried and returned:

        >>> var.insert_subdevices(ncfile)
        >>> Var("flux_prec", isolate=False).query_subdevices(ncfile)
        ['element1', 'element_2']
        >>> Var('flux_prec', isolate=True).query_subdevices(ncfile)
        ['element1', 'element_2']

        >>> ncfile.close()
        """
        tests = [f"{pref}{varmapping['subdevices']}" for pref in (f"{self.name}_", "")]
        for subdevices in tests:
            try:
                chars = ncfile[subdevices][:]
                break
            except (IndexError, KeyError):
                pass
        else:
            raise RuntimeError(
                f"NetCDF file `{get_filepath(ncfile)}` does neither contain a "
                f"variable named `{tests[0]}` nor `{tests[1]}` for defining the "
                f"coordinate locations of variable `{self.name}`."
            )
        return chars2str(chars)

    def query_subdevice2index(self, ncfile: netcdf4.Dataset) -> Subdevice2Index:
        """Return a |Subdevice2Index| object that maps the (sub)device names to their
        position within the given NetCDF file.

        Method |NetCDFVariableBase.query_subdevice2index| relies on
        |NetCDFVariableBase.query_subdevices|.  The returned |Subdevice2Index| object
        remembers the NetCDF file from which the (sub)device names stem, allowing for
        clear error messages:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase, str2chars
        >>> from hydpy import make_abc_testable, TestIO
        >>> from hydpy.core.netcdftools import netcdf4
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("model.nc", "w")
        >>> Var = make_abc_testable(NetCDFVariableBase)
        >>> Var.subdevicenames = ["element3", "element1", "element1_1", "element2"]
        >>> var = Var("flux_prec", isolate=True)
        >>> var.insert_subdevices(ncfile)
        >>> subdevice2index = var.query_subdevice2index(ncfile)
        >>> subdevice2index.get_index("element1_1")
        2
        >>> subdevice2index.get_index("element3")
        0
        >>> subdevice2index.get_index("element5")
        Traceback (most recent call last):
        ...
        RuntimeError: No data for sequence `flux_prec` and (sub)device `element5` in \
NetCDF file `model.nc` available.

        Additionally, |NetCDFVariableBase.query_subdevice2index| checks for duplicates:

        >>> ncfile["station_id"][:] = str2chars(
        ...     ["element3", "element1", "element1_1", "element1"])
        >>> var.query_subdevice2index(ncfile)
        Traceback (most recent call last):
        ...
        RuntimeError: The NetCDF file `model.nc` contains duplicate (sub)device names \
for variable `flux_prec` (the first found duplicate is `element1`).

        >>> ncfile.close()
        """
        subdevices = self.query_subdevices(ncfile)
        self._test_duplicate_exists(ncfile, subdevices)
        subdev2index = {subdev: idx for (idx, subdev) in enumerate(subdevices)}
        return Subdevice2Index(subdev2index, self.name, get_filepath(ncfile))

    def _test_duplicate_exists(
        self, ncfile: netcdf4.Dataset, subdevices: Sequence[str]
    ) -> None:
        if len(subdevices) != len(set(subdevices)):
            for idx, name1 in enumerate(subdevices):
                for name2 in subdevices[idx + 1 :]:
                    if name1 == name2:
                        raise RuntimeError(
                            f"The NetCDF file `{get_filepath(ncfile)}` contains "
                            f"duplicate (sub)device names for variable `{self.name}` "
                            f"(the first found duplicate is `{name1}`)."
                        )

    @abc.abstractmethod
    def read(self, ncfile: netcdf4.Dataset, timegrid_data: timetools.Timegrid) -> None:
        """Read the data from the given NetCDF file."""

    @abc.abstractmethod
    def write(self, ncfile: netcdf4.Dataset) -> None:
        """Write the data to the given NetCDF file."""

    def __getattr__(self, name: str) -> _NetCDFVariableInfo:
        try:
            return _NetCDFVariableInfo(self.sequences[name], self.arrays[name])
        except KeyError:
            raise AttributeError(
                f"The NetCDFVariable object `{self.name}` does neither handle time "
                f"series data under the (sub)device name `{name}` nor does it define "
                f"a member named `{name}`."
            ) from None

    def __dir__(self) -> List[str]:
        return cast(List[str], super().__dir__()) + list(self.sequences.keys())


class NetCDFVariableAgg(NetCDFVariableBase):
    """Relates objects of a specific |IOSequence| subclass with a single NetCDF
    variable for writing aggregated time-series data.

    Essentially, class |NetCDFVariableAgg| is very similar to class |NetCDFVariableFlat|
    but a little bit simpler, as it cannot read data from NetCDF files and always
    writes one column of data for each logged |IOSequence| object.  The following
    examples are a selection of the more thoroughly explained examples of the
    documentation on class |NetCDFVariableFlat|:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()
    >>> from hydpy.core.netcdftools import NetCDFVariableAgg
    >>> var_nied = NetCDFVariableAgg("input_nied_mean", isolate=False)
    >>> var_nkor = NetCDFVariableAgg("flux_nkor_mean", isolate=False)
    >>> var_sp = NetCDFVariableAgg("state_sp_mean", isolate=False)
    >>> for element in (element1, element2):
    ...     nied = element.model.sequences.inputs.nied
    ...     var_nied.log(nied, nied.average_series())
    ...     nkor = element.model.sequences.fluxes.nkor
    ...     var_nkor.log(nkor, nkor.average_series())
    >>> sp = element4.model.sequences.states.sp
    >>> var_sp.log(sp, sp.average_series())
    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("model.nc", "w")
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, "time", 4)
    >>> var_nied.write(ncfile)
    >>> var_nkor.write(ncfile)
    >>> var_sp.write(ncfile)
    >>> ncfile.close()

    As |NetCDFVariableAgg| provides no reading functionality, we show that the
    aggregated values are readily available using the external NetCDF4 library:

    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("model.nc", "r")
    >>> import numpy
    >>> numpy.array(ncfile["input_nied_mean"][:])
    array([[0., 4.],
           [1., 5.],
           [2., 6.],
           [3., 7.]])

    >>> numpy.array(ncfile["flux_nkor_mean"][:])
    array([[12. , 16.5],
           [13. , 18.5],
           [14. , 20.5],
           [15. , 22.5]])

    >>> numpy.array(ncfile["state_sp_mean"][:])
    array([[70.5],
           [76.5],
           [82.5],
           [88.5]])

    >>> ncfile.close()
    """

    @property
    def shape(self) -> Tuple[int, int]:
        """Required shape of |NetCDFVariableAgg.array|.

        The first axis corresponds to the number of timesteps and the second axis to
        the number of devices.  We show this for the 1-dimensional input sequence
        |lland_fluxes.NKor|:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> ncvar = NetCDFVariableAgg("flux_nkor", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (4, 3)

        There is no difference for 2-dimensional sequences as aggregating their
        time-series also results in 1-dimensional data:

        >>> ncvar = NetCDFVariableAgg("state_sp", isolate=False)
        >>> ncvar.log(elements.element4.model.sequences.states.sp, None)
        >>> ncvar.shape
        (4, 1)
        """
        return len(hydpy.pub.timegrids.init), len(self.sequences)

    @property
    def array(self) -> NDArrayFloat:
        """The aggregated data of all logged |IOSequence| objects contained in a
        single |numpy.ndarray| object.

        The documentation on |NetCDFVariableAgg.shape| explains the structure of
        |NetCDFVariableAgg.array|.  This first example confirms that the first axis
        corresponds to time while the second corresponds to the location:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> ncvar = NetCDFVariableAgg("flux_nkor", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         ncvar.log(nkor, nkor.average_series())
        >>> ncvar.array
        array([[12. , 16.5, 25. ],
               [13. , 18.5, 28. ],
               [14. , 20.5, 31. ],
               [15. , 22.5, 34. ]])

        There is no difference for 2-dimensional sequences as aggregating their
        time-series also results in 1-dimensional data:

        >>> ncvar = NetCDFVariableAgg("state_sp", isolate=False)
        >>> sp = elements.element4.model.sequences.states.sp
        >>> ncvar.log(sp, sp.average_series())
        >>> ncvar.array
        array([[70.5],
               [76.5],
               [82.5],
               [88.5]])
        """
        array = numpy.full(self.shape, fillvalue, dtype=float)
        for idx, subarray in enumerate(self.arrays.values()):
            if subarray is not None:
                array[:, idx] = subarray
        return array

    @property
    def subdevicenames(self) -> Tuple[str, ...]:
        """The names of all relevant (sub)devices."""
        return tuple(self.sequences.keys())

    def read(self, ncfile: netcdf4.Dataset, timegrid_data: timetools.Timegrid) -> None:
        """Raise a |RuntimeError| in any case.

        This method always raises the following exception to tell users why
        implementing a reading functionality is not possible:

        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> NetCDFVariableAgg("flux_nkor", isolate=False).read(None, None)
        Traceback (most recent call last):
        ...
        RuntimeError: The process of aggregating values (of sequence `flux_nkor` and \
other sequences as well) is not invertible.
        """
        raise RuntimeError(
            f"The process of aggregating values (of sequence `{self.name}` and other "
            f"sequences as well) is not invertible."
        )

    def write(self, ncfile: netcdf4.Dataset) -> None:
        """Write the data to the given NetCDF file.

        See the general documentation on class |NetCDFVariableAgg| for some examples.
        """
        self.insert_subdevices(ncfile)
        dimensions = self.dimensions
        array = self.array
        create_variable(ncfile, self.name, "f8", dimensions)
        ncfile[self.name][:] = array


class NetCDFVariableFlat(NetCDFVariableBase):
    """Relates objects of a specific |IOSequence| subclass with a single NetCDF
    variable for reading or writing their complete time-series data.

    (1) We prepare some devices handling some sequences by applying the function
    |prepare_io_example_1|.  We limit our attention to the returned elements, which
    handle the more diverse sequences:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()

    (2) We define three |NetCDFVariableFlat| instances with different
    |NetCDFVariableFlat.array| structures and log the |lland_inputs.Nied| and
    |lland_fluxes.NKor| sequences of the first two elements and |hland_states.SP| of
    the fourth element:

    >>> from hydpy.core.netcdftools import NetCDFVariableFlat
    >>> var_nied = NetCDFVariableFlat("input_nied", isolate=False)
    >>> var_nkor = NetCDFVariableFlat("flux_nkor", isolate=False)
    >>> var_sp = NetCDFVariableFlat("state_sp", isolate=False)
    >>> for element in (element1, element2):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)
    >>> sp = element4.model.sequences.states.sp
    >>> var_sp.log(sp, sp.series)

    (3) We prepare a nearly empty NetCDF file. "Nearly", because all data corresponds
    to the same period, which is why usually a central instance of class |NetCDFFile|
    prepares and passes time information:

    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("model.nc", "w")
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, "time", 4)

    (4) We store the data of all logged sequences in the NetCDF file:

    >>> var_nied.write(ncfile)
    >>> var_nkor.write(ncfile)
    >>> var_sp.write(ncfile)
    >>> ncfile.close()

    (5) We set all values of the selected sequences to -777 and check that they are
    different from the original values available via `testarray` attribute:

    >>> seq1 = element1.model.sequences.inputs.nied
    >>> seq2 = element2.model.sequences.fluxes.nkor
    >>> seq3 = element4.model.sequences.states.sp
    >>> import numpy
    >>> for seq in (seq1, seq2, seq3):
    ...     seq.series = -777.0
    ...     print(numpy.any(seq.series == seq.testarray))
    False
    False
    False

    (6) Again, we prepare three |NetCDFVariableFlat| instances and log the same
    sequences as above, open the existing NetCDF file for reading, read its data, and
    confirm that it has been correctly passed to the test sequences:

    >>> nied1 = NetCDFVariableFlat("input_nied", isolate=False)
    >>> nkor1 = NetCDFVariableFlat("flux_nkor", isolate=False)
    >>> sp4 = NetCDFVariableFlat("state_sp", isolate=False)
    >>> for element in (element1, element2):
    ...     sequences = element.model.sequences
    ...     nied1.log(sequences.inputs.nied, None)
    ...     nkor1.log(sequences.fluxes.nkor, None)
    >>> sp4.log(sp, None)
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("model.nc", "r")
    >>> from hydpy import pub
    >>> nied1.read(ncfile, pub.timegrids.init)
    >>> nkor1.read(ncfile, pub.timegrids.init)
    >>> sp4.read(ncfile, pub.timegrids.init)
    >>> for seq in (seq1, seq2, seq3):
    ...     print(numpy.all(seq.series == seq.testarray))
    True
    True
    True

    (6) Trying to read data not stored properly results in error messages like the
    following:

    >>> nied1.log(element3.model.sequences.inputs.nied, None)
    >>> nied1.read(ncfile, pub.timegrids.init)
    Traceback (most recent call last):
    ...
    RuntimeError: No data for sequence `input_nied` and (sub)device `element3` in \
NetCDF file `model.nc` available.

    >>> ncfile.close()

    (7) We repeat the first few steps but pass |True| to the constructor of
    |NetCDFVariableFlat| to indicate that we want to write each type of sequence into a
    separate NetCDF file.  Nevertheless, we try to store two different kinds of
    sequences into the same NetCDF file, which works for the first sequence
    (|lland_inputs.Nied|) but not for the second one (|lland_fluxes.NKor|):

    >>> var_nied = NetCDFVariableFlat("input_nied", isolate=True)
    >>> var_nkor = NetCDFVariableFlat("flux_nkor", isolate=True)
    >>> for element in (element1, element2):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("model.nc", "w")
    >>> create_dimension(ncfile, "time", 4)
    >>> var_nied.write(ncfile)
    >>> try:
    ...     var_nkor.write(ncfile)
    ... except BaseException as exc:
    ...     print(exc)   # doctest: +ELLIPSIS
    While trying to add dimension `stations` with length `3` to the NetCDF file \
`model.nc`, the following error occurred: ...
    >>> ncfile.close()
    >>> from hydpy import TestIO
    >>> from hydpy.core.netcdftools import netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset("model.nc", "r")
    >>> seq1.series = 0.0
    >>> var_nied.read(ncfile, pub.timegrids.init)
    >>> seq1.series
    InfoArray([0., 1., 2., 3.])
    >>> ncfile.close()
    """

    @property
    def shape(self) -> Tuple[int, int]:
        """Required shape of |NetCDFVariableFlat.array|.

        For 0-dimensional sequences like |lland_inputs.Nied|, the first axis
        corresponds to the number of timesteps and the second axis to the number of
        devices:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> ncvar = NetCDFVariableFlat("input_nied", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         ncvar.log(element.model.sequences.inputs.nied, None)
        >>> ncvar.shape
        (4, 3)

        For 1-dimensional sequences as |lland_fluxes.NKor|, the second axis corresponds
        to "subdevices".  Here, these "subdevices" are hydrological response units of
        different elements.  The model instances of the three elements define one, two,
        and three response units, respectively, making up a sum of six subdevices:

        >>> ncvar = NetCDFVariableFlat("flux_nkor", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (4, 6)

        The above assertions also hold for 2-dimensional sequences like
        |hland_states.SP|.  In this specific case, each "subdevice" corresponds to a
        single snow class (one element times three zones times two snow classes makes
        six subdevices):

        >>> ncvar = NetCDFVariableFlat("state_sp", isolate=False)
        >>> ncvar.log(elements.element4.model.sequences.states.sp, None)
        >>> ncvar.shape
        (4, 6)
        """
        return (
            len(hydpy.pub.timegrids.init),
            sum(len(seq) for seq in self.sequences.values()),
        )

    @property
    def array(self) -> NDArrayFloat:
        """The series data of all logged |IOSequence| objects contained in one single
        |numpy.ndarray| object.

        The documentation on |NetCDFVariableAgg.shape| explains the structure of
        |NetCDFVariableAgg.array|.  The first example confirms that the first axis
        corresponds to time while the second corresponds to the location:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> ncvar = NetCDFVariableFlat("input_nied", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nied1 = element.model.sequences.inputs.nied
        ...         ncvar.log(nied1, nied1.series)
        >>> ncvar.array
        array([[ 0.,  4.,  8.],
               [ 1.,  5.,  9.],
               [ 2.,  6., 10.],
               [ 3.,  7., 11.]])

        The flattening of higher dimensional sequences spreads the time-series of
        individual "subdevices" over the array's columns.  For the 1-dimensional
        sequence |lland_fluxes.NKor|, we find the time-series of both zones of the
        second element in columns two and three:

        >>> ncvar = NetCDFVariableFlat("flux_nkor", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         ncvar.log(nkor, nkor.series)
        >>> ncvar.array[:, 1:3]
        array([[16., 17.],
               [18., 19.],
               [20., 21.],
               [22., 23.]])

        The above assertions also hold for 2-dimensional sequences like
        |hland_states.SP|.  In this specific case, each column contains the series of a
        single snow class:

        >>> ncvar = NetCDFVariableFlat("state_sp", isolate=False)
        >>> sp = elements.element4.model.sequences.states.sp
        >>> ncvar.log(sp, sp.series)
        >>> ncvar.array
        array([[68., 69., 70., 71., 72., 73.],
               [74., 75., 76., 77., 78., 79.],
               [80., 81., 82., 83., 84., 85.],
               [86., 87., 88., 89., 90., 91.]])
        """
        array = numpy.full(self.shape, fillvalue, dtype=float)
        idx0 = 0
        idxs: List[Any] = [slice(None)]
        for seq, subarray in zip(self.sequences.values(), self.arrays.values()):
            for prod in self._product(seq.shape):
                if subarray is not None:
                    subsubarray = subarray[tuple(idxs + list(prod))]
                    array[:, idx0] = subsubarray
                idx0 += 1
        return array

    @property
    def subdevicenames(self) -> Tuple[str, ...]:
        """The names of the (sub)devices.

        Property |NetCDFVariableFlat.subdevicenames| clarifies which column of
        |NetCDFVariableAgg.array| contains the series of which (sub)device.  For
        0-dimensional series like |lland_inputs.Nied|, we require no subdivision.
        Hence, it returns the original device names:

        >>> from hydpy.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> ncvar = NetCDFVariableFlat("input_nied", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nied = element.model.sequences.inputs.nied
        ...         ncvar.log(nied, nied.series)
        >>> ncvar.subdevicenames
        ('element1', 'element2', 'element3')

        For 1-dimensional sequences like |lland_fluxes.NKor|, a suffix defines the
        index of the respective subdevice.  The third column of
        |NetCDFVariableAgg.array|, for example, contains the series of the first
        hydrological response unit of the second element:

        >>> ncvar = NetCDFVariableFlat("flux_nkor", isolate=False)
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         ncvar.log(nkor, nkor.series)
        >>> ncvar.subdevicenames
        ('element1_0', 'element2_0', 'element2_1', 'element3_0', 'element3_1', \
'element3_2')

        2-dimensional sequences like |hland_states.SP| require an additional suffix:

        >>> ncvar = NetCDFVariableFlat("state_sp", isolate=False)
        >>> sp = elements.element4.model.sequences.states.sp
        >>> ncvar.log(sp, sp.series)
        >>> ncvar.subdevicenames
        ('element4_0_0', 'element4_0_1', 'element4_0_2', 'element4_1_0', \
'element4_1_1', 'element4_1_2')
        """
        stats: Deque[str] = collections.deque()
        for devicename, seq in self.sequences.items():
            if seq.NDIM:
                temp = devicename + "_"
                for prod in self._product(seq.shape):
                    stats.append(temp + "_".join(str(idx) for idx in prod))
            else:
                stats.append(devicename)
        return tuple(stats)

    @staticmethod
    def _product(shape: Sequence[int]) -> Iterator[Tuple[int, ...]]:
        """Should return all "subdevice index combinations" for sequences with
        arbitrary dimensions.

        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> _product = NetCDFVariableFlat.__dict__["_product"].__func__
        >>> for comb in _product([1, 2, 3]):
        ...     print(comb)
        (0, 0, 0)
        (0, 0, 1)
        (0, 0, 2)
        (0, 1, 0)
        (0, 1, 1)
        (0, 1, 2)
        """
        return itertools.product(*(range(nmb) for nmb in shape))

    def read(self, ncfile: netcdf4.Dataset, timegrid_data: timetools.Timegrid) -> None:
        """Read the data from the given NetCDF file.

        The argument `timegrid_data` defines the data period of the given NetCDF file.

        See the general documentation on class |NetCDFVariableFlat| for some examples.
        """
        array = query_array(ncfile, self.name)
        idxs: Tuple[Any] = (slice(None),)
        subdev2index = self.query_subdevice2index(ncfile)
        for devicename, seq in self.sequences.items():
            if seq.NDIM:
                subshape = (array.shape[0],) + seq.shape
                subarray = numpy.empty(subshape)
                temp = devicename + "_"
                for prod in self._product(seq.shape):
                    station = temp + "_".join(str(idx) for idx in prod)
                    subarray[idxs + prod] = array[:, subdev2index.get_index(station)]
            else:
                subarray = array[:, subdev2index.get_index(devicename)]
            seq.series = seq.adjust_series(timegrid_data, subarray)

    def write(self, ncfile: netcdf4.Dataset) -> None:
        """Write the data to the given NetCDF file.

        See the general documentation on class |NetCDFVariableFlat| for some examples.
        """
        self.insert_subdevices(ncfile)
        create_variable(ncfile, self.name, "f8", self.dimensions)
        ncfile[self.name][:] = self.array
