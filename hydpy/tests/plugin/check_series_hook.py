# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    import numpy

    from hydpy.core import typingtools
    from hydpy.models.hland import hland_fluxes

    list_1d: list[float]
    list_2d: list[list[float]]
    list_3d: list[list[list[float]]]
    list_4d: list[list[list[list[float]]]]
    array_0d: numpy.ndarray[tuple[()], numpy.dtype[numpy.float64]]
    array_1d: typingtools.VectorFloat
    array_2d: typingtools.MatrixFloat
    array_3d: typingtools.TensorFloat
    array_4d: numpy.ndarray[tuple[int, int, int, int], numpy.dtype[numpy.float64]]

    # NDIM = 0, TYPE = float
    perc: hland_fluxes.Perc
    assert_type(perc.series, typingtools.VectorFloat)
    perc.series = 1.0
    perc.series = 1
    perc.series = list_1d
    perc.series = list_2d  # type: ignore[assignment]
    perc.series = array_0d  # type: ignore[assignment]
    perc.series = array_1d
    perc.series = array_2d  # type: ignore[assignment]
    assert_type(perc.simseries, typingtools.VectorFloat)
    assert_type(perc.evalseries, typingtools.VectorFloat)

    # NDIM = 1, TYPE = float
    pc: hland_fluxes.PC
    assert_type(pc.series, typingtools.MatrixFloat)
    pc.series = 1.0
    pc.series = 1
    pc.series = list_1d  # type: ignore[assignment]
    pc.series = list_2d
    pc.series = list_3d  # type: ignore[assignment]
    pc.series = array_1d  # type: ignore[assignment]
    pc.series = array_2d
    pc.series = array_3d  # type: ignore[assignment]
    assert_type(pc.simseries, typingtools.MatrixFloat)
    assert_type(pc.evalseries, typingtools.MatrixFloat)

    # NDIM = 2, TYPE = float
    melt: hland_fluxes.Melt
    assert_type(melt.series, typingtools.TensorFloat)
    melt.series = 1.0
    melt.series = 1
    melt.series = list_2d  # type: ignore[assignment]
    melt.series = list_3d
    melt.series = list_4d  # type: ignore[assignment]
    melt.series = array_2d  # type: ignore[assignment]
    melt.series = array_3d
    melt.series = array_4d  # type: ignore[assignment]
    assert_type(melt.simseries, typingtools.TensorFloat)
    assert_type(melt.evalseries, typingtools.TensorFloat)
