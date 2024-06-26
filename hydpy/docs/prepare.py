# -*- coding: utf-8 -*-
"""Move, create and modify documentation files before applying `Sphinx`.

Sphinx is to be executed in a freshly created folder named `auto`.  If this folder
exists already, `prepare` removes it first and builds it from scratch afterwards, in
order to assure that no old documentation files find their way into the html
documentation.
"""

# import...
# ...from standard library
import importlib
import inspect
import os
import shutil
import sys
import zipfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))
# pylint: disable=wrong-import-position
# (changing the path is necessary when calling `prepare.py` from the command line)
# ...from HydPy
import hydpy
from hydpy import auxs
from hydpy import core
from hydpy import cythons
from hydpy import data
from hydpy import docs
from hydpy import exe
from hydpy import interfaces
from hydpy import models
from hydpy.core import autodoctools
from hydpy.core import masktools
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import variabletools
from hydpy.docs import autofigs
from hydpy.docs import bib
from hydpy.docs import figs
from hydpy.docs import sphinx
from hydpy.docs import rst
from hydpy.core.typingtools import *

# Prepare folder `auto`.
docspath: str = docs.__path__[0]
AUTOPATH = os.path.join(docspath, "auto")
if os.path.exists(AUTOPATH):
    shutil.rmtree(AUTOPATH)
os.makedirs(AUTOPATH)
shutil.copytree(os.path.join(docspath, "html_"), os.path.join(AUTOPATH, "html_"))

# Import all base and application models, to make sure all substituters are up-to-date.
# (I am not sure if this is really necessary but it does not hurt.)
modelspath: str = models.__path__[0]
for filename in sorted(os.listdir(modelspath)):
    if not filename.startswith("_"):
        filename = filename.split(".")[0]
        importlib.import_module(f"{models.__name__}.{filename}")
hydpy.substituter.update_slaves()

# Write one rst file for each module (including the ones defining application models)
# and each base model defining a base model.  Each rst file should contain commands to
# trigger the autodoc mechanism of Sphinx as well as the substitution replacement
# commands relevant for the respective module or package.
path2source = {}
for subpackage in (auxs, core, cythons, exe, interfaces, models):
    subpackagepath: str = subpackage.__path__[0]
    filenames = sorted(os.listdir(subpackagepath))
    substituter = hydpy.substituter
    for filename in filenames:
        is_module = (filename.endswith("py") or filename.endswith("pyx")) and (
            filename != "__init__.py"
        )
        is_package = (
            (subpackage is models)
            and ("." not in filename)
            and (filename not in ("build", "__pycache__"))
        )
        assert not (is_module and is_package)
        source: Optional[str] = None
        if is_module:
            path = os.path.join(subpackagepath, filename)
            with open(path, encoding="utf-8") as file_:
                sources = [file_.read()]
            module = importlib.import_module(
                f'{subpackage.__name__}.{filename.partition(".")[0]}'
            )
            for member in getattr(module, "__dict__", {}).values():
                if inspect.isclass(member) and issubclass(
                    member,
                    (
                        modeltools.Model,
                        modeltools.Method,
                        parametertools.SubParameters,
                        sequencetools.SubSequences,
                        masktools.Masks,
                    ),
                ):
                    sources.append(member.__doc__ if member.__doc__ else "")
            source = "\n".join(sources)
        elif is_package:
            sources = []
            path = os.path.join(subpackagepath, filename)
            for subfilename in sorted(os.listdir(path)):
                if subfilename.endswith(".py"):
                    subpath = os.path.join(path, subfilename)
                    with open(subpath, encoding="utf-8") as file_:
                        sources.append(file_.read())
            source = "\n".join(sources)
            modulename = f'{subpackage.__name__}.{filename.partition(".")[0]}'
            module = importlib.import_module(modulename)
        filename = filename.partition(".")[0]
        if (is_module and (subpackage is models)) or is_package:
            module = importlib.import_module(f"{models.__name__}.{filename}")
            substituter = module.substituter
        if is_module or is_package:
            _exc_mem = autodoctools.excluded_members.copy()
            if subpackage is models:
                for member in vars(module).values():
                    if (
                        inspect.isclass(member)
                        and issubclass(member, variabletools.SubVariables)
                        and not member.CLASSES
                    ):
                        _exc_mem.add(member.__name__)
            excludemembers = ", ".join(_exc_mem)
            lines = [
                "",
                f".. _{filename}:",
                "",
                filename,
                "=" * len(filename),
                "",
                f'.. automodule:: {".".join((subpackage.__name__, filename))}',
                "    :members:",
                "    :show-inheritance:",
                f"    :exclude-members: {excludemembers}",
                "",
            ]
            path = os.path.join(AUTOPATH, filename + ".rst")
            with open(path, "w", encoding="utf-8") as file_:
                assert source is not None
                path2source[path] = source
                file_.write(substituter.get_commands(source))
                file_.write("\n")
                file_.write("\n".join(lines))

# Copy additional files into folder `auto` and, for the rst files, add the
# required substitution replacement commands.
for subpackage in (autofigs, bib, figs, sphinx, rst):
    subpackagepath = subpackage.__path__[0]
    for filename in sorted(os.listdir(subpackagepath)):
        path_in = os.path.join(subpackagepath, filename)
        path_out = os.path.join(AUTOPATH, filename)
        if os.path.isfile(path_in) and (filename != "__init__.py"):
            if subpackage is rst:
                with open(path_in, encoding="utf-8") as file_:
                    orig = file_.read()
                with open(path_out, "w", encoding="utf-8") as file_:
                    source = path2source.get(path_out, "")
                    source = "\n".join([source, orig])
                    file_.write(hydpy.substituter.get_commands(source))
                    file_.write("\n")
                    file_.write(orig)
            elif filename != "build":
                shutil.copy(path_in, path_out)

# copy _themes path from sphinx subpackage into folder `auto`
# _themes folder contains the modified sphinx html themes
themespath = os.path.join(sphinx.__path__[0], "_themes")
themespathdest = os.path.join(AUTOPATH, "_themes")
if not os.path.isdir(themespath):
    raise RuntimeError("Cannot find path `_themes` in sphinx subpackage")
shutil.copytree(themespath, themespathdest)

# Collect all example projects in individual zip archives
datadirpath = data.__path__[0]
for projectname in os.listdir(datadirpath):
    projectpath = os.path.join(datadirpath, projectname)
    if os.path.isdir(projectpath) and not projectname.startswith("_"):
        zipfilename = os.path.join(AUTOPATH, f"{projectname}.zip")
        with zipfile.ZipFile(zipfilename, "w") as zipfile_:
            for subdirpath, _, filenames in os.walk(projectpath):
                zipdirpath = os.path.relpath(subdirpath, datadirpath)
                for filename in filenames:
                    zipfile_.write(
                        filename=os.path.join(subdirpath, filename),
                        arcname=os.path.join(zipdirpath, filename),
                    )
