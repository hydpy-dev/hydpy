# -*- coding: utf-8 -*-
"""This module implements tools for increasing the level of automation and
standardisation of the online documentation generated with Sphinx.
"""
# import...
# ...from standard library
import builtins
import collections
import copy
import datetime
import doctest
import importlib
import inspect
import itertools
import io
import math
import mimetypes
import os
import platform
import pkgutil
import subprocess
import sys
import time
import types
import typing
from typing import *
import unittest
# ...from site-packages
import numpy
import scipy
# ...from HydPy
import hydpy
from hydpy import auxs
from hydpy import core
from hydpy import cythons
from hydpy import exe
from hydpy import models
from hydpy import examples
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.cythons.autogen import annutils
from hydpy.cythons.autogen import pointerutils
from hydpy.cythons.autogen import smoothutils

EXCLUDE_MEMBERS = (
    'CLASSES',
    'RUN_METHODS',
    'ADD_METHODS',
    'INLET_METHODS',
    'OUTLET_METHODS',
    'RECEIVER_METHODS',
    'SENDER_METHODS',
    'PART_ODE_METHODS',
    'FULL_ODE_METHODS',
    'CONTROLPARAMETERS',
    'DERIVEDPARAMETERS',
    'FIXEDPARAMETERS',
    'REQUIREDSEQUENCES',
    'UPDATEDSEQUENCES',
    'RESULTSEQUENCES',
    'SOLVERPARAMETERS',
    'SOLVERSEQUENCES',
    'SUBMETHODS',
)

_PAR_SPEC2CAPT = collections.OrderedDict((('parameters', 'Parameter tools'),
                                          ('constants', 'Constants'),
                                          ('control', 'Control parameters'),
                                          ('derived', 'Derived parameters'),
                                          ('fixed', 'Fixed parameters'),
                                          ('solver', 'Solver parameters')))

_SEQ_SPEC2CAPT = collections.OrderedDict((('sequences', 'Sequence tools'),
                                          ('inputs', 'Input sequences'),
                                          ('fluxes', 'Flux sequences'),
                                          ('states', 'State sequences'),
                                          ('logs', 'Log sequences'),
                                          ('inlets', 'Inlet sequences'),
                                          ('outlets', 'Outlet sequences'),
                                          ('receivers', 'Receiver sequences'),
                                          ('senders', 'Sender sequences'),
                                          ('aides', 'Aide sequences')))

_AUX_SPEC2CAPT = collections.OrderedDict((('masks', 'Masks'),))

_all_spec2capt = _PAR_SPEC2CAPT.copy()
_all_spec2capt.update(_SEQ_SPEC2CAPT)
_all_spec2capt.update(_AUX_SPEC2CAPT)


def _add_title(title, marker):
    """Return a title for a basemodels docstring."""
    return ['', title, marker*len(title)]


def _add_lines(specification, module):
    """Return autodoc commands for a basemodels docstring.

    Note that `collection classes` (e.g. `Model`, `ControlParameters`,
    `InputSequences` are placed on top of the respective section and the
    `contained classes` (e.g. model methods, `ControlParameter` instances,
    `InputSequence` instances at the bottom.  This differs from the order
    of their definition in the respective modules, but results in a better
    documentation structure.
    """
    caption = _all_spec2capt.get(specification, 'dummy')
    if caption.split()[-1] in ('parameters', 'sequences', 'Masks'):
        exists_collectionclass = True
        name_collectionclass = caption.title().replace(' ', '')
    else:
        exists_collectionclass = False
    lines = []
    exc_mem = ", ".join(EXCLUDE_MEMBERS)
    if specification == 'model':
        lines += [f'',
                  f'.. autoclass:: {module.__name__}.Model',
                  f'    :members:',
                  f'    :show-inheritance:',
                  f'    :exclude-members: {exc_mem}']
    elif exists_collectionclass:
        lines += [f'',
                  f'.. autoclass:: {module.__name__.rpartition(".")[0]}'
                  f'.{name_collectionclass}',
                  f'    :members:',
                  f'    :show-inheritance:',
                  f'    :exclude-members: {exc_mem}']
    lines += ['',
              '.. automodule:: ' + module.__name__,
              '    :members:',
              '    :show-inheritance:']
    if specification == 'model':
        lines += [f'    :exclude-members: Model, {exc_mem}']
    elif exists_collectionclass:
        lines += [f'    :exclude-members:  {name_collectionclass}, {exc_mem}']
    return lines


