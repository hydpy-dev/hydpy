# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring
# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools

# ...from lland
from hydpy.models.wq import wq_control


class CrestHeightRegularisation(parametertools.Parameter):
    """Regularisation parameter related to the difference between the water depth and
    the crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.CrestHeightTolerance,)

    def update(self):
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following example in
        some detail:

        >>> from hydpy.models.wq import *
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> parameterstep()
        >>> crestheighttolerance(0.0)
        >>> derived.crestheightregularisation.update()
        >>> round_(smooth_logistic2(0.0, derived.crestheightregularisation))
        0.0
        >>> crestheighttolerance(0.0025)
        >>> derived.crestheightregularisation.update()
        >>> round_(smooth_logistic2(0.0025, derived.crestheightregularisation))
        0.00251
        """
        metapar = self.subpars.pars.control.crestheighttolerance.value
        self(smoothtools.calc_smoothpar_logistic2(1000.0 * metapar) / 1000.0)
