# -*- coding: utf-8 -*-
"""This module implements tools for handling the sequences (time series)
of hydrological models.
"""
# import...
# ...from standard library
from typing import ClassVar
import copy
import os
import struct
import sys
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import variabletools
from hydpy.cythons import pointerutils


class InfoArray(numpy.ndarray):
    """|numpy| |numpy.ndarray| subclass that stores and tries to keep
    an additional `info` attribute.

    >>> from hydpy.core.sequencetools import InfoArray
    >>> array = InfoArray([1.0, 2.0], info='this array is short')
    >>> array
    InfoArray([ 1.,  2.])
    >>> array.info
    'this array is short'
    >>> subarray = array[:1]
    >>> subarray
    InfoArray([ 1.])
    >>> subarray.info
    'this array is short'
    """

    def __new__(cls, array, info=None):
        obj = numpy.asarray(array).view(cls)
        obj.info = info
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.info = getattr(obj, 'info', None)


class Sequences(object):
    """Handles all sequences of a specific model."""

    _NAMES_SUBSEQS = ('inlets', 'receivers', 'inputs', 'fluxes', 'states',
                      'logs', 'aides', 'outlets', 'senders')

    def __init__(self, **kwargs):
        self.model = kwargs.pop('model', None)
        cythonmodule = kwargs.pop('cythonmodule', None)
        cymodel = kwargs.pop('cymodel', None)
        for (name, cls) in kwargs.items():
            if name.endswith('Sequences') and issubclass(cls, SubSequences):
                if cythonmodule:
                    cls_fastaccess = getattr(cythonmodule, name)
                    subseqs = cls(self, cls_fastaccess, cymodel)
                else:
                    subseqs = cls(self, None, None)
                setattr(self, subseqs.name, subseqs)

    def _yield_iosubsequences(self):
        for subseqs in self:
            if isinstance(subseqs, abctools.IOSequencesABC):
                yield subseqs

    def activate_disk(self, names=None):
        """Call method |IOSequences.activate_disk| of all handled
        |IOSequences| objects."""
        for subseqs in self._yield_iosubsequences():
            subseqs.activate_disk(names)

    def deactivate_disk(self, names=None):
        """Call method |IOSequences.deactivate_disk| of all handled
        |IOSequences| objects."""
        for subseqs in self._yield_iosubsequences():
            subseqs.deactivate_disk(names)

    def activate_ram(self, names=None):
        """Call method |IOSequences.activate_ram| of all handled
        |IOSequences| objects."""
        for subseqs in self._yield_iosubsequences():
            subseqs.activate_ram(names)

    def deactivate_ram(self, names=None):
        """Call method |IOSequences.deactivate_ram| of all handled
        |IOSequences| objects."""
        for subseqs in self._yield_iosubsequences():
            subseqs.deactivate_ram(names)

    def open_files(self, idx=0):
        """Call method |IOSequences.open_files| of all handled
        |IOSequences| objects."""
        for subseqs in self._yield_iosubsequences():
            subseqs.open_files(idx)

    def close_files(self):
        """Call method |IOSequences.close_files| of all handled
        |IOSequences| objects."""
        for subseqs in self._yield_iosubsequences():
            subseqs.close_files()

    def load_data(self, idx):
        """Call method |InputSequences.load_data| of all handled
        |InputSequences| objects."""
        for subseqs in self:
            if isinstance(subseqs, abctools.InputSequencesABC):
                subseqs.load_data(idx)

    def save_data(self, idx):
        """Call method `save_data|` of all handled |IOSequences|
        objects registered under |OutputSequencesABC|."""
        for subseqs in self:
            if isinstance(subseqs, abctools.OutputSequencesABC):
                subseqs.save_data(idx)

    def reset(self):
        """Call method |ConditionSequence.reset| of all handled
        |ConditionSequence| objects."""
        for subseqs in self:
            if isinstance(subseqs, abctools.ConditionSequenceABC):
                subseqs.reset()

    def __iter__(self):
        for name in self._NAMES_SUBSEQS:
            subseqs = getattr(self, name, None)
            if subseqs is not None:
                yield subseqs

    @property
    def conditions(self):
        """Generator object yielding all conditions (|StateSequence| and
        |LogSequence| objects).
        """
        for subseqs in ('states', 'logs'):
            for tuple_ in getattr(self, subseqs, ()):
                yield tuple_

    @property
    def hasconditions(self):
        """True or False, whether the |Sequences| object "handles conditions"
        or not (at least one |StateSequence| or |LogSequence| object)."""
        for _ in self.conditions:
            return True
        return False

    @property
    def _conditiondefaultfilename(self):
        filename = objecttools.devicename(self)
        if filename == '?':
            raise RuntimeError(
                'To load or save the conditions of a model from or to a file, '
                'its filename must be known.  This can be done, by passing '
                'filename to method `load_conditions` or `save_conditions` '
                'directly.  But in complete HydPy applications, it is usally '
                'assumed to be consistent with the name of the element '
                'handling the model.  Actually, neither a filename is given '
                'nor does the model know its master element.')
        else:
            return filename + '.py'

    def load_conditions(self, filename=None):
        """Read the initial conditions from a file and assign them to the
        respective |StateSequence| and/or |LogSequence| objects handled by
        the actual |Sequences| object.

        If no filename or dirname is passed, the ones defined by the
        |ConditionManager| stored in module |pub| are used.
        """
        if self.hasconditions:
            if not filename:
                filename = self._conditiondefaultfilename
            namespace = locals()
            for seq in self.conditions:
                namespace[seq.name] = seq
            namespace['model'] = self
            code = pub.conditionmanager.load_file(filename)
            try:
                exec(code)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to gather initial conditions of element %s'
                    % objecttools.devicename(self))

    def save_conditions(self, filename=None):
        """Query the actual conditions of the |StateSequence| and/or
        |LogSequence| objects handled by the actual |Sequences| object and
        write them into a initial condition file.

        If no filename or dirname is passed, the ones defined by the
        |ConditionManager| stored in module |pub| are used.
        """
        if self.hasconditions:
            if filename is None:
                filename = self._conditiondefaultfilename
            con = pub.controlmanager
            lines = ['# -*- coding: utf-8 -*-\n\n',
                     'from hydpy.models.%s import *\n\n' % self.model,
                     'controlcheck(projectdir="%s", controldir="%s")\n\n'
                     % (con.projectdir, con.currentdir)]
            for seq in self.conditions:
                lines.append(repr(seq) + '\n')
            pub.conditionmanager.save_file(filename, ''.join(lines))

    def trim_conditions(self):
        """Call method |trim| of each handled |ConditionSequence|."""
        for seq in self.conditions:
            seq.trim()

    def __len__(self):
        return len(dict(self))