def autodoc_basemodel(module):
    """Add an exhaustive docstring to the given module of a basemodel.

    Works onlye when all modules of the basemodel are named in the
    standard way, e.g. `lland_model`, `lland_control`, `lland_inputs`.
    """
    autodoc_tuple2doc(module)
    namespace = module.__dict__
    moduledoc = namespace.get('__doc__')
    basemodulename = namespace['__name__'].split('.')[-1]
    modules = {key: value for key, value in namespace.items()
               if (isinstance(value, types.ModuleType) and
                   key.startswith(basemodulename+'_'))}
    substituter = Substituter(hydpy.substituter)
    lines = []
    specification = 'model'
    modulename = f'{basemodulename}_{specification}'
    if modulename in modules:
        module = modules[modulename]
        lines += _add_title('Method Features', '-')
        lines += _add_lines(specification, module)
        substituter.add_module(module)
        methods = list(module.Model.get_methods())
    _extend_methoddocstrings(module)
    _gain_and_insert_additional_information_into_docstrings(module, methods)
    for (title, spec2capt) in (('Parameter Features', _PAR_SPEC2CAPT),
                               ('Sequence Features', _SEQ_SPEC2CAPT),
                               ('Auxiliary Features', _AUX_SPEC2CAPT)):
        found_module = False
        new_lines = _add_title(title, '-')
        for (specification, caption) in spec2capt.items():
            modulename = basemodulename+'_'+specification
            module = modules.get(modulename)
            if module:
                found_module = True
                new_lines += _add_title(caption, '.')
                new_lines += _add_lines(specification, module)
                substituter.add_module(module)
                _gain_and_insert_additional_information_into_docstrings(
                    module, methods)
        if found_module:
            lines += new_lines
    moduledoc += '\n'.join(lines)
    namespace['__doc__'] = moduledoc
    basemodule = importlib.import_module(namespace['__name__'])
    substituter.add_module(basemodule)
    substituter.update_masters()
    namespace['substituter'] = substituter


def _insert_links_into_docstring(target, insertion):
    try:
        target.__doc__ += ''
    except BaseException:
        return
    doc = getattr(target, '__doc__', None)
    if doc is not None:
        position = target.__doc__.find('\n\n')
        if position == -1:
            target.__doc__ = '\n\n'.join([doc, insertion])
        else:
            position += 2
            target.__doc__ = ''.join([
                doc[:position],
                insertion,
                doc[position:],
            ])
    return


def _extend_methoddocstrings(module):
    for method in module.Model.get_methods():
        _insert_links_into_docstring(
            method, '\n'.join(_get_methoddocstringinsertions(method)))


def _get_ending(container: Sized):
    return 's' if len(container) > 1 else ''


def _get_methoddocstringinsertions(method):
    insertions = []
    submethods = getattr(method, 'SUBMETHODS', ())
    if submethods:
        insertions.append(
            f'    Required submethod{_get_ending(submethods)}:')
        for submethod in submethods:
            insertions.append(f'      :class:`~{submethod.__module__}.'
                              f'{submethod.__name__}`')
        insertions.append('')
    for pargroup in ('control', 'derived', 'fixed', 'solver'):
        pars = getattr(method, f'{pargroup.upper()}PARAMETERS', ())
        if pars:
            insertions.append(
                f'    Requires the {pargroup} parameter{_get_ending(pars)}:')
            for par in pars:
                insertions.append(
                    f'      :class:`~{par.__module__}.{par.__name__}`')
            insertions.append('')
    for statement, tuplename in (
            ('Requires the', 'REQUIREDSEQUENCES'),
            ('Updates the', 'UPDATEDSEQUENCES'),
            ('Calculates the', 'RESULTSEQUENCES')):
        for seqtype in (
                sequencetools.InletSequence,
                sequencetools.ReceiverSequence,
                sequencetools.InputSequence,
                sequencetools.FluxSequence,
                sequencetools.StateSequence,
                sequencetools.LogSequence,
                sequencetools.AideSequence,
                sequencetools.OutletSequence,
                sequencetools.SenderSequence):
            seqs = [seq for seq in getattr(method, tuplename, ())
                    if issubclass(seq, seqtype)]
            if seqs:
                insertions.append(
                    f'    {statement} '
                    f'{seqtype.__name__[:-8].lower()} '
                    f'sequence{_get_ending(seqs)}:'
                )
                for seq in seqs:
                    insertions.append(
                        f'      :class:`~{seq.__module__}.{seq.__name__}`')
                insertions.append('')
    if insertions:
        insertions.append('')
    return insertions


