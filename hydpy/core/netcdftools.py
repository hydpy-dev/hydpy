# -*- coding: utf-8 -*-
"""This module extends the features of module |filetools| for loading data
from and storing data to netCDF4 files, consistent with the `NetCDF Climate
and Forecast (CF) Metadata Conventions <http://cfconventions.org/Data/
cf-conventions/cf-conventions-1.7/cf-conventions.html>`_
"""
# import...
# ...from standard library
from __future__ import division, print_function
import collections
import os
# ...from site-packages
import numpy
from hydpy import netcdf4
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import timetools


class NetCDFInterface(object):
    """Interface between |SequenceManager| and multiple NetCDF files.

    Either for reading data from multiple NetCDF files and assigning it
    to multiple |IOSequence| objects, or for retrieving data from multiple
    |IOSequence| objects and storing it to multiple NetCDF files, an
    |NetCDFInterface| object is initialized temporarily.  Usually, this
    is done through applying class |SequenceManager| in three steps:

      1. Call either method |SequenceManager.open_netcdf_reader| or method
         |SequenceManager.open_netcdf_writer| to prepare a |NetCDFInterface|
         object for reading or writing.
      2. Call either the usual reading or writing methods of other HydPy
         classes (e.g. method |HydPy.prepare_inputseries| of class |HydPy|
         or method |Elements.save_stateseries| of class |Elements|).
         The reading or writing processes of all |IOSequence| objects with
         property |IOSequence.filetype_ext| set to `nc` are essentially
         performed by the prepared |NetCDFInterface| object.
      3. Finalizes reading or writing by calling either method
         |SequenceManager.close_netcdf_reader| or method
         |SequenceManager.close_netcdf_writer|.

    Step 2 is actually a logging process only, telling the |NetCDFInterface|
    object which data needs to be read or written.  The actual reading from
    or writing of NetCDF files is triggered by step 3.

    During step 2, the |NetCDFInterface| object is accessible, allowing
    to inspect is current state or to modify its behaviour.

    The |NetCDFInterface| object delegates the task to manage the sequences
    of individual application models to different |NetCDFFile| objects.
    Each |NetCDFFile| object is responsible for one type of application
    model (e.g. |lland_v1| or |dam_v002|) and one NetCDF file.  Furthermore,
    each |NetCDFFile| object delegates handling different sequences to
    different |NetCDFVariable| objects.  Each |NetCDFVariable| object is
    responsible for one type of sequence (e.g. |lland_inputs.Nied| of
    |lland| or |dam_states.WaterVolume| of |dam|) and one NetCDF variable.


    >>> from hydpy import pub, Timegrids, Timegrid
    >>> pub.options.printprogress = False
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '05.01.2000',
    ...                                    '1d'))
    >>> from hydpy import Node, Nodes, Element, Elements, prepare_model
    >>> n1 = Node('n1')
    >>> n2 = Node('n2', variable='T')
    >>> ns = Nodes(n1, n2)
    >>> e1 = Element('e1', outlets=n1)
    >>> e2 = Element('e2', outlets=n1)
    >>> e3 = Element('e3', outlets=n1)
    >>> es = Elements(e1, e2, e3)
    >>> from hydpy.models import lland_v1, lland_v2
    >>> e1.connect(prepare_model(lland_v1))
    >>> e2.connect(prepare_model(lland_v1))
    >>> e3.connect(prepare_model(lland_v2))

    >>> e1.model.parameters.control.nhru(1)
    >>> e2.model.parameters.control.nhru(2)
    >>> e3.model.parameters.control.nhru(3)
    >>> es.prepare_fluxseries()
    >>> es.prepare_stateseries()

    >>> import numpy
    >>> e1.model.sequences.fluxes.nkor.series = (
    ...     numpy.arange(0, 4).reshape((4, 1)))
    >>> e2.model.sequences.fluxes.nkor.series = (
    ...     numpy.arange(4, 12).reshape((4, 2)))
    >>> e3.model.sequences.states.bowa.series = (
    ...     numpy.arange(12, 24).reshape((4, 3)))

    >>> from hydpy.core.filetools import SequenceManager
    >>> pub.sequencemanager = SequenceManager()
    >>> pub.sequencemanager.outputfiletype = 'nc'
    >>> pub.sequencemanager.open_netcdf_writer()
    >>> es.save_allseries()
    >>> ns.save_allseries()

    >>> nc = pub.sequencemanager.netcdf_writer
    >>> nc.lland_v1.nkor_fluxes.devicenames
    ('e1', 'e2')
    >>> nc.lland_v1.nkor_fluxes.array[0]
    array([[   0., -999.],
           [   1., -999.],
           [   2., -999.],
           [   3., -999.]])
    >>> nc.lland_v1.nkor_fluxes.array[1]
    array([[  4.,   5.],
           [  6.,   7.],
           [  8.,   9.],
           [ 10.,  11.]])

    >>> nc.lland_v2.bowa_states.devicenames
    ('e3',)
    >>> nc.lland_v2.bowa_states.array[0]
    array([[ 12.,  13.,  14.],
           [ 15.,  16.,  17.],
           [ 18.,  19.,  20.],
           [ 21.,  22.,  23.]])

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.nodepath = ''
    ...     pub.sequencemanager.outputpath = ''
    ...     pub.sequencemanager.close_netcdf_writer()

    >>> from hydpy import netcdf4
    >>> with TestIO():
    ...    v1 = netcdf4.Dataset('lland_v1.nc', 'r')
    ...    v2 = netcdf4.Dataset('lland_v2.nc', 'r')

    >>> for chars in v1['devices'][:]:
    ...     print(''.join(char.decode('utf-8') for char in chars))
    e1
    e2
    >>> numpy.array(v1['nkor_fluxes'][:][0])
    array([[   0., -999.],
           [   1., -999.],
           [   2., -999.],
           [   3., -999.]])

    >>> numpy.array(v1['nkor_fluxes'][:][1])
    array([[  4.,   5.],
           [  6.,   7.],
           [  8.,   9.],
           [ 10.,  11.]])

    >>> for chars in v2['devices'][:]:
    ...     print(''.join(char.decode('utf-8') for char in chars))
    e3
    >>> numpy.array(v2['bowa_states'][:][0])
    array([[ 12.,  13.,  14.],
           [ 15.,  16.,  17.],
           [ 18.,  19.,  20.],
           [ 21.,  22.,  23.]])


    >>> e1.model.sequences.fluxes.nkor.series = 0.0
    >>> e2.model.sequences.fluxes.nkor.series = 0.0
    >>> e3.model.sequences.states.bowa.series = 0.0

    >>> with TestIO():
    ...     pub.sequencemanager.open_netcdf_reader()
    ...     es.prepare_fluxseries(use_ext=True)
    ...     es.prepare_stateseries(use_ext=True)

    >>> e1.model.sequences.fluxes.nkor.series
    array([[ 0.],
           [ 0.],
           [ 0.],
           [ 0.]])
    >>> e2.model.sequences.fluxes.nkor.series
    array([[ 0.,  0.],
           [ 0.,  0.],
           [ 0.,  0.],
           [ 0.,  0.]])
    >>> e3.model.sequences.states.bowa.series
    array([[ 0.,  0.,  0.],
           [ 0.,  0.,  0.],
           [ 0.,  0.,  0.],
           [ 0.,  0.,  0.]])


    >>> pub.sequencemanager.inputpath = ''
    >>> with TestIO():
    ...     pub.sequencemanager.close_netcdf_reader()

    >>> e1.model.sequences.fluxes.nkor.series
    array([[ 0.],
           [ 1.],
           [ 2.],
           [ 3.]])
    >>> e2.model.sequences.fluxes.nkor.series
    array([[  4.,   5.],
           [  6.,   7.],
           [  8.,   9.],
           [ 10.,  11.]])
    >>> e3.model.sequences.states.bowa.series
    array([[ 12.,  13.,  14.],
           [ 15.,  16.,  17.],
           [ 18.,  19.,  20.],
           [ 21.,  22.,  23.]])


    >>> TestIO.clear()
    """

    def __init__(self):
        self._slaves = collections.OrderedDict()

    def log(self, sequence):
        if isinstance(sequence, abctools.ModelIOSequenceABC):
            descr = sequence.descr_model
        else:
            descr = 'node'
        if descr in self._slaves:
            slave = self._slaves[descr]
        else:
            slave = NetCDFFile(name=descr)
            self._slaves[descr] = slave
        slave.log(sequence)

    def read(self):
        for slave in self._slaves.values():
            slave.read()

    def write(self):
        init = pub.timegrids.init
        timeunits = init.firstdate.to_cfunits('hours')
        timepoints = init.to_timepoints('hours')
        for slave in self._slaves.values():
            slave.write(timeunits, timepoints)

    def __getattr__(self, name):
        try:
            return self._slaves[name]
        except KeyError:
            raise AttributeError(
                'to do')

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __dir__(self):
        return objecttools.dir_(self) + list(self._slaves.keys())


