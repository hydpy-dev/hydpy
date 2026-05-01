"""
The Dummy model is a placeholder model. Its inputs are directly handed to the
output sequence and therefore can be used to (temporarily) delete a model
component while maintaining the network structure.
"""

from hydpy.exe.modelimports import *
from hydpy.models.dummy.dummy_model import Model

tester = Tester()
cythonizer = Cythonizer()