class SubSequences(variabletools.SubVariables):
    """Base class for handling subgroups of sequences.

    Attributes:
      * vars: The parent |Sequences| object.
      * seqs: The parent |Sequences| object.
      * fastaccess: The  |sequencetools.FastAccess| object allowing fast
        access to the sequence values. In `Cython` mode, model specific
        cdef classes are applied.

    See the documentation of similar class |SubParameters| for further
    information.  But note the difference, that model developers should
    not subclass |SubSequences| directly, but specialized subclasses
    like |FluxSequences| or |StateSequences| instead.
    """
    CLASSES = ()
    VARTYPE = abctools.SequenceABC

    def __init__(self, variables, cls_fastaccess=None, cymodel=None):
        self.seqs = variables
        variabletools.SubVariables.__init__(
            self, variables, cls_fastaccess, cymodel)

    def _init_fastaccess(self, cls_fastaccess, cymodel):
        if cls_fastaccess is None:
            self.fastaccess = FastAccess()
        else:
            self.fastaccess = cls_fastaccess()
            setattr(cymodel.sequences, self.name, self.fastaccess)

    @property
    def name(self):
        """The classname in lower case letters ommiting the last
        eight characters ("equences").

        >>> from hydpy.core.sequencetools import SubSequences
        >>> class StateSequences(SubSequences):
        ...     CLASSES = ()
        >>> StateSequences(None).name
        'states'
        """
        return objecttools.instancename(self)[:-8]


class IOSequences(SubSequences):
    CLASSES = ()

    def open_files(self, idx=0):
        self.fastaccess.open_files(idx)

    def close_files(self):
        self.fastaccess.close_files()

    def activate_ram(self):
        for seq in self:
            seq.activate_ram()

    def deactivate_ram(self):
        for seq in self:
            seq.deactivate_ram()

    def activate_disk(self):
        for seq in self:
            seq.activate_disk()

    def deactivate_disk(self):
        for seq in self:
            seq.deactivate_disk()

    def ram2disk(self):
        for seq in self:
            seq.ram2disk()

    def disk2ram(self):
        for seq in self:
            seq.disk2ram()


abctools.IOSequencesABC.register(IOSequences)


class InputSequences(IOSequences):
    """Base class for handling input sequences."""
    CLASSES = ()

    def load_data(self, idx):
        self.fastaccess.load_data(idx)


abctools.InputSequencesABC.register(InputSequences)


class FluxSequences(IOSequences):
    """Base class for handling flux sequences."""
    CLASSES = ()

    @property
    def name(self):
        """`fluxes`"""
        return 'fluxes'

    def save_data(self, idx):
        self.fastaccess.save_data(idx)

    @property
    def numerics(self):
        """Iterator for `numerical` flux sequences.

        `numerical` means that the `NUMERIC` class attribute of the
        respective sequence is `True`.
        """
        for flux in self:
            if flux.NUMERIC:
                yield flux


abctools.OutputSequencesABC.register(FluxSequences)


class StateSequences(IOSequences):
    """Base class for handling state sequences."""
    CLASSES = ()

    def _init_fastaccess(self, cls_fastaccess, cymodel):
        IOSequences._init_fastaccess(self, cls_fastaccess, cymodel)
        self.fastaccess_new = self.fastaccess
        if cls_fastaccess is None:
            self.fastaccess_old = FastAccess()
        else:
            setattr(cymodel.sequences, 'new_states', self.fastaccess)
            self.fastaccess_old = cls_fastaccess()
            setattr(cymodel.sequences, 'old_states', self.fastaccess_old)

    def new2old(self):
        """Assign the new/final state values of the actual time step to the
        new/initial state values of the next time step.
        """
        for seq in self:
            seq.new2old()

    def save_data(self, idx):
        self.fastaccess.save_data(idx)

    def reset(self):
        for seq in self:
            seq.reset()


abctools.OutputSequencesABC.register(StateSequences)


class LogSequences(SubSequences):
    """Base class for handling log sequences."""
    CLASSES = ()

    def reset(self):
        for seq in self:
            seq.reset()


class AideSequences(SubSequences):
    """Base class for handling aide sequences."""
    CLASSES = ()


class LinkSequences(SubSequences):
    """Base class for handling link sequences."""
    CLASSES = ()


class Sequence(variabletools.Variable):
    """Base class for defining different kinds of sequences."""

    NDIM, NUMERIC, TYPE = 0, False, float

    NOT_DEEPCOPYABLE_MEMBERS = ('subseqs', 'fastaccess')

    def __init__(self):
        self.subseqs = None
        self.fastaccess = objecttools.FastAccess()
        self.diskflag = False
        self.ramflag = False

    @property
    def subvars(self):
        """Alias for `subseqs`."""
        return self.subseqs

    def connect(self, subseqs):
        self.subseqs = subseqs
        self.fastaccess = subseqs.fastaccess
        self._connect_subattr('ndim', self.NDIM)
        self._connect_subattr('length', 0)
        for idx in range(self.NDIM):
            self._connect_subattr('length_%d' % idx, 0)
        self.diskflag = False
        self.ramflag = False
        try:
            self._connect_subattr('file', '')
        except AttributeError:
            pass
        self._initvalues()

    def _connect_subattr(self, suffix, value):
        setattr(self.fastaccess, '_%s_%s' % (self.name, suffix), value)

    def __call__(self, *args):
        """The prefered way to pass values to |Sequence| instances
        within initial condition files.
        """
        self.values = args

    @property
    def initvalue(self):
        if pub.options.usedefaultvalues:
            initvalue = getattr(self, 'INIT', None)
            if initvalue is None:
                initvalue = 0.
        else:
            initvalue = numpy.nan
        return initvalue

    def _initvalues(self):
        value = None if self.NDIM else self.initvalue
        setattr(self.fastaccess, self.name, value)

    @property
    def value(self):
        """The actual time series value(s) handled by the respective
        |Sequence| instance.  For consistency, `value` and `values`
        can always be used interchangeably.
        """
        value = getattr(self.fastaccess, self.name, None)
        if value is None:
            raise RuntimeError(
                'No value/values of sequence %s has/have been defined so far.'
                % objecttools.devicephrase(self))
        else:
            if self.NDIM:
                value = numpy.asarray(value)
            return value

    @value.setter
    def value(self, value):
        if self.NDIM == 0:
            try:
                temp = value[0]
                if len(value) > 1:
                    raise ValueError(
                        '%d values are assigned to the scalar sequence %s, '
                        'which is ambiguous.'
                        % (len(value), objecttools.devicename(self)))
                value = temp
            except (TypeError, IndexError):
                pass
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise TypeError(
                    'When trying to set the value of sequence %s,  it '
                    'was not possible to convert value `%s` to float.'
                    % (objecttools.devicename(self), value))
        else:
            try:
                value = value.value
            except AttributeError:
                pass
            try:
                value = numpy.full(self.shape, value, dtype=float)
            except ValueError:
                raise ValueError(
                    'For sequence %s setting new values failed.  The '
                    'values `%s` cannot be converted to a numpy ndarray '
                    'with shape %s containing entries of type float.'
                    % (objecttools.devicephrase(self),
                       value, self.shape))
        setattr(self.fastaccess, self.name, value)

    def __repr__(self):
        islong = len(self) > 255
        return variabletools.Variable.to_repr(self, self.values, islong)

    def __dir__(self):
        return objecttools.dir_(self)


abctools.SequenceABC.register(Sequence)


