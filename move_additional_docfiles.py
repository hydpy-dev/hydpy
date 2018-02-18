# -*- coding: utf-8 -*-

import os
import shutil
import sys

# Priorise site-packages (on Debian-based Linux distributions as Ubuntu
# also dist-packages) in the import order to make sure, the following
# imports refer to the newly build hydpy package on the respective computer.
paths = [path for path in sys.path if path.endswith('-packages')]
for path in paths:
    sys.path.insert(0, path)

from hydpy import docs
folder_out = docs.__path__[0]
folder_in = os.path.join(folder_out, 'html')
for filename in os.listdir(folder_in):
    if filename.endswith('.html'):
        path_in = os.path.join(folder_in, filename)
        path_out = os.path.join(folder_out, filename)
        shutil.move(path_in, path_out)
