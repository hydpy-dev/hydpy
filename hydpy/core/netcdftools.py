# -*- coding: utf-8 -*-
"""This module extends the features of module |filetools| for loading data
from and storing data to netCDF4 files, consistent with the `NetCDF Climate
and Forecast (CF) Metadata Conventions <http://cfconventions.org/Data/
cf-conventions/cf-conventions-1.7/cf-conventions.html>`_

Usually, the features implemented in this module are only indirectly.
through applying class |SequenceManager| in three steps:

  1. Call either method |SequenceManager.open_netcdf_reader| or method
     |SequenceManager.open_netcdf_writer| to prepare a |NetCDFInterface|
     object for reading or writing.
  2. Call either the usual reading or writing methods of other HydPy
     classes (e.g. method |HydPy.prepare_inputseries| of class |HydPy|
     or method |Elements.save_stateseries| of class |Elements|).
     The reading or writing processes of all |IOSequence| objects with
     property |IOSequence.filetype_ext| set to `nc` are essentially
     performed by the prepared |NetCDFInterface| object.
  3. Finalize reading or writing by calling either method
     |SequenceManager.close_netcdf_reader| or method
     |SequenceManager.close_netcdf_writer|.

Step 2 is actually a logging process only, telling the |NetCDFInterface|
object which data needs to be read or written.  The actual reading from
or writing to NetCDF files is triggered by step 3.

During step 2, the |NetCDFInterface| object is accessible, allowing
to inspect is current state or to modify its behaviour.

The following real code examples show how to perform these three steps
both for reading and writing data.  They are based on the example
configuration defined by function |prepare_io_example_1|:

>>> from hydpy.tests.examples import prepare_io_example_1
>>> nodes, elements = prepare_io_example_1()

(1) We prepare a |NetCDFInterface| class for reading data by
calling method |SequenceManager.open_netcdf_writer|:

>>> from hydpy import pub
>>> pub.sequencemanager.open_netcdf_writer()

(2) We tell the |SequenceManager| to write all time series
data into NetCDF files:
>>> pub.sequencemanager.generalfiletype = 'nc'

(3) We store all time series handles by the |Node| and |Element|
objects of the example data set by calling |Nodes.save_allseries| of
class |Nodes| and |Elements.save_allseries| of class |Elements|:

>>> nodes.save_allseries()
>>> elements.save_allseries()

(4) We again log all sequences, but this time after telling the
|SequenceManager| that all time series shall be spatially averaged:

>>> pub.sequencemanager.generalaggregation = 'mean'
>>> nodes.save_allseries()
>>> elements.save_allseries()

(5) We can now navigate into the details of the logged time series
data via the |NetCDFInterface| object and its subobjects.  For example,
we can find out which flux sequence objects of type |lland_fluxes.NKor|
belonging to application model |lland_v1| have been logged (those of
elements `element1` and `element2`):

>>> pub.sequencemanager.netcdf_writer.lland_v1.flux_nkor.subdevicenames
('element1', 'element2')

(6) We tell the |SequenceManager| object to read all files from and
write all files to the IO testing directory directly (In real cases
you would just write the last command.  Writing this and the following
IO related commands in an "with |TestIO|:" block just makes sure we
are working in the IO testing directory instead of our current working
directory):

>>> from hydpy import TestIO
>>> with TestIO():
...     pub.sequencemanager.generalpath = ''

(7) We close the |NetCDFInterface| object.  This is the moment
where the writing process actually happens.  After that, the
interface object is not available anymore:

>>> with TestIO():
...     pub.sequencemanager.close_netcdf_writer()
>>> pub.sequencemanager.netcdf_writer
Traceback (most recent call last):
...
RuntimeError: The sequence file manager does currently handle no NetCDF \
writer object.

(8) We set the time series values of two test sequences to zero.
This serves the purpose to demonstrate that reading the data back in
actually works:

>>> nodes.node2.sequences.sim.series = 0.0
>>> elements.element2.model.sequences.fluxes.nkor.series = 0.0

(9) We speed up the process and prepare a |NetCDFInterface| object
for reading data, log all |NodeSequence| and |ModelSequence| objects,
and read their time series data from the created NetCDF file:

>>> pub.sequencemanager.open_netcdf_reader()
>>> nodes.load_simseries()
>>> elements.load_allseries()
>>> with TestIO():
...     pub.sequencemanager.close_netcdf_reader()

(10) We check if the data is available via the test sequences again,
and if the |NetCDFInterface| object has been closed:

>>> nodes.node2.sequences.sim.series
InfoArray([ 64.,  65.,  66.,  67.])
>>> elements.element2.model.sequences.fluxes.nkor.series
InfoArray([[ 16.,  17.],
           [ 18.,  19.],
           [ 20.,  21.],
           [ 22.,  23.]])
>>> pub.sequencemanager.netcdf_reader
Traceback (most recent call last):
...
RuntimeError: The sequence file manager does currently handle no \
NetCDF reader object.

(11) The process of spatial averaging cannot be inverted.  Hence
reading averaged (or somehow else aggregated) time series is left
for preprocessing tools.  To show that writing the averaged series
actually worked, we open access the both relevant NetCDF files
more directly (note that averaging 1-dimensional time series as
those of node sequence |Sim| is allowed for the sake of consistency):

>>> from hydpy import netcdf4
>>> from numpy import array
>>> with TestIO():
...     with netcdf4.Dataset('node.nc') as ncfile:
...         array(ncfile['sim_q_mean'][:])
array([[ 60.,  61.,  62.,  63.]])
>>> with TestIO():
...     with netcdf4.Dataset('lland_v1.nc') as ncfile:
...         array(ncfile['flux_nkor_mean'][:])[1]
array([ 16.5,  18.5,  20.5,  22.5])

The described workflow is, besides the testing related specialities,
more or less standard and can be modified in many ways, which are
described in the documentation of the different features implemented
in module |netcdftools|, but also in the documentation on class
|SequenceManager| of module |filetools| and class |IOSequence| of
module |sequencetools|.

The examples above give little insight in the resulting/required
structure of NetCDF files.  One should at least be aware of the
optional arguments `flatten` and `isolate`.  If `flatten` is |True|,
multidimensional time series are handles as a larger number of
1-dimensional time series.  If `isolate` is |True|, all |IOSequence|
of a certain subclass are handled within a separate NetCDF file.
When reading a NetCDF file one has to choose the same options with
which the file has been written.

The following technical test just shows that the arguments are
passed properly to the constructor of |NetCDFInterface|:

>>> from unittest.mock import patch
>>> with patch('hydpy.core.netcdftools.NetCDFInterface') as mock:
...     pub.sequencemanager.open_netcdf_writer(flatten=True, isolate=False)
...     mock.assert_called_with(flatten=True, isolate=False)
...     pub.sequencemanager.open_netcdf_reader(flatten=True, isolate=False)
...     mock.assert_called_with(flatten=True, isolate=False)

ToDo: Add meta data when writing NetCDF files.

ToDo: Try to determine `flatten` and `isolate` automatically when reading files?

ToDo: Store subperiods of the actual initialization time period.
"""
# import...
# ...from standard library
from typing import Any, Iterator, Dict, List, Tuple, TypeVar
import abc
import collections
import itertools
import os
# ...from site-packages
import numpy
from hydpy import netcdf4
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import timetools

IntOrSlice = TypeVar('IntOrSlice', int, slice)

dimmapping = {
    'nmb_timepoints': 'time',
    'nmb_subdevices': 'stations',
    'nmb_characters': 'char_leng_name'}
"""Mapping between the names of dimensions in HydPy terms and in NetCDF
terms.

You can change this mapping if it does not suit your requirements.  For
example change the value of the key `nmb_subdevices`, if you prefer to
call this dimension `place` instead of `stations` within NetCDF files:

>>> from hydpy.core.netcdftools import dimmapping
>>> dimmapping['nmb_subdevices'] = 'place'
"""

varmapping = {
    'timepoints': 'time',
    'subdevices': 'station_names'}
"""Mapping between the names of variables in HydPy terms and in NetCDF
terms.

You can change this mapping if it does not suit your requirements.  For
example change the value of the key `timepoints`, if you prefer to
call this dimension `period` instead of `time` within NetCDF files:

>>> from hydpy.core.netcdftools import varmapping
>>> varmapping['timepoints'] = 'period'
"""

