# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WBM(sequencetools.AideSequence):
    """Wasserspiegelbreite Hauptgerinne (water level width of the main
    channel) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class WBLV(sequencetools.AideSequence):
    """Wasserspiegelbreite des linken Vorlandes (water level width of the
    left foreland) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class WBRV(sequencetools.AideSequence):
    """Wasserspiegelbreite des rechten Vorlandes (water level width of the
    right foreland) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class WBLVR(sequencetools.AideSequence):
    """Wasserspiegelbreite des linken Vorlandrandes (water level width of
    the left outer embankment) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class WBRVR(sequencetools.AideSequence):
    """Wasserspiegelbreite des rechten Vorlandrandes (water level width of
    the right outer embankment) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class WBG(sequencetools.AideSequence):
    """Wasserspiegelbreite des gesamten Querschnittes (water level width of
    the total cross section) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class AM(sequencetools.AideSequence):
    """Durchflossene Fläche Hauptgerinne (wetted area of the
    main channel) [m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ALV(sequencetools.AideSequence):
    """Durchflossene Fläche linkes Vorland (wetted area of the
    left foreland) [m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ARV(sequencetools.AideSequence):
    """Durchflossene Fläche rechtes Vorland (wetted area of the
    right foreland) [m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ALVR(sequencetools.AideSequence):
    """Durchflossene Fläche linker Vorlandrand (wetted area of the
    left outer embankments) [m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ARVR(sequencetools.AideSequence):
    """Durchflossene Fläche rechter Vorlandrand (wetted area of the
    right outer embankments) [m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class AG(sequencetools.AideSequence):
    """Durchflossene Fläche gesamt  (total wetted area) [m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class UM(sequencetools.AideSequence):
    """Benetzter Umfang Hauptgerinne (wetted perimeter of the
    main channel) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ULV(sequencetools.AideSequence):
    """Benetzter Umfang linkes Vorland (wetted perimeter of the
    left foreland) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class URV(sequencetools.AideSequence):
    """Benetzter Umfang rechtes Vorland (wetted perimeter of the
    right foreland) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ULVR(sequencetools.AideSequence):
    """Benetzter Umfang linker Vorlandrand (wetted perimeter of the
    left outer embankment) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class URVR(sequencetools.AideSequence):
    """Benetzter Umfang rechtes Vorlandrand (wetted perimeter of the
    right outer embankment) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QM(sequencetools.AideSequence):
    """Durchfluss Hauptgerinne (discharge of the main channel) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QLV(sequencetools.AideSequence):
    """Durchfluss linkes Vorland (discharge of the left foreland) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QRV(sequencetools.AideSequence):
    """Durchfluss rechtes Vorland (discharge of the right foreland) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QVR(sequencetools.AideSequence):
    """Durchfluss Vorlandränder (discharge of both outer embankment) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QLVR(sequencetools.AideSequence):
    """Durchfluss linker Vorlandrand (discharge of the left outer
    embankment) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QRVR(sequencetools.AideSequence):
    """Durchfluss rechter Vorlandrand (discharge of the right outer
    embankment) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHM(sequencetools.AideSequence):
    """Hinsichtlich der Gewässersohle regularisierter Wasserstand (stage
    regularised with respect to the channel bottom) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHMDH(sequencetools.AideSequence):
    """Ableitung von |RHM| (derivative of |RHM|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHV(sequencetools.AideSequence):
    """Hinsichtlich der des Übergangs Hauptgerinne/Vorländer regularisierter
    Wasserstand (stage regularised with respect to the transition
    from the main channel to both forelands) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHVDH(sequencetools.AideSequence):
    """Ableitung von |RHV| (derivative of |RHV|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHLVR(sequencetools.AideSequence):
    """Hinsichtlich der des Übergangs linkes Vorland/ linker Vorlandrand
    regularisierter Wasserstand (stage regularised with respect to the
    transition from the left foreland to the left outer embankment) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHLVRDH(sequencetools.AideSequence):
    """Ableitung von |RHLVR| (derivative of |RHLVR|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHRVR(sequencetools.AideSequence):
    """Hinsichtlich der des Übergangs rechtes Vorland/ rechter Vorlandrand
    regularisierter Wasserstand (stage regularised with respect to the
    transition from the right foreland to the right outer embankment) [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class RHRVRDH(sequencetools.AideSequence):
    """Ableitung von |RHRVR| (derivative of |RHRVR|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class AMDH(sequencetools.AideSequence):
    """Ableitung von |AM| (derivative of |AM|) [m²/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ALVDH(sequencetools.AideSequence):
    """Ableitung von |ALV| (derivative of |ALV|) [m²/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ARVDH(sequencetools.AideSequence):
    """Ableitung von |ARV| (derivative of |ARV|) [m²/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ALVRDH(sequencetools.AideSequence):
    """Ableitung von |ALVR| (derivative of |ALVR|) [m²/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ARVRDH(sequencetools.AideSequence):
    """Ableitung von |ARVR| (derivative of |ARVR|) [m²/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class UMDH(sequencetools.AideSequence):
    """Ableitung von |UM| (derivative of |UM|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ULVDH(sequencetools.AideSequence):
    """Ableitung von |ULV| (derivative of |ULV|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class URVDH(sequencetools.AideSequence):
    """Ableitung von |URV| (derivative of |URV|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class ULVRDH(sequencetools.AideSequence):
    """Ableitung von |ULVR| (derivative of |ULVR|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class URVRDH(sequencetools.AideSequence):
    """Ableitung von |URVR| (derivative of |URVR|) [m/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QMDH(sequencetools.AideSequence):
    """Ableitung von |QM| (derivative of |QM|) [m³/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QLVDH(sequencetools.AideSequence):
    """Ableitung von |QLV| (derivative of |QLV|) [m³/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QRVDH(sequencetools.AideSequence):
    """Ableitung von |QRV| (derivative of |QRV|) [m³/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QLVRDH(sequencetools.AideSequence):
    """Ableitung von |QLVR| (derivative of |QLVR|) [m³/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class QRVRDH(sequencetools.AideSequence):
    """Ableitung von |QRVR| (derivative of |QRVR|) [m³/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
