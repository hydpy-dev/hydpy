# -*- coding: utf-8 -*-
"""
This module extends the features of module |filetools| for loading data from and
storing data to netCDF4 files, consistent with the `NetCDF Climate and Forecast (CF)
Metadata Conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/
cf-conventions.html>`_.

.. _`Delft-FEWS`: https://oss.deltares.nl/web/delft-fews

Usually, we apply the features implemented in this module only indirectly by using
the context managers |SequenceManager.netcdfreading| and
|SequenceManager.netcdfwriting|.  However, here we try to be a little more explicit by
using their underlying methods.  Therefore, we need to follow three steps:

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

(1) We prepare a |NetCDFInterface| object for writing data by calling the method
|SequenceManager.open_netcdfwriter|:

>>> from hydpy import pub
>>> pub.sequencemanager.open_netcdfwriter()

(2) We tell the |SequenceManager| to write all the time-series data to NetCDF files:

>>> pub.sequencemanager.filetype = "nc"

(3) We store all the time-series handled by the |Node| and |Element| objects of the
example dataset by calling |Nodes.save_allseries| of class |Nodes| and
|Elements.save_allseries| of class |Elements|.  (In real cases, you would not write the
`with TestIO():` line.  This code block makes sure we pollute the IO testing directory
instead of our current working directory):

>>> from hydpy import TestIO
>>> with TestIO():
...     nodes.save_allseries()
...     elements.save_allseries()

(4) We again log all sequences, but after telling the |SequenceManager| to average each
time series spatially:

>>> with TestIO(), pub.sequencemanager.aggregation("mean"):
...     nodes.save_allseries()
...     elements.save_allseries()

(5) We can now navigate into the details of the logged time series data via the
|NetCDFInterface| object and its subobjects.  For example, we can query the logged flux
sequence objects of type |lland_fluxes.NKor| belonging to application model |lland_v1|
(those of elements `element1` and `element2`; the trailing numbers are the indices of
the relevant hydrological response units):


>>> writer = pub.sequencemanager.netcdfwriter
>>> writer.lland_v1_flux_nkor.subdevicenames
('element1_0', 'element2_0', 'element2_1')

(6) In the example discussed here, all sequences belong to the same folder (`default`).
Storing sequences in separate folders goes hand in hand with storing them in separate
NetCDF files.  In such cases, you must include the folder in the attribute name:

>>> writer.foldernames
('default',)
>>> writer.default_lland_v1_flux_nkor.subdevicenames
('element1_0', 'element2_0', 'element2_1')

(7) We close the |NetCDFInterface| object, which is the moment where the writing
process happens.  After that, the interface object is not available anymore:

>>> from hydpy import TestIO
>>> with TestIO():
...     pub.sequencemanager.close_netcdfwriter()
>>> pub.sequencemanager.netcdfwriter
Traceback (most recent call last):
...
hydpy.core.exceptiontools.AttributeNotReady: The sequence file manager does currently \
handle no NetCDF writer object.

(8) We set the time series values of two test sequences to zero to demonstrate that
reading the data back in actually works:

>>> nodes.node2.sequences.sim.series = 0.0
>>> elements.element2.model.sequences.fluxes.nkor.series = 0.0

(9) We move up a gear and and prepare a |NetCDFInterface| object for reading data, log
all |NodeSequence| and |ModelSequence| objects, and read their time series data from
the created NetCDF file.  We temporarily disable the |Options.checkseries| option to
prevent raising an exception when reading incomplete data from the files:

>>> with TestIO(), pub.options.checkseries(False):
...     pub.sequencemanager.open_netcdfreader()
...     nodes.load_simseries()
...     elements.load_allseries()
...     pub.sequencemanager.close_netcdfreader()

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
>>> filepath = "project/series/default/node_sim_q_mean.nc"
>>> with TestIO(), netcdf4.Dataset(filepath) as ncfile:
...     array(ncfile["sim_q"][:])
array([[60.],
       [61.],
       [62.],
       [63.]])

>>> filepath = "project/series/default/lland_v1_flux_nkor_mean.nc"
>>> with TestIO(), netcdf4.Dataset(filepath) as ncfile:
...         array(ncfile["flux_nkor"][:])[:, 1]
array([16.5, 18.5, 20.5, 22.5])

Besides the testing-related specialities, the described workflow is more or less
standard but allows for different modifications.  We illustrate them in the
documentation of the other features implemented in module |netcdftools| but also the
documentation on class |SequenceManager| of module |filetools| and class |IOSequence|
of module |sequencetools|.

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
import time
import warnings
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


def query_timegrid(
    ncfile: netcdf4.Dataset, sequence: sequencetools.IOSequence
) -> timetools.Timegrid:
    """Return the |Timegrid| defined by the given NetCDF file.

    |query_timegrid| relies on the `timereference` attribute of the given NetCDF file,
    if available, and falls back to the global |Options.timestampleft| option when
    necessary.  The NetCDF files of the `LahnH` example project (and all other NetCDF
    files written by *HydPy*) include such information:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from netCDF4 import Dataset
    >>> filepath = "LahnH/series/default/hland_v1_input_p.nc"
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     ncfile.timereference
    'left interval boundary'

    We start our examples considering the input sequence |hland_inputs.P|, which
    handles precipitation sums.  |query_timegrid| requires an instance of
    |hland_inputs.P| to determine that each value of the time series of the NetCDF file
    references a time interval and not a time point:

    >>> p = hp.elements.land_dill.model.sequences.inputs.p

    If the file-specific setting does not collide with the current value of
    |Options.timestampleft|, |query_timegrid| works silently:

    >>> from hydpy.core.netcdftools import query_timegrid
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)
    Timegrid("1996-01-01 00:00:00",
             "2007-01-01 00:00:00",
             "1d")

    If a file-specific setting is missing, |query_timegrid| applies the current
    |Options.timestampleft| value:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     del ncfile.timereference
    >>> from hydpy.core.testtools import warn_later
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)
    Timegrid("1996-01-01 00:00:00",
             "2007-01-01 00:00:00",
             "1d")

    >>> with TestIO(), Dataset(filepath) as ncfile, pub.options.timestampleft(False):
    ...     query_timegrid(ncfile, p)
    Timegrid("1995-12-31 00:00:00",
             "2006-12-31 00:00:00",
             "1d")

    If the file-specific setting and |Options.timestampleft| conflict, |query_timegrid|
    favours the file attribute and warns about this assumption:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "right interval boundary"
    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)  # doctest: +ELLIPSIS
    Timegrid("1995-12-31 00:00:00",
             "2006-12-31 00:00:00",
             "1d")
    UserWarning: The `timereference` attribute (`right interval boundary`) of the \