fillvalue = -999.
"""Default fill value for writing NetCDF files.

You can set another |float| value before writing a NetCDF file:

>>> from hydpy.core import netcdftools
>>> netcdftools.fillvalue = -777.0
"""


def str2chars(strings) -> numpy.ndarray:
    """Return |numpy.ndarray| containing the byte characters (second axis)
    of all given strings (first axis).

    >>> from hydpy.core.netcdftools import str2chars
    >>> str2chars(['zeros', 'ones'])
    array([[b'z', b'e', b'r', b'o', b's'],
           [b'o', b'n', b'e', b's', b'']],
          dtype='|S1')

    >>> str2chars([])
    array([], shape=(0, 0),
          dtype='|S1')
    """
    maxlen = 0
    for name in strings:
        maxlen = max(maxlen, len(name))
    # noinspection PyTypeChecker
    chars = numpy.full(
        (len(strings), maxlen), b'', dtype='|S1')
    for idx, name in enumerate(strings):
        for jdx, char in enumerate(name):
            chars[idx, jdx] = char.encode('utf-8')
    return chars


def chars2str(chars) -> List[str]:
    """Inversion function of function |str2chars|.

    >>> from hydpy.core.netcdftools import chars2str

    >>> chars2str([[b'z', b'e', b'r', b'o', b's'],
    ...            [b'o', b'n', b'e', b's', b'']])
    ['zeros', 'ones']

    >>> chars2str([])
    []
    """
    strings = collections.deque()
    for subchars in chars:
        substrings = collections.deque()
        for char in subchars:
            if char:
                substrings.append(char.decode('utf-8'))
            else:
                substrings.append('')
        strings.append(''.join(substrings))
    return list(strings)


def create_dimension(ncfile, name, length) -> None:
    """Add a new dimension with the given name and length to the given
    NetCDF file.

    Essentially, |create_dimension| just calls the equally named method
    of the NetCDF library...

    >>> from hydpy import netcdf4, TestIO
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('test.nc', 'w')
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, 'dim1', 5)
    >>> ncfile.dimensions['dim1'].size
    5

    ...but adds information to possible error messages:

    >>> create_dimension(ncfile, 'dim1', 5)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add dimension `dim1` with length `5` \
to the NetCDF file `test.nc`, the following error occurred: \
NetCDF: String match to name in use

    >>> ncfile.close()
    """
    try:
        ncfile.createDimension(name, length)
    except BaseException:
        objecttools.augment_excmessage(
            'While trying to add dimension `%s` with length `%d` '
            'to the NetCDF file `%s`'
            % (name, length, ncfile.filepath()))


def create_variable(ncfile, name, datatype, dimensions) -> None:
    """Add a new variable with the given name, datatype, and dimensions
    to the given NetCDF file.

    Essentially, |create_variable| just calls the equally named method
    of the NetCDF library but adds information to possible error messages:

    >>> from hydpy import netcdf4, TestIO
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('test.nc', 'w')
    >>> from hydpy.core.netcdftools import create_variable
    >>> create_variable(ncfile, 'var1', 'f8', ('dim1',))
    Traceback (most recent call last):
    ...
    ValueError: While trying to add variable `var1` with datatype `f8` and \
dimensions `('dim1',)` to the NetCDF file `test.nc`, the following error \
occurred: cannot find dimension dim1 in this group or parent groups

    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, 'dim1', 5)
    >>> create_variable(ncfile, 'var1', 'f8', ('dim1',))
    >>> import numpy
    >>> numpy.array(ncfile['var1'][:])
    array([-999., -999., -999., -999., -999.])
    >>> ncfile.close()
    """
    default = fillvalue if (datatype == 'f8') else None
    try:
        ncfile.createVariable(
            name, datatype, dimensions=dimensions, fill_value=default)
    except BaseException:
        objecttools.augment_excmessage(
            'While trying to add variable `%s` with datatype `%s` '
            'and dimensions `%s` to the NetCDF file `%s`'
            % (name, datatype, dimensions, ncfile.filepath()))


def query_variable(ncfile, name) -> netcdf4.Variable:
    """
    >>> from hydpy.core.netcdftools import query_variable
    >>> from hydpy import netcdf4, TestIO
    >>> with TestIO():
    ...     file_ = netcdf4.Dataset('model.nc', 'w')
    >>> query_variable(file_, 'flux_prec')
    Traceback (most recent call last):
    ...
    OSError: NetCDF file `model.nc` does not contain variable `flux_prec`.

    >>> from hydpy.core.netcdftools import create_variable
    >>> create_variable(file_, 'flux_prec', 'f8', ())
    >>> isinstance(query_variable(file_, 'flux_prec'), netcdf4.Variable)
    True

    >>> file_.close()
    >>> TestIO.clear()
    """
    try:
        return ncfile[name]
    except IndexError:
        raise OSError(
            'NetCDF file `%s` does not contain variable `%s`.'
            % (ncfile.filepath(), name))


