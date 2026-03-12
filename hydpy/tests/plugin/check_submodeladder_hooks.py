# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    from hydpy.interfaces import aetinterfaces, routinginterfaces
    from hydpy.models import (
        evap_aet_hbv96,
        evap_pet_hbv96,
        hland_96,
        sw1d_channel,
        sw1d_lias,
        wq_trapeze,
    )

    main1: hland_96.Model

    with main1.add_aetmodel_v1(evap_aet_hbv96) as sub_unknown:
        assert_type(sub_unknown, aetinterfaces.AETModel_V1)

    with main1.add_aetmodel_v1("evap_aet_hbv69") as sub_wrong:  # type: ignore[arg-type]
        assert_type(sub_wrong, aetinterfaces.AETModel_V1)

    with main1.add_aetmodel_v1("evap_pet_hbv96") as sub_wrong:  # type: ignore[arg-type]
        assert_type(sub_wrong, aetinterfaces.AETModel_V1)

    with main1.add_aetmodel_v1("evap_aet_hbv96") as sub_aet:
        assert_type(sub_aet, evap_aet_hbv96.Model)
        with sub_aet.add_petmodel_v1("evap_pet_hbv96") as sub_pet:
            assert_type(sub_pet, evap_pet_hbv96.Model)

    main2: sw1d_channel.Model

    with main2.add_routingmodel_v2(sw1d_lias, position=1) as sub_unknown:
        assert_type(sub_unknown, routinginterfaces.RoutingModel_V2)

    with main2.add_routingmodel_v2(
        "sw1d_sial", position=1  # type: ignore[arg-type]
    ) as sub_wrong:
        assert_type(sub_wrong, routinginterfaces.RoutingModel_V2)

    with main2.add_routingmodel_v2(
        "sw1d_q_in", position=1  # type: ignore[arg-type]
    ) as sub_wrong:
        assert_type(sub_wrong, routinginterfaces.RoutingModel_V2)

    with main2.add_routingmodel_v2("sw1d_lias", position=1) as sub_lias:
        assert_type(sub_lias, sw1d_lias.Model)
        with sub_lias.add_crosssection_v2("wq_trapeze") as sub_trapeze:
            assert_type(sub_trapeze, wq_trapeze.Model)
