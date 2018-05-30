# -*- coding: utf-8 -*-
"""Move, create and modify documentation files before applying `Sphinx`.

Sphinx is to be executed in a freshly created folder named `auto`.  If
this folder exists already, `prepare` removes it first and builds it from
scratch afterwards, in order to assure that no old documentation files
find their way into the html documentation.
"""

# import...
# ...from standard library
import importlib
import inspect
import os
import shutil
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))
# pylint: disable=wrong-import-position
# (changing the path is necessary when calling `prepare.py` from the
# command line)
# ...from HydPy
import hydpy
from hydpy import auxs
from hydpy import core
from hydpy import cythons
from hydpy import docs
from hydpy import models
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.docs import figs
from hydpy.docs import sphinx
from hydpy.docs import rst

# Prepare folder `auto`.
AUTOPATH = os.path.join(docs.__path__[0], 'auto')
if os.path.exists(AUTOPATH):
    shutil.rmtree(AUTOPATH)
os.makedirs(AUTOPATH)
shutil.copytree(os.path.join(docs.__path__[0], 'html'),
                os.path.join(AUTOPATH, 'html'))

# Import all base and application models, to make sure all substituters
# are up-to-date. (I am not sure, if this is really necessary, but it
# does not hurt.)
for filename in os.listdir(models.__path__[0]):
    if not filename.startswith('_'):
        filename = filename.split('.')[0]
        importlib.import_module(
            '%s.%s'
            % (models.__name__, filename))

# Write one rst file for each module (including the ones defining application
# models) and each base model defining a base model.  Each rst file should
# contain commands to trigger the autodoc mechanism of Sphinx as well as
# the substitution replacement commands relevant for the respective module
# or package.
for subpackage in (auxs, core, cythons, models):
    filenames = os.listdir(subpackage.__path__[0])
    substituter = hydpy.substituter
    for filename in filenames:
        is_module = (
            (filename.endswith('py') or filename.endswith('pyx')) and
            (filename != '__init__.py'))
        is_package = (
            (subpackage is models) and
            ('.' not in filename) and
            (filename not in ('build', '__pycache__')))
        if is_module:
            path = os.path.join(subpackage.__path__[0], filename)
            sources = [open(path, encoding='utf-8').read()]
            module = importlib.import_module(
                '%s.%s' % (subpackage.__name__, filename.split('.')[0]))
            for member in getattr(module, '__dict__', {}).values():
                if (inspect.isclass(member) and
                        issubclass(member, (parametertools.SubParameters,
                                            sequencetools.SubSequences,
                                            modeltools.Model))):
                    sources.append(member.__doc__ if member.__doc__ else '')
            source = '\n'.join(sources)
        if is_package:
            sources = []
            path = os.path.join(subpackage.__path__[0], filename)
            for subfilename in os.listdir(path):
                if subfilename.endswith('.py'):
                    subpath = os.path.join(path, subfilename)
                    sources.append(open(subpath, encoding='utf-8').read())
            source = '\n'.join(sources)
        filename = filename.split('.')[0]
        if (is_module and (subpackage is models)) or is_package:
            module = importlib.import_module(
                '%s.%s' % (models.__name__, filename))
            substituter = module.substituter
        if is_module or is_package:
            lines = []
            lines.append('')
            lines.append('.. _%s:' % filename)
            lines.append('')
            lines.append(filename)
            lines.append('=' * len(filename))
            lines.append('')
            lines.append('.. automodule:: %s'
                         % '.'.join((subpackage.__name__, filename)))
            lines.append('    :members:')
            lines.append('    :show-inheritance:')
            lines.append('')
            path = os.path.join(AUTOPATH, filename+'.rst')
            with open(path, 'w', encoding="utf-8") as file_:
                file_.write(substituter.get_commands(source))
                file_.write('\n')
                file_.write('\n'.join(lines))

# Copy additional files into folder `auto` and, for the rst files, add the
# required substitution replacement commands.
for subpackage in (figs, sphinx, rst):
    for filename in os.listdir(subpackage.__path__[0]):
        path_in = os.path.join(subpackage.__path__[0], filename)
        path_out = os.path.join(AUTOPATH, filename)
        if filename not in ('__init__.py', '__pycache__'):
            if subpackage is rst:
                orig = open(path_in, encoding="utf-8").read()
                with open(path_out, 'w', encoding="utf-8") as file_:
                    file_.write(hydpy.substituter.get_commands(orig))
                    file_.write('\n')
                    file_.write(orig)
            else:
                shutil.copy(path_in, path_out)
