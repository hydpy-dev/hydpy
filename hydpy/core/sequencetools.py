# -*- coding: utf-8 -*-
"""This module implements tools for handling the sequences (time series)
of hydrological models.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import os
import sys
import copy
import struct
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import variabletools
from hydpy.cythons.autogen import pointerutils


class Sequences(object):
    """Handles all sequences of a specific model."""

    _names_subseqs = ('inlets', 'receivers', 'inputs', 'fluxes', 'states',
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
        for name in self._names_subseqs:
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
        for dummy in self.conditions:
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


class _MetaSubSequencesType(type):
    def __new__(mcs, name, parents, dict_):
        seqclasses = dict_.get('_SEQCLASSES')
        if seqclasses is None:
            raise NotImplementedError(
                'For class `%s`, the required tuple `_SEQCLASSES` is not '
                'defined.  Please see the documentation of class '
                '`SubSequences` of module `sequencetools` for further '
                'information.' % name)
        if seqclasses:
            lst = ['\n\n\n    The following sequence classes are selected:']
            for seqclass in seqclasses:
                lst.append('      * :class:`~%s` %s'
                           % ('.'.join((seqclass.__module__,
                                        seqclass.__name__)),
                              autodoctools.description(seqclass)))
            doc = dict_.get('__doc__', None)
            if doc is None:
                doc = ''
            dict_['__doc__'] = doc + '\n'.join(l for l in lst)
        return type.__new__(mcs, name, parents, dict_)


_MetaSubSequencesClass = _MetaSubSequencesType('_MetaSubSequencesClass',
                                               (), {'_SEQCLASSES': ()})


class SubSequences(_MetaSubSequencesClass):
    """Base class for handling subgroups of sequences.

    Attributes:
      * seqs: The parent |Sequences| object.
      * fastaccess: The  |sequencetools.FastAccess| object allowing fast
        access to the sequence values. In `Cython` mode, model specific
        cdef classes are applied.

    Additional attributes are the actual |Sequence| instances, representing
    the individual time series.  These need to be defined in
    |SubSequences| subclasses.  Therefore, one needs to collect the
    appropriate |Sequence| subclasses in the (hidden) class attribute
    `_SEQCLASSES`, as shown in the following example:

    >>> from hydpy.core.sequencetools import *
    >>> class Temperature(Sequence):
    ...    NDIM, NUMERIC = 0, False
    >>> class Precipitation(Sequence):
    ...    NDIM, NUMERIC = 0, True
    >>> class InputSequences(SubSequences):
    ...     _SEQCLASSES = (Temperature, Precipitation)
    >>> inputs = InputSequences(None) # Assign `None` for brevity.
    >>> inputs
    temperature(nan)
    precipitation(nan)

    The order within the tuple determines the order of iteration, hence:

    >>> for sequence in inputs:
    ...     print(sequence)
    temperature(nan)
    precipitation(nan)

    If one forgets to define a `_SEQCLASSES` tuple so (and maybe tries to
    add the sequences in the constructor of the subclass of |SubSequences|,
    the following error is raised:

    >>> class InputSequences(SubSequences):
    ...     pass
    Traceback (most recent call last):
    ...
    NotImplementedError: For class `InputSequences`, the required tuple \
`_SEQCLASSES` is not defined.  Please see the documentation of class \
`SubSequences` of module `sequencetools` for further information.

    """
    _SEQCLASSES = ()

    def __init__(self, seqs, cls_fastaccess=None, cymodel=None):
        self.seqs = seqs
        self._initfastaccess(cls_fastaccess, cymodel)
        self._initsequences()

    def _initfastaccess(self, cls_fastaccess, cymodel):
        if cls_fastaccess is None:
            self.fastaccess = FastAccess()
        else:
            self.fastaccess = cls_fastaccess()
            setattr(cymodel.sequences, self.name, self.fastaccess)

    def _initsequences(self):
        for cls_seq in self._SEQCLASSES:
            setattr(self, objecttools.instancename(cls_seq), cls_seq())

    @classmethod
    def getname(cls):
        return objecttools.instancename(cls)[:-8]

    @property
    def name(self):
        return self.getname()

    def __setattr__(self, name, value):
        """Attributes and methods should usually not be replaced.  Existing
        |Sequence| attributes are protected in a way, that only their
        values are changed through assignements.  For new |Sequence|
        attributes, additional `fastaccess` references are defined.  If you
        actually want to replace a sequence, you have to delete it first.
        """
        try:
            attr = getattr(self, name)
        except AttributeError:
            object.__setattr__(self, name, value)
            if isinstance(value, Sequence):
                value.connect(self)
        else:
            try:
                attr.values = value
            except AttributeError:
                raise RuntimeError(
                    '`%s` instances do not allow the direct replacement of '
                    'their members.  After initialization you should usually '
                    'only change parameter values through assignements.  '
                    'If you really need to replace a object member, delete '
                    'it beforehand.'
                    % objecttools.classname(self))

    def __iter__(self):
        for seqclass in self._SEQCLASSES:
            name = objecttools.instancename(seqclass)
            yield getattr(self, name)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        lines = []
        if pub.options.reprcomments:
            lines.append('#%s object defined in module %s.'
                         % (objecttools.classname(self),
                            objecttools.modulename(self)))
            lines.append('#The implemented sequences with their actual '
                         'values are:')
        for sequence in self:
            try:
                lines.append('%s' % repr(sequence))
            except BaseException:
                lines.append('%s(?)' % sequence.name)
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class IOSequences(SubSequences):
    _SEQCLASSES = ()

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
    _SEQCLASSES = ()

    def load_data(self, idx):
        self.fastaccess.load_data(idx)


abctools.InputSequencesABC.register(InputSequences)


class FluxSequences(IOSequences):
    """Base class for handling flux sequences."""
    _SEQCLASSES = ()

    @classmethod
    def getname(cls):
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
    _SEQCLASSES = ()

    def _initfastaccess(self, cls_fastaccess, cymodel):
        IOSequences._initfastaccess(self, cls_fastaccess, cymodel)
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
    _SEQCLASSES = ()

    def reset(self):
        for seq in self:
            seq.reset()


class AideSequences(SubSequences):
    """Base class for handling aide sequences."""
    _SEQCLASSES = ()


class LinkSequences(SubSequences):
    """Base class for handling link sequences."""
    _SEQCLASSES = ()


class Sequence(variabletools.Variable):
    """Base class for defining different kinds of sequences."""

    NDIM, NUMERIC = 0, False

    NOT_DEEPCOPYABLE_MEMBERS = ('subseqs', 'fastaccess')

    def __init__(self):
        self.subseqs = None
        self.fastaccess = objecttools.FastAccess()

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

    def _getvalue(self):
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

    def _setvalue(self, value):
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

    value = property(_getvalue, _setvalue)
    values = property(_getvalue, _setvalue)

    def _getshape(self):
        """A tuple containing the lengths in all dimensions of the sequence
        values at a specific time point.  Note that setting a new shape
        results in a loss of the actual values of the respective sequence.
        For 0-dimensional sequences an empty tuple is returned.
        """
        if self.NDIM:
            try:
                shape = self.values.shape
                return tuple(int(x) for x in shape)
            except AttributeError:
                raise RuntimeError(
                    'Shape information for %s can only be retrieved '
                    'after it has been defined.'
                    % objecttools.devicephrase(self))
        else:
            return ()

    def _setshape(self, shape):
        if self.NDIM:
            try:
                array = numpy.full(shape, self.initvalue, dtype=float)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying create a new numpy ndarray` for sequence %s'
                    % objecttools.devicephrase(self))
            if array.ndim == self.NDIM:
                setattr(self.fastaccess, self.name, array)
            else:
                raise ValueError(
                    'Sequence %s is %d-dimensional, but the given '
                    'shape indicates %d dimensions.'
                    % (objecttools.devicephrase(self),
                       self.NDIM, array.ndim))
        else:
            if shape:
                raise ValueError(
                    'The shape information of 0-dimensional sequences '
                    'as %s can only be `()`, but `%s` is given.'
                    % (objecttools.devicephrase(self), shape))
            else:
                self.value = 0.

    shape = property(_getshape, _setshape)

    def __getitem__(self, key):
        try:
            return self.values[key]
        except BaseException:
            self._raiseitemexception()

    def __setitem__(self, key, values):
        try:
            self.values[key] = values
        except BaseException:
            self._raiseitemexception()

    def _raiseitemexception(self):
        if self.values is None:
            raise RuntimeError(
                'Sequence %s has no values so far.'
                % objecttools.devicephrase(self))
        else:
            objecttools.augment_excmessage(
                'While trying to item access the values of sequence %s'
                % objecttools.devicephrase(self))

    def __repr__(self):
        islong = self.length > 255
        return variabletools.Variable.repr_(self, self.values, islong)

    def __dir__(self):
        return objecttools.dir_(self)


abctools.SequenceABC.register(Sequence)


class IOSequence(Sequence):
    """Base class for sequences with input/output functionalities."""

    def __init__(self):
        Sequence.__init__(self)
        self._rawfilename = None
        self._filetype_ext = None
        self._filename_ext = None
        self._dirpath_ext = None
        self._dirpath_int = None
        self._filepath_ext = None
        self._filepath_int = None

    def _getfiletype_ext(self):
        """Ending of the external data file.

        Normally, each sequence queries its current "external" file type
        from the |SequenceManager| object stored in module |pub|:

        >>> from hydpy import pub
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        Depending if the actual sequence is logged as an |InputSequenceABC|,
        |OutputSequenceABC|, or |NodeSequenceABC|, either
        |SequenceManager.inputfiletype|, |SequenceManager.outputfiletype|,
        or |SequenceManager.nodefiletype| are queried:

        >>> pub.sequencemanager.inputfiletype = 'npy'
        >>> pub.sequencemanager.outputfiletype = 'asc'
        >>> pub.sequencemanager.nodefiletype = 'nc'
        >>> from hydpy.core import sequencetools as st
        >>> st.InputSequence().filetype_ext
        'npy'
        >>> st.FluxSequence().filetype_ext
        'asc'
        >>> st.NodeSequence().filetype_ext
        'nc'

        Alternatively, you can specify |IOSequence.filetype_ext| for each
        sequence object individually:

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
        RuntimeError: For sequence `inputsequence` the type of the \
external data file cannot be determined.  Either set it manually or \
prepare `pub.sequencemanager` correctly.
        """
        if self._filetype_ext:
            return self._filetype_ext
        else:
            try:
                if isinstance(self, abctools.InputSequenceABC):
                    return pub.sequencemanager.inputfiletype
                elif isinstance(self, abctools.NodeSequenceABC):
                    return pub.sequencemanager.nodefiletype
                return pub.sequencemanager.outputfiletype
            except AttributeError:
                raise RuntimeError(
                    'For sequence %s the type of the external data '
                    'file cannot be determined.  Either set it manually '
                    'or prepare `pub.sequencemanager` correctly.'
                    % objecttools.devicephrase(self))

    def _setfiletype_ext(self, name):
        self._filetype_ext = name

    def _delfiletype_ext(self):
        self._filetype_ext = None

    filetype_ext = property(
        _getfiletype_ext, _setfiletype_ext, _delfiletype_ext)

    def _getfilename_ext(self):
        """Complete filename of the external data file.

        The "external" filename consists either of
        |ModelIOSequence.rawfilename| of subclass |ModelIOSequence] of
        |NodeSequence.rawfilename| of subclass |NodeSequence], and of
        |IOSequence.filetype_ext| of class |IOSequence|.  For simplicity,
        we define add the attribute `rawfilename` to the initialized
        sequence object in the following example:

        >>> from hydpy.core import sequencetools as st
        >>> seq = st.IOSequence()
        >>> seq.rawfilename = 'test'
        >>> seq.filetype_ext = 'npy'
        >>> seq.filename_ext
        'test.npy'
        """
        if self._filename_ext:
            return self._filename_ext
        return '.'.join((self.rawfilename, self.filetype_ext))

    def _setfilename_ext(self, name):
        self._filename_ext = name

    def _delfilename_ext(self):
        self._filename_ext = None

    filename_ext = property(
        _getfilename_ext, _setfilename_ext, _delfilename_ext)

    def _getfilename_int(self):
        """Complete filename of the internal data file.

        The "external" filename consists either of
        |ModelIOSequence.rawfilename| of subclass |ModelIOSequence] of
        |NodeSequence.rawfilename| of subclass |NodeSequence] and the
        file ending `.bin`.  For simplicity, we define add the attribute
        `rawfilename` to the initialized sequence object in the following
        example:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> seq = IOSequence()
        >>> seq.rawfilename = 'test'
        >>> seq.filename_int
        'test.bin'
        """
        return self.rawfilename + '.bin'

    filename_int = property(_getfilename_int)

    def _getdirpath_ext(self):
        """Absolute path of the directory of the external data file.

        Normally, each sequence queries its current "external" directory
        path from the |SequenceManager| object stored in module |pub|:

        >>> from hydpy import pub
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        We overwrite |FileManager.basepath| and disable checking the
        existence of given paths in order to simplify the following
        examples:

        >>> basepath = SequenceManager.basepath
        >>> SequenceManager.basepath = 'test'
        >>> pub.sequencemanager.check_exists = False

        Depending if the actual sequence is logged as an |InputSequenceABC|,
        |OutputSequenceABC|, or |NodeSequenceABC|, either
        |SequenceManager.inputpath|, |SequenceManager.outputpath|,
        or |SequenceManager.nodepath| are queried:

        >>> from hydpy.core import sequencetools as st
        >>> from hydpy import repr_
        >>> repr_(st.InputSequence().dirpath_ext)
        'test/input'
        >>> repr_(st.FluxSequence().dirpath_ext)
        'test/output'
        >>> repr_(st.NodeSequence().dirpath_ext)
        'test/node'

        Alternatively, you can specify |IOSequence.dirpath_ext| for each
        sequence object individually:

        >>> seq = st.InputSequence()
        >>> from hydpy import repr_
        >>> repr_(seq.dirpath_ext)
        'test/input'
        >>> seq.dirpath_ext = 'path'
        >>> repr_(seq.dirpath_ext)
        'path'
        >>> del seq.dirpath_ext
        >>> repr_(seq.dirpath_ext)
        'test/input'

        If neither an individual definition nor |SequenceManager| is
        available, the following error is raised:

        >>> del pub.sequencemanager
        >>> seq.dirpath_ext
        Traceback (most recent call last):
        ...
        RuntimeError: For sequence `inputsequence` the directory of \
