# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    from hydpy.interfaces import aetinterfaces
    from hydpy.models import evap_aet_hbv96, evap_pet_hbv96, hland_96

    main: hland_96.Model

    with main.add_aetmodel_v1(evap_aet_hbv96) as sub_unknown:
        assert_type(sub_unknown, aetinterfaces.AETModel_V1)

    with main.add_aetmodel_v1("evap_aet_hbv69") as sub_wrong:  # type: ignore[arg-type]
        assert_type(sub_wrong, aetinterfaces.AETModel_V1)

    with main.add_aetmodel_v1("evap_pet_hbv96") as sub_wrong:  # type: ignore[arg-type]
        assert_type(sub_wrong, aetinterfaces.AETModel_V1)

    with main.add_aetmodel_v1("evap_aet_hbv96") as sub_aet:
        assert_type(sub_aet, evap_aet_hbv96.Model)
        with sub_aet.add_petmodel_v1("evap_pet_hbv96") as sub_pet:
            assert_type(sub_pet, evap_pet_hbv96.Model)
