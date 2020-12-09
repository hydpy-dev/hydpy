# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
import numpy

try:
    python = sys.executable

    sitepackagepath = os.path.split(numpy.__path__[0])[0]
    for name in os.listdir(sitepackagepath):
        if "hydpy" in name.lower():
            path = os.path.join(sitepackagepath, name)
            try:
                os.remove(path)
            except BaseException:
                shutil.rmtree(path)
    scriptspath = os.path.join(
        os.path.split(os.path.split(sitepackagepath)[0])[0], "Scripts"
    )
    os.remove(
        os.path.join(
            os.path.split(os.path.split(sitepackagepath)[0])[0], "Scripts", "hyd.py"
        )
    )

    pyversion = f"cp{sys.version_info.major}{sys.version_info.minor}"

    if pyversion == "cp36":
        subprocess.run([python, "setup.py", "sdist"])
    subprocess.run([python, "setup.py", "bdist_wheel"])

    oldname = [fn for fn in os.listdir("dist") if fn.endswith("whl")][0]
    parts = oldname.split("-")
    newname = "-".join(parts[:2] + [pyversion, "none", f"win_amd64.whl"])
    os.chdir("dist")
    os.rename(oldname, newname)
    subprocess.run([python, "-m", "pip", "install", newname])
    os.chdir("..")
except BaseException as exc:
    print(exc)