class _IOProperty(propertytools.DefaultProperty):

    DOCSTRING: ClassVar[str]

    def __init__(self):
        super().__init__(fget=self.__fget)

    def __set_name__(self, objtype, name):
        super().__set_name__(objtype, name)
        attr_seq = self.name
        cls = objecttools.classname(self.objtype)
        attr_man = f'{cls.lower()[:-8]}{self.name.split("_")[0]}'
        self.__attr_manager = attr_man
        self.__doc__ = f"""
            {self.DOCSTRING}

        Attribute {attr_seq} is connected with attribute {attr_man} of 
        class |SequenceManager|, as shown by the following technical 
        example (see the documentation on class |IOSequence| for some 
        explanations on the usage of this and similar properties of 
        |IOSequence| subclasses):

        >>> from hydpy.core.filetools import SequenceManager
        >>> temp = SequenceManager.{attr_man}
        >>> SequenceManager.{attr_man} = 'global'
        >>> from hydpy import pub
        >>> pub.sequencemanager = SequenceManager()
        >>> from hydpy.core.sequencetools import {cls}
        >>> sequence = {cls}()
        >>> sequence.{attr_seq}
        'global'
        >>> sequence.{attr_seq} = 'local'
        >>> sequence.{attr_seq}
        'local'
        >>> del sequence.{attr_seq}
        >>> sequence.{attr_seq}
        'global'
        >>> SequenceManager.{attr_man} = temp
        """

    def __fget(self, obj):
        try:
            manager = pub.sequencemanager
        except RuntimeError:
            raise RuntimeError(
                f'For sequence {objecttools.devicephrase(obj)} attribute '
                f'{self.name} cannot be determined.  Either set it manually '
                'or prepare `pub.sequencemanager` correctly.')
        return getattr(manager, self.__attr_manager)


class _FileType(_IOProperty):

    DOCSTRING = 'Ending of the external data file.'


class _DirPathProperty(_IOProperty):

    DOCSTRING = 'Absolute path of the directory of the external data file.'


class _AggregationProperty(_IOProperty):

    DOCSTRING = ('Type of aggregation performed when writing the '
                 'time series data to an external data file.')


class _OverwriteProperty(_IOProperty):

    DOCSTRING = ('True/False flag indicating if overwriting an existing '
                 'data file is allowed or not.')