def _gain_and_insert_additional_information_into_docstrings(module, allmethods):
    for value in vars(module).values():
        insertions = []
        for role, description in (('SUBMETHODS', 'Required'),
                                  ('CONTROLPARAMETERS', 'Required'),
                                  ('DERIVEDPARAMETERS', 'Required'),
                                  ('FIXEDPARAMETERS', 'Required'),
                                  ('RESULTSEQUENCES', 'Calculated'),
                                  ('UPDATEDSEQUENCES', 'Updated'),
                                  ('REQUIREDSEQUENCES', 'Required')):
            relevantmethods = set()
            for method in allmethods:
                if value in getattr(method, role, ()):
                    relevantmethods.add(method)
            if relevantmethods:
                subinsertions = []
                for method in relevantmethods:
                    subinsertions.append(f'      :class:`~{method.__module__}.'
                                         f'{method.__name__}`')
                insertions.append(
                    f'    {description} by the '
                    f'method{_get_ending(subinsertions)}:')
                insertions.extend(sorted(subinsertions))
                insertions.append('\n')

        _insert_links_into_docstring(value, '\n'.join(insertions))


def autodoc_applicationmodel(module):
    """Improves the docstrings of application models when called
    at the bottom of the respective module.

    |autodoc_applicationmodel| requires, similar to
    |autodoc_basemodel|, that both the application model and its
    base model are defined in the conventional way.
    """
    autodoc_tuple2doc(module)
    name_applicationmodel = module.__name__
    name_basemodel = name_applicationmodel.split('_')[0]
    module_basemodel = importlib.import_module(name_basemodel)
    substituter = Substituter(module_basemodel.substituter)
    substituter.add_module(module)
    substituter.update_masters()
    module.substituter = substituter


