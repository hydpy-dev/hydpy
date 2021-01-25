# -*- coding: utf-8 -*-
"""The L-Stream model provides features for implementing storage based
routing methods similar to those implemented by the water balance model
`LARSIM`_.

.. _`LARSIM`: http://www.larsim.de/en/the-model/

Conceptionally, application models derived from HydPy-L-Stream can
be very similar to those of LARSIM.  However, while LARSIM makes use of
approximate "ad hoc" solutions of the underlying ordinary differential
equations, L-Stream defines the differential equations in their original
form and leaves their solution to numerical integration algorithms.
On the upside, this allows for more flexibility (regarding the coupling
and extension of methodologies),  accuracy (the user can define the
aimed accuracy), and correctness (one can easily avoid problems resulting
from  approximate solutions like the water balance errors of the Williams
implementation of LARSIM).  On the downside, numerical convergence might
require (sometimes much) more time.

To, at least partly, solve the computation time issue, we implement all
differential equations in a "smooth" form.  By applying regularisation
functions like the ones supplied by module |smoothtools|, we remove all
discontinuities from the original formulations, which speeds up numerical
convergence a lot.  However, it is up to the user to define a reasonable
degree of "smoothness".  Please read the related documentation of module
|smoothtools| and module |modeltools| for further information.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.auxs.anntools import ann

# ...from lstream
from hydpy.models.lstream.lstream_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