the external data file cannot be determined.  Either set it manually \
or prepare `pub.sequencemanager` correctly.

        Remove the `basepath` mock:

        >>> SequenceManager.basepath = basepath
        """
        if self._dirpath_ext:
            return self._dirpath_ext
        else:
            try:
                if isinstance(self, InputSequence):
                    return pub.sequencemanager.inputpath
                elif isinstance(self, NodeSequence):
                    return pub.sequencemanager.nodepath
                return pub.sequencemanager.outputpath
            except AttributeError:
                raise RuntimeError(
                    'For sequence %s the directory of the external '
                    'data file cannot be determined.  Either set it '
                    'manually or prepare `pub.sequencemanager` correctly.'
                    % objecttools.devicephrase(self))

    def _setdirpath_ext(self, name):
        self._dirpath_ext = name

    def _deldirpath_ext(self):
        self._dirpath_ext = None

    dirpath_ext = property(
        _getdirpath_ext, _setdirpath_ext, _deldirpath_ext)

    def _getdirpath_int(self):
        """Absolute path of the directory of the internal data file.

        Normally, each sequence queries its current "internal" directory
        path from the |SequenceManager| object stored in module |pub|:

        >>> from hydpy import pub
        >>> from hydpy.core.filetools import SequenceManager
        >>> pub.sequencemanager = SequenceManager()

        We overwrite |FileManager.basepath| and disable checking the
        existence of given paths in order to simplify the following
        examples:

        >>> basepath = SequenceManager.basepath
        >>> SequenceManager.basepath = 'test'
        >>> pub.sequencemanager.check_exists = False

        Generally, |SequenceManager.temppath| is queried:

        >>> import os
        >>> from hydpy.core import sequencetools as st
        >>> seq = st.InputSequence()
        >>> from hydpy import repr_
        >>> repr_(seq.dirpath_int)
        'test/temp'

        Alternatively, you can specify |IOSequence.dirpath_int| for each
        sequence object individually:

        >>> seq.dirpath_int = 'path'
        >>> os.path.split(seq.dirpath_int)
        ('', 'path')
        >>> del seq.dirpath_int
        >>> os.path.split(seq.dirpath_int)
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
        if self._dirpath_int:
            return self._dirpath_int
        else:
            try:
                return pub.sequencemanager.temppath
            except AttributeError:
                raise RuntimeError(
                    'For sequence %s the directory of the internal '
                    'data file cannot be determined.  Either set it '
                    'manually or prepare `pub.sequencemanager` correctly.'
                    % objecttools.devicephrase(self))

    def _setdirpath_int(self, name):
        self._dirpath_int = name

    def _deldirpath_int(self):
        self._dirpath_int = None
    dirpath_int = property(
        _getdirpath_int, _setdirpath_int, _deldirpath_int)

    def _getfilepath_ext(self):
        """Absolute path to the external data file.

        The path pointing to the "external" file consists of
        |IOSequence.dirpath_ext| and |IOSequence.filename_ext|.  For
        simplicity, we define both manually in the following example:

        >>> from hydpy.core.sequencetools import IOSequence
        >>> seq = IOSequence()
        >>> seq.dirpath_ext = 'path'
        >>> seq.filename_ext = 'file.npy'
        >>> from hydpy import repr_
        >>> repr_(seq.filepath_ext)
        'path/file.npy'
        """
        if self._filepath_ext:
            return self._filepath_ext
        return os.path.join(self.dirpath_ext, self.filename_ext)

    def _setfilepath_ext(self, name):
        self._filepath_ext = name

    def _delfilepath_ext(self):
        self._filepath_ext = None

    filepath_ext = property(
        _getfilepath_ext, _setfilepath_ext, _delfilepath_ext)

    def _getfilepath_int(self):
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
        if self._filepath_int:
            return self._filepath_int
        return os.path.join(self.dirpath_int, self.filename_int)

    def _setfilepath_int(self, name):
        self._filepath_int = name

    def _delfilepath_int(self):
        self._filepath_int = None

    filepath_int = property(
        _getfilepath_int, _setfilepath_int, _delfilepath_int)

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

    def _getdiskflag(self):
        diskflag = getattr(
            self.fastaccess, '_%s_diskflag' % self.name, None)
        if diskflag is not None:
            return diskflag
        else:
            raise RuntimeError(
                'The `diskflag` of sequence `%s` has not been set yet.'
                % objecttools.devicephrase(self))

    def _setdiskflag(self, value):
        setattr(self.fastaccess, '_%s_diskflag' % self.name, bool(value))

    diskflag = property(_getdiskflag, _setdiskflag)

    def _getramflag(self):
        ramflag = getattr(self.fastaccess, '_%s_ramflag' % self.name, None)
        if ramflag is not None:
            return ramflag
        else:
            raise RuntimeError(
                'The `ramflag` of sequence `%s` has not been set yet.'
                % objecttools.devicephrase(self))

    def _setramflag(self, value):
        setattr(self.fastaccess, '_%s_ramflag' % self.name, bool(value))

    ramflag = property(_getramflag, _setramflag)

    def _getmemoryflag(self):
        return self.ramflag or self.diskflag

    memoryflag = property(_getmemoryflag)

    def _getarray(self):
        array = getattr(self.fastaccess, '_%s_array' % self.name, None)
        if array is not None:
            return numpy.asarray(array)
        else:
            raise RuntimeError(
                'The `ram array` of sequence `%s` has not been set yet.'
                % objecttools.devicephrase(self))

    def _setarray(self, values):
        values = numpy.array(values, dtype=float)
        setattr(self.fastaccess, '_%s_array' % self.name, values)

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

    def _getseries(self):
        if self.diskflag:
            return self._load_int()
        elif self.ramflag:
            return self._getarray()
        else:
            raise RuntimeError(
                'Sequence %s is not requested to make any internal '
                'data available to the user.'
                % objecttools.devicephrase(self))

    def _setseries(self, values):
        series = self.series
        series[:] = values
        if self.diskflag:
            self._save_int(series)
        elif self.ramflag:
            self._setarray(series)
        else:
            raise RuntimeError(
                'Sequence `%s` is not requested to make any '
                'internal data available to the user.'
                % objecttools.devicephrase(self))

    def _delseries(self):
        if self.diskflag:
            os.remove(self.filepath_int)
        elif self.ramflag:
            setattr(self.fastaccess, '_%s_array' % self.name, None)

    series = property(_getseries, _setseries, _delseries)

    def load_ext(self):
        """Load the external data series in accordance with
        `pub.timegrids.init` and store it as internal data.
        """
        if self.filetype_ext == 'npy':
            timegrid_data, values = self._load_npy()
        else:
            timegrid_data, values = self._load_asc()
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
                values = self.adjust_short_series(timegrid_data, values)
        else:
            idx1 = timegrid_data[pub.timegrids.init.firstdate]
            idx2 = timegrid_data[pub.timegrids.init.lastdate]
            values = values[idx1:idx2]
        if self.diskflag:
            self._save_int(values)
        elif self.ramflag:
            self._setarray(values)
        else:
            raise RuntimeError(
                'Sequence %s is not requested to make '
                'any internal data available the the user.'
                % objecttools.devicephrase(self))

    def adjust_short_series(self, timegrid, values):
        """Adjust a short time series to a longer timegrid.

        Normally, time series data to be read from a external data files
        should span (at least) the whole initialization time period of a
        HydPy project.  However, for some variables which are only used
        for comparison (e.g. observed runoff used for calibration),
        incomplete time series might also be helpful.  This method it
        thought for adjusting such incomplete series to the public
        initialization time grid stored in module |pub|.  It is
        automatically called in method |IOSequence.load_ext| if necessary
        provided that the option |Options.checkseries| is disabled.

        Assume the initialization time period of a HydPy project spans
        five day:

        >>> from hydpy import pub, Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('2000.01.10',
        ...                                    '2000.01.15',
        ...                                    '1d'))

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
        if self.filetype_ext == 'npy':
            series = pub.timegrids.init.array2series(self.series)
            numpy.save(self.filepath_ext, series)
        else:
            with open(self.filepath_ext, 'w') as file_:
                file_.write(repr(pub.timegrids.init) + '\n')
            with open(self.filepath_ext, 'ab') as file_:
                numpy.savetxt(file_, self.series, delimiter='\t')

    def _load_npy(self):
        """Return the data timegrid and the complete external data from a
        binary numpy file.
        """
        try:
            data = numpy.load(self.filepath_ext)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to load the external data of sequence '
                '%s from file `%s`'
                % (objecttools.devicephrase(self), self.filepath_ext))
        try:
            timegrid_data = timetools.Timegrid.fromarray(data)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to retrieve the data timegrid of the '
                'external data file `%s` of sequence %s'
                % (self.filepath_ext, objecttools.devicephrase(self)))
        return timegrid_data, data[13:]

    def _load_asc(self):
        with open(self.filepath_ext) as file_:
            header = '\n'.join([file_.readline() for idx in range(3)])
        timegrid_data = eval(header, {}, {'Timegrid': timetools.Timegrid})
        values = numpy.loadtxt(self.filepath_ext, skiprows=3,
                               ndmin=self.NDIM+1)
        return timegrid_data, values

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
            self._setarray(values)
        else:
            raise RuntimeError(
                'Sequence %s is not requested to make any '
                'internal data available to the user.'
                % objecttools.devicephrase(self.name))

    def _save_int(self, values):
        values.tofile(self.filepath_int)

    def activate_disk(self):
        """Demand reading/writing internal data from/to hard disk."""
        self.deactivate_ram()
        self.diskflag = True
        if (isinstance(self, InputSequence) or
                (isinstance(self, NodeSequence) and self.use_ext)):
            self.load_ext()
        else:
            self.zero_int()
        self.update_fastaccess()

    def deactivate_disk(self):
        """Prevent from reading/writing internal data from/to hard disk."""
        if self.diskflag:
            del self.series
            self.diskflag = False

    def activate_ram(self):
        """Demand reading/writing internal data from/to hard disk."""
        self.deactivate_disk()
        self.ramflag = True
        if (isinstance(self, InputSequence) or
                (isinstance(self, NodeSequence) and self.use_ext)):
            self.load_ext()
        else:
            self.zero_int()
        self.update_fastaccess()

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
        self._setarray(values)
        self.update_fastaccess()

    def ram2disk(self):
        """Move internal data from RAM to disk."""
        values = self.series
        self.deactivate_ram()
        self.diskflag = True
        self._save_int(values)
        self.update_fastaccess()

    def _setshape(self, shape):
        Sequence._setshape(self, shape)
        self.update_fastaccess()

    shape = property(Sequence._getshape, _setshape)

    def _getrawfilename(self):
        """Filename without ending for external and internal date files."""
        if self._rawfilename:
            return self._rawfilename
        else:
            try:
                return '%s_%s' % (self.descr_device, self.descr_sequence)
            except AttributeError:
                raise RuntimeError(
                    'For sequence `%s` the raw filename cannot determined.  '
                    'Either set it manually or embed the sequence object '
                    'into a device object.'
                    % self.name)

    def _setrawfilename(self, name):
        self._rawfilename = str(name)

    def _delrawfilename(self):
        self._rawfilename = None

    rawfilename = property(_getrawfilename, _setrawfilename, _delrawfilename)


class ModelIOSequence(IOSequence):
    """Base class for sequences to be handled by |Model| objects."""

    @property
    def descr_sequence(self):
        """Description of the |ModelIOSequence| object itself and the
        |SubSequences| group it belongs to.

        >>> from hydpy import prepare_model
        >>> from hydpy.models import test_v1
        >>> model = prepare_model(test_v1)
        >>> model.sequences.fluxes.q.descr_sequence
        'q_fluxes'
        """
        return '%s_%s' % (self.name, self.subseqs.name)

    @property
    def descr_model(self):
        """Description of the |Model| the |ModelIOSequence| object belongs to.

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
        """Description of the |Element| object the |ModelIOSequence| object
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


class InputSequence(ModelIOSequence):
    """Base class for input sequences of |Model| objects."""


abctools.InputSequenceABC.register(InputSequence)


class FluxSequence(ModelIOSequence):
    """Base class for flux sequences of |Model| objects."""

    def _initvalues(self):
        ModelIOSequence._initvalues(self)
        if self.NUMERIC:
            value = None if self.NDIM else numpy.zeros(self.numericshape)
            self._connect_subattr('points', value)
            self._connect_subattr('integrals', copy.copy(value))
            self._connect_subattr('results', copy.copy(value))
            value = None if self.NDIM else 0.
            self._connect_subattr('sum', value)

    def _setshape(self, shape):
        ModelIOSequence._setshape(self, shape)
        if self.NDIM and self.NUMERIC:
            self._connect_subattr('points', numpy.zeros(self.numericshape))
            self._connect_subattr('integrals', numpy.zeros(self.numericshape))
            self._connect_subattr('results', numpy.zeros(self.numericshape))
            self._connect_subattr('sum', numpy.zeros(self.shape))

    shape = property(ModelIOSequence._getshape, _setshape)


abctools.FluxSequenceABC.register(FluxSequence)


class LeftRightSequence(ModelIOSequence):
    NDIM = 1

    def _initvalues(self):
        setattr(self.fastaccess, self.name,
                numpy.full(2, self.initvalue, dtype=float))

    def _getleft(self):
        """The "left" value of the actual parameter."""
        return self.values[0]

    def _setleft(self, value):
        self.values[0] = value

    left = property(_getleft, _setleft)

    def _getright(self):
        """The "right" value of the actual parameter."""
        return self.values[1]

    def _setright(self, value):
        self.values[1] = value

    right = property(_getright, _setright)


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


class StateSequence(ModelIOSequence, ConditionSequence):
    """Base class for state sequences of |Model| objects."""

    NOT_DEEPCOPYABLE_MEMBERS = ('subseqs', 'fastaccess_old', 'fastaccess_new')

    def __init__(self):
        ModelIOSequence.__init__(self)
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
        ModelIOSequence.connect(self, subseqs)
        self.fastaccess_old = subseqs.fastaccess_old
        self.fastaccess_new = subseqs.fastaccess_new
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, None)
        else:
            setattr(self.fastaccess_old, self.name, 0.)

    def _initvalues(self):
        ModelIOSequence._initvalues(self)
        if self.NUMERIC:
            value = None if self.NDIM else numpy.zeros(self.numericshape)
            self._connect_subattr('points', value)
            self._connect_subattr('results', copy.copy(value))

    def _setshape(self, shape):
        ModelIOSequence._setshape(self, shape)
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, self.new.copy())
            if self.NUMERIC:
                self._connect_subattr('points',
                                      numpy.zeros(self.numericshape))
                self._connect_subattr('results',
                                      numpy.zeros(self.numericshape))

    shape = property(ModelIOSequence._getshape, _setshape)

    new = Sequence.values
    """Complete access to the state value(s), which will be used in the
    next calculation steps.  Note that |StateSequence.new| is a synonym
    of |Sequence.values|.  Use this property to modify the initial
    condition(s) of a single |StateSequence| object.
    """

    def _getold(self):
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

    def _setold(self, value):
        if self.NDIM == 0:
            try:
                temp = value[0]
                if len(value) > 1:
                    raise ValueError(
                        '%d values are assigned to the scalar '
                        'sequence `%s`, which is ambiguous.'
                        % (len(value)), self.name)
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

    old = property(_getold, _setold)

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
    """Base class for aide sequences of |Model| objects."""
    pass


abctools.AideSequenceABC.register(AideSequence)


class LinkSequence(Sequence):
    """Base class for link sequences of |Model| objects."""

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

    def _getvalue(self):
        """ToDo"""
        raise AttributeError(
            'To retrieve a pointer is very likely to result in bugs '
            'and is thus not supported at the moment.')

    def _setvalue(self, value):
        """Could be implemented, but is not important at the moment..."""
        raise AttributeError(
            'To change a pointer is very likely to result in bugs '
            'and is thus not supported at the moment.')

    value = property(_getvalue, _setvalue)
    values = value

    def _getshape(self):
        if self.NDIM == 0:
            return ()
        elif self.NDIM == 1:
            try:
                return getattr(self.fastaccess, self.name).shape
            except AttributeError:
                return (getattr(self.fastaccess, '_%s_length_0' % self.name),)
        raise NotImplementedError(
            'Getting the shape of a %d dimensional link sequence '
            'is not supported so far.'
            % self.NDIM)

    def _setshape(self, shape):
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

    shape = property(_getshape, _setshape)


abctools.LinkSequenceABC.register(LinkSequence)


class NodeSequence(IOSequence):
    """Base class for all sequences to be handled by |Node| objects."""

    @property
    def descr_sequence(self):
        """Description of the |NodeSequence| object including the
        |Node.variable| to be represented.

        >>> from hydpy import Node
        >>> Node('test_node_1', 'T').sequences.sim.descr_sequence
        'sim_T'
        """
        return '%s_%s' % (self.name, self.subseqs.node.variable)

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

    def _getvalues(self):
        """Actual value(s) handled by the sequence.  For consistency,
        `value` and `values` can always be used interchangeably."""
        try:
            return getattr(self.fastaccess, self.name)
        except AttributeError:
            if self.NDIM == 0:
                return self.fastaccess.getpointer0d(self.name)
            elif self.NDIM == 1:
                return self.fastaccess.getpointer1d(self.name)

    def _setvalues(self, values):
        getattr(self.fastaccess, self.name)[0] = values

    values = property(_getvalues, _setvalues)
    value = values


abctools.NodeSequenceABC.register(NodeSequence)


class Sim(NodeSequence):
    """Base class for simulation sequences of |Node| objects."""
    NDIM, NUMERIC = 0, False

    def __init__(self):
        NodeSequence.__init__(self)
        self.use_ext = False

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

    def __init__(self):
        NodeSequence.__init__(self)
        self.use_ext = True

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
    _SEQCLASSES = (Sim, Obs)

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
            if (diskflag or ramflag):
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


autodoctools.autodoc_module()