class NetCDFInterface(object):
    """Interface between |SequenceManager| and multiple NetCDF files.

    The core task of class |NetCDFInterface| is to distribute different
    |IOSequence| objects on different instances of class |NetCDFFile|.

   (1) We prepare an |SequenceManager| object and some devices handling
   different sequences by applying function |prepare_io_example_1|:

    >>> from hydpy.tests.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    (2) We collect all sequences to be used in the following examples:

    >>> sequences = []
    >>> for node in nodes:
    ...     sequences.append(node.sequences.sim)
    >>> for element in elements:
    ...     sequences.append(element.model.sequences.inputs.nied)
    ...     sequences.append(element.model.sequences.fluxes.nkor)

    (3) We prepare a |NetCDFInterface| object and log all test
    sequences.  Due to setting `flatten` to |False|, three
    |NetCDFFile| objects are prepared for the sequences handled by
    |Node| objects, or the application models |lland_v1| and
    |lland_v2| respectively:

    >>> from hydpy.core.netcdftools import NetCDFInterface
    >>> interface = NetCDFInterface(flatten=False, isolate=False)
    >>> for sequence in sequences:
    ...     interface.log(sequence, sequence.series)
    ...     interface.log(sequence, sequence.average_series())
    >>> list(interface.filenames)
    ['node', 'lland_v1', 'lland_v2']
    >>> interface.lland_v1.variablenames
    ('input_nied', 'input_nied_mean', 'flux_nkor', 'flux_nkor_mean')

    (4) We store all NetCDF files directly into the testing directory:

    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.generalpath = ''
    ...     interface.write()

    (5) We define a shorter initialization time period and re-activate
    the time series of the test sequences:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('02.01.2000',
    ...                                    '04.01.2000',
    ...                                    '1d'))
    >>> for sequence in sequences:
    ...     sequence.activate_ram()

    (6) We again initialize class |NetCDFInterface|, log all
    test sequences, and read the test data of the defined subperiod:

    >>> from hydpy.core.netcdftools import NetCDFInterface
    >>> interface = NetCDFInterface(flatten=False, isolate=False)
    >>> for sequence in sequences:
    ...     interface.log(sequence, None)

    >>> with TestIO():
    ...     interface.read()
    >>> nodes.node1.sequences.sim.series
    InfoArray([ 61.,  62.])
    >>> elements.element2.model.sequences.fluxes.nkor.series
    InfoArray([[ 18.,  19.],
               [ 20.,  21.]])

    (7) We repeat the above steps, except that we set both
    `flatten` and `isolate` to |True|.  The relevant difference is
    that each NetCDF variable is now stored in a separate file:

    >>> from hydpy.tests.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    >>> sequences = []
    >>> for node in nodes:
    ...     sequences.append(node.sequences.sim)
    >>> for element in elements:
    ...     sequences.append(element.model.sequences.inputs.nied)
    ...     sequences.append(element.model.sequences.fluxes.nkor)

    >>> interface = NetCDFInterface(flatten=True, isolate=True)
    >>> for sequence in sequences:
    ...     interface.log(sequence, sequence.series)
    ...     interface.log(sequence, sequence.average_series())
    >>> from pprint import pprint
    >>> pprint(interface.filenames)
    ('node_sim_q',
     'node_sim_q_mean',
     'node_sim_t',
     'node_sim_t_mean',
     'lland_v1_input_nied',
     'lland_v1_input_nied_mean',
     'lland_v1_flux_nkor',
     'lland_v1_flux_nkor_mean',
     'lland_v2_input_nied',
     'lland_v2_input_nied_mean',
     'lland_v2_flux_nkor',
     'lland_v2_flux_nkor_mean')
    >>> interface.lland_v1_input_nied_mean.variablenames
    ('input_nied_mean',)

    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.outputpath = ''
    ...     interface.write()

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('02.01.2000',
    ...                                    '04.01.2000',
    ...                                    '1d'))
    >>> for sequence in sequences:
    ...     sequence.activate_ram()

    >>> interface = NetCDFInterface(flatten=True, isolate=True)
    >>> for sequence in sequences:
    ...     interface.log(sequence, None)
    >>> with TestIO():
    ...     pub.sequencemanager.inputpath = ''
    ...     interface.read()
    >>> nodes.node1.sequences.sim.series
    InfoArray([ 61.,  62.])
    >>> elements.element2.model.sequences.fluxes.nkor.series
    InfoArray([[ 18.,  19.],
               [ 20.,  21.]])

    (8) We technically confirm that the `isolate` argument is passed
    to the constructor of class |NetCDFFile| correctly:

    >>> from unittest.mock import patch
    >>> with patch('hydpy.core.netcdftools.NetCDFFile') as mock:
    ...     interface = NetCDFInterface(flatten=True, isolate=False)
    ...     interface.log(sequences[0], sequences[0].series)
    ...     mock.assert_called_once_with(
    ...         name='node', flatten=True, isolate=False)
    """

    def __init__(self, flatten, isolate):
        self._flatten = flatten
        self._isolate = isolate
        self.files: 'Dict[str, NetCDFFile]' = collections.OrderedDict()

    def log(self, sequence, infoarray) -> None:
        """Prepare a |NetCDFFile| object suitable for the given |IOSequence|
        object, when necessary, and pass the given arguments to its
        |NetCDFFile.log| method."""
        if isinstance(sequence, sequencetools.ModelIOSequence):
            descr = sequence.descr_model
        else:
            descr = 'node'
        if self._isolate:
            descr = '%s_%s' % (descr, sequence.descr_sequence)
            if ((infoarray is not None) and
                    (infoarray.info['type'] != 'unmodified')):
                descr = '%s_%s' % (descr, infoarray.info['type'])
        if descr in self.files:
            file_ = self.files[descr]
        else:
            file_ = NetCDFFile(
                name=descr, flatten=self._flatten, isolate=self._isolate)
            self.files[descr] = file_
        file_.log(sequence, infoarray)

    def read(self) -> None:
        """Call method |NetCDFFile.read| of all handled |NetCDFFile| objects.
        """
        for file_ in self.files.values():
            file_.read()

    def write(self) -> None:
        """Call method |NetCDFFile.write| of all handled |NetCDFFile| objects.
        """
        if self.files:
            init = pub.timegrids.init
            timeunits = init.firstdate.to_cfunits('hours')
            timepoints = init.to_timepoints('hours')
            for file_ in self.files.values():
                file_.write(timeunits, timepoints)

    @property
    def filenames(self) -> Tuple[str, ...]:
        """Tuple of names of all handled |NetCDFFile| objects."""
        return tuple(self.files.keys())

    def __getattr__(self, name):
        try:
            return self.files[name]
        except KeyError:
            raise AttributeError(
                'The current NetCDFInterface object does neither handle '
                'a NetCDFFile object named `%s` nor does it define a '
                'member named `%s`.'
                % (name, name))

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __dir__(self):
        return objecttools.dir_(self) + list(self.files.keys())