class IOSequence(Sequence):
    """Base class for sequences with input/output functionalities.

    The |IOSequence| subclasses |InputSequence|, |FluxSequence|,
    |StateSequence|, and |NodeSequence| all implement similar
    special properties, which configure the processes of reading
    and writing time series files.  In the following, property
    `filetype_ext` is taken as an example to explain how to
    handle them:

    Normally, each sequence queries its current "external" file type
    from the |SequenceManager| object stored in module |pub|:

    >>> from hydpy import pub
    >>> from hydpy.core.filetools import SequenceManager
    >>> pub.sequencemanager = SequenceManager()

    Depending if the actual sequence derived from |InputSequence|,
    |FluxSequence|,  |StateSequence|, or |NodeSequence|, either
    |SequenceManager.inputfiletype|, |SequenceManager.fluxfiletype|,
    |SequenceManager.statefiletype|, or |SequenceManager.nodefiletype|
    are queried:

    >>> pub.sequencemanager.inputfiletype = 'npy'
    >>> pub.sequencemanager.fluxfiletype = 'asc'
    >>> pub.sequencemanager.nodefiletype = 'nc'
    >>> from hydpy.core import sequencetools as st
    >>> st.InputSequence().filetype_ext
    'npy'
    >>> st.FluxSequence().filetype_ext
    'asc'
    >>> st.NodeSequence().filetype_ext
    'nc'

    Alternatively, you can specify `filetype_ext` for each sequence
    object individually:

    >>> seq = st.InputSequence()
    >>> seq.filetype_ext
    'npy'
    >>> seq.filetype_ext = 'nc'
    >>> seq.filetype_ext
    'nc'
    >>> del seq.filetype_ext
    >>> seq.filetype_ext
    'npy'

    If neither an individual definition nor |SequenceManager| is
    available, the following error is raised:

    >>> del pub.sequencemanager
    >>> seq.filetype_ext
    Traceback (most recent call last):
    ...
    RuntimeError: For sequence `inputsequence` attribute filetype_ext \
cannot be determined.  Either set it manually or prepare \
`pub.sequencemanager` correctly.
    """

    filetype_ext: str
    dirpath_ext: str
    aggregation_ext: str
    descr_device: str

    @propertytools.DefaultProperty
    def rawfilename(self):
        """|DefaultProperty| handling the filename without ending for
        external and internal date files.

        >>> from hydpy.core.sequencetools import IOSequence
        >>> class Test(IOSequence):
        ...     descr_device = 'node1'
        ...     descr_sequence = 'subgroup_test'
        >>> Test().rawfilename
        'node1_subgroup_test'
        """
        try:
            return f'{self.descr_device}_{self.descr_sequence}'
        except AttributeError:
            raise RuntimeError(
                'For sequence `%s` the raw filename cannot determined.  '
                'Either set it manually or embed the sequence object '
                'into a device object.'
                % self.name)

    @propertytools.DefaultProperty
    def filename_ext(self):
        """Complete filename of the external data file.

        The "external" filename consists of |IOSequence.rawfilename| and
        of |FluxSequence.filetype_ext|.  For simplicity, we define add the
        attribute `rawfilename` to the initialized sequence object in the
        following example:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> seq = IOSequence()
        >>> seq.rawfilename = 'test'
        >>> seq.filetype_ext = 'nc'
        >>> seq.filename_ext
        'test.nc'
        """
        return '.'.join((self.rawfilename, self.filetype_ext))

    @property
    def filename_int(self):
        """Complete filename of the internal data file.

        The "internal" filename consists of |IOSequence.rawfilename|
        and the file ending `.bin`.  For simplicity, we define add
        the attribute `rawfilename` to the initialized sequence object
        in the following example:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> seq = IOSequence()
        >>> seq.rawfilename = 'test'
        >>> seq.filename_int
        'test.bin'
        """
        return self.rawfilename + '.bin'

    @propertytools.DefaultProperty
    def dirpath_int(self):
        """Absolute path of the directory of the internal data file.

        Normally, each sequence queries its current "internal" directory
        path from the |SequenceManager| object stored in module |pub|:

        >>> from hydpy import pub, repr_, TestIO
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        We overwrite |FileManager.basepath| and prepare a folder in teh
        `iotesting` directory to simplify the following examples:

        >>> basepath = SequenceManager.basepath
        >>> SequenceManager.basepath = 'test'
        >>> TestIO.clear()
        >>> import os
        >>> with TestIO():
        ...     os.makedirs('test/temp')

        Generally, |SequenceManager.tempdirpath| is queried:

        >>> from hydpy.core import sequencetools as st
        >>> seq = st.InputSequence()
        >>> with TestIO():
        ...     repr_(seq.dirpath_int)
        'test/temp'

        Alternatively, you can specify |IOSequence.dirpath_int| for each
        sequence object individually:

        >>> seq.dirpath_int = 'path'
        >>> os.path.split(seq.dirpath_int)
        ('', 'path')
        >>> del seq.dirpath_int
        >>> with TestIO():
        ...     os.path.split(seq.dirpath_int)
        ('test', 'temp')

        If neither an individual definition nor |SequenceManager| is
        available, the following error is raised:

        >>> del pub.sequencemanager
        >>> seq.dirpath_int
        Traceback (most recent call last):
        ...
        RuntimeError: For sequence `inputsequence` the directory of \
the internal data file cannot be determined.  Either set it manually \
or prepare `pub.sequencemanager` correctly.

        Remove the `basepath` mock:

        >>> SequenceManager.basepath = basepath
        """
        try:
            return pub.sequencemanager.tempdirpath
        except RuntimeError:
            raise RuntimeError(
                f'For sequence {objecttools.devicephrase(self)} '
                f'the directory of the internal data file cannot '
                f'be determined.  Either set it manually or prepare '
                f'`pub.sequencemanager` correctly.')

    @propertytools.DefaultProperty
    def filepath_ext(self):
        """Absolute path to the external data file.

        The path pointing to the "external" file consists of
        |FluxSequence.dirpath_ext| and |IOSequence.filename_ext|.  For
        simplicity, we define both manually in the following example:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> seq = IOSequence()
        >>> seq.dirpath_ext = 'path'
        >>> seq.filename_ext = 'file.npy'
        >>> from hydpy import repr_
        >>> repr_(seq.filepath_ext)
        'path/file.npy'
        """
        return os.path.join(self.dirpath_ext, self.filename_ext)

    @propertytools.DefaultProperty
    def filepath_int(self):
        """Absolute path to the internal data file.

        The path pointing to the "internal" file consists of
        |IOSequence.dirpath_int| and |IOSequence.filename_int|, which
        itself is defined by `rawfilename`.  For simplicity, we define
        both manually in the following example:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> seq = IOSequence()
        >>> seq.dirpath_int = 'path'
        >>> seq.rawfilename = 'file'
        >>> from hydpy import repr_
        >>> repr_(seq.filepath_int)
        'path/file.bin'
        """
        return os.path.join(self.dirpath_int, self.filename_int)

    def update_fastaccess(self):
        if self.diskflag:
            path = self.filepath_int
        else:
            path = None
        setattr(self.fastaccess, '_%s_path' % self.name, path)
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
            setattr(self.fastaccess, '_%s_length_%d' % (self.name, idx),
                    self.shape[idx])
        setattr(self.fastaccess, '_%s_length' % self.name, length)

    @property
    def diskflag(self):
        diskflag = getattr(
            self.fastaccess, '_%s_diskflag' % self.name, None)
        if diskflag is not None:
            return diskflag
        else:
            raise RuntimeError(
                'The `diskflag` of sequence `%s` has not been set yet.'
                % objecttools.devicephrase(self))

    @diskflag.setter
    def diskflag(self, value):
        setattr(self.fastaccess, '_%s_diskflag' % self.name, bool(value))

    @property
    def ramflag(self):
        ramflag = getattr(self.fastaccess, '_%s_ramflag' % self.name, None)
        if ramflag is not None:
            return ramflag
        else:
            raise RuntimeError(
                'The `ramflag` of sequence `%s` has not been set yet.'
                % objecttools.devicephrase(self))

    @ramflag.setter
    def ramflag(self, value):
        setattr(self.fastaccess, '_%s_ramflag' % self.name, bool(value))

    def activate_disk(self):
        """Demand reading/writing internal data from/to hard disk."""
        self.deactivate_ram()
        self.diskflag = True
        self._activate()

    def activate_ram(self):
        """Demand reading/writing internal data from/to hard disk."""
        self.deactivate_disk()
        self.ramflag = True
        self._activate()

    def _activate(self):
        self.zero_int()
        self.update_fastaccess()

    def deactivate_disk(self):
        """Prevent from reading/writing internal data from/to hard disk."""
        if self.diskflag:
            del self.series
            self.diskflag = False

    def deactivate_ram(self):
        """Prevent from reading/writing internal data from/to hard disk."""
        if self.ramflag:
            del self.series
            self.ramflag = False

    def disk2ram(self):
        """Move internal data from disk to RAM."""
        values = self.series
        self.deactivate_disk()
        self.ramflag = True
        self.__set_array(values)
        self.update_fastaccess()

    def ram2disk(self):
        """Move internal data from RAM to disk."""
        values = self.series
        self.deactivate_ram()
        self.diskflag = True
        self._save_int(values)
        self.update_fastaccess()

    @property
    def memoryflag(self):
        return self.ramflag or self.diskflag

    def __get_array(self):
        array = getattr(self.fastaccess, '_%s_array' % self.name, None)
        if array is not None:
            return numpy.asarray(array)
        else:
            raise RuntimeError(
                'The `ram array` of sequence `%s` has not been set yet.'
                % objecttools.devicephrase(self))

    def __set_array(self, values):
        values = numpy.array(values, dtype=float)
        setattr(self.fastaccess, '_%s_array' % self.name, values)

    @Sequence.shape.setter
    def shape(self, shape):
        Sequence.shape.fset(self, shape)
        self.update_fastaccess()

    @property
    def seriesshape(self):
        """Shape of the whole time series (time being the first dimension)."""
        seriesshape = [len(pub.timegrids.init)]
        seriesshape.extend(self.shape)
        return tuple(seriesshape)

    @property
    def numericshape(self):
        """Shape of the array of temporary values required for the numerical
        solver actually being selected."""
        try:
            numericshape = [self.subseqs.seqs.model.numconsts.nmb_stages]
        except AttributeError:
            objecttools.augment_excmessage(
                'The `numericshape` of a sequence like `%s` depends on the '
                'configuration of the actual integration algorithm.  '
                'While trying to query the required configuration data '
                '`nmb_stages` of the model associated with element `%s`'
                % (self.name, objecttools.devicename(self)))
        numericshape.extend(self.shape)
        return tuple(numericshape)

    @property
    def series(self) -> InfoArray:
        """Internal time series data within an |numpy.ndarray|."""
        if self.diskflag:
            array = self._load_int()
        elif self.ramflag:
            array = self.__get_array()
        else:
            raise RuntimeError(
                'Sequence %s is not requested to make any '
                'internal data available to the user.'
                % objecttools.devicephrase(self))
        return InfoArray(array, info={'type': 'unmodified'})

    @series.setter
    def series(self, values):
        series = numpy.full(self.seriesshape, values, dtype=float)
        if self.diskflag:
            self._save_int(series)
        elif self.ramflag:
            self.__set_array(series)
        else:
            raise RuntimeError(
                'Sequence `%s` is not requested to make any '
                'internal data available to the user.'
                % objecttools.devicephrase(self))

    @series.deleter
    def series(self):
        if self.diskflag:
            os.remove(self.filepath_int)
        elif self.ramflag:
            setattr(self.fastaccess, '_%s_array' % self.name, None)

    def load_ext(self):
        """Read the internal data from an external data file."""
        try:
            sequencemanager = pub.sequencemanager
        except AttributeError:
            raise RuntimeError(
                'The time series of sequence %s cannot be loaded.  Firstly, '
                'you have to prepare `pub.sequencemanager` correctly.'
                % objecttools.devicephrase(self))
        sequencemanager.load_file(self)

    def adjust_series(self, timegrid_data, values):   # ToDo: Docstring
        if self.shape != values.shape[1:]:
            raise RuntimeError(
                'The shape of sequence %s is `%s`, but according to '
                'the external data file `%s` it should be `%s`.'
                % (objecttools.devicephrase(self), self.shape,
                   self.filepath_ext, values.shape[1:]))
        if pub.timegrids.init.stepsize != timegrid_data.stepsize:
            raise RuntimeError(
                'According to external data file `%s`, the date time '
                'step of sequence %s is `%s`, but the actual simulation '
                'time step is `%s`.'
                % (self.filepath_ext, objecttools.devicephrase(self),
                   timegrid_data.stepsize, pub.timegrids.init.stepsize))
        elif pub.timegrids.init not in timegrid_data:
            if pub.options.checkseries:
                raise RuntimeError(
                    'For sequence `%s the initialization time grid (%s) '
                    'does not define a subset of the time grid of the '
                    'external data file %s (%s).'
                    % (objecttools.devicephrase(self), pub.timegrids.init,
                       self.filepath_ext, timegrid_data))
            else:
                return self.adjust_short_series(timegrid_data, values)
        idx1 = timegrid_data[pub.timegrids.init.firstdate]
        idx2 = timegrid_data[pub.timegrids.init.lastdate]
        return values[idx1:idx2]

    def adjust_short_series(self, timegrid, values):
        """Adjust a short time series to a longer timegrid.

        Normally, time series data to be read from a external data files
        should span (at least) the whole initialization time period of a
        HydPy project.  However, for some variables which are only used
        for comparison (e.g. observed runoff used for calibration),
        incomplete time series might also be helpful.  This method it
        thought for adjusting such incomplete series to the public
        initialization time grid stored in module |pub|.  It is
        automatically called in method |IOSequence.adjust_series| when
        necessary provided that the option |Options.checkseries| is
        disabled.

        Assume the initialization time period of a HydPy project spans
        five day:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.10', '2000.01.15', '1d'

        Prepare a node series object for observational data:

        >>> from hydpy.core.sequencetools import Obs
        >>> obs = Obs()

        Prepare a test function that expects the timegrid of the
        data and the data itself, which returns the ajdusted array by
        means of calling method |IOSequence.adjust_short_series|:

        >>> import numpy
        >>> def test(timegrid):
        ...     values = numpy.ones(len(timegrid))
        ...     return obs.adjust_short_series(timegrid, values)

        The following calls to the test function shows the arrays
        returned for different kinds misalignments:

        >>> from hydpy import Timegrid
        >>> test(Timegrid('2000.01.05', '2000.01.20', '1d'))
        array([ 1.,  1.,  1.,  1.,  1.])
        >>> test(Timegrid('2000.01.12', '2000.01.15', '1d'))
        array([ nan,  nan,   1.,   1.,   1.])
        >>> test(Timegrid('2000.01.12', '2000.01.17', '1d'))
        array([ nan,  nan,   1.,   1.,   1.])
        >>> test(Timegrid('2000.01.10', '2000.01.13', '1d'))
        array([  1.,   1.,   1.,  nan,  nan])
        >>> test(Timegrid('2000.01.08', '2000.01.13', '1d'))
        array([  1.,   1.,   1.,  nan,  nan])
        >>> test(Timegrid('2000.01.12', '2000.01.13', '1d'))
        array([ nan,  nan,   1.,  nan,  nan])
        >>> test(Timegrid('2000.01.05', '2000.01.10', '1d'))
        array([ nan,  nan,  nan,  nan,  nan])
        >>> test(Timegrid('2000.01.05', '2000.01.08', '1d'))
        array([ nan,  nan,  nan,  nan,  nan])
        >>> test(Timegrid('2000.01.15', '2000.01.18', '1d'))
        array([ nan,  nan,  nan,  nan,  nan])
        >>> test(Timegrid('2000.01.16', '2000.01.18', '1d'))
        array([ nan,  nan,  nan,  nan,  nan])

        Through enabling option |Options.usedefaultvalues| the missing
        values are initialized with zero instead of nan:

        >>> pub.options.usedefaultvalues = True

        >>> test(Timegrid('2000.01.12', '2000.01.17', '1d'))
        array([ 0.,  0.,  1.,  1.,  1.])

        >>> pub.options.usedefaultvalues = False
        """
        idxs = [timegrid[pub.timegrids.init.firstdate],
                timegrid[pub.timegrids.init.lastdate]]
        valcopy = values
        values = numpy.full(self.seriesshape, self.initvalue)
        len_ = len(valcopy)
        jdxs = []
        for idx in idxs:
            if idx < 0:
                jdxs.append(0)
            elif idx <= len_:
                jdxs.append(idx)
            else:
                jdxs.append(len_)
        valcopy = valcopy[jdxs[0]:jdxs[1]]
        zdx1 = max(-idxs[0], 0)
        zdx2 = zdx1+jdxs[1]-jdxs[0]
        values[zdx1:zdx2] = valcopy
        return values

    def save_ext(self):
        """Write the internal data into an external data file."""
        try:
            sequencemanager = pub.sequencemanager
        except AttributeError:
            raise RuntimeError(
                'The time series of sequence %s cannot be saved.  Firstly,'
                'you have to prepare `pub.sequencemanager` correctly.'
                % objecttools.devicephrase(self))
        sequencemanager.save_file(self)

    def save_mean(self, *args, **kwargs):   # ToDo: Docstring
        array = InfoArray(
            self.average_series(*args, **kwargs),
            info={'type': 'mean',
                  'args': args,
                  'kwargs': kwargs})
        pub.sequencemanager.save_file(self, array=array)

    def _load_int(self):
        """Load internal data from file and return it."""
        values = numpy.fromfile(self.filepath_int)
        if self.NDIM > 0:
            values = values.reshape(self.seriesshape)
        return values

    def zero_int(self):
        """Initialize the internal data series with zero values."""
        values = numpy.zeros(self.seriesshape)
        if self.diskflag:
            self._save_int(values)
        elif self.ramflag:
            self.__set_array(values)
        else:
            raise RuntimeError(
                'Sequence %s is not requested to make any '
                'internal data available to the user.'
                % objecttools.devicephrase(self.name))

    def _save_int(self, values):
        values.tofile(self.filepath_int)

    def average_series(self, *args, **kwargs) -> InfoArray:
        """Average the actual time series of the |Variable| object for all
        time points.

        Method |IOSequence.average_series| works similarly as method
        |Variable.average_values| of class |Variable|, from which we
        borrow some examples. However, firstly, we have to prepare a
        |Timegrids| object to define the |IOSequence.series| length:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2000-01-04', '1d'

        As shown for method |Variable.average_values|, for 0-dimensional
        |IOSequence| objects the result of |IOSequence.average_series|
        equals |IOSequence.series| itself:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> class SoilMoisture(IOSequence):
        ...     NDIM = 0
        >>> sm = SoilMoisture()
        >>> sm.activate_ram()
        >>> import numpy
        >>> sm.series = numpy.array([190.0, 200.0, 210.0])
        >>> sm.average_series()
        InfoArray([ 190.,  200.,  210.])

        For |IOSequence| objects with an increased dimensionality, a
        weighting parameter is required, again:

        >>> SoilMoisture.NDIM = 1
        >>> sm.shape = 3
        >>> sm.activate_ram()
        >>> sm.series = (
        ...     [190.0, 390.0, 490.0],
        ...     [200.0, 400.0, 500.0],
        ...     [210.0, 410.0, 510.0])
        >>> from hydpy.core.variabletools import Variable
        >>> class Area(Variable):
        ...     NDIM = 1
        ...     shape = (3,)
        ...     value = numpy.array([1.0, 1.0, 2.0])
        >>> area = Area()
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> sm.average_series()
        InfoArray([ 390.,  400.,  410.])

        The documentation on method |Variable.average_values| provides
        many examples on how to use different masks in different ways.
        Here we restrict ourselves to the first example, where a new
        mask enforces that |IOSequence.average_series| takes only the
        first two columns of the `series` into account:

        >>> from hydpy.core.masktools import DefaultMask
        >>> class Soil(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask([True, True, False])
        >>> SoilMoisture.mask = Soil()
        >>> sm.average_series()
        InfoArray([ 290.,  300.,  310.])
        """
        try:
            if not self.NDIM:
                array = self.series
            else:
                mask = self.get_submask(*args, **kwargs)
                if numpy.any(mask):
                    weights = self.refweights[mask]
                    weights /= numpy.sum(weights)
                    series = self.series[:, mask]
                    axes = tuple(range(1, self.NDIM+1))
                    array = numpy.sum(weights*series, axis=axes)
                else:
                    return numpy.nan
            return InfoArray(array, info={'type': 'mean'})
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to calculate the mean value of '
                'the internal time series of sequence %s'
                % objecttools.devicephrase(self))

    def aggregate_series(self, *args, **kwargs) -> InfoArray:
        """Aggregates time series data based on the actual
        |FluxSequence.aggregation_ext| attribute of |IOSequence|
        subclasses.

        We prepare some nodes and elements with the help of
        method |prepare_io_example_1| and select a 1-dimensional
        flux sequence of type |lland_fluxes.NKor| as an example:

        >>> from hydpy.core.examples import prepare_io_example_1
        >>> nodes, elements = prepare_io_example_1()
        >>> seq = elements.element3.model.sequences.fluxes.nkor

        If no |FluxSequence.aggregation_ext| is `none`, the
        original time series values are returned:

        >>> seq.aggregation_ext
        'none'
        >>> seq.aggregate_series()
        InfoArray([[ 24.,  25.,  26.],
                   [ 27.,  28.,  29.],
                   [ 30.,  31.,  32.],
                   [ 33.,  34.,  35.]])

        If no |FluxSequence.aggregation_ext| is `mean`, function
        |IOSequence.aggregate_series| is called:

        >>> seq.aggregation_ext = 'mean'
        >>> seq.aggregate_series()
        InfoArray([ 25.,  28.,  31.,  34.])

        In case the state of the sequence is invalid:

        >>> seq.aggregation_ext = 'nonexistent'
        >>> seq.aggregate_series()
        Traceback (most recent call last):
        ...
        RuntimeError: Unknown aggregation mode `nonexistent` for \
sequence `nkor` of element `element3`.

        The following technical test confirms that all potential
        positional and keyword arguments are passed properly:
        >>> seq.aggregation_ext = 'mean'

        >>> from unittest import mock
        >>> seq.average_series = mock.MagicMock()
        >>> _ = seq.aggregate_series(1, x=2)
        >>> seq.average_series.assert_called_with(1, x=2)
        """
        mode = self.aggregation_ext
        if mode == 'none':
            return self.series
        elif mode == 'mean':
            return self.average_series(*args, **kwargs)
        else:
            raise RuntimeError(
                'Unknown aggregation mode `%s` for sequence %s.'
                % (mode, objecttools.devicephrase(self)))

    @property
    def descr_sequence(self):
        """Description of the |IOSequence| object itself and the
        |SubSequences| group it belongs to."""
        raise NotImplementedError()


