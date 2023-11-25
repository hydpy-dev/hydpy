"""Perform all available consistency checks."""
# import...
# ...from standard library
import os
import sys
from typing import List

# ...from HydPy
from hydpy import models
from hydpy.core.testtools import perform_consistencychecks

print("Perform all available consistency checks:\n")
dirpath: str = models.__path__[0]
applicationmodels = sorted(
    fn.split(".")[0]
    for fn in os.listdir(dirpath)
    if (fn != "__init__.py") and os.path.isfile(os.path.join(dirpath, fn))
)
results: List[str] = []
for applicationmodel in applicationmodels:
    subresult = perform_consistencychecks(applicationmodel=applicationmodel, indent=4)
    if subresult:
        results.append(
            f"Potential consistency problems for "
            f"application model {applicationmodel}"
        )
        results.append(f"{subresult}\n")
if results:
    print("\n".join(results))
    sys.exit(1)
print("   nothing to report\n")
sys.exit(0)