class NetCDFFile(object):
    """Handles a single NetCDF file.

    The core task of class |NetCDFFile| is to distribute different
    |IOSequence| objects on different instances of |NetCDFVariableBase|
    subclasses.  This is explained in detail in the documentation of
    method |NetCDFFile.log|.  Here we focus on how a |NetCDFFile| objects
    triggers the reading and writing functionalities of its subobjects.

    (1) we prepare an |SequenceManager| object and some devices handling
    different sequences by applying function |prepare_io_example_1|:

    >>> from hydpy.tests.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3) = prepare_io_example_1()

    (2) We define two shortcuts for the sequences actually used
    in the following examples:

    >>> nied = element1.model.sequences.inputs.nied
    >>> nkor = element1.model.sequences.fluxes.nkor

    (3) We prepare a |NetCDFFile| object and log the
    |lland_inputs.Nied| sequence:

    >>> from hydpy.core.netcdftools import NetCDFFile
    >>> ncfile = NetCDFFile('model', flatten=False, isolate=False)
    >>> ncfile.log(nied, nied.series)

    (4) We store NetCDF file directly into the testing directory:

    >>> from hydpy import pub, TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.outputpath = ''
    ...     init = pub.timegrids.init
    ...     ncfile.write(timeunit=init.firstdate.to_cfunits('hours'),
    ...                  timepoints=init.to_timepoints('hours'))

    (5) We set the time series values of the test sequence to zero,
    log the sequence to a new |NetCDFFile| instance, read the data
    from the NetCDF file, and check that is actually passed to the
    sequence object:

    >>> nied.series = 0.0
    >>> ncfile = NetCDFFile('model', flatten=True, isolate=False)
    >>> ncfile.log(nied, nied.series)
    >>> with TestIO():
    ...     pub.sequencemanager.inputpath = ''
    ...     ncfile.read()
    >>> nied.series
    InfoArray([ 0.,  1.,  2.,  3.])

    (6) We show that IO errors should result in readable error messages:

    >>> ncfile.log(nkor, nkor.series)
    >>> with TestIO():
    ...     ncfile.read()
    Traceback (most recent call last):
    ...
    OSError: While trying to read data from NetCDF file `model.nc`, \
the following error occurred: NetCDF file `model.nc` does not \
contain variable `flux_nkor`.
    """

    def __init__(self, name: str, flatten, isolate):
        self.name = name
        self._flatten = flatten
        self._isolate = isolate
        self.variables: 'Dict[str, NetCDFVariableBase]' = \
            collections.OrderedDict()

    def log(self, sequence, infoarray) -> None:
        """Pass the given |IoSequence| to a suitable instance of
        a |NetCDFVariableBase| subclass.

        When writing data, the second argument should be an |InfoArray|.
        When reading data, this argument is ignored. Simply pass |None|.

        (1) We prepare some devices handling some sequences by applying
        function |prepare_io_example_1|.  We will limit out attention to
        the returned elements, which handle the more diverse sequences:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, (element1, element2, element3) = prepare_io_example_1()

        (2) We define some shortcuts for the sequences actually used
        in the following examples:

        >>> nied1 = element1.model.sequences.inputs.nied
        >>> nied2 = element2.model.sequences.inputs.nied
        >>> nkor2 = element2.model.sequences.fluxes.nkor
        >>> nkor3 = element3.model.sequences.fluxes.nkor

        (3) We define a function that logs these example sequences
        to a given |NetCDFFile| object and prints some information
        about the resulting object structure.  Note that sequence
        `nkor2` is logged twice, the first time with its original
        time series data, the second time with averaged values:

        >>> from hydpy import classname
        >>> def test(ncfile):
        ...     ncfile.log(nied1, nied1.series)
        ...     ncfile.log(nied2, nied2.series)
        ...     ncfile.log(nkor2, nkor2.series)
        ...     ncfile.log(nkor2, nkor2.average_series())
        ...     ncfile.log(nkor3, nkor3.average_series())
        ...     for name, variable in ncfile.variables.items():
        ...         print(name, classname(variable), variable.subdevicenames)

        (4) We prepare a |NetCDFFile| object with both options
        `flatten` and `isolate` beeing disabled:

        >>> from hydpy.core.netcdftools import NetCDFFile
        >>> ncfile = NetCDFFile('model', flatten=False, isolate=False)

        (5) we logging all test sequences results in two
        |NetCDFVariableDeep| and one |NetCDFVariableAgg| objects.
        To keep both objects related to |lland_fluxes.NKor|
        distinguishable, the name `flux_nkor_mean` includes an
        information about the kind of aggregation performed:

        >>> test(ncfile)
        input_nied NetCDFVariableDeep ('element1', 'element2')
        flux_nkor NetCDFVariableDeep ('element2',)
        flux_nkor_mean NetCDFVariableAgg ('element2', 'element3')

        (6) Wo confirm that all information required by the
        |NetCDFVariableBase| objects has been passed:

        >>> ncfile.flux_nkor.element2.sequence.descr_device
        'element2'
        >>> ncfile.flux_nkor.element2.array
        InfoArray([[ 16.,  17.],
                   [ 18.,  19.],
                   [ 20.,  21.],
                   [ 22.,  23.]])
        >>> ncfile.flux_nkor_mean.element2.sequence.descr_device
        'element2'
        >>> ncfile.flux_nkor_mean.element2.array
        InfoArray([ 16.5,  18.5,  20.5,  22.5])

        (7) We again prepare a |NetCDFFile| object, but now with
        both options `flatten` and `isolate` beeing enabled.
        Logging test sequences with their original time series data
        does now trigger the initialization of class
        |NetCDFVariableFlat|.  Logging sequences with aggregated
        data remains unaffected:

        >>> ncfile = NetCDFFile('model', flatten=True, isolate=True)
        >>> test(ncfile)
        input_nied NetCDFVariableFlat ('element1', 'element2')
        flux_nkor NetCDFVariableFlat ('element2_0', 'element2_1')
        flux_nkor_mean NetCDFVariableAgg ('element2', 'element3')
        >>> ncfile.flux_nkor.element2.sequence.descr_device
        'element2'
        >>> ncfile.flux_nkor.element2.array
        InfoArray([[ 16.,  17.],
                   [ 18.,  19.],
                   [ 20.,  21.],
                   [ 22.,  23.]])
        >>> ncfile.flux_nkor_mean.element2.sequence.descr_device
        'element2'
        >>> ncfile.flux_nkor_mean.element2.array
        InfoArray([ 16.5,  18.5,  20.5,  22.5])

        (8) We technically confirm that the `isolate` argument is passed
        to the constructor of subclasses of |NetCDFVariableBase| correctly:

        >>> from unittest.mock import patch
        >>> with patch('hydpy.core.netcdftools.NetCDFVariableFlat') as mock:
        ...     ncfile = NetCDFFile('model', flatten=True, isolate=False)
        ...     ncfile.log(nied1, nied1.series)
        ...     mock.assert_called_once_with(
        ...         name='input_nied', isolate=False)
        """
        aggregated = ((infoarray is not None) and
                      (infoarray.info['type'] != 'unmodified'))
        descr = sequence.descr_sequence
        if aggregated:
            descr = '_'.join([descr, infoarray.info['type']])
        if descr in self.variables:
            var_ = self.variables[descr]
        else:
            if aggregated:
                cls = NetCDFVariableAgg
            elif self._flatten:
                cls = NetCDFVariableFlat
            else:
                cls = NetCDFVariableDeep
            var_ = cls(name=descr, isolate=self._isolate)
            self.variables[descr] = var_
        var_.log(sequence, infoarray)

    @property
    def filepath_read(self) -> str:
        """File path for reading data from the corresponding NetCDF file.

        (1) We prepare an |SequenceManager| object by applying
        function |prepare_io_example_1|:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> _ = prepare_io_example_1()

        (2) We initialize class |NetCDFFile| with (nearly) random
        arguments.  The resulting path for reading data is:

        >>> from hydpy.core.netcdftools import NetCDFFile
        >>> ncfile = NetCDFFile('some_model', flatten=None, isolate=None)
        >>> from hydpy import repr_
        >>> repr_(ncfile.filepath_read)
        'inputpath/some_model.nc'

        (3) We repeat the second step with another name argument.
        The occurence of substring `node` changes the base directory:

        >>> ncfile = NetCDFFile('some_node_q', flatten=None, isolate=None)
        >>> repr_(ncfile.filepath_read)
        'nodepath/some_node_q.nc'
        """
        return self._filepath(read=True)

    @property
    def filepath_write(self) -> str:
        """File path for writing data to the corresponding NetCDF file.

        (1) We prepare an |SequenceManager| object by applying
        function |prepare_io_example_1|:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> _ = prepare_io_example_1()

        (2) We initialize class |NetCDFFile| with (nearly) random
        arguments.  The resulting path for writing data is:

        >>> from hydpy.core.netcdftools import NetCDFFile
        >>> ncfile = NetCDFFile('some_model', flatten=None, isolate=None)
        >>> from hydpy import repr_
        >>> repr_(ncfile.filepath_write)
        'outputpath/some_model.nc'

        (3) We repeat the second step with another name argument.
        The occurence of substring `node` changes the base directory:

        >>> ncfile = NetCDFFile('some_node_q', flatten=None, isolate=None)
        >>> repr_(ncfile.filepath_write)
        'nodepath/some_node_q.nc'
        """
        return self._filepath(read=False)

    def _filepath(self, read) -> str:
        # FixMe: pub must become an object!!!
        if 'node' in self.name:
            path = pub.sequencemanager.nodepath
        else:
            if read:
                path = pub.sequencemanager.inputpath
            else:
                path = pub.sequencemanager.outputpath
        return os.path.join(path, self.name + '.nc')

    def read(self) -> None:
        """Open an existing NetCDF file temporarily and call method
        |NetCDFVariableDeep.read| of all handled |NetCDFVariableBase|
        objects."""
        filepath = self.filepath_read
        try:
            with netcdf4.Dataset(filepath, "r") as ncfile:
                timepoints = ncfile[varmapping['timepoints']]
                refdate = timetools.Date.from_cfunits(timepoints.units)
                timegrid = timetools.Timegrid.from_timepoints(
                    timepoints=timepoints[:],
                    refdate=refdate,
                    unit=timepoints.units.strip().split()[0])
                for variable in self.variables.values():
                    variable.read(ncfile, timegrid)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to read data from NetCDF file `%s`'
                % filepath)

    def write(self, timeunit, timepoints) -> None:
        """Open a new NetCDF file temporarily and call method
        |NetCDFVariableDeep.write| of all handled |NetCDFVariableBase|
        objects."""
        with netcdf4.Dataset(self.filepath_write, "w") as ncfile:
            self._insert_timepoints(ncfile, timepoints, timeunit)
            for variable in self.variables.values():
                variable.write(ncfile)

    @staticmethod
    def _insert_timepoints(ncfile, timepoints, timeunit) -> None:
        dim_name = dimmapping['nmb_timepoints']
        var_name = varmapping['timepoints']
        create_dimension(ncfile, dim_name, len(timepoints))
        create_variable(ncfile, var_name, 'f8', (dim_name,))
        var_ = ncfile[var_name]
        var_[:] = timepoints
        var_.units = timeunit

    @property
    def variablenames(self) -> Tuple[str, ...]:
        """The names of all handled |IOSequence| objects."""
        return tuple(self.variables.keys())

    def __getattr__(self, name):
        try:
            return self.variables[name]
        except KeyError:
            raise AttributeError(
                'The NetCDFFile object `%s` does neither handle a '
                'NetCDFVariableDeep object named `%s` nor does it define a '
                'member named `%s`.'
                % (self.name, name, name))

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __dir__(self):
        return objecttools.dir_(self) + list(self.variablenames)


NetCDFVariableInfo = collections.namedtuple(
    'NetCDFVariableInfo', ['sequence', 'array'])


class Subdevice2Index(object):
    """Return type of method |NetCDFVariableBase.query_subdevice2index|."""

    def __init__(self, dict_, name_sequence, name_ncfile):
        self.dict_ = dict_
        self.name_sequence = name_sequence
        self.name_ncfile = name_ncfile

    def get_index(self, name_subdevice) -> int:
        """Item access to the wrapped |dict| object with a specialized
        error message."""
        try:
            return self.dict_[name_subdevice]
        except KeyError:
            raise OSError(
                'No data for sequence `%s` and (sub)device `%s` '
                'in NetCDF file `%s` available.'
                % (self.name_sequence,
                   name_subdevice,
                   self.name_ncfile))


