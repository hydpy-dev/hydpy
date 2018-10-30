# -*- coding: utf-8 -*-

import os
import numpy
import shutil
import subprocess
import sys

try:
    sitepackagepath = os.path.split(numpy.__path__[0])[0]
    for name in os.listdir(sitepackagepath):
        if name.lower().startswith('hydpy'):
            path = os.path.join(sitepackagepath, name)
            try:
                os.remove(path)
            except BaseException:
                shutil.rmtree(path)

    pyversion = f'cp{sys.version_info.major}{sys.version_info.minor}'

    if pyversion == 'cp36':
        subprocess.run(['python', 'setup.py', 'sdist'])
    subprocess.run(['python', 'setup.py', 'bdist_wheel'])

    oldname = [fn for fn in os.listdir('dist') if fn.endswith('whl')][0]
    parts = oldname.split('-')
    newname = '-'.join(parts[:2] + [pyversion, 'none', f'win_amd64.whl'])
    os.rename(f'dist/{oldname}', f'dist/{newname}')

    subprocess.run(['pip', 'install', f'dist/{newname}'])
except BaseException as exc:
    print(exc)
