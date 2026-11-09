# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type

    import numpy

    from hydpy.core import parametertools
    from hydpy.core import typingtools
    from hydpy.models.evap import evap_control
    from hydpy.models.hland import hland_control

    area: hland_control.Area  # NDIM = 0, TYPE = float
    nmbzones: hland_control.NmbZones  # NDIM = 0, TYPE = int
    resparea: hland_control.RespArea  # NDIM = 0, TYPE = bool
    zonearea: hland_control.ZoneArea  # NDIM = 1, TYPE = float
    zonetype: hland_control.ZoneType  # NDIM = 1, TYPE = int
    water: evap_control.Water  # NDIM = 1, TYPE = bool
    sred: hland_control.SRed  # NDIM = 2, TYPE = float
    parameter: parametertools.Parameter  # NDIM and TYPE unknown

    class SubArea(hland_control.Area):
        """Inherits the precise signature of `Area.__array__`."""

    subarea: SubArea

    # explicit calls
    assert_type(area.__array__(), numpy.ndarray[tuple[()], numpy.dtype[numpy.float64]])
    assert_type(
        nmbzones.__array__(), numpy.ndarray[tuple[()], numpy.dtype[numpy.int64]]
    )
    assert_type(
        resparea.__array__(), numpy.ndarray[tuple[()], numpy.dtype[numpy.bool_]]
    )
    assert_type(zonearea.__array__(), typingtools.VectorFloat)
    assert_type(zonetype.__array__(), typingtools.VectorInt)
    assert_type(water.__array__(), typingtools.VectorBool)
    assert_type(sred.__array__(), typingtools.MatrixFloat)
    assert_type(sred.__array__(numpy.dtype(numpy.float64)), typingtools.MatrixFloat)
    assert_type(sred.__array__(copy=True), typingtools.MatrixFloat)
    assert_type(
        subarea.__array__(), numpy.ndarray[tuple[()], numpy.dtype[numpy.float64]]
    )
    assert_type(parameter.__array__(), typingtools.NDArray[Any])
    _ = sred.__array__(copy="yes")  # type: ignore[arg-type]

    # numpy's array protocol
    assert_type(numpy.sum(zonearea), numpy.float64)
    assert_type(numpy.sum(zonetype), numpy.int64)
    assert_type(numpy.sum(sred, axis=0), typingtools.NDArrayFloat)
    assert_type(numpy.asarray(zonearea), typingtools.NDArrayFloat)
    assert_type(numpy.asarray(parameter), typingtools.NDArray[Any])
    assert_type(numpy.asarray(zonetype), typingtools.NDArrayInt)
    assert_type(numpy.asarray(water), typingtools.NDArrayBool)
    assert_type(numpy.sum(water), numpy.int_)