class NetCDFVariableBase(abc.ABC):
    """

    >>> from hydpy.core.netcdftools import NetCDFVariableBase
    >>> from hydpy import make_abc_testable, dummies
    >>> dummies.NetCDFVariableBase_ = make_abc_testable(NetCDFVariableBase)
    """
    def __init__(self, name, isolate):
        self.name = name
        self._isolate = isolate
        self.sequences: Dict[str, sequencetools.IOSequence] = \
            collections.OrderedDict()
        self.arrays: Dict[str, sequencetools.InfoArray] = \
            collections.OrderedDict()

    def log(self, sequence, infoarray) -> None:
        """Log the given |IOSequence| object either for reading or writing
        data.

        The optional `array` argument allows for passing alternative data
        in an |InfoArray| object replacing the series of the |IOSequence|
        object. This is usefull for writing modified (e.g. spatially
        averaged) time series.
        """
        descr_device = sequence.descr_device
        self.sequences[descr_device] = sequence
        self.arrays[descr_device] = infoarray

    @property
    @abc.abstractmethod
    def subdevicenames(self) -> Tuple[str, ...]:
        """A |tuple| containing the station names."""
        ...

    @property
    @abc.abstractmethod
    def dimensions(self) -> Tuple[str, ...]:
        ...

    @property
    @abc.abstractmethod
    def array(self) -> numpy.ndarray:
        ...

    @property
    def prefix(self) -> str:
        """

        >>> from hydpy import dummies
        >>> dummies.NetCDFVariableBase_('name', isolate=False).prefix
        'name_'
        >>> dummies.NetCDFVariableBase_('name', isolate=True).prefix
        ''
        """
        return '' if self._isolate else '%s_' % self.name

    def insert_subdevices(self, ncfile) -> None:
        """

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable, netcdf4, TestIO
        >>> Var = make_abc_testable(NetCDFVariableBase)

        >>> Var.subdevicenames = 'element1', 'element2'
        >>> var1 = Var('var1', isolate=False)
        >>> var1.subdevicenames = 'element1', 'element2'
        >>> with TestIO(clear_all=True):
        ...     file1 = netcdf4.Dataset('model1.nc', 'w')

        >>> var1.insert_subdevices(file1)

        >>> for dimension in file1.dimensions.values():
        ...     print(dimension.name, dimension.size)
        var1_stations 2
        var1_char_leng_name 8

        >>> for variable in file1.variables.values():
        ...     print(variable.name, variable.dimensions, variable.shape)
        var1_station_names ('var1_stations', 'var1_char_leng_name') (2, 8)


        >>> var2 = Var('var2', isolate=True)
        >>> var2.subdevicenames = 'element1', 'element2'
        >>> with TestIO(clear_all=True):
        ...     file2 = netcdf4.Dataset('model2.nc', 'w')
        >>> var2.insert_subdevices(file2)
        >>> for variable in file2.variables.values():
        ...     print(variable.name, variable.dimensions, variable.shape)
        station_names ('stations', 'char_leng_name') (2, 8)

        """
        prefix = self.prefix
        nmb_subdevices = '%s%s' % (prefix, dimmapping['nmb_subdevices'])
        nmb_characters = '%s%s' % (prefix, dimmapping['nmb_characters'])
        subdevices = '%s%s' % (prefix, varmapping['subdevices'])
        statchars = str2chars(self.subdevicenames)
        create_dimension(ncfile, nmb_subdevices, statchars.shape[0])
        create_dimension(ncfile, nmb_characters, statchars.shape[1])
        create_variable(
            ncfile, subdevices, 'S1', (nmb_subdevices, nmb_characters))
        ncfile[subdevices][:, :] = statchars

    def query_subdevices(self, ncfile) -> List[str]:
        """
        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable, netcdf4, TestIO

        >>> with TestIO():
        ...     file_ = netcdf4.Dataset('model.nc', 'w')

        >>> var = make_abc_testable(NetCDFVariableBase)(
        ...     'flux_prec', isolate=False)
        >>> var.query_subdevices(file_)
        Traceback (most recent call last):
        ...
        OSError: NetCDF file `model.nc` does neither contain a variable \
named `flux_prec_station_names` nor `station_names` for defining the \
coordinate locations of variable `flux_prec`.

        >>> from hydpy.core import netcdftools as nct
        >>> nct.create_dimension(file_, 'stations', 2)
        >>> nct.create_dimension(file_, 'char_leng_name', 8)
        >>> nct.create_variable(file_,
        ...     'station_names', 'S1', ('stations', 'char_leng_name'))
        >>> file_['station_names'][:] = nct.str2chars(
        ...     ['element1', 'element2'])

        >>> file_.close()
        >>> TestIO.clear()
        """
        tests = ['%s%s' % (prefix, varmapping['subdevices'])
                 for prefix in ('%s_' % self.name, '')]
        for subdevices in tests:
            try:
                chars = ncfile[subdevices][:]
                break
            except IndexError:
                pass
        else:
            raise IOError(
                'NetCDF file `%s` does neither contain a variable '
                'named `%s` nor `%s` for defining the coordinate '
                'locations of variable `%s`.'
                % (ncfile.filepath(), tests[0], tests[1], self.name))
        return chars2str(chars)

    def query_subdevice2index(self, ncfile) -> Subdevice2Index:
        """Return a |Subdevice2Index| that maps the (sub)device names to
        their position within the given NetCDF file.

        >>> from hydpy.core.netcdftools import NetCDFVariableBase
        >>> from hydpy import make_abc_testable, netcdf4, TestIO
        >>> with TestIO():
        ...     file_ = netcdf4.Dataset('model.nc', 'w')
        >>> from hydpy.core import netcdftools as nct
        >>> nct.create_dimension(file_, 'stations', 4)
        >>> nct.create_dimension(file_, 'char_leng_name', 10)
        >>> nct.create_variable(file_,
        ...     'station_names', 'S1', ('stations', 'char_leng_name'))
        >>> file_['station_names'][:] = nct.str2chars(
        ...     ['element3', 'element1', 'element1_1', 'element2'])

        >>> var = make_abc_testable(NetCDFVariableBase)(
        ...     'flux_prec', isolate=False)

        >>> var.query_subdevice2index(file_).get_index('element1_1')
        2
        >>> var.query_subdevice2index(file_).get_index('element3')
        0
        >>> var.query_subdevice2index(file_).get_index('element5')
        Traceback (most recent call last):
        ...
        OSError: No data for sequence `flux_prec` and (sub)device \
`element5` in NetCDF file `model.nc` available.

        >>> file_['station_names'][:] = nct.str2chars(
        ...     ['element3', 'element1', 'element1_1', 'element1'])
        >>> var.query_subdevice2index(file_)
        Traceback (most recent call last):
        ...
        OSError: The NetCDF file `model.nc` contains duplicate (sub)device \
names for variable `flux_prec` (the first found duplicate is `element1`).

        >>> file_.close()
        >>> TestIO.clear()
        """
        subdevices = self.query_subdevices(ncfile)
        self._test_duplicate_exists(ncfile, subdevices)
        subdev2index = {subdev: idx for (idx, subdev) in enumerate(subdevices)}
        return Subdevice2Index(subdev2index, self.name, ncfile.filepath())

    def _test_duplicate_exists(self, ncfile, subdevices) -> None:
        if len(subdevices) != len(set(subdevices)):
            for idx, name1 in enumerate(subdevices):
                for name2 in subdevices[idx+1:]:
                    if name1 == name2:
                        raise OSError(
                            'The NetCDF file `%s` contains duplicate '
                            '(sub)device names for variable `%s` (the '
                            'first found duplicate is `%s`).'
                            % (ncfile.filepath(), self.name, name1))

    @abc.abstractmethod
    def read(self, ncfile, timegrid_data) -> None:
        ...

    @abc.abstractmethod
    def write(self, ncfile) -> None:
        ...

    def __getattr__(self, name):
        try:
            return NetCDFVariableInfo(self.sequences[name], self.arrays[name])
        except KeyError:
            raise AttributeError(
                'The NetCDFVariable object `%s` does neither handle a '
                'IOSequence object named `%s` nor does it define a '
                'member named `%s`.'
                % (self.name, name, name))

    def __dir__(self):
        return objecttools.dir_(self) + list(self.sequences.keys())


