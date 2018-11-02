# -*- coding: utf-8 -*-
"""This module implements features for handling the folder structure of
HydPy projects as well as loading data from and storing data to files.
"""
# import...
# ...from standard library
import os
import runpy
import shutil
import weakref
from typing import List
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import netcdftools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import selectiontools
from hydpy.core import timetools


class Folder2Path(object):
    """Map folder names to their path names.

    You can both pass positional arguments and keyword arguments when
    initialising |Folder2Path|.  For positional arguments, the folder
    and its path are assumed to be identical.  For keyword arguments,
    the keyword corresponds to the folder name and its value to the
    path name:

    >>> from hydpy.core.filetools import Folder2Path
    >>> Folder2Path()
    Folder2Path()
    >>> f2p = Folder2Path(
    ...     'folder1', 'folder2', folder3='folder3', folder4='path4')
    >>> f2p
    Folder2Path(folder1,
                folder2,
                folder3,
                folder4=path4)
    >>> print(f2p)
    Folder2Path(folder1, folder2, folder3, folder4=path4)

    Adding folders after initialisation is supported:

    >>> f2p.add('folder5')
    >>> f2p.add('folder6', 'path6')
    >>> f2p
    Folder2Path(folder1,
                folder2,
                folder3,
                folder5,
                folder4=path4,
                folder6=path6)

    Folder names are required to be valid Python identifiers:

    >>> f2p.add('folder 7')
    Traceback (most recent call last):
    ...
    ValueError: The given name string `folder 7` does not define a valid \
variable identifier.  Valid identifiers do not contain characters like `-` \
or empty spaces, do not start with numbers, cannot be mistaken with Python \
built-ins like `for`...)

    You can query the folder and attribute names:

    >>> f2p.folders
    ['folder1', 'folder2', 'folder3', 'folder4', 'folder5', 'folder6']
    >>> f2p.paths
    ['folder1', 'folder2', 'folder3', 'path4', 'folder5', 'path6']

    Attribute access and iteration are also supported:

    >>> 'folder1' in dir(f2p)
    True
    >>> f2p.folder1
    'folder1'
    >>> f2p.folder4
    'path4'

    >>> for folder, path in f2p:
    ...     print(folder, path)
    folder1 folder1
    folder2 folder2
    folder3 folder3
    folder4 path4
    folder5 folder5
    folder6 path6

    >>> len(f2p)
    6
    >>> bool(f2p)
    True
    >>> bool(Folder2Path())
    False
    """

    def __init__(self, *args, **kwargs):
        for arg in args:
            self.add(arg)
        for (key, value) in kwargs.items():
            self.add(key, value)

    def add(self, directory, path=None) -> None:
        """Add a directory and optionally its path."""
        objecttools.valid_variable_identifier(directory)
        if path is None:
            path = directory
        setattr(self, directory, path)

    @property
    def folders(self) -> List[str]:
        return [folder for folder, path in self]

    @property
    def paths(self) -> List[str]:
        return [path for folder, path in self]

    def __iter__(self):
        for key, value in sorted(vars(self).items()):
            yield key, value

    def __len__(self):
        return len(vars(self))

    def __str__(self):
        return ' '.join(repr(self).split())

    def __repr__(self):
        if self:
            args, kwargs = [], []
            for key, value in self:
                if key == value:
                    args.append(key)
                else:
                    kwargs.append(f'{key}={objecttools.repr_(value)}')
            lines = [f'            {arg},' for arg in args+kwargs]
            lines[0] = 'Folder2Path(' + lines[0][12:]
            lines[-1] = lines[-1][:-1] + ')'
            return '\n'.join(lines)
        return 'Folder2Path()'

    def __dir__(self):
        return objecttools.dir_(self)