abctools.IOSequenceABC.register(IOSequence)


class ModelSequence(IOSequence):
    """Base class for sequences to be handled by |Model| objects."""

    @property
    def descr_sequence(self):
        """Description of the |ModelSequence| object itself and the
        |SubSequences| group it belongs to.

        >>> from hydpy import prepare_model
        >>> from hydpy.models import test_v1
        >>> model = prepare_model(test_v1)
        >>> model.sequences.fluxes.q.descr_sequence
        'flux_q'
        """
        return ('%s_%s'
                % (objecttools.classname(self.subseqs)[:-9].lower(),
                   self.name))

    @property
    def descr_model(self):
        """Description of the |Model| the |ModelSequence| object belongs to.

        >>> from hydpy import prepare_model
        >>> from hydpy.models import test, test_v1
        >>> model = prepare_model(test)
        >>> model.sequences.fluxes.q.descr_model
        'test'
        >>> model = prepare_model(test_v1)
        >>> model.sequences.fluxes.q.descr_model
        'test_v1'
        """
        return self.subseqs.seqs.model.__module__.split('.')[2]

    @property
    def descr_device(self):
        """Description of the |Element| object the |ModelSequence| object
        belongs to.

        >>> from hydpy import prepare_model, Element
        >>> element = Element('test_element_1')
        >>> from hydpy.models import test_v1
        >>> model = prepare_model(test_v1)
        >>> element.connect(model)
        >>> model.sequences.fluxes.q.descr_device
        'test_element_1'
        """
        return self.subseqs.seqs.model.element.name


