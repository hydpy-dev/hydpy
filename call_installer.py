import os
import sys

folderpath = os.path.join("build", "nsis")
for filename in os.listdir(folderpath):
    if filename.endswith(".exe"):
        break
sys.exit(os.system(f"{os.path.join(folderpath, filename)} /S"))
