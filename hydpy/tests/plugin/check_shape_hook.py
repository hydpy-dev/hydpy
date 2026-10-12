# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    import numpy

    from hydpy.models.hland import hland_control

    # NDIM = 0
    area: hland_control.Area
    assert_type(area.shape, tuple[()])
    area.shape = 1  # type: ignore[assignment]
    area.shape = ()
    area.shape = (1,)  # type: ignore[assignment]
    area.shape = [1]  # type: ignore[assignment]
    area.shape = numpy.ones((), dtype=int)  # type: ignore[assignment]

    # NDIM = 1
    zonearea: hland_control.ZoneArea
    zonearea.shape = 1.0  # type: ignore[assignment]
    zonearea.shape = 1
    zonearea.shape = ()  # type: ignore[assignment]
    zonearea.shape = 1.0  # type: ignore[assignment]
    zonearea.shape = (1,)
    zonearea.shape = [1]  # type: ignore[assignment]
    zonearea.shape = numpy.ones((1,), dtype=int)  # type: ignore[assignment]

    # NDIM = 2
    sred: hland_control.SRed
    sred.shape = 1  # type: ignore[assignment]
    sred.shape = ()  # type: ignore[assignment]
    sred.shape = (1,)  # type: ignore[assignment]
    sred.shape = (1.0, 1.0)  # type: ignore[assignment]
    sred.shape = (1, 1)
    sred.shape = [1]  # type: ignore[assignment]
    sred.shape = numpy.ones((1, 1), dtype=int)  # type: ignore[assignment]
