# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import os
import sys
import warnings
# ...from HydPy
from hydpy import pub
from hydpy.framework import objecttools
from hydpy.framework import timetools
from hydpy.framework import devicetools
from hydpy.framework import selectiontools


class MainManager(object):

    def __init__(self):
        self.info = {}
        self.networkfile = None
        self.controlfiles = None
        self.sequencefiles = None
        self.initialvaluefiles = None
        self.parameterfiles = None
        self.checkpath()
        self.loadinfo()
        self.applyinfo()
        self.clearinfo()

    def _getpath(self):
        return os.path.abspath(pub.projectname+'.py')
    path = property(_getpath)

    def checkpath(self):
        if not os.path.exists(self.path):
            raise IOError('The required project main file `%s` does not exist.'
                          % self.path)

    def loadinfo(self):
        """Load general information from the project's main file."""
        try:
            execfile(self.path, {}, self.info)
        except Exception:
            exc, message, traceback_ = sys.exc_info()
            message = ('While trying to load the genereal project settings '
                       'from `%s`, the following error occured:  %s'
                       % (self.path, message))
            raise exc, message, traceback_

    def clearinfo(self):
        self.info = {}

    def applyinfo(self):
        self.timegrids2pub()
        self.getmanagers()

    def timegrids2pub(self):
        selection = [value for value in self.info.itervalues()
                     if isinstance(value, timetools.Timegrids)]
        if len(selection) != 1:
            print(self.info)
            raise ImportError('The main project file `%s` must define exactly '
                              '1 `Timegrids` object; %d objects are defined '
                              'instead.' % (self.path, len(selection)))
        else:
            pub.timegrids = selection[0]

    def getmanagers(self):
        for FileClass in (NetworkManager, ControlManager,
                          SequenceManager, ConditionManager):
            selection = [value for value in self.info.itervalues()
                         if isinstance(value, FileClass)]
            if len(selection) > 1:
                raise ImportError('The main project file `%s` must not define '
                                  'more then one `%s` objects but %d objects '
                                  'are defined.'
                                  % (self.path, FileClass.__name__,
                                     len(selection)))
            elif len(selection) == 1:
                setattr(self, FileClass.__name__.lower(), selection[0])
            else:
                setattr(self, FileClass.__name__.lower(), FileClass())

    def __dir__(self):
        return objecttools.dir_(self)