class FileManager(object):
    """Base class for |NetworkManager|, |ControlManager|, |ConditionManager|,
    and |SequenceManager|.

    |FileManager| defines the general folder structure for storing
    network, control, condition, and time series files.  Generally,
    it is `projectdir/BASEDIR/currentdir/`; concretely, taking
    the (default) network working directory of example project
    `LahnHBV` as an example, it is `LahnHBV/network/default`.
    """

    BASEDIR: str
    DEFAULTDIR = None

    def __init__(self):
        self._projectdir = None
        try:
            self.projectdir = pub.projectname
        except RuntimeError:
            pass
        self._currentdir = None

    @propertytools.ProtectedProperty
    def projectdir(self) -> str:
        """The name of the main folder of a project.

        For the `LahnHBV` example project, |FileManager.projectdir| is
        (not surprisingly) `LahnHBV`, and is queried from the |pub| module.
        However, you can define or change |FileManager.projectdir|
        interactively, which can be usefull for more complex tasks like
        copying (parts of) projects:

        >>> from hydpy.core.filetools import FileManager
        >>> from hydpy import pub
        >>> pub.projectname = 'project_A'
        >>> filemanager = FileManager()
        >>> filemanager.projectdir
        'project_A'

        >>> del filemanager.projectdir
        >>> filemanager.projectdir
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `projectdir` \
of object `filemanager` has not been prepared so far.
        >>> filemanager.projectdir = 'project_B'
        >>> filemanager.projectdir
        'project_B'

        >>> del pub.projectname
        >>> FileManager().projectdir
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `projectdir` \
of object `filemanager` has not been prepared so far.
        """
        return self._projectdir

    @projectdir.setter_
    def projectdir(self, name):
        self._projectdir = name

    @projectdir.deleter_
    def projectdir(self):
        self._projectdir = None

    @property
    def basepath(self) -> str:
        """Absolute path pointing to the available working directories.

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> from hydpy import repr_, TestIO
        >>> with TestIO():
        ...     repr_(filemanager.basepath)   # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename'
        """
        return os.path.abspath(
            os.path.join(self.projectdir, self.BASEDIR))

    @property
    def availabledirs(self) -> Folder2Path:
        """Names and paths of the available working directories.

        Available working directories are those beeing stored in the
        base directory of the respective |FileManager| subclass.
        Folders with names starting with an underscore are ignored
        (use this for directories handling additional data files,
        if you like).  Zipped directories, which can be unpacked
        on the fly, do also count as available directories:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> import os
        >>> from hydpy import repr_, TestIO
        >>> TestIO.clear()
        >>> with TestIO():
        ...     os.makedirs('projectname/basename/folder1')
        ...     os.makedirs('projectname/basename/folder2')
        ...     open('projectname/basename/folder3.zip', 'w').close()
        ...     os.makedirs('projectname/basename/_folder4')
        ...     open('projectname/basename/folder5.tar', 'w').close()
        ...     filemanager.availabledirs   # doctest: +ELLIPSIS
        Folder2Path(folder1=.../projectname/basename/folder1,
                    folder2=.../projectname/basename/folder2,
                    folder3=.../projectname/basename/folder3.zip)
        """
        directories = Folder2Path()
        for directory in os.listdir(self.basepath):
            if not directory.startswith('_'):
                path = os.path.join(self.basepath, directory)
                if os.path.isdir(path):
                    directories.add(directory, path)
                elif directory.endswith('.zip'):
                    directories.add(directory[:-4], path)
        return directories

    @property
    def currentdir(self) -> str:
        """Name of the current working directory containing the relevant files.

        To show most of the functionality of |property|
        |FileManager.currentdir| (unpacking zip files on the fly is
        explained in the documentation on function
        (|FileManager.zip_currentdir|), we first prepare a |FileManager|
        object corresponding to the |FileManager.basepath|
        `projectname/basename`:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> import os
        >>> from hydpy import repr_, TestIO
        >>> TestIO.clear()
        >>> with TestIO():
        ...     os.makedirs('projectname/basename')
        ...     repr_(filemanager.basepath)    # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename'

        At first, the base directory is empty and asking for the
        current working directory results in the following error:

        >>> with TestIO():
        ...     filemanager.currentdir   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The current working directory of the FileManager object \
has not been defined manually and cannot be determined automatically: \
`.../projectname/basename` does not contain any available directories.

        If only one directory exists, it is considered as the current
        working directory automatically:

        >>> with TestIO():
        ...     os.mkdir('projectname/basename/dir1')
        ...     filemanager.currentdir
        'dir1'

        |property| |FileManager.currentdir| memorises the name of the
        current working directory, even if another directory is later
        added to the base path:

        >>> with TestIO():
        ...     os.mkdir('projectname/basename/dir2')
        ...     filemanager.currentdir
        'dir1'

        Set the value of |FileManager.currentdir| to |None| to let it
        forget the memorised directory.  After that, asking for the
        current working directory now results in another error, as
        it is not clear which directory to select:

        >>> with TestIO():
        ...     filemanager.currentdir = None
        ...     filemanager.currentdir   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The current working directory of the FileManager object \
has not been defined manually and cannot be determined automatically: \
`....../projectname/basename` does contain multiple available directories \
(dir1 and dir2).

        Setting |FileManager.currentdir| manually solves the problem:

        >>> with TestIO():
        ...     filemanager.currentdir = 'dir1'
        ...     filemanager.currentdir
        'dir1'

        Remove the current working directory `dir1` with the `del` statement:

        >>> with TestIO():
        ...     del filemanager.currentdir
        ...     os.path.exists('projectname/basename/dir1')
        False

        |FileManager| subclasses can define a default directory name.
        When many directories exist and none is selected manually, the
        default directory is selected automatically.  The following
        example shows an error message due to multiple directories
        without any having the default name:

        >>> with TestIO():
        ...     os.mkdir('projectname/basename/dir1')
        ...     filemanager.DEFAULTDIR = 'dir3'
        ...     del filemanager.currentdir
        ...     filemanager.currentdir   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The current working directory of the FileManager object \
has not been defined manually and cannot be determined automatically: The \
default directory (dir3) is not among the available directories (dir1 and dir2).

        We can fix this by adding the required default directory manually:

        >>> with TestIO():
        ...     os.mkdir('projectname/basename/dir3')
        ...     filemanager.currentdir
        'dir3'

        Setting the |FileManager.currentdir| to `dir4` not only overwrites
        the default name, but also creates the required folder:

        >>> with TestIO():
        ...     filemanager.currentdir = 'dir4'
        ...     filemanager.currentdir
        'dir4'
        >>> with TestIO():
        ...     sorted(os.listdir('projectname/basename'))
        ['dir1', 'dir2', 'dir3', 'dir4']

        Failed attempts in removing directories result in error messages
        like the following one:

        >>> import shutil
        >>> from unittest.mock import patch
        >>> with patch.object(shutil, 'rmtree', side_effect=AttributeError):
        ...     with TestIO():
        ...         del filemanager.currentdir   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: While trying to delete the current working directory \
`.../projectname/basename/dir4` of the FileManager object, the following \
error occurred: ...

        Then, the current working directory still exists and is remembered
        by |FileManager.currentdir|:

        >>> with TestIO():
        ...     filemanager.currentdir
        'dir4'
        >>> with TestIO():
        ...     sorted(os.listdir('projectname/basename'))
        ['dir1', 'dir2', 'dir3', 'dir4']
        """
        if self._currentdir is None:
            directories = self.availabledirs.folders
            if len(directories) == 1:
                self.currentdir = directories[0]
            elif self.DEFAULTDIR in directories:
                self.currentdir = self.DEFAULTDIR
            else:
                prefix = (f'The current working directory of the '
                          f'{objecttools.classname(self)} object '
                          f'has not been defined manually and cannot '
                          f'be determined automatically:')
                if not directories:
                    raise RuntimeError(
                        f'{prefix} `{objecttools.repr_(self.basepath)}` '
                        f'does not contain any available directories.')
                if self.DEFAULTDIR is None:
                    raise RuntimeError(
                        f'{prefix} `{objecttools.repr_(self.basepath)}` '
                        f'does contain multiple available directories '
                        f'({objecttools.enumeration(directories)}).')
                raise RuntimeError(
                    f'{prefix} The default directory ({self.DEFAULTDIR}) '
                    f'is not among the available directories '
                    f'({objecttools.enumeration(directories)}).')
        return self._currentdir

    @currentdir.setter
    def currentdir(self, directory):
        if directory is None:
            self._currentdir = None
        else:
            dirpath = os.path.join(self.basepath, directory)
            zippath = f'{dirpath}.zip'
            if os.path.exists(zippath):
                shutil.unpack_archive(
                    filename=zippath,
                    extract_dir=self.basepath,
                    format='zip',
                )
                os.remove(zippath)
            elif not os.path.exists(dirpath):
                os.makedirs(dirpath)
            self._currentdir = str(directory)

    @currentdir.deleter
    def currentdir(self):
        path = os.path.join(self.basepath, self.currentdir)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to delete the current working '
                    f'directory `{objecttools.repr_(path)}` of the '
                    f'{objecttools.classname(self)} object')
        self._currentdir = None

    @property
    def currentpath(self) -> str:
        """Absolute path of the current working directory.

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> from hydpy import repr_, TestIO
        >>> with TestIO():
        ...     filemanager.currentdir = 'testdir'
        ...     repr_(filemanager.currentpath)    # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename/testdir'
        """
        return os.path.join(self.basepath, self.currentdir)

    @property
    def filenames(self) -> List[str]:
        """Names of the files contained in the the current working directory.

        Files names starting with underscores are ignored:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> from hydpy import TestIO
        >>> with TestIO():
        ...     filemanager.currentdir = 'testdir'
        ...     open('projectname/basename/testdir/file1.txt', 'w').close()
        ...     open('projectname/basename/testdir/file2.npy', 'w').close()
        ...     open('projectname/basename/testdir/_file1.nc', 'w').close()
        ...     filemanager.filenames
        ['file1.txt', 'file2.npy']
        """
        return sorted(
            fn for fn in os.listdir(self.currentpath)
            if not fn.startswith('_'))

    @property
    def filepaths(self) -> List[str]:
        """Absolute path names of the files contained in the current
        working directory.

        Files names starting with underscores are ignored:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> from hydpy import repr_, TestIO
        >>> with TestIO():
        ...     filemanager.currentdir = 'testdir'
        ...     open('projectname/basename/testdir/file1.txt', 'w').close()
        ...     open('projectname/basename/testdir/file2.npy', 'w').close()
        ...     open('projectname/basename/testdir/_file1.nc', 'w').close()
        ...     for filepath in filemanager.filepaths:
        ...         repr_(filepath)    # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename/testdir/file1.txt'
        '...hydpy/tests/iotesting/projectname/basename/testdir/file2.npy'
        """
        path = self.currentpath
        return [os.path.join(path, name) for name in self.filenames]

    def zip_currentdir(self) -> None:
        """Pack the current working directory in a `zip` file.

        |FileManager| subclasses allow for manual packing and automatic
        unpacking of working directories.  The only supported format is `zip`.
        To avoid possible inconsistencies, origin directories and zip
        files are removed after packing or unpacking, respectively.

        As an example scenario, we prepare a |FileManager| object with
        the current working directory `folder` containing the files
        `test1.txt` and `text2.txt`:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = 'basename'
        >>> filemanager.projectdir = 'projectname'
        >>> import os
        >>> from hydpy import repr_, TestIO
        >>> TestIO.clear()
        >>> basepath = 'projectname/basename'
        >>> with TestIO():
        ...     os.makedirs(basepath)
        ...     filemanager.currentdir = 'folder'
        ...     open(f'{basepath}/folder/file1.txt', 'w').close()
        ...     open(f'{basepath}/folder/file2.txt', 'w').close()
        ...     filemanager.filenames
        ['file1.txt', 'file2.txt']

        The directories existing under the base path are identical
        with the ones returned by property |FileManager.availabledirs|:

        >>> with TestIO():
        ...     sorted(os.listdir(basepath))
        ...     filemanager.availabledirs    # doctest: +ELLIPSIS
        ['folder']
        Folder2Path(folder=.../projectname/basename/folder)

        After packing the current working directory manually, it is
        still counted as a available directory:

        >>> with TestIO():
        ...     filemanager.zip_currentdir()
        ...     sorted(os.listdir(basepath))
        ...     filemanager.availabledirs    # doctest: +ELLIPSIS
        ['folder.zip']
        Folder2Path(folder=.../projectname/basename/folder.zip)

        The zip file is unpacked again, as soon as `folder` becomes
        the current working directory:

        >>> with TestIO():
        ...     filemanager.currentdir = 'folder'
        ...     sorted(os.listdir(basepath))
        ...     filemanager.availabledirs
        ...     filemanager.filenames    # doctest: +ELLIPSIS
        ['folder']
        Folder2Path(folder=.../projectname/basename/folder)
        ['file1.txt', 'file2.txt']
        """
        shutil.make_archive(
            base_name=self.currentpath,
            format='zip',
            root_dir=self.basepath,
            base_dir=self.currentdir,
        )
        del self.currentdir

    def __dir__(self):
        return objecttools.dir_(self)


