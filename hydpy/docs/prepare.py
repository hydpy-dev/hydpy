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
from hydpy import exe
from hydpy import models
from hydpy.core import masktools
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
try:
    shutil.move(os.path.join(AUTOPATH, 'html', 'coverage.html'),
                os.path.join(AUTOPATH, 'coverage.html'))
except BaseException:
    print('coverage.html could not be moved')

# Import all base and application models, to make sure all substituters
# are up-to-date. (I am not sure, if this is really necessary, but it
# does not hurt.)
for filename in os.listdir(models.__path__[0]):
    if not filename.startswith('_'):
        filename = filename.split('.')[0]
        importlib.import_module(
            '%s.%s'
            % (models.__name__, filename))
hydpy.substituter.update_slaves()

# Write one rst file for each module (including the ones defining application
# models) and each base model defining a base model.  Each rst file should
# contain commands to trigger the autodoc mechanism of Sphinx as well as
# the substitution replacement commands relevant for the respective module
# or package.
path2source = {}
for subpackage in (auxs, core, cythons, exe, models):
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
            with open(path, encoding='utf-8') as file_:
                sources = [file_.read()]
            module = importlib.import_module(
                '%s.%s' % (subpackage.__name__, filename.split('.')[0]))
            for member in getattr(module, '__dict__', {}).values():
                if (inspect.isclass(member) and
                        issubclass(member, (modeltools.Model,
                                            parametertools.SubParameters,
                                            sequencetools.SubSequences,
                                            masktools.Masks))):
                    sources.append(member.__doc__ if member.__doc__ else '')
            source = '\n'.join(sources)
        if is_package:
            sources = []
            path = os.path.join(subpackage.__path__[0], filename)
            for subfilename in os.listdir(path):
                if subfilename.endswith('.py'):
                    subpath = os.path.join(path, subfilename)
                    with open(subpath, encoding='utf-8') as file_:
                        sources.append(file_.read())
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
                path2source[path] = source
                file_.write(substituter.get_commands(source))
                file_.write('\n')
                file_.write('\n'.join(lines))

# Copy additional files into folder `auto` and, for the rst files, add the
# required substitution replacement commands.
for subpackage in (figs, sphinx, rst):
    for filename in os.listdir(subpackage.__path__[0]):
        path_in = os.path.join(subpackage.__path__[0], filename)
        path_out = os.path.join(AUTOPATH, filename)
        if os.path.isfile(path_in) and (filename != '__init__.py'):
            if subpackage is rst:
                with open(path_in, encoding="utf-8") as file_:
                    orig = file_.read()
                with open(path_out, 'w', encoding="utf-8") as file_:
                    source = path2source.get(path_out, '')
                    source = '\n'.join([source, orig])
                    file_.write(hydpy.substituter.get_commands(source))
                    file_.write('\n')
                    file_.write(orig)
            elif filename != 'build':
                shutil.copy(path_in, path_out)
