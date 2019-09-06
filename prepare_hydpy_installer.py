
import importlib
import os
import shutil
import sys


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
            version = importlib.import_module(name).__version__
        lines[idx] = line.replace('[auto]', version)
with open('make_hydpy_installer.cfg', 'w') as file_:
    file_.writelines(lines)

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
