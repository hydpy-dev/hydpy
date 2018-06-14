# -*- coding: utf-8 -*-
"""This module implements features for handling the folder structure of
HydPy projects as well as loading data from and storing data to files.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import os
import runpy
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import netcdftools
from hydpy.core import objecttools
from hydpy.core import selectiontools
from hydpy.core import timetools


class _Directories(object):

    def __init__(self, *args, **kwargs):
        for arg in args:
            self.add(arg)
        for (key, value) in kwargs.items():
            self.add(key, value)

    def add(self, directory, path=None):
        """Add a directory and optionally its path."""
        if path is None:
            path = directory
        try:
            exec('self.%s = r"%s"' % (directory, path))
        except BaseException:
            raise IOError(
                'The directory name `%s` cannot be handled as a '
                'variable name.  Please avoid arithmetic operators '
                'like `-`, prefixed numbers...'
                % directory)

    def __iter__(self):
        for (key, value) in vars(self).items():
            yield (key, value)

    def __getitem__(self, key):
        return sorted(vars(self).values())[key]

    def __len__(self):
        return len(vars(self))

    def __repr__(self):
        if self:
            args, kwargs = [], []
            for key, value in self:
                if key == value:
                    args.append(key)
                else:
                    kwargs.append('%s=%s' % (key, value))
            lines = ['             %s,' % arg for arg in args+kwargs]
            lines[0] = '_Directories(' + lines[0][11:]
            lines[-1] = lines[-1][:-1] + ')'
            return '\n'.join(lines)
        return '_Directories()'

    def __dir__(self):
        return objecttools.dir_(self)


class FileManager(object):
    """Base class for the more specific file managers implemented in
    module |filetools|."""

    def __init__(self):
        self.check_exists = True
        self._isready = exceptiontools.IsReady(false=['projectdir'])
        self._BASEDIR = 'must_be_overwritten'
        self._projectdir = None
        if pub.projectname:
            self.projectdir = pub.projectname
        self._currentdir = None
        self._defaultdir = None
        self.createdirs = False
        self.deletedirs = False

    def _get_projectdir(self):
        return self._projectdir

    def _set_projectdir(self, name):
        self._projectdir = name

    def _del_projectdir(self):
        self._projectdir = None

    projectdir = exceptiontools.protected_property(
        'projectdir', _get_projectdir, _set_projectdir, _del_projectdir)

    @property
    def basepath(self):
        """Absolute path pointing to the actual directories."""
        return os.path.abspath(
            os.path.join(self.projectdir, self._BASEDIR))

    @property
    def availabledirs(self):
        """Available directories containing the respective files."""
        directories = _Directories()
        for directory in os.listdir(self.basepath):
            if not directory.startswith('_'):
                path = os.path.join(self.basepath, directory)
                if os.path.isdir(path):
                    directories.add(directory)
        return directories

    def _get_currentdir(self):
        """Current directory containing the network files."""
        directories = self.availabledirs
        if self._currentdir:
            directory = self._make_and_get_currentdir(
                directories, self._currentdir)
            if directory:
                return directory
            else:
                raise IOError(
                    'The base path `%s` does not contain the currently '
                    'set directory `%s` and creating a new directory is '
                    'currently disabled.'
                    % (self.basepath, self._currentdir))
        if self._defaultdir:
            directory = self._make_and_get_currentdir(
                directories, self._defaultdir)
        else:
            directory = None
        if directory:
            return directory
        else:
            raise IOError(
                'The base path `%s` does not contain the default directory '
                '`%s`.  Please specify he current directory to be worked '
                'with manually.'
                % (self.basepath, self._defaultdir))

    def _make_and_get_currentdir(self, directories, directory):
        try:
            return getattr(directories, directory)
        except AttributeError:
            if self.createdirs:
                path = os.path.join(self.basepath, directory)
                os.makedirs(path)
                return directory
            return None

    def _set_currentdir(self, directory):
        path = os.path.join(self.basepath, directory)
        if not os.path.exists(path):
            if self.createdirs:
                os.makedirs(path)
            elif self.check_exists:
                raise IOError(
                    'The base path `%s` does not contain directory `%s` '
                    'and creating a new directory is currently disabled.'
                    % (self.basepath, directory))
        self._currentdir = str(directory)

    def _del_currentdir(self):
        if self.deletedirs:
            path = os.path.join(self.basepath, self.currentdir)
            if os.path.exists(path):
                os.removedirs(path)
        self._currentdir = None

    currentdir = property(_get_currentdir, _set_currentdir, _del_currentdir)

    @property
    def currentpath(self):
        """Complete path of the directory containing the respective files."""
        return os.path.join(self.basepath, self.currentdir)

    @property
    def filenames(self):
        """Tuple of names of the respective files of the current directory."""
        return tuple(fn for fn in os.listdir(self.currentpath)
                     if (fn.endswith('.py') and not fn.startswith('_')))

    @property
    def filepaths(self):
        """Tuple of paths of the respective files of the current directory."""
        path = self.currentpath
        return tuple(os.path.join(path, name) for name in self.filenames)


class NetworkManager(FileManager):
    """Manager for network files."""

    def __init__(self):
        FileManager.__init__(self)
        self._BASEDIR = 'network'
        self._defaultdir = 'default'

    def load_files(self):
        """Load nodes and elements from all network files and return them in
        a |Selections| instance.  Each single network file defines a separate
        |Selection| instance.  Additionally, all |Element| and |Node| objects
        are bundled in a selection named `complete`.
        """
        selections = selectiontools.Selections()
        for (filename, path) in zip(self.filenames, self.filepaths):
            # Ensure both `Node` and `Element`start with a `fresh` memory.
            devicetools.Node.gather_new_nodes()
            devicetools.Element.gather_new_elements()
            try:
                info = runpy.run_path(path)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to load the network file `%s`'
                    % path)
            try:
                selections += selectiontools.Selection(
                    filename.split('.')[0],
                    info['Node'].gather_new_nodes(),
                    info['Element'].gather_new_elements())
            except KeyError as exc:
                raise KeyError(
                    'The class `%s` cannot be loaded from the network '
                    'file `%s`.  Please refer to the HydPy documentation '
                    'on how to prepare network files properly.'
                    % (exc.args[0], filename))
        selections += selectiontools.Selection(
            'complete',
            info['Node'].registered_nodes(),
            info['Element'].registered_elements())
        return selections

    def save_files(self, selections):
        """Save the nodes and elements from each |Selection| object contained
        within the given |Selections| instance to a separate network file of
        the same name.
        """
        try:
            currentpath = self.currentpath
            selections = selectiontools.Selections(selections)
            for selection in selections:
                if selection.name == 'complete':
                    continue
                path = os.path.join(currentpath, selection.name+'.py')
                selection.save(path=path, write_nodes=True)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to save selections `%s` into network files'
                % selections)

    def delete_files(self, selections):
        """Delete network files.  One or more filenames and/or |Selection|
        instances can serve as function arguments.
        """
        try:
            currentpath = self.currentpath
            for selection in selections:
                name = str(selection)
                if name == 'complete':
                    continue
                if not name.endswith('.py'):
                    name += '.py'
                path = os.path.join(currentpath, name)
                os.remove(path)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to remove the network files of selections `%s`'
                % selections)

    def __dir__(self):
        return objecttools.dir_(self)


class ControlManager(FileManager):
    """Manager for control parameter files."""

    # The following file path to content mapping is used to circumvent reading
    # the same auxiliary control parameter file from disk multiple times.
    _registry = {}
    _workingpath = '.'

    def __init__(self):
        FileManager.__init__(self)
        self._BASEDIR = 'control'
        self._defaultdir = 'default'

    def load_file(self, element=None, filename=None, clear_registry=True):
        """Return the namespace of the given file (and eventually of its
        corresponding auxiliary subfiles) as a |dict|.

        By default, the internal registry is cleared when a control file and
        all its corresponding auxiliary files have been loaded.  You can
        change this behaviour by passing `False` for the `clear_registry`
        argument.  This might decrease model initialization times
        significantly.  But then it is your own responsibility to call
        method |ControlManager.clear_registry| when necessary (before
        reloading a changed control file).
        """
        if not filename:
            filename = element.name
        type(self)._workingpath = self.currentpath
        info = {}
        if element:
            info['element'] = element
        try:
            self.read2dict(filename, info)
        finally:
            type(self)._workingpath = '.'
            if clear_registry:
                self._registry.clear()
        return info

    @classmethod
    def read2dict(cls, filename, info):
        """Read the control parameters from the given path (and its
        auxiliary paths, where appropriate) and store them in the given
        |dict| object `info`.

        Note that the |dict| `info` can be used to feed information
        into the execution of control files.  Use this method only if you
        are completely sure on how the control parameter import of HydPy
        works.  Otherwise, you should most probably prefer to use
        |ControlManager.load_file|.
        """
        if not filename.endswith('.py'):
            filename += '.py'
        path = os.path.join(cls._workingpath, filename)
        try:
            if path not in cls._registry:
                with open(path) as file_:
                    cls._registry[path] = file_.read()
            exec(cls._registry[path], {}, info)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to load the control file `%s`'
                % path)
        if 'model' not in info:
            raise IOError(
                'Model parameters cannot be loaded from control file `%s`.  '
                'Please refer to the HydPy documentation on how to prepare '
                'control files properly.'
                % path)

    @classmethod
    def clear_registry(cls):
        """Clear the internal registry of read control files.
        """
        cls._registry.clear()

    def save_file(self, filename, text):
        """Save the given text under the given control filename and the
        current path."""
        if not filename.endswith('.py'):
            filename += '.py'
        path = os.path.join(self.currentpath, filename)
        with open(path, 'w', encoding="utf-8") as file_:
            file_.write(text)


class ConditionManager(FileManager):
    """Manager for condition files."""

    def __init__(self):
        FileManager.__init__(self)
        self._BASEDIR = 'conditions'
        self._defaultdir = None

    def load_file(self, filename):
        """Read and return the content of the given file.

        If the current directory is not defined explicitly, the directory
        name is constructed with the actual simulation start date.  If
        such an directory does not exist, it is created immediately.
        """
        _defaultdir = self._defaultdir
        try:
            if not filename.endswith('.py'):
                filename += '.py'
            try:
                self._defaultdir = (
                    'init_' + pub.timegrids.sim.firstdate.string('os'))
            except AttributeError:
                pass
            filepath = os.path.join(self.currentpath, filename)
            with open(filepath) as file_:
                return file_.read()
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to read the conditions file `%s`'
                % filename)
        finally:
            self._defaultdir = _defaultdir

    def save_file(self, filename, text):
        """Save the given text under the given condition filename and the
        current path.

        If the current directory is not defined explicitly, the directory
        name is constructed with the actual simulation end date.  If
        such an directory does not exist, it is created immediately.
        """
        _defaultdir = self._defaultdir
        try:
            if not filename.endswith('.py'):
                filename += '.py'
            try:
                self._defaultdir = (
                    'init_' + pub.timegrids.sim.lastdate.string('os'))
            except AttributeError:
                pass
            path = os.path.join(self.currentpath, filename)
            with open(path, 'w', encoding="utf-8") as file_:
                file_.write(text)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to write the conditions file `%s`'
                % filename)
        finally:
            self._defaultdir = _defaultdir


class _Context(object):

    def __init__(self, name, default):
        self.default = default
        self.attrname = '_%s_value' % name

    def get_value(self, obj):
        value = getattr(obj, self.attrname, None)
        return self.default if (value is None) else value

    def set_value(self, obj, value):
        setattr(obj, self.attrname, value)

    def del_value(self, obj):
        setattr(obj, self.attrname, None)


class _ContextDir(_Context):

    def __init__(self, name, default, sequence_type):
        _Context.__init__(self, name, default)
        self.sequence_type = sequence_type
        self.__doc__ = (
            'Current directory containing the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        try:
            obj.currentdir = self.get_value(obj)
            return obj._currentdir
        except IOError:
            objecttools.augment_excmessage(
                'While trying to get the %s sequence directory'
                % self.sequence_type)
        finally:
            obj._currentdir = None

    def __set__(self, obj, directory):
        try:
            obj.currentdir = directory
            self.set_value(obj, directory)
        except IOError:
            objecttools.augment_excmessage(
                'While trying to set the %s sequence directory'
                % self.sequence_type)
        finally:
            obj._currentdir = None

    def __delete__(self, obj):
        try:
            obj.currentdir = self.get_value(obj)
            del obj.currentdir
        except IOError:
            objecttools.augment_excmessage(
                'While trying to delete the input sequence directory')
        finally:
            self.del_value(obj)


class _ContextType(_Context):

    def __init__(self, name, default, sequence_type):
        _Context.__init__(self, name, default)
        self.__doc__ = (
            'Currently selected type of the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return self.get_value(obj)

    def __set__(self, obj, value):
        value = str(value)
        if value in obj._supportedmodes:
            self.set_value(obj, value)
        else:
            raise ValueError(
                'The given sequence file type `%s` is not implemented.  '
                'Please choose one of the following file types: %s.'
                % (value, objecttools.enumeration(obj._supportedmodes)))


class _ContextOverwrite(_Context):

    def __init__(self, name, default, sequence_type):
        _Context.__init__(self, name, default)
        self.__doc__ = (
            'Currently selected overwrite flag of the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return self.get_value(obj)

    def __set__(self, obj, value):
        self.set_value(obj, value)


class _ContextPath(_Context):

    def __init__(self, name, sequence_dir, sequence_type):
        _Context.__init__(self, name, None)
        self.sequence_dir = sequence_dir
        self.sequence_type = sequence_type
        self.__doc__ = (
            'Path of the %s sequence directory.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        value = self.get_value(obj)
        if value is None:
            return os.path.join(obj.basepath, getattr(obj, self.sequence_dir))
        return value

    def __set__(self, obj, path):
        path = str(path)
        abspath = os.path.abspath(path)
        if os.path.exists(abspath):
            self.set_value(obj, path)
        elif obj.createdirs:
            os.makedirs(abspath)
            self.set_value(obj, path)
        elif obj.check_exists:
            raise IOError(
                'The %s sequence path `%s` does not exist.'
                % (self.sequence_type, abspath))
        else:
            self.set_value(obj, path)

    def __delete__(self, obj):
        self.del_value(obj)


class SequenceManager(FileManager):
    """Manager for sequence files.

    Usually, there is only one |SequenceManager| used within each HydPy
    project, stored in module |pub|.  This object is responsible for the
    actual I/O tasks related to |IOSequence| objects.

    In complete HydPy project, the |SequenceManager| object is often not
    used directly by the user, except if one wishes to load data from or
    store data to directories that differ from the default settings.
    In the following examples, we partially set up a project manually,
    and show the basic features of class |SequenceManager|.

    Firstly, we define project called `test_project`, set a short time
    period and prepare a |SequenceManager| object:

    >>> from hydpy import pub, Timegrids, Timegrid
    >>> pub.projectname = 'test_project'
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '05.01.2000',
    ...                                    '1d'))
    >>> from hydpy.core.filetools import SequenceManager
    >>> pub.sequencemanager = SequenceManager()

    Allowing the |SequenceManager| object to create missing directories
    is not default, but more convenient for the following examples:

    >>> pub.sequencemanager.createdirs = True

    Secondly, we prepare an 0-dimensional |IOSequence| object called
    `test_sequence` and assign a small time series to it:

    >>> from hydpy.core.sequencetools import IOSequence
    >>> seq = IOSequence()
    >>> seq.NDIM = 0
    >>> seq.rawfilename = 'test_sequence'
    >>> seq.activate_ram()
    >>> seq.series = 1.0, 2.0, 3.0, 4.0

    Now we can store this time series in an ASCII file:

    >>> seq.filetype_ext = 'asc'
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.save_file(seq)

    To check that this was actually successful, be can load the file
    content from the standard output directory and print it:

    >>> import os
    >>> path = os.path.join(
    ...     'test_project', 'sequences', 'output', 'test_sequence.asc')
    >>> with TestIO():
    ...     with open(path) as file_:
    ...         print(file_.read().strip())
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    1.000000000000000000e+00
    2.000000000000000000e+00
    3.000000000000000000e+00
    4.000000000000000000e+00

    To show that reloading the data works, we first set the values of
    the internal time series of the |IOSequence| object to zero:

    >>> seq.series = 0.
    >>> seq.series
    array([ 0.,  0.,  0.,  0.])
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(seq)
    >>> seq.series
    array([ 1.,  2.,  3.,  4.])

    Badly formated ASCII files should result in clear error messages:

    >>> with TestIO():
    ...     with open(path) as file_:
    ...         right = file_.read()
    ...     wrong = right.replace('Timegrid', 'timegrid')
    ...     with open(path, 'w') as file_:
    ...         _ = file_.write(wrong)
    >>> with TestIO(clear_all=True):
    ...     pub.sequencemanager.load_file(seq)
    Traceback (most recent call last):
    ...
    NameError: While trying to load the external data of sequence \
