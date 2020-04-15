# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import sequencetools


class QUH1(sequencetools.LogSequence):
    """Whole outflow delayed by means of the unit hydrograph UH1 [mm].

    The last value is always set to zero to avoid biased results:

    >>> from hydpy.models.grxjland import *
    >>> from hydpy import pub
    >>> ret = pub.options.warnsimulationstep(False)
    >>> parameterstep('1d')
    >>> simulationstep('1d')
    >>> ret = pub.options.usedefaultvalues(True)
    >>> x4(3.4)
    >>> derived.uh1.update()
    
    logs q9 have initial values of 0.:
    
    >>> logs.quh1
    quh1(0.0, 0.0, 0.0, 0.0)
    >>> logs.quh1(1.0, 2.0, 1.0, 3.0)
    >>> logs.quh1
    quh1(1.0, 2.0, 1.0, 0.0)

    When a wrong number of input values is given, |Q9| distributes
    their sum equally and emits the following warning:

    >>> import warnings
    >>> warnings.filterwarnings("error")
    >>> logs.quh1(1.0, 2.0, 3.0)
    Traceback (most recent call last):
    ...
    UserWarning: Due to the following problem, log sequence `quh1` of \
element `?` handling model `grxjland` could be initialised with a averaged \
value only: While trying to set the value(s) of variable `quh1`, the \
following error occurred: While trying to convert the value(s) \
`(1.0, 2.0, 3.0)` to a numpy ndarray with shape `(4,)` and type \
`float`, the following error occurred: could not broadcast input array \
from shape (3) into shape (4)

    >>> logs.quh1
    quh1(2.0, 2.0, 2.0, 0.0)
    """
    NDIM, NUMERIC, SPAN = 1, False, (0., None)
    INIT = 0

    def __call__(self, *args):
        try:
            sequencetools.LogSequence.__call__(self, *args)
            self.values[-1] = 0.
        except BaseException as exc:
            sequencetools.LogSequence.__call__(
                self, numpy.sum(args)/(self.shape[0]-1))
            self.values[-1] = 0.
            warnings.warn(
                f'Due to the following problem, log sequence '
                f'{objecttools.elementphrase(self)} handling model '
                f'`{self.subseqs.seqs.model}` could be initialised '
                f'with a averaged value only: {exc}')
            

class QUH2(sequencetools.LogSequence):
    """Whole outflow delayed by means of the unit hydrograph UH2 [mm].

    The last value is always set to zero to avoid biased results:

    >>> from hydpy.models.grxjland import *
    >>> from hydpy import pub
    >>> ret = pub.options.warnsimulationstep(False)
    >>> parameterstep('1d')
    >>> simulationstep('1d')
    >>> x4(3.4)
    >>> derived.uh2.update()
    >>> logs.quh2(1.0, 2.0, 1.0, 3.0, 4.0, 6.0, 0.0)
    >>> logs.quh2
    quh2(1.0, 2.0, 1.0, 3.0, 4.0, 6.0, 0.0)

    When a wrong number of input values is given, |Q1| distributes
    their sum equally and emits the following warning:
    >>> import warnings
    >>> warnings.filterwarnings("error")
    >>> logs.quh2(1.0, 2.0, 3.0)
    Traceback (most recent call last):
    ...
    UserWarning: Due to the following problem, log sequence `quh2` of \
element `?` handling model `grxjland` could be initialised with a averaged \
value only: While trying to set the value(s) of variable `quh2`, the \
following error occurred: While trying to convert the value(s) \
`(1.0, 2.0, 3.0)` to a numpy ndarray with shape `(7,)` and type \
`float`, the following error occurred: could not broadcast input array \
from shape (3) into shape (7)

    >>> logs.quh2
    quh2(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0)
    """
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def __call__(self, *args):
        try:
            sequencetools.LogSequence.__call__(self, *args)
            self.values[-1] = 0.
        except BaseException as exc:
            sequencetools.LogSequence.__call__(
                self, numpy.sum(args)/(self.shape[0]-1))
            self.values[-1] = 0.
            warnings.warn(
                f'Due to the following problem, log sequence '
                f'{objecttools.elementphrase(self)} handling model '
                f'`{self.subseqs.seqs.model}` could be initialised '
                f'with a averaged value only: {exc}')
