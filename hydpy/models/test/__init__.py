"""
The base model |test| is intended for implementing small application model that allow
for testing or demonstrating specific features of the HydPy framework.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from test
from hydpy.models.test.test_model import Model

tester = Tester()
cythonizer = Cythonizer()