class NonFlatMixin(object):
    """Mixin class for |NetCDFVariableDeep| and |NetCDFVariableAgg|"""

    @property
    def subdevicenames(self) -> Tuple[str, ...]:
        """A |tuple| containing the device names."""
        self: NetCDFVariableBase
        return tuple(self.sequences.keys())

    def write(self, ncfile) -> None:
        """Write the data to the given NetCDF file.

        See the general documentation on classes |NetCDFVariableDeep|
        and |NetCDFVariableAgg| for some examples.
        """
        self: NetCDFVariableBase
        self.insert_subdevices(ncfile)
        dimensions = self.dimensions
        array = self.array
        for dimension, length in zip(dimensions[2:], array.shape[2:]):
            create_dimension(ncfile, dimension, length)
        create_variable(ncfile, self.name, 'f8', dimensions)
        ncfile[self.name][:] = array


class NonDeepMixin(object):
    """"Mixin class for | NetCDFVariableFlat| and | NetCDFVariableAgg|."""

    @property
    def dimensions(self) -> Tuple[str, ...]:
        """The dimension names of the NetCDF variable.

        Usually, the first dimension names related to place is
        prefixed with |IOSequence.descr_sequence|, which allows
        to store different sequences in one NetCDF file:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> ncvar = NetCDFVariableAgg('flux_nkor', isolate=False)
        >>> ncvar.log(elements.element1.model.sequences.fluxes.nkor, None)
        >>> ncvar.dimensions
        ('flux_nkor_stations', 'time')

        But when isolating variables into separate NetCDF files, the
        variable specific suffix is omitted:

        >>> ncvar = NetCDFVariableAgg('flux_nkor', isolate=True)
        >>> ncvar.log(elements.element1.model.sequences.fluxes.nkor, None)
        >>> ncvar.dimensions
        ('stations', 'time')
        """
        self: NetCDFVariableBase
        nmb_subdevices = '%s%s' % (self.prefix, dimmapping['nmb_subdevices'])
        return nmb_subdevices, dimmapping['nmb_timepoints']


class NetCDFVariableDeep(NonFlatMixin, NetCDFVariableBase):
    """Relates some objects of a specific |IOSequence| subclass with
    a single NetCDF variable without modifying dimensionality.

    Suitable both for reading and writing time series of sequences of
    arbitrary dimensionality.  Performs no flattening.

    (1) We prepare some devices handling some sequences by applying
    function |prepare_io_example_1|.  We will limit out attention to the
    returned elements, which handle the more diverse sequences:

    >>> from hydpy.tests.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3) = prepare_io_example_1()

    (2) We define two |NetCDFVariableMulti| instances and log the
    |lland_inputs.Nied| and |lland_fluxes.NKor| sequences of the first
    two elements:

    >>> from hydpy.core.netcdftools import NetCDFVariableDeep
    >>> var_nied = NetCDFVariableDeep('input_nied', isolate=False)
    >>> var_nkor = NetCDFVariableDeep('flux_nkor', isolate=False)
    >>> for element in (element1, element2):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)

    (3) We prepare a (nearly) empty NetCDF file. "Nearly", because
    all sequences have to be related to the same period, which is why
    time information is usually defined by a central instance of class
    |NetCDFFile|):

    >>> from hydpy import TestIO, netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'w')
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, 'time', 4)

    (4) We store the data of all logged sequences in the NetCDF file:

    >>> var_nied.write(ncfile)
    >>> var_nkor.write(ncfile)
    >>> ncfile.close()

    (5) We set all values of the series of both selected sequences
    to -777 and check that they are actually different from the original
    values available via attribute `testarray`:

    >>> seq1 = element1.model.sequences.inputs.nied
    >>> seq2 = element2.model.sequences.fluxes.nkor
    >>> import numpy
    >>> for seq in (seq1, seq2):
    ...     seq.series = -777.0
    ...     print(numpy.any(seq.series == seq.testarray))
    False
    False

    (6) We again prepare two |NetCDFVariableMulti| instances and
    log the same sequences as above, open the existing NetCDF file
    for reading, read its data, and confirm that this data has been
    passed to both test sequences properly:

    >>> nied1 = NetCDFVariableDeep('input_nied', isolate=False)
    >>> nkor1 = NetCDFVariableDeep('flux_nkor', isolate=False)
    >>> for element in (element1, element2):
    ...     sequences = element.model.sequences
    ...     nied1.log(sequences.inputs.nied, None)
    ...     nkor1.log(sequences.fluxes.nkor, None)
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'r')
    >>> nied1.read(ncfile, pub.timegrids.init)
    >>> nkor1.read(ncfile, pub.timegrids.init)
    >>> for seq in (seq1, seq2):
    ...     print(numpy.all(seq.series == seq.testarray))
    True
    True

    (6) We confirm that trying to read data that has not been stored
    properly, results in error messages like the following one:

    >>> nied1.log(element3.model.sequences.inputs.nied, None)
    >>> nied1.read(ncfile, pub.timegrids.init)
    Traceback (most recent call last):
    ...
    OSError: No data for sequence `input_nied` and (sub)device `element3` \
in NetCDF file `model.nc` available.

    >>> ncfile.close()

    (7) We repeat the first few steps, but pass |True| to the
    constructor of |NetCDFVariableMulti|.  This is done when one
    definitely wants to store only one sequence per NetCDF file.
    Nevertheless, we try to store two sequences within the same
    NetCDF file.  This works for the first sequence (|lland_inputs.Nied|),
    but not for the second one (|lland_fluxes.Nied|):

    >>> var_nied = NetCDFVariableDeep('input_nied', isolate=True)
    >>> var_nkor = NetCDFVariableDeep('flux_nkor', isolate=True)
    >>> for element in (element1, element2):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'w')
    >>> create_dimension(ncfile, 'time', 4)
    >>> var_nied.write(ncfile)
    >>> var_nkor.write(ncfile)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add dimension `stations` with length `2` \
to the NetCDF file `model.nc`, the following error occurred: \
NetCDF: String match to name in use
    >>> ncfile.close()
    >>> from hydpy import TestIO, netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'r')
    >>> seq1.series = 0.0
    >>> var_nied.read(ncfile, pub.timegrids.init)
    >>> seq1.series
    InfoArray([ 0.,  1.,  2.,  3.])
    >>> ncfile.close()
    """

    @staticmethod
    def get_slices(idx, shape) -> List[IntOrSlice]:
        """Return a |tuple| of one |int| and some |slice| objects that
        completely accesses all values within |NetCDFVariableMulti.array|
        based on the given primary index and shape of a sequence.

        >>> from hydpy.core.netcdftools import NetCDFVariableDeep
        >>> NetCDFVariableDeep.get_slices(2, [3])
        (2, slice(None, None, None), slice(0, 3, None))

        >>> NetCDFVariableDeep.get_slices(4, (1, 2))
        (4, slice(None, None, None), slice(0, 1, None), slice(0, 2, None))
        """
        slices = [idx, slice(None)]
        for length in shape:
            slices.append(slice(0, length))
        return tuple(slices)

    @property
    def shape(self) -> Tuple[int, ...]:
        """Required shape of |NetCDFVariableMulti.array|.

        The first axis corresponds to the number of devices, the
        second one two the number of timesteps.  We show this
        for the 0-dimensional input sequence |lland_inputs.Nied|:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableDeep
        >>> ncvar = NetCDFVariableDeep('input_nied', isolate=False)
        >>> for element in elements:
        ...     ncvar.log(element.model.sequences.inputs.nied, None)
        >>> ncvar.shape
        (3, 4)

        For higher dimensional sequences, each new entry corresponds
        to he maximum number of fields the respective sequences require.
        In the next example, we select the 1-dimensional sequence
        |lland_fluxes.NKor|.  The maximum number 3 (last value of the
        returned |tuple|) is due to the third element defining three
        hydrological response units:

        >>> ncvar = NetCDFVariableDeep('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (3, 4, 3)
        """
        maxshape = collections.deque()
        for sequence in self.sequences.values():
            maxshape.append(sequence.seriesshape)
        shape = [len(self.sequences)] + list(numpy.max(maxshape, axis=0))
        return tuple(shape)

    @property
    def array(self) -> numpy.ndarray:
        """The series data of all logged |IOSequence| objects contained
        in one single |numpy.ndarray| object.

        The documentation on |NetCDFVariableMulti.shape| explaines
        how |NetCDFVariableMulti.array| is structured.  The first
        examples confirms that the first axis corresponds to place,
        while the second one corresponds to time:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableDeep
        >>> ncvar = NetCDFVariableDeep('input_nied', isolate=False)
        >>> for element in elements:
        ...     nied1 = element.model.sequences.inputs.nied
        ...     ncvar.log(nied1, nied1.series)
        >>> ncvar.array
        array([[  0.,   1.,   2.,   3.],
               [  4.,   5.,   6.,   7.],
               [  8.,   9.,  10.,  11.]])

        For higher dimensional sequences, |NetCDFVariableMulti.array|
        can contain missing values.  This is the case for its fields
        related to the second example element, which defines only
        two hydrological response units instead of three:

        >>> ncvar = NetCDFVariableDeep('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     nkor1 = element.model.sequences.fluxes.nkor
        ...     ncvar.log(nkor1, nkor1.series)
        >>> ncvar.array[1]
        array([[  16.,   17., -999.],
               [  18.,   19., -999.],
               [  20.,   21., -999.],
               [  22.,   23., -999.]])
        """
        array = numpy.full(self.shape, fillvalue, dtype=float)
        for idx, (descr, subarray) in enumerate(self.arrays.items()):
            sequence = self.sequences[descr]
            array[self.get_slices(idx, sequence.shape)] = subarray
        return array

    @property
    def dimensions(self) -> Tuple[str, ...]:
        """The dimension names of the NetCDF variable.

        Usually, all dimension names except the one related to
        time are prefixed with |IOSequence.descr_sequence|, which
        allows to store different sequences in one NetCDF file:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableDeep
        >>> ncvar = NetCDFVariableDeep('flux_nkor', isolate=False)
        >>> ncvar.log(elements.element1.model.sequences.fluxes.nkor, None)
        >>> ncvar.dimensions
        ('flux_nkor_stations', 'time', 'flux_nkor_axis3')

        But when isolating variables into separate NetCDF files, the
        variable specific suffix is omitted:

        >>> ncvar = NetCDFVariableDeep('flux_nkor', isolate=True)
        >>> ncvar.log(elements.element1.model.sequences.fluxes.nkor, None)
        >>> ncvar.dimensions
        ('stations', 'time', 'axis3')
        """
        dimensions = ['%s%s' % (self.prefix, dimmapping['nmb_subdevices']),
                      dimmapping['nmb_timepoints']]
        for idx in range(list(self.sequences.values())[0].NDIM):
            dimensions.append('%saxis%d' % (self.prefix, idx + 3))
        return tuple(dimensions)

    def read(self, ncfile, timegrid_data) -> None:
        """Read the data from the given NetCDF file.

        The argument `timegrid_data` defines the data period of the
        given NetCDF file.

        See the general documentation on class |NetCDFVariableDeep|
        for some examples.
        """
        array = query_variable(ncfile, self.name)[:]
        subdev2index = self.query_subdevice2index(ncfile)
        for subdevice, sequence in self.sequences.items():
            idx = subdev2index.get_index(subdevice)
            values = array[self.get_slices(idx, sequence.shape)]
            sequence.series = sequence.adjust_series(
                timegrid_data, values)