abctools.ModelSequenceABC.register(IOSequence)


class InputSequence(ModelSequence):
    """Base class for input sequences of |Model| objects."""

    filetype_ext = _FileType()

    dirpath_ext = _DirPathProperty()

    aggregation_ext = _AggregationProperty()

    overwrite_ext = _OverwriteProperty()


abctools.InputSequenceABC.register(InputSequence)


class FluxSequence(ModelSequence):
    """Base class for flux sequences of |Model| objects."""

    filetype_ext = _FileType()

    dirpath_ext = _DirPathProperty()

    aggregation_ext = _AggregationProperty()

    overwrite_ext = _OverwriteProperty()

    def _initvalues(self):
        ModelSequence._initvalues(self)
        if self.NUMERIC:
            value = None if self.NDIM else numpy.zeros(self.numericshape)
            self._connect_subattr('points', value)
            self._connect_subattr('integrals', copy.copy(value))
            self._connect_subattr('results', copy.copy(value))
            value = None if self.NDIM else 0.
            self._connect_subattr('sum', value)

    @ModelSequence.shape.setter
    def shape(self, shape):
        ModelSequence.shape.fset(self, shape)
        if self.NDIM and self.NUMERIC:
            self._connect_subattr('points', numpy.zeros(self.numericshape))
            self._connect_subattr('integrals', numpy.zeros(self.numericshape))
            self._connect_subattr('results', numpy.zeros(self.numericshape))
            self._connect_subattr('sum', numpy.zeros(self.shape))


abctools.FluxSequenceABC.register(FluxSequence)


class LeftRightSequence(ModelSequence):
    NDIM = 1

    def _initvalues(self):
        setattr(self.fastaccess, self.name,
                numpy.full(2, self.initvalue, dtype=float))

    def _get_left(self):
        """The "left" value of the actual parameter."""
        return self.values[0]

    def _set_left(self, value):
        self.values[0] = value

    left = property(_get_left, _set_left)

    def _get_right(self):
        """The "right" value of the actual parameter."""
        return self.values[1]

    def _set_right(self, value):
        self.values[1] = value

    right = property(_get_right, _set_right)


class ConditionSequence(object):

    def __call__(self, *args):
        self.values = args
        self.trim()
        self._oldargs = copy.deepcopy(args)

    def trim(self, lower=None, upper=None):
        """Apply |trim| of module |variabletools|."""
        variabletools.trim(self, lower, upper)

    def warn_trim(self):
        warnings.warn(
            'For sequence %s at least one value needed to be trimmed.  '
            'One possible reason could be that the related control '
            'parameter and initial condition files are inconsistent.'
            % objecttools.elementphrase(self))

    def reset(self):
        if self._oldargs:
            self(*self._oldargs)


