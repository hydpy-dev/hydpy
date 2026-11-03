# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type, Callable

    from hydpy.models import evap_aet_morsim, meteo_glob_fao56, wq_trapeze
    from hydpy.models.evap import evap_model

    b: evap_model.Model
    a: evap_aet_morsim.Model

    # short names only for methods with a single version:
    assert_type(b.calc_currentalbedo, Any)  # type: ignore[attr-defined]
    assert_type(b.calc_currentalbedo_v1, Callable[[], None])
    assert_type(b.calc_currentalbedo_v2, Callable[[], None])
    assert_type(a.calc_currentalbedo, Callable[[], None])
    assert_type(a.calc_currentalbedo_v1, Callable[[], None])
    assert_type(a.calc_currentalbedo_v2, Any)  # type: ignore[attr-defined]

    # methods with arguments and return values:
    assert_type(b.return_adjustedwindspeed_v1, Callable[[float], float])
    assert_type(a.return_adjustedwindspeed_v1, Callable[[float], float])

    # auto methods:
    assert_type(b.determine_interceptionevaporation_v2, Callable[[], None])
    assert_type(a.determine_interceptionevaporation_v2, Callable[[], None])

    # interface methods:
    w: wq_trapeze.Model
    assert_type(w.set_wettedarea_v1, Callable[[float], None])

    # reusable methods:
    m: meteo_glob_fao56.Model
    assert_type(m.process_radiation_v1, Callable[[], None])
