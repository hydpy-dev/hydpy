# -*- coding: utf-8 -*-
"""This module implements tools for handling the folder structure
of HydPy projects.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import os
import runpy
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import selectiontools


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


class _ContextDir(object):

    def __init__(self, value, sequence_type):
        self.value = value
        self.sequence_type = sequence_type
        self.__doc__ = (
            'Current directory containing the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        try:
            obj.currentdir = self.value
            return obj._currentdir
        except IOError:
            objecttools.augment_excmessage(
                'While trying to get the %s sequence directory'
                % self.sequence_type)
        finally:
            obj._currentdir = None

    def __set__(self, obj, directory):
        obj._inputdir = None
        try:
            obj.currentdir = directory
            self.value = directory
        except IOError:
            objecttools.augment_excmessage(
                'While trying to set the %s sequence directory'
                % self.sequence_type)
        finally:
            obj._currentdir = None

    def __delete__(self, obj):
        try:
            obj.currentdir = self.value
            del obj.currentdir
        except IOError:
            objecttools.augment_excmessage(
                'While trying to delete the input sequence directory')
        finally:
            self.value = None


class _ContextType(object):

    def __init__(self, value, sequence_type):
        self.value = value
        self.__doc__ = (
            'Currently selected type of the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return self.value

    def __set__(self, obj, value):
        value = str(value)
        if value in obj._supportedmodes:
            self.value = value
        else:
            raise ValueError(
                'The given sequence file type `%s` is not implemented.  '
                'Please choose one of the following file types: %s.'
                % (value, objecttools.enumeration(obj._supportedmodes)))


class _ContextOverwrite(object):

    def __init__(self, value, sequence_type):
        self.value = value
        self.__doc__ = (
            'Currently selected overwrite flag of the %s sequence files.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return self.value

    def __set__(self, obj, value):
        self.value = bool(value)


class _ContextPath(object):

    def __init__(self, sequence_dir, sequence_type):
        self.value = None
        self.sequence_dir = sequence_dir
        self.sequence_type = sequence_type
        self.__doc__ = (
            'Path of the %s sequence directory.'
            % sequence_type)

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        if self.value:
            return self.value
        else:
            return os.path.join(obj.basepath, getattr(obj, self.sequence_dir))

    def __set__(self, obj, path):
        if os.path.exists(path):
            self.value = path
        elif obj.createdirs:
            os.makedirs(path)
            self.value = path
        elif obj.check_exists:
            raise IOError(
                'The %s sequence path `%s` does not exist.'
                % (self.sequence_type, os.path.abspath(path)))

    def __delete__(self, obj):
        self.value = None


class SequenceManager(FileManager):
    """Manager for sequence files."""

    _supportedmodes = ('npy', 'asc')

    inputdir = _ContextDir('input', 'input')
    outputdir = _ContextDir('output', 'output')
    nodedir = _ContextDir('node', 'node')
    tempdir = _ContextDir('temp', 'temporary')

    inputfiletype = _ContextType('npy', 'input')
    outputfiletype = _ContextType('npy', 'output')
    nodefiletype = _ContextType('npy', 'node')
    tempfiletype = _ContextType('npy', 'temporary')

    inputoverwrite = _ContextOverwrite(False, 'input')
    outputoverwrite = _ContextOverwrite(False, 'output')
    simoverwrite = _ContextOverwrite(False, 'sim node')
    obsoverwrite = _ContextOverwrite(False, 'obs node')
    tempoverwrite = _ContextOverwrite(False, 'temporary')

    inputpath = _ContextPath('inputdir', 'input')
    outputpath = _ContextPath('outputdir', 'output')
    nodepath = _ContextPath('nodedir', 'node')
    temppath = _ContextPath('tempdir', 'temporary')

    def __init__(self):
        FileManager.__init__(self)
        self._BASEDIR = 'sequences'
        self._defaultdir = None





    def __dir__(self):
        return objecttools.dir_(self)


autodoctools.autodoc_module()
