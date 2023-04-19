# -*- coding: utf-8 -*-
"""This module provides functions for preparing tutorial projects and other test data.

.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN
"""
# import...
# ...from standard library
from __future__ import annotations
import os
import shutil

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import data
from hydpy.core import devicetools
from hydpy.core import importtools
from hydpy.core import filetools
from hydpy.core import hydpytools
from hydpy.core import testtools
from hydpy.tests import iotesting
from hydpy.models import hland
from hydpy.models import lland
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import pubtools
    from hydpy.core import sequencetools
    from hydpy.core import timetools

    class TestIOSequence(sequencetools.IOSequence):
        """|IOSequence| subclass for testing purposes."""

        testarray: NDArrayFloat
        descr_device = "just_for_testing"
        descr_sequence = "just_for_testing"


def prepare_io_example_1() -> Tuple[devicetools.Nodes, devicetools.Elements]:
    """Prepare an IO example configuration for testing purposes.

    Function |prepare_io_example_1| is thought for testing the functioning of *HydPy*
    and thus should be of interest for framework developers only.  It uses the
    application models |lland_v1|, |lland_v3|, and |hland_v1|.  Here, we apply
    |prepare_io_example_1| and shortly discuss different aspects of its generated data.

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    (1) It defines a short initialisation period of five days:

    >>> from hydpy import pub
    >>> pub.timegrids
    Timegrids("2000-01-01 00:00:00",
              "2000-01-05 00:00:00",
              "1d")

    (2) It prepares an empty directory for IO testing:

    >>> import os
    >>> from hydpy import repr_, TestIO
    >>> with TestIO():  # doctest: +ELLIPSIS
    ...     repr_(pub.sequencemanager.currentpath)
    ...     os.listdir("project/series/default")
    '...iotesting/project/series/default'
    []

    (3) It returns four |Element| objects handling either application model |lland_v1|
    |lland_v3|, or |hland_v1|, and two |Node| objects handling variables `Q` and `T`:

    >>> for element in elements:
    ...     print(element.name, element.model)
    element1 lland_v1
    element2 lland_v1
    element3 lland_v3
    element4 hland_v1
    >>> for node in nodes:
    ...     print(node.name, node.variable)
    node1 Q
    node2 T

    (4) It generates artificial time series data for the input sequence
    |lland_inputs.Nied|, the flux sequence |lland_fluxes.NKor|, and the state sequence
    |lland_states.BoWa| of each |lland| model instance, the state sequence
    |hland_states.SP| of the |hland_v1| model instance, and the |Sim| sequence of each
    node instance.  For precise test results, all generated values are unique:

    >>> nied1 = elements.element1.model.sequences.inputs.nied
    >>> nied1.series
    InfoArray([0., 1., 2., 3.])
    >>> nkor1 = elements.element1.model.sequences.fluxes.nkor
    >>> nkor1.series
    InfoArray([[12.],
               [13.],
               [14.],
               [15.]])
    >>> bowa3 = elements.element3.model.sequences.states.bowa
    >>> bowa3.series
    InfoArray([[48., 49., 50.],
               [51., 52., 53.],
               [54., 55., 56.],
               [57., 58., 59.]])
    >>> sim2 = nodes.node2.sequences.sim
    >>> sim2.series
    InfoArray([64., 65., 66., 67.])
    >>> sp4 = elements.element4.model.sequences.states.sp
    >>> sp4.series
    InfoArray([[[68., 69., 70.],
                [71., 72., 73.]],
    <BLANKLINE>
               [[74., 75., 76.],
                [77., 78., 79.]],
    <BLANKLINE>
               [[80., 81., 82.],
                [83., 84., 85.]],
    <BLANKLINE>
               [[86., 87., 88.],
                [89., 90., 91.]]])

    (5) All sequences carry |numpy.ndarray| objects with (deep) copies of the
    time-series data for testing:

    >>> import numpy
    >>> (numpy.all(nied1.series == nied1.testarray) and
    ...  numpy.all(nkor1.series == nkor1.testarray) and
    ...  numpy.all(bowa3.series == bowa3.testarray) and
    ...  numpy.all(sim2.series == sim2.testarray) and
    ...  numpy.all(sp4.series == sp4.testarray))
    InfoArray(True)
    >>> bowa3.series[1, 2] = -999.0
    >>> numpy.all(bowa3.series == bowa3.testarray)
    InfoArray(False)
    """
    testtools.TestIO.clear()

    hydpy.pub.projectname = "project"
    hydpy.pub.sequencemanager = filetools.SequenceManager()
    with testtools.TestIO():
        os.makedirs("project/series/default")

    hydpy.pub.timegrids = "2000-01-01", "2000-01-05", "1d"

    node1 = devicetools.Node("node1")
    node2 = devicetools.Node("node2", variable="T")
    nodes = devicetools.Nodes(node1, node2)
    element1 = devicetools.Element("element1", outlets=node1)
    element2 = devicetools.Element("element2", outlets=node1)
    element3 = devicetools.Element("element3", outlets=node1)
    element4 = devicetools.Element("element4", outlets=node1)
    elements_lland = devicetools.Elements(element1, element2, element3)
    elements = elements_lland + element4

    element1.model = importtools.prepare_model("lland_v1")
    element2.model = importtools.prepare_model("lland_v1")
    element3.model = importtools.prepare_model("lland_v3")
    element4.model = importtools.prepare_model("hland_v1")

    for idx, element in enumerate(elements_lland):
        parameters = element.model.parameters
        parameters.control.nhru(idx + 1)
        parameters.control.lnk(lland.ACKER)
        parameters.derived.absfhru(10.0)
    control = element4.model.parameters.control
    control.nmbzones(3)
    control.sclass(2)
    control.zonetype(hland.FIELD)
    control.zonearea.values = 10.0

    with hydpy.pub.options.printprogress(False):
        nodes.prepare_simseries(allocate_ram=False)  # ToDo: add option "reset"
        nodes.prepare_simseries(allocate_ram=True)
        elements.prepare_inputseries(allocate_ram=False)
        elements.prepare_inputseries(allocate_ram=True)
        elements.prepare_factorseries(allocate_ram=False)
        elements.prepare_factorseries(allocate_ram=True)
        elements.prepare_fluxseries(allocate_ram=False)
        elements.prepare_fluxseries(allocate_ram=True)
        elements.prepare_stateseries(allocate_ram=False)
        elements.prepare_stateseries(allocate_ram=True)

    def init_values(seq: TestIOSequence, value1_: float) -> float:
        value2_ = value1_ + len(seq.series.flatten())
        values_ = numpy.arange(value1_, value2_, dtype=float)
        seq.testarray = values_.reshape(seq.seriesshape)
        seq.series = seq.testarray.copy()
        return value2_

    value1 = 0.0
    for subname, seqname in zip(
        ["inputs", "fluxes", "states"], ["nied", "nkor", "bowa"]
    ):
        for element in elements_lland:
            subseqs = getattr(element.model.sequences, subname)
            value1 = init_values(getattr(subseqs, seqname), value1)
    for node in nodes:
        value1 = init_values(node.sequences.sim, value1)  # type: ignore[arg-type]
    init_values(element4.model.sequences.states.sp, value1)  # type: ignore[arg-type]

    return nodes, elements


