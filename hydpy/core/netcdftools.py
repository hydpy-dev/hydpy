"""
This module extends the features of module |filetools| for loading data from and
storing data to netCDF4 files, consistent with the `NetCDF Climate and Forecast (CF)
Metadata Conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/
cf-conventions.html>`_.

.. _`Delft-FEWS`: https://oss.deltares.nl/web/delft-fews

Usually, we only indirectly apply the features implemented in this module.  Here, we
demonstrate the underlying functionalities, which can be subsumed by following three
steps:

  1. Call either method |SequenceManager.open_netcdfreader| or method
     |SequenceManager.open_netcdfwriter| of the |SequenceManager| object available in
     module |pub| to prepare a |NetCDFInterfaceReader| object for reading or a
     |NetCDFInterfaceWriter| object for writing.
  2. Call either the usual reading or writing methods of other HydPy classes like
     method |HydPy.load_fluxseries| of class |HydPy| or method
     |Elements.save_stateseries| of class |Elements|.  The prepared interface object
     collects all requests of those sequences one wants to read from or write to NetCDF
     files.
  3. Finalise reading or writing by calling either method
     |SequenceManager.close_netcdfreader| or |SequenceManager.close_netcdfwriter|.

Step 2 is a logging process only, telling the interface object which data needs to be
read or written, while step 3 triggers the actual reading from or writing to NetCDF
files.

During step 2, the interface object and its subobjects of type
|NetCDFVariableFlatReader|, |NetCDFVariableFlatWriter|, or |NetCDFVariableAggregated|
are accessible, allowing one to inspect their current state or modify their behaviour.

The following real code examples show how to perform these three steps both for reading
and writing data, based on the example configuration defined by function
|prepare_io_example_1|:

>>> from hydpy.core.testtools import prepare_io_example_1
>>> nodes, elements = prepare_io_example_1()

We prepare a |NetCDFInterfaceWriter| object for writing data via method
|SequenceManager.open_netcdfwriter|:

>>> from hydpy import pub
>>> pub.sequencemanager.open_netcdfwriter()

We tell the |SequenceManager| object to write all the time series data to NetCDF files:

>>> pub.sequencemanager.filetype = "nc"

We store all the time series handled by the |Node| and |Element| objects of the example
dataset by calling |Nodes.save_allseries| of class |Nodes| and
|Elements.save_allseries| of class |Elements|.  (In real cases, you would not write the
`with TestIO():` line.  This code block makes sure we pollute the IO testing directory
instead of our current working directory):

>>> from hydpy import TestIO
>>> with TestIO():
...     nodes.save_allseries()
...     elements.save_allseries()

We again log all sequences, but after telling the |SequenceManager| object to average
each time series spatially:

ToDo: Support spatial averaging for sequences of submodels.

>>> with TestIO(), pub.sequencemanager.aggregation("mean"):
...     nodes.save_allseries()
...     elements.element3.model.aetmodel.prepare_allseries(allocate_ram=False)
...     elements.save_allseries()
...     elements.element3.model.aetmodel.prepare_allseries(allocate_ram=True)

We can now navigate into the details of the logged time series data via the
|NetCDFInterfaceWriter| object and its |NetCDFVariableFlatReader| and
|NetCDFVariableAggregated| subobjects.  For example, we can query the logged flux
sequence objects of type |lland_fluxes.NKor| belonging to application model |lland_dd|
(those of elements `element1` and `element2`; the trailing numbers are the indices of
the relevant hydrological response units):

>>> writer = pub.sequencemanager.netcdfwriter
>>> writer.lland_dd_flux_nkor.subdevicenames
('element1_0', 'element2_0', 'element2_1')

In the example discussed here, all sequences belong to the same folder (`default`).
Storing sequences in separate folders means storing them in separate NetCDF files.  In
such cases, you must include the folder in the attribute name:

>>> writer.foldernames
('default',)
>>> writer.default_lland_dd_flux_nkor.subdevicenames
('element1_0', 'element2_0', 'element2_1')

We close the |NetCDFInterfaceWriter| object, which is the moment when the writing
process happens.  After that, the interface object is no longer available:

>>> from hydpy import TestIO
>>> with TestIO():
...     pub.sequencemanager.close_netcdfwriter()
>>> pub.sequencemanager.netcdfwriter
Traceback (most recent call last):
...
hydpy.core.exceptiontools.AttributeNotReady: The sequence file manager currently \
handles no NetCDF writer object. Consider applying the \
`pub.sequencemanager.netcdfwriting` context manager first (search in the \
documentation for help).


We set the time series values of two test sequences to zero to demonstrate that
reading the data back in actually works:

>>> nodes.node2.sequences.sim.series = 0.0
>>> elements.element2.model.sequences.fluxes.nkor.series = 0.0

We move up a gear and and prepare a |NetCDFInterfaceReader| object for reading data,
log all |NodeSequence| and |ModelSequence| objects, and read their time series data
from the created NetCDF file.  We temporarily disable the |Options.checkseries| option
to prevent raising an exception when reading incomplete data from the files:

>>> with TestIO(), pub.options.checkseries(False):
...     pub.sequencemanager.open_netcdfreader()
...     nodes.load_simseries()
...     elements.load_allseries()
...     pub.sequencemanager.close_netcdfreader()

We check if the data is available via the test sequences again:

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
hydpy.core.exceptiontools.AttributeNotReady: The sequence file manager currently \
handles no NetCDF reader object. Consider applying the \
`pub.sequencemanager.netcdfreading` context manager first (search in the \
documentation for help).

We cannot invert spatial aggregation.  Hence reading averaged time series is left for
postprocessing tools.  To show that writing the averaged series worked, we access both
relevant NetCDF files more directly using the underlying NetCDF4 library (note that
averaging 1-dimensional time series as those of node sequence |Sim| is allowed for the
sake of consistency):

>>> from numpy import array
>>> from hydpy import print_matrix
>>> from hydpy.core.netcdftools import netcdf4
>>> filepath = "project/series/default/sim_q_mean.nc"
>>> with TestIO(), netcdf4.Dataset(filepath) as ncfile:
...     print_matrix(array(ncfile["sim_q_mean"][:]))
| 60.0 |
| 61.0 |
| 62.0 |
| 63.0 |

>>> from hydpy import print_vector
>>> filepath = "project/series/default/lland_dd_flux_nkor_mean.nc"
>>> with TestIO(), netcdf4.Dataset(filepath) as ncfile:
...         print_vector(array(ncfile["lland_dd_flux_nkor_mean"][:])[:, 1])
16.5, 18.5, 20.5, 22.5

The previous examples relied on "model-specific" file names and variable names.  The
documentation on class |HydPy| introduces the standard "HydPy" convention as an
alternative for naming input time series files and demonstrates it for file types that
store the time series of single sequence instances.  Here, we take the input sequence
|lland_inputs.Nied| as an example to show that one can use its standard name
|StandardInputNames.PRECIPITATION| to read and write more generally named NetCDF files
and variables:

>>> print_vector(elements.element2.model.sequences.inputs.nied.series)
4.0, 5.0, 6.0, 7.0

>>> pub.sequencemanager.convention = "HydPy"
>>> with TestIO():
...     elements.save_inputseries()
>>> filepath = "project/series/default/precipitation.nc"
>>> with TestIO(), netcdf4.Dataset(filepath) as ncfile:
...         print_vector(array(ncfile["precipitation"][:])[:, 1])
4.0, 5.0, 6.0, 7.0

>>> elements.element2.model.sequences.inputs.nied.series = 0.0
>>> with TestIO(), pub.options.checkseries(False):
...     elements.load_inputseries()
>>> print_vector(elements.element2.model.sequences.inputs.nied.series)
4.0, 5.0, 6.0, 7.0

In the last example, the methods |Elements.load_inputseries| and
|Elements.save_inputseries| of class |Elements| opened and closed the required NetCDF
reader and writer objects automatically by using the context managers
|SequenceManager.netcdfreading| and |SequenceManager.netcdfwriting|.  Such comfort is
only available for these and the similar methods of the classes |HydPy|, |Elements|,
and |Nodes|.  If you, for example, apply the |IOSequence.load_series| or the
|IOSequence.save_series| method of individual |IOSequence| instances, you must activate
|SequenceManager.netcdfreading| or |SequenceManager.netcdfwriting| manually.  This
discomfort is intentional and should help prevent accidentally opening and closing
the same NetCDF file repeatedly, which could result in an immense waste of computation
time.  The following example shows how to apply these context managers manually and
that this does not conflict with using methods that could automatically open and close
NetCDF reader and writer objects:

>>> sequences = elements.element2.model.sequences
>>> sequences.inputs.nied.series = 1.0, 3.0, 5.0, 7.0
>>> sequences.fluxes.qah.series = 2.0, 4.0, 6.0, 8.0
>>> sequences.fluxes.qa.series = 3.0, 5.0, 7.0, 9.0
>>> with TestIO(), pub.sequencemanager.netcdfwriting():
...     sequences.fluxes.qa.save_series()
...     elements.save_inputseries()
...     sequences.fluxes.qah.save_series()

>>> sequences.inputs.nied.series = 0.0
>>> sequences.fluxes.qah.series = 0.0
>>> sequences.fluxes.qa.series = 0.0
>>> with TestIO(), pub.options.checkseries(False), pub.sequencemanager.netcdfreading():
...     sequences.fluxes.qah.load_series()
...     elements.load_inputseries()
...     sequences.fluxes.qa.load_series()
>>> print_vector(sequences.inputs.nied.series)
1.0, 3.0, 5.0, 7.0
>>> print_vector(sequences.fluxes.qah.series)
2.0, 4.0, 6.0, 8.0
>>> print_vector(sequences.fluxes.qa.series)
3.0, 5.0, 7.0, 9.0

Besides the testing-related specialities, the described workflow is more or less
standard but allows for different modifications.  We illustrate them in the
documentation of the other features implemented in module |netcdftools| and the
documentation on class |SequenceManager| of module |filetools| and class |IOSequence|
of module |sequencetools|.

Using the NetCDF format allows reading or writing data "just in time" during simulation
runs.  The documentation of class "HydPy" explains how to select and set the relevant
|IOSequence| objects for this option.  See the documentation on method
|NetCDFInterfaceJIT.provide_jitaccess| of class |NetCDFInterfaceJIT| for more in-depth
information.
"""

# import...
# ...from standard library
from __future__ import annotations
import abc
import collections
import functools
import contextlib
import itertools
import os
import time
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import printtools
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
"""Dimension-related terms within NetCDF files.

You can change this mapping if it does not suit your requirements.  For example, change 
the value of the keyword "nmb_subdevices" if you prefer to call this dimension 
"location" instead of "stations" within NetCDF files:

>>> from hydpy.core.netcdftools import dimmapping
>>> dimmapping["nmb_subdevices"] = "location"
"""

