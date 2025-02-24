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
from hydpy.models.whmod import whmod_parameters
from hydpy.models.whmod import whmod_control


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class RelArea(whmod_parameters.NutzCompleteParameter):
    """[-]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (whmod_control.ZoneArea, whmod_control.Area)

    def update(self):
        """


        >>> from hydpy import pub
        >>> pub.options.usecython = False

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(GRAS, WASSER, VERSIEGELT)
        >>> area(100.0)
        >>> zonearea(20.0, 30.0, 50.0)
        >>> derived.relarea.update()
        >>> derived.relarea
        relarea(gras=0.2, versiegelt=0.5, wasser=0.3)
        """
        control = self.subpars.pars.control
        self(control.zonearea / control.area)


class Wurzeltiefe(whmod_parameters.NutzBodenParameter):
    """[m]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.RootingDepth, whmod_control.GroundwaterDepth)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> landtype(GRAS, LAUBWALD, NADELWALD, WASSER, VERSIEGELT)
        >>> groundwaterdepth(1.0)
        >>> rootingdepth(0.5, 1.0, 1.5, 2.0, 2.0)
        >>> derived.wurzeltiefe.update()
        >>> derived.wurzeltiefe
        wurzeltiefe(gras=0.5, laubwald=1.0, nadelwald=1.0)
        """
        control = self.subpars.pars.control
        self(numpy.clip(control.rootingdepth, None, control.groundwaterdepth.values))


class nFKwe(whmod_parameters.NutzBodenParameter):
    """[mm]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.AvailableFieldCapacity,)
    DERIVEDPARAMETERS = (Wurzeltiefe,)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(7)
        >>> landtype(GRAS, MAIS, LAUBWALD, NADELWALD, SOMMERWEIZEN, WASSER, VERSIEGELT)
        >>> availablefieldcapacity(200.0)
        >>> derived.wurzeltiefe(0.0, 0.2, 0.3, 0.4, 1.0, 1.0, 1.0)
        >>> derived.nfkwe.update()
        >>> derived.nfkwe
        nfkwe(gras=60.0, laubwald=60.0, mais=60.0, nadelwald=80.0,
              sommerweizen=200.0)
        """
        availablefieldcapacity = self.subpars.pars.control.availablefieldcapacity
        wurzeltiefe = self.subpars.wurzeltiefe
        self(availablefieldcapacity * numpy.clip(wurzeltiefe, 0.3, None))


class Beta(whmod_parameters.NutzBodenParameter):
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.LandType,)
    DERIVEDPARAMETERS = (nFKwe,)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(26)
        >>> landtype(GRAS)
        >>> derived.nfkwe(range(0, 260, 10))
        >>> derived.beta.update()
        >>> from hydpy import print_vector
        >>> for values in zip(derived.nfkwe, derived.beta):
        ...     print_vector(values)
        0.0, 1.0
        10.0, 1.000001
        20.0, 1.000058
        30.0, 1.000806
        40.0, 1.005223
        50.0, 1.022215
        60.0, 1.072058
        70.0, 1.192281
        80.0, 1.438593
        90.0, 1.869943
        100.0, 2.510161
        110.0, 3.307578
        120.0, 4.143126
        130.0, 4.895532
        140.0, 5.498714
        150.0, 5.945944
        160.0, 6.262712
        170.0, 6.48211
        180.0, 6.632992
        190.0, 6.736978
        200.0, 6.809179
        210.0, 6.859826
        220.0, 6.895768
        230.0, 6.921582
        240.0, 6.940345
        250.0, 6.954142

        >>> nmbzones(2)
        >>> landtype(WASSER, VERSIEGELT)
        >>> derived.nfkwe(100.0)
        >>> derived.beta.update()
        >>> derived.beta
        beta(nan)
        """
        landtype = self.subpars.pars.control.landtype
        nfkwe = self.subpars.nfkwe
        self(0.0)
        idxs1 = (landtype.values != WASSER) * (landtype.values != VERSIEGELT)
        idxs2 = nfkwe.values <= 0.0
        idxs3 = idxs1 * idxs2
        self.values[idxs3] = 1.0
        idxs4 = idxs1 * ~idxs2
        self.values[idxs4] = 1.0 + 6.0 / (1 + (nfkwe[idxs4] / 118.25) ** -6.5)

    def update_old(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(26)
        >>> landtype(GRAS)
        >>> derived.nfkwe(range(0, 260, 10))
        >>> derived.beta.update_old()
        >>> from hydpy import print_vector
        >>> for values in zip(derived.nfkwe, derived.beta):
        ...     print_vector(values)
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

        >>> nmbzones(2)
        >>> landtype(WASSER, VERSIEGELT)
        >>> derived.nfkwe(100.0)
        >>> derived.beta.update_old()
        >>> derived.beta
        beta(nan)
        """
        landtype = self.subpars.pars.control.landtype
        nfkwe = self.subpars.nfkwe
        self(0.0)
        idxs1 = (landtype.values != WASSER) * (landtype.values != VERSIEGELT)
        idxs2 = idxs1 * (nfkwe.values > 200.0)
        self.values[idxs2] = 7.0
        idxs3 = idxs1 * (nfkwe.values <= 200.0)
        self.values[idxs3] = 1.0 + 6.0 * (nfkwe[idxs3] / 118.25) ** 6.5
        idxs4 = idxs3 * (nfkwe.values >= 90.0)
        subtrahend = 5.14499665e-9
        for constant in (
            -2.54885486e-6,
            5.90669258e-4,
            -7.26381809e-2,
            4.47631543,
            -108.1457328,
        ):
            subtrahend = subtrahend * nfkwe[idxs4] + constant
        self.values[idxs4] -= subtrahend
