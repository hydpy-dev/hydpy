# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    import numpy

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.models.hland import hland_control

    # NDIM = ?, TYPE = ?
    parameter: parametertools.Parameter
    parameter.trim("x", "x")  # type: ignore[arg-type]
    parameter.trim(True, True)
    parameter.trim([True], [True])
    parameter.trim([[True]], [[True]])
    parameter.trim([[[True]]], [[[True]]])
    parameter.trim([[[[True]]]], [[[[True]]]])  # type: ignore[arg-type]
    sequence: sequencetools.ConditionSequence
    sequence.trim("x", "x")  # type: ignore[arg-type]
    sequence.trim(True, True)
    sequence.trim([True], [True])
    sequence.trim([[True]], [[True]])
    sequence.trim([[[True]]], [[[True]]])
    sequence.trim([[[[True]]]], [[[[True]]]])  # type: ignore[arg-type]

    # NDIM = 0, TYPE = float
    area: hland_control.Area
    # area.trim()
    # area.trim(1.0, None)
    # area.trim(None, 1.0)
    # area.trim(1.0, 1.0)
    # area.trim(1, 1)
    # area.trim(1.0, upper=1.0)
    # area.trim(lower=1.0, upper=1.0)
    # area.trim("x", 1)  # type: ignore[arg-type]
    # area.trim(1, "x")  # type: ignore[arg-type]
    area.trim([1.0], 1.0)  # type: ignore[arg-type]
    area.trim(numpy.ones((), dtype=numpy.float64), 1)  # type: ignore[arg-type]

    # NDIM = 0, TYPE = int
    nmbzones: hland_control.NmbZones
    nmbzones.trim(1.0, 1.0)  # type: ignore[arg-type]
    nmbzones.trim(1, 1)
    nmbzones.trim(True, True)

    # NDIM = 0, TYPE = bool
    resparea: hland_control.RespArea
    resparea.trim(1, 1)  # type: ignore[arg-type]
    resparea.trim(True, True)

    # NDIM = 1, TYPE = float
    zonearea: hland_control.ZoneArea
    zonearea.trim(1.0, 1.0)
    zonearea.trim([1.0], [1.0])
    zonearea.trim([[1.0]], [[1.0]])  # type: ignore[list-item]

    # NDIM = 1, TYPE = int
    zonetype: hland_control.ZoneType
    zonetype.trim([1.0], [1.0])  # type: ignore[list-item]
    zonetype.trim([1], [1])

    # NDIM = 2, TYPE = float
    sred: hland_control.SRed
    sred.trim(1.0, 1.0)
    sred.trim([1.0], [1.0])  # type: ignore[list-item]
    sred.trim([[1.0]], [[1.0]])
    sred.trim([[[1.0]]], [[[1.0]]])  # type: ignore[list-item]