class NetworkManager(object):
    """Manager for network files."""

    def __init__(self):
        self._BASEDIRECTORY = 'network'
        self.directory = pub.projectname

    def _getbasepath(self):
        """Absolute path pointing to all network directories."""
        return os.path.abspath(self._BASEDIRECTORY)
    basepath = property(_getbasepath)

    def _getdirectory(self):
        """Directory containing the network files."""
        return self._subdirectory
    def _setdirectory(self, subdirectory):
        directory = os.path.join(self.basepath, subdirectory)
        if not os.path.exists(directory):
            raise IOError('A directory `%s` within the network base path '
                          '`%s` does not exist.'
                          % (subdirectory, self.basepath))
        self._subdirectory = str(subdirectory)
    directory = property(_getdirectory, _setdirectory)

    def _getdirpath(self):
        """Complete path of the directory containing the network files."""
        return os.path.join(self.basepath, self.directory)
    dirpath = property(_getdirpath)

    def _getfilenames(self):
        """Names of the network files."""
        return [fn for fn in os.listdir(self.dirpath)
                if (fn.endswith('.py') and not fn.startswith('_'))]
    filenames = property(_getfilenames)

    def _getfilepaths(self):
        """Complete paths of the defined networks files."""
        root = os.path.join(self.basepath, self.directory)
        return [os.path.join(root, fn) for fn in self.filenames]
    filepaths = property(_getfilepaths)

    def load(self):
        """Load nodes and elements from all network files and return them in
        a :class:`~hydpy.selectiontools.Selections` instance.  Each single
        network file defines a seperate
        :class:`~hydpy.selectiontools.Selection` instance.  Additionally, all
        elements and nodes are bundled in a selection named `complete`.
        """
        selections = selectiontools.Selections()
        for (filename, path) in zip(self.filenames, self.filepaths):
            # Ensure both `Node` and `Element`start with a `fresh` memory.
            devicetools.Node.gathernewnodes()
            devicetools.Element.gathernewelements()
            info = {}
            try:
                execfile(path, {}, info)
            except Exception:
                exc, message, traceback_ = sys.exc_info()
                message = ('While trying to load the network file `%s`, '
                           'the following error occured:  %s'
                           % (path, message))
                raise exc, message, traceback_
            try:
                selections += selectiontools.Selection(
                                           filename.split('.')[0],
                                           info['Node'].gathernewnodes(),
                                           info['Element'].gathernewelements())

            except KeyError as exc:
                KeyError('The class `%s` cannot be loaded from the network '
                         'file `%s`.  Please refer to the HydPy documentation '
                         'on how to prepare network files properly.'
                         % (exc.args[0], filename))
        selections += selectiontools.Selection(
                                          'complete',
                                          info['Node'].registerednodes(),
                                          info['Element'].registeredelements())
        return selections

    def save(self, selections, overwrite=False):
        """Save the nodes and elements from each
        :class:`~hydpy.selectiontools.Selection` object contained within the
        given :class:`~hydpy.selectiontools.Selections` instance to a seperate
        network file of the same name.  Set `overwrite` to `True`, if you
        want to overwrite already existing network files.
        """
        selections = selectiontools.Selections(selections)
        for (name, selection) in selections:
            if name == 'complete':
                continue
            path = os.path.join(self.dirpath, name+'.py')
            if os.path.exists(path) and not overwrite:
                warnings.warn('The path `%s` does already exist, selection '
                              '`%s` cannot be saved.  Please select another '
                              'network directory or set the `overwrite` flag '
                              'to `True`' % (path, name))
            else:
                with open(path, 'w') as file_:
                    file_.write('from hydpy import *\n\n')
                    file_.write(repr(selection.elements))

    def delete(self, *selections):
        """Delete network files.  One or more filenames and/or
        :class:`~hydpy.selectiontools.Selection` instances can serve as
        function arguments.
        """
        for selection in selections:
            name = str(selection)
            if not name.endswith('.py'):
                name += '.py'
            path = os.path.join(self.dirpath, name)
            try:
                os.remove(path)
            except EnvironmentError:
                Exception_, message, traceback_ = sys.exc_info()
                Exception_ = str(Exception_)[:-2].split('.')[-1]
                warnings.warn(': '.join((Exception_, str(message))))

    def __dir__(self):
        return objecttools.dir_(self)