NetCDF file `...hland_v1_input_p.nc` conflicts with the current value of the global \
`timestampleft` option (`True`).  The file-specific information is prioritised.

    State sequences like |hland_states.SM| handle data for specific time points instead
    of time intervals.  Their |IOSequence.series| vector contains the calculated values
    for the end of each simulation step.  Hence, without file-specific information,
    |query_timegrid| ignores the |Options.timestampleft| option and follows the `right
    interval boundary` convention:

    >>> sm = hp.elements.land_dill.model.sequences.states.sm
    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     del ncfile.timereference
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)
    Timegrid("1995-12-31 00:00:00",
             "2006-12-31 00:00:00",
             "1d")

    Add a `timereference` attribute with the value `current time` to explicitly include
    this information in a NetCDF file:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "current time"
    >>> with TestIO(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)
    Timegrid("1995-12-31 00:00:00",
             "2006-12-31 00:00:00",
             "1d")

    |query_timegrid| raises special warnings when a NetCDF file's `timereference`
    attribute conflicts with its judgement whether the contained data addresses time
    intervals or time points:

    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)  # doctest: +ELLIPSIS
    Timegrid("1995-12-31 00:00:00",
             "2006-12-31 00:00:00",
             "1d")
    UserWarning: The `timereference` attribute (`current time`) of the NetCDF file \
`...hland_v1_input_p.nc` conflicts with the type of the relevant sequence (`P`).  The \
file-specific information is prioritised.

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "left interval boundary"
    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)  # doctest: +ELLIPSIS
    Timegrid("1996-01-01 00:00:00",
             "2007-01-01 00:00:00",
             "1d")
    UserWarning: The `timereference` attribute (`left interval boundary`) of the \
NetCDF file `...hland_v1_input_p.nc` conflicts with the type of the relevant sequence \
(`SM`).  The file-specific information is prioritised.

    |query_timegrid| also raises specific warnings for misstated `timereference`
    attributes describing the different fallbacks for data related to time intervals
    and time points:

    >>> with TestIO(), Dataset(filepath, "r+") as ncfile:
    ...     ncfile.timereference = "wrong"
    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, p)  # doctest: +ELLIPSIS
    Timegrid("1996-01-01 00:00:00",
             "2007-01-01 00:00:00",
             "1d")
    UserWarning: The value of the `timereference` attribute (`wrong`) of the NetCDF \
file `...hland_v1_input_p.nc` is not among the accepted values (`left...`, \
`right...`, `current...`).  Assuming `left interval boundary` according to the \
current value of the global `timestampleft` option.

    >>> with TestIO(), warn_later(), Dataset(filepath) as ncfile:
    ...     query_timegrid(ncfile, sm)  # doctest: +ELLIPSIS
    Timegrid("1995-12-31 00:00:00",
             "2006-12-31 00:00:00",
             "1d")
    UserWarning: The value of the `timereference` attribute (`wrong`) of the NetCDF \