class NetCDFVariableAgg(NonFlatMixin, NonDeepMixin, NetCDFVariableBase):
    """Relates some objects of a specific |IOSequence| subclass with
    a single NetCDF variable when aggregation of data is required.

    Suitable for writing time series data only.  Performs no flattening.

    Essentially, class |NetCDFVariableAgg| is very similar to class
    |NetCDFVariableDeep| but a little bit simpler, as it handles
    arrays with fixed dimensionality and provides no functionality
    for reading data from NetCDF files.  Hence, the following examples
    are a selection of the examples of the documentation on class
    |NetCDFVariableDeep|, which can be read for further information:

    >>> from hydpy.tests.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3) = prepare_io_example_1()
    >>> from hydpy.core.netcdftools import NetCDFVariableAgg
    >>> var_nied = NetCDFVariableAgg('input_nied_mean', isolate=False)
    >>> var_nkor = NetCDFVariableAgg('flux_nkor_mean', isolate=False)
    >>> for element in (element1, element2):
    ...     nied1 = element.model.sequences.inputs.nied
    ...     var_nied.log(nied1, nied1.average_series())
    ...     nkor1 = element.model.sequences.fluxes.nkor
    ...     var_nkor.log(nkor1, nkor1.average_series())
    >>> from hydpy import TestIO, netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'w')
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, 'time', 4)
    >>> var_nied.write(ncfile)
    >>> var_nkor.write(ncfile)
    >>> ncfile.close()

    As |NetCDFVariableAgg| provides no reading functionality, we
    show that the aggregated values are stored properly by using
    the external NetCDF4 library directly:

    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'r')
    >>> import numpy
    >>> numpy.array(ncfile['input_nied_mean'][:])
    array([[ 0.,  1.,  2.,  3.],
           [ 4.,  5.,  6.,  7.]])

    >>> numpy.array(ncfile['flux_nkor_mean'][:])
    array([[ 12. ,  13. ,  14. ,  15. ],
           [ 16.5,  18.5,  20.5,  22.5]])
    """

    @property
    def shape(self) -> Tuple[int, int]:
        """Required shape of |NetCDFVariableAgg.array|.

        The first axis corresponds to the number of devices, the
        second one two the number of timesteps.  We show this
        for the 1-dimensional input sequence |lland_inputs.NKor|:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> ncvar = NetCDFVariableAgg('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (3, 4)
        """
        return (len(self.sequences),
                len(tuple(self.sequences.values())[0].series))

    @property
    def array(self) -> numpy.ndarray:
        """The aggregated data of all logged |IOSequence| objects contained
        in one single |numpy.ndarray| object.

        The documentation on |NetCDFVariableAgg.shape| explaines
        how |NetCDFVariableAgg.array| is structured.  This first
        examples confirms, that first axis corresponds to place,
        while the second one corresponds time:

       >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> ncvar = NetCDFVariableAgg('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     nkor1 = element.model.sequences.fluxes.nkor
        ...     ncvar.log(nkor1, nkor1.average_series())
        >>> ncvar.array
        array([[ 12. ,  13. ,  14. ,  15. ],
               [ 16.5,  18.5,  20.5,  22.5],
               [ 25. ,  28. ,  31. ,  34. ]])
        """
        array = numpy.full(self.shape, fillvalue, dtype=float)
        for idx, subarray in enumerate(self.arrays.values()):
            array[idx] = subarray
        return array

    def read(self, ncfile, timegrid_data) -> None:
        """Raises a |RuntimeError| in any case.

        This method just raises the following exception, in order to tell
        users why implementing a real reading functionality is not possible:

        >>> from hydpy.core.netcdftools import NetCDFVariableAgg
        >>> NetCDFVariableAgg('flux_nkor', isolate=False).read(None, None)
        Traceback (most recent call last):
        ...
        RuntimeError: The process of aggregating values (of sequence \
`flux_nkor` and other sequences as well) is not invertible.
        """
        raise RuntimeError(
            'The process of aggregating values (of sequence `%s` and '
            'other sequences as well) is not invertible.'
            % self.name)