class NetCDFFile(object):
    """Handles one NetCDF file.

    >>> from hydpy.core.netcdftools import NetCDFFile
    >>> nc = NetCDFFile('node')
    >>> from hydpy import dummies
    >>> dummies.nc = nc
    """

    def __init__(self, name):
        self.name = name
        self._slaves = collections.OrderedDict()

    def log(self, sequence):
        descr = sequence.descr_sequence
        if descr in self._slaves:
            slave = self._slaves[descr]
        else:
            slave = NetCDFVariable(name=descr)
            self._slaves[descr] = slave
        slave.log(sequence)

    @property
    def filepath_read(self):
        """
        >>> from hydpy import pub, dummies, TestIO
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()
        >>> pub.sequencemanager.createdirs = True
        >>> with TestIO():
        ...     pub.sequencemanager.nodepath = 'testpath1'
        ...     pub.sequencemanager.inputpath = 'testpath2'
        >>> nc = dummies.nc
        >>> from hydpy import repr_
        >>> repr_(nc.filepath_read)
        'testpath1/node.nc'

        >>> nc.name = 'lland_v1'
        >>> repr_(nc.filepath_read)
        'testpath2/lland_v1.nc'

        >>> TestIO.clear()
        >>> del pub.sequencemanager.nodepath
        >>> del pub.sequencemanager.inputpath
        """
        return self._filepath(read=True)

    @property
    def filepath_write(self):
        """
        >>> from hydpy import pub, dummies, TestIO
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()
        >>> pub.sequencemanager.createdirs = True
        >>> with TestIO():
        ...     pub.sequencemanager.nodepath = 'testpath3'
        ...     pub.sequencemanager.outputpath = 'testpath4'
        >>> nc = dummies.nc
        >>> from hydpy import repr_
        >>> repr_(nc.filepath_write)
        'testpath3/node.nc'

        >>> nc.name = 'lland_v1'
        >>> repr_(nc.filepath_write)
        'testpath4/lland_v1.nc'

        >>> TestIO.clear()
        >>> del pub.sequencemanager.nodepath
        >>> del pub.sequencemanager.outputpath
        """
        return self._filepath(read=False)

    def _filepath(self, read):
        if self.name == 'node':
            path = pub.sequencemanager.nodepath
        else:
            if read:
                path = pub.sequencemanager.inputpath
            else:
                path = pub.sequencemanager.outputpath
        return os.path.join(path, self.name+'.nc')

    def read(self):
        with netcdf4.Dataset(self.filepath_read, "r") as rootgroup:
            timepoints = rootgroup['timepoints']
            refdate = timetools.Date.from_cfunits(timepoints.units)
            timegrid = timetools.Timegrid.from_timepoints(
                timepoints=timepoints[:],
                refdate=refdate,
                unit=timepoints.units.strip().split()[0])
            devicename2index = self.devicename2index(rootgroup)
            for slave in self._slaves.values():
                slave.read(rootgroup, timegrid, devicename2index)

    def write(self, timeunit, timepoints):
        devicechars = list(self._slaves.values())[0].devicechars
        with netcdf4.Dataset(self.filepath_write, "w") as rootgroup:
            rootgroup.createDimension(
                'nmb_timepoints', len(timepoints))
            rootgroup.createDimension(
                'nmb_devices', devicechars.shape[0])
            rootgroup.createDimension(
                'nmb_chars', devicechars.shape[1])
            var_t = rootgroup.createVariable(
                'timepoints', 'f8', ('nmb_timepoints',))
            var_d = rootgroup.createVariable(
                'devices', 'S1', ('nmb_devices', 'nmb_chars'))
            var_t[:] = timepoints
            var_t.units = timeunit
            var_d[:, :] = devicechars
            for slave in self._slaves.values():
                slave.write(rootgroup)

    @staticmethod
    def devicename2index(rootgroup):
        d2i = {}
        for idx, chars in enumerate(rootgroup['devices'][:]):
            name = ''.join(char.decode('utf-8') for char in chars)
            d2i[name] = idx
        return d2i

    @property
    def sequencenames(self):
        return tuple(self._slaves.keys())

    def __getattr__(self, name):
        try:
            return self._slaves[name]
        except KeyError:
            raise AttributeError(
                'to do ' + name)

    __copy__ = objecttools.copy_
    __deepcopy__ = objecttools.deepcopy_

    def __dir__(self):
        return objecttools.dir_(self) + list(self.sequencenames)


