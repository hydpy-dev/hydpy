# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.kinw import kinw_variables


class WBM(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Wasserspiegelbreite Hauptgerinne (water level width of the main channel) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class WBLV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Wasserspiegelbreite des linken Vorlandes (water level width of the left foreland)
    [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class WBRV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Wasserspiegelbreite des rechten Vorlandes (water level width of the right
    foreland) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class WBLVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Wasserspiegelbreite des linken Vorlandrandes (water level width of the left outer
    embankment) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class WBRVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Wasserspiegelbreite des rechten Vorlandrandes (water level width of the right
    outer embankment) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class WBG(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Wasserspiegelbreite des gesamten Querschnittes (water level width of the total
    cross section) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class AM(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchflossene Fläche Hauptgerinne (wetted area of the main channel) [m²]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ALV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchflossene Fläche linkes Vorland (wetted area of the left foreland) [m²]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ARV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchflossene Fläche rechtes Vorland (wetted area of the right foreland) [m²]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ALVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchflossene Fläche linker Vorlandrand (wetted area of the left outer
    embankments) [m²]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ARVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchflossene Fläche rechter Vorlandrand (wetted area of the right outer
    embankments) [m²]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class AG(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchflossene Fläche gesamt  (total wetted area) [m²]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class UM(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Benetzter Umfang Hauptgerinne (wetted perimeter of the main channel) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ULV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Benetzter Umfang linkes Vorland (wetted perimeter of the left foreland) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class URV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Benetzter Umfang rechtes Vorland (wetted perimeter of the right foreland) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ULVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Benetzter Umfang linker Vorlandrand (wetted perimeter of the left outer
    embankment) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class URVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Benetzter Umfang rechtes Vorlandrand (wetted perimeter of the right outer
    embankment) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QM(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchfluss Hauptgerinne (discharge of the main channel) [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QLV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchfluss linkes Vorland (discharge of the left foreland) [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QRV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchfluss rechtes Vorland (discharge of the right foreland) [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchfluss Vorlandränder (discharge of both outer embankment) [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QLVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchfluss linker Vorlandrand (discharge of the left outer embankment) [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QRVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Durchfluss rechter Vorlandrand (discharge of the right outer embankment)
    [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHM(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Hinsichtlich der Gewässersohle regularisierter Wasserstand (stage regularised
    with respect to the channel bottom) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHMDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |RHM| (derivative of |RHM|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHV(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Hinsichtlich der des Übergangs Hauptgerinne/Vorländer regularisierter Wasserstand
    (stage regularised with respect to the transition from the main channel to both
    forelands) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |RHV| (derivative of |RHV|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHLVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Hinsichtlich der des Übergangs linkes Vorland/ linker Vorlandrand regularisierter
    Wasserstand (stage regularised with respect to the transition from the left foreland
    to the left outer embankment) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHLVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |RHLVR| (derivative of |RHLVR|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHRVR(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Hinsichtlich der des Übergangs rechtes Vorland/ rechter Vorlandrand
    regularisierter Wasserstand (stage regularised with respect to the transition from
    the right foreland to the right outer embankment) [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class RHRVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |RHRVR| (derivative of |RHRVR|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class AMDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |AM| (derivative of |AM|) [m²/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ALVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |ALV| (derivative of |ALV|) [m²/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ARVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |ARV| (derivative of |ARV|) [m²/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ALVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |ALVR| (derivative of |ALVR|) [m²/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ARVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |ARVR| (derivative of |ARVR|) [m²/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class UMDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |UM| (derivative of |UM|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ULVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |ULV| (derivative of |ULV|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class URVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |URV| (derivative of |URV|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class ULVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |ULVR| (derivative of |ULVR|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class URVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |URVR| (derivative of |URVR|) [m/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QMDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |QM| (derivative of |QM|) [m³/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QLVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |QLV| (derivative of |QLV|) [m³/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QRVDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |QRV| (derivative of |QRV|) [m³/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QLVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |QLVR| (derivative of |QLVR|) [m³/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QRVRDH(kinw_variables.MixinSubsections, sequencetools.AideSequence):
    """Ableitung von |QRVR| (derivative of |QRVR|) [m³/m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)