class StateSequence(ModelSequence, ConditionSequence):
    """Base class for state sequences of |Model| objects."""

    NOT_DEEPCOPYABLE_MEMBERS = ('subseqs', 'fastaccess_old', 'fastaccess_new')

    filetype_ext = _FileType()

    dirpath_ext = _DirPathProperty()

    aggregation_ext = _AggregationProperty()

    overwrite_ext = _OverwriteProperty()

    def __init__(self):
        ModelSequence.__init__(self)
        self.fastaccess_old = None
        self.fastaccess_new = None
        self._oldargs = None

    def __call__(self, *args):
        """The prefered way to pass values to |Sequence| instances within
        initial condition files.
        """
        ConditionSequence.__call__(self, *args)
        self.new2old()

    def connect(self, subseqs):
        ModelSequence.connect(self, subseqs)
        self.fastaccess_old = subseqs.fastaccess_old
        self.fastaccess_new = subseqs.fastaccess_new
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, None)
        else:
            setattr(self.fastaccess_old, self.name, 0.)

    def _initvalues(self):
        ModelSequence._initvalues(self)
        if self.NUMERIC:
            value = None if self.NDIM else numpy.zeros(self.numericshape)
            self._connect_subattr('points', value)
            self._connect_subattr('results', copy.copy(value))

    @ModelSequence.shape.setter
    def shape(self, shape):
        ModelSequence.shape.fset(self, shape)
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, self.new.copy())
            if self.NUMERIC:
                self._connect_subattr('points',
                                      numpy.zeros(self.numericshape))
                self._connect_subattr('results',
                                      numpy.zeros(self.numericshape))

    new = Sequence.values
    """Complete access to the state value(s), which will be used in the
    next calculation steps.  Note that |StateSequence.new| is a synonym
    of |Variable.value|.  Use this property to modify the initial
    condition(s) of a single |StateSequence| object.
    """

    def _get_old(self):
        """Assess to the state value(s) at beginning of the time step, which
        has been processed most recently.  When using :ref:`HydPy` in the
        normal manner.  But it can be helpful for demonstration and debugging
        purposes.
        """
        value = getattr(self.fastaccess_old, self.name, None)
        if value is None:
            raise RuntimeError(
                'No value/values of sequence %s has/have '
                'not been defined so far.'
                % objecttools.elementphrase(self))
        else:
            if self.NDIM:
                value = numpy.asarray(value)
            return value

    def _set_old(self, value):
        if self.NDIM == 0:
            try:
                temp = value[0]
                if len(value) > 1:
                    raise ValueError(
                        f'{len(value)} values are assigned to the scalar '
                        f'sequence `{self.name}`, which is ambiguous.')
                value = temp
            except (TypeError, IndexError):
                pass
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise TypeError(
                    'When trying to set the value of sequence %s, '
                    'it was not possible to convert `%s` to float.'
                    % (objecttools.devicephrase(self), value))
        else:
            try:
                value = value.value
            except AttributeError:
                pass
            try:
                value = numpy.full(self.shape, value, dtype=float)
            except ValueError:
                raise ValueError(
                    'The values `%s` cannot be converted to a numpy '
                    'ndarray with shape %s containing entries of type float.'
                    % (value, self.shape))
        setattr(self.fastaccess_old, self.name, value)

    old = property(_get_old, _set_old)

    def new2old(self):
        if self.NDIM:
            self.old[:] = self.new[:]
        else:
            self.old = self.new


abctools.StateSequenceABC.register(StateSequence)


class LogSequence(Sequence, ConditionSequence):
    """Base class for logging sequences of |Model| objects."""

    def __init__(self):
        Sequence.__init__(self)
        self._oldargs = None

    def __call__(self, *args):
        self.values = args
        self.trim()
        self._oldargs = copy.deepcopy(args)


abctools.LogSequenceABC.register(LogSequence)


class AideSequence(Sequence):
    """Base class for aide sequences of |Model| objects.

    Aide sequences are thought for storing data that is of importance
    only temporarily but needs to be shared between different
    calculation methods of a |Model| object.
    """
    pass


abctools.AideSequenceABC.register(AideSequence)


class LinkSequence(Sequence):
    """Base class for link sequences of |Model| objects.

    Link sequences point (based on module |pointerutils| to data
    values of |NodeSequence| objects.  This allows |Model| objects,
    which are handled by |Element| objects, to query and to modify
    data, which lies in the area of responsibility of |Node| objects.
    """

    def set_pointer(self, double, idx=0):
        pdouble = pointerutils.PDouble(double)
        if self.NDIM == 0:
            try:
                self.fastaccess.set_pointer0d(self.name, pdouble)
            except AttributeError:
                setattr(self.fastaccess, self.name, pdouble)
        elif self.NDIM == 1:
            try:
                self.fastaccess.set_pointer1d(self.name, pdouble, idx)
            except AttributeError:
                ppdouble = getattr(self.fastaccess, self.name)
                ppdouble.set_pointer(double, idx)

    def _initvalues(self):
        value = pointerutils.PPDouble() if self.NDIM else None
        try:
            setattr(self.fastaccess, self.name, value)
        except AttributeError:
            pass

    @property
    def value(self):
        raise AttributeError(
            'To retrieve a pointer is very likely to result in bugs '
            'and is thus not supported at the moment.')

    @value.setter
    def value(self, value):
        """Could be implemented, but is not important at the moment..."""
        raise AttributeError(
            'To change a pointer is very likely to result in bugs '
            'and is thus not supported at the moment.')

    @property
    def shape(self):
        if self.NDIM == 0:
            return ()
        elif self.NDIM == 1:
            try:
                return getattr(self.fastaccess, self.name).shape
            except AttributeError:
                return getattr(self.fastaccess, '_%s_length_0' % self.name),
        raise NotImplementedError(
            'Getting the shape of a %d dimensional link sequence '
            'is not supported so far.'
            % self.NDIM)

    @shape.setter
    def shape(self, shape):
        if self.NDIM == 1:
            try:
                getattr(self.fastaccess, self.name).shape = shape
            except AttributeError:
                self.fastaccess.dealloc()
                self.fastaccess.alloc(self.name, shape)
            setattr(self.fastaccess, 'len_'+self.name, self.shape[0])
        elif self.NDIM > 1:
            raise NotImplementedError(
                'Setting the shape of a %d dimensional link sequence '
                'is not supported so far.'
                % self.NDIM)


abctools.LinkSequenceABC.register(LinkSequence)


class NodeSequence(IOSequence):
    """Base class for all sequences to be handled by |Node| objects."""

    filetype_ext = _FileType()

    dirpath_ext = _DirPathProperty()

    aggregation_ext = _AggregationProperty()

    overwrite_ext = _OverwriteProperty()

    @property
    def descr_sequence(self):
        """Description of the |NodeSequence| object including the
        |Node.variable| to be represented.

        >>> from hydpy import Node
        >>> Node('test_node_1', 'T').sequences.sim.descr_sequence
        'sim_t'
        """
        return '%s_%s' % (self.name, self.subseqs.node.variable.lower())

    @property
    def descr_device(self):
        """Description of the |Node| object the |NodeSequence| object
        belongs to.

        >>> from hydpy import Node
        >>> Node('test_node_2').sequences.sim.descr_device
        'test_node_2'
        """
        return self.subseqs.node.name

    def _initvalues(self):
        setattr(self.fastaccess, self.name, pointerutils.Double(0.))

    @property
    def value(self):
        """Actual value(s) handled by the sequence.  For consistency,
        `value` and `values` can always be used interchangeably."""
        try:
            return getattr(self.fastaccess, self.name)
        except AttributeError:
            if self.NDIM == 0:
                return self.fastaccess.getpointer0d(self.name)
            elif self.NDIM == 1:
                return self.fastaccess.getpointer1d(self.name)

    @value.setter
    def value(self, values):
        getattr(self.fastaccess, self.name)[0] = values


