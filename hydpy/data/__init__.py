# -*- coding: utf-8 -*-

# import...
# ...from standard library
import os

def get_path(*names):
    return os.path.join(__path__[0], *names)
