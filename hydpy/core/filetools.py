# -*- coding: utf-8 -*-
"""This module implements features for handling the folder structure of
HydPy projects as well as loading data from and storing data to files.
"""
# import...
# ...from standard library
import os
import runpy
import weakref
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
        objecttools.valid_variable_identifier(directory)
        if path is None:
            path = directory
        setattr(self, directory, path)

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

    _BASEDIR = 'must_be_overwritten'

    def __init__(self):
        self.check_exists = True
        self._projectdir = None
        if pub.projectname:
            self.projectdir = pub.projectname
        self._currentdir = None
        self._defaultdir = None
        self.createdirs = False
        self.deletedirs = False

    projectdir = exceptiontools.ProtectedProperty(name='projectdir')

    @projectdir.getter
    def projectdir(self):
        return self._projectdir

    @projectdir.setter
    def projectdir(self, name):
        self._projectdir = name

    @projectdir.deleter
    def projectdir(self):
        self._projectdir = None

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

    @property
    def currentdir(self):
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

    @currentdir.setter
    def currentdir(self, directory):
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

    @currentdir.deleter
    def currentdir(self):
        if self.deletedirs:
            path = os.path.join(self.basepath, self.currentdir)
            if os.path.exists(path):
                os.removedirs(path)
        self._currentdir = None

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

    _BASEDIR = 'network'

    def __init__(self):
        FileManager.__init__(self)
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
    _BASEDIR = 'control'

    def __init__(self):
        FileManager.__init__(self)
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

    _BASEDIR = 'conditions'

    def __init__(self):
        FileManager.__init__(self)
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


class _Descriptor(object):

    def __init__(self, default):
        self.default = default
        self.obj2value = weakref.WeakKeyDictionary()

    def get_value(self, obj):
        """Get the value from the given object and return it."""
        return self.obj2value.get(obj, self.default)

    def set_value(self, obj, value):
        """Assign the given value to the given object."""
        self.obj2value[obj] = value

    def del_value(self, obj):
        """Delete the value from the given object."""
        del self.obj2value[obj]