class Substituter:
    """Implements a HydPy specific docstring substitution mechanism."""

    def __init__(self, master=None):
        self.master = master
        self.slaves = []
        if master:
            master.slaves.append(self)
            self.short2long = copy.deepcopy(master.short2long)
            self.medium2long = copy.deepcopy(master.medium2long)
            self.blacklist = copy.deepcopy(master.blacklist)
        else:
            self.short2long = {}
            self.medium2long = {}
            self.blacklist = set()

    @staticmethod
    def consider_member(name_member, member, module, class_=None):
        """Return |True| if the given member should be added to the
        substitutions. If not return |False|.

        Some examples based on the site-package |numpy|:

        >>> from hydpy.core.autodoctools import Substituter
        >>> import numpy

        A constant like |numpy.nan| should be added:

        >>> Substituter.consider_member(
        ...     'nan', numpy.nan, numpy)
        True

        Members with a prefixed underscore should not be added:

        >>> Substituter.consider_member(
        ...     '_NoValue', numpy._NoValue, numpy)
        False

        Members that are actually imported modules should not be added:

        >>> Substituter.consider_member(
        ...     'warnings', numpy.warnings, numpy)
        False

        Members that are actually defined in other modules should
        not be added:

        >>> numpy.Substituter = Substituter
        >>> Substituter.consider_member(
        ...     'Substituter', numpy.Substituter, numpy)
        False
        >>> del numpy.Substituter

        Members that are defined in submodules of a given package
        (either from the standard library or from site-packages)
        should be added...

        >>> Substituter.consider_member(
        ...     'clip', numpy.clip, numpy)
        True

        ...but not members defined in *HydPy* submodules:

        >>> import hydpy
        >>> Substituter.consider_member(
        ...     'Node', hydpy.Node, hydpy)
        False

        For descriptor instances (with method `__get__`) beeing members
        of classes should be added:

        >>> from hydpy.auxs import anntools
        >>> Substituter.consider_member(
        ...     'shape_neurons', anntools.ANN.shape_neurons,
        ...     anntools, anntools.ANN)
        True
        """
        if name_member.startswith('_'):
            return False
        if inspect.ismodule(member):
            return False
        real_module = getattr(member, '__module__', None)
        if not real_module:
            return True
        if real_module != module.__name__:
            if class_ and hasattr(member, '__get__'):
                return True
            if 'hydpy' in real_module:
                return False
            if module.__name__ not in real_module:
                return False
        return True

    @staticmethod
    def get_role(member, cython=False):
        """Return the reStructuredText role `func`, `class`, or `const`
        best describing the given member.

        Some examples based on the site-package |numpy|.  |numpy.clip|
        is a function:

        >>> from hydpy.core.autodoctools import Substituter
        >>> import numpy
        >>> Substituter.get_role(numpy.clip)
        'func'

        |numpy.ndarray| is a class:

        >>> Substituter.get_role(numpy.ndarray)
        'class'

        |numpy.ndarray.clip| is a method, for which also the `function`
        role is returned:

        >>> Substituter.get_role(numpy.ndarray.clip)
        'func'

        For everything else the `constant` role is returned:

        >>> Substituter.get_role(numpy.nan)
        'const'

        When analysing cython extension modules, set the option `cython`
        flag to |True|.  |Double| is correctly identified as a class:

        >>> from hydpy.cythons import pointerutils
        >>> Substituter.get_role(pointerutils.Double, cython=True)
        'class'

        Only with the `cython` flag beeing |True|, for everything else
        the `function` text role is returned (doesn't make sense here,
        but the |numpy| module is not something defined in module
        |pointerutils| anyway):

        >>> Substituter.get_role(pointerutils.numpy, cython=True)
        'func'
        """
        if inspect.isroutine(member) or isinstance(member, numpy.ufunc):
            return 'func'
        if inspect.isclass(member):
            return 'class'
        if cython:
            return 'func'
        return 'const'

    def add_substitution(self, short, medium, long, module):
        """Add the given substitutions both as a `short2long` and a
        `medium2long` mapping.

        Assume `variable1` is defined in the hydpy module `module1` and the
        short and medium descriptions are `var1` and `mod1.var1`:

        >>> import types
        >>> module1 = types.ModuleType('hydpy.module1')
        >>> from hydpy.core.autodoctools import Substituter
        >>> substituter = Substituter()
        >>> substituter.add_substitution(
        ...     'var1', 'mod1.var1', 'module1.variable1', module1)
        >>> print(substituter.get_commands())
        .. var1 replace:: module1.variable1
        .. mod1.var1 replace:: module1.variable1

        Adding `variable2` of `module2` has no effect on the predefined
        substitutions:

        >>> module2 = types.ModuleType('hydpy.module2')
        >>> substituter.add_substitution(
        ...     'var2', 'mod2.var2', 'module2.variable2', module2)
        >>> print(substituter.get_commands())
        .. var1 replace:: module1.variable1
        .. var2 replace:: module2.variable2
        .. mod1.var1 replace:: module1.variable1
        .. mod2.var2 replace:: module2.variable2

        But when adding `variable1` of `module2`, the `short2long` mapping
        of `variable1` would become inconclusive, which is why the new
        one (related to `module2`) is not stored and the old one (related
        to `module1`) is removed:

        >>> substituter.add_substitution(
        ...     'var1', 'mod2.var1', 'module2.variable1', module2)
        >>> print(substituter.get_commands())
        .. var2 replace:: module2.variable2
        .. mod1.var1 replace:: module1.variable1
        .. mod2.var1 replace:: module2.variable1
        .. mod2.var2 replace:: module2.variable2

        Adding `variable2` of `module2` accidentally again, does not
        result in any undesired side-effects:

        >>> substituter.add_substitution(
        ...     'var2', 'mod2.var2', 'module2.variable2', module2)
        >>> print(substituter.get_commands())
        .. var2 replace:: module2.variable2
        .. mod1.var1 replace:: module1.variable1
        .. mod2.var1 replace:: module2.variable1
        .. mod2.var2 replace:: module2.variable2

        In order to reduce the risk of name conflicts, only the
        `medium2long` mapping is supported for modules not part of the
        *HydPy* package:

        >>> module3 = types.ModuleType('module3')
        >>> substituter.add_substitution(
        ...     'var3', 'mod3.var3', 'module3.variable3', module3)
        >>> print(substituter.get_commands())
        .. var2 replace:: module2.variable2
        .. mod1.var1 replace:: module1.variable1
        .. mod2.var1 replace:: module2.variable1
        .. mod2.var2 replace:: module2.variable2
        .. mod3.var3 replace:: module3.variable3

        The only exception to this rule is |builtins|, for which only
        the `short2long` mapping is supported (note also, that the
        module name `builtins` is removed from string `long`):

        >>> import builtins
        >>> substituter.add_substitution(
        ...     'str', 'blt.str', ':func:`~builtins.str`', builtins)
        >>> print(substituter.get_commands())
        .. str replace:: :func:`str`
        .. var2 replace:: module2.variable2
        .. mod1.var1 replace:: module1.variable1
        .. mod2.var1 replace:: module2.variable1
        .. mod2.var2 replace:: module2.variable2
        .. mod3.var3 replace:: module3.variable3
        """
        name = module.__name__
        if 'builtin' in name:
            self.short2long[short] = long.split('~')[0] + long.split('.')[-1]
        else:
            if ('hydpy' in name) and (short not in self.blacklist):
                if short in self.short2long:
                    if self.short2long[short] != long:
                        self.blacklist.add(short)
                        del self.short2long[short]
                else:
                    self.short2long[short] = long
            self.medium2long[medium] = long

    def add_module(self, module, cython=False):
        """Add the given module, its members, and their submembers.

        The first examples are based on the site-package |numpy|: which
        is passed to method |Substituter.add_module|:

        >>> from hydpy.core.autodoctools import Substituter
        >>> substituter = Substituter()
        >>> import numpy
        >>> substituter.add_module(numpy)

        Firstly, the module itself is added:

        >>> substituter.find('|numpy|')
        |numpy| :mod:`~numpy`

        Secondly, constants like |numpy.nan| are added:

        >>> substituter.find('|numpy.nan|')
        |numpy.nan| :const:`~numpy.nan`

        Thirdly, functions like |numpy.clip| are added:

        >>> substituter.find('|numpy.clip|')
        |numpy.clip| :func:`~numpy.clip`

        Fourthly, clases line |numpy.ndarray| are added:

        >>> substituter.find('|numpy.ndarray|')
        |numpy.ndarray| :class:`~numpy.ndarray`

        When adding Cython modules, the `cython` flag should be set |True|:

        >>> from hydpy.cythons import pointerutils
        >>> substituter.add_module(pointerutils, cython=True)
        >>> substituter.find('set_pointer')
        |PPDouble.set_pointer| \
:func:`~hydpy.cythons.autogen.pointerutils.PPDouble.set_pointer`
        |pointerutils.PPDouble.set_pointer| \
:func:`~hydpy.cythons.autogen.pointerutils.PPDouble.set_pointer`
        """
        name_module = module.__name__.split('.')[-1]
        short = ('|%s|'
                 % name_module)
        long = (':mod:`~%s`'
                % module.__name__)
        self.short2long[short] = long
        for (name_member, member) in vars(module).items():
            if self.consider_member(
                    name_member, member, module):
                role = self.get_role(member, cython)
                short = ('|%s|'
                         % name_member)
                medium = ('|%s.%s|'
                          % (name_module,
                             name_member))
                long = (':%s:`~%s.%s`'
                        % (role,
                           module.__name__,
                           name_member))
                self.add_substitution(short, medium, long, module)
                if inspect.isclass(member):
                    for name_submember, submember in vars(member).items():
                        if self.consider_member(
                                name_submember, submember, module, member):
                            role = self.get_role(submember, cython)
                            short = ('|%s.%s|'
                                     % (name_member,
                                        name_submember))
                            medium = ('|%s.%s.%s|'
                                      % (name_module,
                                         name_member,
                                         name_submember))
                            long = (':%s:`~%s.%s.%s`'
                                    % (role,
                                       module.__name__,
                                       name_member,
                                       name_submember))
                            self.add_substitution(short, medium, long, module)

    def add_modules(self, package):
        """Add the modules of the given package without their members."""
        for name in os.listdir(package.__path__[0]):
            if name.startswith('_'):
                continue
            name = name.split('.')[0]
            short = '|%s|' % name
            long = ':mod:`~%s.%s`' % (package.__package__, name)
            self.short2long[short] = long

    def update_masters(self):
        """Update all `master` |Substituter| objects.

        If a |Substituter| object is passed to the constructor of another
        |Substituter| object, they become `master` and `slave`:

        >>> from hydpy.core.autodoctools import Substituter
        >>> sub1 = Substituter()
        >>> from hydpy.core import devicetools
        >>> sub1.add_module(devicetools)
        >>> sub2 = Substituter(sub1)
        >>> sub3 = Substituter(sub2)
        >>> sub3.master.master is sub1
        True
        >>> sub2 in sub1.slaves
        True

        During initialization, all mappings handled by the master object
        are passed to its new slave:

        >>> sub3.find('Node|')
        |Node| :class:`~hydpy.core.devicetools.Node`
        |devicetools.Node| :class:`~hydpy.core.devicetools.Node`

        Updating a slave, does not affect its master directly:

        >>> from hydpy.core import hydpytools
        >>> sub3.add_module(hydpytools)
        >>> sub3.find('HydPy|')
        |HydPy| :class:`~hydpy.core.hydpytools.HydPy`
        |hydpytools.HydPy| :class:`~hydpy.core.hydpytools.HydPy`
        >>> sub2.find('HydPy|')

        Through calling |Substituter.update_masters|, the `medium2long`
        mappings are passed from the slave to its master:

        >>> sub3.update_masters()
        >>> sub2.find('HydPy|')
        |hydpytools.HydPy| :class:`~hydpy.core.hydpytools.HydPy`

        Then each master object updates its own master object also:

        >>> sub1.find('HydPy|')
        |hydpytools.HydPy| :class:`~hydpy.core.hydpytools.HydPy`

        In reverse, subsequent updates of master objects to not affect
        their slaves directly:

        >>> from hydpy.core import masktools
        >>> sub1.add_module(masktools)
        >>> sub1.find('Masks|')
        |Masks| :class:`~hydpy.core.masktools.Masks`
        |masktools.Masks| :class:`~hydpy.core.masktools.Masks`
        >>> sub2.find('Masks|')

        Through calling |Substituter.update_slaves|, the `medium2long`
        mappings are passed the master to all of its slaves:

        >>> sub1.update_slaves()
        >>> sub2.find('Masks|')
        |masktools.Masks| :class:`~hydpy.core.masktools.Masks`
        >>> sub3.find('Masks|')
        |masktools.Masks| :class:`~hydpy.core.masktools.Masks`
        """
        if self.master is not None:
            self.master.medium2long.update(self.medium2long)
            self.master.update_masters()

    def update_slaves(self):
        """Update all `slave` |Substituter| objects.

        See method |Substituter.update_masters| for further information.
        """
        for slave in self.slaves:
            slave.medium2long.update(self.medium2long)
            slave.update_slaves()

    def get_commands(self, source=None):
        """Return a string containing multiple `reStructuredText`
        replacements with the substitutions currently defined.

        Some examples based on the subpackage |optiontools|:

        >>> from hydpy.core.autodoctools import Substituter
        >>> substituter = Substituter()
        >>> from hydpy.core import optiontools
        >>> substituter.add_module(optiontools)

        When calling |Substituter.get_commands| with the `source`
        argument, the complete `short2long` and `medium2long` mappings
        are translated into replacement commands (only a few of them
        are shown):

        >>> print(substituter.get_commands())
        .. |Options.autocompile| replace:: \
:const:`~hydpy.core.optiontools.Options.autocompile`
        .. |Options.checkseries| replace:: \
:const:`~hydpy.core.optiontools.Options.checkseries`
        ...
        .. |optiontools.Options.warntrim| replace:: \
:const:`~hydpy.core.optiontools.Options.warntrim`
        .. |optiontools.Options| replace:: \
:class:`~hydpy.core.optiontools.Options`

        Through passing a string (usually the source code of a file
        to be documented), only the replacement commands relevant for
        this string are translated:

        >>> from hydpy.core import objecttools
        >>> import inspect
        >>> source = inspect.getsource(objecttools)
        >>> print(substituter.get_commands(source))
        .. |Options.reprdigits| replace:: \
:const:`~hydpy.core.optiontools.Options.reprdigits`
        """
        commands = []
        for key, value in self:
            if (source is None) or (key in source):
                commands.append('.. %s replace:: %s' % (key, value))
        return '\n'.join(commands)

    def find(self, text):
        """Print all substitutions that include the given text string."""
        for key, value in self:
            if (text in key) or (text in value):
                print(key, value)

    def __iter__(self):
        for item in sorted(self.short2long.items()):
            yield item
        for item in sorted(self.medium2long.items()):
            yield item