varmapping = {"timepoints": "time", "subdevices": "station_id"}
"""Variable-related terms within NetCDF files.

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


TypeNetCDFVariable = TypeVar("TypeNetCDFVariable", bound="NetCDFVariable")

FlatUnion: TypeAlias = Union["NetCDFVariableFlatReader", "NetCDFVariableFlatWriter"]


def summarise_ncfile(ncfile: netcdf4.Dataset | str, /) -> str:
    """Give a summary describing (a HydPy-compatible) NetCDF file.

    You can pass the file path:

    >>> import os
    >>> from hydpy import data, repr_, summarise_ncfile
    >>> filepath = os.path.join(
    ...     data.__path__[0], "HydPy-H-Lahn", "series", "default", "hland_96_input_p.nc"
    ... )
    >>> print(repr_(summarise_ncfile(filepath)))  # doctest: +ELLIPSIS
    GENERAL
        file path = .../hydpy/data/HydPy-H-Lahn/series/default/hland_96_input_p.nc
        file format = NETCDF4
        disk format = HDF5
        Attributes
            hydts_timeRef = begin
            title = Daily total precipitation sum HydPy-H-HBV96 model river Lahn
            ...
    DIMENSIONS
        stations = 4
        time = 11384
        str_len = 40
    VARIABLES
        time
            dimensions = time
            shape = 11384
            data type = float64
            Attributes
                units = days since 1900-01-01 00:00:00 +0100
                long_name = time
                axis = T
                calendar = standard
        hland_96_input_p
            dimensions = time, stations
            shape = 11384, 4
            data type = float64
            Attributes
                units = mm
                _FillValue = -9999.0
                long_name = Daily Precipitation Sum
        station_id
            dimensions = stations, str_len
            shape = 4, 40
            data type = |S1
            Attributes
                long_name = station or node identification code
        station_names
            dimensions = stations, str_len
            shape = 4, 40
            data type = |S1
            Attributes
                long_name = station or node name
        river_names
            dimensions = stations, str_len
            shape = 4, 40
            data type = |S1
            Attributes
                long_name = river name
    TIME GRID
        first date = 1989-11-01 00:00:00+01:00
        last date = 2021-01-01 00:00:00+01:00
        step size = 1d

    Alternatively, you can pass a NetCDF4 `Dataset` object:

    >>> from netCDF4 import Dataset
    >>> with Dataset(filepath, "r") as ncfile:
    ...     print(repr_(summarise_ncfile(ncfile)))  # doctest: +ELLIPSIS
    GENERAL
        file path = ...data/HydPy-H-Lahn/series/default/hland_96_input_p.nc
    ...
                _FillValue = -9999.0
    ...
    """

    def _summarize(nc: netcdf4.Dataset) -> str:

        i1, i2, i3 = 4 * " ", 8 * " ", 12 * " "

        lines: list[str] = []
        append = lines.append

        append("GENERAL")
        append(f"{i1}file path = {nc.filepath()}")
        append(f"{i1}file format = {nc.file_format}")
        append(f"{i1}disk format = {nc.disk_format}")
        if attrs_file := nc.ncattrs():
            append(f"{i1}Attributes")
            for attr_file in attrs_file:
                append(f"{i2}{attr_file} = {nc.getncattr(attr_file)}")

        if dims := nc.dimensions:
            append("DIMENSIONS")
            for name, dim in dims.items():
                append(f"{i1}{name} = {dim.size}")

        if vars_ := nc.variables:
            append("VARIABLES")
            for name, var in vars_.items():
                append(f"{i1}{name}")
                append(f"{i2}dimensions = {', '.join(var.dimensions)}")
                append(f"{i2}shape = {', '.join(str(s) for s in var.shape)}")
                append(f"{i2}data type = {var.datatype}")
                if attrs_var := var.ncattrs():
                    append(f"{i2}Attributes")
                    for attr_var in attrs_var:
                        append(f"{i3}{attr_var} = {var.getncattr(attr_var)}")

        timereference: str | None = getattr(nc, "timereference", None)
        if timereference is not None:
            append("TIME GRID")
            tg = _query_timegrid(ncfile=nc, left=timereference.startswith("left"))
            opts = hydpy.pub.options
            firstdate = tg.firstdate.to_string(style="iso2", utcoffset=opts.utcoffset)
            append(f"{i1}first date = {firstdate}")
            lastdate = tg.lastdate.to_string(style="iso2", utcoffset=opts.utcoffset)
            append(f"{i1}last date = {lastdate}")
            append(f"{i1}step size = {tg.stepsize}")

        return "\n".join(lines)

    if isinstance(ncfile, str):
        with netcdf4.Dataset(ncfile, "r") as ncfile_:
            return _summarize(ncfile_)
    return _summarize(ncfile)


def str2chars(strings: Sequence[str]) -> MatrixBytes:
    """Return a |numpy.ndarray| object containing the byte characters (second axis) of
    all given strings (first axis).

    >>> from hydpy.core.netcdftools import str2chars
    >>> str2chars(['street', 'St.', 'Straße', 'Str.'])
    array([[b's', b't', b'r', b'e', b'e', b't', b''],
           [b'S', b't', b'.', b'', b'', b'', b''],
           [b'S', b't', b'r', b'a', b'\xc3', b'\x9f', b'e'],
           [b'S', b't', b'r', b'.', b'', b'', b'']], dtype='|S1')

    >>> str2chars([])
    array([], shape=(0, 0), dtype='|S1')
    """
    if len(strings) == 0:
        return numpy.full((0, 0), b"", dtype="|S1")
    bytess = tuple(string.encode("utf-8") for string in strings)
    max_length = max(len(bytes_) for bytes_ in bytess)
    chars = numpy.full((len(strings), max_length), b"", dtype="|S1")
    for idx, bytes_ in enumerate(bytess):
        for jdx, int_ in enumerate(bytes_):
            chars[idx, jdx] = bytes([int_])
    return chars


def chars2str(chars: MatrixBytes) -> list[str]:
    r"""Inversion function of |str2chars|.

    >>> from hydpy.core.netcdftools import chars2str

    >>> chars2str([[b"s", b"t", b"r", b"e", b"e", b"t", b""],
    ...            [b"S", b"t", b".", b"", b"", b"", b""],
    ...            [b"S", b"t", b"r", b"a", b"\xc3", b"\x9f", b"e"],
    ...            [b"S", b"t", b"r", b".", b"", b"", b""]])
    ['street', 'St.', 'Straße', 'Str.']

    >>> chars2str([])
    []

    >>> chars2str([[b"s", b"t", b"r", b"e", b"e", b"t"],
    ...            [b"S", b"t", b".", b"", b"", b""],
    ...            [b"S", b"t", b"r", b"a", b"\xc3", b"e"],
    ...            [b"S", b"t", b"r", b".", b"", b""]])
    Traceback (most recent call last):
    ...
    ValueError: Cannot decode `b'Stra\xc3e'` (not UTF-8 compliant).
    """
    strings = []
    for subchars in chars:
        try:
            bytes_ = b"".join(subchars)
            strings.append(bytes_.decode("utf-8"))
        except UnicodeDecodeError:
            raise ValueError(
                f"Cannot decode `{bytes_!r}` (not UTF-8 compliant)."
            ) from None
    return strings


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
    ...     print(exc)  # doctest: +ELLIPSIS
    While trying to add dimension `dim1` with length `5` to the NetCDF file \
`test.nc`, the following error occurred: ...

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
    ncfile: netcdf4.Dataset, name: str, datatype: str, dimensions: Sequence[str]
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
    ...     print(str(exc).strip('"'))  # doctest: +ELLIPSIS
    While trying to add variable `var1` with datatype `f8` and dimensions `('dim1',)` \
to the NetCDF file `test.nc`, the following error occurred: ...

    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, "dim1", 5)
    >>> create_variable(ncfile, "var1", "f8", ("dim1",))
    >>> import numpy
    >>> from hydpy import print_vector
    >>> print_vector(numpy.array(ncfile["var1"][:]))
    nan, nan, nan, nan, nan

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
    >>> query_variable(file_, "values")
    Traceback (most recent call last):
    ...
    RuntimeError: NetCDF file `model.nc` does not contain variable `values`.

    >>> from hydpy.core.netcdftools import create_variable
    >>> create_variable(file_, "values", "f8", ())
    >>> assert isinstance(query_variable(file_, "values"), netcdf4.Variable)

    >>> file_.close()
    """
    try:
        return ncfile[name]
    except (IndexError, KeyError):
        raise RuntimeError(
            f"NetCDF file `{get_filepath(ncfile)}` does not contain variable `{name}`."
        ) from None


def query_timegrid(
    ncfile: netcdf4.Dataset, sequence: sequencetools.IOSequence
) -> timetools.Timegrid:
    """Return the |Timegrid| defined by the given NetCDF file.

    |query_timegrid| relies on the `timereference` attribute of the given NetCDF file,
    if available, and falls back to the global |Options.timestampleft| option when
    necessary.  The NetCDF files of the `HydPy-H-Lahn` example project (and all other
    NetCDF files written by *HydPy*) include such information:

    >>> from hydpy.core.testtools import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from netCDF4 import Dataset
    >>> filepath = "HydPy-H-Lahn/series/default/hland_96_input_p.nc"
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     ncfile.timereference
    'left interval boundary'

    We start our examples considering the input sequence |hland_inputs.P|, which
    handles precipitation sums.  |query_timegrid| requires an instance of
    |hland_inputs.P| to determine that each value of the time series of the NetCDF file
    references a time interval and not a time point:

    >>> p = hp.elements.land_dill_assl.model.sequences.inputs.p

    If the file-specific setting does not conflict with the current value of
    |Options.timestampleft|, |query_timegrid| works silently:

    >>> from hydpy.core.netcdftools import query_timegrid
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)
    Timegrid("1989-11-01 00:00:00",
             "2021-01-01 00:00:00",
             "1d")

    If a file-specific setting is missing, |query_timegrid| applies the current
    |Options.timestampleft| value:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     del ncfile.timereference
    >>> from hydpy.core.testtools import warn_later
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)
    Timegrid("1989-11-01 00:00:00",
             "2021-01-01 00:00:00",
             "1d")

    >>> with TestIO(), Dataset(filepath) as ncfile, pub.options.timestampleft(False):
    ...     query_timegrid(ncfile, p)
    Timegrid("1989-10-31 00:00:00",
             "2020-12-31 00:00:00",
             "1d")

    If the file-specific setting and |Options.timestampleft| conflict, |query_timegrid|
    favours the file attribute and warns about this assumption:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "right interval boundary"
    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)  # doctest: +ELLIPSIS
    Timegrid("1989-10-31 00:00:00",
             "2020-12-31 00:00:00",
             "1d")
    UserWarning: The `timereference` attribute (`right interval boundary`) of the \
NetCDF file `HydPy-H-Lahn/series/default/hland_96_input_p.nc` conflicts with the \
current value of the global `timestampleft` option (`True`).  The file-specific \
information is prioritised.


    State sequences like |hland_states.SM| handle data for specific time points instead
    of time intervals.  Their |IOSequence.series| vector contains the calculated values
    for the end of each simulation step.  Hence, without file-specific information,
    |query_timegrid| ignores the |Options.timestampleft| option and follows the `right
    interval boundary` convention:

    >>> sm = hp.elements.land_dill_assl.model.sequences.states.sm
    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     del ncfile.timereference
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)
    Timegrid("1989-10-31 00:00:00",
             "2020-12-31 00:00:00",
             "1d")

    Add a `timereference` attribute with the value `current time` to explicitly include
    this information in a NetCDF file:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "current time"
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)
    Timegrid("1989-10-31 00:00:00",
             "2020-12-31 00:00:00",
             "1d")

    |query_timegrid| raises special warnings when a NetCDF file's `timereference`
    attribute conflicts with its judgement whether the contained data addresses time
    intervals or time points:

    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)  # doctest: +ELLIPSIS
    Timegrid("1989-10-31 00:00:00",
             "2020-12-31 00:00:00",
             "1d")
    UserWarning: The `timereference` attribute (`current time`) of the NetCDF file \
`HydPy-H-Lahn/series/default/hland_96_input_p.nc` conflicts with the type of the \
relevant sequence (`P`).  The file-specific information is prioritised.


    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "left interval boundary"
    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)  # doctest: +ELLIPSIS
    Timegrid("1989-11-01 00:00:00",
             "2021-01-01 00:00:00",
             "1d")
    UserWarning: The `timereference` attribute (`left interval boundary`) of the \
NetCDF file `HydPy-H-Lahn/series/default/hland_96_input_p.nc` conflicts with the type \
of the relevant sequence (`SM`).  The file-specific information is prioritised.


    |query_timegrid| also raises specific warnings for misstated `timereference`
    attributes describing the different fallbacks for data related to time intervals
    and time points:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "wrong"
    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)  # doctest: +ELLIPSIS
    Timegrid("1989-11-01 00:00:00",
             "2021-01-01 00:00:00",
             "1d")
    UserWarning: The value of the `timereference` attribute (`wrong`) of the NetCDF \
file `HydPy-H-Lahn/series/default/hland_96_input_p.nc` is not among the accepted \
values (`left...`, `right...`, `current...`).  Assuming `left interval boundary` \
according to the current value of the global `timestampleft` option.



    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)  # doctest: +ELLIPSIS
    Timegrid("1989-10-31 00:00:00",
             "2020-12-31 00:00:00",
             "1d")
    UserWarning: The value of the `timereference` attribute (`wrong`) of the NetCDF \
file `...hland_96_input_p.nc` is not among the accepted values (`left...`, `right...`, \
`current...`).  Assuming `current time` according to the type of the relevant \
sequence (`SM`).
    """
    currenttime = _timereference_currenttime(sequence)
    opts = hydpy.pub.options
    ref: str | None = getattr(ncfile, "timereference", None)
    if ref is None:
        left = bool(opts.timestampleft and not currenttime)
    elif ref.startswith("left") or ref.startswith("right"):
        left = ref.startswith("left")
        if currenttime:
            warnings.warn(
                f"The `timereference` attribute (`{ncfile.timereference}`) of the "
                f"NetCDF file `{ncfile.filepath()}` conflicts with the type of the "
                f"relevant sequence (`{type(sequence).__name__}`).  The file-specific "
                f"information is prioritised."
            )
        elif left != opts.timestampleft:
            warnings.warn(
                f"The `timereference` attribute (`{ncfile.timereference}`) of the "
                f"NetCDF file `{ncfile.filepath()}` conflicts with the current value "
                f"of the global `timestampleft` option (`{bool(opts.timestampleft)}`). "
                f" The file-specific information is prioritised."
            )
    elif ref.startswith("current"):
        left = False
        if not currenttime:
            warnings.warn(
                f"The `timereference` attribute (`{ncfile.timereference}`) of the "
                f"NetCDF file `{ncfile.filepath()}` conflicts with the type of the "
                f"relevant sequence (`{type(sequence).__name__}`).  The file-specific "
                f"information is prioritised."
            )
    elif currenttime:
        left = False
        warnings.warn(
            f"The value of the `timereference` attribute (`{ncfile.timereference}`) "
            f"of the NetCDF file `{ncfile.filepath()}` is not among the accepted "
            f"values (`left...`, `right...`, `current...`).  Assuming `current time` "
            f"according to the type of the relevant sequence "
            f"(`{type(sequence).__name__}`)."
        )
    else:
        left = bool(opts.timestampleft)
        text = "left" if left else "right"
        warnings.warn(
            f"The value of the `timereference` attribute (`{ncfile.timereference}`) "
            f"of the NetCDF file `{ncfile.filepath()}` is not among the accepted "
            f"values (`left...`, `right...`, `current...`).  Assuming `{text} "
            f"interval boundary` according to the current value of the global "
            f"`timestampleft` option."
        )
    return _query_timegrid(ncfile=ncfile, left=left)


