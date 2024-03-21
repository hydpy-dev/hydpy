# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages

# ...from HydPy
from hydpy.core import sequencetools


class Factor1DSequence(sequencetools.FactorSequence):
    """Base class for 1-dimensional factor subclasses that support aggregation with
    respect to |RelArea|.

    All |Factor1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |RelbodenFeuchte| works:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmb_cells(5)
    >>> nutz_nr(GRAS, WASSER, SOMMERWEIZEN, LAUBWALD, VERSIEGELT)
    >>> f_area(10.0, 20.0, 30.0, 35.0, 5.0)
    >>> area(100.0)
    >>> derived.relarea.update()
    >>> factors.relbodenfeuchte(0.5, 0.2, 0.4, 0.1, 0.6)
    >>> from hydpy import round_
    >>> round_(factors.relbodenfeuchte.average_values())
    0.275
    """

    NDIM, NUMERIC = 1, False

    @property
    def refweights(self):
        return self.subseqs.seqs.model.parameters.derived.relarea


class Flux1DSequence(sequencetools.FluxSequence):
    """Base class for 1-dimensional flux subclasses that support aggregation with
    respect to |RelArea|.

    All |Flux1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |ZuflussBoden| works:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmb_cells(5)
    >>> nutz_nr(GRAS, WASSER, SOMMERWEIZEN, LAUBWALD, VERSIEGELT)
    >>> f_area(10.0, 20.0, 30.0, 35.0, 5.0)
    >>> area(100.0)
    >>> derived.relarea.update()
    >>> fluxes.zuflussboden(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(fluxes.zuflussboden.average_values())
    2.75
    """

    NDIM, NUMERIC = 1, False

    @property
    def refweights(self):
        return self.subseqs.seqs.model.parameters.derived.relarea


class State1DSequence(sequencetools.StateSequence):
    """Base class for 1-dimensional flux subclasses that support aggregation with
    respect to |RelArea|.

    All |State1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |ZuflussBoden| works:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmb_cells(5)
    >>> nutz_nr(GRAS, WASSER, SOMMERWEIZEN, LAUBWALD, VERSIEGELT)
    >>> f_area(10.0, 20.0, 30.0, 35.0, 5.0)
    >>> area(100.0)
    >>> derived.relarea.update()
    >>> states.interzeptionsspeicher(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(states.interzeptionsspeicher.average_values())
    2.75
    """

    NDIM, NUMERIC = 1, False

    @property
    def refweights(self):
        return self.subseqs.seqs.model.parameters.derived.relarea