def prepare_mainsubstituter():
    """Prepare and return a |Substituter| object for the main `__init__`
    file of *HydPy*."""
    substituter = Substituter()
    for module in (builtins, numpy, datetime, unittest, doctest, inspect, io,
                   os, sys, time, collections, itertools, subprocess, scipy,
                   typing, platform, math, mimetypes):
        substituter.add_module(module)
    for subpackage in (auxs, core, cythons, exe):
        for _, name, _ in pkgutil.walk_packages(subpackage.__path__):
            full_name = subpackage.__name__ + '.' + name
            substituter.add_module(importlib.import_module(full_name))
    substituter.add_module(examples)
    substituter.add_modules(models)
    for cymodule in (annutils, smoothutils, pointerutils):
        substituter.add_module(cymodule, cython=True)
    substituter.short2long['|pub|'] = ':mod:`~hydpy.pub`'
    substituter.short2long['|config|'] = ':mod:`~hydpy.config`'
    return substituter


def _number_of_line(member_tuple):
    """Try to return the number of the first line of the definition of a
    member of a module."""
    member = member_tuple[1]
    try:
        return member.__code__.co_firstlineno
    except AttributeError:
        pass
    try:
        return inspect.findsource(member)[1]
    except BaseException:
        pass
    for value in vars(member).values():
        try:
            return value.__code__.co_firstlineno
        except AttributeError:
            pass
    return 0