file `...hland_v1_input_p.nc` is not among the accepted values (`left...`, \
`right...`, `current...`).  Assuming `current time` according to the type of the \
relevant sequence (`SM`).
    """
    currenttime = _timereference_currenttime(sequence)
    opts = hydpy.pub.options
    ref: Optional[str] = getattr(ncfile, "timereference", None)
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
        left = opts.timestampleft
        text = "left" if left else "right"
        warnings.warn(
            f"The value of the `timereference` attribute (`{ncfile.timereference}`) "
            f"of the NetCDF file `{ncfile.filepath()}` is not among the accepted "
            f"values (`left...`, `right...`, `current...`).  Assuming `{text} "
            f"interval boundary` according to the current value of the global "
            f"`timestampleft` option."
        )
    with opts.timestampleft(left):
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

    >>> from hydpy import TestIO
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
    >>> query_variable(ncfile, "var")[:].data
    array([[-999., -999., -999.],
           [-999., -999., -999.]])
    >>> query_array(ncfile, "var")
    array([[nan, nan, nan],
           [nan, nan, nan]])
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
    >>> query_array(ncfile, "var")
    array([[1.1, 1.2, 1.3],
           [2.1, 2.2, 2.3]])
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
    ...         query_array(ncfile, "var")
    array([[nan, nan, nan],
           [nan, nan, nan]])
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
    """Variable for the direct access to the relevant section of the NetCDF file."""
    realisation: bool
    """Flag that indicates if the relevant |JITAccessInfo.ncvariable| comes with an
    additional `realization` dimension (explained in the documentation on function
    |query_array|)"""
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
            jdx = idx + reader.timedelta
            if reader.realisation:
                reader.data[:] = reader.ncvariable[jdx, 0, reader.columns]
            else:
                reader.data[:] = reader.ncvariable[jdx, reader.columns]

    def write_slices(self, idx: int) -> None:
        """Write the time slice relevant for the current simulation step from each
        NetCDF file selected for writing."""
        for writer in self.writers:
            jdx = idx + writer.timedelta
            if writer.realisation:
                writer.ncvariable[jdx, 0, writer.columns] = writer.data
            else:
                writer.ncvariable[jdx, writer.columns] = writer.data


class NetCDFInterface:
    """Interface between |SequenceManager| and multiple NetCDF files.

    The core task of class |NetCDFInterface| is to distribute different |IOSequence|
    objects on multiple instances of class |NetCDFVariableBase|.

    (1) We prepare a |SequenceManager| object and some devices handling different
    sequences by applying function |prepare_io_example_1|:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    (2) We collect all sequences used in the following examples except
    |lland_fluxes.NKor| of element `element1`, which we reserve for special tests:

    >>> sequences = []
    >>> for node in nodes:
    ...     sequences.append(node.sequences.sim)
    >>> for element in elements:
    ...     if element.model.name == "hland_v1":
    ...         sequences.append(element.model.sequences.states.sp)
    ...     else:
    ...         sequences.append(element.model.sequences.inputs.nied)
    ...         if element.name != "element1":
    ...             sequences.append(element.model.sequences.fluxes.nkor)

    (3) We prepare a |NetCDFInterface| object and log and write all test sequences
    except |lland_fluxes.NKor| of element `element1`.  |NetCDFInterface| initialises
    one |NetCDFVariableFlat| and one |NetCDFVariableAgg| object for each |IOSequence|
    subtype:

    >>> from hydpy.core.netcdftools import NetCDFInterface
    >>> interface = NetCDFInterface()
    >>> len(interface)
    0

    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     for sequence in sequences:
    ...         _ = interface.log(sequence, sequence.series)
    ...         _ = interface.log(sequence, sequence.average_series())
    >>> len(interface)
    14

    We change the relevant directory before logging the reserved sequence.
    |NetCDFInterface| initialises two new |NetCDFVariableBase| objects, despite other
    |NetCDFVariableBase| objects related to the same sequence type being already
    available:

    >>> nkor = elements.element1.model.sequences.fluxes.nkor
    >>> with TestIO():
    ...     pub.sequencemanager.currentdir = "test"
    ...     _ = interface.log(nkor, nkor.series)
    ...     _ = interface.log(nkor, nkor.average_series())
    >>> len(interface)
    16

    You can query all relevant folder names, filenames and variable names via
    properties |NetCDFInterface.foldernames|, |NetCDFInterface.filenames|, and
    |NetCDFInterface.variablenames|:

    >>> from hydpy import print_values
    >>> print_values(interface.foldernames)
    default, test
    >>> print_values(interface.filenames)
    hland_v1_state_sp, hland_v1_state_sp_mean, lland_v1_flux_nkor,
    lland_v1_flux_nkor_mean, lland_v1_input_nied,
    lland_v1_input_nied_mean, lland_v2_flux_nkor, lland_v2_flux_nkor_mean,
    lland_v2_input_nied, lland_v2_input_nied_mean, node_sim_q,
    node_sim_q_mean, node_sim_t, node_sim_t_mean
    >>> interface.variablenames
    ('flux_nkor', 'input_nied', 'sim_q', 'sim_t', 'state_sp')

    |NetCDFInterface| provides attribute access to its |NetCDFVariableBase| instances,
    both via their filenames and the combination of its folder names and filenames:

    >>> interface.node_sim_q is interface.default_node_sim_q
    True
    >>> print_values(sorted(set(dir(interface)) - set(object.__dir__(interface))))
    default_hland_v1_state_sp, default_hland_v1_state_sp_mean,
    default_lland_v1_flux_nkor, default_lland_v1_flux_nkor_mean,
    default_lland_v1_input_nied, default_lland_v1_input_nied_mean,
    default_lland_v2_flux_nkor, default_lland_v2_flux_nkor_mean,
    default_lland_v2_input_nied, default_lland_v2_input_nied_mean,
    default_node_sim_q, default_node_sim_q_mean, default_node_sim_t,
    default_node_sim_t_mean, hland_v1_state_sp, hland_v1_state_sp_mean,
    lland_v1_input_nied, lland_v1_input_nied_mean, lland_v2_flux_nkor,
    lland_v2_flux_nkor_mean, lland_v2_input_nied,
    lland_v2_input_nied_mean, node_sim_q, node_sim_q_mean, node_sim_t,
    node_sim_t_mean, test_lland_v1_flux_nkor, test_lland_v1_flux_nkor_mean

    If multiple NetCDF files have the same name, you must prefix the relevant folder
    name:

    >>> interface.lland_v1_flux_nkor
    Traceback (most recent call last):
    ...
    AttributeError: The current NetCDFInterface object handles multiple NetCDF files \
named `lland_v1_flux_nkor`.  Please be more specific.
    >>> hasattr(interface, "default_lland_v1_flux_nkor")
    True

    |NetCDFInterface| raises the following error for completely wrong attribute names:

    >>> interface.lland_v1
    Traceback (most recent call last):
    ...
    AttributeError: The current NetCDFInterface object neither handles a NetCDF file \
