# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
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
