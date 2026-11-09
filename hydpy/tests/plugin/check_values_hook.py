# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type

    import numpy

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.core import typingtools
    from hydpy.models.evap import evap_control
    from hydpy.models.hland import hland_control
    from hydpy.models.hland import hland_states
    from hydpy.models.sw1d import sw1d_control

    vector_float: typingtools.VectorFloat
    vector_int: typingtools.VectorInt
    matrix_float: typingtools.MatrixFloat
    matrix_int: typingtools.MatrixInt
    vector_float32: numpy.ndarray[tuple[int], numpy.dtype[numpy.float32]]
    vector_int32: numpy.ndarray[tuple[int], numpy.dtype[numpy.int32]]
    vector_bool: typingtools.VectorBool
    matrix_int32: numpy.ndarray[tuple[int, int], numpy.dtype[numpy.int32]]

    # NDIM = ?, TYPE = ?
    parameter: parametertools.Parameter
    assert_type(parameter.value, Any)
    assert_type(numpy.sum(numpy.isnan(parameter.values)), Any)
    iosequence: sequencetools.IOSequence
    assert_type(numpy.sum(numpy.isnan(iosequence.series)), Any)

    # NDIM = 0, TYPE = float
    area: hland_control.Area
    assert_type(area.value, float)
    area.value = 1.0
    area.value = 1
    area.value = [1.0]  # type: ignore[assignment]
    area.value = numpy.ones((), dtype=numpy.float64)  # type: ignore[assignment]
    area.value = numpy.float64(1.0)
    area.value = numpy.float32(1.0)
    area.value = numpy.int64(1)
    area.value = numpy.bool_(True)
    area.value = numpy.str_("x")  # type: ignore[assignment]

    # NDIM = 0, TYPE = int
    nmbzones: hland_control.NmbZones
    assert_type(nmbzones.value, int)
    nmbzones.value = 1.0  # type: ignore[assignment]
    nmbzones.value = 1
    nmbzones.value = True
    nmbzones.value = [1]  # type: ignore[assignment]
    nmbzones.value = numpy.ones((), dtype=numpy.int64)  # type: ignore[assignment]
    nmbzones.value = numpy.int64(1)
    nmbzones.value = numpy.int32(1)
    nmbzones.value = numpy.bool_(True)
    nmbzones.value = numpy.float64(1.0)  # type: ignore[assignment]

    # NDIM = 0, TYPE = bool
    resparea: hland_control.RespArea
    assert_type(resparea.value, bool)
    resparea.value = 1  # type: ignore[assignment]
    resparea.value = True
    resparea.value = [True]  # type: ignore[assignment]
    resparea.value = numpy.ones((), dtype=numpy.bool_)  # type: ignore[assignment]
    resparea.value = numpy.bool_(True)
    resparea.value = numpy.int64(1)  # type: ignore[assignment]

    # NDIM = 1, TYPE = float
    zonearea: hland_control.ZoneArea
    assert_type(zonearea.value, typingtools.VectorFloat)
    zonearea.value = 1.0
    zonearea.value = 1
    zonearea.value = [1.0]
    zonearea.value = [[1.0], [1.0]]  # type: ignore[list-item]
    zonearea.value = vector_float
    zonearea.value = vector_int
    zonearea.value = [numpy.float64(1.0), numpy.int64(2), 3]
    zonearea.value = vector_float32
    zonearea.value = vector_int32
    zonearea.value = vector_bool
    zonearea[0] = zonearea[1]
    zonearea[0] = numpy.float32(1.0)

    # NDIM = 1, TYPE = int
    zonetype: hland_control.ZoneType
    assert_type(zonetype.value, typingtools.VectorInt)
    zonetype.value = 1.0  # type: ignore[assignment]
    zonetype.value = 1
    zonetype.value = True
    zonetype.value = [1]
    zonetype.value = [1.0]  # type: ignore[list-item]
    zonetype.value = [[1], [1]]  # type: ignore[list-item]
    zonetype.value = vector_float  # type: ignore[assignment]
    zonetype.value = vector_int
    zonetype.value = [numpy.int64(1), 2]
    zonetype.value = vector_int32
    zonetype.value = vector_bool
    zonetype.value = vector_float32  # type: ignore[assignment]
    zonetype[0] = zonetype[1]
    zonetype[0] = numpy.bool_(True)
    zonetype[0] = numpy.float64(1.0)  # type: ignore[assignment]

    # NDIM = 1, TYPE = bool
    water: evap_control.Water
    assert_type(water.value, typingtools.VectorBool)
    water.value = [True, numpy.bool_(False)]
    water.value = vector_bool
    water.value = vector_int32  # type: ignore[assignment]
    water[0] = water[1]
    water[0] = 1  # type: ignore[assignment]

    # NDIM = 2, TYPE = float
    sred: hland_control.SRed
    assert_type(sred.value, typingtools.MatrixFloat)
    sred.value = 1.0
    sred.value = 1
    sred.value = [1.0]  # type: ignore[list-item]
    sred.value = [[1.0], [1.0]]
    sred.value = matrix_float
    sred.value = matrix_int
    sred.value = [[numpy.float64(1.0)], [numpy.float64(2.0)]]
    sred.value = [zonearea.value, zonearea.value]
    sred.value = matrix_int32
    sred[0] = zonearea.value
    sred[0] = vector_int32
    sred[0, 0] = sred[1, 1]

    # `new` and `old` of state sequences
    sm: hland_states.SM
    assert_type(sm.new, typingtools.VectorFloat)
    assert_type(sm.old, typingtools.VectorFloat)
    sm.new = [1.0]
    sm.old = [[1.0], [1.0]]  # type: ignore[list-item]
    uz: hland_states.UZ
    assert_type(uz.new, float)
    assert_type(uz.old, float)
    uz.new = 1.0
    uz.old = [1.0]  # type: ignore[assignment]

    # callback parameters
    gateheight: sw1d_control.GateHeight
    assert_type(gateheight.value, float)
    gateheight.value = 1.0
    gateheight.value = [1.0]  # type: ignore[assignment]

    # node sequences
    sim: sequencetools.Sim
    assert_type(sim.value, float)
    assert_type(sim.values, float)
    assert_type(sim.series, typingtools.VectorFloat)
    sim.value = 1.0
    sim.values = 1
    sim.value = [1.0]  # type: ignore[assignment]
    sim.series = [1.0]
    obs: sequencetools.Obs
    assert_type(obs.value, float)
    assert_type(obs.values, float)
    assert_type(obs.series, typingtools.VectorFloat)