def autodoc_module(module):
    """Add a short summary of all implemented members to a modules docstring.
    """
    doc = getattr(module, '__doc__')
    members = []
    for name, member in inspect.getmembers(module):
        if ((not name.startswith('_')) and
                (inspect.getmodule(member) is module)):
            members.append((name, member))
    members = sorted(members, key=_number_of_line)
    if members:
        lines = ['\n\nModule :mod:`~%s` implements the following members:\n'
                 % module.__name__]
        for (name, member) in members:
            if inspect.isfunction(member):
                type_ = 'func'
            elif inspect.isclass(member):
                type_ = 'class'
            else:
                type_ = 'obj'
            lines.append('      * :%s:`~%s` %s'
                         % (type_, name, objecttools.description(member)))
        doc = doc + '\n\n' + '\n'.join(lines) + '\n\n' + 80*'_'
        module.__doc__ = doc


_name2descr = {
    'CLASSES': 'The following classes are selected',
    'RUN_METHODS': ('The following "run methods" are called '
                    'each simulation step run in the given sequence'),
    'ADD_METHODS': ('The following "additional methods" are '
                    'called by at least one "run method"'),
    'INLET_METHODS': ('The following "inlet update methods" '
                      'are called in the given sequence immediately '
                      'of the respective model'),
    'OUTLET_METHODS': ('The following "outlet update methods" '
                       'are called in the given sequence immediately '
                       'after solving the differential equations '
                       'of the respective model'),
    'RECEIVER_METHODS': ('The following "receiver update methods" '
                         'are called in the given sequence before solving '
                         'the differential equations of any model'),
    'SENDER_METHODS': ('The following "sender update methods" '
                       'are called in the given sequence after solving '
                       'the differential equations of all models'),
    'PART_ODE_METHODS': ('The following methods define the '
                         'relevant components of a system of ODE '
                         'equations (e.g. direct runoff)'),
    'FULL_ODE_METHODS': ('The following methods define the '
                         'complete equations of an ODE system '
                         '(e.g. change in storage of `fast water` due to '
                         ' effective precipitation and direct runoff)')
}

_loggedtuples: Set[str] = set()


def autodoc_tuple2doc(module):
    """Include tuples as `CLASSES` of `ControlParameters` and `RUN_METHODS`
    of `Models` into the respective docstring."""
    modulename = module.__name__
    for membername, member in inspect.getmembers(module):
        for tuplename, descr in _name2descr.items():
            tuple_ = getattr(member, tuplename, None)
            if tuple_:
                logstring = f'{modulename}.{membername}.{tuplename}'
                if logstring not in _loggedtuples:
                    _loggedtuples.add(logstring)
                    lst = [f'\n\n\n    {descr}:']
                    if tuplename == 'CLASSES':
                        type_ = 'func'
                    else:
                        type_ = 'class'
                    for cls in tuple_:
                        lst.append(
                            f'      * '
                            f':{type_}:`~{cls.__module__}.{cls.__name__}`'
                            f' {objecttools.description(cls)}')
                    doc = getattr(member, '__doc__')
                    member.__doc__ = doc + '\n'.join(l for l in lst)