class NetCDFVariable(object):
    """Handles a NetCDF variable.


    >>> from hydpy.core.netcdftools import NetCDFVariable
    >>> nc = NetCDFVariable('temperature')
    >>> from hydpy.core.sequencetools import IOSequence
    >>> import numpy
    >>> class Zeros(object):
    ...     name = 'zeros'
    ...     series = numpy.zeros((4,2))
    ...     shape = (2,)
    >>> class Ones(object):
    ...     name = 'ones'
    ...     series = numpy.ones((4,3))
    ...     shape = (3,)
    >>> from collections import OrderedDict
    >>> nc._slaves = OrderedDict(
    ...     [('zeros', Zeros()),
    ...      ('ones', Ones())])
    >>> from hydpy import dummies
    >>> dummies.nc = nc
    """

    def __init__(self, name):
        self.name = name
        self._slaves = collections.OrderedDict()

    def log(self, sequence):
        self._slaves[sequence.descr_device] = sequence

    def read(self, rootgroup, timegrid_data, devicename2index):
        array = rootgroup[self.name][:]
        for devicename, sequence in self._slaves.items():
            idx = devicename2index[devicename]
            values = array[self._get_slices(idx, sequence)]
            sequence.series = sequence.adjust_series(timegrid_data, values)

    def write(self, rootgroup):
        dimensions = self.dimensions
        array = self.array
        for dimension, length in zip(dimensions[2:], array.shape[2:]):
            rootgroup.createDimension(dimension, length)
        var = rootgroup.createVariable(self.name, 'f8', dimensions)
        var[:] = array

    @property
    def shape(self):
        """
        >>> from hydpy import dummies
        >>> dummies.nc.shape
        (2, 4, 3)
        """
        maxshape = collections.deque()
        for sequence in self._slaves.values():
            maxshape.append(sequence.series.shape)
        shape = [len(self._slaves)] + list(numpy.max(maxshape, axis=0))
        return tuple(shape)

    @property
    def array(self):
        """
        >>> from hydpy import dummies
        >>> dummies.nc.array
        array([[[   0.,    0., -999.],
                [   0.,    0., -999.],
                [   0.,    0., -999.],
                [   0.,    0., -999.]],
        <BLANKLINE>
               [[   1.,    1.,    1.],
                [   1.,    1.,    1.],
                [   1.,    1.,    1.],
                [   1.,    1.,    1.]]])
        """
        array = numpy.full(self.shape, -999., dtype=float)
        for idx, sequence in enumerate(self._slaves.values()):
            array[self._get_slices(idx, sequence)] = sequence.series
        return array

    @staticmethod
    def _get_slices(idx, sequence):
        slices = [idx, slice(None)]
        for length in sequence.shape:
            slices.append(slice(0, length))
        return slices

    @property
    def dimensions(self):
        """
        >>> from hydpy import dummies
        >>> dummies.nc.dimensions
        ('nmb_devices', 'nmb_timepoints', 'nmb_temperature_axis3')
        """
        dimensions = ['nmb_devices', 'nmb_timepoints']
        for idx, length in enumerate(self.shape[2:]):
            dimensions.append('nmb_%s_axis%d' % (self.name, idx+3))
        return tuple(dimensions)

    @property
    def devicenames(self):
        return tuple(self._slaves.keys())

    @property
    def devicechars(self):
        """|numpy.ndarray| containing the byte characters (second axis)
        of all current device names (first axis).

        >>> from hydpy import dummies
        >>> print(repr(dummies.nc.devicechars).replace('b', ''))
        array([['z', 'e', 'r', 'o', 's'],
               ['o', 'n', 'e', 's', '']],
              dtype='|S1')
        """
        maxlen = 0
        devicenames = self.devicenames
        for name in devicenames:
            maxlen = max(maxlen, len(name))
        chars = numpy.full(
            (len(devicenames), maxlen), b'', dtype='|S1')
        for idx, name in enumerate(self.devicenames):
            for jdx, char in enumerate(name):
                chars[idx, jdx] = char.encode('utf-8')
        return chars


autodoctools.autodoc_module()