def prepare_full_example_1(dirpath: Optional[str] = None) -> None:
    """Prepare the `LahnH` example project on disk.

    *HydPy* comes with a complete project data set for the German river Lahn, provided
    by the `German Federal Institute of Hydrology (BfG)`_.  The Lahn is a medium-sized
    tributary to the Rhine.  The given project configuration agrees with the BfG's
    forecasting model, using HBV96 to simulate the inflow of the Rhine's tributaries.
    The catchment consists of four sub-catchments, each one with a river gauge (Marburg,
    Asslar, Leun, Kalkofen) at its outlet.  The sub-catchments consists of a different
    number of zones.

    .. image:: LahnH.png

    By default, function |prepare_full_example_1| copies the original project data into
    the `iotesting` directory, thought for performing automated tests on real-world
    data.  The following doctest shows the generated folder structure:

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import TestIO
    >>> import os
    >>> with TestIO():
    ...     print("root:", *sorted(os.listdir(".")))
    ...     for folder in ("control", "conditions", "series"):
    ...         print(f"LahnH/{folder}:",
    ...               *sorted(os.listdir(f"LahnH/{folder}")))
    root: LahnH __init__.py
    LahnH/control: default
    LahnH/conditions: init_1996_01_01_00_00_00
    LahnH/series: default

    Pass an alternative path if you prefer to work in another directory:

    .. testsetup::

        >>> "LahnH" in os.listdir(".")
        False

    >>> prepare_full_example_1(dirpath=".")

    .. testsetup::

        >>> "LahnH" in os.listdir(".")
        True
        >>> import shutil
        >>> shutil.rmtree("LahnH")
    """
    if dirpath is None:
        testtools.TestIO.clear()
        dirpath = iotesting.__path__[0]
    datapath: str = data.__path__[0]
    shutil.copytree(os.path.join(datapath, "LahnH"), os.path.join(dirpath, "LahnH"))


def prepare_full_example_2(
    lastdate: timetools.DateConstrArg = "1996-01-05",
) -> Tuple[hydpytools.HydPy, pubtools.Pub, Type[testtools.TestIO]]:
    """Prepare the `LahnH` project on disk and in RAM.

    Function |prepare_full_example_2| is an extensions of function
    |prepare_full_example_1|.  Besides preparing the project data of the `LahnH`
    example project, it performs all necessary steps to start a simulation run.
    Therefore, it returns a readily prepared |HydPy| instance, as well as, for
    convenience, module |pub| and class |TestIO|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> hp.nodes
    Nodes("dill", "lahn_1", "lahn_2", "lahn_3")
    >>> hp.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3",
             "stream_dill_lahn_2", "stream_lahn_1_lahn_2",
             "stream_lahn_2_lahn_3")
    >>> pub.timegrids
    Timegrids("1996-01-01 00:00:00",
              "1996-01-05 00:00:00",
              "1d")
    >>> from hydpy import classname
    >>> classname(TestIO)
    'TestIO'

    Function |prepare_full_example_2| is primarily thought for testing and thus does
    not allow for many configurations except changing the end date of the
    initialisation period:

    >>> hp, pub, TestIO = prepare_full_example_2("1996-02-01")
    >>> pub.timegrids
    Timegrids("1996-01-01 00:00:00",
              "1996-02-01 00:00:00",
              "1d")
    """
    prepare_full_example_1()
    with testtools.TestIO():
        hp = hydpytools.HydPy("LahnH")
        hydpy.pub.timegrids = "1996-01-01", lastdate, "1d"
        hp.prepare_everything()
    return hp, hydpy.pub, testtools.TestIO
