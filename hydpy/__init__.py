"""
HydPy

An interactive framework for the developement and a application of
hydrological models.
"""

from hydpy.core.hydpytools import HydPy
from hydpy.core.timetools import Date
from hydpy.core.timetools import Period
from hydpy.core.timetools import Timegrid
from hydpy.core.timetools import Timegrids
from hydpy.core.filetools import MainManager
from hydpy.core.filetools import NetworkManager
from hydpy.core.filetools import ControlManager
from hydpy.core.filetools import SequenceManager
from hydpy.core.filetools import ConditionManager
from hydpy.core.devicetools import Node
from hydpy.core.devicetools import Nodes
from hydpy.core.devicetools import Element
from hydpy.core.devicetools import Elements
from hydpy.core.selectiontools import Selection
from hydpy.core.selectiontools import Selections
from hydpy.core.objecttools import HydPyDeprecationWarning

from hydpy import pub
from hydpy.core import optiontools as __optiontools
from hydpy.core import indextools as __indextools
from hydpy.cythons import configutils as __configutils
pub.options = __optiontools.Options()
pub.indexer = __indextools.Indexer()
pub.config = __configutils.Config()

import sys
import warnings


def customwarn(message, category, filename, lineno, file=None, line=None):
    sys.stdout.write(warnings.formatwarning(
                                    message, category, filename, lineno))
warnings.showwarning = customwarn
warnings.filterwarnings('always', category=HydPyDeprecationWarning)
warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')


__all__ = ['HydPy', 'pub',
           'Date', 'Period', 'Timegrid', 'Timegrids',
           'MainManager', 'NetworkManager', 'ControlManager',
           'SequenceManager', 'ConditionManager',
           'Node', 'Nodes', 'Element', 'Elements', 'Selection', 'Selections']