class NetworkManager(FileManager):
    """Manager for network files.

    The base and default folder names of class |NetworkManager| are:

    >>> from hydpy.core.filetools import NetworkManager
    >>> NetworkManager.BASEDIR
    'network'
    >>> NetworkManager.DEFAULTDIR
    'default'

    The general handling of (the folder structure) of class |NetworkManager|
    is explained by the documentation on its parent class |FileManager|.
    The following examples deal with reading, writing, and removing
    network files.  For this purpose, we prepare example project `LahnHBV`
    in the `iotesting` directory by calling function |prepare_full_example_1|:

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    The complete network structure of an `HydPy` project is defined by
    an arbitrary number of "network files".  These are valid Python
    files which define certain |Node| and |Element| objects as well as
    their connections.  Network files are allowed to overlap, meaning
    two or more files can define the same objects (in a consistent manner
    only, of course).  The primary purpose of class |NetworkManager| is
    to execute each network file individually and pass its content to
    a separate |Selection| which is the done by method
    |NetworkManager.load_files|:

    >>> networkmanager = NetworkManager()
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     networkmanager.projectdir = 'LahnHBV'
    ...     selections = networkmanager.load_files()

    File names are taken as selection names (without file endings).
    Additionally, |NetworkManager.load_files| creates a "complete"
    selection including all |Node| and |Element| objects of the file
    specific selections:

    >>> selections
    Selections("headwaters", "nonheadwaters", "streams", "complete")
    >>> selections.headwaters
    Selection("headwaters",
              elements=("land_dill", "land_lahn_1"),
              nodes=("dill", "lahn_1"))
    >>> selections.complete
    Selection("complete",
              elements=("land_dill", "land_lahn_1", "land_lahn_2",
                        "land_lahn_3", "stream_dill_lahn_2",
                        "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"),
              nodes=("dill", "lahn_1", "lahn_2", "lahn_3"))

    Method ... ToDo

    >>> import os
    >>> with TestIO():
    ...     networkmanager.currentdir = 'testdir'
    ...     networkmanager.save_files(selections)
    ...     sorted(os.listdir('LahnHBV/network/testdir'))
    ['headwaters.py', 'nonheadwaters.py', 'streams.py']

    >>> with TestIO():
    ...     selections == networkmanager.load_files()
    True

    >>> selections -= selections.streams
    >>> with TestIO():
    ...     networkmanager.delete_files(selections)
    ...     sorted(os.listdir('LahnHBV/network/testdir'))
    ['streams.py']

    >>> with TestIO():
    ...     networkmanager.delete_files(['headwaters'])   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to remove the network files of selections \
`['headwaters']`, the following error occurred: ...

    >>> with TestIO():
    ...     with open('LahnHBV/network/testdir/streams.py', 'w') as wrongfile:
    ...         _ = wrongfile.write('x = y')
    ...     networkmanager.load_files()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    NameError: While trying to load the network file `...streams.py`, the \
following error occurred: name 'y' is not defined

    >>> with TestIO():
    ...     with open('LahnHBV/network/testdir/streams.py', 'w') as wrongfile:
    ...         _ = wrongfile.write('from hydpy import Node')
    ...     networkmanager.load_files()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: The class Element cannot be loaded from the network file \
`...streams.py`.

    >>> with TestIO():
    ...     with open('LahnHBV/network/testdir/streams.py', 'w') as wrongfile:
    ...         _ = wrongfile.write('from hydpy import Element')
    ...     networkmanager.load_files()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: The class Node cannot be loaded from the network file \
`...streams.py`.

    >>> import shutil
    >>> with TestIO():
    ...     shutil.rmtree('LahnHBV/network/testdir')
    ...     networkmanager.save_files(selections)   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to save selections \
`Selections("headwaters", "nonheadwaters", "complete")` into network files, \
the following error occurred: ...
    """

    BASEDIR = 'network'
    DEFAULTDIR = 'default'

    def load_files(self) -> selectiontools.Selections:
        """Read all network files of the current working directory, structure
        their contents in a |selectiontools.Selections| object, and return it.
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
                    f'While trying to load the network file `{path}`')
            try:
                selections += selectiontools.Selection(
                    filename.split('.')[0],
                    info['Node'].gather_new_nodes(),
                    info['Element'].gather_new_elements())
            except KeyError as exc:
                raise RuntimeError(
                    f'The class {exc.args[0]} cannot be loaded from the '
                    f'network file `{path}`.')
        selections += selectiontools.Selection(
            'complete',
            info['Node'].registered_nodes(),
            info['Element'].registered_elements())
        return selections

    def save_files(self, selections) -> None:
        """Save the |Selection| objects contained in the given |Selections|
        instance to separate network files."""
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

    def delete_files(self, selections) -> None:
        """Delete the network files corresponding to the given selections
        (e.g. a |list| of |str| objects or a |Selections| object)."""
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
                f'While trying to remove the network files of '
                f'selections `{selections}`')


class ControlManager(FileManager):
    """Manager for control parameter files."""

    # The following file path to content mapping is used to circumvent reading
    # the same auxiliary control parameter file from disk multiple times.
    _registry = {}
    _workingpath = '.'
    BASEDIR = 'control'
    DEFAULTDIR = 'default'

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

    BASEDIR = 'conditions'
    DEFAULTDIR = None

    def load_file(self, filename):
        """Read and return the content of the given file.

        If the current directory is not defined explicitly, the directory
        name is constructed with the actual simulation start date.  If
        such an directory does not exist, it is created immediately.
        """
        _defaultdir = self.DEFAULTDIR
        try:
            if not filename.endswith('.py'):
                filename += '.py'
            try:
                self.DEFAULTDIR = (
                    'init_' + pub.timegrids.sim.firstdate.to_string('os'))
            except KeyError:
                pass
            filepath = os.path.join(self.currentpath, filename)
            with open(filepath) as file_:
                return file_.read()
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to read the conditions file `%s`'
                % filename)
        finally:
            self.DEFAULTDIR = _defaultdir

    def save_file(self, filename, text):
        """Save the given text under the given condition filename and the
        current path.

        If the current directory is not defined explicitly, the directory
        name is constructed with the actual simulation end date.  If
        such an directory does not exist, it is created immediately.
        """
        _defaultdir = self.DEFAULTDIR
        try:
            if not filename.endswith('.py'):
                filename += '.py'
            try:
                self.DEFAULTDIR = (
                    'init_' + pub.timegrids.sim.lastdate.to_string('os'))
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
            self.DEFAULTDIR = _defaultdir


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
        if not os.path.exists(abspath):
            os.makedirs(abspath)
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
    In the following examples, show the essential features of class
    |SequenceManager| based on the example project configuratio defined
    by function |prepare_io_example_1|:

    (1) We prepare the project and select one 0-dimensional sequence of type
    |Sim| and one 1-dimensional sequence of type |lland_fluxes.NKor| for the
    following examples:

    >>> from hydpy.core.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()
    >>> sim = nodes.node2.sequences.sim
    >>> nkor = elements.element2.model.sequences.fluxes.nkor

    (2) We store the time series data of both sequences in ASCII files
    (Methods |SequenceManager.save_file| and |IOSequence.save_ext| are
    interchangeable here.  The last one is only a convenience function
    for the first one):

    >>> from hydpy import pub
    >>> pub.sequencemanager.generalfiletype = 'asc'
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.save_file(sim)
    ...     nkor.save_ext()

    (3) To check that this was successful, we can load the file content from
    the output directory defined by |prepare_io_example_1| and print it:

    >>> import os
    >>> from hydpy import round_
    >>> def print_file(path, filename):
    ...     path = os.path.join(path, filename)
    ...     with TestIO():
    ...         with open(path) as file_:
    ...             lines = file_.readlines()
    ...     print(''.join(lines[:3]), end='')
    ...     for line in lines[3:]:
    ...         round_([float(x) for x in line.split()])
    >>> print_file('nodepath', 'node2_sim_t.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    64.0
    65.0
    66.0
    67.0
    >>> print_file('outputpath', 'element2_flux_nkor.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    16.0, 17.0
    18.0, 19.0
    20.0, 21.0
    22.0, 23.0

    (4) To show that reloading the data works, we set the values of the
    time series of both objects to zero and recover the original values
    afterwards:

    >>> sim.series = 0.0
    >>> sim.series
    InfoArray([ 0.,  0.,  0.,  0.])
    >>> nkor.series = 0.0
    >>> nkor.series
    InfoArray([[ 0.,  0.],
               [ 0.,  0.],
               [ 0.,  0.],
               [ 0.,  0.]])
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(sim)
    ...     nkor.load_ext()
    >>> sim.series
    InfoArray([ 64.,  65.,  66.,  67.])
    >>> nkor.series
    InfoArray([[ 16.,  17.],
               [ 18.,  19.],
               [ 20.,  21.],
               [ 22.,  23.]])

    (5) Wrongly formatted ASCII files should result in understandable error
    messages:

    >>> path = os.path.join('nodepath', 'node2_sim_t.asc')
    >>> with TestIO():
    ...     with open(path) as file_:
    ...         right = file_.read()
    ...     wrong = right.replace('Timegrid', 'timegrid')
    ...     with open(path, 'w') as file_:
    ...         _ = file_.write(wrong)
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(sim)
    Traceback (most recent call last):
    ...
    NameError: While trying to load the external data of sequence `sim` of \
node `node2`, the following error occurred: name 'timegrid' is not defined

    (6) By default, overwriting existing time series files is disabled:

    >>> with TestIO():
    ...     sim.save_ext()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    OSError: While trying to save the external data of sequence `sim` of \
node `node2`, the following error occurred: Sequence `sim` of node `node2` \
is not allowed to overwrite the existing file `...`.
    >>> pub.sequencemanager.generaloverwrite = True
    >>> with TestIO():
    ...     sim.save_ext()

    (7) When a sequence comes with a weighting parameter referenced by
    |property| |Variable.refweights|, one can save the averaged time
    series by using function |IOSequence.save_mean|:

    >>> with TestIO():
    ...     nkor.save_mean()
    >>> print_file('outputpath', 'element2_flux_nkor_mean.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    16.5
    18.5
    20.5
    22.5

    (8) Method |IOSequence.save_mean| is strongly related with method
    |IOSequence.average_series|, meaning one can pass the same arguments.
    We show this by changing the land use classes of `element2` (parameter
    |lland_control.Lnk|) to field (|lland_constants.ACKER|) and water
    (|lland_constants.WASSER|), and averaging the values of sequence
    |lland_fluxes.NKor| for the single area of type field only:

    >>> from hydpy.models.lland_v1 import ACKER, WASSER
    >>> nkor.subseqs.seqs.model.parameters.control.lnk = ACKER, WASSER
    >>> with TestIO():
    ...     nkor.save_mean('acker')
    >>> print_file('outputpath', 'element2_flux_nkor_mean.asc')
    Timegrid('2000-01-01 00:00:00+01:00',
             '2000-01-05 00:00:00+01:00',
             '1d')
    16.0
    18.0
    20.0
    22.0

    (9) Another option is to store data using |numpy| binary files, which
    is a good option for saving computation times, but a bad option for
    sharing data with colleagues:

    >>> pub.sequencemanager.generalfiletype = 'npy'
    >>> with TestIO():
    ...     sim.save_ext()
    ...     nkor.save_ext()

    (10) The time information (without time zone information) is available
    within the first thirteen entries:

    >>> path = os.path.join('nodepath', 'node2_sim_t.npy')
    >>> from hydpy import numpy, print_values
    >>> with TestIO():
    ...     print_values(numpy.load(path))
    2000.0, 1.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 1.0, 5.0, 0.0, 0.0, 0.0,
    86400.0, 64.0, 65.0, 66.0, 67.0

    (11) Reloading the data works as expected:

    >>> sim.series = 0.0
    >>> nkor.series = 0.0
    >>> with TestIO():
    ...     sim.load_ext()
    ...     nkor.load_ext()
    >>> sim.series
    InfoArray([ 64.,  65.,  66.,  67.])
    >>> nkor.series
    InfoArray([[ 16.,  17.],
               [ 18.,  19.],
               [ 20.,  21.],
               [ 22.,  23.]])

    (12) Writing mean vlues into |numpy| binary files is also supported:

    >>> import numpy
    >>> with TestIO():
    ...     nkor.save_mean('wasser')
    ...     numpy.load(os.path.join('outputpath',
    ...                             'element2_flux_nkor_mean.npy'))[-4:]
    array([ 17.,  19.,  21.,  23.])

    (13) Generally, trying to load data for "not activated" sequences
    results in the following error message:

    >>> nkor.deactivate_ram()
    >>> with TestIO(clear_all=True):
    ...     pub.sequencemanager.save_file(nkor)
    Traceback (most recent call last):
    ...
    RuntimeError: Sequence `nkor` of element `element2` is not requested \
to make any internal data available to the user.

    The third option to store data in netCDF files, which is explained
    separately in the documentation on class |NetCDFInterface|.
    """

    SUPPORTED_MODES = ('npy', 'asc', 'nc')
    BASEDIR = 'series'
    DEFAULTDIR = None

    inputdir = _DescriptorDir('input', 'input')   # ToDo: can be removed?
    fluxdir = _DescriptorDir('output', 'flux')
    statedir = _DescriptorDir('output', 'state')
    nodedir = _DescriptorDir('node', 'node')
    tempdir = _DescriptorDir('temp', 'temporary')
    generaldir = _GeneralDescriptor(inputdir,
                                    fluxdir,
                                    statedir,
                                    nodedir,
                                    tempdir)

    inputfiletype = _DescriptorType('npy', 'input')
    fluxfiletype = _DescriptorType('npy', 'flux')
    statefiletype = _DescriptorType('npy', 'state')
    nodefiletype = _DescriptorType('npy', 'node')
    tempfiletype = _DescriptorType('npy', 'temporary')
    generalfiletype = _GeneralDescriptor(inputfiletype,
                                         fluxfiletype,
                                         statefiletype,
                                         nodefiletype,
                                         tempfiletype)

    inputoverwrite = _DescriptorOverwrite(False, 'input')
    fluxoverwrite = _DescriptorOverwrite(False, 'flux')
    stateoverwrite = _DescriptorOverwrite(False, 'state')
    nodeoverwrite = _DescriptorOverwrite(False, 'node')
    tempoverwrite = _DescriptorOverwrite(False, 'temporary')
    generaloverwrite = _GeneralDescriptor(inputoverwrite,
                                          fluxoverwrite,
                                          stateoverwrite,
                                          nodeoverwrite,
                                          tempoverwrite)

    inputdirpath = _DescriptorPath('inputdir', 'input')
    fluxdirpath = _DescriptorPath('fluxdir', 'flux')
    statedirpath = _DescriptorPath('statedir', 'state')
    nodedirpath = _DescriptorPath('nodedir', 'node')
    tempdirpath = _DescriptorPath('tempdir', 'temporary')
    generaldirpath = _GeneralDescriptor(inputdirpath,
                                        fluxdirpath,
                                        statedirpath,
                                        nodedirpath,
                                        tempdirpath)

    inputaggregation = _DescriptorAggregate('none', 'input')
    fluxaggregation = _DescriptorAggregate('none', 'flux')
    stateaggregation = _DescriptorAggregate('none', 'state')
    nodeaggregation = _DescriptorAggregate('none', 'node')
    generalaggregation = _GeneralDescriptor(inputaggregation,
                                            fluxaggregation,
                                            stateaggregation,
                                            nodeaggregation)

    def __init__(self):
        FileManager.__init__(self)
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
            if sequence.filetype_ext == 'nc':
                self._save_nc(sequence, array)
            else:
                filepath = sequence.filepath_ext
                if ((array is not None) and
                        (array.info['type'] != 'unmodified')):
                    filepath = (f'{filepath[:-4]}_{array.info["type"]}'
                                f'{filepath[-4:]}')
                if not sequence.overwrite_ext and os.path.exists(filepath):
                    raise OSError(
                        f'Sequence {objecttools.devicephrase(sequence)} '
                        f'is not allowed to overwrite the existing file '
                        f'`{sequence.filepath_ext}`.')
                if sequence.filetype_ext == 'npy':
                    self._save_npy(array, filepath)
                elif sequence.filetype_ext == 'asc':
                    self._save_asc(array, filepath)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to save the external data of sequence %s'
                % objecttools.devicephrase(sequence))

    @staticmethod
    def _save_npy(array, filepath):
        numpy.save(filepath, pub.timegrids.init.array2series(array))

    @staticmethod
    def _save_asc(array, filepath):
        with open(filepath, 'w') as file_:
            file_.write(
                pub.timegrids.init.assignrepr(
                    prefix='',
                    style='iso2',
                    utcoffset=pub.options.utcoffset) + '\n')
        with open(filepath, 'ab') as file_:
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

    def open_netcdf_reader(self, flatten=False, isolate=False, timeaxis=1):
        """Prepare a new |NetCDFInterface| object for reading data."""
        self._netcdf_reader = netcdftools.NetCDFInterface(
            flatten=bool(flatten),
            isolate=bool(isolate),
            timeaxis=int(timeaxis))

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

    def open_netcdf_writer(self, flatten=False, isolate=False, timeaxis=1):
        """Prepare a new |NetCDFInterface| object for writing data."""
        self._netcdf_writer = netcdftools.NetCDFInterface(
            flatten=bool(flatten),
            isolate=bool(isolate),
            timeaxis=int(timeaxis))

    def close_netcdf_writer(self):
        """Write data with a prepared |NetCDFInterface| object and remove it.
        """
        self._netcdf_writer.write()
        self._netcdf_writer = None


autodoctools.autodoc_module()