def _query_timegrid(ncfile: netcdf4.Dataset, left: bool) -> timetools.Timegrid:
    with hydpy.pub.options.timestampleft(left):
        timepoints = ncfile[varmapping["timepoints"]]
        refdate = timetools.Date.from_cfunits(timepoints.units)
        return timetools.Timegrid.from_timepoints(
            timepoints=timepoints[:],
            refdate=refdate,
            unit=timepoints.units.strip().split()[0],
        )


def query_array(ncfile: netcdf4.Dataset, name: str) -> NDArrayFloat:
    """Return the data of the variable with the given name from the given NetCDF file.

    The following example shows that |query_array| returns |numpy.nan| entries for
    representing missing values even when the respective NetCDF variable defines a
    different fill value:

    >>> from hydpy import print_matrix, TestIO
    >>> from hydpy.core import netcdftools
    >>> from hydpy.core.netcdftools import netcdf4, create_dimension, create_variable
    >>> import numpy
    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         create_dimension(ncfile, "time", 2)
    ...         create_dimension(ncfile, "stations", 3)
    ...         netcdftools.fillvalue = -999.0
    ...         create_variable(ncfile, "var", "f8", ("time", "stations"))
    ...         netcdftools.fillvalue = numpy.nan
    ...     ncfile = netcdf4.Dataset("test.nc", "r")
    >>> from hydpy.core.netcdftools import query_variable, query_array
    >>> print_matrix(query_variable(ncfile, "var")[:].data)
    | -999.0, -999.0, -999.0 |
    | -999.0, -999.0, -999.0 |
    >>> print_matrix(query_array(ncfile, "var"))
    | nan, nan, nan |
    | nan, nan, nan |
    >>> ncfile.close()

    Usually, *HydPy* expects all data variables in NetCDF files to be 2-dimensional,
    with time on the first and location on the second axis.  However, |query_array|
    allows for an exception for compatibility with `Delft-FEWS`_.  When working with
    ensembles, `Delft-FEWS`_ defines a third dimension called `realization` and puts it
    between the first dimension (`time`) and the last dimension (`stations`).  In our
    experience, this additional dimension is always of length one, meaning we can
    safely ignore it:

    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         create_dimension(ncfile, "time", 2)
    ...         create_dimension(ncfile, "realization", 1)
    ...         create_dimension(ncfile, "stations", 3)
    ...         var = create_variable(ncfile, "var", "f8",
    ...                               ("time", "realization", "stations"))
    ...         ncfile["var"][:] = [[[1.1, 1.2, 1.3]], [[2.1, 2.2, 2.3]]]
    ...     ncfile = netcdf4.Dataset("test.nc", "r")
    >>> var = query_variable(ncfile, "var")[:]
    >>> var.shape
    (2, 1, 3)
    >>> query_array(ncfile, "var").shape
    (2, 3)
    >>> print_matrix(query_array(ncfile, "var"))
    | 1.1, 1.2, 1.3 |
    | 2.1, 2.2, 2.3 |
    >>> ncfile.close()

    |query_array| raises errors if dimensionality is smaller than two or larger than
    three or if there are three dimensions and the length of the second dimension is
    not one:

    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         create_dimension(ncfile, "time", 2)
    ...         var = create_variable(ncfile, "var", "f8", ("time",))
    ...     with netcdf4.Dataset("test.nc", "r") as ncfile:
    ...         query_array(ncfile, "var")
    Traceback (most recent call last):
    ...
    RuntimeError: Variable `var` of NetCDF file `test.nc` must be 2-dimensional (or \
3-dimensional with a length of one on the second axis) but has the shape `(2,)`.

    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         create_dimension(ncfile, "time", 2)
    ...         create_dimension(ncfile, "realization", 2)
    ...         create_dimension(ncfile, "stations", 3)
    ...         var = create_variable(ncfile, "var", "f8",
    ...                               ("time", "realization", "stations"))
    ...     with netcdf4.Dataset("test.nc", "r") as ncfile:
    ...         query_array(ncfile, "var")
    Traceback (most recent call last):
    ...
    RuntimeError: Variable `var` of NetCDF file `test.nc` must be 2-dimensional (or \
3-dimensional with a length of one on the second axis) but has the shape `(2, 2, 3)`.

    The skipping of the `realization` axis is very specific to `Delft-FEWS`_.  To
    prevent hiding problems when reading erroneous data from other sources,
    |query_array| emits the following warning if the name of the second dimension is
    not `realization`:

    >>> from hydpy.core.testtools import warn_later
    >>> with TestIO():
    ...     with netcdf4.Dataset("test.nc", "w") as ncfile:
    ...         create_dimension(ncfile, "time", 2)
    ...         create_dimension(ncfile, "realisation", 1)
    ...         create_dimension(ncfile, "stations", 3)
    ...         var = create_variable(ncfile, "var", "f8",
    ...                               ("time", "realisation", "stations"))
    ...     with netcdf4.Dataset("test.nc", "r") as ncfile, warn_later():
    ...         print_matrix(query_array(ncfile, "var"))
    | nan, nan, nan |
    | nan, nan, nan |
    UserWarning: Variable `var` of NetCDF file `test.nc` is 3-dimensional and the \
length of the second dimension is one, but its name is `realisation` instead of \
`realization`.
    """
    variable = query_variable(ncfile, name)
    if _is_realisation(variable, ncfile):
        maskedarray = variable[:, 0, :]
    else:
        maskedarray = variable[:]
    fillvalue_ = getattr(variable, "_FillValue", numpy.nan)
    if not numpy.isnan(fillvalue_):
        maskedarray[maskedarray.mask] = numpy.nan
    return cast(NDArrayFloat, maskedarray.data)


def _is_realisation(variable: netcdf4.Variable, ncfile: netcdf4.Dataset) -> bool:
    if variable.ndim == 2:
        return False
    if (variable.ndim == 3) and (variable.shape[1] == 1):
        if variable.dimensions[1] != "realization":
            warnings.warn(
                f"Variable `{variable.name}` of NetCDF file `{ncfile.filepath()}` is "
                f"3-dimensional and the length of the second dimension is one, but "
                f"its name is `{variable.dimensions[1]}` instead of `realization`."
            )
        return True
    raise RuntimeError(
        f"Variable `{variable.name}` of NetCDF file `{ncfile.filepath()}` must be "
        f"2-dimensional (or 3-dimensional with a length of one on the second axis) "
        f"but has the shape `{variable.shape}`."
    )


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


def _timereference_currenttime(sequence: sequencetools.IOSequence) -> bool:
    return isinstance(sequence, sequencetools.StateSequence)


class JITAccessInfo(NamedTuple):
    """Helper class for structuring reading from or writing to a NetCDF file "just in
    time" during a simulation run for a specific |NetCDFVariableFlat| object."""

    ncvariable: netcdf4.Variable
    """Variable for direct access to the relevant section of the NetCDF file."""
    realisation: bool
    """Flag that indicates if the relevant |JITAccessInfo.ncvariable| comes with an
    additional `realization` dimension (explained in the documentation on function
    |query_array|)"""
    timedelta: int
    """Difference between the relevant row of the NetCDF file and the current 
    simulation index (as defined by |Idx_Sim|)."""
    columns: tuple[int, ...]
    """Indices of the relevant columns of the NetCDF file correctly ordered with 
    respect to |JITAccessInfo.data|."""
    data: NDArrayFloat
    """Bridge to transfer data between the NetCDF file and the (cythonized) 
    hydrological models."""


class JITAccessHandler(NamedTuple):
    """Handler used by the |SequenceManager| object available in module |pub| for
    reading data from and/or writing data to NetCDF files at each step of a simulation
    run."""

    readers: tuple[JITAccessInfo, ...]
    """All |JITAccessInfo| objects responsible for reading data during the simulation 
    run."""
    writers: tuple[JITAccessInfo, ...]
    """All |JITAccessInfo| objects responsible for writing data during the simulation 
    run."""

    def read_slices(self, idx: int) -> None:
        """Read the time slice of the current simulation step from each NetCDF file
        selected for reading."""
        for reader in self.readers:
            jdx = idx + reader.timedelta
            if reader.realisation:
                reader.data[:] = reader.ncvariable[jdx, 0, reader.columns]
            else:
                reader.data[:] = reader.ncvariable[jdx, reader.columns]

    def write_slices(self, idx: int) -> None:
        """Write the time slice of the current simulation step from each NetCDF file
        selected for writing."""
        for writer in self.writers:
            jdx = idx + writer.timedelta
            if writer.realisation:
                writer.ncvariable[jdx, 0, writer.columns] = writer.data
            else:
                writer.ncvariable[jdx, writer.columns] = writer.data


class Subdevice2Index:
    """Return type of method |NetCDFVariable.query_subdevice2index|."""

    dict_: dict[str, int]
    name_sequence: str
    name_ncfile: str

    def __init__(self, dict_: dict[str, int], name_ncfile: str) -> None:
        self.dict_ = dict_
        self.name_ncfile = name_ncfile

    def get_index(self, name_subdevice: str) -> int:
        """Item access to the wrapped |dict| object with a specialised error message."""
        try:
            return self.dict_[name_subdevice]
        except KeyError:
            raise RuntimeError(
                f"No data for (sub)device `{name_subdevice}` is available in NetCDF "
                f"file `{self.name_ncfile}`."
            ) from None