class ControlManager(object):
    """Manager for control parameter files."""

    # The following file path to content mapping is used to circumvent reading
    # the same secondary control parameter file from disk multiple times.
    _registry = {}

    def __init__(self):
        self._BASEDIRECTORY = 'control'
        self._projectdirectory = pub.projectname
        self._controldirectory = None

    def _getbasepath(self):
        """Absolute path pointing to all control directories."""
        return os.path.abspath(self._BASEDIRECTORY)
    basepath = property(_getbasepath)

    def _getprojectdirectory(self):
        """Folder containing the control directories of the current project."""
        return self._projectdirectory
    def _setprojectdirectory(self, directory):
        directory = str(directory)
        directory = os.path.join(self.basepath, directory)
        if not os.path.exists(directory):
            raise IOError('Path `%s` does not contain a control directory '
                          'named `%s`.' % (self.basepath, directory))
        self._projectdirectory = directory
    projectdirectory = property(_getprojectdirectory, _setprojectdirectory)

    def _getprojectpath(self):
        """Absolute path of the project directory."""
        return os.path.join(self.basepath, self.projectdirectory)
    projectpath = property(_getprojectpath)

    def _getcontroldirectories(self):
        """Folders containing the control files of different parameter sets."""
        directories = FolderShow()
        for directory in os.listdir(self.projectpath):
            if not directory.startswith('_'):
                path = os.path.join(self.projectpath, directory)
                if os.path.isdir(path):
                    directories.add(directory)
        return directories
    controldirectories = property(_getcontroldirectories)

    def _getcontrolpaths(self):
        """Absolute paths of the control directories."""
        paths = FolderShow()
        for (directory, dummy) in self.controldirectories:
            paths.add(directory, os.path.join(self.projectpath, directory))
        return paths
    controlpaths = property(_getcontrolpaths)

    def _getcontroldirectory(self):
        """The selected (or the only selectable) control directory"""
        directories = self.controldirectories
        if self._controldirectory is not None:
            try:
                return getattr(directories, self._controldirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified control directory `%s`.'
                              % (self.projectpath, self._controldirectory))
        elif len(directories) == 1:
            return directories[0]
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'control directories.' % self.projectpath)
        try:
            return directories.default
        except AttributeError:
            raise IOError('The project path `%s` contains multiple control'
                          'directories, but none is named `default`.  '
                          'Please specify the control directory to be '
                          'worked with manually.' % self.projectpath)
    def _setcontroldirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._controldirectory = directory
        else:
            raise IOError('The project path `%s` does not contain a '
                          'control directory named `%s`.'
                          % (self.projectpath, directory))
    def _delcontroldirectory(self):
        self._controldirectory = None
    controldirectory = property(_getcontroldirectory, _setcontroldirectory,
                                _delcontroldirectory)

    def _getcontrolpath(self):
        """Absolute paths of the selected control directory."""
        return os.path.join(self.projectpath, self.controldirectory)
    controlpath = property(_getcontrolpath)

    def loadfile(self, filename):
        """Return the namespace of the given file (and eventually of its
        subfile) as a :class:`dict`.

        Argument:
            * filename (:class:`str`): Any object returning a valid filename
              with or without extension.
        """
        workingpath = os.path.abspath(os.curdir)
        try:
            os.chdir(self.controlpath)
        except OSError:
            raise IOError('The specified control path `%s` does not exist.'
                          % self.controlpath)
        else:
            info = {}
            self.read2dict(filename, info)
            return info
        finally:
            self._registry.clear()
            os.chdir(workingpath)

    @classmethod
    def read2dict(cls, path, info):
        """Reads the control parameters of the given path (and its subpaths
        where appropriate) and stores it in the given :class:`dict` `info`.

        Arguments:
            * path (:class:`str`): Any object returning a valid path
              with or without extension.
            * info (:info:`dict`): Target dictionary.

        Note that the :class:`dict` `info` can be used to feed information
        into the execution of control files.  Use this function only if you
        are completely sure on how the control parameter import of HydPy
        works.  Otherwise, you should most probably prefer to use
        :func:`loadfile` or :func:`loadfiles`.
        """
        path = str(path)
        if not path.endswith('.py'):
            path += '.py'
        try:
            if path not in cls._registry:
                with file(path) as file_:
                    cls._registry[path] = file_.read()
            exec(cls._registry[path], {}, info)
        except BaseException:
            exc, message, traceback_ = sys.exc_info()
            message = ('While trying to load the control file `%s`, '
                       'the following error occured:  %s'
                       % (path, message))
            raise exc, message, traceback_
        if 'model' not in info:
            raise IOError('Model parameters cannot be loaded from control '
                          'file `%s`.  Please refer to the HydPy '
                          'documentation on how to prepare control files '
                          'properly.' % path)

