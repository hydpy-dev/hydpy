# pylint: disable=missing-module-docstring, used-before-assignment
# pylint: disable=unnecessary-dunder-call
# mypy: disable-error-code="no-untyped-call"

if __name__ == "__main__":

    import math
    import operator
    from collections.abc import Iterable, Iterator
    from typing import Any, assert_type, Self

    import numpy

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
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
    sim: sequencetools.Sim  # NDIM = 0, TYPE = float
    vector: typingtools.VectorFloat

    class StrParameter(parametertools.Parameter):
        """Overrides members annotated with `GeneralHook` more specifically."""

        NDIM = 0
        TYPE = float

        def __add__(self, other: str) -> str:
            return other

        def __iadd__(self, other: str) -> Self:
            return self

        def __floor__(self) -> str:
            return ""

    strparameter: StrParameter

    # binary operators
    assert_type(area + 1.0, float)
    assert_type(area + 1, float)
    assert_type(1.0 + area, float)
    assert_type(area + area, float)
    assert_type(area + zonearea, typingtools.VectorFloat)
    assert_type(area + vector, typingtools.VectorFloat)
    assert_type(vector + area, typingtools.NDArrayFloat)  # numpy's stubs decide
    assert_type(nmbzones + 1, int)
    assert_type(nmbzones + 1.0, float)
    assert_type(nmbzones / 2, float)
    assert_type(nmbzones // 2, int)
    assert_type(nmbzones % 2, int)
    assert_type(resparea + resparea, int)
    assert_type(zonearea * 2.0, typingtools.VectorFloat)
    assert_type(2.0 * zonearea, typingtools.VectorFloat)
    assert_type(zonearea * zonetype, typingtools.VectorFloat)
    assert_type(zonetype * zonetype, typingtools.VectorInt)
    assert_type(zonetype / 2, typingtools.VectorFloat)
    assert_type(nmbzones + zonetype, typingtools.VectorInt)
    assert_type(sred - zonearea, typingtools.MatrixFloat)
    assert_type(zonearea**2, typingtools.VectorFloat)
    assert_type(2.0**zonearea, typingtools.VectorFloat)
    assert_type(divmod(area, 2.0), tuple[float, float])
    assert_type(
        divmod(zonearea, 2.0), tuple[typingtools.VectorFloat, typingtools.VectorFloat]
    )
    assert_type(area + parameter, Any)
    assert_type(parameter + area, Any)
    assert_type(numpy.sum(numpy.isnan(parameter + 1.0)), Any)
    assert_type(parameter - parameter, Any)
    assert_type(parameter + [1.0, 2.0], Any)  # fine for multidimensional variables
    assert_type(parameter + vector, Any)
    _ = parameter + "wrong"  # type: ignore[operator]
    _ = "wrong" + parameter  # type: ignore[operator]
    _ = area + "wrong"  # type: ignore[operator]
    assert_type(sim + 1.0, float)
    assert_type(sim - area, float)
    assert_type(sim * zonearea, typingtools.VectorFloat)
    _ = sim + "wrong"  # type: ignore[operator]

    # binary functions
    assert_type(
        divmod(2.0, zonearea), tuple[typingtools.VectorFloat, typingtools.VectorFloat]
    )
    assert_type(pow(area, 2), float)
    assert_type(pow(area, 2.0), Any)  # like `area ** 2.0` (might be complex)
    assert_type(pow(2.0, zonearea), typingtools.VectorFloat)
    assert_type(pow(zonetype, 2), typingtools.VectorInt)
    assert_type(pow(area, parameter), Any)
    assert_type(pow(2, 3), int)
    _ = pow(zonearea, "wrong")  # type: ignore[operator]
    _ = pow(nmbzones, 2, 3)  # type: ignore[call-overload]
    assert_type(operator.add(area, zonearea), typingtools.VectorFloat)
    assert_type(operator.__add__(area, zonearea), typingtools.VectorFloat)
    assert_type(operator.sub(sred, zonearea), typingtools.MatrixFloat)
    assert_type(operator.mul(2.0, sim), float)
    assert_type(operator.truediv(nmbzones, 2), float)
    assert_type(operator.floordiv(nmbzones, 2), int)
    assert_type(operator.mod(zonetype, nmbzones), typingtools.VectorInt)
    assert_type(operator.pow(zonearea, 2), typingtools.VectorFloat)
    assert_type(operator.add(parameter, area), Any)
    _ = pow(parameter, "wrong")  # type: ignore[operator]
    assert_type(operator.add(1, 2), Any)
    _ = operator.add(area, "wrong")  # type: ignore[operator]

    # in-place operators
    area += 1.0
    assert_type(area, hland_control.Area)
    zonearea *= zonearea
    assert_type(zonearea, hland_control.ZoneArea)
    zonearea -= vector
    nmbzones //= 2
    parameter += area
    parameter -= [1.0, 2.0]
    parameter += "wrong"  # type: ignore[operator]
    zonearea += area
    zonearea *= zonetype
    zonetype += zonetype
    zonetype //= 2
    zonetype *= 1.5  # type: ignore[assignment]
    sred -= sred
    sred /= zonearea
    nmbzones *= 2
    nmbzones *= 1.5  # type: ignore[assignment]
    nmbzones /= 2  # type: ignore[assignment]
    resparea += resparea  # type: ignore[assignment]
    area += "wrong"  # type: ignore[operator]
    sim += 1.0
    assert_type(sim, sequencetools.Sim)
    zonearea **= "wrong"  # type: ignore[operator]
    _ = zonearea["wrong"]  # type: ignore[call-overload]

    # in-place functions
    assert_type(operator.iadd(area, 1.0), hland_control.Area)
    assert_type(operator.__imul__(zonearea, zonetype), hland_control.ZoneArea)
    assert_type(operator.isub(sred, zonearea), hland_control.SRed)
    assert_type(operator.ifloordiv(nmbzones, 2), hland_control.NmbZones)
    assert_type(operator.imod(zonetype, 2), hland_control.ZoneType)
    assert_type(operator.ipow(sim, 2), sequencetools.Sim)
    assert_type(operator.iadd(parameter, area), parametertools.Parameter)
    operator.iadd(parameter, "wrong")  # type: ignore[operator]
    operator.itruediv(nmbzones, 2)  # type: ignore[assignment]
    operator.isub(area, zonearea)  # type: ignore[assignment]
    operator.iadd(area, "wrong")  # type: ignore[operator]
    assert_type(operator.iadd(1.0, area), float)
    assert_type(operator.iadd(vector, zonearea), typingtools.VectorFloat)
    assert_type(operator.iadd(1.0, 2.0), Any)

    # more specific annotations of overriding members
    assert_type(strparameter + "a", str)
    assert_type(operator.add(strparameter, "a"), Any)
    strparameter += "a"
    assert_type(operator.iadd(strparameter, "a"), Any)
    assert_type(math.floor(strparameter), str)
    _ = "a" + strparameter  # type: ignore[operator]

    # unary operators and functions
    assert_type(+area, float)
    assert_type(-area, float)
    assert_type(-zonetype, typingtools.VectorInt)
    assert_type(abs(area), float)
    assert_type(abs(zonearea), typingtools.VectorFloat)
    assert_type(~area, float)
    assert_type(~zonetype, typingtools.VectorFloat)
    assert_type(math.floor(area), int)
    assert_type(math.ceil(zonearea), typingtools.VectorInt)
    assert_type(math.trunc(area), int)
    assert_type(math.trunc(zonearea), typingtools.VectorInt)
    assert_type(round(area), int)
    assert_type(round(area, None), int)
    assert_type(round(area, 1), float)
    assert_type(area.__round__(), int)
    assert_type(area.__round__(1), float)
    assert_type(round(nmbzones), int)
    assert_type(round(nmbzones, -1), int)
    assert_type(round(resparea), int)
    assert_type(round(zonearea), typingtools.VectorFloat)
    assert_type(round(zonearea, 1), typingtools.VectorFloat)
    assert_type(zonearea.__round__(1), typingtools.VectorFloat)
    assert_type(round(zonetype), typingtools.VectorInt)
    assert_type(round(water), typingtools.VectorBool)
    round(area, "1")  # type: ignore[call-overload]
    area.__round__("1")  # type: ignore[arg-type]
    assert_type(abs(parameter), Any)
    assert_type(-sim, float)
    assert_type(math.floor(sim), int)
    assert_type(operator.pos(area), float)
    assert_type(operator.neg(zonetype), typingtools.VectorInt)
    assert_type(operator.__neg__(sim), float)
    assert_type(operator.abs(zonearea), typingtools.VectorFloat)
    assert_type(operator.invert(zonetype), typingtools.VectorFloat)
    assert_type(operator.inv(area), float)
    assert_type(operator.__inv__(sred), typingtools.MatrixFloat)
    assert_type(operator.neg(parameter), Any)
    assert_type(operator.neg(1), int)

    # item access
    assert_type(area[0], float)
    assert_type(area[:], float)
    assert_type(zonearea[0], numpy.float64)
    assert_type(zonearea[:], typingtools.VectorFloat)
    assert_type(zonetype[0], numpy.int64)
    assert_type(sred[0], typingtools.VectorFloat)
    assert_type(sred[:, 0], typingtools.VectorFloat)
    assert_type(sred[0, 0], numpy.float64)
    assert_type(sred[:, :], typingtools.MatrixFloat)
    assert_type(zonearea[0] + zonearea, typingtools.VectorFloat)
    assert_type(zonearea[[0, 1]], typingtools.NDArrayFloat)
    assert_type(numpy.sum(numpy.isnan(parameter[0])), Any)

    # iteration
    for value_float in zonearea:
        assert_type(value_float, numpy.float64)
    for value_int in zonetype:
        assert_type(value_int, numpy.int64)
    for row in sred:
        assert_type(row, typingtools.VectorFloat)
    for _ in area:  # type: ignore[attr-defined]
        pass
    for _ in sim:  # type: ignore[attr-defined]
        pass
    _ = 1.0 in area  # type: ignore[attr-defined]
    assert_type(1.0 in zonearea, bool)
    assert_type(1 in sred, bool)
    first, second = area  # type: ignore[attr-defined]
    for value_any in parameter:
        assert_type(value_any, Any)
    for value_zonearea in zonearea:
        assert_type(value_zonearea, numpy.float64)

    # functions iterating over variables
    assert_type(list(zonearea), list[numpy.float64])
    assert_type(tuple(zonetype), tuple[numpy.int64, ...])
    assert_type(sorted(zonearea), list[numpy.float64])
    assert_type(iter(sred), Iterator[typingtools.VectorFloat])
    assert_type(enumerate(zonearea), enumerate[numpy.float64])
    assert_type(sum(zonearea), numpy.float64)
    assert_type(sum(water), numpy.int64)
    assert_type(sum(sred), typingtools.VectorFloat)
    assert_type(sum(water, start=0.5), numpy.bool_ | float)
    assert_type(sum(zonearea, 1.0), float)
    assert_type(min(zonearea), numpy.float64)
    assert_type(max(zonetype), numpy.int64)
    _ = max(area, 1.0)  # no iteration
    _ = min(sred)  # type: ignore[arg-type]
    _ = max(sred)  # type: ignore[arg-type]
    _ = sorted(sred)  # type: ignore[arg-type]
    _ = sorted(sred, key=None)  # type: ignore[arg-type]
    assert_type(min(sred, key=sum), typingtools.VectorFloat)
    assert_type(sorted(sred, key=sum), list[typingtools.VectorFloat])
    assert_type(sorted(zonearea, reverse=True), list[numpy.float64])
    assert_type(list(parameter), list[Any])
    assert_type(list(zonearea), list[numpy.float64])
    _ = list(area)  # type: ignore[arg-type]
    _ = sum(area)  # type: ignore[arg-type]
    _ = min(area)  # type: ignore[arg-type]
    _ = zip(zonearea, area)  # type: ignore[arg-type]
    _ = map(abs, area)  # type: ignore[arg-type]

    # variables as iterables of the expected type (precise `__iter__` signatures)
    class SubZoneArea(hland_control.ZoneArea):
        """Inherits the precise signature of `ZoneArea.__iter__`."""

    class StrZones(parametertools.Parameter):
        """Defines `__iter__` itself."""

        NDIM = 1
        TYPE = float

        def __iter__(self) -> Iterator[str]:
            yield ""

    class SubArea(hland_control.Area):
        """Inherits the dimensionality and value type of `Area`."""

    class SubSRed(hland_control.SRed):
        """Inherits the dimensionality and value type of `SRed`."""

    def take_strings(values: Iterable[str]) -> None:  # pylint: disable=unused-argument
        """Expects an iterable of strings."""

    subzonearea: SubZoneArea
    strzones: StrZones
    subarea: SubArea
    subsred: SubSRed
    for _ in subarea:  # type: ignore[attr-defined]
        pass
    _ = list(subarea)  # type: ignore[arg-type]
    _ = min(subsred)  # type: ignore[arg-type]
    assert_type(sum(subsred), typingtools.VectorFloat)
    floats: Iterable[numpy.float64] = zonearea
    rows: Iterable[typingtools.VectorFloat] = sred
    int64s: list[numpy.int64] = list(zonetype)
    subfloats: list[numpy.float64] = list(subzonearea)
    strings: list[str] = list(strzones)
    anything: list[str] = list(parameter)  # unknown dimensionality: no check
    ints: list[int] = list(zonetype)  # type: ignore[arg-type]
    floats_str: list[str] = list(zonearea)  # type: ignore[arg-type]
    subfloats_str: list[str] = list(subzonearea)  # type: ignore[arg-type]
    tuple_str: tuple[str, ...] = tuple(zonetype)  # type: ignore[arg-type]
    sorted_str: list[str] = sorted(zonearea)  # type: ignore[arg-type]
    iterable_str: Iterable[str] = zonearea  # type: ignore[assignment]
    rows_float: Iterable[numpy.float64] = sred  # type: ignore[assignment]
    take_strings(zonetype)  # type: ignore[arg-type]
    take_strings(strzones)
    zonetype.values = list(zonetype)
    zonetype.values = list(zonearea)  # type: ignore[arg-type]
    water.values = list(zonetype)  # type: ignore[arg-type]
    sred.values = list(sred)
    sred.values = list(zonearea)  # type: ignore[arg-type]

    # item assignment
    area[0] = 1.0
    area[:] = 1
    area["wrong"] = 1.0  # type: ignore[index]
    area[0] = [1.0]  # type: ignore[assignment]
    nmbzones[0] = 1.5  # type: ignore[assignment]
    zonearea[0] = 1.0
    zonearea[:] = [1.0, 2.0]
    zonearea[:] = vector
    zonearea["wrong"] = 1.0  # type: ignore[call-overload]
    zonetype[0] = 1
    zonetype[0] = 1.5  # type: ignore[assignment]
    sred[0] = [1.0, 2.0]
    sred[0, 0] = 1.0
    sred[:] = [[1.0], [2.0]]
    parameter[0] = 1
    parameter[:] = [[1.0, 2.0], [3.0, 4.0]]
    parameter[:] = vector
    parameter[0] = "wrong"  # type: ignore[assignment]
    parameter[0] = None  # type: ignore[assignment]

    # conversions depending on the dimensionality
    assert_type(float(area), float)
    assert_type(int(nmbzones), int)
    assert_type(len(zonearea), int)
    _ = float(zonearea)  # type: ignore[arg-type]
    _ = int(zonetype)  # type: ignore[arg-type]
    _ = len(area)  # type: ignore[arg-type]
    assert_type(float(parameter), float)
    assert_type(len(parameter), int)
    assert_type(float(sim), float)
    _ = len(sim)  # type: ignore[arg-type]
    reversed(zonearea)
    reversed(sred)
    reversed(parameter)
    reversed(area)  # type: ignore[arg-type]
    reversed(sim)  # type: ignore[arg-type]
    assert_type(complex(area), complex)
    complex(zonearea)  # type: ignore[arg-type]
    assert_type(math.exp(area), float)
    assert_type(math.isnan(nmbzones), bool)
    assert_type(math.frexp(sim), tuple[float, int])
    assert_type(math.exp(parameter), float)
    _ = math.exp(zonearea)  # type: ignore[arg-type]
    _ = math.isnan(sred)  # type: ignore[arg-type]
    assert_type(math.atan2(area, sim), float)
    _ = math.atan2(area, zonearea)  # type: ignore[arg-type]
    _ = math.pow(zonearea, area)  # type: ignore[arg-type]
    assert_type(math.log(area, nmbzones), float)
    _ = math.log(area, zonearea)  # type: ignore[arg-type]
    assert_type(math.isclose(area, sim, abs_tol=area), bool)
    _ = math.isclose(area, sim, rel_tol=zonearea)  # type: ignore[arg-type]
    assert_type(math.hypot(area, sim, nmbzones), float)
    _ = math.hypot(area, sim, zonearea)  # type: ignore[arg-type]
