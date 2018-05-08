# -*- coding: utf-8 -*-
"""
Test if the default backend of matplotlib required for pyplot is available.

Required for Travis CI, where it is not available.

If the backend is available, the exit code of this script is 0, otherwise 1.

Actually, the only test is calling pyplots `plot` command.  If this script
fails due to another reason than a missing backend, one will be informed by
another failure in the testing routines defined somewhere else.
"""

import sys
from hydpy import pyplot
try:
    pyplot.plot()
except BaseException:
    sys.exit(1)
else:
    sys.exit(0)
