# -*- coding: utf-8 -*-
"""This module supports writing auxiliary files.

In HydPy, parameter values are usually not shared between different
model objects handled by different elements, even if the model objects
are of the same type (e.g. HBV).  This offers flexibility in applying
different parameterization schemes.  But very often, modellers prefer
to use a very limited amount of values for certain parameters (at least
within hydrologically homogeneous regions).  Hence, the downside of
this flexibility is that the same parameter values might be defined in
hundreds or even thousands of parameter control files (one file for
each model/element).

To decrease this redundancy, HydPy allows for passing names of
`auxiliary` control files to parameters defined within `normal`
control files.  The actual parameter values are than read from the
auxiliary files, each one possibly referenced within a large number
of control files.

Reading parameters from `normal` and `auxiliary` control files is
straightforward.   But storing some parameters in a large number
of `normal` control files and some other parameters in a small number
of `auxiliary` files can be a little complicated.  The features
implemented in |auxfiletools| are a means to perform such actions in a
semi-automated manner (another means are the selection mechanism
implemented in module |selectiontools|).
"""
# import...
# ...from standard library
from __future__ import division, print_function
import copy
import importlib
import types
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import importtools
from hydpy.core import objecttools
from hydpy.core import parametertools


class Auxfiler(object):
    """Structures auxiliary file information.

    To save some parameter information to auxiliary files, it is advisable
    to prepare (only) one |Auxfiler| object:

    >>> from hydpy import Auxfiler
    >>> aux = Auxfiler()

    Each |Auxfiler| object is capable of handling parameter
    information for different kinds of models and performs some plausibility
    checks on added data.  Assume, we want to store the control files of
    a "LARSIM type" HydPy project involving the application models |lland_v1|,
    |lland_v2| and |lstream_v1|.  The following example shows, that these
    models can be added to the |Auxfiler| object by passing their module
    (|lland_v1|), a working model object (|lland_v2|) or their name
    (|lstream_v1|):


    >>> from hydpy import prepare_model
    >>> from hydpy.models import lland_v1 as module
    >>> from hydpy.models import lland_v2
    >>> model = prepare_model(lland_v2)
    >>> string = 'lstream_v1'

    All new model types can be added individually or in groups using the
    `+=` operator:

    >>> aux += module
    >>> aux += model, string
    >>> aux
    Auxfiler(lland_v1, lland_v2, lstream_v1)

    Wrong model specifications result in errors like the following one:

    >>> aux += 'asdf'   # doctest: +SKIP
    Traceback (most recent call last):
    ...
    ModuleNotFoundError: While trying to add one ore more models to the \
actual auxiliary file handler, the following error occurred: \
While trying to import a model named `asdf`, the following error occurred: \
No module named `hydpy.models.asdf`.

    .. testsetup::

        >>> try:
        ...     aux += 'asdf'
        ... except ImportError:
        ...     pass


    The |Auxfiler| object allocates a separate |Variable2Auxfile| object to
    each model type.  These are available via attribute reading access, but
    setting new or deleting existing |Variable2Auxfile| objects is disabled
    for safety purposes:

    >>> aux.lland_v1
    Variable2Auxfile()
    >>> aux.lland_v2 = aux.lland_v1
    Traceback (most recent call last):
    ...
    AttributeError: Auxiliary file handler do not support setting \
attributes.  Use the `+=` operator to register additional models instead.
    >>> del aux.lland_v1
    Traceback (most recent call last):
    ...
    AttributeError: Auxiliary file handler do not support deleting \
attributes.  Use the `-=` operator to remove registered models instead.

    As stated by the last error message, removing models and their
    |Variable2Auxfile| object should be done via the `-=` operator:

    >>> aux -= module, string
    >>> aux
    Auxfiler(lland_v2)

    The handling of the individual |Variable2Auxfile| objects is
    explained below.  But there are some additional plausibility checks,
    which require that these objects are contained by a single master
    |Auxfiler| object.  For demonstration, the removed models are added again:

    >>> aux += module, string

    The first plausibility check is for duplicate filenames:

    >>> model.parameters.control.eqd1(200.0)
    >>> aux.lland_v1.file1 = model.parameters.control.eqd1
    >>> model.parameters.control.eqd2(100.0)
    >>> aux.lland_v2.file1 = model.parameters.control.eqd2
    Traceback (most recent call last):
    ...
    ValueError: While trying to extend the range of variables handled \
by the actual Variable2AuxFile object, the following error occurred: \
Filename `file1` is already allocated to another `Variable2Auxfile` object.
    >>> aux.lland_v2.file2 = model.parameters.control.eqd2

    Secondly, it is checked if an assigned parameter actually belongs
    to the corresponding model:

    >>> aux.lstream_v1.file3 = model.parameters.control.eqd1
    Traceback (most recent call last):
    ...
    TypeError: While trying to extend the range of variables handled \
by the actual Variable2AuxFile object, the following error occurred: \
Variable type `EQD1` is not handled by model `lstream_v1`.
    >>> aux.lland_v2.file2 = model.parameters.control.eqd1

    The |Auxfiler| object defined above is also used in the documentation
    of the following class members.  Hence it is stored in the |Dummies|
    object:

    >>> from hydpy import dummies
    >>> dummies.aux = aux
    """
    def __init__(self):
        with objecttools.ResetAttrFuncs(self):
            self._dict = {}

    def __iadd__(self, values):
        try:
            for model in self._get_models(values):
                self._dict[str(model)] = Variable2Auxfile(
                    _master=self, _model=model)
            return self
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to add one ore more models '
                'to the actual auxiliary file handler')

    def __isub__(self, values):
        try:
            for model in self._get_models(values):
                try:
                    del self._dict[str(model)]
                except KeyError:
                    raise AttributeError(
                        'The handler does not contain model `%s`.'
                        % model)
            return self
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to remove one or more models '
                'from the actual auxiliary file handler')

    @staticmethod
    def _get_models(values):
        for value in objecttools.extract(
                values, (str, types.ModuleType, abctools.ModelABC)):
            yield Auxfiler._get_model(value)

    @staticmethod
    def _get_model(value):
        if isinstance(value, abctools.StringABC):
            try:
                value = importlib.import_module('hydpy.models.'+value)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to import a model named `%s`'
                    % value)
        if isinstance(value, types.ModuleType):
            try:
                value = importtools.prepare_model(value)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to prepare the model defined in'
                    'module `hydpy.models.%s`'
                    % objecttools.modulename(value))
        return value

    def __getattr__(self, name):
        try:
            return self._dict[name]
        except KeyError:
            raise AttributeError(
                'The actual auxiliary file handler does neither have a '
                'standard member nor does it handle a model named `%s`.'
                % name)

    def __setattr__(self, name, value):
        raise AttributeError(
            'Auxiliary file handler do not support setting attributes.  '
            'Use the `+=` operator to register additional models instead.')

    def __delattr__(self, name):
        raise AttributeError(
            'Auxiliary file handler do not support deleting attributes.  '
            'Use the `-=` operator to remove registered models instead.')

    def __iter__(self):
        for (key, value) in sorted(self._dict.items()):
            yield (key, value)

    @property
    def modelnames(self):
        """A sorted list of all names of the handled models.

        >>> from hydpy import dummies
        >>> dummies.aux.modelnames
        ['lland_v1', 'lland_v2', 'lstream_v1']
    """
        return sorted(self._dict.keys())

    def save(self, parameterstep=None, simulationstep=None):
        """Save all defined auxiliary control files.

        The target path is taken from the |ControlManager| object stored
        in module |pub|.  Hence we initialize one and override its
        |property| `currentpath` with a simple |str| object defining the
        test target path:

        >>> from hydpy import pub
        >>> pub.projectname = 'test'
        >>> from hydpy.core.filetools import ControlManager
        >>> ControlManager.currentpath = 'test_directory'
        >>> pub.controlmanager = ControlManager()

        Normally, the control files would be written to disk, of course.
        But to show (and test) the results in the following doctest,
        file writing is temporarily redirected via |Open|:

        >>> from hydpy import dummies
        >>> from hydpy import Open
        >>> with Open():
        ...     dummies.aux.save(
        ...         parameterstep='1d',
        ...         simulationstep='12h')
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        test_directory/file1.py
        -----------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.lland_v1 import *
        <BLANKLINE>
        simulationstep("12h")
        parameterstep("1d")
        <BLANKLINE>
        eqd1(200.0)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        test_directory/file2.py
        -----------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.lland_v2 import *
        <BLANKLINE>
        simulationstep("12h")
        parameterstep("1d")
        <BLANKLINE>
        eqd1(200.0)
        eqd2(100.0)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """
        par = parametertools.Parameter
        if not parameterstep:
            parameterstep = par.parameterstep
        if not simulationstep:
            simulationstep = par.simulationstep
        for (modelname, var2aux) in self:
            for filename in var2aux.filenames:
                with par.parameterstep(parameterstep), \
                         par.simulationstep(simulationstep):
                    lines = [parametertools.header_controlfile(
                        modelname, parameterstep, simulationstep)]
                    for par in getattr(var2aux, filename):
                        lines.append(repr(par) + '\n')
                pub.controlmanager.save_file(filename, ''.join(lines))

    __copy__ = objecttools.copy_

    __deepcopy__ = objecttools.deepcopy_

    def __repr__(self):
        return objecttools.assignrepr_values(
            self.modelnames, 'Auxfiler(', width=70) + ')'

    def __dir__(self):
        """
        >>> from hydpy import print_values
        >>> aux = Auxfiler()
        >>> aux += 'llake_v1', 'lland_v1', 'lstream_v1'
        >>> print_values(dir(aux))
        llake_v1, lland_v1, lstream_v1, modelnames, save
        """
        return objecttools.dir_(self) + self.modelnames