class FolderShow(object):

    def __init__(self, *args, **kwargs):
        for arg in args:
            self.add(arg)
        for (key, value) in kwargs.items():
            self.add(key, value)

    def add(self, directory, path=None):
        if path is None:
            path = directory
        try:
            exec('self.%s = r"%s"' %(directory, path))
        except BaseException:
            raise IOError('The directory name `%s` cannot be handled as a '
                          'variable name.  Please avoid arithmetic operators '
                          'like `-`, prefixed numbers...' % directory)

    def __iter__(self):
        return vars(self).items()

    def __getitem__(self, key):
        return sorted(vars(self).values())[key]

    def __len__(self):
        return len(vars(self))

    def __repr__(self):
        if not len(self):
            return 'Folders()'
        else:
            args, kwargs = [], []
            for (idx, (key, value)) in enumerate(self):
                if key == value:
                    args.append(key)
                else:
                    kwargs.append('%s=%s' % (key, value))
            lines = ['           %s,' %arg for arg in (args + kwargs)]
            lines[0] = 'FolderShow(' + lines[0][11:]
            lines[-1] = lines[-1][:-1] + ')'
            return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class SequenceManager(object):
    """Manager for sequence files."""

    _supportedmodes = ('npy', 'asc')

    def __init__(self, projectdirectory=None, inputdirectory=None,
                 outputdirectory=None, nodedirectory=None, tempdirectory=None,
                 inputfiletype=None, outputfiletype=None, nodefiletype=None):
        self._BASEDIRECTORY = 'sequences'
        if projectdirectory:
            self.projectdirectory = projectdirectory
        else:
            self._projectdirectory = pub.projectname
        if inputdirectory:
            self.inputdirectory = inputdirectory
        else:
            self._inputdirectory = None
        if outputdirectory:
            self.outputdirectory = outputdirectory
        else:
            self._outputdirectory = None
        if nodedirectory:
            self.nodedirectory = nodedirectory
        else:
            self._nodedirectory = None
        if tempdirectory:
            self.tempdirectory = tempdirectory
        else:
            self._tempdirectory = None
        if inputfiletype:
            self.inputfiletype = inputfiletype
        else:
            self._inputfiletype = 'npy'
        if outputfiletype:
            self.outputfiletype = outputfiletype
        else:
            self._outputfiletype = 'npy'
        if outputfiletype:
            self.outputfiletype = outputfiletype
        else:
            self._outputfiletype = 'npy'
        if nodefiletype:
            self.nodefiletype = nodefiletype
        else:
            self._nodefiletype = 'npy'
        self._inputoverwrite = False
        self._outputoverwrite = False
        self._simoverwrite = False
        self._obsoverwrite = False

    def _getbasepath(self):
        """Absolute path pointing to all sequence directories."""
        return os.path.abspath(self._BASEDIRECTORY)
    basepath = property(_getbasepath)

    def _getprojectdirectory(self):
        """Folder containing the file directories of the current project."""
        return self._projectdirectory
    def _setprojectdirectory(self, directory):
        directory = str(directory)
        directory = os.path.join(self.basepath, directory)
        if not os.path.exists(directory):
            raise IOError('Path `%s` does not contain a directory named `%s`.'
                          % (self.basepath, directory))
        self._projectdirectory = directory
    projectdirectory = property(_getprojectdirectory, _setprojectdirectory)

    def _getprojectpath(self):
        """Absolute path of the project directory."""
        return os.path.join(self.basepath, self.projectdirectory)
    projectpath = property(_getprojectpath)

    def _getsequencedirectories(self):
        """Folders containing the different input/output/temp sequences."""
        directories = FolderShow()
        for directory in os.listdir(self.projectpath):
            if not directory.startswith('_'):
                path = os.path.join(self.projectpath, directory)
                if os.path.isdir(path):
                    directories.add(directory)
        return directories
    sequencedirectories = property(_getsequencedirectories)

    def _getsequencepaths(self):
        """Absolute paths of the sequence directories."""
        paths = FolderShow()
        for (key, value) in self.sequencedirectories:
            paths.add(key, os.path.join(self.projectpath, key))
        return paths
    sequencepaths = property(_getsequencepaths)

    def _getinputdirectory(self):
        """The selected (or the only selectable) input sequence directory."""
        directories = self.sequencedirectories
        if self._inputdirectory is not None:
            try:
                return getattr(directories, self._inputdirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified input sequence directory `%s`.'
                              % (self.projectpath, self._inputdirectory))
        elif len(directories) == 1:
            return directories[0]
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'sequence directories.' % self.projectpath)
        else:
            try:
                return directories.input
            except AttributeError:
                raise IOError('The project path `%s` contains multiple '
                              'sequence directories, but none is named '
                              '`input`.  Please specify the input sequence '
                              'directory to be worked with manually.'
                              % self.projectpath)
    def _setinputdirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._inputdirectory = directory
        else:
            raise IOError('The project path `%s` does not contain sequence '
                          'directory named `%s`.'
                          % (self.projectpath, directory))
    def _delinputdirectory(self):
        self._inputdirectory = None
    inputdirectory = property(_getinputdirectory, _setinputdirectory,
                              _delinputdirectory)

    def _getoutputdirectory(self):
        """The selected (or the only selectable) output sequence directory."""
        directories = self.sequencedirectories
        if self._outputdirectory is not None:
            try:
                return getattr(directories, self._outputdirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified output sequence directory `%s`.'
                              % (self.projectpath, self._outputdirectory))
        elif len(directories) == 1:
            return directories[0]
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'sequence directories.' % self.projectpath)
        else:
            try:
                return directories.output
            except AttributeError:
                raise IOError('The project path `%s` contains multiple '
                              'sequence directories, but none is named '
                              '`output`.  Please specify the sequence '
                              'directory to be worked with manually.'
                              % self.projectpath)
    def _setoutputdirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._outputdirectory = directory
        else:
            raise IOError('The project path `%s` does not contain sequence '
                          'directory named `%s`.'
                          % (self.projectpath, directory))
    def _deloutputdirectory(self):
        self._outputdirectory = None
    outputdirectory = property(_getoutputdirectory, _setoutputdirectory,
                               _deloutputdirectory)

    def _getnodedirectory(self):
        """The selected (or the only selectable) node sequence directory."""
        directories = self.sequencedirectories
        if self._nodedirectory is not None:
            try:
                return getattr(directories, self._nodedirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified node sequence directory `%s`.'
                              % (self.projectpath, self._nodedirectory))
        elif len(directories) == 1:
            return directories[0]
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'sequence directories.' % self.projectpath)
        else:
            try:
                return directories.node
            except AttributeError:
                raise IOError('The project path `%s` contains multiple '
                              'sequence directories, but none is named '
                              '`node`.  Please specify the node sequence '
                              'directory to be worked with manually.'
                              % self.projectpath)
    def _setnodedirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._nodedirectory = directory
        else:
            raise IOError('The project path `%s` does not contain sequence '
                          'directory named `%s`.'
                          % (self.projectpath, directory))
    def _delnodedirectory(self):
        self._nodedirectory = None
    nodedirectory = property(_getnodedirectory, _setnodedirectory,
                              _delnodedirectory)

    def _gettempdirectory(self):
        """The selected (or the only selectable) temporary sequence directory.
        """
        directories = self.sequencedirectories
        if self._tempdirectory is not None:
            try:
                return getattr(directories, self._tempdirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified temporary sequence directory `%s`.'
                              % (self.projectpath, self._tempdirectory))
        elif len(directories) == 1:
            return directories[0]
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'sequence directories.' % self.projectpath)
        else:
            try:
                return directories.temp
            except AttributeError:
                raise IOError('The project path `%s` contains multiple '
                              'sequence directories, but none is named '
                              '`temp`.  Please specify the temporary sequence '
                              'directory to be worked with manually.'
                              % self.projectpath)
    def _settempdirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._tempdirectory = directory
        else:
            raise IOError('The project path `%s` does not contain sequence '
                          'directory named `%s`.'
                          % (self.projectpath, directory))
    def _deltempdirectory(self):
        self._tempdirectory = None
    tempdirectory = property(_gettempdirectory, _settempdirectory,
                             _deltempdirectory)

    def _getinputpath(self):
        """Absolute paths of the selected input sequence directory."""
        return os.path.join(self.projectpath, self.inputdirectory)
    inputpath = property(_getinputpath)

    def _getoutputpath(self):
        """Absolute paths of the selected output sequence directory."""
        return os.path.join(self.projectpath, self.outputdirectory)
    outputpath = property(_getoutputpath)

    def _getnodepath(self):
        """Absolute paths of the selected node sequence directory."""
        return os.path.join(self.projectpath, self.nodedirectory)
    nodepath = property(_getnodepath)

    def _gettemppath(self):
        """Absolute paths of the selected temporary sequence directory."""
        return os.path.join(self.projectpath, self.tempdirectory)
    temppath = property(_gettemppath)

    def _getinputfiletype(self):
        """File type of the external input files."""
        return self._inputfiletype
    def _setinputfiletype(self, inputfiletype):
        inputfiletype = str(inputfiletype)
        if inputfiletype in self._supportedmodes:
            self._inputfiletype = inputfiletype
        else:
            raise NotImplementedError('The given input file type `%s` is not '
                                      'implemented yet.  Please choose one '
                                      'of the following file types: %s.'
                                      % (inputfiletype, self._supportedmodes))
    inputfiletype = property(_getinputfiletype, _setinputfiletype)

    def _getoutputfiletype(self):
        """File type of the external output files."""
        return self._outputfiletype
    def _setoutputfiletype(self, outputfiletype):
        outputfiletype = str(outputfiletype)
        if outputfiletype in self._supportedmodes:
            self._outputfiletype = outputfiletype
        else:
            raise NotImplementedError('The given output file type `%s` is not '
                                      'implemented yet.  Please choose one '
                                      'of the following file types: %s.'
                                      % (outputfiletype, self._supportedmodes))
    outputfiletype = property(_getoutputfiletype, _setoutputfiletype)

    def _getnodefiletype(self):
        """File type of the external node files."""
        return self._nodefiletype
    def _setnodefiletype(self, nodefiletype):
        nodefiletype = str(nodefiletype)
        if nodefiletype in self._supportedmodes:
            self._nodefiletype = nodefiletype
        else:
            raise NotImplementedError('The given node file type `%s` is not '
                                      'implemented yet.  Please choose one '
                                      'of the following file types: %s.'
                                      % (nodefiletype, self._supportedmodes))
    nodefiletype = property(_getnodefiletype, _setnodefiletype)

    def _getinputoverwrite(self):
        return self._inputoverwrite
    def _setinputoverwrite(self, value):
        self._inputoverwrite = bool(value)
    inputoverwrite = property(_getinputoverwrite, _setinputoverwrite)

    def _getoutputoverwrite(self):
        return self._outputoverwrite
    def _setoutputoverwrite(self, value):
        self._outputoverwrite = bool(value)
    outputoverwrite = property(_getoutputoverwrite, _setoutputoverwrite)

    def _getsimoverwrite(self):
        return self._simoverwrite
    def _setsimoverwrite(self, value):
        self._simoverwrite = bool(value)
    simoverwrite = property(_getsimoverwrite, _setsimoverwrite)

    def _getobsoverwrite(self):
        return self._obsoverwrite
    def _setobsoverwrite(self, value):
        self._obsoverwrite = bool(value)
    obsoverwrite = property(_getobsoverwrite, _setobsoverwrite)

    def __dir__(self):
        return objecttools.dir_(self)