abctools.NodeSequenceABC.register(NodeSequence)


class Sim(NodeSequence):
    """Base class for simulation sequences of |Node| objects."""
    NDIM, NUMERIC = 0, False

    def activate_disk(self):
        try:
            NodeSequence.activate_disk(self)
        except IOError:
            message = sys.exc_info()[1]
            self.diskflag = False
            if pub.options.warnmissingsimfile:
                warnings.warn(
                    'The option `diskflag` of the simulation '
                    'sequence `%s` had to be set to `False` due '
                    'to the following problem: %s.'
                    % (objecttools.devicename(self), message))

    def activate_ram(self):
        try:
            NodeSequence.activate_ram(self)
        except IOError:
            message = sys.exc_info()[1]
            self.ramflag = False
            if pub.options.warnmissingsimfile:
                warnings.warn(
                    'The option `ramflag` of the simulation '
                    'sequence `%s` had to be set to `False` due '
                    'to the following problem: %s.'
                    % (objecttools.devicename(self), message))


class Obs(NodeSequence):
    """Base class for observation sequences of |Node| objects."""
    NDIM, NUMERIC = 0, False

    def activate_disk(self):
        try:
            NodeSequence.activate_disk(self)
        except IOError:
            message = sys.exc_info()[1]
            self.diskflag = False
            if pub.options.warnmissingobsfile:
                warnings.warn(
                    'The option `diskflag` of the observation '
                    'sequence `%s` had to be set to `False` due '
                    'to the following problem: %s.'
                    % (objecttools.devicename(self), message))

    def activate_ram(self):
        try:
            NodeSequence.activate_ram(self)
        except IOError:
            message = sys.exc_info()[1]
            self.ramflag = False
            if pub.options.warnmissingobsfile:
                warnings.warn(
                    'The option `ramflag` of the observation '
                    'sequence `%s` had to be set to `False` due '
                    'to the following problem: %s.'
                    % (objecttools.devicename(self), message))

    @property
    def series_complete(self):
        return self.memoryflag and not numpy.any(numpy.isnan(self.series))


class NodeSequences(IOSequences):
    """Base class for handling node sequences."""
    CLASSES = (Sim,
               Obs)

    def __init__(self, seqs, cls_fastaccess=None):
        IOSequences.__init__(self, seqs, cls_fastaccess)
        self.node = seqs

    def load_data(self, idx):
        self.fastaccess.load_data(idx)

    def save_data(self, idx):
        self.fastaccess.save_data(idx)


class FastAccess(object):
    """Provides fast access to the values of the sequences of a sequence
    subgroup and supports the handling of internal data series during
    simulations.

    The following details are of relevance for :ref:`HydPy` developers only.

    |sequencetools.FastAccess| is applied in Python mode only.  In Cython
    mode, specialized and more efficient cdef classes replace it.  For
    compatibility with these cdef classes, |sequencetools.FastAccess|
    objects work with dynamically set instance members.  Suppose there
    is a sequence named `seq1` which is 2-dimensional, then its associated
    attributes are:

      * seq1 (|numpy.ndarray|): The actual sequence values.
      * _seq1_ndim (|int|): Number of dimensions.
      * _seq1_length_0 (|int|): Length in the first dimension.
      * _seq1_length_1 (|int|): Length in the second dimension.
      * _seq1_ramflag (|bool|): Handle internal data in RAM?
      * _seq1_diskflag (|bool|): Handle internal data on disk?
      * _seq1_path (|str|): Path of the internal data file.
      * _seq1_file (|io.open|): Object handling the internal data file.

    Note that all these dynamical attributes and the following methods are
    initialised, changed or applied by the respective |SubSequences| and
    |Sequence| objects.  Handling them directly is error prone and thus
    not recommended.
    """

    def open_files(self, idx):
        """Open all files with an activated disk flag."""
        for name in self:
            if getattr(self, '_%s_diskflag' % name):
                path = getattr(self, '_%s_path' % name)
                file_ = open(path, 'rb+')
                ndim = getattr(self, '_%s_ndim' % name)
                position = 8*idx
                for idim in range(ndim):
                    length = getattr(self, '_%s_length_%d' % (name, idim))
                    position *= length
                file_.seek(position)
                setattr(self, '_%s_file' % name, file_)

    def close_files(self):
        """Close all files with an activated disk flag."""
        for name in self:
            if getattr(self, '_%s_diskflag' % name):
                file_ = getattr(self, '_%s_file' % name)
                file_.close()

    def load_data(self, idx):
        """Load the internal data of all sequences.  Load from file if the
        corresponding disk flag is activated, otherwise load from RAM."""
        for name in self:
            ndim = getattr(self, '_%s_ndim' % name)
            diskflag = getattr(self, '_%s_diskflag' % name)
            ramflag = getattr(self, '_%s_ramflag' % name)
            if diskflag:
                file_ = getattr(self, '_%s_file' % name)
                length_tot = 1
                shape = []
                for jdx in range(ndim):
                    length = getattr(self, '_%s_length_%s' % (name, jdx))
                    length_tot *= length
                    shape.append(length)
                raw = file_.read(length_tot*8)
                values = struct.unpack(length_tot*'d', raw)
                if ndim:
                    values = numpy.array(values).reshape(shape)
                else:
                    values = values[0]
            elif ramflag:
                array = getattr(self, '_%s_array' % name)
                values = array[idx]
            if diskflag or ramflag:
                if ndim == 0:
                    setattr(self, name, values)
                else:
                    getattr(self, name)[:] = values

    def save_data(self, idx):
        """Save the internal data of all sequences with an activated flag.
        Write to file if the corresponding disk flag is activated; store
        in working memory if the corresponding ram flag is activated."""
        for name in self:
            actual = getattr(self, name)
            diskflag = getattr(self, '_%s_diskflag' % name)
            ramflag = getattr(self, '_%s_ramflag' % name)
            if diskflag:
                file_ = getattr(self, '_%s_file' % name)
                ndim = getattr(self, '_%s_ndim' % name)
                length_tot = 1
                for jdx in range(ndim):
                    length = getattr(self, '_%s_length_%s' % (name, jdx))
                    length_tot *= length
                if ndim:
                    raw = struct.pack(length_tot*'d', *actual.flatten())
                else:
                    raw = struct.pack('d', actual)
                file_.write(raw)
            elif ramflag:
                array = getattr(self, '_%s_array' % name)
                array[idx] = actual

    def __iter__(self):
        """Iterate over all sequence names."""
        for key in vars(self).keys():
            if not key.startswith('_'):
                yield key


__test__ = dict()
autodoctools.autodoc_module(__test__)
