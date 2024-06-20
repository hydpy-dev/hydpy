# -*- coding: utf-8 -*-
"""The |kinw.DOCNAME.long| model family provides features for implementing storage
based routing methods
similar to those implemented by the water balance model `LARSIM`_.

.. _`LARSIM`: http://www.larsim.de/en/the-model/

Conceptionally, application models of the |kinw.DOCNAME.long| model family can be very
similar to those of LARSIM.  However, while LARSIM uses approximate "ad hoc" solutions of the
underlying ordinary differential equations, |kinw.DOCNAME.long| defines the differential equations
in their original form and leaves their solution to numerical integration algorithms.
On the upside, this allows for more flexibility (regarding the coupling and extension
of methodologies),  accuracy (the user can define the aimed accuracy), and correctness
(one can easily avoid problems resulting from  approximate solutions like the water
balance errors of the Williams implementation of LARSIM).  On the downside, numerical
convergence might require (sometimes much) more time.

To partly solve the computation time issue, we implement all differential equations in
a "smooth" form.  By applying the regularisation functions supplied by module
|smoothtools|, we remove all discontinuities from the original formulations, which
speeds up numerical convergence.  However, it is up to the user to define a reasonable
degree of "smoothness".  Please read the related documentation of module |smoothtools|
and module |modeltools| for further information.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.auxs.anntools import ANN
from hydpy.auxs.ppolytools import Poly, PPoly

# ...from kinw
from hydpy.models.kinw.kinw_model import Model

tester = Tester()
cythonizer = Cythonizer()