class ConditionManager(object):
    """Manager for condition files."""

    def __init__(self):
        self._BASEDIRECTORY = 'conditions'
        self._projectdirectory = pub.projectname
        self._loaddirectory = None
        self._savedirectory = None

    def _getbasepath(self):
        """Absolute path pointing to all condition directories."""
        return os.path.abspath(self._BASEDIRECTORY)
    basepath = property(_getbasepath)

    def _getprojectdirectory(self):
        """Folder containing the condition directories of the current
        project.
        """
        return self._projectdirectory
    def _setprojectdirectory(self, directory):
        directory = str(directory)
        directory = os.path.join(self.basepath, directory)
        if not os.path.exists(directory):
            raise IOError('Path `%s` does not contain a condition directory '
                          'named `%s`.' % (self.basepath, directory))
        self._projectdirectory = directory
    projectdirectory = property(_getprojectdirectory, _setprojectdirectory)

    def _getprojectpath(self):
        """Absolute path of the project directory."""
        return os.path.join(self.basepath, self.projectdirectory)
    projectpath = property(_getprojectpath)

    def _getconditiondirectories(self):
        """Folders containing the condition files of e.g. different time
        points.
        """
        directories = FolderShow()
        for directory in os.listdir(self.projectpath):
            if not directory.startswith('_'):
                path = os.path.join(self.projectpath, directory)
                if os.path.isdir(path):
                    directories.add(directory)
        return directories
    conditiondirectories = property(_getconditiondirectories)

    def _getloaddirectory(self):
        """The selected (or only selectable) initial conditions directory"""
        directories = self.conditiondirectories
        if self._loaddirectory is not None:
            try:
                return getattr(directories, self._loaddirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified conditions directory `%s`.'
                              % (self.projectpath, self._loaddirectory))
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'conditions directories.' % self.projectpath)
        try:
            string = 'init_' + pub.timegrids.sim.firstdate.string('os')
        except AttributeError:
            raise IOError('The project path `%s` contains multiple control'
                          'directories, and no first simulation date is '
                          'available to determine the relevant one.  '
                          'Please specify the control directory to be '
                          'worked with manually.' % self.projectpath)
        try:
            return getattr(directories, string)
        except AttributeError:
            raise IOError('The project path `%s` contains multiple control'
                          'directories, but none is in accordance with the  '
                          'first simulation date (%s).  Please specify'
                          'the control directory to be worked with manually.'
                          % (self.projectpath, string))
    def _setloaddirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._loaddirectory = directory
        else:
            raise IOError('The project path `%s` does not contain a '
                          'condition directory named `%s`.'
                          % (self.projectpath, directory))
    def _delloaddirectory(self):
        self._loaddirectory = None
    loaddirectory = property(_getloaddirectory, _setloaddirectory,
                             _delloaddirectory)

    def _getsavedirectory(self):
        """The selected (or only selectable) final conditions directory"""
        directories = self.conditiondirectories
        if self._savedirectory is not None:
            try:
                return getattr(directories, self._savedirectory)
            except AttributeError:
                raise IOError('The project path `%s` does not contain the'
                              'specified conditions directory `%s`.'
                              % (self.projectpath, self._savedirectory))
        elif len(directories) == 0:
            raise IOError('The project path `%s` does not contain any '
                          'conditions directories.' % self.projectpath)
        try:
            string = 'init_' + pub.timegrids.sim.lastdate.string('os')
        except AttributeError:
            raise IOError('The project path `%s` contains multiple control'
                          'directories, and no last simulation date is '
                          'available to determine the relevant one.  '
                          'Please specify the control directory to be '
                          'worked with manually.' % self.projectpath)
        try:
            return getattr(directories, string)
        except AttributeError:
            raise IOError('The project path `%s` contains multiple control'
                          'directories, but none is in accordance with the  '
                          'last simulation date (%s).  Please specify'
                          'the control directory to be worked with manually.'
                          % (self.projectpath, string))
    def _setsavedirectory(self, directory):
        directory = str(directory)
        path = os.path.join(self.projectpath, directory)
        if os.path.exists(path):
            self._savedirectory = directory
        else:
            raise IOError('The project path `%s` does not contain a '
                          'condition directory named `%s`.'
                          % (self.projectpath, directory))
    def _delsavedirectory(self):
        self._loaddirectory = None
    savedirectory = property(_getsavedirectory, _setsavedirectory,
                             _delsavedirectory)

    def _getloadpath(self):
        """Absolute paths of the relevant initial condition directory."""
        return os.path.join(self.projectpath, self.loaddirectory)
    loadpath = property(_getloadpath)

    def _getsavepath(self):
        """Absolute paths of the relevant final condition directory."""
        return os.path.join(self.projectpath, self.savedirectory)
    savepath = property(_getsavepath)

    def loadfile(self, filename, dirname=None):
        if not filename.endswith('.py'):
            filename += '.py'
        if dirname is None:
            dirname = os.path.join(pub.conditionmanager.loadpath)
        filepath = os.path.join(dirname, filename)
        try:
            with file(filepath) as file_:
                return file_.read()
        except BaseException:
            exc, message, traceback_ = sys.exc_info()
            message = ('While trying to read the conditions file `%s`, '
                       'the following error occured:  %s'
                       % (filepath, message))
            raise exc, message, traceback_