class NetCDFVariableFlat(NonDeepMixin, NetCDFVariableBase):
    """Relates some objects of a specific |IOSequence| subclass with
    a single NetCDF variable when flattening of data is required.

    Suitable both for reading and writing time series of sequences of
    arbitrary dimensionality.

    The following examples on the usage of class |NetCDFVariableFlat|
    are identical to the ones on the usage of class |NetCDFVariableDeep|.
    We repeat the examples for testing purposes, but refrain from repeating
    the explanations. The relevant difference on how the data is actually
    structered within NetCDF files should become clear when comparing
    the documenation on the different members of both classes.

    >>> from hydpy.tests.examples import prepare_io_example_1
    >>> nodes, (element1, element2, element3) = prepare_io_example_1()

    (2) We define two |NetCDFVariableFlat| instances and log the
    |lland_inputs.Nied| and |lland_fluxes.NKor| sequences of the first
    two elements:

    >>> from hydpy.core.netcdftools import NetCDFVariableFlat
    >>> var_nied = NetCDFVariableFlat('input_nied', isolate=False)
    >>> var_nkor = NetCDFVariableFlat('flux_nkor', isolate=False)
    >>> for element in (element1, element2):
    ...     seqs = element.model.sequences
    ...     var_nied.log(seqs.inputs.nied, seqs.inputs.nied.series)
    ...     var_nkor.log(seqs.fluxes.nkor, seqs.fluxes.nkor.series)


    >>> from hydpy import TestIO, netcdf4
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'w')
    >>> from hydpy.core.netcdftools import create_dimension
    >>> create_dimension(ncfile, 'time', 4)

    >>> var_nied.write(ncfile)
    >>> var_nkor.write(ncfile)
    >>> ncfile.close()

    >>> seq1 = element1.model.sequences.inputs.nied
    >>> seq2 = element2.model.sequences.fluxes.nkor
    >>> import numpy
    >>> for seq in (seq1, seq2):
    ...     seq.series = -777.0
    ...     print(numpy.any(seq.series == seq.testarray))
    False
    False

    >>> nied1 = NetCDFVariableFlat('input_nied', isolate=False)
    >>> nkor1 = NetCDFVariableFlat('flux_nkor', isolate=False)
    >>> for element in (element1, element2):
    ...     sequences = element.model.sequences
    ...     nied1.log(sequences.inputs.nied, None)
    ...     nkor1.log(sequences.fluxes.nkor, None)
    >>> with TestIO():
    ...     ncfile = netcdf4.Dataset('model.nc', 'r')
    >>> nied1.read(ncfile, pub.timegrids.init)
    >>> nkor1.read(ncfile, pub.timegrids.init)
    >>> for seq in (seq1, seq2):
    ...     print(numpy.all(seq.series == seq.testarray))
    True
    True
    """

    @property
    def shape(self) -> Tuple[int, int]:
        """Required shape of |NetCDFVariableFlat.array|.

        For 0-dimensional sequences like |lland_inputs.Nied|, the
        first axis corresponds to the number of devices, and the
        second one two the number of timesteps:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> ncvar = NetCDFVariableFlat('input_nied', isolate=False)
        >>> for element in elements:
        ...     ncvar.log(element.model.sequences.inputs.nied, None)
        >>> ncvar.shape
        (3, 4)

        For higher dimensional sequences, the first axis corresponds
        to "subdevices", e.g. hydrological response units within
        different elements.  The 1-dimensional sequence |lland_fluxes.NKor|
        is logged for three elements with one, two, and three response
        units respectively, making up a sum of six subdevices:

        >>> ncvar = NetCDFVariableFlat('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     ncvar.log(element.model.sequences.fluxes.nkor, None)
        >>> ncvar.shape
        (6, 4)
        """
        return (sum(len(seq) for seq in self.sequences.values()),
                len(pub.timegrids.init))

    @property
    def array(self) -> numpy.ndarray:
        """The series data of all logged |IOSequence| objects contained in
        one single |numpy.ndarray| object.

        The documentation on |NetCDFVariableAgg.shape| explaines
        how |NetCDFVariableAgg.array| is structured.  The first
        examples confirms that the first axis corresponds to place,
        while the second one corresponds to time:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> ncvar = NetCDFVariableFlat('input_nied', isolate=False)
        >>> for element in elements:
        ...     nied1 = element.model.sequences.inputs.nied
        ...     ncvar.log(nied1, nied1.series)
        >>> ncvar.array
        array([[  0.,   1.,   2.,   3.],
               [  4.,   5.,   6.,   7.],
               [  8.,   9.,  10.,  11.]])

        Due to the flattening of higher dimensional sequences,
        their individual time series (e.g. of different hydrological
        response units) are spread over the rows of the array.
        For the 1-dimensional sequence |lland_fluxes.NKor|, the
        individual time series of the second element are stored
        in row two and three:

        >>> ncvar = NetCDFVariableFlat('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     nkor1 = element.model.sequences.fluxes.nkor
        ...     ncvar.log(nkor1, nkor1.series)
        >>> ncvar.array[1:3]
        array([[ 16.,  18.,  20.,  22.],
               [ 17.,  19.,  21.,  23.]])
        """
        array = numpy.full(self.shape, fillvalue, dtype=float)
        idx0 = 0
        idxs: List[Any] = [slice(None)]
        for seq, subarray in zip(self.sequences.values(),
                                 self.arrays.values()):
            for prod in self._product(seq.shape):
                array[idx0] = subarray[tuple(idxs + list(prod))]
                idx0 += 1
        return array

    @property
    def subdevicenames(self) -> Tuple[str, ...]:
        """A |tuple| containing the (sub)device names.

        Property |NetCDFVariableFlat.subdevicenames| clarifies which
        time series is stored in which row of|NetCDFVariableFlat.array|.
        The first examples confirms that for 0-dimensional series like
        |lland_inputs.Nied|, the plain device names are returned:

        >>> from hydpy.tests.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> ncvar = NetCDFVariableFlat('input_nied', isolate=False)
        >>> for element in elements:
        ...     nied1 = element.model.sequences.inputs.nied
        ...     ncvar.log(nied1, nied1.series)
        >>> ncvar.subdevicenames
        ('element1', 'element2', 'element3')

        For higher dimensional sequences like |lland_fluxes.NKor|
        an additional suffix in the individual name defines the
        index of the respective subdevice.  For example, the time
        series of the first hydrological response unit of the second
        element is stored in the third row:

        >>> ncvar = NetCDFVariableFlat('flux_nkor', isolate=False)
        >>> for element in elements:
        ...     nkor1 = element.model.sequences.fluxes.nkor
        ...     ncvar.log(nkor1, nkor1.series)
        >>> ncvar.subdevicenames[1:3]
        ('element2_0', 'element2_1')
        """
        stats: List[str] = collections.deque()
        for devicename, seq in self.sequences.items():
            if seq.NDIM:
                temp = devicename + '_'
                for prod in self._product(seq.shape):
                    stats.append(temp + '_'.join(str(idx) for idx in prod))
            else:
                stats.append(devicename)
        return tuple(stats)

    @staticmethod
    def _product(shape) -> Iterator[Tuple[int, ...]]:
        """Should return all "subdevice index combinations" for sequences
        with arbitrary dimensions:

        >>> from hydpy.core.netcdftools import NetCDFVariableFlat
        >>> _product = NetCDFVariableFlat.__dict__['_product'].__func__
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

    def read(self, ncfile, timegrid_data) -> None:
        """Read the data from the given NetCDF file.

        The argument `timegrid_data` defines the data period of the
        given NetCDF file.

        See the general documentation on class |NetCDFVariableFlat|
        for some examples.
        """
        array = query_variable(ncfile, self.name)[:]
        idxs: List[Any] = [slice(None)]
        subdev2index = self.query_subdevice2index(ncfile)
        for devicename, seq in self.sequences.items():
            subshape = [array.shape[1]] + list(seq.shape)
            subarray = numpy.empty(subshape)
            if seq.NDIM:
                temp = devicename + '_'
                for prod in self._product(seq.shape):
                    station = temp + '_'.join(str(idx) for idx in prod)
                    idx0 = subdev2index.get_index(station)
                    subarray[tuple(idxs+list(prod))] = array[idx0]
            else:
                subarray[:] = array[subdev2index.get_index(devicename)]
            seq.series = seq.adjust_series(timegrid_data, subarray)

    def write(self, ncfile) -> None:
        """Write the data to the given NetCDF file.

        See the general documentation on class |NetCDFVariableFlat|
        for some examples.
        """
        self.insert_subdevices(ncfile)
        create_variable(ncfile, self.name, 'f8', self.dimensions)
        ncfile[self.name][:] = self.array


autodoctools.autodoc_module()