class Variable2Auxfile(object):
    """Map |Variable| objects to names of auxiliary files.

    Normally, |Variable2Auxfile| object are not initialized by the
    user explicitly but made available by a `master` |Auxfiler| object.

    To show how |Variable2Auxfile| works, we firstly initialize a
    HydPy-L-Land (version 1) model:

    >>> from hydpy import pub
    >>> pub.options.usedefaultvalues = True
    >>> from hydpy.models.lland_v1 import *
    >>> simulationstep('1d')
    >>> parameterstep('1d')

    Note that we made use of the `usedefaultvalues` option.
    Hence, all parameters used in the following examples have
    some predefined values, e.g.:

    >>> eqb
    eqb(5000.0)

    Next, we initialize a |Variable2Auxfile| object, which is supposed
    to allocate some calibration parameters related to runoff
    concentration to two axiliary files named `file1` and `file2`:

    >>> from hydpy.core.auxfiletools import Variable2Auxfile
    >>> v2af = Variable2Auxfile()

    Auxiliary file `file1` shall contain the actual values of parameters
    `eqb`, `eqi1` and `eqi2`:

    >>> v2af.file1 = eqb
    >>> v2af.file1 = eqi1, eqi2
    >>> v2af.file1
    [eqb(5000.0), eqi1(2000.0), eqi2(1000.0)]

    Auxiliary file `file2` shall contain the actual values of parameters
    `eqd1`, `eqd2` and (also!) of parameter `eqb`:

    >>> v2af.file2 = eqd1, eqd2
    >>> v2af.file2 = eqb
    Traceback (most recent call last):
    ...
    ValueError: While trying to extend the range of variables handled by the \
actual Variable2AuxFile object, the following error occurred: You tried to \
allocate variable `eqb(5000.0)` to filename `file2`, but an equal `EQB` \
object has already been allocated to filename `file1`.
    >>> v2af.file2
    [eqd1(100.0), eqd2(50.0)]

    As explained by the error message, allocating the same parameter type
    with equal values to two different auxiliary files is not allowed.
    (If you really want to store equal values of the same type of parameter
    whithin different auxiliary files, work with selections instead.)

    Nevertheless, after changing the value of parameter `eqb`, it can be
    allocated to file name `file2`:

    >>> eqb *= 2
    >>> v2af.file2 = eqb
    >>> v2af.file2
    [eqb(10000.0), eqd1(100.0), eqd2(50.0)]

    The following example shows that the value of parameter `eqb` already
    allocated to `file1` has not been changed (this safety mechanism is
    accomplished via deep copying), and that all registered parameters can
    be viewed by using their names as an attribute names:

    >>> v2af.eqb
    [eqb(5000.0), eqb(10000.0)]

    Unfortunately, the string representations of |Variable2Auxfile|
    are not executable at the moment:

    >>> v2af
    Variable2Auxfile(file1, file2)

    The |Variable2Auxfile| object defined above is also used in the
    documentation of the following class members.  Hence it is stored in
    the |Dummies| object:

    >>> from hydpy import dummies
    >>> dummies.v2af = v2af

    The explanations above focus on parameter objects only.
    |Variable2Auxfile| could be used to handle sequence objects as well,
    but possibly without a big benefit as long as `auxiliary condition
    files` are not supported.
    """

    def __init__(self, _master=None, _model=None):
        with objecttools.ResetAttrFuncs(self):
            self._master = _master
            self._model = _model
            self._type2filename2variable = {}

    def __getattr__(self, name):
        variables = self._sort_variables(self._yield_variables(name))
        if variables:
            return variables
        else:
            raise AttributeError(
                '`{0}` is neither a filename nor a name of a variable '
                'handled by the actual Variable2AuxFile object.'
                .format(name))

    def __setattr__(self, filename, variables):
        try:
            self._check_filename(filename)
            new_vars = objecttools.extract(
                variables,
                (abctools.ParameterABC, abctools.ConditionSequenceABC))
            for new_var in new_vars:
                self._check_variable(new_var)
                fn2var = self._type2filename2variable.get(type(new_var), {})
                self._check_duplicate(fn2var, new_var, filename)
                fn2var[filename] = copy.deepcopy(new_var)
                self._type2filename2variable[type(new_var)] = fn2var
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to extend the range of variables handled by '
                'the actual Variable2AuxFile object')

    def _check_filename(self, filename):
        objecttools.valid_variable_identifier(filename)
        if self._master is not None:
            for dummy, var2aux in self._master:
                if (var2aux is not self) and (filename in var2aux.filenames):
                    raise ValueError(
                        'Filename `{0}` is already allocated to '
                        'another `Variable2Auxfile` object.'
                        .format(filename))

    def _check_variable(self, variable):
        if self._model and (variable not in self._model.parameters.control):
            raise TypeError(
                'Variable type `{0}` is not handled by model `{1}`.'
                .format(objecttools.classname(variable), self._model))

    @staticmethod
    def _check_duplicate(fn2var, new_var, filename):
        for (reg_fn, reg_var) in fn2var.items():
            if (reg_fn != filename) and (reg_var == new_var):
                raise ValueError(
                    'You tried to allocate variable `{0!r}` to '
                    'filename `{1}`, but an equal `{2}` object has '
                    'already been allocated to filename `{3}`.'
                    .format(new_var, filename,
                            objecttools.classname(new_var), reg_fn))

    def remove(self, *values):
        """Remove the defined variables.

        The variables to be removed can be selected in two ways.  But the
        first example shows that passing nothing or an empty iterable to
        method |Variable2Auxfile.remove| does not remove any variable:

        >>> from hydpy import dummies
        >>> v2af = dummies.v2af
        >>> v2af.remove()
        >>> v2af.remove([])
        >>> from hydpy import print_values
        >>> print_values(v2af.filenames)
        file1, file2
        >>> print_values(v2af.variables, width=30)
        eqb(5000.0), eqb(10000.0),
        eqd1(100.0), eqd2(50.0),
        eqi1(2000.0), eqi2(1000.0)

        The first option is to pass auxiliary file names:

        >>> v2af.remove('file1')
        >>> print_values(v2af.filenames)
        file2
        >>> print_values(v2af.variables)
        eqb(10000.0), eqd1(100.0), eqd2(50.0)

        The second option is, to pass variables of the correct type
        and value:

        >>> v2af = dummies.v2af
        >>> v2af.remove(v2af.eqb[0])
        >>> print_values(v2af.filenames)
        file1, file2
        >>> print_values(v2af.variables)
        eqb(10000.0), eqd1(100.0), eqd2(50.0), eqi1(2000.0), eqi2(1000.0)

        One can pass multiple variables or iterables containing variables
        at once:

        >>> v2af = dummies.v2af
        >>> v2af.remove(v2af.eqb, v2af.eqd1, v2af.eqd2)
        >>> print_values(v2af.filenames)
        file1
        >>> print_values(v2af.variables)
        eqi1(2000.0), eqi2(1000.0)

        Passing an argument that equals neither a registered file name or a
        registered variable results in the following exception:

        >>> v2af.remove('test')
        Traceback (most recent call last):
        ...
        ValueError: While trying to remove the given object `test` of type \
`str` from the actual Variable2AuxFile object, the following error occurred:  \
`'test'` is neither a registered filename nor a registered variable.
        """
        for value in objecttools.extract(values, (str, abctools.VariableABC)):
            try:
                deleted_something = False
                for fn2var in list(self._type2filename2variable.values()):
                    for fn_, var in list(fn2var.items()):
                        if value in (fn_, var):
                            del fn2var[fn_]
                            deleted_something = True
                if not deleted_something:
                    raise ValueError(
                        ' `{0!r}` is neither a registered filename nor a '
                        'registered variable.'.format(value))
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to remove the given object `{0}` of type '
                    '`{1}` from the actual Variable2AuxFile object'
                    .format(value, objecttools.classname(value)))

    @property
    def types(self):
        """A list of all handled variable types.

        >>> from hydpy import dummies
        >>> from hydpy import print_values
        >>> print_values(dummies.v2af.types, width=50)
        <class 'hydpy.models.lland.lland_control.EQB'>,
        <class 'hydpy.models.lland.lland_control.EQD1'>,
        <class 'hydpy.models.lland.lland_control.EQD2'>,
        <class 'hydpy.models.lland.lland_control.EQI1'>,
        <class 'hydpy.models.lland.lland_control.EQI2'>
        """
        return sorted(self._type2filename2variable.keys(), key=str)

    @property
    def filenames(self):
        """A list of all handled auxiliary file names.

        >>> from hydpy import dummies
        >>> dummies.v2af.filenames
        ['file1', 'file2']
        """
        fns = set()
        for fn2var in self._type2filename2variable.values():
            fns.update(fn2var.keys())
        return sorted(fns)

    @property
    def variables(self):
        """A list of all handled variable objects.

        >>> from hydpy import dummies
        >>> from hydpy import print_values
        >>> print_values(dummies.v2af.variables, width=30)
        eqb(5000.0), eqb(10000.0),
        eqd1(100.0), eqd2(50.0),
        eqi1(2000.0), eqi2(1000.0)
        """
        return self._sort_variables(self._yield_variables())

    def _yield_variables(self, name=None):
        for fn2var in self._type2filename2variable.values():
            for fn_, var in fn2var.items():
                if name in (None, fn_, var.name):
                    yield var

    @staticmethod
    def _sort_variables(variables):
        return sorted(variables, key=lambda x: (x.name, sum(x)))

    def get_filename(self, variable):
        """Return the auxiliary file name the given variable is allocated
        to or |None| if the given variable is not allocated to any
        auxiliary file name.

        >>> from hydpy import dummies
        >>> eqb = dummies.v2af.eqb[0]
        >>> dummies.v2af.get_filename(eqb)
        'file1'
        >>> eqb += 500.0
        >>> dummies.v2af.get_filename(eqb)
        """
        fn2var = self._type2filename2variable.get(type(variable), {})
        for (fn_, var) in fn2var.items():
            if var == variable:
                return fn_
        return None

    __copy__ = objecttools.copy_

    __deepcopy__ = objecttools.deepcopy_

    def __repr__(self):
        return objecttools.assignrepr_values(
            self.filenames, 'Variable2Auxfile(', width=70) + ')'

    def __dir__(self):
        """
        >>> from hydpy import dummies
        >>> from hydpy import print_values
        >>> print_values(dir(dummies.v2af))
        eqb, eqd1, eqd2, eqi1, eqi2, file1, file2, filenames, get_filename,
        remove, types, variables
        """
        return (objecttools.dir_(self) +
                self.filenames +
                [objecttools.instancename(type_) for type_ in self.types])


autodoctools.autodoc_module()
