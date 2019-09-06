# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Input(sequencetools.FluxSequence):
    """Total input [e.g. m³/s]."""
    NDIM, NUMERIC = 0, False


class Outputs(sequencetools.FluxSequence):
    """Branched outputs [e.g. m³/s]."""
    NDIM, NUMERIC = 1, False

    def __repr__(self):
        nodenames = self.subseqs.seqs.model.nodenames
        lines = []
        for (idx, value) in enumerate(self.values):
            line = '%s=%s,' % (nodenames[idx], repr(value))
            if not idx:
                lines.append('outputs('+line)
            else:
                lines.append('        '+line)
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the hbranch model."""
    CLASSES = (Input,
               Outputs)
