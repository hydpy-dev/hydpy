
from distutils.version import StrictVersion
import importlib
import json
import os
import packaging.version
import shutil
import sys
import urllib


with open('make_hydpy_installer.cfgt') as file_:
    lines = file_.readlines()
for idx, line in enumerate(lines):
    if 'cp[auto]' in line:
        lines[idx] = line.replace(
            '[auto]', "".join(str(v) for v in sys.version_info[:2]))
for idx, line in enumerate(lines):
    if 'version = [auto]' in line:
        lines[idx] = line.replace(
            '[auto]', ".".join(str(v) for v in sys.version_info[:3]))
for idx, line in enumerate(lines):
    if '==[auto]' in line:
        name = line.split()[-1].split('==')[0]
        if name == 'python-dateutil':
            version = importlib.import_module('dateutil').__version__
        elif name == 'PyYAML':
            version = importlib.import_module('yaml').__version__
        elif name == 'attrs':
            version = importlib.import_module('attr').__version__
        elif name == 'Pillow':
            version = importlib.import_module('PIL').__version__
        elif name == 'tornado':
            version_info = importlib.import_module('tornado').version_info
            version = '.'.join(str(v) for v in version_info[:3])
        else:
            try:
                version = '.'.join(
                    str(number) for number in
                    packaging.version.parse(
                        importlib.import_module(name).__version__
                    ).release
                )
            except AttributeError:
                data = json.load(
                    urllib.request.urlopen(
                        urllib.request.Request(
                            f'https://pypi.python.org/pypi/{name}/json'
                        )
                    )
                )
                versions = (
                    packaging.version.parse(v) for v in data["releases"]
                )
                version = str(max(v for v in versions if not v.is_prerelease))
        lines[idx] = line.replace('[auto]', version)
with open('make_hydpy_installer.cfg', 'w') as file_:
    file_.writelines(lines)


wheeldir = 'extra_wheel_sources'
if os.path.exists(wheeldir):
    shutil.rmtree(wheeldir)
os.makedirs(wheeldir)
os.system(f'{sys.executable} -m pip wheel retrying --wheel-dir={wheeldir}')

for folderpath in sys.path:
    if os.path.isdir(folderpath):
        for filename in os.listdir(folderpath):
            if filename in ('tcl86t.dll', 'tk86t.dll', 'tcl'):
                source = os.path.join(folderpath, filename)
                print(f'copy {source} to {filename}')
                if filename == 'tcl':
                    shutil.copytree(source, 'lib')
                else:
                    shutil.copy(source, filename)
