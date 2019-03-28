# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import parametertools
# ...from whmod
from hydpy.models.whmod.whmod_constants import *


class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

    def update(self):
        """Reference the actual |Indexer.monthofyear| array of the
        |Indexer| object stored in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> derived.moy.update()
        >>> derived.moy
        moy(1, 1, 1, 2, 2)
        """
        self.setreference(pub.indexer.monthofyear)


class RelArea(parametertools.Parameter):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)

    def update(self):
        """
        >>> from hydpy import pub
        >>> pub.options.usecython = False

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmb_cells(3)
        >>> area(100.0)
        >>> f_area(20.0, 30.0, 50.0)
        >>> derived.relarea.update()
        >>> derived.relarea
        relarea(0.2, 0.3, 0.5)
        """
        control = self.subpars.pars.control
        self(control.f_area/control.area)


class Wurzeltiefe(parametertools.Parameter):
    """[m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """
        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmb_cells(3)
        >>> flurab(1.0)
        >>> maxwurzeltiefe(0.5, 1.0, 1.5)
        >>> derived.wurzeltiefe.update()
        >>> derived.wurzeltiefe
        wurzeltiefe(0.5, 1.0, 1.0)
        """
        control = self.subpars.pars.control
        self(numpy.clip(control.maxwurzeltiefe, None, control.flurab))


class nFKwe(parametertools.Parameter):
    """[mm]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """
        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmb_cells(5)
        >>> nfk100_mittel(200.0)
        >>> derived.wurzeltiefe(0.0, 0.2, 0.3, 0.4, 1.0)
        >>> derived.nfkwe.update()
        >>> derived.nfkwe
        nfkwe(60.0, 60.0, 60.0, 80.0, 200.0)
        """
        nfk100_mittel = self.subpars.pars.control.nfk100_mittel
        wurzeltiefe = self.subpars.wurzeltiefe
        self(nfk100_mittel * numpy.clip(wurzeltiefe, 0.3, None))


class Beta(parametertools.Parameter):
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """
        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmb_cells(26)
        >>> nutz_nr(GRAS)
        >>> derived.nfkwe(range(0, 260, 10))
        >>> derived.beta.update()
        >>> from hydpy import print_values
        >>> for values in zip(derived.nfkwe, derived.beta):
        ...     print_values(values)
        0.0, 1.0
        10.0, 1.000001
        20.0, 1.000058
        30.0, 1.000806
        40.0, 1.005228
        50.0, 1.022297
        60.0, 1.072933
        70.0, 1.198647
        80.0, 1.473183
        90.0, 1.915863
        100.0, 2.680365
        110.0, 3.559094
        120.0, 4.408956
        130.0, 5.164394
        140.0, 5.810723
        150.0, 6.362129
        160.0, 6.844528
        170.0, 7.283464
        180.0, 7.697228
        190.0, 8.095355
        200.0, 8.482689
        210.0, 7.0
        220.0, 7.0
        230.0, 7.0
        240.0, 7.0
        250.0, 7.0

        >>> nmb_cells(2)
        >>> nutz_nr(WASSER, VERSIEGELT)
        >>> derived.nfkwe(100.0)
        >>> derived.beta.update()
        >>> derived.beta
        beta(0.0)
        """
        nutz_nr = self.subpars.pars.control.nutz_nr
        nfkwe = self.subpars.nfkwe
        self(0.0)
        idxs1 = (nutz_nr.values != WASSER) * (nutz_nr.values != VERSIEGELT)
        idxs2 = idxs1 * (nfkwe.values > 200.)
        self.values[idxs2] = 7.
        idxs3 = idxs1 * (nfkwe.values <= 200.)
        self.values[idxs3] = 1.0 + 6.0*(nfkwe[idxs3]/118.25)**6.5
        idxs4 = idxs3 * (nfkwe.values >= 90.)
        sel = nfkwe[idxs4]
        self.values[idxs4] -= (((((5.14499665e-9 * sel
                                   - 2.54885486e-6) * sel
                                  + 5.90669258e-4) * sel
                                 - 7.26381809e-2) * sel
                                + 4.47631543) * sel
                               - 108.1457328)


class DerivedParameters(parametertools.SubParameters):
    CLASSES = (MOY,
               RelArea,
               Wurzeltiefe,
               nFKwe,
               Beta)
