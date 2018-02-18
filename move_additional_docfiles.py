# -*- coding: utf-8 -*-

import os
import shutil
from hydpy import docs
folder_out = docs.__path__[0]
folder_in = os.path.join(folder_out, 'html')
for filename in os.listdir(folder_in):
    path_in = os.path.join(folder_in, filename)
    path_out = os.path.join(folder_out, filename)
    shutil.move(path_in, path_out)
