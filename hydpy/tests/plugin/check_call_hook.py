# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    import numpy

    from hydpy import Date
    from hydpy.auxs import iuhtools
    from hydpy.auxs import ppolytools
    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.models.arma import arma_control
    from hydpy.models.conv import conv_control
    from hydpy.models.conv import conv_derived
    from hydpy.models.dam import dam_control
    from hydpy.models.evap import evap_control
    from hydpy.models.exch import exch_control
    from hydpy.models.hland import hland_control
    from hydpy.models.hland import hland_derived
    from hydpy.models.hland import hland_states
    from hydpy.models.kinw import kinw_control
    from hydpy.models.lland import lland_control
    from hydpy.models.manager import manager_control
    from hydpy.models.manager import manager_derived
    from hydpy.models.musk import musk_control
    from hydpy.models.rconc import rconc_control
    from hydpy.models.whmod import whmod_control
    from hydpy.models import hland_96, lland_knauf, wland_wag

    # NDIM = ?, TYPE = ?
    parameter: parametertools.Parameter
    parameter("x")  # type: ignore[arg-type]
    parameter(True)
    parameter(1, 2)
    parameter([1.0])
    parameter(numpy.ones(2, dtype=numpy.int64))
    parameter(numpy.ones(2, dtype=numpy.bool_))
    parameter([[1.0]])
    parameter([[[1.0]]])
    parameter([[[[1.0]]]])  # type: ignore[arg-type]
    parameter(auxfile="file")
    parameter(auxfile=1)  # type: ignore[call-overload]
    parameter(wrong="file")  # type: ignore[call-overload]
    parameter(1.0, auxfile="file")  # type: ignore[call-overload]
    sequence: sequencetools.StateSequence
    sequence("x")  # type: ignore[arg-type]
    sequence(1.0)
    sequence([[[1.0]]])
    sequence(auxfile="file")  # type: ignore[call-arg]

    # NDIM = 0, TYPE = float
    area: hland_control.Area
    area(1.0)
    area(1)
    area([1.0])  # type: ignore[call-overload]
    area(numpy.ones((), dtype=numpy.float64))  # type: ignore[call-overload]
    area(auxfile="file")
    area(auxfile=1)  # type: ignore[call-overload]
    area(wrong=1.0)  # type: ignore[call-overload]

    # NDIM = 0, TYPE = int
    nmbzones: hland_control.NmbZones
    nmbzones(1)
    nmbzones(True)
    nmbzones(1.0)  # type: ignore[call-overload]

    # NDIM = 0, TYPE = int, TIME = True
    recstep: hland_control.RecStep
    recstep(1)
    recstep(1200.0)
    nmbsteps: rconc_control.NmbSteps
    nmbsteps(4.2)
    nmbsteps("x")  # type: ignore[call-overload]

    # NDIM = 0, TYPE = bool
    resparea: hland_control.RespArea
    resparea(True)
    resparea(1)  # type: ignore[call-overload]

    # NDIM = 1, TYPE = float
    zonearea: hland_control.ZoneArea
    zonearea(1.0)
    zonearea(1.0, 2.0)
    zonearea([1.0, 2.0])
    zonearea(numpy.ones(2, dtype=numpy.float64))
    zonearea([[1.0]])  # type: ignore[list-item]

    # NDIM = 1, TYPE = int
    zonetype: hland_control.ZoneType
    zonetype(1, 2)
    zonetype([1, 2])
    zonetype([1.0])  # type: ignore[list-item]

    # NDIM = 2, TYPE = float
    distances: conv_derived.Distances
    distances(1.0)
    distances([1.0, 2.0])
    distances([1.0, 2.0], [3.0, 4.0])
    distances([[1.0, 2.0], [3.0, 4.0]])
    distances(numpy.ones((2, 2), dtype=numpy.float64))
    distances([[[1.0]]])  # type: ignore[arg-type]

    # NDIM = 2, TYPE = int
    sredorder: hland_derived.SRedOrder
    sredorder([[1, 2]])
    sredorder([[1.0, 2.0]])  # type: ignore[arg-type]

    # NDIM = 2, TYPE = bool
    adjacency: manager_derived.Adjacency
    adjacency([True, False])
    adjacency([[True, False], [False, True]])
    adjacency(numpy.ones((2, 2), dtype=numpy.bool_))
    adjacency([1, 0])  # type: ignore[arg-type]

    # sequences
    sm: hland_states.SM
    sm(1.0)
    sm([1.0, 2.0])
    sm([[1.0]])  # type: ignore[list-item]

    # additional keyword arguments
    inputheights: conv_control.InputHeights
    inputheights(1.0, 2.0)
    inputheights([1.0, 2.0])
    inputheights(auxfile="file")
    inputheights(in1=1.0, in2=2.0)
    inputheights(in1=[1.0])  # type: ignore[call-overload]
    xpoints: exch_control.XPoints  # deprecated model, only the supported form
    xpoints(1.0, 2.0)
    xpoints([1.0, 2.0])  # type: ignore[arg-type]
    xpoints(auxfile="file")  # type: ignore[call-arg]
    ypoints: exch_control.YPoints  # deprecated model, only the supported form
    ypoints(branch1=[1.0, 2.0], branch2=numpy.ones(2, dtype=numpy.float64))
    ypoints(branch1=1.0)  # type: ignore[arg-type]
    ypoints([1.0, 2.0], [3.0, 4.0])  # type: ignore[call-arg]
    kapgrenz: lland_control.KapGrenz
    kapgrenz(1.0, 2.0)
    kapgrenz([[1.0, 2.0], [3.0, 4.0]])
    kapgrenz([[1.0, 2.0], [3.0, "x"]])  # type: ignore[arg-type]
    kapgrenz(option="FK")
    kapgrenz(option="wrong")  # type: ignore[call-overload]
    coefficients: musk_control.Coefficients
    coefficients(0.0, 1.0, 2.0)
    coefficients(0.0, 1.0, "x")  # type: ignore[arg-type]
    coefficients(damp=0.5)
    coefficients(k=1.0, x=0.2)
    coefficients(k=1.0)  # type: ignore[call-overload]

    # framework classes
    seasonal: dam_control.RemoteDischargeMinimum
    seasonal(1.0)
    seasonal(toy_1_1_12=1.0, toy_7_1_12=2.0)
    seasonal(toy_1_1_12="x")  # type: ignore[arg-type]
    seasonal(toy_1=1.0, toy_12_31_23_59_59=2.0)
    seasonal(toy_1_1_12_0_0_0=1.0)  # type: ignore[call-overload]
    seasonal(toy=1.0)  # type: ignore[call-overload]
    seasonal(toy_x=1.0)  # type: ignore[call-overload]
    seasonal(toy_01_1_12=1.0, toy_07_01_00_00_00=2.0)
    seasonal(_1_1_12=1.0)  # type: ignore[deprecated]
    seasonal(toy_001_1_12=1.0)  # type: ignore[deprecated]
    seasonal(something_3_13=1.0)  # type: ignore[deprecated]
    seasonal(_2_30=1.0)  # type: ignore[call-arg]
    seasonal(toy_7_1=1.0, _7_1=2.0)  # type: ignore[call-arg, deprecated]
    seasonal(toy_7_1=1.0, toy_07_01=2.0)  # type: ignore[call-arg]
    seasonal(toy_02_30=1.0)  # type: ignore[call-arg]
    seasonal(**{"_1_1_12": 1.0})  # unpacked dictionary: no check
    seasonal(toy_2_29=1.0, toy_12_31_23_59_59=2.0)
    seasonal(toy_13=1.0)  # type: ignore[call-arg]
    seasonal(toy_0=1.0)  # type: ignore[call-arg]
    seasonal(toy_2_30=1.0)  # type: ignore[call-arg]
    seasonal(toy_4_31=1.0)  # type: ignore[call-arg]
    seasonal(toy_1_0=1.0)  # type: ignore[call-arg]
    seasonal(toy_1_1_24=1.0)  # type: ignore[call-arg]
    seasonal(toy_1_1_0_60=1.0)  # type: ignore[call-arg]
    seasonal(toy_1_1_0_0_60=1.0)  # type: ignore[call-arg]
    seasonal(toy_1_1=1.0, toy_1_1_0_0_0=2.0)  # type: ignore[call-arg]
    seasonal(toy_1=1.0, toy_2=2.0, toy_1_1_0=3.0)  # type: ignore[call-arg]
    leftright: kinw_control.BV
    leftright(left=1.0, right=2.0)
    leftright(l=1.0, r=2.0)
    leftright(left=1.0)  # type: ignore[call-overload]
    commission: dam_control.Commission
    commission(1)
    commission("2000-01-01")
    commission(Date("2000-01-01"))
    commission(1.0)  # type: ignore[call-overload]
    active: manager_control.Active
    active(True)
    active(True, a=False)
    active(a=True, b=False)
    active(a="x")  # type: ignore[call-overload]

    # special parameters
    responses: arma_control.Responses
    responses(((1.0,), (2.0,)))
    responses([[], [1.0]])
    responses(th_0_0=((1.0,), (2.0,)), th_1_0=iuhtools.TranslationDiffusionEquation())
    responses(1.0)  # type: ignore[call-overload]
    responses(((1.0,), (2.0,)), th_1_0=((1.0,), (2.0,)))  # type: ignore[call-overload]
    responses(th_10_25=((1.0,), (2.0,)), th_0_05=((1.0,), (2.0,)))
    responses(th=((1.0,), (2.0,)))  # type: ignore[call-overload]
    responses(th_1_x=((1.0,), (2.0,)))  # type: ignore[call-overload]
    responses(ht_0_0=((1.0,), (2.0,)))  # type: ignore[deprecated]
    responses(_0_0=((1.0,), (2.0,)))  # type: ignore[deprecated]
    responses(th_1=((1.0,), (2.0,)))  # type: ignore[deprecated]
    responses(th_01_0=((1.0,), (2.0,)))  # type: ignore[deprecated]
    responses(th_1_50=((1.0,), (2.0,)))  # type: ignore[deprecated]
    responses(th_1_5=((), ()), th_1_50=((), ()))  # type: ignore[call-arg, deprecated]
    targetrules: exch_control.Rules
    targetrules(ppolytools.PPolys(a=ppolytools.PPoly.from_data([0.0], [0.0])))
    targetrules(toy_1_1_12=ppolytools.PPoly.from_data([0.0], [0.0]))
    targetrules(1.0)  # type: ignore[call-overload]
    ppoly = ppolytools.PPoly.from_data([0.0], [0.0])
    targetrules(_1_1_12=ppoly)  # type: ignore[deprecated]
    targetrules(toy_2_30=ppoly)  # type: ignore[call-arg]
    targetrules(toy_3=ppoly, toy_3_1=ppoly)  # type: ignore[call-arg]

    # zip parameters of main models
    zonearea(field=1.0, forest=2.0)
    zonearea(default=1.0, glacier=2.0)
    zonearea(acre=1.0, woods=2.0)  # type: ignore[call-overload]
    zonearea(field="x")  # type: ignore[call-overload]
    pwmax: lland_control.PWMax
    pwmax(acker=1.0, wasser=2.0)
    pwmax(rhot0=0.2, rhodkrit=0.4)
    pwmax(field=1.0)  # type: ignore[call-overload]
    pwmax(rhot0=0.2)  # type: ignore[call-overload]
    pwmax(rhot0=0.2, rhodkrit=0.4, acker=1.0)  # type: ignore[call-overload]
    pwp: lland_control.PWP
    pwp(relative=0.2)
    pwp(r_dmin=0.2)  # type: ignore[call-overload]
    pwp(relative=0.2, default=1.0)  # type: ignore[call-overload]
    dmin: lland_control.DMin
    dmin(1.0)
    dmin(auxfile="file")
    dmin(default=1.0, acker=2.0)
    dmin(r_dmin=1.0)
    dmin(r_dmin=1.0, acker=2.0)  # type: ignore[call-overload]
    dmin(r_dmax=1.0)  # type: ignore[call-overload]
    dmax: lland_control.DMax
    dmax(r_dmax=1.0)
    dmax(r_dmax=1.0, default=2.0)  # type: ignore[call-overload]

    # zip parameters of submodels (their constants depend on the main model)
    soilmoisturelimit: evap_control.SoilMoistureLimit
    soilmoisturelimit(field=1.0, acker=2.0)  # unknown main model: no check
    hland: hland_96.Model
    with hland.add_aetmodel_v1("evap_aet_hbv96") as aet_hland:
        control_aet = aet_hland.parameters.control
        control_aet.soilmoisturelimit(field=1.0, forest=2.0)
        control_aet.soilmoisturelimit(acker=1.0)  # type: ignore[call-overload]
        control_aet.water(field=True, default=False)
        control_aet.water(field=1.0)  # type: ignore[call-overload]
        with aet_hland.add_petmodel_v1("evap_pet_hbv96") as pet_hland:
            control_pet = pet_hland.parameters.control
            control_pet.evapotranspirationfactor(field=1.0, forest=2.0)
            control_pet.evapotranspirationfactor(acker=1.0)  # type: ignore[call-overload]
            # this adder passes no land types (neither at runtime nor for the
            # plugin), so keyword arguments remain unchecked here:
            with pet_hland.add_tempmodel_v2("meteo_temp_io") as temp_hland:
                control_temp = temp_hland.parameters.control
                control_temp.temperatureaddend(acker=1.0)  # no check
    control_aet.soilmoisturelimit(field=1.0, forest=2.0)
    control_aet.soilmoisturelimit(acker=1.0)  # type: ignore[call-overload]
    control_pet.evapotranspirationfactor(field=1.0, forest=2.0)
    control_pet.evapotranspirationfactor(field=1.0, forest=2.0)
    lland: lland_knauf.Model
    with lland.add_aetmodel_v1("evap_aet_hbv96") as aet_lland:
        # reassigning a variable updates its context:
        control_aet = aet_lland.parameters.control
        control_aet.soilmoisturelimit(acker=1.0, laubw=2.0)
        control_aet.soilmoisturelimit(field=1.0)  # type: ignore[call-overload]
    control_aet.soilmoisturelimit(acker=1.0, laubw=2.0)
    control_aet.soilmoisturelimit(field=1.0)  # type: ignore[call-overload]
    wland: wland_wag.Model
    with wland.add_petmodel_v1("evap_pet_hbv96") as pet_wland:
        regular = pet_wland.parameters.control.regular
        regular.evapotranspirationfactor(conifer=1.0, default=2.0)
        regular.evapotranspirationfactor(forest=1.0)  # type: ignore[call-overload]

    # keyword parameters with fixed entry names (1-dimensional)
    delta: exch_control.Delta
    delta(1.0)
    delta(auxfile="file")
    delta(
        jan=1.0, feb=1.0, mar=1.0, apr=1.0, may=1.0, jun=1.0,
        jul=1.0, aug=1.0, sep=1.0, oct=1.0, nov=1.0, dec=1.0,
    )  # fmt: skip
    delta(jan=1.0, feb=2.0)  # type: ignore[call-arg]
    delta(  # type: ignore[call-arg]
        jan=1.0, feb=1.0, mar=1.0, apr=1.0, may=1.0, jun=1.0,
        jul=1.0, aug=1.0, sep=1.0, oct=1.0, nov=1.0, dec=1.0, wrong=1.0,
    )  # fmt: skip
    delta(jan="x")  # type: ignore[call-arg, call-overload]
    delta(1.0, jan=1.0)  # type: ignore[call-overload]
    delta(**{"jan": 1.0})  # unpacked dictionary: no check

    # keyword parameters with fixed row names (2-dimensional)
    capacity: whmod_control.InterceptionCapacity
    capacity(
        grass=1.0, deciduous=[1.0, 2.0], corn=1.0, conifer=1.0, springwheat=1.0,
        winterwheat=1.0, sugarbeets=1.0, sealed=numpy.ones(12, dtype=numpy.float64),
    )  # fmt: skip
    capacity(grass=1.0)  # type: ignore[call-arg]
    capacity(  # type: ignore[call-arg]
        grass=1.0, deciduous=1.0, corn=1.0, conifer=1.0, springwheat=1.0,
        winterwheat=1.0, sugarbeets=1.0, sealed=1.0, forest=1.0,
    )  # fmt: skip
    capacity(grass=1.0, forest=1.0)  # type: ignore[call-arg]  # missing and unknown
    capacity(auxfile="file", grass=1.0)  # type: ignore[call-overload]
    capacity(grass="x")  # type: ignore[arg-type, call-arg]
    capacity(grass=[[1.0]])  # type: ignore[call-arg, list-item]

    # keyword parameters with row names depending on the main model
    landmonthfactor: evap_control.LandMonthFactor
    landmonthfactor(anything=1.0)  # unknown main model: no check
    with wland.add_petmodel_v1("evap_pet_mlc") as pet_wland_:
        factor = pet_wland_.parameters.control.landmonthfactor
        factor(
            conifer=1.0, decidious=1.0, field=1.0, mixed=1.0, orchard=1.0, pasture=1.0,
            sealed=1.0, soil=1.0, trees=1.0, water=1.0, wetland=1.0, wine=1.0,
        )  # fmt: skip
        factor(field=1.0)  # type: ignore[call-arg]
        factor(  # type: ignore[call-arg]
            conifer=1.0, decidious=1.0, field=1.0, mixed=1.0, orchard=1.0, pasture=1.0,
            sealed=1.0, soil=1.0, trees=1.0, water=1.0, wetland=1.0, wine=1.0,
            acker=1.0,
        )  # fmt: skip
    with hland.add_aetmodel_v1("evap_aet_hbv96") as aet_hland:
        with aet_hland.add_petmodel_v1("evap_pet_mlc") as mlc_hland:
            factor = mlc_hland.parameters.control.landmonthfactor
            factor(field=1.0, forest=1.0, glacier=1.0, ilake=1.0, sealed=1.0)
            factor(field=1.0, conifer=1.0)  # type: ignore[call-arg]
