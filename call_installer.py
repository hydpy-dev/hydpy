import os
import sys

folderpath = os.path.join("build", "nsis")
for filename in os.listdir(folderpath):
    if filename.startswith("HydPy") and filename.endswith(".exe"):
        command_ = f"{os.path.join(folderpath, filename)} /S"
        break
else:
    raise RuntimeError("Did not find the HydPy installer.")
print("Execute the HydPy installer with:", command_)
returncode = os.system(command_)

# useful for debugging
# print("Found HydPy executables:", command_)
# for dirpath, _, filenames in os.walk(os.path.abspath(os.sep)):
#     for filename in filenames:
#         fn = filename.lower()
#         if (("hydpy" in fn or "hyd.py" in fn)) and (".exe" in fn):
#             print("", os.path.abspath(os.path.join(dirpath, filename)))

sys.exit(returncode)
