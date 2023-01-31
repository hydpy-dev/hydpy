import os
import shutil
import sys

import lastversion


with open("make_hydpy_installer.cfgt") as file_:
    lines = file_.readlines()

for idx, line in enumerate(lines):
    if "cp[auto]" in line:
        lines[idx] = line.replace(
            "[auto]", "".join(str(v) for v in sys.version_info[:2])
        )

for idx, line in enumerate(lines):
    if "version = [auto]" in line:
        lines[idx] = line.replace(
            "[auto]", ".".join(str(v) for v in sys.version_info[:3])
        )

for idx, line in enumerate(lines):
    if "==[auto]" in line:
        name = line.split()[-1].split("==")[0]
        version = lastversion.latest(name, at="pip")
        lines[idx] = line.replace("[auto]", str(version))

with open("make_hydpy_installer.cfg", "w") as file_:
    file_.writelines(lines)


wheeldir = "extra_wheel_sources"
if os.path.exists(wheeldir):
    shutil.rmtree(wheeldir)
os.makedirs(wheeldir)
os.system(f"{sys.executable} -m pip wheel retrying --wheel-dir={wheeldir}")

this_path = os.path.abspath(os.getcwd())
for folderpath in sys.path:
    if os.path.isdir(folderpath) and (os.path.abspath(folderpath) != this_path):
        for filename in os.listdir(folderpath):
            if filename in ("tcl86t.dll", "tk86t.dll", "tcl"):
                source = os.path.join(folderpath, filename)
                print(f"copy {source} to {filename}")
                if filename == "tcl":
                    shutil.copytree(source, "lib")
                else:
                    shutil.copy(source, filename)
