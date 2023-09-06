"""Create `make_hydpy_installer.cfg` based on `make_hydpy_installer.cfgt` and copy
additional sources into the directories `extra_wheel_sources` and
`extra_python_sources`."""

import os
import shutil
import sys

import lastversion

with open("make_hydpy_installer.cfgt", encoding="utf-8") as file_:
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

with open("make_hydpy_installer.cfg", "w", encoding="utf-8") as file_:
    file_.writelines(lines)


wheeldir = "extra_wheel_sources"
shutil.rmtree(wheeldir, ignore_errors=True)
os.makedirs(wheeldir)
os.system(f"{sys.executable} -m pip wheel retrying --wheel-dir={wheeldir}")

extra = "extra_python_sources"
cwd = os.path.abspath(os.getcwd())
shutil.rmtree(extra, ignore_errors=True)
os.makedirs(extra)
for dirpath in sys.path:
    if os.path.isdir(dirpath) and (os.path.abspath(dirpath) != cwd):
        for filename in ("tcl86t.dll", "tk86t.dll"):
            if os.path.exists(sourcefilepath := os.path.join(dirpath, filename)):
                targetfilepath = os.path.join(cwd, extra, filename)
                print(f"copy {sourcefilepath} to {targetfilepath}")
                shutil.copy(sourcefilepath, targetfilepath)
        for dirname in ("tcl", "include", "libs"):
            if os.path.exists(sourcedirpath := os.path.join(dirpath, dirname)):
                targetdirpath = os.path.join(
                    cwd, extra, "lib" if dirname == "tcl" else dirname
                )
                print(f"copy {sourcedirpath} to {targetdirpath}")
                shutil.copytree(sourcedirpath, targetdirpath)
