# -*- coding: utf-8 -*-
"""This module implements tools for increasing the level of automation and
standardisation of the online documentation generated with Sphinx.
"""
# import...
# ...from the Python standard library
from __future__ import division, print_function
import collections
import copy
import importlib
import inspect
import os
import re
import sys
import types
# ...from HydPy
import hydpy
# from hydpy.core import objecttools (actual import commands moved to
# different functions below to avoid circular dependencies)


def description(self):
    """Returns the first "paragraph" of the docstring of the given object.

    Note that ugly things like multiple whitespaces and newline characters
    are removed:

    >>> from hydpy.core import autodoctools, objecttools
    >>> autodoctools.description(objecttools.augment_excmessage)
    'Augment an exception message with additional information while keeping \
the original traceback.'

    In case the given object does not define a docstring, the following
    is returned:
    >>> autodoctools.description(type('Test', (), {}))
    'no description available'
    """
    if self.__doc__ in (None, ''):
        return 'no description available'
    return ' '.join(self.__doc__.split('\n\n')[0].split())


_PAR_SPEC2CAPT = collections.OrderedDict((('parameters', 'Parameter tools'),
                                          ('constants', 'Constants'),
                                          ('control', 'Control parameters'),
                                          ('derived', 'Derived parameters')))

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

_all_spec2capt = _PAR_SPEC2CAPT.copy()   # pylint: disable=invalid-name
_all_spec2capt.update(_SEQ_SPEC2CAPT)


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
    if caption.split()[-1] in ('parameters', 'sequences'):
        exists_collectionclass = True
        name_collectionclass = caption.title().replace(' ', '')
    else:
        exists_collectionclass = False
    lines = []
    if specification == 'model':
        lines += ['',
                  '.. autoclass:: ' + module.__name__ + '.Model',
                  '    :members:',
                  '    :show-inheritance:']
    elif exists_collectionclass:
        lines += ['',
                  '.. autoclass:: %s.%s' % (module.__name__,
                                            name_collectionclass),
                  '    :members:',
                  '    :show-inheritance:']
    lines += ['',
              '.. automodule:: ' + module.__name__,
              '    :members:',
              '    :show-inheritance:']
    if specification == 'model':
        lines += ['    :exclude-members: Model']
    elif exists_collectionclass:
        lines += ['    :exclude-members: ' + name_collectionclass]
    return lines


def autodoc_basemodel():
    """Add an exhaustive docstring to the `__init__` module of a basemodel.

    One just has to write `autodoc_basemodel()` at the bottom of an `__init__`
    module of a basemodel, and all model, parameter and sequence information
    are appended to the modules docstring.  The resulting docstring is suitable
    automatic documentation generation via `Sphinx` and `autodoc`.  Hence
    it helps in constructing HydPy's online documentation and supports the
    embeded help feature of `Spyder` (to see the result, import the package
    of an arbitrary basemodel, e.g. `from hydpy.models import lland` and
    press `cntr+i` with the cursor placed on `lland` written in the IPython
    console afterwards).

    Note that the resulting documentation will be complete only when the
    modules of the basemodel are named in the standard way, e.g. `lland_model`,
    `lland_control`, `lland_inputs`.
    """
    if getattr(sys, 'frozen', False):
        # Do nothing when HydPy has been freezed with PyInstaller.
        return
    namespace = inspect.currentframe().f_back.f_locals
    doc = namespace.get('__doc__')
    if doc is None:
        doc = ''
    basemodulename = namespace['__name__'].split('.')[-1]
    modules = {key: value for key, value in namespace.items()
               if (isinstance(value, types.ModuleType) and
                   key.startswith(basemodulename+'_'))}
    substituter = Substituter(hydpy.substituter)
    lines = []
    specification = 'model'
    modulename = basemodulename+'_'+specification
    if modulename in modules:
        module = modules[modulename]
        lines += _add_title('Model features', '-')
        lines += _add_lines(specification, module)
        substituter.add_everything(module)
    for (spec2capt, title) in zip((_PAR_SPEC2CAPT, _SEQ_SPEC2CAPT),
                                  ('Parameter features', 'Sequence features')):
        new_lines = _add_title(title, '-')
        found_module = False
        for (specification, caption) in spec2capt.items():
            modulename = basemodulename+'_'+specification
            module = modules.get(modulename)
            if module:
                found_module = True
                new_lines += _add_title(caption, '.')
                new_lines += _add_lines(specification, module)
                substituter.add_everything(module)
        if found_module:
            lines += new_lines
    doc += '\n'.join(lines)
    namespace['__doc__'] = doc
    basemodule = importlib.import_module(namespace['__name__'])
    substituter.add_everything(basemodule)
    substituter.apply_on_members()
    namespace['substituter'] = substituter


