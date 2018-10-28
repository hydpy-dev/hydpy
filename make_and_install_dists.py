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

    for dist in ['sdist', 'bdist_wheel', 'bdist_wininst', 'bdist_msi']:
        subprocess.run(['python', 'setup.py', dist])

    pyversion = f'cp{sys.version_info.major}{sys.version_info.minor}'

    for ext in ['exe', 'whl']:
        oldname = [fn for fn in os.listdir('dist') if fn.endswith(ext)][0]
        parts = oldname.split('-')
        newname = '-'.join(parts[:2] + [pyversion, 'none', f'win_amd64.{ext}'])
        os.rename(f'dist/{oldname}', f'dist/{newname}')

    subprocess.run(['pip', 'install', f'dist/{newname}'])
except BaseException as exc:
    print(exc)
