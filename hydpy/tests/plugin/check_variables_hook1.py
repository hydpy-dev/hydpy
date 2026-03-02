# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.models import hland_96
    from hydpy.models.hland import hland_model

    h: hland_model.Model
    h96: hland_96.Model
    assert_type(h.parameters, parametertools.Parameters[hland_model.Model])
    assert_type(h96.parameters, parametertools.Parameters[hland_96.Model])
    assert_type(h.sequences, sequencetools.Sequences[hland_model.Model])
    assert_type(h96.sequences, sequencetools.Sequences[hland_96.Model])
