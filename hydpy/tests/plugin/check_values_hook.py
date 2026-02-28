# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    import numpy

    from hydpy.core import typingtools
    from hydpy.models.hland import hland_control

    # NDIM = 0, TYPE = float
    area: hland_control.Area
    assert_type(area.value, float)
    area.value = 1.0
    area.value = 1
    area.value = [1.0]  # type: ignore[assignment]
    area.value = numpy.ones((), dtype=numpy.float64)  # type: ignore[assignment]

    # NDIM = 0, TYPE = int
    nmbzones: hland_control.NmbZones
    assert_type(nmbzones.value, int)
    nmbzones.value = 1.0  # type: ignore[assignment]
    nmbzones.value = 1
    nmbzones.value = True
    nmbzones.value = [1]  # type: ignore[assignment]
    nmbzones.value = numpy.ones((), dtype=numpy.int64)  # type: ignore[assignment]

    # NDIM = 0, TYPE = bool
    resparea: hland_control.RespArea
    assert_type(resparea.value, bool)
    resparea.value = 1  # type: ignore[assignment]
    resparea.value = True
    resparea.value = [True]  # type: ignore[assignment]
    resparea.value = numpy.ones((), dtype=numpy.bool_)  # type: ignore[assignment]

    # NDIM = 1, TYPE = float
    zonearea: hland_control.ZoneArea
    assert_type(zonearea.value, typingtools.VectorFloat)
    zonearea.value = 1.0
    zonearea.value = 1
    zonearea.value = [1.0]
    zonearea.value = [[1.0], [1.0]]  # type: ignore[list-item]
    zonearea.value = numpy.ones((1,), dtype=numpy.float64)
    zonearea.value = numpy.ones((1,), dtype=numpy.int64)

    # NDIM = 1, TYPE = int
    zonetype: hland_control.ZoneType
    assert_type(zonetype.value, typingtools.VectorInt)
    zonetype.value = 1.0  # type: ignore[assignment]
    zonetype.value = 1
    zonetype.value = True
    zonetype.value = [1]
    zonetype.value = [1.0]  # type: ignore[list-item]
    zonetype.value = [[1], [1]]  # type: ignore[list-item]
    zonetype.value = numpy.ones((1,), dtype=numpy.float64)
    zonetype.value = numpy.ones((1,), dtype=numpy.int64)

    # NDIM = 2, TYPE = float
    sred: hland_control.SRed
    assert_type(sred.value, typingtools.VectorFloat)
    sred.value = 1.0
    sred.value = 1
    sred.value = [1.0]  # type: ignore[list-item]
    sred.value = [[1.0], [1.0]]
    sred.value = numpy.ones((1, 1), dtype=numpy.float64)
    sred.value = numpy.ones((1, 1), dtype=numpy.int64)
