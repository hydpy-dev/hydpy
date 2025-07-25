# pylint: disable=missing-module-docstring

# import...
# ...from standard library
import itertools

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.auxs import anntools
from hydpy.auxs import interptools


class Laen(parametertools.Parameter):
    """Flusslänge (channel length) [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class Length(parametertools.Parameter):
    """Channel length [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class Gef(parametertools.Parameter):
    """Sohlgefälle (channel slope) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class GTS(parametertools.Parameter):
    """Anzahl Gewässerteilstrecken (number of channel subsections) [-].

    Calling the parameter |GTS| prepares the shape of all 1-dimensional
    sequences for which each entry corresponds to an individual channel
    subsection:

    >>> from hydpy.models.kinw import *
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


class NmbSegments(parametertools.Parameter):
    """Number of channel segments [-].

    |NmbSegments| prepares the shape of some 1-dimensional sequences automatically:

    >>> from hydpy.models.kinw import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> nmbsegments
    nmbsegments(2)
    >>> states.watervolume.shape
    (2,)
    >>> factors.waterdepth.shape
    (2,)
    >>> fluxes.internalflow.shape
    (1,)

    |NmbSegments| preserves existing values if the number of segments does not change:

    >>> states.watervolume = 1.0, 2.0
    >>> nmbsegments(2)
    >>> states.watervolume
    watervolume(1.0, 2.0)

    Setting its value to zero is allowed:

    >>> nmbsegments(0)
    >>> states.watervolume.shape
    (0,)
    >>> fluxes.internalflow.shape
    (0,)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs) -> None:

        super().__call__(*args, **kwargs)

        nmb = self.value
        model = self.subpars.pars.model
        model.nmb_segments = nmb
        seqs = model.sequences
        for subseqs in (seqs.factors, seqs.fluxes, seqs.states):
            for seq in subseqs:
                delta = getattr(seq, "__HYDPY__DELTA_SEGMENTS__", None)
                if delta is not None:
                    assert isinstance(delta, int)
                    old = exceptiontools.getattr_(seq, "shape", None)
                    new = (max(nmb + delta, 0),)
                    if old != new:
                        seq.shape = new


class HM(parametertools.Parameter):
    """Höhe Hauptgerinne (height of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BM(parametertools.Parameter):
    """Sohlbreite Hauptgerinne (bed width of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BNM(parametertools.Parameter):
    """Böschungsneigung Hauptgerinne (slope of both main channel embankments) [-]."""

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
    """Rauigkeitsbeiwert Hauptgerinne (roughness coefficient of the main channel)
    [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class SKV(parametertools.LeftRightParameter):
    """Rauigkeitsbeiwert Vorländer (roughness coefficient of both forelands)
    [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class EKM(parametertools.Parameter):
    """Kalibrierfaktor Hauptgerinne (calibration factor for the main channel) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class EKV(parametertools.LeftRightParameter):
    """Kalibrierfaktor Vorländer (calibration factor for both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class HR(parametertools.Parameter):
    """Allgemeiner Glättungsparameter für den Wasserstand (general smoothing parameter
    for the water stage) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class VG2FG(interptools.SimpleInterpolator):
    """Flexibler Interpolator zur Berechnung der Fließgeschwindigkeit in Abhängigkeit
    zur aktuellen Wasserspeicherung einer Gewässerteilstrecke (flexible interpolator
    describing the relationship between the flow velocity and the water storage of
    individual channel subsections) [m/s].

    You can configure the velocity-storage relationship with all functionalities
    provided by classes |ANN| and |PPoly|.  Here, we define a small neural network:

    >>> from hydpy.models.kinw import *
    >>> parameterstep()
    >>> vg2fg(ANN(weights_input=-1.0, weights_output=0.4,
    ...           intercepts_hidden=0.0, intercepts_output=0.2))
    >>> vg2fg
    vg2fg(
        ANN(
            weights_input=[[-1.0]],
            weights_output=[[0.4]],
            intercepts_hidden=[[0.0]],
            intercepts_output=[0.2],
        )
    )
    >>> vg2fg.print_table([0.0, 1.0, inf])
    x    y         dy/dx
    0.0  0.4       -0.1
    1.0  0.307577  -0.078645
    inf  0.2       0.0

    If you prefer a constant velocity, you can set it directly via the keyword
    `velocity` (its unit must be m/s):

    >>> vg2fg(velocity=1.0)
    >>> vg2fg
    vg2fg(velocity=1.0)
    >>> vg2fg.print_table([0.0, 1.0])
    x    y    dy/dx
    0.0  1.0  0.0
    1.0  1.0  0.0

    Alternatively, the keyword `timedelay` allows for defining the flow velocity via
    the number of hours it takes for a flood wave to travel through the whole channel:

    >>> laen(100.0)
    >>> vg2fg(timedelay=27.77778)
    >>> vg2fg
    vg2fg(timedelay=27.77778)

    >>> vg2fg.inputs[0] = 0.0
    >>> vg2fg.calculate_values()
    >>> vg2fg.print_table([0.0, 1.0])
    x    y    dy/dx
    0.0  1.0  0.0
    1.0  1.0  0.0

    The same time delay indicates a ten times slower flow velocity for a ten times
    shorter channel:

    >>> laen(10.0)
    >>> vg2fg(timedelay=27.77778)
    >>> vg2fg
    vg2fg(timedelay=27.77778)
    >>> vg2fg.print_table([0.0, 1.0])
    x    y    dy/dx
    0.0  0.1  0.0
    1.0  0.1  0.0

    You must supply precisely one argument:

    >>> vg2fg()
    Traceback (most recent call last):
    ...
    ValueError: parameter `vg2fg` of element `?` requires exactly one argument but \
`0` are given.
    """

    XLABEL = "VG [million m³]"
    YLABEL = "FG [m/s]"

    _simple_ann = anntools.ANN(
        weights_input=[[0.0]],
        weights_output=[[0.0]],
        intercepts_hidden=[[0.0]],
        intercepts_output=[0.0],
    )
    _keyword: Literal["velocity", "timedelay"] | None = None

    @overload
    def __call__(self, *, velocity: float) -> None: ...

    @overload
    def __call__(self, *, timedelay: float) -> None: ...

    @overload
    def __call__(self, algorithm: interptools.InterpAlgorithm) -> None: ...

    def __call__(
        self,
        algorithm: interptools.InterpAlgorithm | None = None,
        velocity: float | None = None,
        timedelay: float | None = None,
    ) -> None:
        nmb = (algorithm is not None) + (velocity is not None) + (timedelay is not None)
        if nmb != 1:
            raise ValueError(
                f"parameter {objecttools.elementphrase(self)} requires exactly one "
                f"argument but `{nmb}` are given."
            )
        self._keyword = None
        if algorithm is None:
            if velocity is None:
                assert timedelay is not None
                velocity = self._convert_velocity_timedelay(timedelay)
                self._keyword = "timedelay"
            else:
                self._keyword = "velocity"
            algorithm = anntools.ANN(
                weights_input=[[0.0]],
                weights_output=[[0.0]],
                intercepts_hidden=[[0.0]],
                intercepts_output=[velocity],
            )
        super().__call__(algorithm)

    def _convert_velocity_timedelay(self, value: float) -> float:
        return (self.subpars.laen * 1000.0) / (value * 60.0 * 60.0)

    def __repr__(self) -> str:
        algorithm = self.algorithm
        if (self.nmb_outputs == 1) and isinstance(algorithm, anntools.ANN):
            self._simple_ann.intercepts_output = algorithm.intercepts_output
            if (self._keyword is not None) and (algorithm == self._simple_ann):
                value = algorithm.intercepts_output[0]
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
