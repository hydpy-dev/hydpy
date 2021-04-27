# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
import itertools
from typing import *
from typing_extensions import Literal

# ...from HydPy
from hydpy.auxs import anntools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class Laen(parametertools.Parameter):
    """Flusslänge (channel length) [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class Gef(parametertools.Parameter):
    """Sohlgefälle (channel slope) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class GTS(parametertools.Parameter):
    """Anzahl Gewässerteilstrecken (number of channel subsections) [-].

    Calling the parameter |GTS| prepares the shape of all 1-dimensional
    sequences for which each entry corresponds to an individual channel
    subsection:

    >>> from hydpy.models.lstream import *
    >>> parameterstep()
    >>> gts(3)
    >>> states.h
    h(nan, nan, nan)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        seqs = self.subpars.pars.model.sequences
        for seq in itertools.chain(seqs.fluxes, seqs.states, seqs.aides):
            if seq.NDIM:
                seq.shape = self.value


class HM(parametertools.Parameter):
    """Höhe Hauptgerinne (height of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BM(parametertools.Parameter):
    """Sohlbreite Hauptgerinne (bed width of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BNM(parametertools.Parameter):
    """Böschungsneigung Hauptgerinne (slope of both main channel embankments)
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BV(parametertools.LeftRightParameter):
    """Sohlbreite Vorländer (bed widths of both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BBV(parametertools.LeftRightParameter):
    """Breite Vorlandböschungen (width of both foreland embankments) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BNV(parametertools.LeftRightParameter):
    """Böschungsneigung Vorländer (slope of both foreland embankments) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BNVR(parametertools.LeftRightParameter):
    """Böschungsneigung Vorlandränder (slope of both outer embankments) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class SKM(parametertools.Parameter):
    """Rauigkeitsbeiwert Hauptgerinne (roughness coefficient of the main
    channel) [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class SKV(parametertools.LeftRightParameter):
    """Rauigkeitsbeiwert Vorländer (roughness coefficient of both
    forelands) [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class EKM(parametertools.Parameter):
    """Kalibrierfaktor Hauptgerinne (calibration factor for the main
    channel) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class EKV(parametertools.LeftRightParameter):
    """Kalibrierfaktor Vorländer (calibration factor for both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class HR(parametertools.Parameter):
    """Allgemeiner Glättungsparameter für den Wasserstand (general smoothing
    parameter for the water stage) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class VG2FG(anntools.ANN):
    """Künstliches Neuronales Netz zur Berechnung der Fließgeschwindigkeit in
    Abhängigkeit zur aktuellen Wasserspeicherung einer Gewässerteilstrecke (artificial
    neural network describing the relationship between the flow velocity and the
    water storage of individual channel subsections) [m/s].

    You can configure the velocity-storage relationship with all functionalities
    provided by (and explained in the documentation of) base class |anntools.ANN|:

    >>> from hydpy.models.lstream import *
    >>> parameterstep()
    >>> vg2fg(weights_input=-1.0, weights_output=0.4,
    ...       intercepts_hidden=0.0, intercepts_output=0.2)
    >>> vg2fg
    vg2fg(
        weights_input=[[-1.0]],
        weights_output=[[0.4]],
        intercepts_hidden=[[0.0]],
        intercepts_output=[0.2],
    )

    >>> from hydpy import round_
    >>> vg2fg.inputs[0] = 0.0
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    0.4
    >>> vg2fg.inputs[0] = 1.0
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    0.307577
    >>> vg2fg.inputs[0] = inf
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    0.2

    If you prefer a constant velocity, you can set it directly via the keyword
    `velocity` (its unit must be m/s):

    >>> vg2fg(velocity=1.0)

    >>> vg2fg
    vg2fg(velocity=1.0)

    >>> vg2fg.inputs[0] = 0.0
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    1.0
    >>> vg2fg.inputs[0] = 1.0
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    1.0

    Alternatively, the keyword `timedelay` allows defining the flow velocity via the
    number of hours it takes for a flood wave to travel through the whole channel:

    >>> laen(100.0)
    >>> vg2fg(timedelay=27.77778)
    >>> vg2fg
    vg2fg(timedelay=27.77778)

    >>> vg2fg.inputs[0] = 0.0
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    1.0

    For a ten times shorter channel, the same time delay implies a ten times slower
    flow velocity:

    >>> laen(10.0)
    >>> vg2fg(timedelay=27.77778)
    >>> vg2fg
    vg2fg(timedelay=27.77778)

    >>> vg2fg.inputs[0] = 0.0
    >>> vg2fg.calculate_values()
    >>> round_(vg2fg.outputs[0])
    0.1
    """

    XLABEL = "VG [million m³]"
    YLABEL = "FG [m/s]"

    _simple_ann = anntools.ann(
        weights_input=((0.0,),),
        weights_output=((0.0,),),
        intercepts_hidden=((0.0,),),
        intercepts_output=(0.0,),
    )
    _keyword: Optional[Literal["velocity", "timedelay"]] = None

    @overload
    def __call__(self, *, velocity: float) -> None:
        ...

    @overload
    def __call__(self, *, timedelay: float) -> None:
        ...

    @overload
    def __call__(
        self,
        *,
        nmb_inputs: int = 1,
        nmb_neurons: Tuple[int, ...] = (1,),
        nmb_outputs: int = 1,
        weights_input: Optional[MatrixInput[float]] = None,
        weights_output: Optional[MatrixInput[float]] = None,
        weights_hidden=None,
        intercepts_hidden: Optional[MatrixInput[float]] = None,
        intercepts_output: Optional[VectorInput[float]] = None,
        activation: Optional[MatrixInput[int]] = None,
    ) -> None:
        ...

    def __call__(self, **kwargs) -> None:
        self._keyword = None
        velocity = None
        if "velocity" in kwargs:
            self._keyword = "velocity"
            velocity = float(kwargs["velocity"])
        elif "timedelay" in kwargs:
            self._keyword = "timedelay"
            timedelay = float(kwargs["timedelay"])
            velocity = self._convert_velocity_timedelay(timedelay)
        if velocity is not None:
            kwargs = dict(
                weights_input=0.0,
                weights_output=0.0,
                intercepts_hidden=0.0,
                intercepts_output=velocity,
            )
        super().__call__(**kwargs)

    def _convert_velocity_timedelay(self, value: float) -> float:
        return (self.subpars.laen * 1000.0) / (value * 60.0 * 60.0)

    def __repr__(self) -> str:
        if self.shape_outputs == (1,):
            self._simple_ann.intercepts_output = self.intercepts_output
            if (self._keyword is not None) and (self == self._simple_ann):
                value = self.intercepts_output[0]
                if self._keyword == "velocity":
                    return f"{self.name}(velocity={objecttools.repr_(value)})"
                if self._keyword == "timedelay":
                    value = self._convert_velocity_timedelay(value)
                    return f"{self.name}(timedelay={objecttools.repr_(value)})"
                assert False
        return super().__repr__()


class EK(parametertools.Parameter):
    """Kalibrierfaktor (calibration factor) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