class NetCDFVariableInfo(NamedTuple):
    """Returned type of |NetCDFVariableFlatWriter| and |NetCDFVariableAggregated| when
    querying logged data via attribute access."""

    sequence: sequencetools.IOSequence
    array: sequencetools.InfoArray | None


class NetCDFVariable(abc.ABC):
    """Base class for handling single NetCDF variables of a single NetCDF file."""

    filepath: str
    """Path to the relevant NetCDF file."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    @property
    def name(self) -> str:
        """Name of the NetCDF file and the NetCDF variable containing the time series
        data."""
        return os.path.basename(self.filepath)[:-3]

    @property
    @abc.abstractmethod
    def subdevicenames(self) -> tuple[str, ...]:
        """The names of all relevant (sub)devices."""

    def query_subdevices(self, ncfile: netcdf4.Dataset) -> list[str]:
        """Query the names of the (sub)devices of the logged sequences from the given
        NetCDF file.

        We apply method |NetCDFVariable.query_subdevices| on an empty NetCDF file.  The
        error message shows that the method tries to query the (sub)device names:

        >>> from hydpy import TestIO
        >>> from hydpy.core.netcdftools import netcdf4, NetCDFVariableFlatWriter
        >>> class Var(NetCDFVariableFlatWriter):
        ...     pass
        >>> Var.subdevicenames = "element1", "element_2"
        >>> var = Var("filename.nc")
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("filename.nc", "w")
        >>> var.query_subdevices(ncfile)
        Traceback (most recent call last):
        ...
        RuntimeError: NetCDF file `filename.nc` does neither contain a variable named \
`values_station_id` nor `station_id` for defining coordinate locations.

        After inserting the (sub)device names, they can be queried and returned:

        >>> var.insert_subdevices(ncfile)
        >>> Var("filename.nc").query_subdevices(ncfile)
        ['element1', 'element_2']

        >>> ncfile.close()
        """
        tests = [f"{pref}{varmapping['subdevices']}" for pref in ("values_", "")]
        for subdevices in tests:
            try:
                chars = ncfile[subdevices][:]
                break
            except (IndexError, KeyError):
                pass
        else:
            raise RuntimeError(
                f"NetCDF file `{get_filepath(ncfile)}` does neither contain a "
                f"variable named `{tests[0]}` nor `{tests[1]}` for defining "
                f"coordinate locations."
            )
        return chars2str(chars.data)

    def query_subdevice2index(self, ncfile: netcdf4.Dataset) -> Subdevice2Index:
        """Return a |Subdevice2Index| object that maps the (sub)device names to their
        position within the given NetCDF file.

        Method |NetCDFVariable.query_subdevice2index| relies on
        |NetCDFVariable.query_subdevices|.  The returned |Subdevice2Index| object
        remembers the NetCDF file from which the (sub)device names stem, allowing for
        clear error messages:

        >>> from hydpy import TestIO
        >>> from hydpy.core.netcdftools import (
        ...     netcdf4, NetCDFVariableFlatWriter, str2chars)
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("filename.nc", "w")
        >>> class Var(NetCDFVariableFlatWriter):
        ...     pass
        >>> Var.subdevicenames = ["element3", "element1", "element1_1", "element2"]
        >>> var = Var("filename.nc")
        >>> var.insert_subdevices(ncfile)
        >>> subdevice2index = var.query_subdevice2index(ncfile)
        >>> subdevice2index.get_index("element1_1")
        2
        >>> subdevice2index.get_index("element3")
        0
        >>> subdevice2index.get_index("element5")
        Traceback (most recent call last):
        ...
        RuntimeError: No data for (sub)device `element5` is available in NetCDF file \
`filename.nc`.

        Additionally, |NetCDFVariable.query_subdevice2index| checks for duplicates:

        >>> ncfile["station_id"][:] = str2chars(
        ...     ["element3", "element1", "element1_1", "element1"])
        >>> var.query_subdevice2index(ncfile)
        Traceback (most recent call last):
        ...
        RuntimeError: The NetCDF file `filename.nc` contains duplicate (sub)device \
names (the first found duplicate is `element1`).

        >>> ncfile.close()
        """
        subdevices = self.query_subdevices(ncfile)
        self._test_duplicate_exists(ncfile, subdevices)
        subdev2index = {subdev: idx for (idx, subdev) in enumerate(subdevices)}
        return Subdevice2Index(subdev2index, get_filepath(ncfile))

    @property
    @abc.abstractmethod
    def _anysequence(self) -> sequencetools.IOSequence: ...

    @property
    @abc.abstractmethod
    def _descr2anysequence(self) -> dict[str, sequencetools.IOSequence]: ...

    def _test_duplicate_exists(
        self, ncfile: netcdf4.Dataset, subdevices: Sequence[str]
    ) -> None:
        if len(subdevices) != len(set(subdevices)):
            for idx, name1 in enumerate(subdevices):
                for name2 in subdevices[idx + 1 :]:
                    if name1 == name2:
                        raise RuntimeError(
                            f"The NetCDF file `{get_filepath(ncfile)}` contains "
                            f"duplicate (sub)device names (the first found duplicate "
                            f"is `{name1}`)."
                        )

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


class NetCDFVariableFlat(NetCDFVariable, abc.ABC):
    """Base class for handling single "flat" NetCDF variables (which deal with
    unaggregated time series) of single NetCDF files.

    The following examples describe the functioning of the subclasses
    |NetCDFVariableFlatReader| and |NetCDFVariableFlatWriter|, which serve to read and
    write data, respectively.

    We prepare some devices handling some sequences by applying the function
    |prepare_io_example_1|.  We limit our attention to the returned elements, which
    handle the more diverse sequences:

    >>> from hydpy.core.testtools import prepare_io_example_1
    >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()

    We define three |NetCDFVariableFlatWriter| instances with different
    dimensionalities structures and log the |lland_inputs.Nied| and |lland_fluxes.NKor|
    instances of the first two elements and the |hland_states.SP| instance of the
    fourth element:

    >>> from hydpy.core.netcdftools import NetCDFVariableFlatWriter
    >>> var_nied = NetCDFVariableFlatWriter("nied.nc")
    >>> var_nkor = NetCDFVariableFlatWriter("nkor.nc")
    >>> var_sp = NetCDFVariableFlatWriter("sp.nc")
    >>> for element in (element1, element3):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)
    >>> sp = element4.model.sequences.states.sp
    >>> var_sp.log(sp, sp.series)

    We further try to log the equally named "wind speed" sequences of the main model
    |lland_knauf| and the submodel |evap_aet_morsim|.  As both models are handled by
    the same element, which defines the column name, their time series cannot be stored
    separately in the same NetCDF file.  The |MixinVariableWriter.log| method defined
    by |MixinVariableWriter| checks for potential conflicts:

    >>> var_windspeed = NetCDFVariableFlatWriter("windspeed.nc")
    >>> windspeed_l = element3.model.sequences.inputs.windspeed
    >>> var_windspeed.log(windspeed_l, windspeed_l.series)
    >>> windspeed_e = element3.model.aetmodel.sequences.inputs.windspeed
    >>> var_windspeed.log(windspeed_e, 2.0 * windspeed_e.series)
    Traceback (most recent call last):
    ...
    RuntimeError: When trying to log the time series of sequence `windspeed` of \
