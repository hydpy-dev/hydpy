# pylint: disable=missing-module-docstring

if __name__ == "__main__":

    from typing import assert_type

    from hydpy import prepare_model
    from hydpy.core import modeltools
    from hydpy.models import hland, hland_96
    from hydpy.models.hland import hland_model

    prepare_model("hland_69")  # type: ignore[arg-type]

    assert_type(prepare_model(hland), modeltools.Model)
    assert_type(prepare_model("hland"), hland_model.Model)
    assert_type(prepare_model("hland_96"), hland_96.Model)