def autodoc_applicationmodel():
    """Improves the docstrings of application models when called
    at the bottom of the respective module.

    |autodoc_applicationmodel| requires, similar to
    |autodoc_basemodel|, that both the application model and its
    base model are defined in the conventional way.
    """
    if getattr(sys, 'frozen', False):
        # Do nothing when HydPy has been freezed with PyInstaller.
        return
    namespace = inspect.currentframe().f_back.f_locals
    doc = namespace.get('__doc__')
    if doc is None:
        doc = ''
    name_applicationmodel = namespace['__name__']
    module_applicationmodel = importlib.import_module(name_applicationmodel)
    name_basemodel = name_applicationmodel.split('_')[0]
    module_basemodel = importlib.import_module(name_basemodel)
    substituter = Substituter(module_basemodel.substituter)
    substituter.add_everything(module_applicationmodel)
    substituter.apply_on_members()
    namespace['substituter'] = substituter


class Substituter(object):
    """Implements a HydPy specific docstring substitution mechanism."""

    def __init__(self, substituter=None):
        if substituter:
            self.substitutions = copy.deepcopy(substituter.substitutions)
            self.fallbacks = copy.deepcopy(substituter.fallbacks)
            self.blacklist = copy.deepcopy(substituter.blacklist)
        else:
            self.substitutions = {}
            self.fallbacks = {}
            self.blacklist = set()
        self.members = []
        self.regex = None

    def update(self):
        """Update the internal substitution commands based on all
        substitutions defined so far."""
        self.regex = re.compile('|'.join(map(re.escape, self.substitutions)))

    def add_everything(self, module, cython=False):
        """Add all members of the given module including the module itself."""
        name_module = module.__name__.split('.')[-1]
        short = '|%s|' % name_module
        self.substitutions[short] = ':mod:`~%s`' % module.__name__
        if not cython:
            self.members.append(module)
        for (name, member) in module.__dict__.items():
            if name.startswith('_'):
                continue
            if getattr(member, '__module__', None) != module.__name__:
                continue
            if name == 'CONSTANTS':
                for key, value in member.items():
                    self._add_single_object(
                        'const', name_module, module, key, value, cython)
                continue
            if inspect.isfunction(member):
                role = 'func'
            elif inspect.isclass(member):
                role = 'class'
            elif cython:
                role = 'func'
            else:
                continue
            self._add_single_object(
                role, name_module, module, name, member, cython)

    def _add_single_object(
            self, role, name_module, module, name_member, member, cython):
        short = '|%s|' % name_member
        medium = ('|%s.%s|' % (name_module, name_member))
        long = ':%s:`~%s.%s`' % (role, module.__name__, name_member)
        if short not in self.blacklist:
            if short in self.substitutions:
                self.blacklist.add(short)
                del self.substitutions[short]
            else:
                self.substitutions[short] = long
        self.substitutions[medium] = long
        if not cython:
            self.members.append(member)

    def add_modules(self, package):
        """Add the modules of the given package without not their members."""
        for name in os.listdir(package.__path__[0]):
            if name.startswith('_'):
                continue
            name = name.split('.')[0]
            short = '|%s|' % name
            long = ':mod:`~%s.%s`' % (package.__package__, name)
            self.substitutions[short] = long

    def _get_substitute(self, match):
        return self.substitutions[match.group(0)]

    def __call__(self, text):
        return self.regex.sub(self._get_substitute, text)

    def apply_on_members(self):
        """Apply all substitutions defined so far on all handled members."""
        self.update()
        for member in self.members:
            try:
                member.__doc__ = self(member.__doc__)
            except (AttributeError, TypeError):
                pass
            for submember in getattr(member, '__dict__', {}).values():
                try:
                    submember.__doc__ = self(submember.__doc__)
                except (AttributeError, TypeError):
                    pass


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


def autodoc_module():
    """Add a short summary of all implemented members to a modules docstring.

    Just write `autodoctools.autodoc_module()` at the very bottom of the
    module.

    Note that function :func:`autodoc_module` is not thought to be used for
    modules defining models.  For base models, see function
    :func:`autodoc_basemodel` instead.
    """
    if getattr(sys, 'frozen', False):
        # Do nothing when HydPy has been freezed with PyInstaller.
        return
    module = inspect.getmodule(inspect.currentframe().f_back)
    doc = module.__doc__
    if doc is None:
        doc = ''
    lines = ['\n\nModule :mod:`~%s` implements the following members:\n'
             % module.__name__]
    members = []
    for (name, member) in inspect.getmembers(module):
        if ((not name.startswith('_')) and
                (inspect.getmodule(member) is module)):
            members.append((name, member))
    members = sorted(members, key=_number_of_line)
    for (name, member) in members:
        if inspect.isfunction(member):
            type_ = 'func'
        elif inspect.isclass(member):
            type_ = 'class'
        else:
            type_ = 'obj'
        lines.append('      * :%s:`~%s` %s'
                     % (type_, name, description(member)))
    module.__doc__ = doc + '\n\n' + '\n'.join(lines) + '\n\n' + 80*'_'


autodoc_module()
