# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class PotentialExchange(sequencetools.FluxSequence):
    """The potential bidirectional water exchange [m³/s]."""

    NDIM, NUMERIC = 0, False


class ActualExchange(sequencetools.FluxSequence):
    """The actual bidirectional water exchange [m³/s]."""

    NDIM, NUMERIC = 0, False


class OriginalInput(sequencetools.FluxSequence):
    """Unadjusted total input [e.g. m³/s]."""

    NDIM, NUMERIC = 0, False


class AdjustedInput(sequencetools.FluxSequence):
    """Adjusted total input [e.g. m³/s]."""

    NDIM, NUMERIC = 0, False


class Outputs(sequencetools.FluxSequence):
    """Branched outputs [e.g. m³/s]."""

    NDIM, NUMERIC = 1, False

    def __repr__(self) -> str:
        names = self.subseqs.seqs.model.nodenames
        lines = []
        for idx, (name, values) in enumerate(zip(names, self.values)):
            line = f"{name}={repr(values)},"
            if not idx:
                lines.append(f"outputs({line}")
            else:
                lines.append(f"        {line}")
        lines[-1] = f"{lines[-1][:-1]})"
        return "\n".join(lines)
