"""
The |conv.DOCNAME.complete| model family allows connecting different kinds of models
providing output and requiring input that does not fit immediately.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.conv.conv_model import Model

tester = Tester()
cythonizer = Cythonizer()