element `element3` of model `evap_aet_morsim` for writing, the following error \
occurred: Sequence `windspeed` of element `element3` of model `lland_knauf` is \
already registered under the same column name(s) but with different time series data.

    If the supplied time series are equal, there is no problem.  So,
    |MixinVariableWriter.log| neither accepts the new sequence nor raises an error in
    such cases:

    ToDo: Should we implement additional checks for just-in-time writing?

    >>> assert var_windspeed.element3.sequence is windspeed_l
    >>> var_windspeed.log(windspeed_e, windspeed_e.series)
    >>> assert var_windspeed.element3.sequence is windspeed_l

    We write the data of all logged sequences to separate NetCDF files:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     var_nied.write()
    ...     var_nkor.write()
    ...     var_sp.write()
    ...     var_windspeed.write()

    We set all the values of the selected sequences to -777 and check that they differ
    from the original values available via the `testarray` attribute:

    >>> nied = element1.model.sequences.inputs.nied
    >>> nkor = element3.model.sequences.fluxes.nkor
    >>> sp = element4.model.sequences.states.sp
    >>> import numpy
    >>> for seq in (nied, nkor, sp, windspeed_l, windspeed_e):
    ...     seq.series = -777.0
    ...     assert numpy.any(seq.series != seq.testarray)

    Now, we prepare three |NetCDFVariableFlatReader| instances and log the same
    sequences as above, open the existing NetCDF file for reading, read its data, and
    confirm that it has been correctly passed to the test sequences:

    >>> from hydpy.core.netcdftools import NetCDFVariableFlatReader
    >>> var_nied = NetCDFVariableFlatReader("nied.nc")
    >>> var_nkor = NetCDFVariableFlatReader("nkor.nc")
    >>> var_sp = NetCDFVariableFlatReader("sp.nc")
    >>> var_windspeed = NetCDFVariableFlatReader("windspeed.nc")
    >>> for element in (element1, element3):
    ...     sequences = element.model.sequences
    ...     var_nied.log(sequences.inputs.nied)
    ...     var_nkor.log(sequences.fluxes.nkor)
    >>> var_sp.log(sp)
    >>> var_windspeed.log(windspeed_l)
    >>> var_windspeed.log(windspeed_e)
    >>> with TestIO():
    ...     var_nied.read()
    ...     var_nkor.read()
    ...     var_sp.read()
    ...     var_windspeed.read()
    >>> for seq in (nied, nkor, sp):
    ...     assert numpy.all(seq.series == seq.testarray)
    >>> assert numpy.all(windspeed_l.series == windspeed_l.testarray)
    >>> assert numpy.all(windspeed_e.series == windspeed_l.testarray)

    Trying to read data that is not stored properly results in error messages like
    the following:

    >>> for element in (element1, element2, element3):
    ...     element.model.sequences.inputs.nied.series = -777.0
    ...     var_nied.log(element.model.sequences.inputs.nied)
    >>> with TestIO():
    ...     var_nied.read()
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to read data from NetCDF file `nied.nc`, the following \
error occurred: No data for (sub)device `element2` is available in NetCDF file \
`nied.nc`.

    Note that method |NetCDFVariableFlatReader.read| does not abort the reading process
    when missing a time series.  Instead, it sets the entries of the corresponding
    |IOSequence.series| array to |numpy.nan|, proceeds with the following sequences,
    and finally re-raises the first encountered exception:

    >>> element1.model.sequences.inputs.nied.series
    InfoArray([0., 1., 2., 3.])
    >>> element2.model.sequences.inputs.nied.series
    InfoArray([nan, nan, nan, nan])
    >>> element3.model.sequences.inputs.nied.series
    InfoArray([ 8.,  9., 10., 11.])
    """

    @property
    def subdevicenames(self) -> tuple[str, ...]:
        """The names of the (sub)devices.

        Property |NetCDFVariableFlat.subdevicenames| clarifies which column of NetCDF
        file contains the series of which (sub)device.  For  0-dimensional series like
        |lland_inputs.Nied|, we require no subdivision.  Hence, it returns the original
        device names:

        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlatReader
        >>> var = NetCDFVariableFlatReader("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         var.log(element.model.sequences.inputs.nied)
        >>> var.subdevicenames
        ('element1', 'element2', 'element3')

        For 1-dimensional sequences like |lland_fluxes.NKor|, a suffix defines the
        index of the respective subdevice.  For example, the third column of
        |NetCDFVariableFlatWriter.array| contains the series of the first hydrological
        response unit of the second element:

        >>> var = NetCDFVariableFlatReader("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         var.log( element.model.sequences.fluxes.nkor)
        >>> var.subdevicenames
        ('element1_0', 'element2_0', 'element2_1', 'element3_0', 'element3_1', \
'element3_2')

        2-dimensional sequences like |hland_states.SP| require an additional suffix:

        >>> var = NetCDFVariableFlatReader("filename.nc")
        >>> var.log(elements.element4.model.sequences.states.sp)
        >>> var.subdevicenames
        ('element4_0_0', 'element4_0_1', 'element4_0_2', 'element4_1_0', \
'element4_1_1', 'element4_1_2')
        """
        stats: collections.deque[str] = collections.deque()
        for devicename, seq in self._descr2anysequence.items():
            if seq.NDIM:
                temp = devicename + "_"
                for prod in self._product(seq.shape):
                    stats.append(temp + "_".join(str(idx) for idx in prod))
            else:
                stats.append(devicename)
        return tuple(stats)

    @property
    def shape(self) -> tuple[int, int]:
        """Required shape of the NetCDF variable.

        For 0-dimensional sequences like |lland_inputs.Nied|, the first axis
        corresponds to the number of timesteps and the second axis to the number of
        devices:

        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlatReader
        >>> var = NetCDFVariableFlatReader("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         var.log(element.model.sequences.inputs.nied)
        >>> var.shape
        (4, 3)

        For 1-dimensional sequences as |lland_fluxes.NKor|, the second axis corresponds
        to "subdevices".  Here, these "subdevices" are hydrological response units of
        different elements.  The model instances of the three elements define one, two,
        and three response units, respectively, making up a sum of six subdevices:

        >>> var = NetCDFVariableFlatReader("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         var.log(element.model.sequences.fluxes.nkor)
        >>> var.shape
        (4, 6)

        The above statements also hold for 2-dimensional sequences as
        |hland_states.SP|.  In this specific case, each "subdevice" corresponds to a
        single snow class (one element times three zones times two snow classes makes
        six subdevices):

        >>> var = NetCDFVariableFlatReader( "filename.nc")
        >>> var.log(elements.element4.model.sequences.states.sp)
        >>> var.shape
        (4, 6)
        """
        return (
            len(hydpy.pub.timegrids.init),
            sum(seq.numberofvalues for seq in self._descr2anysequence.values()),
        )

    @staticmethod
    def _product(shape: Sequence[int]) -> Iterator[tuple[int, ...]]:
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


class NetCDFVariableFlatReader(NetCDFVariableFlat):
    """Concrete class for reading data of single "flat" NetCDF variables (which deal
    with unaggregated time series) from single NetCDF files.

    For a general introduction to using |NetCDFVariableFlatReader|, see the
    documentation on base class |NetCDFVariableFlat|.
    """

    _descr2sequences: dict[str, set[sequencetools.IOSequence]]

    def __init__(self, filepath: str) -> None:
        super().__init__(filepath=filepath)
        self._descr2sequences = {}

    @property
    def _anysequence(self) -> sequencetools.IOSequence:
        return next(iter(next(iter(self._descr2sequences.values()))))

    @property
    def _descr2anysequence(self) -> dict[str, sequencetools.IOSequence]:
        return {d: next(iter(s)) for d, s in self._descr2sequences.items()}

    def log(self, sequence: sequencetools.IOSequence) -> None:
        """Log the given |IOSequence| object for reading data.

        The logged sequence is available via attribute access:

        >>> from hydpy.core.netcdftools import NetCDFVariableFlatReader
        >>> class Var(NetCDFVariableFlatReader):
        ...     pass
        >>> var = Var("filepath.nc")
        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> nkor = elements.element1.model.sequences.fluxes.nkor
        >>> var.log(nkor)
        >>> assert "element1" in dir(var)
        >>> assert nkor in var.element1
        >>> assert "element2" not in dir(var)
        >>> var.element2  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: The selected NetCDFVariableFlatReader object does neither \
handle a sequence for the (sub)device `element2` nor define a member named \
`element2`...
        """
        descr_device = sequence.descr_device
        if descr_device not in self._descr2sequences:
            self._descr2sequences[descr_device] = set()
        self._descr2sequences[descr_device].add(sequence)

    def read(self) -> None:
        """Read the data from the relevant NetCDF file.

        See the general documentation on class |NetCDFVariableFlat| for some examples.
        """
        try:
            with netcdf4.Dataset(self.filepath, "r") as ncfile:
                timegrid = query_timegrid(ncfile, self._anysequence)
                array = query_array(ncfile, self.name)
                idxs: tuple[Any] = (slice(None),)
                subdev2index = self.query_subdevice2index(ncfile)
                first_exception: RuntimeError | None = None
                for devicename, seqs in self._descr2sequences.items():
                    for seq in seqs:
                        try:
                            if seq.NDIM:
                                subshape = (array.shape[0],) + seq.shape
                                subarray = numpy.empty(subshape)
                                temp = devicename + "_"
                                for prod in self._product(seq.shape):
                                    station = temp + "_".join(str(idx) for idx in prod)
                                    subarray[idxs + prod] = array[
                                        :, subdev2index.get_index(station)
                                    ]
                            else:
                                subarray = array[:, subdev2index.get_index(devicename)]
                            series = seq.adjust_series(timegrid, subarray)
                            seq.apply_adjusted_series(timegrid, series)
                        except RuntimeError as current_exception:
                            seq.series[:] = numpy.nan
                            if first_exception is None:
                                first_exception = current_exception
                if first_exception is not None:
                    raise first_exception
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to read data from NetCDF file `{self.filepath}`"
            )

    def __getattr__(self, name: str) -> set[sequencetools.IOSequence]:
        try:
            return self._descr2sequences[name]
        except KeyError:
            raise AttributeError(
                f"The selected NetCDFVariableFlatReader object does neither handle a "
                f"sequence for the (sub)device `{name}` nor define a member named "
                f"`{name}`."
            ) from None

    def __dir__(self) -> list[str]:
        return cast(list[str], super().__dir__()) + list(self._descr2sequences.keys())


class MixinVariableWriter(NetCDFVariable, abc.ABC):
    """Mixin class for |NetCDFVariableFlatWriter| and |NetCDFVariableAggregated|."""

    _descr2sequence: dict[str, sequencetools.IOSequence]
    _descr2array: dict[str, sequencetools.InfoArray | None]

    def __init__(self, filepath: str) -> None:
        assert isinstance(self, NetCDFVariable)
        super().__init__(filepath=filepath)
        self._descr2sequence = {}
        self._descr2array = {}

    @property
    def _anysequence(self) -> sequencetools.IOSequence:
        return next(iter(self._descr2sequence.values()))

    @property
    def _descr2anysequence(self) -> dict[str, sequencetools.IOSequence]:
        return self._descr2sequence

    def insert_subdevices(self, ncfile: netcdf4.Dataset) -> None:
        """Insert a variable of the names of the (sub)devices of the logged sequences
        into the given NetCDF file.

        We prepare a |NetCDFVariableFlatWriter| subclass with fixed (sub)device names:

        >>> from hydpy import TestIO
        >>> from hydpy.core.netcdftools import NetCDFVariableFlatWriter, chars2str
        >>> from hydpy.core.netcdftools import netcdf4
        >>> class Var(NetCDFVariableFlatWriter):
        ...     pass
        >>> Var.subdevicenames = "element1", "element_2", "element_ß"

        The first dimension of the added variable corresponds to the number of
        (sub)devices, and the second dimension to the number of characters of the
        longest (sub)device name:

        >>> var = Var("filename.nc")
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("filename.nc", "w")
        >>> var.insert_subdevices(ncfile)
        >>> ncfile["station_id"].dimensions
        ('stations', 'char_leng_name')
        >>> ncfile["station_id"].shape
        (3, 10)
        >>> chars2str(ncfile["station_id"][:].data)
        ['element1', 'element_2', 'element_ß']
        >>> ncfile.close()
        """
        nmb_subdevices = dimmapping["nmb_subdevices"]
        nmb_characters = dimmapping["nmb_characters"]
        subdevices = varmapping["subdevices"]
        statchars = str2chars(self.subdevicenames)
        create_dimension(ncfile, nmb_subdevices, statchars.shape[0])
        create_dimension(ncfile, nmb_characters, statchars.shape[1])
        create_variable(ncfile, subdevices, "S1", (nmb_subdevices, nmb_characters))
        ncfile[subdevices][:, :] = statchars

    def log(
        self,
        sequence: sequencetools.IOSequence,
        infoarray: sequencetools.InfoArray | None = None,
    ) -> None:
        """Log the given |IOSequence| object for writing data.

        When writing data "in one step", the second argument must be an |InfoArray|.
        Pass |None| when using |NetCDFVariableFlatWriter| to write data "just in time".
        The `infoarray` argument allows for passing alternative data that replaces the
        original series of the |IOSequence| object.

        The logged time series data is available via attribute access:

        >>> from hydpy.core.netcdftools import NetCDFVariableFlatWriter
        >>> class Var(NetCDFVariableFlatWriter):
        ...     pass
        >>> var = Var("filepath.nc")
        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> nkor = elements.element1.model.sequences.fluxes.nkor
        >>> var.log(nkor, nkor.series)
        >>> assert "element1" in dir(var)
        >>> assert var.element1.sequence is nkor
        >>> import numpy
        >>> assert numpy.all(var.element1.array == nkor.series)
        >>> assert "element2" not in dir(var)
        >>> var.element2  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: The selected NetCDFVariable object does neither handle time \
series data for the (sub)device `element2` nor define a member named `element2`...
        """

        def _dp(seq: sequencetools.IOSequence) -> str:
            return (
                f"{objecttools.devicephrase(sequence)} of model "
                f"`{seq.subseqs.seqs.model.name}`"
            )

        descr_device = sequence.descr_device
        old_sequence = self._descr2sequence.get(descr_device)
        if old_sequence is None:
            self._descr2sequence[descr_device] = sequence
            self._descr2array[descr_device] = infoarray
        elif old_sequence is not sequence:
            old_array = self._descr2array[descr_device]
            if (
                (infoarray is not None)
                and (old_array is not None)
                and not numpy.array_equal(old_array, infoarray, equal_nan=True)
            ):
                raise RuntimeError(
                    f"When trying to log the time series of sequence {_dp(sequence)} "
                    f"for writing, the following error occurred: Sequence "
                    f"{_dp(old_sequence)} is already registered under the same column "
                    f"name(s) but with different time series data."
                )

    @property
    @abc.abstractmethod
    def array(self) -> NDArrayFloat:
        """A |numpy.ndarray| containing the values of all logged sequences."""

    def write(self) -> None:
        """Write the logged data to a new NetCDF file.

        See the general documentation on classes |NetCDFVariableFlatWriter| and
        |NetCDFVariableAggregated| for some examples.
        """
        with netcdf4.Dataset(self.filepath, "w") as ncfile:
            now = time.ctime(time.time())
            ncfile.history = f"Created {now} by HydPy {hydpy.__version__}"
            ncfile.sequence = (
                f"{os.path.split(self.filepath)[-1][:-3]} "
                f"(naming convention: {hydpy.pub.sequencemanager.convention})"
            )
            ncfile.Conventions = "CF-1.8"
            init = hydpy.pub.timegrids.init
            timeunit = init.firstdate.to_cfunits("hours")
            opts = hydpy.pub.options
            if _timereference_currenttime(self._anysequence):
                with opts.timestampleft(False):
                    timepoints = init.to_timepoints("hours")
                ncfile.timereference = "current time"
            else:
                timepoints = init.to_timepoints("hours")
                ncfile.timereference = (
                    f"{'left' if opts.timestampleft else 'right'} interval boundary"
                )
            self._insert_timepoints(ncfile, timepoints, timeunit)
            self.insert_subdevices(ncfile)
            dimensions = dimmapping["nmb_timepoints"], dimmapping["nmb_subdevices"]
            create_variable(ncfile, self.name, "f8", dimensions)
            ncfile[self.name][:] = self.array

    def __getattr__(self, name: str) -> NetCDFVariableInfo:
        try:
            return NetCDFVariableInfo(
                self._descr2sequence[name], self._descr2array[name]
            )
        except KeyError:
            raise AttributeError(
                f"The selected NetCDFVariable object does neither handle time series "
                f"data for the (sub)device `{name}` nor define a member named "
                f"`{name}`."
            ) from None

    def __dir__(self) -> list[str]:
        return cast(list[str], super().__dir__()) + list(self._descr2sequence.keys())


class NetCDFVariableFlatWriter(MixinVariableWriter, NetCDFVariableFlat):
    """Concrete class for writing data from single "flat" NetCDF variables (which deal
    with unaggregated time series) to single NetCDF files.

    For a general introduction to using |NetCDFVariableFlatWriter|, see the
    documentation on base class |NetCDFVariableFlat|.
    """

    @property
    def array(self) -> NDArrayFloat:
        """The time series data of all logged |IOSequence| objects in one single
        |numpy.ndarray| object.

        The documentation on |NetCDFVariableFlat.shape| explains the structure of
        |NetCDFVariableFlatWriter.array|.  The first example confirms that the first
        axis corresponds to time while the second corresponds to the location:

        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlatWriter
        >>> var = NetCDFVariableFlatWriter("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nied1 = element.model.sequences.inputs.nied
        ...         var.log(nied1, nied1.series)
        >>> from hydpy import print_matrix
        >>> print_matrix(var.array)
        | 0.0, 4.0, 8.0 |
        | 1.0, 5.0, 9.0 |
        | 2.0, 6.0, 10.0 |
        | 3.0, 7.0, 11.0 |

        The flattening of higher-dimensional sequences spreads the time series of
        individual "subdevices" over the array's columns.  For the 1-dimensional
        sequence |lland_fluxes.NKor|, we find the time series of both zones of the
        second element in columns two and three:

        >>> var = NetCDFVariableFlatWriter("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         var.log(nkor, nkor.series)
        >>> print_matrix(var.array[:, 1:3])
        | 16.0, 17.0 |
        | 18.0, 19.0 |
        | 20.0, 21.0 |
        | 22.0, 23.0 |

        The above statements also hold for 2-dimensional sequences like
        |hland_states.SP|.  In this specific case, each column contains the time series
        of a single snow class:

        >>> var = NetCDFVariableFlatWriter("filename.nc")
        >>> sp = elements.element4.model.sequences.states.sp
        >>> var.log(sp, sp.series)
        >>> print_matrix(var.array)
        | 68.0, 69.0, 70.0, 71.0, 72.0, 73.0 |
        | 74.0, 75.0, 76.0, 77.0, 78.0, 79.0 |
        | 80.0, 81.0, 82.0, 83.0, 84.0, 85.0 |
        | 86.0, 87.0, 88.0, 89.0, 90.0, 91.0 |
        """
        array = numpy.full(self.shape, fillvalue, dtype=config.NP_FLOAT)
        idx0 = 0
        idxs: list[Any] = [slice(None)]
        for seq, subarray in zip(
            self._descr2sequence.values(), self._descr2array.values()
        ):
            for prod in self._product(seq.shape):
                if subarray is not None:
                    subsubarray = subarray[tuple(idxs + list(prod))]
                    array[:, idx0] = subsubarray
                idx0 += 1
        return array


class NetCDFVariableAggregated(MixinVariableWriter, NetCDFVariable):
    """Concrete class for writing data from single "aggregated" NetCDF variables (which
    deal with aggregated time series) to single NetCDF files.

    Class |NetCDFVariableAggregated| works very similarly to class
    |NetCDFVariableFlatWriter|. The following is a selection of the more thoroughly
    explained examples of the documentation on class |NetCDFVariableFlat|:

    >>> from hydpy.core.testtools import prepare_io_example_1
    >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()
    >>> from hydpy.core.netcdftools import NetCDFVariableAggregated
    >>> var_nied = NetCDFVariableAggregated("nied.nc")
    >>> var_nkor = NetCDFVariableAggregated("nkor.nc")
    >>> var_sp = NetCDFVariableAggregated("sp.nc")
    >>> for element in (element1, element2):
    ...     nied = element.model.sequences.inputs.nied
    ...     var_nied.log(nied, nied.average_series())
    ...     nkor = element.model.sequences.fluxes.nkor
    ...     var_nkor.log(nkor, nkor.average_series())
    >>> sp = element4.model.sequences.states.sp
    >>> var_sp.log(sp, sp.average_series())
    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     var_nied.write()
    ...     var_nkor.write()
    ...     var_sp.write()

    As |NetCDFVariableAggregated| provides no reading functionality, we show that the
    aggregated values are readily available using the external NetCDF4 library:

    >>> import numpy
    >>> from hydpy import print_matrix
    >>> with TestIO(), netcdf4.Dataset("nied.nc", "r") as ncfile:
    ...     print_matrix(numpy.array(ncfile["nied"][:]))
    | 0.0, 4.0 |
    | 1.0, 5.0 |
    | 2.0, 6.0 |
    | 3.0, 7.0 |

    >>> with TestIO(), netcdf4.Dataset("nkor.nc", "r") as ncfile:
    ...     print_matrix(numpy.array(ncfile["nkor"][:]))
    | 12.0, 16.5 |
    | 13.0, 18.5 |
    | 14.0, 20.5 |
    | 15.0, 22.5 |

    >>> with TestIO(), netcdf4.Dataset("sp.nc", "r") as ncfile:
    ...     print_matrix(numpy.array(ncfile["sp"][:]))
    | 70.5 |
    | 76.5 |
    | 82.5 |
    | 88.5 |
    """

    @property
    def shape(self) -> tuple[int, int]:
        """Required shape of |NetCDFVariableAggregated.array|.

        The first axis corresponds to the number of timesteps and the second axis to
        the number of devices.  We show this for the 1-dimensional input sequence
        |lland_fluxes.NKor|:

        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAggregated
        >>> var = NetCDFVariableAggregated("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         var.log(element.model.sequences.fluxes.nkor, None)
        >>> var.shape
        (4, 3)

        There is no difference for 2-dimensional sequences as aggregating their time
        series also results in 1-dimensional data:

        >>> var = NetCDFVariableAggregated("filename.nc")
        >>> var.log(elements.element4.model.sequences.states.sp, None)
        >>> var.shape
        (4, 1)
        """
        return len(hydpy.pub.timegrids.init), len(self._descr2sequence)

    @property
    def array(self) -> NDArrayFloat:
        """The aggregated time series data of all logged |IOSequence| objects in a
        single |numpy.ndarray| object.

        The documentation on |NetCDFVariableAggregated.shape| explains the structure of
        |NetCDFVariableAggregated.array|.  This first example confirms that the first
        axis corresponds to time while the second corresponds to the location:

        >>> from hydpy.core.testtools import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAggregated
        >>> var = NetCDFVariableAggregated("filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         var.log(nkor, nkor.average_series())
        >>> from hydpy import print_matrix
        >>> print_matrix(var.array)
        | 12.0, 16.5, 25.0 |
        | 13.0, 18.5, 28.0 |
        | 14.0, 20.5, 31.0 |
        | 15.0, 22.5, 34.0 |

        There is no difference for 2-dimensional sequences as aggregating their time
        series also results in 1-dimensional data:

        >>> var = NetCDFVariableAggregated("filename.nc")
        >>> sp = elements.element4.model.sequences.states.sp
        >>> var.log(sp, sp.average_series())
        >>> print_matrix(var.array)
        | 70.5 |
        | 76.5 |
        | 82.5 |
        | 88.5 |
        """
        array = numpy.full(self.shape, fillvalue, dtype=config.NP_FLOAT)
        for idx, subarray in enumerate(self._descr2array.values()):
            if subarray is not None:
                array[:, idx] = subarray
        return array

    @property
    def subdevicenames(self) -> tuple[str, ...]:
        """The names of all relevant devices."""
        return tuple(self._descr2sequence.keys())


class NetCDFInterfaceBase(Generic[TypeNetCDFVariable]):
    """Base class for interfaces between |SequenceManager| and multiple NetCDF files.

    The core task of all concrete |NetCDFInterfaceBase| subclasses is to distribute
    different |IOSequence| objects on multiple instances of the concrete subclasses of
    |NetCDFVariable|.  The following examples describe the functioning of the
    subclasses |NetCDFInterfaceReader| and |NetCDFInterfaceWriter|, which serve to read
    and write data "in one step", respectively.

    We prepare a |SequenceManager| object and some devices handling different sequences
    by applying function |prepare_io_example_1|:

    >>> from hydpy.core.testtools import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    We collect all sequences used in the following examples except |lland_fluxes.NKor|
    of element `element1`, which we reserve for special tests:

    >>> sequences = []
    >>> for node in nodes:
    ...     sequences.append(node.sequences.sim)
    >>> for element in elements:
    ...     if element.model.name == "hland_96":
    ...         sequences.append(element.model.sequences.states.sp)
    ...     else:
    ...         sequences.append(element.model.sequences.inputs.nied)
    ...         if element.name != "element1":
    ...             sequences.append(element.model.sequences.fluxes.nkor)

    We prepare a |NetCDFInterfaceWriter| object and log and write all test sequences
    except |lland_fluxes.NKor| of element `element1`.  |NetCDFInterfaceWriter|
    initialises one |NetCDFVariableFlatWriter| and one |NetCDFVariableAggregated|
    object for each |IOSequence| subtype:

    >>> from hydpy.core.netcdftools import NetCDFInterfaceWriter
    >>> writer = NetCDFInterfaceWriter()
    >>> len(writer)
    0

    >>> from hydpy import pub, TestIO
    >>> pub.sequencemanager.filetype = "nc"
    >>> with TestIO():
    ...     for sequence in sequences:
    ...         _ = writer.log(sequence, sequence.series)
    ...         with pub.sequencemanager.aggregation("mean"):
    ...             _ = writer.log(sequence, sequence.average_series())
    >>> len(writer)
    14

    We change the relevant directory before logging the reserved sequence.
    |NetCDFInterfaceWriter| initialises two new |NetCDFVariable| objects, despite
    other |NetCDFVariable| objects related to the same sequence type already being
    available:

    >>> nkor = elements.element1.model.sequences.fluxes.nkor
    >>> with TestIO():
    ...     pub.sequencemanager.currentdir = "test"
    ...     _ = writer.log(nkor, nkor.series)
    ...     with pub.sequencemanager.aggregation("mean"):
    ...         _ = writer.log(nkor, nkor.average_series())
    >>> len(writer)
    16

    You can query all relevant folder names and filenames via properties
    |NetCDFInterfaceBase.foldernames| and |NetCDFInterfaceBase.filenames|:

    >>> from hydpy import print_vector
    >>> print_vector(writer.foldernames)
    default, test
    >>> print_vector(writer.filenames)
    hland_96_state_sp, hland_96_state_sp_mean, lland_dd_flux_nkor,
    lland_dd_flux_nkor_mean, lland_dd_input_nied,
    lland_dd_input_nied_mean, lland_knauf_flux_nkor,
    lland_knauf_flux_nkor_mean, lland_knauf_input_nied,
    lland_knauf_input_nied_mean, sim_q, sim_q_mean, sim_t, sim_t_mean

    |NetCDFInterfaceWriter| provides attribute access to its |NetCDFVariable|
    instances, both via their filenames and the combination of their folder names and
    filenames:

    >>> assert writer.sim_q is writer.default_sim_q
    >>> print_vector(sorted(set(dir(writer)) - set(object.__dir__(writer))))
    default_hland_96_state_sp, default_hland_96_state_sp_mean,
    default_lland_dd_flux_nkor, default_lland_dd_flux_nkor_mean,
    default_lland_dd_input_nied, default_lland_dd_input_nied_mean,
    default_lland_knauf_flux_nkor, default_lland_knauf_flux_nkor_mean,
    default_lland_knauf_input_nied, default_lland_knauf_input_nied_mean,
    default_sim_q, default_sim_q_mean, default_sim_t, default_sim_t_mean,
    hland_96_state_sp, hland_96_state_sp_mean, lland_dd_input_nied,
    lland_dd_input_nied_mean, lland_knauf_flux_nkor,
    lland_knauf_flux_nkor_mean, lland_knauf_input_nied,
    lland_knauf_input_nied_mean, sim_q, sim_q_mean, sim_t, sim_t_mean,
    test_lland_dd_flux_nkor, test_lland_dd_flux_nkor_mean

    If multiple NetCDF files have the same name, you must prefix the relevant folder
    name:

    >>> writer.lland_dd_flux_nkor
    Traceback (most recent call last):
    ...
    RuntimeError: The current NetCDFInterface object handles multiple NetCDF files \
named `lland_dd_flux_nkor`.  Please be more specific.
    >>> assert hasattr(writer, "default_lland_dd_flux_nkor")

    |NetCDFInterfaceWriter| raises the following error for completely wrong attribute
    names:

    >>> writer.lland_dd
    Traceback (most recent call last):
    ...
    AttributeError: The current NetCDFInterface object neither handles a NetCDF file \
named `lland_dd` nor does it define a member named `lland_dd`.

    We write all NetCDF files into the `default` folder of the testing directory,
    defined by |prepare_io_example_1|:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     writer.write()

    We define a shorter initialisation period and re-activate the time series of the
    test sequences:

    >>> from hydpy import pub
    >>> pub.timegrids = "02.01.2000", "04.01.2000", "1d"
    >>> for sequence in sequences:
    ...     sequence.prepare_series(allocate_ram=False)
    ...     sequence.prepare_series(allocate_ram=True)
    >>> nkor.prepare_series(allocate_ram=False)
    >>> nkor.prepare_series(allocate_ram=True)

    We now initialise an object of class |NetCDFInterfaceReader|, log all test
    sequences, and read the test data of the defined subperiod:

    >>> from hydpy.core.netcdftools import NetCDFInterfaceReader
    >>> reader = NetCDFInterfaceReader()
    >>> with TestIO():
    ...     _ = reader.log(nkor)
    ...     pub.sequencemanager.currentdir = "default"
    ...     for sequence in sequences:
    ...         _ = reader.log(sequence)
    ...     reader.read()
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
    """

    _dir2file2var: dict[str, dict[str, TypeNetCDFVariable]]

    def __init__(self) -> None:
        self._dir2file2var = {}

    def _get_dir2file_stem(
        self, sequence: sequencetools.IOSequence
    ) -> tuple[dict[str, TypeNetCDFVariable], str]:
        dirpath = sequence.dirpath
        try:
            file2var = self._dir2file2var[dirpath]
        except KeyError:
            file2var = {}
            self._dir2file2var[dirpath] = file2var
        stem = sequence.filename.rsplit(".")[0]
        return file2var, stem

    @staticmethod
    def _yield_disksequences(
        deviceorder: Iterable[devicetools.Node | devicetools.Element],
    ) -> Iterator[sequencetools.IOSequence]:
        for device in deviceorder:
            if isinstance(device, devicetools.Node):
                yield from device.sequences
            else:
                for model in device.model.find_submodels(
                    include_mainmodel=True
                ).values():
                    for subseqs in model.sequences.iosubsequences:
                        yield from subseqs

    @property
    def foldernames(self) -> tuple[str, ...]:
        """The names of all folders the sequences shall be read from or written to."""
        return tuple(os.path.split(d)[-1] for d in self._dir2file2var)

    @property
    def filenames(self) -> tuple[str, ...]:
        """The base file names of all handled |NetCDFVariable| objects."""
        filenames = (file2var.keys() for file2var in self._dir2file2var.values())
        return tuple(sorted(set(itertools.chain(*filenames))))

    def __getattr__(self, name: str) -> TypeNetCDFVariable:
        counter = 0
        memory = None
        for dirpath, file2var in self._dir2file2var.items():
            dirname = os.path.split(dirpath)[-1]
            for filename, variable in file2var.items():
                if name == f"{dirname}_{filename}":
                    return variable
                if name == filename:
                    counter += 1
                    memory = variable
        if counter == 1:
            assert memory is not None
            return memory
        if counter > 1:
            raise RuntimeError(
                f"The current NetCDFInterface object handles multiple NetCDF files "
                f"named `{name}`.  Please be more specific."
            )
        raise AttributeError(
            f"The current NetCDFInterface object neither handles a NetCDF file named "
            f"`{name}` nor does it define a member named `{name}`."
        )

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __len__(self) -> int:
        return len(tuple(ncfiles for ncfiles in self))

    def __iter__(self) -> Iterator[TypeNetCDFVariable]:
        for file2var in self._dir2file2var.values():
            yield from file2var.values()

    def __dir__(self) -> list[str]:
        adds_long = []
        counter: collections.defaultdict[str, int] = collections.defaultdict(int)
        for dirpath, file2var in self._dir2file2var.items():
            dirname = os.path.split(dirpath)[-1]
            for filename in file2var.keys():
                adds_long.append(f"{dirname}_{filename}")
                counter[filename] += 1
        adds_short = [name for name, nmb in counter.items() if nmb == 1]
        return cast(list[str], super().__dir__()) + adds_long + adds_short


class NetCDFInterfaceReader(NetCDFInterfaceBase[NetCDFVariableFlatReader]):
    """Interface between |SequenceManager| and multiple |NetCDFVariableFlatReader|
    instances for reading data in one step.

    For a general introduction to using |NetCDFInterfaceReader|, see the
    documentation on base class |NetCDFInterfaceBase|.
    """

    def log(self, sequence: sequencetools.IOSequence) -> NetCDFVariableFlatReader:
        """Pass the given |IOSequence| to the log method of an already existing or, if
        necessary, freshly created |NetCDFVariableFlatReader| object."""
        file2var, stem = self._get_dir2file_stem(sequence=sequence)
        try:
            variable = file2var[stem]
        except KeyError:
            variable = NetCDFVariableFlatReader(sequence.filepath)
            file2var[stem] = variable
        variable.log(sequence)
        return variable

    @printtools.print_progress
    def read(self) -> None:
        """Call method |NetCDFVariableFlatReader.read| of all handled
        |NetCDFVariableFlatReader| objects."""
        for variable in printtools.progressbar(self):
            variable.read()


class NetCDFInterfaceWriter(
    NetCDFInterfaceBase[NetCDFVariableAggregated | NetCDFVariableFlatWriter]
):
    """Interface between |SequenceManager| and multiple |NetCDFVariableFlatWriter| or
    |NetCDFVariableAggregated| instances for writing data in one step.

    For a general introduction to using |NetCDFInterfaceWriter|, see the
    documentation on base class |NetCDFInterfaceBase|.
    """

    def log(
        self,
        sequence: sequencetools.IOSequence,
        infoarray: sequencetools.InfoArray | None = None,
    ) -> NetCDFVariableAggregated | NetCDFVariableFlatWriter:
        """Pass the given |IOSequence| to the log method of an already existing or, if
        necessary, freshly created |NetCDFVariableFlatWriter| or
        |NetCDFVariableAggregated| object (depending on the currently active
        |SequenceManager.aggregation| mode)."""
        file2var, stem = self._get_dir2file_stem(sequence=sequence)
        try:
            variable = file2var[stem]
        except KeyError:
            if hydpy.pub.sequencemanager.aggregation != "none":
                variable = NetCDFVariableAggregated(sequence.filepath)
            else:
                variable = NetCDFVariableFlatWriter(sequence.filepath)
            file2var[stem] = variable
        variable.log(sequence, infoarray)
        return variable

    @printtools.print_progress
    def write(self) -> None:
        """Call method |MixinVariableWriter.write| of all handled
        |NetCDFVariableFlatWriter| and |NetCDFVariableAggregated| objects."""
        for variable in printtools.progressbar(self):
            variable.write()


class NetCDFInterfaceJIT(NetCDFInterfaceBase[FlatUnion]):
    """Interface between |SequenceManager| and multiple |NetCDFVariableFlatWriter|
    instances for reading or writing data just in time.

    See the documentation on method |NetCDFInterfaceJIT.provide_jitaccess| for further
    information.
    """

    def log(self, sequence: sequencetools.IOSequence) -> FlatUnion:
        """Pass the given |IOSequence| to the log method of an already existing or, if
        necessary, freshly created |NetCDFVariableFlatWriter| object."""
        file2var, stem = self._get_dir2file_stem(sequence)
        try:
            variable = file2var[stem]
        except KeyError:
            if sequence.diskflag_reading:
                variable = NetCDFVariableFlatReader(sequence.filepath)
            else:
                variable = NetCDFVariableFlatWriter(sequence.filepath)
            file2var[stem] = variable
        variable.log(sequence)
        return variable

    @contextlib.contextmanager
    def provide_jitaccess(
        self, deviceorder: Iterable[devicetools.Node | devicetools.Element]
    ) -> Iterator[JITAccessHandler]:
        """Allow method |HydPy.simulate| of class |HydPy| to read data from or write
        data to NetCDF files "just in time" during simulation runs.

        We consider it unlikely users need ever to call the method
        |NetCDFInterfaceJIT.provide_jitaccess| directly.  See the documentation on
        class |HydPy| on applying it indirectly.  However, the following explanations
        might give some additional insights into the options and limitations of the
        related functionalities.

        You can only either read from or write to each NetCDF file.  We think this
        should rarely be a limitation for the anticipated workflows.  One particular
        situation where one could eventually try to read and write simultaneously is
        when trying to overwrite some of the available input data.  The following
        example tries to read the input data for all "headwater" catchments from
        specific NetCDF files but defines zero input values for all "non-headwater"
        catchments and tries to write them into the same files:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, print_vector, pub, TestIO
        >>> with TestIO():
        ...     hp = HydPy("HydPy-H-Lahn")
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
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
For a specific NetCDF file, you can either read or write data during a simulation run \
but for file `...hland_96_input_p.nc` both is requested.

        Clearly, each NetCDF file we want to read data from needs to span the current
        simulation period:

        >>> with TestIO():
        ...     pub.timegrids.init.firstdate = "1987-01-01"
        ...     pub.timegrids.sim.firstdate = "1988-01-01"
        ...     hp.prepare_inputseries(allocate_ram=False, read_jit=True)
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
The data of the NetCDF `...hland_96_input_p.nc` (Timegrid("1989-11-01 00:00:00", \
"2021-01-01 00:00:00", "1d")) does not correctly cover the current simulation period \
(Timegrid("1988-01-01 00:00:00", "1996-01-05 00:00:00", "1d")).

        However, each NetCDF file selected for writing must also cover the complete
        initialisation period.  If there is no adequately named NetCDF file,
        |NetCDFInterfaceJIT.provide_jitaccess| creates a new one for the current
        initialisation period.  If an adequately named file exists,
        |NetCDFInterfaceJIT.provide_jitaccess| uses it without any attempt to extend it
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
        >>> print_vector(
        ...     hp.elements["land_dill_assl"].model.sequences.factors.contriarea.series)
        0.497067, 0.496728, 0.496461, 0.496361
        >>> from hydpy.core.netcdftools import netcdf4
        >>> filepath = "HydPy-H-Lahn/series/default/hland_96_factor_contriarea.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath, "r") as ncfile:
        ...     print_vector(ncfile["hland_96_factor_contriarea"][:, 0])
        0.497067, 0.496728, 0.496461, 0.496361

        Under particular circumstances, the data variable of a NetCDF file can be
        3-dimensional.  The documentation on function |query_array| explains this in
        detail.  The following example demonstrates that reading and writing such
        3-dimensional variables "just in time" works correctly.  Therefore, we add a
        `realization` dimension to the input file `hland_96_input_t.nc` (part of the
        example project data) and the output file `hland_96_factor_contriarea.nc`
        (written in the previous example) and use them for redefining their data
        variables with this additional dimension.  As expected, the results are the
        same as in the previous example:

        >>> with TestIO():
        ...     for name in ("hland_96_input_t", "hland_96_factor_contriarea"):
        ...         filepath = f"HydPy-H-Lahn/series/default/{name}.nc"
        ...         with netcdf4.Dataset(filepath, "r+") as ncfile:
        ...             ncfile.renameVariable(name, "old")
        ...             _ = ncfile.createDimension("realization", 1)
        ...             var = ncfile.createVariable(name, "f8",
        ...                     dimensions=("time", "realization", "stations"))
        ...             if name == "hland_96_input_t":
        ...                 var[:] = ncfile["old"][:]
        ...             else:
        ...                 var[:] = -999.0
        ...     pub.timegrids = "1996-01-01", "1996-01-05", "1d"
        ...     hp.simulate()
        >>> with TestIO(), netcdf4.Dataset(filepath, "r") as ncfile:
        ...     print_vector(ncfile["hland_96_factor_contriarea"][:, 0, 0])
        0.496003, 0.495664, 0.495398, 0.495298

        If we try to write the output of a simulation run beyond the original
        initial initialisation period into the same files,
        |NetCDFInterfaceJIT.provide_jitaccess| raises an equal error as above:

        >>> with TestIO():
        ...     pub.timegrids = "1996-01-05", "1996-01-10", "1d"
        ...     hp.prepare_inputseries(allocate_ram=True, read_jit=False)
        ...     hp.prepare_factorseries(allocate_ram=True, write_jit=True)
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
The data of the NetCDF `...hland_96_factor_tc.nc` (Timegrid("1996-01-01 00:00:00", \
"1996-01-05 00:00:00", "1d")) does not correctly cover the current simulation period \
(Timegrid("1996-01-05 00:00:00", "1996-01-10 00:00:00", "1d")).

        >>> hp.prepare_factorseries(allocate_ram=False, write_jit=False)

        Regarding the spatial dimension, things are similar.  You can write data for
        different sequences in subsequent simulation runs, but you need to ensure all
        required data columns are available right from the start.  Hence, relying on
        the automatic file generation of |NetCDFInterfaceJIT.provide_jitaccess| fails
        in the following example:

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
No data for (sub)device `land_lahn_kalk_0` is available in NetCDF \
file `...hland_96_flux_pc.nc`.

        Of course, one way to prepare complete HydPy-compatible NetCDF files is to let
        HydPy do it:

        >>> with TestIO(), pub.sequencemanager.filetype("nc"):
        ...     hp.prepare_fluxseries(allocate_ram=False, write_jit=False)
        ...     hp.prepare_fluxseries(allocate_ram=True, write_jit=False)
        ...     hp.save_fluxseries()
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for element in hp.elements.search_keywords("catchment"):
        ...     print_vector(element.model.sequences.fluxes.qt.series)
        11.757526, 8.865079, 7.101815, 5.994195
        11.672862, 10.100089, 8.984317, 8.202706
        20.588949, 8.644722, 7.265526, 6.385012
        9.64767, 8.513649, 7.777628, 7.343314
        >>> filepath_qt = "HydPy-H-Lahn/series/default/hland_96_flux_qt.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath_qt, "r") as ncfile:
        ...     for jdx in range(4):
        ...         print_vector(ncfile["hland_96_flux_qt"][:, jdx])
        11.757526, 8.865079, 7.101815, 5.994195
        0.0, 0.0, 0.0, 0.0
        0.0, 0.0, 0.0, 0.0
        9.64767, 8.513649, 7.777628, 7.343314
        >>> with TestIO():
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=False)
        ...     nonheadwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> with TestIO(), netcdf4.Dataset(filepath_qt, "r") as ncfile:  #
        ...         for jdx in range(4):
        ...             print_vector(ncfile["hland_96_flux_qt"][:, jdx])
        11.757526, 8.865079, 7.101815, 5.994195
        11.672862, 10.100089, 8.984317, 8.202706
        20.588949, 8.644722, 7.265526, 6.385012
        9.64767, 8.513649, 7.777628, 7.343314

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
        ...     print_vector(node.sequences.sim.series)
        11.757526, 8.865079, 7.101815, 5.994195
        54.019337, 37.257561, 31.865308, 28.359542
        42.346475, 27.157472, 22.88099, 20.156836
        9.64767, 8.513649, 7.777628, 7.343314
        >>> for node in hp.nodes:
        ...     print_vector(node.sequences.obs.series)
        11.757526, 8.865079, 7.101815, 5.994195
        54.019337, 37.257561, 31.865308, 28.359542
        42.346475, 27.157472, 22.88099, 20.156836
        9.64767, 8.513649, 7.777628, 7.343314
        >>> filepath_sim = "HydPy-H-Lahn/series/default/sim_q.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath_sim, "r") as ncfile:
        ...     for jdx in range(4):
        ...         print_vector(ncfile["sim_q"][:, jdx])
        11.757526, 8.865079, 7.101815, 5.994195
        9.64767, 8.513649, 7.777628, 7.343314
        42.346475, 27.157472, 22.88099, 20.156836
        54.019337, 37.257561, 31.865308, 28.359542
        >>> filepath_obs = "HydPy-H-Lahn/series/default/obs_q.nc"
        >>> from hydpy.core.netcdftools import query_timegrid
        >>> with TestIO(), netcdf4.Dataset(filepath_obs, "r") as ncfile:
        ...     tg = query_timegrid(ncfile, hp.nodes.dill_assl.sequences.obs)
        ...     i0 = tg[pub.timegrids.sim.firstdate]
        ...     i1 = tg[pub.timegrids.sim.lastdate]
        ...     for jdx in range(4):
        ...         print_vector(ncfile["obs_q"][i0:i1, jdx])
        9.64767, 8.513649, 7.777628, 7.343314
        11.757526, 8.865079, 7.101815, 5.994195
        42.346475, 27.157472, 22.88099, 20.156836
        54.019337, 37.257561, 31.865308, 28.359542

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
        ...     print_vector(node.sequences.sim.series)
        0.0, 0.0, 0.0, 0.0
        42.261811, 18.744811, 16.249844, 14.587718
        30.588949, 8.644722, 7.265526, 6.385012
        0.0, 0.0, 0.0, 0.0

        Finally, we set the |Node.deploymode| of the headwater nodes `dill_assl` and
        `lahn_marb` to `oldsim` and `obs`, respectively, and read their previously
        written time series "just in time".  As expected, the values of the two
        non-headwater nodes are identical to those of our initial example:

        >>> with TestIO():
        ...     hp.nodes["dill_assl"].prepare_simseries(allocate_ram=True,
        ...                                             read_jit=True)
        ...     hp.nodes["dill_assl"].deploymode = "oldsim"
        ...     hp.nodes["lahn_marb"].prepare_obsseries(allocate_ram=True,
        ...                                             read_jit=True)
        ...     hp.nodes["lahn_marb"].deploymode = "obs"
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for node in hp.nodes:
        ...     print_vector(node.sequences.sim.series)
        11.757526, 8.865079, 7.101815, 5.994195
        54.019337, 37.257561, 31.865308, 28.359542
        42.346475, 27.157472, 22.88099, 20.156836
        0.0, 0.0, 0.0, 0.0
        """

        readers: list[JITAccessInfo] = []
        writers: list[JITAccessInfo] = []
        variable2readmode: dict[FlatUnion, bool] = {}
        variable2ncfile: dict[FlatUnion, netcdf4.Dataset] = {}
        variable2infos: dict[FlatUnion, list[JITAccessInfo]] = {}
        variable2sequences: collections.defaultdict[
            FlatUnion, list[sequencetools.IOSequence]
        ] = collections.defaultdict(list)
        disabled: dict[sequencetools.IOSequence, sequencetools.SeriesMode] = {}

        try:  # pylint: disable=too-many-nested-blocks

            # just-in-time calculations only work with NetCDF files
            with hydpy.pub.sequencemanager.filetype("nc"):

                # collect the relevant sequences:
                log = self.log
                for sequence in self._yield_disksequences(deviceorder):
                    if sequence.diskflag:
                        variable = log(sequence)
                        readmode = sequence.diskflag_reading
                        variable2readmode.setdefault(variable, readmode)
                        if variable2readmode[variable] != readmode:
                            raise RuntimeError(
                                f"For a specific NetCDF file, you can either read or "
                                f"write data during a simulation run but for file "
                                f"`{variable.filepath}` both is requested."
                            )
                        variable2infos[variable] = readers if readmode else writers
                        variable2sequences[variable].append(sequence)

                if variable2sequences:
                    # prepare NetCDF files:
                    variable2timedelta: dict[FlatUnion, int] = {}
                    tg_init = hydpy.pub.timegrids.init
                    tg_sim = hydpy.pub.timegrids.sim
                    for variable in tuple(variable2readmode):
                        filepath = variable.filepath
                        if not os.path.exists(filepath):
                            if isinstance(variable, NetCDFVariableFlatReader):
                                if hydpy.pub.options.checkseries:
                                    raise FileNotFoundError(
                                        f"No file `{filepath}` available for reading."
                                    )
                                del variable2readmode[variable]
                                del variable2infos[variable]
                                if sequences := variable2sequences.pop(variable):
                                    for sequence in sequences:
                                        sequence.prepare_series(read_jit=False)
                                        disabled[sequence] = sequence.seriesmode
                                continue
                            variable.write()
                        ncfile = netcdf4.Dataset(filepath, "r+")
                        variable2ncfile[variable] = ncfile
                        sequence = variable2sequences[variable][0]
                        tg_variable = query_timegrid(ncfile, sequence)
                        if tg_sim not in tg_variable:
                            raise RuntimeError(
                                f"The data of the NetCDF `{filepath}` ({tg_variable}) "
                                f"does not correctly cover the current simulation "
                                f"period ({tg_sim})."
                            )
                        variable2timedelta[variable] = tg_variable[tg_init.firstdate]

                    # make information for reading and writing temporarily available:
                    for variable, sequences in variable2sequences.items():
                        ncfile = variable2ncfile[variable]
                        assert ncfile is not None
                        get = variable.query_subdevice2index(ncfile).get_index
                        data: NDArrayFloat
                        data = numpy.full(
                            variable.shape[1], numpy.nan, dtype=config.NP_FLOAT
                        )
                        variable2infos[variable].append(
                            JITAccessInfo(
                                ncvariable=(ncvariable := ncfile[variable.name]),
                                realisation=_is_realisation(ncvariable, ncfile),
                                timedelta=variable2timedelta[variable],
                                columns=tuple(get(n) for n in variable.subdevicenames),
                                data=data,
                            )
                        )
                        # the following algorithm relies on the iteration order defined
                        # by method _yield_disksequences:
                        i0, delta, descr_old = 0, 0, ""
                        for sequence in sequences:
                            if (descr_new := sequence.descr_device) != descr_old:
                                descr_old = descr_new
                                i0 += delta
                                delta = int(numpy.prod(sequence.shape))
                            sequence.connect_netcdf(ncarray=data[i0 : i0 + delta])

                    yield JITAccessHandler(
                        readers=tuple(readers), writers=tuple(writers)
                    )

                else:
                    # return without useless efforts:
                    yield JITAccessHandler(readers=(), writers=())

        except BaseException:
            objecttools.augment_excmessage(
                "While trying to prepare NetCDF files for reading or writing data "
                '"just in time" during the current simulation run'
            )
        finally:
            for sequence, seriesmode in disabled.items():
                sequence.seriesmode = seriesmode
            for ncfile in variable2ncfile.values():
                ncfile.close()


def add_netcdfreading(wrapped: Callable[P, None]) -> Callable[P, None]:
    """Enable a function or method that can read time series from NetCDF files to
    automatically activate the |SequenceManager.netcdfreading| mode if not already
    done."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        sm = hydpy.pub.sequencemanager
        if sm._netcdfreader is None:  # pylint: disable=protected-access
            with sm.netcdfreading():
                wrapped(*args, **kwargs)
        else:
            wrapped(*args, **kwargs)

    functools.update_wrapper(wrapper=wrapper, wrapped=wrapped)
    return wrapper


def add_netcdfwriting(wrapped: Callable[P, None]) -> Callable[P, None]:
    """Enable a function or method that can write time series to NetCDF files to
    automatically activate the |SequenceManager.netcdfwriting| mode if not already
    done."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        sm = hydpy.pub.sequencemanager
        if sm._netcdfwriter is None:  # pylint: disable=protected-access
            with sm.netcdfwriting():
                wrapped(*args, **kwargs)
        else:
            wrapped(*args, **kwargs)

    functools.update_wrapper(wrapper=wrapper, wrapped=wrapped)
    return wrapper
