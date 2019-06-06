# -*- coding: utf-8 -*-
"""This module implements functions that prepare test setups."""
# import...
# ...from standard library
from typing import Tuple
import os
import shutil
# ...from HydPy
import hydpy
from hydpy import data
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import testtools
from hydpy.tests import iotesting


def prepare_io_example_1() -> Tuple[devicetools.Nodes, devicetools.Elements]:
    # noinspection PyUnresolvedReferences
    """Prepare an IO example configuration.

    >>> from hydpy.core.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    (1) Prepares a short initialisation period of five days:

    >>> from hydpy import pub
    >>> pub.timegrids
    Timegrids(Timegrid('2000-01-01 00:00:00',
                       '2000-01-05 00:00:00',
                       '1d'))

    (2) Prepares a plain IO testing directory structure:

    >>> pub.sequencemanager.inputdirpath
    'inputpath'
    >>> pub.sequencemanager.fluxdirpath
    'outputpath'
    >>> pub.sequencemanager.statedirpath
    'outputpath'
    >>> pub.sequencemanager.nodedirpath
    'nodepath'
    >>> import os
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     print(sorted(filename for filename in os.listdir('.')
    ...                  if not filename.startswith('_')))
    ['inputpath', 'nodepath', 'outputpath']

    (3) Returns three |Element| objects handling either application model
    |lland_v1| or |lland_v2|, and two |Node| objects handling variables
    `Q` and `T`:

    >>> for element in elements:
    ...     print(element.name, element.model)
    element1 lland_v1
    element2 lland_v1
    element3 lland_v2
    >>> for node in nodes:
    ...     print(node.name, node.variable)
    node1 Q
    node2 T

    (4) Prepares the time series data of the input sequence
    |lland_inputs.Nied|, flux sequence |lland_fluxes.NKor|, and state
    sequence |lland_states.BoWa| for each model instance, and |Sim| for
    each node instance (all values are different), e.g.:

    >>> nied1 = elements.element1.model.sequences.inputs.nied
    >>> nied1.series
    InfoArray([ 0.,  1.,  2.,  3.])
    >>> nkor1 = elements.element1.model.sequences.fluxes.nkor
    >>> nkor1.series
    InfoArray([[ 12.],
               [ 13.],
               [ 14.],
               [ 15.]])
    >>> bowa3 = elements.element3.model.sequences.states.bowa
    >>> bowa3.series
    InfoArray([[ 48.,  49.,  50.],
               [ 51.,  52.,  53.],
               [ 54.,  55.,  56.],
               [ 57.,  58.,  59.]])
    >>> sim2 = nodes.node2.sequences.sim
    >>> sim2.series
    InfoArray([ 64.,  65.,  66.,  67.])

    (5) All sequences carry |numpy.ndarray| objects with (deep) copies
    of the time series data for testing:

    >>> import numpy
    >>> (numpy.all(nied1.series == nied1.testarray) and
    ...  numpy.all(nkor1.series == nkor1.testarray) and
    ...  numpy.all(bowa3.series == bowa3.testarray) and
    ...  numpy.all(sim2.series == sim2.testarray))
    InfoArray(True, dtype=bool)
    >>> bowa3.series[1, 2] = -999.0
    >>> numpy.all(bowa3.series == bowa3.testarray)
    InfoArray(False, dtype=bool)
    """
    from hydpy import TestIO
    TestIO.clear()
    from hydpy.core.filetools import SequenceManager
    hydpy.pub.sequencemanager = SequenceManager()
    with TestIO():
        hydpy.pub.sequencemanager.inputdirpath = 'inputpath'
        hydpy.pub.sequencemanager.fluxdirpath = 'outputpath'
        hydpy.pub.sequencemanager.statedirpath = 'outputpath'
        hydpy.pub.sequencemanager.nodedirpath = 'nodepath'

    hydpy.pub.timegrids = '2000-01-01', '2000-01-05', '1d'

    from hydpy import Node, Nodes, Element, Elements, prepare_model
    node1 = Node('node1')
    node2 = Node('node2', variable='T')
    nodes = Nodes(node1, node2)
    element1 = Element('element1', outlets=node1)
    element2 = Element('element2', outlets=node1)
    element3 = Element('element3', outlets=node1)
    elements = Elements(element1, element2, element3)

    from hydpy.models import lland_v1, lland_v2
    element1.model = prepare_model(lland_v1)
    element2.model = prepare_model(lland_v1)
    element3.model = prepare_model(lland_v2)

    from hydpy.models.lland import ACKER
    for idx, element in enumerate(elements):
        parameters = element.model.parameters
        parameters.control.nhru(idx+1)
        parameters.control.lnk(ACKER)
        parameters.derived.absfhru(10.0)

    with hydpy.pub.options.printprogress(False):
        nodes.prepare_simseries()
        elements.prepare_inputseries()
        elements.prepare_fluxseries()
        elements.prepare_stateseries()

    def init_values(seq, value1_):
        value2_ = value1_ + len(seq.series.flatten())
        values_ = numpy.arange(value1_, value2_, dtype=float)
        seq.testarray = values_.reshape(seq.seriesshape)
        seq.series = seq.testarray.copy()
        return value2_

    import numpy
    value1 = 0
    for subname, seqname in zip(['inputs', 'fluxes', 'states'],
                                ['nied', 'nkor', 'bowa']):
        for element in elements:
            subseqs = getattr(element.model.sequences, subname)
            value1 = init_values(getattr(subseqs, seqname), value1)
    for node in nodes:
        value1 = init_values(node.sequences.sim, value1)

    return nodes, elements