`iosequence`, the following error occured: name 'timegrid' is not defined

    Another option is to store data using |numpy| binary files, which
    is a good option for saving computation times, but a bad option for
    sharing data with collegues:

    >>> seq.filetype_ext = 'npy'
    >>> with TestIO():
    ...     pub.sequencemanager.save_file(seq)

    The data time period information is stored without time zone information
    within the first thirteen entries:

    >>> path = os.path.join(
    ...     'test_project', 'sequences', 'output', 'test_sequence.npy')
    >>> from hydpy import numpy, print_values
    >>> with TestIO():
    ...     print_values(numpy.load(path))
    2000.0, 1.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 1.0, 5.0, 0.0, 0.0, 0.0,
    86400.0, 1.0, 2.0, 3.0, 4.0

    Reloading the data works as expected:

    >>> seq.series = 0.
    >>> seq.series
    array([ 0.,  0.,  0.,  0.])
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(seq)
    >>> seq.series
    array([ 1.,  2.,  3.,  4.])

    In the ASCII example, an example error messages for loading data
    was shown.  Here is an example for saving data:

    >>> seq.deactivate_ram()
    >>> with TestIO(clear_all=True):
    ...     pub.sequencemanager.save_file(seq)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to save the external data of sequence \
`iosequence`, the following error occured: Sequence `iosequence` is not \
requested to make any internal data available to the user.

    The third option to store data in netCDF files, which is explained
    separately in the documentation on class |NetCDFInterface|.
    """

    _supportedmodes = ('npy', 'asc', 'nc')

    inputdir = _ContextDir('inputdir', 'input', 'input')
    outputdir = _ContextDir('outputdir', 'output', 'output')
    nodedir = _ContextDir('nodedir', 'node', 'node')
    tempdir = _ContextDir('tempdir', 'temp', 'temporary')

    inputfiletype = _ContextType('inputfiletype', 'npy', 'input')
    outputfiletype = _ContextType('outputfiletype', 'npy', 'output')
    nodefiletype = _ContextType('nodefiletype', 'npy', 'node')
    tempfiletype = _ContextType('tempfiletype', 'npy', 'temporary')

    inputoverwrite = _ContextOverwrite('inputoverwrite', False, 'input')
    outputoverwrite = _ContextOverwrite('outputoverwrite', False, 'output')
    simoverwrite = _ContextOverwrite('simoverwrite', False, 'sim node')
    obsoverwrite = _ContextOverwrite('obsoverwrite', False, 'obs node')
    tempoverwrite = _ContextOverwrite('tempoverwrite', False, 'temporary')

    inputpath = _ContextPath('inputpath', 'inputdir', 'input')
    outputpath = _ContextPath('outputpath', 'outputdir', 'output')
    nodepath = _ContextPath('nodepath', 'nodedir', 'node')
    temppath = _ContextPath('temppath', 'tempdir', 'temporary')

    def __init__(self):
        FileManager.__init__(self)
        self._BASEDIR = 'sequences'
        self._defaultdir = None
        self.netcdf_reader = None
        self.netcdf_writer = None

    def new_netcdf(self):
        pass

    def load_file(self, sequence):
        """Load data from an "external" data file an pass it to
        the given |IOSequence|."""
        try:
            if sequence.filetype_ext == 'npy':
                sequence.series = sequence.adjust_series(
                    *self._load_npy(sequence))
            elif sequence.filetype_ext == 'asc':
                sequence.series = sequence.adjust_series(
                    *self._load_asc(sequence))
            elif sequence.filetype_ext == 'nc':
                self._load_nc(sequence)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to load the external data of sequence %s'
                % objecttools.devicephrase(sequence))

    @staticmethod
    def _load_npy(sequence):
        data = numpy.load(sequence.filepath_ext)
        timegrid_data = timetools.Timegrid.from_array(data)
        return timegrid_data, data[13:]

    @staticmethod
    def _load_asc(sequence):
        with open(sequence.filepath_ext) as file_:
            header = '\n'.join([file_.readline() for idx in range(3)])
        timegrid_data = eval(header, {}, {'Timegrid': timetools.Timegrid})
        values = numpy.loadtxt(
            sequence.filepath_ext, skiprows=3, ndmin=sequence.NDIM+1)
        return timegrid_data, values

    def _load_nc(self, sequence):
        try:
            self.netcdf_reader.log(sequence)
        except AttributeError:
            raise RuntimeError(
                'to do')

    def save_file(self, sequence):
        """Write the date stored in |IOSequence.series| of the given
        |IOSequence| into an "external" data file. """
        try:
            if sequence.filetype_ext == 'npy':
                self._save_npy(sequence)
            elif sequence.filetype_ext == 'asc':
                self._save_asc(sequence)
            elif sequence.filetype_ext == 'nc':
                self._save_nc(sequence)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to save the external data of sequence %s'
                % objecttools.devicephrase(sequence))

    @staticmethod
    def _save_npy(sequence):
        series = pub.timegrids.init.array2series(sequence.series)
        numpy.save(sequence.filepath_ext, series)

    @staticmethod
    def _save_asc(sequence):
        with open(sequence.filepath_ext, 'w') as file_:
            file_.write(
                pub.timegrids.init.assignrepr(
                    prefix='',
                    style='iso2',
                    utcoffset=pub.options.utcoffset) + '\n')
        with open(sequence.filepath_ext, 'ab') as file_:
            numpy.savetxt(file_, sequence.series, delimiter='\t')

    def _save_nc(self, sequence):
        try:
            self.netcdf_writer.log(sequence)
        except AttributeError:
            raise RuntimeError(
                'to do')

    def open_netcdf_reader(self):
        self.netcdf_reader = netcdftools.NetCDFInterface()

    def close_netcdf_reader(self):
        self.netcdf_reader.read()
        self.netcdf_reader = None

    def open_netcdf_writer(self):
        self.netcdf_writer = netcdftools.NetCDFInterface()

    def close_netcdf_writer(self):
        self.netcdf_writer.write()
        self.netcdf_writer = None

    def __dir__(self):
        return objecttools.dir_(self)


autodoctools.autodoc_module()
