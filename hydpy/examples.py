# -*- coding: utf-8 -*-
"""This module implements functions for preparing tutorial projects and
other test data.

.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN
"""
# import...
# ...from standard library
import os
import shutil
from typing import *

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
from hydpy.models import lland

if TYPE_CHECKING:
    from hydpy.core import pubtools
    from hydpy.core import timetools


def prepare_io_example_1() -> Tuple[devicetools.Nodes, devicetools.Elements]:
    """Prepare an IO example configuration for testing purposes.

    Function |prepare_io_example_1| is thought for testing the functioning
    of *HydPy* and thus should be of interest for framework developers only.
    It uses the application models |lland_v1| and |lland_v2|.  Here, we
    apply |prepare_io_example_1| and shortly discuss different aspects of
    the data it generates.

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    (1) It defines a short initialisation period of five days:

    >>> from hydpy import pub
    >>> pub.timegrids
    Timegrids("2000-01-01 00:00:00",
              "2000-01-05 00:00:00",
              "1d")

    (2) It creates a flat IO testing directory structure:

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
    ...     print(sorted(filename for filename in os.listdir(".")
    ...                  if not filename.startswith("_")))
    ['inputpath', 'nodepath', 'outputpath']

    (3) It returns three |Element| objects handling either application model
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

    (4) It generates artificial time series data of the input sequence
    |lland_inputs.Nied|, the flux sequence |lland_fluxes.NKor|, and the
    state sequence |lland_states.BoWa| of each model instance, and the
    |Sim| sequence of each node instance.  For unambiguous test results,
    all generated values are unique:

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

    (5) All sequences carry |numpy.ndarray| objects with (deep) copies
    of the time series data for testing:

    >>> import numpy
    >>> (numpy.all(nied1.series == nied1.testarray) and
    ...  numpy.all(nkor1.series == nkor1.testarray) and
    ...  numpy.all(bowa3.series == bowa3.testarray) and
    ...  numpy.all(sim2.series == sim2.testarray))
    InfoArray(True)
    >>> bowa3.series[1, 2] = -999.0
    >>> numpy.all(bowa3.series == bowa3.testarray)
    InfoArray(False)
    """
    testtools.TestIO.clear()
    hydpy.pub.sequencemanager = filetools.SequenceManager()
    with testtools.TestIO():
        hydpy.pub.sequencemanager.inputdirpath = "inputpath"
        hydpy.pub.sequencemanager.fluxdirpath = "outputpath"
        hydpy.pub.sequencemanager.statedirpath = "outputpath"
        hydpy.pub.sequencemanager.nodedirpath = "nodepath"

    hydpy.pub.timegrids = "2000-01-01", "2000-01-05", "1d"

    node1 = devicetools.Node("node1")
    node2 = devicetools.Node("node2", variable="T")
    nodes = devicetools.Nodes(node1, node2)
    element1 = devicetools.Element("element1", outlets=node1)
    element2 = devicetools.Element("element2", outlets=node1)
    element3 = devicetools.Element("element3", outlets=node1)
    elements = devicetools.Elements(element1, element2, element3)

    element1.model = importtools.prepare_model("lland_v1")
    element2.model = importtools.prepare_model("lland_v1")
    element3.model = importtools.prepare_model("lland_v2")

    for idx, element in enumerate(elements):
        parameters = element.model.parameters
        parameters.control.nhru(idx + 1)
        parameters.control.lnk(lland.ACKER)
        parameters.derived.absfhru(10.0)

    # pylint: disable=not-callable
    # pylint usually understands that all options are callable
    # but, for unknown reasons, not in the following line:
    with hydpy.pub.options.printprogress(False):
        nodes.prepare_simseries()
        elements.prepare_inputseries()
        elements.prepare_fluxseries()
        elements.prepare_stateseries()
    # pylint: enable=not-callable

    def init_values(seq, value1_):
        value2_ = value1_ + len(seq.series.flatten())
        values_ = numpy.arange(value1_, value2_, dtype=float)
        seq.testarray = values_.reshape(seq.seriesshape)
        seq.series = seq.testarray.copy()
        return value2_

    value1 = 0
    for subname, seqname in zip(
        ["inputs", "fluxes", "states"], ["nied", "nkor", "bowa"]
    ):
        for element in elements:
            subseqs = getattr(element.model.sequences, subname)
            value1 = init_values(getattr(subseqs, seqname), value1)
    for node in nodes:
        value1 = init_values(node.sequences.sim, value1)

    return nodes, elements


def prepare_full_example_1(dirpath: Optional[str] = None) -> None:
    """Prepare the `LahnH` example project on disk.

    *HydPy* comes with a complete project data set for the German river
    Lahn, provided by the `German Federal Institute of Hydrology (BfG)`_.
    The Lahn is a medium-sized tributary to the Rhine.  The given project
    configuration agrees with the BfG's forecasting model, using HBV96
    to simulate the inflow of the Rhine's tributaries.
    The catchment is subdivided into four sub-catchments, each one with a
    river gauge (Marburg, Asslar, Leun, Kalkofen) at its outlet.  The
    sub-catchments are further subdivided into a different number of zones.

    .. image:: LahnH.png

    By default, function |prepare_full_example_1| copies the original
    project data into the `iotesting` directory, thought for performing
    automated tests on real-world data.  The following doctest shows
    the generated folder structure:

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
    LahnH/series: input node output temp

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
        dirpath = iotesting.__path__[0]  # type: ignore[attr-defined, name-defined] # pylint: disable=line-too-long
    datapath: str = data.__path__[0]  # type: ignore[attr-defined, name-defined]
    shutil.copytree(os.path.join(datapath, "LahnH"), os.path.join(dirpath, "LahnH"))
    seqpath = os.path.join(dirpath, "LahnH", "series")
    for folder in ("output", "node", "temp"):
        os.makedirs(os.path.join(seqpath, folder))


def prepare_full_example_2(
    lastdate: "timetools.DateConstrArg" = "1996-01-05",
) -> Tuple[hydpytools.HydPy, "pubtools.Pub", Type[testtools.TestIO]]:
    """Prepare the `LahnH` project on disk and in RAM.

    Function |prepare_full_example_2| is an extensions of function
    |prepare_full_example_1|.  Besides preparing the project data of
    the `LahnH` example project, it performs all necessary steps to
    start a simulation run.  Therefore, it returns a readily prepared
    |HydPy| instance, as well as, for convenience, module |pub| and
    class |TestIO|:

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

    Function |prepare_full_example_2| is primarily thought for testing
    and thus does not allow for many configurations except changing the
    end date of the initialisation period:

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