named `lland_v1` nor does it define a member named `lland_v1`.

    (4) We write all NetCDF files into the `default` folder of the testing directory,
    defined by |prepare_io_example_1|:

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
    >>> nkor.prepare_series(allocate_ram=False)
    >>> nkor.prepare_series(allocate_ram=True)

    (6) We again initialise class |NetCDFInterface|, log all test sequences, and read
    the test data of the defined subperiod:

    >>> interface = NetCDFInterface()
    >>> with TestIO():
    ...     _ = interface.log(nkor, nkor.series)
    ...     pub.sequencemanager.currentdir = "default"
    ...     for sequence in sequences:
    ...         _ = interface.log(sequence, None)
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
    """

    _dir2file2var: Dict[str, Dict[str, NetCDFVariable]]

    def __init__(self) -> None:
        self._dir2file2var = {}

    def log(
        self,
        sequence: sequencetools.IOSequence,
        infoarray: Optional[sequencetools.InfoArray] = None,
    ) -> NetCDFVariable:
        """Prepare a |NetCDFVariableBase| object suitable for the given |IOSequence|
        object, when necessary, and pass the given arguments to its
        |NetCDFVariableBase.log| method."""
        dirpath = sequence.dirpath
        try:
            file2var = self._dir2file2var[dirpath]
        except KeyError:
            file2var = {}
            self._dir2file2var[dirpath] = file2var
        filename = self._query_filename(sequence, infoarray)
        try:
            variable = file2var[filename]
        except KeyError:
            aggregation = self._query_aggregation(infoarray)
            cls: Type[NetCDFVariable]
            cls = NetCDFVariableFlat if (aggregation is None) else NetCDFVariableAgg
            filepath = f"{os.path.join(dirpath, filename)}.nc"
            variable = cls(name=sequence.descr_sequence, filepath=filepath)
            file2var[filename] = variable
        variable.log(sequence, infoarray)
        return variable

    def _query_filename(
        self,
        sequence: sequencetools.IOSequence,
        infoarray: Optional[sequencetools.InfoArray],
    ) -> str:
        if isinstance(sequence, sequencetools.ModelSequence):
            filename = sequence.descr_model
        else:
            filename = "node"
        filename = f"{filename}_{sequence.descr_sequence}"
        aggregation = self._query_aggregation(infoarray)
        if aggregation:
            filename = f"{filename}_{aggregation}"
        return filename

    @staticmethod
    def _query_aggregation(
        infoarray: Optional[sequencetools.InfoArray],
    ) -> Optional[str]:
        if (infoarray is not None) and (infoarray.aggregation != "unmodified"):
            return infoarray.aggregation
        return None

    def read(self) -> None:
        """Call method |NetCDFVariableBase.read| of all handled |NetCDFVariableBase|
        objects."""
        for variable in self:
            variable.read()

    def write(self) -> None:
        """Call method |NetCDFVariableBase.write| of all handled |NetCDFVariableBase|
        objects."""
        for variable in self:
            variable.write()

    @staticmethod
    def _yield_disksequences(
        deviceorder: Iterable[Union[devicetools.Node, devicetools.Element]]
    ) -> Iterator[sequencetools.IOSequence]:
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
        give some additional insights into the options and limitations of the related
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
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
For a specific NetCDF file, you can either read or write data during a simulation run \
but for file `...hland_v1_input_p.nc` both is requested.

        Clearly, each NetCDF file we want to read data from needs to span the current
        simulation period:

        >>> with TestIO():
        ...     pub.timegrids.init.firstdate = "1990-01-01"
        ...     pub.timegrids.sim.firstdate = "1995-01-01"
        ...     hp.prepare_inputseries(allocate_ram=False, read_jit=True)
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
The data of the NetCDF `...hland_v1_input_p.nc` \
(Timegrid("1996-01-01 00:00:00", "2007-01-01 00:00:00", "1d")) does not correctly \
cover the current simulation period \
(Timegrid("1995-01-01 00:00:00", "1996-01-05 00:00:00", "1d")).

        However, each NetCDF file selected for writing must also cover the complete
        initialisation period.  If there is no adequately named NetCDF file,
        |NetCDFInterface.provide_jitaccess| creates a new one for the current
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
        >>> filepath = "LahnH/series/default/hland_v1_factor_tmean.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath, "r") as ncfile:
        ...     print_values(ncfile["factor_tmean"][:, 0])
        -0.572053, -1.084746, -2.767055, -6.242055

        Under particular circumstances, the data variable of a NetCDF file can be
        3-dimensional.  The documentation on function |query_array| explains this in
        detail.  The following example demonstrates that reading and writing such
        3-dimensional variables "just in time" works correctly.  Therefore, we add a
        `realization` dimension to the input file `hland_v1_input_t.nc` (part of the
        example project data) and the output file `hland_v1_factor_tmean.nc` (written
        in the previous example) and use them for redefining their data variables with
        this additional dimension.  As expected, the results are the same as in the
        previous example:

        >>> with TestIO():
        ...     for name in ("input_t", "factor_tmean"):
        ...         filepath = f"LahnH/series/default/hland_v1_{name}.nc"
        ...         with netcdf4.Dataset(filepath, "r+") as ncfile:
        ...             ncfile.renameVariable(name, "old")
        ...             _ = ncfile.createDimension("realization", 1)
        ...             var = ncfile.createVariable(
        ...                 name, "f8", dimensions=("time", "realization", "stations"))
        ...             var[:] = ncfile["old"][:] if name == "input_t" else -999.0
        ...     pub.timegrids = "1996-01-01", "1996-01-05", "1d"
        ...     hp.simulate()
        >>> with TestIO(), netcdf4.Dataset(filepath, "r") as ncfile:
        ...     print_values(ncfile["factor_tmean"][:, 0, 0])
        -0.572053, -1.084746, -2.767055, -6.242055

        If we try to write the output of a simulation run beyond the original
        initial initialisation period into the same files,
        |NetCDFInterface.provide_jitaccess| raises an equal error as above:

        >>> with TestIO():
        ...     pub.timegrids = "1996-01-05", "1996-01-10", "1d"
        ...     hp.prepare_inputseries(allocate_ram=True, read_jit=False)
        ...     hp.prepare_factorseries(allocate_ram=True, write_jit=True)
        ...     hp.simulate()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to prepare NetCDF files for reading or writing \
data "just in time" during the current simulation run, the following error occurred: \
The data of the NetCDF `...hland_v1_factor_tmean.nc` \
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
        with an ordinary NetCDF writer object via |SequenceManager.netcdfwriting|:

        >>> with TestIO(), pub.sequencemanager.filetype("nc"):
        ...     hp.prepare_fluxseries(allocate_ram=False, write_jit=False)
        ...     hp.prepare_fluxseries(allocate_ram=True, write_jit=False)
        ...     with pub.sequencemanager.netcdfwriting():
        ...         hp.save_fluxseries()
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> for element in hp.elements.search_keywords("catchment"):
        ...     print_values(element.model.sequences.fluxes.qt.series)
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        20.58932, 8.66144, 7.281198, 6.402232
        11.674045, 10.110371, 8.991987, 8.212314
        >>> filepath_qt = "LahnH/series/default/hland_v1_flux_qt.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath_qt, "r") as ncfile:
        ...     for jdx in range(4):
        ...         print_values(ncfile["flux_qt"][:, jdx])
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        0.0, 0.0, 0.0, 0.0
        0.0, 0.0, 0.0, 0.0
        >>> with TestIO():
        ...     headwaters.prepare_fluxseries(allocate_ram=True, write_jit=False)
        ...     nonheadwaters.prepare_fluxseries(allocate_ram=True, write_jit=True)
        ...     hp.load_conditions()
        ...     hp.simulate()
        >>> with TestIO(), netcdf4.Dataset(filepath_qt, "r") as ncfile:  #
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
        >>> filepath_sim = "LahnH/series/default/node_sim_q.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath_sim, "r") as ncfile:
        ...     for jdx in range(4):
        ...         print_values(ncfile["sim_q"][:, jdx])
        11.78038, 8.901179, 7.131072, 6.017787
        9.647824, 8.517795, 7.781311, 7.344944
        42.3697, 27.210443, 22.930066, 20.20133
        54.043745, 37.320814, 31.922053, 28.413644
        >>> filepath_obs = "LahnH/series/default/node_obs_q.nc"
        >>> with TestIO(), netcdf4.Dataset(filepath_obs, "r") as ncfile:
        ...     for jdx in range(4):
        ...         print_values(ncfile["obs_q"][:, jdx])
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
        variable2readmode: Dict[NetCDFVariableFlat, bool] = {}
        variable2ncfile: Dict[NetCDFVariableFlat, netcdf4.Dataset] = {}
        variable2infos: Dict[NetCDFVariableFlat, List[JITAccessInfo]] = {}
        variable2sequences: DefaultDict[
            NetCDFVariableFlat, List[sequencetools.IOSequence]
        ] = collections.defaultdict(lambda: [])

        try:  # pylint: disable=too-many-nested-blocks
            # collect the relevant sequences:
            log = self.log
            for sequence in self._yield_disksequences(deviceorder):
                if sequence.diskflag:
                    variable = log(sequence)
                    assert isinstance(variable, NetCDFVariableFlat)
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
                variable2timedelta: Dict[NetCDFVariable, int] = {}
                tg_init = hydpy.pub.timegrids.init
                tg_sim = hydpy.pub.timegrids.sim
                for variable, readmode in variable2readmode.items():
                    if not os.path.exists(variable.filepath):
                        if readmode and hydpy.pub.options.checkseries:
                            raise FileNotFoundError(
                                f"No file `{variable.filepath}` available for reading."
                            )
                        variable.write()
                    ncfile = netcdf4.Dataset(variable.filepath, "r+")
                    variable2ncfile[variable] = ncfile
                    sequence = variable2sequences[variable][0]
                    tg_variable = query_timegrid(ncfile, sequence)
                    if tg_sim not in tg_variable:
                        raise RuntimeError(
                            f"The data of the NetCDF `{variable.filepath}` "
                            f"({tg_variable}) does not correctly cover the current "
                            f"simulation period ({tg_sim})."
                        )
                    variable2timedelta[variable] = tg_init[tg_variable.firstdate]

                # make information for reading and writing temporarily available:
                for variable, sequences in variable2sequences.items():
                    ncfile = variable2ncfile[variable]
                    assert ncfile is not None
                    get = variable.query_subdevice2index(ncfile).get_index
                    data: NDArrayFloat = numpy.full(
                        variable.shape[1], numpy.nan, dtype=float
                    )
                    variable2infos[variable].append(
                        JITAccessInfo(
                            ncvariable=ncfile[variable.name],
                            realisation=_is_realisation(ncfile[variable.name], ncfile),
                            timedelta=variable2timedelta[variable],
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
            for ncfile in variable2ncfile.values():
                ncfile.close()

    @property
    def foldernames(self) -> Tuple[str, ...]:
        """The names of all folders the sequences shall be read from or written to."""
        return tuple(os.path.split(d)[-1] for d in self._dir2file2var)

    @property
    def filenames(self) -> Tuple[str, ...]:
        """The names of all relevant |NetCDFVariableBase| objects."""
        filenames = (file2var.keys() for file2var in self._dir2file2var.values())
        return tuple(sorted(set(itertools.chain(*filenames))))

    @property
    def variablenames(self) -> Tuple[str, ...]:
        """The names of all handled |NetCDFVariableBase| objects."""
        variables = (file2var.values() for file2var in self._dir2file2var.values())
        return tuple(sorted(set(v.name for v in itertools.chain(*variables))))

    def __getattr__(self, name: str) -> NetCDFVariable:
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
            raise AttributeError(
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

    def __iter__(self) -> Iterator[NetCDFVariable]:
        for file2var in self._dir2file2var.values():
            for var in file2var.values():
                yield var

    def __dir__(self) -> List[str]:
        adds_long = []
        counter: DefaultDict[str, int] = collections.defaultdict(lambda: 0)
        for dirpath, file2var in self._dir2file2var.items():
            dirname = os.path.split(dirpath)[-1]
            for filename in file2var.keys():
                adds_long.append(f"{dirname}_{filename}")
                counter[filename] += 1
        adds_short = [name for name, nmb in counter.items() if nmb == 1]
        return cast(List[str], super().__dir__()) + adds_long + adds_short


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
    """Name of the NetCDF variable within the NetCDF file."""
    filepath: str
    """Path to the relevant NetCDF file."""
    _descr2sequence: Dict[str, sequencetools.IOSequence]
    _descr2array: Dict[str, Optional[sequencetools.InfoArray]]

    def __init__(self, name: str, filepath: str) -> None:
        self.name = name
        self.filepath = filepath
        self._descr2sequence = {}
        self._descr2array = {}

    def log(
        self,
        sequence: sequencetools.IOSequence,
        infoarray: Optional[sequencetools.InfoArray],
    ) -> None:
        """Log the given |IOSequence| object either for reading or writing data.

        When writing data, the second argument should be an |InfoArray|.  When reading
        data, this argument is irrelevant. Pass |None|.

        For writing, the `infoarray` argument allows for passing alternative data that
        replaces the original series of the |IOSequence| object, which helps write
        modified (e.g. spatially averaged) time series.

        The logged time-series data is available via attribute access:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable
        >>> NCVar = make_abc_testable(NetCDFVariableBase)
        >>> ncvar = NCVar("flux_nkor", "filepath.nc")
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
        AttributeError: The NetCDFVariable object `flux_nkor` does neither handle \