def prepare_full_example_1() -> None:
    """Prepare the complete `LahnH` project for testing.

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import TestIO
    >>> import os
    >>> with TestIO():
    ...     print('root:', *sorted(os.listdir('.')))
    ...     for folder in ('control', 'conditions', 'series'):
    ...         print(f'LahnH/{folder}:',
    ...               *sorted(os.listdir(f'LahnH/{folder}')))
    root: LahnH __init__.py
    LahnH/control: default
    LahnH/conditions: init_1996_01_01_00_00_00
    LahnH/series: input node output temp

    ToDo: Improve, test, and explain this example data set.
    """
    testtools.TestIO.clear()
    shutil.copytree(
        os.path.join(data.__path__[0], 'LahnH'),
        os.path.join(iotesting.__path__[0], 'LahnH'))
    seqpath = os.path.join(iotesting.__path__[0], 'LahnH', 'series')
    for folder in ('output', 'node', 'temp'):
        os.makedirs(os.path.join(seqpath, folder))


def prepare_full_example_2(lastdate='1996-01-05') -> (
        hydpytools.HydPy, hydpy.pub, testtools.TestIO):
    """Prepare the complete `LahnH` project for testing.

    |prepare_full_example_2| calls |prepare_full_example_1|, but also
    returns a readily prepared |HydPy| instance, as well as module
    |pub| and class |TestIO|, for convenience:

    >>> from hydpy.core.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> hp.nodes
    Nodes("dill", "lahn_1", "lahn_2", "lahn_3")
    >>> hp.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3",
             "stream_dill_lahn_2", "stream_lahn_1_lahn_2",
             "stream_lahn_2_lahn_3")
    >>> pub.timegrids
    Timegrids(Timegrid('1996-01-01 00:00:00',
                       '1996-01-05 00:00:00',
                       '1d'))
    >>> from hydpy import classname
    >>> classname(TestIO)
    'TestIO'

    The last date of the initialisation period is configurable:

    >>> hp, pub, TestIO = prepare_full_example_2('1996-02-01')
    >>> pub.timegrids
    Timegrids(Timegrid('1996-01-01 00:00:00',
                       '1996-02-01 00:00:00',
                       '1d'))
    """
    prepare_full_example_1()
    with testtools.TestIO():
        hp = hydpytools.HydPy('LahnH')
        hydpy.pub.timegrids = '1996-01-01', lastdate, '1d'
        hp.prepare_everything()
    return hp, hydpy.pub, testtools.TestIO
