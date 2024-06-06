# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.ga import ga_control


class Moisture(sequencetools.StateSequence):
    """The relative soil moisture of each bin (within the wetting front) [-].

    The current moisture of inactive bins usually equals the "initial moisture" of the
    first "filled" bin.  However, withdrawal (e.g. due to evaporation) can result in
    moisture values of inactive bins larger than the initial moisture.

    ToDo: What is the reason behind this behaviour? Can we change it?
    """

    NDIM, NUMERIC, SPAN = 2, False, (0.0, 1.0)

    CONTROLPARAMETERS = (ga_control.ResidualMoisture, ga_control.SaturationMoisture)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim the relative moisture following
        :math:`ResidualMoisture \leq Moisture \leq SaturationMoisture`.

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> nmbbins(5)
        >>> residualmoisture(0.2, 0.4)
        >>> saturationmoisture(0.8, 0.6)
        >>> states.moisture([[0.0, 0.0],
        ...                  [0.2, 0.4],
        ...                  [0.5, 0.5],
        ...                  [0.8, 0.6],
        ...                  [1.0, 1.0]])
        >>> states.moisture
        moisture([[0.2, 0.4],
                  [0.2, 0.4],
                  [0.5, 0.5],
                  [0.8, 0.6],
                  [0.8, 0.6]])
        """
        control = self.subseqs.seqs.model.parameters.control
        if lower is None:
            lower = control.residualmoisture
        if upper is None:
            upper = control.saturationmoisture
        return super().trim(lower, upper)


class FrontDepth(sequencetools.StateSequence):
    """The depth of the wetting front in each bin [-].

    The current wetting front depth of inactive bins is zero.  But zero front depth
    does not necessarily mean a bin is inactive.
    """

    NDIM, NUMERIC, SPAN = 2, False, (0.0, None)

    CONTROLPARAMETERS = (ga_control.SoilDepth,)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim the wetting front depth following
        :math:`0 \leq FrontDepth \leq SoilDepth`.

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> nmbbins(5)
        >>> soildepth(100.0, 500.0)
        >>> states.frontdepth([[-10.0, -10.0],
        ...                    [0.0, 0.0],
        ...                    [50.0, 250.0],
        ...                    [100.0, 500.0],
        ...                    [110.0, 510.0]])
        >>> states.frontdepth
        frontdepth([[0.0, 0.0],
                    [0.0, 0.0],
                    [50.0, 250.0],
                    [100.0, 500.0],
                    [100.0, 500.0]])
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.soildepth
        return super().trim(lower, upper)