time series data under the (sub)device name `element2` nor does it define a member \
named `element2`.
        """
        descr_device = sequence.descr_device
        self._descr2sequence[descr_device] = sequence
        self._descr2array[descr_device] = infoarray

    @property
    @abc.abstractmethod
    def subdevicenames(self) -> Tuple[str, ...]:
        """The names of all relevant (sub)devices."""

    @property
    @abc.abstractmethod
    def array(self) -> NDArrayFloat:
        """A |numpy.ndarray| containing the values of all logged sequences."""

    def insert_subdevices(self, ncfile: netcdf4.Dataset) -> None:
        """Insert a variable of the names of the (sub)devices of the logged sequences
        into the given NetCDF file.

        We prepare a |NetCDFVariableBase| subclass with fixed (sub)device names:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase, chars2str
        >>> from hydpy import make_abc_testable, TestIO
        >>> from hydpy.core.netcdftools import netcdf4
        >>> Var = make_abc_testable(NetCDFVariableBase)
        >>> Var.subdevicenames = "element1", "element_2"

        The first dimension of the added variable corresponds to the number of
        (sub)devices, and the second dimension to the number of characters of the
        longest (sub)device name:

        >>> var = Var("var", "filename.nc")
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("filename.nc", "w")
        >>> var.insert_subdevices(ncfile)
        >>> ncfile["station_id"].dimensions
        ('stations', 'char_leng_name')
        >>> ncfile["station_id"].shape
        (2, 9)
        >>> chars2str(ncfile["station_id"][:])
        ['element1', 'element_2']
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

    def query_subdevices(self, ncfile: netcdf4.Dataset) -> List[str]:
        """Query the names of the (sub)devices of the logged sequences from the given
        NetCDF file.

        We apply the function |NetCDFVariableBase.query_subdevices| on an empty NetCDF
        file.  The error message shows that the method tries to query the (sub)device
        names:

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable, TestIO
        >>> from hydpy.core.netcdftools import netcdf4
        >>> Var = make_abc_testable(NetCDFVariableBase)
        >>> Var.subdevicenames = "element1", "element_2"
        >>> var = Var("flux_prec", "filename.nc")
        >>> with TestIO():
        ...     ncfile = netcdf4.Dataset("filename.nc", "w")
        >>> var.query_subdevices(ncfile)
        Traceback (most recent call last):
        ...
        RuntimeError: NetCDF file `filename.nc` does neither contain a variable named \
`flux_prec_station_id` nor `station_id` for defining the coordinate locations of \
variable `flux_prec`.

        After inserting the (sub)device names, they can be queried and returned:

        >>> var.insert_subdevices(ncfile)
        >>> Var("flux_prec", "filename.nc").query_subdevices(ncfile)
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
        ...     ncfile = netcdf4.Dataset("filename.nc", "w")
        >>> Var = make_abc_testable(NetCDFVariableBase)
        >>> Var.subdevicenames = ["element3", "element1", "element1_1", "element2"]
        >>> var = Var("flux_prec", "filename.nc")
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
NetCDF file `filename.nc` available.

        Additionally, |NetCDFVariableBase.query_subdevice2index| checks for duplicates:

        >>> ncfile["station_id"][:] = str2chars(
        ...     ["element3", "element1", "element1_1", "element1"])
        >>> var.query_subdevice2index(ncfile)
        Traceback (most recent call last):
        ...
        RuntimeError: The NetCDF file `filename.nc` contains duplicate (sub)device \
names for variable `flux_prec` (the first found duplicate is `element1`).

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
    def read(self) -> None:
        """Read the data from a NetCDF file.

        Raise a |RuntimeError| if the relevant |NetCDFVariableBase| subclass does not
        support reading data.
        """

    def write(self) -> None:
        """Write the data to a new NetCDF file.

        See the general documentation on class |NetCDFVariableFlat| for some examples.
        """
        with netcdf4.Dataset(self.filepath, "w") as ncfile:
            now = time.ctime(time.time())
            ncfile.history = f"Created {now} by HydPy {hydpy.__version__}"
            ncfile.Conventions = "CF-1.6"
            init = hydpy.pub.timegrids.init
            timeunit = init.firstdate.to_cfunits("hours")
            opts = hydpy.pub.options
            if _timereference_currenttime(next(iter(self._descr2sequence.values()))):
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

    def __getattr__(self, name: str) -> _NetCDFVariableInfo:
        try:
            return _NetCDFVariableInfo(
                self._descr2sequence[name], self._descr2array[name]
            )
        except KeyError:
            raise AttributeError(
                f"The NetCDFVariable object `{self.name}` does neither handle time "
                f"series data under the (sub)device name `{name}` nor does it define "
                f"a member named `{name}`."
            ) from None

    def __dir__(self) -> List[str]:
        return cast(List[str], super().__dir__()) + list(self._descr2sequence.keys())


class NetCDFVariableAgg(NetCDFVariableBase):
    """Relates objects of a specific |IOSequence| subclass with a single NetCDF
    variable for writing aggregated time series data.

    Essentially, class |NetCDFVariableAgg| is very similar to class |NetCDFVariableFlat|
    but a little bit simpler, as it cannot read data from NetCDF files and always
    writes one column of data for each logged |IOSequence| object.  The following
    examples are a selection of the more thoroughly explained examples of the
    documentation on class |NetCDFVariableFlat|:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3, element4) = prepare_io_example_1()
    >>> from hydpy.core.netcdftools import NetCDFVariableAgg
    >>> var_nied = NetCDFVariableAgg("input_nied_mean", "nied.nc")
    >>> var_nkor = NetCDFVariableAgg("flux_nkor_mean", "nkor.nc")
    >>> var_sp = NetCDFVariableAgg("state_sp_mean", "sp.nc")
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

    As |NetCDFVariableAgg| provides no reading functionality, we show that the
    aggregated values are readily available using the external NetCDF4 library:

    >>> import numpy
    >>> with TestIO(), netcdf4.Dataset("nied.nc", "r") as ncfile:
    ...     numpy.array(ncfile["input_nied_mean"][:])
    array([[0., 4.],
           [1., 5.],
           [2., 6.],
           [3., 7.]])

    >>> with TestIO(), netcdf4.Dataset("nkor.nc", "r") as ncfile:
    ...     numpy.array(ncfile["flux_nkor_mean"][:])
    array([[12. , 16.5],
           [13. , 18.5],
           [14. , 20.5],
           [15. , 22.5]])

    >>> with TestIO(), netcdf4.Dataset("sp.nc", "r") as ncfile:
    ...     numpy.array(ncfile["state_sp_mean"][:])
    array([[70.5],
           [76.5],
           [82.5],
           [88.5]])
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
        >>> ncvar = NetCDFVariableAgg("flux_nkor", "filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (4, 3)

        There is no difference for 2-dimensional sequences as aggregating their time
        series also results in 1-dimensional data:

        >>> ncvar = NetCDFVariableAgg("state_sp", "filename.nc")
        >>> ncvar.log(elements.element4.model.sequences.states.sp, None)
        >>> ncvar.shape
        (4, 1)
        """
        return len(hydpy.pub.timegrids.init), len(self._descr2sequence)

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
        >>> ncvar = NetCDFVariableAgg("flux_nkor", "filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         ncvar.log(nkor, nkor.average_series())
        >>> ncvar.array
        array([[12. , 16.5, 25. ],
               [13. , 18.5, 28. ],
               [14. , 20.5, 31. ],
               [15. , 22.5, 34. ]])

        There is no difference for 2-dimensional sequences as aggregating their time
        series also results in 1-dimensional data:

        >>> ncvar = NetCDFVariableAgg("state_sp", "filename.nc")
        >>> sp = elements.element4.model.sequences.states.sp
        >>> ncvar.log(sp, sp.average_series())
        >>> ncvar.array
        array([[70.5],
               [76.5],
               [82.5],
               [88.5]])
        """
        array = numpy.full(self.shape, fillvalue, dtype=float)
        for idx, subarray in enumerate(self._descr2array.values()):
            if subarray is not None:
                array[:, idx] = subarray
        return array

    @property
    def subdevicenames(self) -> Tuple[str, ...]:
        """The names of all relevant devices."""
        return tuple(self._descr2sequence.keys())

    def read(self) -> None:
        """Raise a |RuntimeError| in any case.

        This method always raises the following exception to tell users why
        implementing a reading functionality is not possible:

        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> NetCDFVariableAgg("flux_nkor", "filename.nc").read()
        Traceback (most recent call last):
        ...
        RuntimeError: The process of aggregating values (of sequence `flux_nkor` and \
other sequences as well) is not invertible.
        """
        raise RuntimeError(
            f"The process of aggregating values (of sequence `{self.name}` and other "
            f"sequences as well) is not invertible."
        )


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
    >>> var_nied = NetCDFVariableFlat("input_nied", "nied.nc")
    >>> var_nkor = NetCDFVariableFlat("flux_nkor", "nkor.nc")
    >>> var_sp = NetCDFVariableFlat("state_sp", "sp.nc")
    >>> for element in (element1, element2):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)
    >>> sp = element4.model.sequences.states.sp
    >>> var_sp.log(sp, sp.series)

    (3) We write the data of all logged sequences to separate NetCDF files:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     var_nied.write()
    ...     var_nkor.write()
    ...     var_sp.write()

    (4) We set all values of the selected sequences to -777 and check that they are
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

    (5) Again, we prepare three |NetCDFVariableFlat| instances and log the same
    sequences as above, open the existing NetCDF file for reading, read its data, and
    confirm that it has been correctly passed to the test sequences:

    >>> nied1 = NetCDFVariableFlat("input_nied", "nied.nc")
    >>> nkor1 = NetCDFVariableFlat("flux_nkor", "nkor.nc")
    >>> sp4 = NetCDFVariableFlat("state_sp", "sp.nc")
    >>> for element in (element1, element2):
    ...     sequences = element.model.sequences
    ...     nied1.log(sequences.inputs.nied, None)
    ...     nkor1.log(sequences.fluxes.nkor, None)
    >>> sp4.log(sp, None)
    >>> with TestIO():
    ...     nied1.read()
    ...     nkor1.read()
    ...     sp4.read()
    >>> for seq in (seq1, seq2, seq3):
    ...     print(numpy.all(seq.series == seq.testarray))
    True
    True
    True

    (6) Trying to read data not stored properly results in error messages like the
    following:

    >>> nied1.log(element3.model.sequences.inputs.nied, None)
    >>> with TestIO():
    ...     nied1.read()
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to read data from NetCDF file `nied.nc`, the following \
error occurred: No data for sequence `input_nied` and (sub)device `element3` in \
NetCDF file `nied.nc` available.
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
        >>> ncvar = NetCDFVariableFlat("input_nied", "filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         ncvar.log(element.model.sequences.inputs.nied, None)
        >>> ncvar.shape
        (4, 3)

        For 1-dimensional sequences as |lland_fluxes.NKor|, the second axis corresponds
        to "subdevices".  Here, these "subdevices" are hydrological response units of
        different elements.  The model instances of the three elements define one, two,
        and three response units, respectively, making up a sum of six subdevices:

        >>> ncvar = NetCDFVariableFlat("flux_nkor", "filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (4, 6)

        The above assertions also hold for 2-dimensional sequences like
        |hland_states.SP|.  In this specific case, each "subdevice" corresponds to a
        single snow class (one element times three zones times two snow classes makes
        six subdevices):

        >>> ncvar = NetCDFVariableFlat("state_sp", "filename.nc")
        >>> ncvar.log(elements.element4.model.sequences.states.sp, None)
        >>> ncvar.shape
        (4, 6)
        """
        return (
            len(hydpy.pub.timegrids.init),
            sum(len(seq) for seq in self._descr2sequence.values()),
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
        >>> ncvar = NetCDFVariableFlat("input_nied", "filename.nc")
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

        >>> ncvar = NetCDFVariableFlat("flux_nkor", "filename.nc")
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

        >>> ncvar = NetCDFVariableFlat("state_sp", "filename.nc")
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
        for seq, subarray in zip(
            self._descr2sequence.values(), self._descr2array.values()
        ):
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
        >>> ncvar = NetCDFVariableFlat("input_nied", "filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nied = element.model.sequences.inputs.nied
        ...         ncvar.log(nied, nied.series)
        >>> ncvar.subdevicenames
        ('element1', 'element2', 'element3')

        For 1-dimensional sequences like |lland_fluxes.NKor|, a suffix defines the
        index of the respective subdevice.  For example, the third column of
        |NetCDFVariableAgg.array| contains the series of the first hydrological
        response unit of the second element:

        >>> ncvar = NetCDFVariableFlat("flux_nkor", "filename.nc")
        >>> for element in elements:
        ...     if element.model.name.startswith("lland"):
        ...         nkor = element.model.sequences.fluxes.nkor
        ...         ncvar.log(nkor, nkor.series)
        >>> ncvar.subdevicenames
        ('element1_0', 'element2_0', 'element2_1', 'element3_0', 'element3_1', \
'element3_2')

        2-dimensional sequences like |hland_states.SP| require an additional suffix:

        >>> ncvar = NetCDFVariableFlat("state_sp", "filename.nc")
        >>> sp = elements.element4.model.sequences.states.sp
        >>> ncvar.log(sp, sp.series)
        >>> ncvar.subdevicenames
        ('element4_0_0', 'element4_0_1', 'element4_0_2', 'element4_1_0', \
'element4_1_1', 'element4_1_2')
        """
        stats: Deque[str] = collections.deque()
        for devicename, seq in self._descr2sequence.items():
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

    def read(self) -> None:
        """Read the data from the relevant NetCDF file.

        See the general documentation on class |NetCDFVariableFlat| for some examples.
        """
        try:
            with netcdf4.Dataset(self.filepath, "r") as ncfile:
                sequence = next(iter(self._descr2sequence.values()))
                timegrid = query_timegrid(ncfile, sequence)
                array = query_array(ncfile, self.name)
                idxs: Tuple[Any] = (slice(None),)
                subdev2index = self.query_subdevice2index(ncfile)
                for devicename, seq in self._descr2sequence.items():
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
                    seq.series = seq.adjust_series(timegrid, subarray)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to read data from NetCDF file `{self.filepath}`"
            )
