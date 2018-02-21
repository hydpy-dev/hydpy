"""
HydPy

An interactive framework for the developement and a application of
hydrological models.
"""
# import...
# ...from standard library
import importlib
import pkgutil
import sys
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy import auxs
from hydpy import core
from hydpy import cythons
from hydpy import models
from hydpy.cythons.autogen import annutils
from hydpy.cythons.autogen import pointerutils
from hydpy.cythons.autogen import smoothutils
from hydpy.core import dummytools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.cythons import configutils
from hydpy.core.autodoctools import Substituter
from hydpy.core.auxfiletools import Auxfiler
from hydpy.core.devicetools import Node
from hydpy.core.devicetools import Nodes
from hydpy.core.devicetools import Element
from hydpy.core.devicetools import Elements
from hydpy.core.filetools import MainManager
from hydpy.core.filetools import NetworkManager
from hydpy.core.filetools import ControlManager
from hydpy.core.filetools import SequenceManager
from hydpy.core.filetools import ConditionManager
from hydpy.core.hydpytools import HydPy
from hydpy.core.objecttools import HydPyDeprecationWarning
from hydpy.core.selectiontools import Selection
from hydpy.core.selectiontools import Selections
from hydpy.core.timetools import Date
from hydpy.core.timetools import Period
from hydpy.core.timetools import Timegrid
from hydpy.core.timetools import Timegrids


pub.options = optiontools.Options()
pub.indexer = indextools.Indexer()
pub.config = configutils.Config()
dummies = dummytools.Dummies()   # pylint: disable=invalid-name


def customwarn(message, category, filename, lineno, file=None, line=None):
    """Redirect warnings to `stdout`."""
    sys.stdout.write(warnings.formatwarning(
        message, category, filename, lineno))


warnings.showwarning = customwarn
warnings.filterwarnings('always', category=HydPyDeprecationWarning)
warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

# Numpy introduced new string representations in version 1.14 affecting
# our doctests.  Hence, the old style is selected for now:
try:
    # pylint: disable=unexpected-keyword-arg
    numpy.set_printoptions(legacy='1.13')
except TypeError:
    pass

if not getattr(sys, 'frozen', False):
    # Don't do this when HydPy has been freezed with PyInstaller.
    substituter = Substituter()
    substituter.substitutions['|idx_sim|'] = \
        ':attr:`~hydpy.core.modeltools.Model.idx_sim`'
    for subpackage in (auxs, core, cythons):
        for loader, name, is_pkg in pkgutil.walk_packages(subpackage.__path__):
            full_name = subpackage.__name__ + '.' + name
            substituter.add_everything(importlib.import_module(full_name))
    substituter.add_modules(models)
    for cymodule in (annutils, smoothutils, pointerutils):
        substituter.add_everything(cymodule, cython=True)
    substituter.apply_on_members()


__all__ = ['HydPy', 'pub',
           'Auxfiler',
           'Date', 'Period', 'Timegrid', 'Timegrids',
           'MainManager', 'NetworkManager', 'ControlManager',
           'SequenceManager', 'ConditionManager',
           'Node', 'Nodes', 'Element', 'Elements', 'Selection', 'Selections',
           'HydPyDeprecationWarning']