class _DescriptorDir(_Descriptor):

    def __init__(self, default, sequence_type):
        _Descriptor.__init__(self, default)
        self.sequence_type = sequence_type
        self.__doc__ = (
            'Current directory containing the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        try:
            obj.currentdir = self.get_value(obj)
            return getattr(obj, '_currentdir')
        except IOError:
            objecttools.augment_excmessage(
                'While trying to get the %s sequence directory'
                % self.sequence_type)
        finally:
            setattr(obj, '_currentdir', None)

    def __set__(self, obj, directory):
        try:
            obj.currentdir = directory
            self.set_value(obj, directory)
        except IOError:
            objecttools.augment_excmessage(
                'While trying to set the %s sequence directory'
                % self.sequence_type)
        finally:
            setattr(obj, '_currentdir', None)

    def __delete__(self, obj):
        try:
            obj.currentdir = self.get_value(obj)
            del obj.currentdir
        except IOError:
            objecttools.augment_excmessage(
                'While trying to delete the input sequence directory')
        finally:
            self.del_value(obj)


class _DescriptorType(_Descriptor):

    def __init__(self, default, sequence_type):
        _Descriptor.__init__(self, default)
        self.__doc__ = (
            'Currently selected type of the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return self.get_value(obj)

    def __set__(self, obj, value):
        value = str(value)
        if value in obj.SUPPORTED_MODES:
            self.set_value(obj, value)
        else:
            raise ValueError(
                'The given sequence file type `%s` is not implemented.  '
                'Please choose one of the following file types: %s.'
                % (value, objecttools.enumeration(obj.SUPPORTED_MODES)))


class _DescriptorOverwrite(_Descriptor):

    def __init__(self, default, sequence_type):
        _Descriptor.__init__(self, default)
        self.__doc__ = (
            'Currently selected overwrite flag of the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return self.get_value(obj)

    def __set__(self, obj, value):
        self.set_value(obj, value)


class _DescriptorPath(_Descriptor):

    def __init__(self, sequence_dir, sequence_type):
        _Descriptor.__init__(self, None)
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


class _DescriptorAggregate(_Descriptor):

    AVAILABLE_MODES = ('none', 'mean')

    def __init__(self, aggragation_mode, sequence_type):
        _Descriptor.__init__(self, None)
        self.aggragation_mode = aggragation_mode
        self.sequence_type = sequence_type
        self.__doc__ = (
            'Mode of aggregation for writing %s time series data to files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        value = self.get_value(obj)
        if value is None:
            return self.aggragation_mode
        return value

    def __set__(self, obj, aggregation_mode):
        mode = str(aggregation_mode)
        if mode in self.AVAILABLE_MODES:
            self.set_value(obj, mode)
        else:
            raise ValueError(
                'The given mode `%s`for aggregating time series is not '
                'available.  Select one of the following modes: %s.'
                % (mode, self.AVAILABLE_MODES))

    def __delete__(self, obj):
        self.del_value(obj)


class _GeneralDescriptor(object):

    def __init__(self, *specific_descriptors):
        self.specific_descriptors = specific_descriptors

    def __set__(self, obj, value):
        for descr in self.specific_descriptors:
            descr.__set__(obj, value)

    def __delete__(self, obj):
        for descr in self.specific_descriptors:
            descr.__delete__(obj)


class SequenceManager(FileManager):
    """Manager for sequence files.

    Usually, there is only one |SequenceManager| used within each HydPy
    project, stored in module |pub|.  This object is responsible for the
    actual I/O tasks related to |IOSequence| objects.

    Working with a complete HydPy project, one often does not use the
    |SequenceManager|  directly, except one wishes to load data from
    or store data to directories that differ from the default settings.
    In the following examples, we partially set up a project manually,
    and show the essential features of class |SequenceManager|.

    Firstly, we define project called `test_project`, set a short
    initialisation period and prepare a |SequenceManager| object:

    >>> from hydpy import pub, Timegrids, Timegrid
    >>> pub.projectname = 'test_project'
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '05.01.2000',
    ...                                    '1d'))
    >>> from hydpy.core.filetools import SequenceManager
    >>> pub.sequencemanager = SequenceManager()

    Allowing the |SequenceManager| object to create missing directories
    is not the default, but more convenient for the following examples:

    >>> pub.sequencemanager.createdirs = True

    Secondly, we prepare a 0-dimensional |IOSequence| object called
    `test_sequence` and assign a small time series to it:

    >>> from hydpy.core.sequencetools import ModelSequence
    >>> class Seq0(ModelSequence):
    ...     NDIM = 0
    ...     rawfilename = 'test_sequence'
    >>> seq0 = Seq0()
    >>> seq0.activate_ram()
    >>> seq0.series = 1.0, 2.0, 3.0, 4.0

    Now we can store this time series in an ASCII file:

    >>> seq0.filetype_ext = 'asc'
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.save_file(seq0)

    To check that this was successful, we can load the file content from
    the standard output directory and print it:

    >>> import os
    >>> from hydpy import round_
    >>> def print_file(filename):
    ...     path = os.path.join(
    ...         'test_project', 'sequences', 'output', filename)
    ...     with TestIO():
    ...         with open(path) as file_:
    ...             lines = file_.readlines()
    ...     print(''.join(lines[:3]), end='')
    ...     for line in lines[3:]:
    ...         round_([float(x) for x in line.split()])
    >>> print_file('test_sequence.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    1.0
    2.0
    3.0
    4.0

    To show that reloading the data works, we first set the values of
    the internal time series of the |IOSequence| object to zero:

    >>> seq0.series = 0.
    >>> seq0.series
    InfoArray([ 0.,  0.,  0.,  0.])
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(seq0)
    >>> seq0.series
    InfoArray([ 1.,  2.,  3.,  4.])

    Wrongly formatted ASCII files should result in understandable error
    messages:

    >>> path = os.path.join(
    ...     'test_project', 'sequences', 'output', 'test_sequence.asc')
    >>> with TestIO():
    ...     with open(path) as file_:
    ...         right = file_.read()
    ...     wrong = right.replace('Timegrid', 'timegrid')
    ...     with open(path, 'w') as file_:
    ...         _ = file_.write(wrong)
    >>> with TestIO(clear_all=True):
    ...     pub.sequencemanager.load_file(seq0)
    Traceback (most recent call last):
    ...
    NameError: While trying to load the external data of sequence \
`seq0`, the following error occurred: name 'timegrid' is not defined

    Alternatively, one can call method |IOSequence.save_ext| of the
    respective |IOSequence| object, which itself calls
    |SequenceManager.save_file|.  We show this for a 1-dimensional
    sequence:

    >>> class Seq1(ModelSequence):
    ...     NDIM = 1
    ...     rawfilename = 'test_sequence'
    >>> seq1 = Seq1()
    >>> seq1.shape = (3,)
    >>> seq1.filetype_ext = 'asc'
    >>> seq1.activate_ram()
    >>> seq1.series = [[1.0, 2.0, 3.0],
    ...               [2.0, 3.0, 4.0],
    ...               [3.0, 4.0, 5.0],
    ...               [4.0, 5.0, 6.0]]
    >>> with TestIO():
    ...     seq1.save_ext()
    >>> print_file('test_sequence.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    1.0, 2.0, 3.0
    2.0, 3.0, 4.0
    3.0, 4.0, 5.0
    4.0, 5.0, 6.0

    If a sequence comes with a weighting parameter referenced by
    |property| |Variable.refweights|, one can save the averaged time
    series by using function |IOSequence.save_mean|:

    >>> from hydpy import numpy
    >>> from hydpy.core.parametertools import MultiParameter
    >>> class Weights(MultiParameter):
    ...     NDIM = 1
    ...     value = numpy.array([1.0, 1.0, 1.0])
    >>> Seq1.refweights = Weights()
    >>> with TestIO():
    ...     seq1.save_mean()
    >>> print_file('test_sequence.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    2.0
    3.0
    4.0
    5.0

    Method |IOSequence.save_mean| is strongly related with method
    |IOSequence.average_series|, meaning one can pass the same arguments.
    One example:

    >>> from hydpy.core import masktools
    >>> class TestMask(masktools.DefaultMask):
    ...     @classmethod
    ...     def new(cls, variable, **kwargs):
    ...         return cls.array2mask([True, True, False])
    >>> class Masks(masktools.Masks):
    ...     CLASSES = (TestMask,)
    >>> Seq1.availablemasks = Masks(None)
    >>> with TestIO():
    ...     seq1.save_mean('testmask')
    >>> print_file('test_sequence.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    1.5
    2.5
    3.5
    4.5

    Another option is to store data using |numpy| binary files, which
    is a good option for saving computation times, but a bad option for
    sharing data with colleagues:

    >>> seq0.filetype_ext = 'npy'
    >>> with TestIO():
    ...     pub.sequencemanager.save_file(seq0)

    The time information (without time zone information) is available
    within the first thirteen entries:

    >>> path = os.path.join(
    ...     'test_project', 'sequences', 'output', 'test_sequence.npy')
    >>> from hydpy import numpy, print_values
    >>> with TestIO():
    ...     print_values(numpy.load(path))
    2000.0, 1.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 1.0, 5.0, 0.0, 0.0, 0.0,
    86400.0, 1.0, 2.0, 3.0, 4.0

    Reloading the data works as expected:

    >>> seq0.series = 0.
    >>> seq0.series
    InfoArray([ 0.,  0.,  0.,  0.])
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(seq0)
    >>> seq0.series
    InfoArray([ 1.,  2.,  3.,  4.])

    Using the ASCII format, we showed error messages related to loading
    data above. Here we show an error related to saving data:

    >>> seq0.deactivate_ram()
    >>> with TestIO(clear_all=True):
    ...     pub.sequencemanager.save_file(seq0)
    Traceback (most recent call last):
    ...
    RuntimeError: Sequence `seq0` is not requested to make any internal \
data available to the user.

    Of course, one can also write mean values into |numpy| binary files:

    >>> seq1.filetype_ext = 'npy'
    >>> with TestIO():
    ...     seq1.save_mean(seq1.availablemasks.testmask)
    >>> with TestIO():
    ...     print_values(numpy.load(path))
    2000.0, 1.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 1.0, 5.0, 0.0, 0.0, 0.0,
    86400.0, 1.5, 2.5, 3.5, 4.5

    The third option to store data in netCDF files, which is explained
    separately in the documentation on class |NetCDFInterface|.
    """

    SUPPORTED_MODES = ('npy', 'asc', 'nc')
    _BASEDIR = 'sequences'

    inputdir = _DescriptorDir('input', 'input')
    outputdir = _DescriptorDir('output', 'output')
    nodedir = _DescriptorDir('node', 'node')
    tempdir = _DescriptorDir('temp', 'temporary')
    generaldir = _GeneralDescriptor(inputdir,
                                    outputdir,
                                    nodedir,
                                    tempdir)

    inputfiletype = _DescriptorType('npy', 'input')
    outputfiletype = _DescriptorType('npy', 'output')
    nodefiletype = _DescriptorType('npy', 'node')
    tempfiletype = _DescriptorType('npy', 'temporary')
    generalfiletype = _GeneralDescriptor(inputfiletype,
                                         outputfiletype,
                                         nodefiletype,
                                         tempfiletype)

    inputoverwrite = _DescriptorOverwrite(False, 'input')
    outputoverwrite = _DescriptorOverwrite(False, 'output')
    simoverwrite = _DescriptorOverwrite(False, 'sim node')
    obsoverwrite = _DescriptorOverwrite(False, 'obs node')
    tempoverwrite = _DescriptorOverwrite(False, 'temporary')
    generaloverwrite = _GeneralDescriptor(inputoverwrite,
                                          outputoverwrite,
                                          simoverwrite,
                                          obsoverwrite,
                                          tempoverwrite)

    inputpath = _DescriptorPath('inputdir', 'input')
    outputpath = _DescriptorPath('outputdir', 'output')
    nodepath = _DescriptorPath('nodedir', 'node')
    temppath = _DescriptorPath('tempdir', 'temporary')
    generalpath = _GeneralDescriptor(inputpath,
                                     outputpath,
                                     nodepath,
                                     temppath)

    inputaggregation = _DescriptorAggregate('none', 'input')
    outputaggregation = _DescriptorAggregate('none', 'output')
    nodeaggregation = _DescriptorAggregate('none', 'node')
    generalaggregation = _GeneralDescriptor(inputaggregation,
                                            outputaggregation,
                                            nodeaggregation)

    def __init__(self):
        FileManager.__init__(self)
        self._defaultdir = None
        self._netcdf_reader = None
        self._netcdf_writer = None

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
            header = '\n'.join([file_.readline() for _ in range(3)])
        timegrid_data = eval(header, {}, {'Timegrid': timetools.Timegrid})
        values = numpy.loadtxt(
            sequence.filepath_ext, skiprows=3, ndmin=sequence.NDIM+1)
        return timegrid_data, values

    def _load_nc(self, sequence):
        self.netcdf_reader.log(sequence, None)

    def save_file(self, sequence, array=None):
        """Write the date stored in |IOSequence.series| of the given
        |IOSequence| into an "external" data file. """
        if array is None:
            array = sequence.aggregate_series()
        try:
            if sequence.filetype_ext == 'npy':
                self._save_npy(sequence, array)
            elif sequence.filetype_ext == 'asc':
                self._save_asc(sequence, array)
            elif sequence.filetype_ext == 'nc':
                self._save_nc(sequence, array)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to save the external data of sequence %s'
                % objecttools.devicephrase(sequence))

    @staticmethod
    def _save_npy(sequence, array):
        numpy.save(sequence.filepath_ext,
                   pub.timegrids.init.array2series(array))

    @staticmethod
    def _save_asc(sequence, array):
        with open(sequence.filepath_ext, 'w') as file_:
            file_.write(
                pub.timegrids.init.assignrepr(
                    prefix='',
                    style='iso2',
                    utcoffset=pub.options.utcoffset) + '\n')
        with open(sequence.filepath_ext, 'ab') as file_:
            numpy.savetxt(file_, array, delimiter='\t')

    def _save_nc(self, sequence, array):
        self.netcdf_writer.log(sequence, array)

    @property
    def netcdf_reader(self):
        """A |NetCDFInterface| object to be prepared by method
        |SequenceManager.open_netcdf_reader| and to be finalized
        by method |SequenceManager.close_netcdf_reader|.

        >>> from hydpy.core.filetools import SequenceManager
        >>> sm = SequenceManager()
        >>> sm.netcdf_reader
        Traceback (most recent call last):
        ...
        RuntimeError: The sequence file manager does currently handle \
no NetCDF reader object.

        >>> sm.open_netcdf_reader()
        >>> from hydpy.core.objecttools import classname
        >>> classname(sm.netcdf_reader)
        'NetCDFInterface'

        >>> sm.close_netcdf_reader()
        >>> sm.netcdf_reader
        Traceback (most recent call last):
        ...
        RuntimeError: The sequence file manager does currently handle \
no NetCDF reader object.
        """
        if self._netcdf_reader:
            return self._netcdf_reader
        raise RuntimeError(
            'The sequence file manager does currently handle '
            'no NetCDF reader object.')

    def open_netcdf_reader(self, flatten=False, isolate=False):
        """Prepare a new |NetCDFInterface| object for reading data."""
        self._netcdf_reader = netcdftools.NetCDFInterface(
            flatten=flatten, isolate=isolate)

    def close_netcdf_reader(self):
        """Read data with a prepared |NetCDFInterface| object and remove it."""
        self._netcdf_reader.read()
        self._netcdf_reader = None

    @property
    def netcdf_writer(self):
        """A |NetCDFInterface| object to be prepared by method
        |SequenceManager.open_netcdf_writer| and to be finalized
        by method |SequenceManager.close_netcdf_writer|.

        >>> from hydpy.core.filetools import SequenceManager
        >>> sm = SequenceManager()
        >>> sm.netcdf_writer
        Traceback (most recent call last):
        ...
        RuntimeError: The sequence file manager does currently handle \
no NetCDF writer object.

        >>> sm.open_netcdf_writer()
        >>> from hydpy.core.objecttools import classname
        >>> classname(sm.netcdf_writer)
        'NetCDFInterface'

        >>> sm.close_netcdf_writer()
        >>> sm.netcdf_writer
        Traceback (most recent call last):
        ...
        RuntimeError: The sequence file manager does currently handle \
no NetCDF writer object.
        """
        if self._netcdf_writer:
            return self._netcdf_writer
        raise RuntimeError(
            'The sequence file manager does currently handle '
            'no NetCDF writer object.')

    def open_netcdf_writer(self, flatten=False, isolate=False):
        """Prepare a new |NetCDFInterface| object for writing data."""
        self._netcdf_writer = netcdftools.NetCDFInterface(
            flatten=flatten, isolate=isolate)

    def close_netcdf_writer(self):
        """Write data with a prepared |NetCDFInterface| object and remove it.
        """
        self._netcdf_writer.write()
        self._netcdf_writer = None

    def __dir__(self):
        return objecttools.dir_(self)


autodoctools.autodoc_module()
