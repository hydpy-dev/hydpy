# -*- coding: utf-8 -*-
"""This module provides features for executing *HydPy* workflows based on XML
configuration files.

.. _HydPy release: https://github.com/hydpy-dev/hydpy/releases
.. _`OpenDA`: https://www.openda.org/

At the heart of module |xmltools| lies function |run_simulation|, thought to be applied
via a command line (see the documentation on script |hyd| for further information).
|run_simulation| expects that the *HydPy* project you want to work with is available in
your current working directory and contains an XML configuration file (as
`single_run.xml` in the example project folder `HydPy-H-Lahn`).  This configuration
file must agree with the XML schema `HydPyConfigSingleRun.xsd`, which is available in
the :ref:`configuration` subpackage and separately downloadable for each `HydPy
release`_.  If you did implement new or changed existing models, you have to update
this schema file.  *HydPy* does this automatically through its setup mechanism (see the
documentation on class |XSDWriter|).

To show how to apply |run_simulation| via a command line, we first copy the
`HydPy-H-Lahn` project into the `iotesting` folder by calling the function
|prepare_full_example_1|:

>>> from hydpy.core.testtools import prepare_full_example_1
>>> prepare_full_example_1()

Running the simulation requires defining the main script (`hyd.py`), the function
specifying the actual workflow (`run_simulation`), the name of the project of interest
(`HydPy-H-Lahn`), and the name of the relevant XML configuration file
(`single_run.xml`).  We pass the required text to function |run_subprocess| of module
subprocess to simulate using the command line:

>>> from hydpy import run_subprocess, TestIO
>>> import subprocess
>>> with TestIO():  # doctest: +ELLIPSIS
...     result = run_subprocess("hyd.py run_simulation HydPy-H-Lahn single_run.xml")
Start HydPy project `HydPy-H-Lahn` (...).
Read configuration file `single_run.xml` (...).
Interpret the defined options (...).
Interpret the defined period (...).
Read all network files (...).
Activate the selected network (...).
Read the required control files (...).
Read the required condition files (...).
Read the required time series files (...).
Perform the simulation run (...).
Write the desired condition files (...).
Write the desired time series files (...).

As defined by the XML configuration file, the simulation started on the first and
ended on the sixth of January 1996.  The following example shows the read initial
conditions and the written final conditions of sequence |hland_states.SM| for the
12 hydrological response units of the subcatchment `land_dill_assl`:

>>> with TestIO():
...     filepath = "HydPy-H-Lahn/conditions/init_1996_01_01_00_00_00/land_dill_assl.py"
...     with open(filepath) as file_:
...         print("".join(file_.readlines()[10:12]))
...     filepath = "HydPy-H-Lahn/conditions/init_1996_01_06/land_dill_assl.py"
...     with open(filepath) as file_:
...         print("".join(file_.readlines()[10:13]))
sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
   222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)
<BLANKLINE>
sm(191.065482, 187.420409, 205.624741, 202.683004, 217.592014,
   215.326441, 227.312224, 225.578811, 235.104658, 233.744139,
   241.326832, 240.265835)
<BLANKLINE>

The intermediate soil moisture values have been stored in a NetCDF file called
`hland_96_state_sm.nc`:

>>> import numpy
>>> from hydpy import print_vector
>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset("HydPy-H-Lahn/series/soildata/hland_96_state_sm.nc")
...     chars2str(query_variable(ncfile, "station_id")[:].data)[:3]
...     print_vector(query_variable(ncfile, "hland_96_state_sm")[:, 0])
['land_dill_assl_0', 'land_dill_assl_1', 'land_dill_assl_2']
184.692176, 189.887226, 191.919177, 191.439738, 191.065482
>>> ncfile.close()

Spatially averaged time series values have been stored in files ending with the suffix
`_mean`:

>>> import time
>>> time.sleep(10)

>>> with TestIO(clear_all=True):
...     print_vector(
...         numpy.load("HydPy-H-Lahn/series/averages/lahn_marb_sim_q_mean.npy")[13:]
...     )
9.863194, 12.538947, 17.996259, 17.534, 13.948004
"""
# import...
# ...from standard library
from __future__ import annotations
import collections
import contextlib
import copy
import itertools
import os
import warnings
from xml.etree import ElementTree

# ...from HydPy
import hydpy
from hydpy import conf
from hydpy import config
from hydpy import models
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import hydpytools
from hydpy.core import importtools
from hydpy.core import itemtools
from hydpy.core import objecttools
from hydpy.core import selectiontools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.exe import commandtools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    import netCDF4 as netcdf4
    import xmlschema
    from hydpy.core import modeltools
    from hydpy.core import variabletools
else:
    netcdf4 = exceptiontools.OptionalImport(
        "netcdf4", ["netCDF4", "h5netcdf.legacyapi"], locals()
    )
    xmlschema = exceptiontools.OptionalImport("xmlschema", ["xmlschema"], locals())

_TypeSetOrAddOrMultiplyItem = TypeVar(
    "_TypeSetOrAddOrMultiplyItem",
    itemtools.SetItem,
    itemtools.AddItem,
    itemtools.MultiplyItem,
)
_TypeGetOrChangeItem = TypeVar(
    "_TypeGetOrChangeItem", itemtools.GetItem, itemtools.ChangeItem, itemtools.SetItem
)

namespace = (
    "{https://github.com/hydpy-dev/hydpy/releases/download/your-hydpy-version/"
    "HydPyConfigBase.xsd}"
)
_ITEMGROUP2ITEMCLASS = {
    "setitems": itemtools.SetItem,
    "additems": itemtools.AddItem,
    "multiplyitems": itemtools.MultiplyItem,
    "getitems": itemtools.GetItem,
}


@overload
def find(
    root: ElementTree.Element, name: str, optional: Literal[True] = True
) -> Optional[ElementTree.Element]:
    """Optional version of function |find|."""


@overload
def find(
    root: ElementTree.Element, name: str, optional: Literal[False]
) -> ElementTree.Element:
    """Non-optional version of function |find|."""


def find(
    root: ElementTree.Element, name: str, optional: Literal[True, False] = True
) -> Optional[ElementTree.Element]:
    """Return the first XML element with the given name found in the given XML root.

    >>> from hydpy.auxs.xmltools import find, XMLInterface
    >>> from hydpy.data import make_filepath
    >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
    >>> find(interface.root, "timegrid").tag.endswith("timegrid")
    True

    By default, function |find| returns |None| in case the required element is missing:

    >>> find(interface.root, "wrong")

    Set the argument `optional` to |False| to let function |find| raise errors instead:

    >>> find(interface.root, "wrong", optional=False)
    Traceback (most recent call last):
    ...
    AttributeError: The actual XML element `config` does not define a XML subelement \
named `wrong`.  Please make sure your XML file follows the relevant XML schema.
    """
    element = root.find(f"{namespace}{name}")
    if element is None and not optional:
        raise AttributeError(
            f"The actual XML element `{root.tag.rsplit('}')[-1]}` does not define a "
            f"XML subelement named `{name}`.  Please make sure your XML file follows "
            f"the relevant XML schema."
        )
    return element


def _query_selections(xmlelement: ElementTree.Element) -> selectiontools.Selections:
    selections = []
    text = xmlelement.text
    assert text is not None
    for name in text.split():
        try:
            selections.append(getattr(hydpy.pub.selections, name))
        except AttributeError:
            raise NameError(
                f"The XML configuration file tries to define a selection using the "
                f"text `{name}`, but the actual project does not handle such a "
                f"`Selection` object."
            ) from None
    return selectiontools.Selections(*selections)


def strip(name: str) -> str:
    """Remove the XML namespace from the given string and return it.

    >>> from hydpy.auxs.xmltools import strip
    >>> strip("{https://github.com/something.xsd}something")
    'something'
    """
    return name.split("}")[-1]


class PrepareSeriesArguments(NamedTuple):
    """Helper class that determines and provides the arguments for function
    |IOSequence.prepare_series|."""

    allocate_ram: bool
    read_jit: bool
    write_jit: bool

    @classmethod
    def from_xmldata(
        cls, is_reader: bool, is_input: bool, prefer_ram: bool
    ) -> PrepareSeriesArguments:
        """Create a |PrepareSeriesArguments| object based on the (already prepared)
        information of an XML file.

        Meaning of the arguments:
         * is_reader: is the current XML-Element responsible for reading (or writing)?
         * is_input: serve the addressed sequences as inputs (or outputs)?
         * prefer_ram: prefer to handle time series data in RAM (or read and write it
           just in time)?

        >>> from hydpy.auxs.xmltools import PrepareSeriesArguments
        >>> from_xmldata = PrepareSeriesArguments.from_xmldata

        Test cases for reading input data:

        >>> from_xmldata(is_reader=True, is_input=True, prefer_ram=True)
        PrepareSeriesArguments(allocate_ram=True, read_jit=False, write_jit=False)

        >>> from_xmldata(is_reader=True, is_input=True, prefer_ram=False)
        PrepareSeriesArguments(allocate_ram=False, read_jit=True, write_jit=False)

        Attempting to read output data results in an |AssertionError| (disallowed by
        all available XML schema files):

        >>> from_xmldata(is_reader=True, is_input=False, prefer_ram=True)
        Traceback (most recent call last):
        ...
        AssertionError: reading output values is disallowed

        >>> from_xmldata(is_reader=True, is_input=False, prefer_ram=False)
        Traceback (most recent call last):
        ...
        AssertionError: reading output values is disallowed

        Test cases for writing input data (this is for the rare case where an
        external tool like `OpenDA`_ provides or modifies the input data in RAM, and we
        want to write it to a file for documentation purposes):

        >>> from_xmldata(is_reader=False, is_input=True, prefer_ram=True)
        PrepareSeriesArguments(allocate_ram=True, read_jit=False, write_jit=False)

        >>> from_xmldata(is_reader=False, is_input=True, prefer_ram=False)
        PrepareSeriesArguments(allocate_ram=True, read_jit=False, write_jit=True)

        Test cases for writing output data:

        >>> from_xmldata(is_reader=False, is_input=False, prefer_ram=True)
        PrepareSeriesArguments(allocate_ram=True, read_jit=False, write_jit=False)

        >>> from_xmldata(is_reader=False, is_input=False, prefer_ram=False)
        PrepareSeriesArguments(allocate_ram=False, read_jit=False, write_jit=True)

        """
        is_writer = not is_reader
        is_output = not is_input
        prefer_jit = not prefer_ram
        assert not (is_reader and is_output), "reading output values is disallowed"
        return PrepareSeriesArguments(
            allocate_ram=prefer_ram or (is_input and is_writer),
            read_jit=is_reader and prefer_jit,
            write_jit=is_writer and prefer_jit,
        )


def run_simulation(projectname: str, xmlfile: str) -> None:
    """Perform a *HydPy* workflow according to the given XML configuration file
    available in the given project's directory.

    Function |run_simulation| is a "script function".  We explain its normal usage
    in the main documentation on module |xmltools|.
    """
    write = commandtools.print_textandtime
    hydpy.pub.options.printprogress = False
    write(f"Start HydPy project `{projectname}`")
    hp = hydpytools.HydPy(projectname)
    write(f"Read configuration file `{xmlfile}`")
    interface = XMLInterface(xmlfile)
    write("Interpret the defined options")
    interface.update_options()
    hydpy.pub.options.printprogress = False
    write("Interpret the defined period")
    interface.update_timegrids()
    write("Read all network files")
    interface.network_io.prepare_network()
    write("Create the custom selections (if defined)")
    interface.update_selections()
    write("Activate the selected network")
    hp.update_devices(selection=interface.fullselection, silent=True)
    write("Read the required control files")
    interface.control_io.prepare_models()
    write("Read the required condition files")
    interface.conditions_io.load_conditions()
    write("Read the required time series files")
    series_io = interface.series_io
    series_io.prepare_series()
    series_io.load_series()
    write("Perform the simulation run")
    with series_io.modify_inputdir(), series_io.modify_outputdir():
        hp.simulate()
    write("Write the desired condition files")
    interface.conditions_io.save_conditions()
    write("Write the desired time series files")
    series_io.save_series()


class XMLBase:
    """Base class for the concrete classes |XMLInterface|, |XMLConditions|,
    |XMLSeries|, and |XMLSubseries|.

    Subclasses of |XMLBase| support iterating XML subelements while skipping those
    named `selections`:

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy.data import make_filepath
    >>> interface = XMLInterface("multiple_runs.xml", make_filepath("HydPy-H-Lahn"))
    >>> itemgroup = interface.exchange.itemgroups[1]
    >>> for element in itemgroup:
    ...     print(strip(element.tag))
    hland_96
    rconc_uh
    >>> for element in itemgroup.models[0].subvars[0].vars[0]:
    ...     print(strip(element.tag))
    name
    level
    """

    root: ElementTree.Element

    @property
    def name(self) -> str:
        """Apply function |strip| to the root of the object of the |XMLBase| subclass.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> interface.name
        'config'
        >>> interface.series_io.readers[0].name
        'reader'
        """
        return strip(self.root.tag)

    @overload
    def find(
        self, name: str, optional: Literal[True] = True
    ) -> Optional[ElementTree.Element]:
        """Optional version of method |XMLBase.find|."""

    @overload
    def find(self, name: str, optional: Literal[False]) -> ElementTree.Element:
        """Non-optional version of function |XMLBase.find|."""

    def find(
        self, name: str, optional: Literal[True, False] = True
    ) -> Optional[ElementTree.Element]:
        """Apply function |find| to the root of the object of the |XMLBase| subclass.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> interface.find("timegrid").tag.endswith("timegrid")
        True

        >>> interface.find("wrong")

        >>> interface.find("wrong", optional=False)
        Traceback (most recent call last):
        ...
        AttributeError: The actual XML element `config` does not define a XML \
subelement named `wrong`.  Please make sure your XML file follows the relevant XML \
schema.
        """
        return find(self.root, name, optional)

    def __iter__(self) -> Iterator[ElementTree.Element]:
        for element in self.root:
            name = strip(element.tag)
            if name != "selections":
                yield element


class XMLInterface(XMLBase):
    """An interface to XML configuration files that are valid concerning schema file
    `HydPyConfigSingleRun.xsd` or `HydPyConfigMultipleRuns.xsd`.

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy.data import make_filepath
    >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
    >>> interface.root.tag
    '{https://github.com/hydpy-dev/hydpy/releases/download/your-hydpy-version/\
HydPyConfigSingleRun.xsd}config'
    >>> interface = XMLInterface('multiple_runs.xml', make_filepath('HydPy-H-Lahn'))
    >>> interface.root.tag
    '{https://github.com/hydpy-dev/hydpy/releases/download/your-hydpy-version/\
HydPyConfigMultipleRuns.xsd}config'
    >>> XMLInterface('wrongfilepath.xml', 'wrongdir')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to parse the XML configuration file \
...wrongfilepath.xml, the following error occurred: \
[Errno 2] No such file or directory: '...wrongfilepath.xml'
    """

    def __init__(self, filename: str, directory: Optional[str] = None) -> None:
        if directory is None:
            directory = hydpy.pub.projectname
        self.filepath = os.path.abspath(os.path.join(directory, filename))
        try:
            self.root = ElementTree.parse(self.filepath).getroot()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to parse the XML configuration file " f"{self.filepath}"
            )

    def validate_xml(self) -> None:
        """Raise an error if the actual XML does not agree with one of the available
        schema files.

        # ToDo: should it be accompanied by a script function?

        The first example relies on a distorted version of the configuration file
        `single_run.xml`:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import TestIO, xml_replace
        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> import os
        >>> with TestIO():  # doctest: +ELLIPSIS
        ...     xml_replace("HydPy-H-Lahn/single_run",
        ...                 firstdate="1996-01-32T00:00:00")
        template file: HydPy-H-Lahn/single_run.xmlt
        target file: HydPy-H-Lahn/single_run.xml
        replacements:
          config_start --> <...HydPyConfigBase.xsd"
                      ...HydPyConfigSingleRun.xsd"> (default argument)
          firstdate --> 1996-01-32T00:00:00 (given argument)
          zip_ --> false (default argument)
          config_end --> </hpcsr:config> (default argument)
        >>> with TestIO():
        ...     interface = XMLInterface("single_run.xml", "HydPy-H-Lahn")
        >>> interface.validate_xml()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        xmlschema.validators.exceptions.XMLSchemaDecodeError: While trying to \
validate XML file `...single_run.xml`, the following error occurred: failed \
validating '1996-01-32T00:00:00' with XsdAtomicBuiltin(name='xs:dateTime')...
        ...
        Reason: day is out of range for month
        ...
        Schema component:
        ...
        Instance:
        ...
          <firstdate xmlns="https://github.com/hydpy-dev/hydpy/releases/\
download/your-hydpy-version/HydPyConfigBase.xsd">1996-01-32T00:00:00</firstdate>
        ...
        Path: /hpcsr:config/timegrid/firstdate
        ...

        In the second example, we examine a correct configuration file:

        >>> with TestIO():  # doctest: +ELLIPSIS
        ...     xml_replace("HydPy-H-Lahn/single_run")
        ...     interface = XMLInterface("single_run.xml", "HydPy-H-Lahn")
        template file: HydPy-H-Lahn/single_run.xmlt
        target file: HydPy-H-Lahn/single_run.xml
        replacements:
          config_start --> <...HydPyConfigBase.xsd"
                      ...HydPyConfigSingleRun.xsd"> (default argument)
          firstdate --> 1996-01-01T00:00:00 (default argument)
          zip_ --> false (default argument)
          config_end --> </hpcsr:config> (default argument)
        >>> interface.validate_xml()

        The XML configuration file must correctly refer to the corresponding schema
        file:

        >>> with TestIO():
        ...     xml_replace("HydPy-H-Lahn/single_run",
        ...                 config_start="<config>",
        ...                 config_end="</config>")
        ...     interface = XMLInterface("single_run.xml", "HydPy-H-Lahn")
        template file: HydPy-H-Lahn/single_run.xmlt
        target file: HydPy-H-Lahn/single_run.xml
        replacements:
          config_start --> <config> (given argument)
          firstdate --> 1996-01-01T00:00:00 (default argument)
          zip_ --> false (default argument)
          config_end --> </config> (given argument)
        >>> interface.validate_xml()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to validate XML file `...single_run.xml`, \
the following error occurred: Configuration file `single_run.xml` does not \
correctly refer to one of the available XML schema files \
(HydPyConfigSingleRun.xsd and HydPyConfigMultipleRuns.xsd).

        XML files based on `HydPyConfigMultipleRuns.xsd` can be validated as well:

        >>> with TestIO():
        ...     interface = XMLInterface("multiple_runs.xml", "HydPy-H-Lahn")
        >>> interface.validate_xml()
        """
        try:
            filenames = ("HydPyConfigSingleRun.xsd", "HydPyConfigMultipleRuns.xsd")
            for name in filenames:
                if name in self.root.tag:
                    schemafile = name
                    break
            else:
                raise RuntimeError(
                    f"Configuration file `{os.path.split(self.filepath)[-1]}` does "
                    f"not correctly refer to one of the available XML schema files "
                    f"({objecttools.enumeration(filenames)})."
                )
            confpath: str = conf.__path__[0]
            schemapath = os.path.join(confpath, schemafile)
            schema = xmlschema.XMLSchema(schemapath)
            schema.validate(self.filepath)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to validate XML file `{self.filepath}`"
            )

    def update_options(self) -> None:
        """Update the |Options| object available in the |pub| module with the values
        defined in the `options` XML element.

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.timegrids
            >>> del pub.options.simulationstep

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import pub
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> pub.options.ellipsis = 0
        >>> pub.options.parameterstep = "1h"
        >>> pub.options.printprogress = True
        >>> pub.options.reprdigits = -1
        >>> pub.options.utcoffset = -60
        >>> pub.options.timestampleft = False
        >>> pub.options.warnsimulationstep = 0
        >>> interface.update_options()
        >>> pub.options
        Options(
            checkseries -> TRUE
            ellipsis -> 0
            parameterstep -> Period("1d")
            printprogress -> FALSE
            reprdigits -> 6
            simulationstep -> Period()
            timestampleft -> TRUE
            trimvariables -> TRUE
            usecython -> TRUE
            usedefaultvalues -> FALSE
            utclongitude -> 15
            utcoffset -> 60
            warnmissingcontrolfile -> FALSE
            warnmissingobsfile -> TRUE
            warnmissingsimfile -> TRUE
            warnsimulationstep -> FALSE
            warntrim -> TRUE
        )
        >>> pub.options.printprogress = False
        >>> pub.options.reprdigits = 6
        """
        options = hydpy.pub.options
        for option in self.find("options", optional=False):
            value = option.text
            if value in ("true", "false"):
                setattr(options, strip(option.tag), value == "true")
            else:
                setattr(options, strip(option.tag), value)
        options.printprogress = False

    def update_timegrids(self) -> None:
        """Update the |Timegrids| object available in the |pub| module with the values
        defined in the `timegrid` XML element.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     XMLInterface("single_run.xml").update_timegrids()
        >>> pub.timegrids
        Timegrids("1996-01-01T00:00:00",
                  "1996-01-06T00:00:00",
                  "1d")
        """
        timegrid_xml = self.find("timegrid", optional=False)
        firstdate = timegrid_xml[0].text
        assert firstdate is not None
        lastdate = timegrid_xml[1].text
        assert lastdate is not None
        stepsize = timegrid_xml[2].text
        assert stepsize is not None
        hydpy.pub.timegrids = (firstdate, lastdate, stepsize)

    def update_selections(self) -> None:
        """Create |Selection| objects based on the `add_selections` XML element and
        add them to the |Selections| object available in module |pub|.

        The `Lahn` example project comes with four selections:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> from hydpy.auxs.xmltools import find, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> pub.selections
        Selections("complete", "headwaters", "nonheadwaters", "streams")

        Following the definitions of the `add_selections` element of the configuration
        file `single_run.xml`, method |XMLInterface.update_selections| creates three
        additional selections based on given device names, keywords, or selection
        names (you could also combine these subelements):

        >>> interface.update_selections()
        >>> pub.selections
        Selections("complete", "from_devices", "from_keywords",
                   "from_selections", "headwaters", "nonheadwaters", "streams")
        >>> pub.selections.from_devices
        Selection("from_devices",
                  nodes=(),
                  elements=("land_lahn_leun", "land_lahn_marb"))
        >>> pub.selections.from_keywords
        Selection("from_keywords",
                  nodes=(),
                  elements=("land_dill_assl", "land_lahn_kalk",
                            "land_lahn_leun", "land_lahn_marb"))
        >>> pub.selections.from_selections
        Selection("from_selections",
                  nodes=("dill_assl", "lahn_kalk", "lahn_leun", "lahn_marb"),
                  elements=("land_dill_assl", "land_lahn_kalk",
                            "land_lahn_leun", "land_lahn_marb",
                            "stream_dill_assl_lahn_leun",
                            "stream_lahn_leun_lahn_kalk",
                            "stream_lahn_marb_lahn_leun"))

        Defining wrong device names, keywords, or selection names results in error
        messages:

        >>> add_selections = find(interface.root, "add_selections")
        >>> add_selections[2][1].text = "streams no_selection"
        >>> interface.update_selections()
        Traceback (most recent call last):
        ...
        RuntimeError: The XML configuration file tried to add the devices of a \
selection named `no_selection` to the custom selection `from_selections` but none \
of the available selections has this name.

        >>> add_selections[1][1].text = "catchment no_keyword"
        >>> interface.update_selections()
        Traceback (most recent call last):
        ...
        RuntimeError: The XML configuration file tried to add at least one device \
based on the keyword `no_keyword` to the custom selection `from_keywords` but none \
of the available devices has this keyword.

        >>> add_selections[0][1].text = "dill_assl no_device"
        >>> interface.update_selections()
        Traceback (most recent call last):
        ...
        RuntimeError: The XML configuration file tried to add a device named \
`no_device` to the custom selection `from_devices` but none of the available \
devices has this name.
        """

        def _get_texts(root: ElementTree.Element, name: str) -> list[str]:
            xmlelement = find(root=root, name=name, optional=True)
            if xmlelement is None or xmlelement.text is None:
                return []
            return xmlelement.text.split()

        elements = hydpy.pub.selections.complete.elements
        nodes = hydpy.pub.selections.complete.nodes
        add_selections = find(self.root, "add_selections", optional=True)
        if add_selections is not None:
            for add_selection in add_selections:
                name_new_selection = find(add_selection, "name", optional=False).text
                assert name_new_selection is not None
                new_selection = selectiontools.Selection(name_new_selection)
                for name_device in _get_texts(add_selection, "devices"):
                    try:
                        element = elements[name_device]
                        new_selection.elements.add_device(element)
                    except KeyError:
                        try:
                            node = nodes[name_device]
                            new_selection.nodes.add_device(node)
                        except KeyError:
                            raise RuntimeError(
                                f"The XML configuration file tried to add a device "
                                f"named `{name_device}` to the custom selection "
                                f"`{name_new_selection}` but none of the available "
                                f"devices has this name."
                            ) from None
                for keyword in _get_texts(add_selection, "keywords"):
                    nmb_devices = len(new_selection)
                    new_selection.elements += elements.search_keywords(keyword)
                    new_selection.nodes += nodes.search_keywords(keyword)
                    if len(new_selection) == nmb_devices:
                        raise RuntimeError(
                            f"The XML configuration file tried to add at least one "
                            f"device based on the keyword `{keyword}` to the custom "
                            f"selection `{name_new_selection}` but none of the "
                            f"available devices has this keyword."
                        ) from None
                for name_old_selection in _get_texts(add_selection, "selections"):
                    try:
                        new_selection += hydpy.pub.selections[name_old_selection]
                    except KeyError:
                        raise RuntimeError(
                            f"The XML configuration file tried to add the devices of "
                            f"a selection named `{name_old_selection}` to the custom "
                            f"selection `{name_new_selection}` but none of the "
                            f"available selections has this name."
                        ) from None
                hydpy.pub.selections += new_selection

    @property
    def selections(self) -> selectiontools.Selections:
        """The |Selections| object defined on the main level of the actual XML file.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_selections()
        >>> interface.find("selections").text = "headwaters streams"
        >>> selections = interface.selections
        >>> for selection in selections:
        ...     print(selection.name)
        headwaters
        streams
        >>> selections.headwaters
        Selection("headwaters",
                  nodes=("dill_assl", "lahn_marb"),
                  elements=("land_dill_assl", "land_lahn_marb"))
        >>> interface.find("selections").text = "head_waters"
        >>> interface.selections
        Traceback (most recent call last):
        ...
        NameError: The XML configuration file tries to define a selection using the \
text `head_waters`, but the actual project does not handle such a `Selection` object.
        """
        return _query_selections(self.find("selections", optional=False))

    @property
    def elements(self) -> Iterator[devicetools.Element]:
        """Yield all |Element| objects returned by |XMLInterface.selections| without
        duplicates.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_timegrids()
        >>> interface.update_selections()
        >>> interface.find("selections").text = "headwaters streams"
        >>> for element in interface.elements:
        ...      print(element.name)
        land_dill_assl
        land_lahn_marb
        stream_dill_assl_lahn_leun
        stream_lahn_leun_lahn_kalk
        stream_lahn_marb_lahn_leun
        """
        selections = copy.copy(self.selections)
        elements: set[devicetools.Element] = set()
        for selection in selections:
            for element in selection.elements:
                if element not in elements:
                    elements.add(element)
                    yield element

    @property
    def fullselection(self) -> selectiontools.Selection:
        """A |Selection| object that contains all |Element| and |Node| objects defined
        by |XMLInterface.selections|.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_selections()
        >>> interface.find("selections").text = "nonheadwaters"
        >>> interface.fullselection
        Selection("fullselection",
                  nodes=("lahn_kalk", "lahn_leun"),
                  elements=("land_lahn_kalk", "land_lahn_leun"))
        >>> interface.find("selections").text = "from_keywords"
        >>> interface.fullselection
        Selection("fullselection",
                  nodes=(),
                  elements=("land_dill_assl", "land_lahn_kalk",
                            "land_lahn_leun", "land_lahn_marb"))
        """
        fullselection = selectiontools.Selection("fullselection")
        for selection in self.selections:
            fullselection += selection
        return fullselection

    @property
    def network_io(self) -> Union[XMLNetworkDefault, XMLNetworkUserDefined]:
        """The `network_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> interface.network_io.text
        'default'
        >>> interface = XMLInterface("multiple_runs.xml", make_filepath("HydPy-H-Lahn"))
        >>> interface.network_io.text
        'default'
        """
        network_io = self.find("network_io", optional=True)
        if network_io is None:
            return XMLNetworkDefault(self, text="default")
        return XMLNetworkUserDefined(self, network_io, text=network_io.text)

    @property
    def control_io(self) -> Union[XMLControlDefault, XMLControlUserDefined]:
        """The `control_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> interface.control_io.text
        'default'
        >>> interface = XMLInterface("multiple_runs.xml", make_filepath("HydPy-H-Lahn"))
        >>> interface.control_io.text
        'default'
        """
        control_io = self.find("control_io", optional=True)
        if control_io is None:
            return XMLControlDefault(self, text="default")
        return XMLControlUserDefined(self, control_io, text=control_io.text)

    @property
    def conditions_io(self) -> XMLConditions:
        """The `condition_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLConditions(self, self.find("conditions_io", optional=False))

    @property
    def series_io(self) -> XMLSeries:
        """The `series_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLSeries(self, self.find("series_io", optional=False))

    @property
    def exchange(self) -> XMLExchange:
        """The `exchange` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface(
        ...     "multiple_runs.xml", make_filepath("HydPy-H-Lahn"))
        >>> strip(interface.exchange.root.tag)
        'exchange'
        """
        return XMLExchange(self, self.find("exchange", optional=False))


class XMLNetworkBase:
    """Base class for |XMLNetworkDefault| and |XMLNetworkUserDefined|."""

    master: XMLInterface
    text: Optional[str]

    def prepare_network(self) -> None:
        """Prepare the |Selections| object available in the global |pub| module:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import attrready, HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.find("network_io").text = "wrong"
        ...     interface.network_io.prepare_network()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The directory `...wrong` does not contain any network files.

        >>> with TestIO():
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.find("network_io").text = "default"
        ...     interface.network_io.prepare_network()  # doctest: +ELLIPSIS
        >>> pub.selections
        Selections("complete", "headwaters", "nonheadwaters", "streams")
        """
        if self.text:
            hydpy.pub.networkmanager.currentdir = str(self.text)
        hydpy.pub.selections = hydpy.pub.networkmanager.load_files()


class XMLNetworkDefault(XMLNetworkBase):
    """Helper class for |XMLInterface| responsible for loading devices from network
    files when the XML file does not specify a network directory."""

    def __init__(self, master: XMLInterface, text: Optional[str]) -> None:
        self.master: XMLInterface = master
        self.text: Optional[str] = text


class XMLNetworkUserDefined(XMLBase, XMLNetworkBase):
    """Helper class for |XMLInterface| responsible for loading devices from network
    files when the XML file specifies a network directory."""

    def __init__(
        self, master: XMLInterface, root: ElementTree.Element, text: Optional[str]
    ) -> None:
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root
        self.text: Optional[str] = text


class XMLControlBase:
    """Base class for |XMLControlDefault| and |XMLControlUserDefined|."""

    master: XMLInterface
    text: Optional[str]

    def prepare_models(self) -> None:
        """Prepare the |Model| objects of all |Element| objects returned by
        |XMLInterface.elements|:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import attrready, HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.update_selections()
        ...     interface.find("selections").text = "headwaters"
        ...     interface.control_io.prepare_models()
        >>> interface.update_timegrids()
        >>> hp.elements.land_lahn_marb.model.parameters.control.alpha
        alpha(1.0)
        >>> attrready(hp.elements.land_lahn_leun, "model")
        False
        """
        if self.text:
            hydpy.pub.controlmanager.currentdir = str(self.text)
        for element in self.master.elements:
            element.prepare_model()


class XMLControlDefault(XMLControlBase):
    """Helper class for |XMLInterface| responsible for loading models from control
    files when the XML file does not specify a control directory."""

    def __init__(self, master: XMLInterface, text: Optional[str]) -> None:
        self.master: XMLInterface = master
        self.text: Optional[str] = text


class XMLControlUserDefined(XMLBase, XMLControlBase):
    """Helper class for |XMLInterface| responsible for loading models from control
    files when the XML file specifies a control directory."""

    def __init__(
        self, master: XMLInterface, root: ElementTree.Element, text: Optional[str]
    ) -> None:
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root
        self.text: Optional[str] = text


class XMLConditions(XMLBase):
    """Helper class for |XMLInterface| responsible for loading and saving initial
    conditions."""

    def __init__(self, master: XMLInterface, root: ElementTree.Element) -> None:
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    def load_conditions(self, currentdir: Optional[str] = None) -> None:
        """Load the condition files of the |Model| objects of all |Element| objects
        returned by |XMLInterface.elements|:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.update_selections()
        ...     interface.find("selections").text = "headwaters"
        ...     interface.conditions_io.load_conditions()
        >>> interface.update_timegrids()
        >>> hp.elements.land_lahn_marb.model.sequences.states.lz
        lz(8.18711)
        >>> hp.elements.land_lahn_leun.model.sequences.states.lz
        lz(nan)
        """
        if currentdir is None:
            currentdir = str(self.find("inputdir", optional=False).text)
        hydpy.pub.conditionmanager.currentdir = currentdir
        for element in self.master.elements:
            element.model.load_conditions()

    def save_conditions(self, currentdir: Optional[str] = None) -> None:
        """Save the condition files of the |Model| objects of all |Element| objects
        returned by |XMLInterface.elements|:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> import os
        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     hp.elements.land_dill_assl.model.sequences.states.lz = 999.0
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.update_timegrids()
        ...     interface.update_selections()
        ...     interface.find("selections").text = "headwaters"
        ...     interface.conditions_io.save_conditions()
        ...     dirpath = "HydPy-H-Lahn/conditions/init_1996_01_06"
        ...     with open(os.path.join(dirpath, "land_dill_assl.py")) as file_:
        ...         print(file_.readlines()[12].strip())
        ...     os.path.exists(os.path.join(dirpath, "land_lahn_leun.py"))
        lz(999.0)
        False
        >>> from hydpy import xml_replace
        >>> with TestIO():
        ...     xml_replace("HydPy-H-Lahn/single_run", printflag=False, zip_="true")
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.find("selections").text = "headwaters"
        ...     os.path.exists("HydPy-H-Lahn/conditions/init_1996_01_06.zip")
        ...     interface.conditions_io.save_conditions()
        ...     os.path.exists("HydPy-H-Lahn/conditions/init_1996_01_06.zip")
        False
        True
        """
        if currentdir is None:
            currentdir = str(self.find("outputdir", optional=False).text)
        hydpy.pub.conditionmanager.currentdir = currentdir
        for element in self.master.elements:
            element.model.save_conditions()
        if self.find("zip", optional=False).text == "true":
            hydpy.pub.conditionmanager.zip_currentdir()


class XMLSeries(XMLBase):
    """Helper class for |XMLInterface| responsible for loading and saving time series
    data, which is further delegated to suitable instances of class |XMLSubseries|."""

    def __init__(self, master: XMLInterface, root: ElementTree.Element) -> None:
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    @property
    def readers(self) -> list[XMLSubseries]:
        """The reader XML elements defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> for reader in interface.series_io.readers:
        ...     print(reader.info)
        all input data
        """
        return [XMLSubseries(self, _) for _ in self.find("readers", optional=False)]

    @property
    def writers(self) -> list[XMLSubseries]:
        """The writer XML elements defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> for writer in interface.series_io.writers:
        ...     print(writer.info)
        precipitation
        soilmoisture
        averaged
        """
        return [XMLSubseries(self, _) for _ in self.find("writers", optional=False)]

    def prepare_series(self) -> None:
        """Call |XMLSubseries.prepare_series| of all |XMLSubseries| objects."""
        for ioseries in itertools.chain(self.readers, self.writers):
            ioseries.prepare_series()

    def load_series(self, currentdir: Optional[str] = None) -> None:
        """Call |XMLSubseries.load_series| of all |XMLSubseries| objects handled as
        "readers"."""
        for reader in self.readers:
            reader.load_series(currentdir)

    def save_series(self, currentdir: Optional[str] = None) -> None:
        """Call |XMLSubseries.load_series| of all |XMLSubseries| objects handled as
        "writers"."""
        for writer in self.writers:
            writer.save_series(currentdir)

    @contextlib.contextmanager
    def modify_inputdir(self, currentdir: Optional[str] = None) -> Iterator[None]:
        """Temporarily modify the |IOSequence.dirpath| of all |IOSequence| objects
        registered for reading time series data "just in time" during a simulation
        run."""
        try:
            for reader in self.readers:
                reader.change_dirpath(currentdir)
            yield
        finally:
            for reader in self.readers:
                reader.reset_dirpath()

    @contextlib.contextmanager
    def modify_outputdir(self, currentdir: Optional[str] = None) -> Iterator[None]:
        """Temporarily modify the |IOSequence.dirpath| of all |IOSequence| objects
        registered for writing time series data "just in time" during a simulation
        run."""
        try:
            for writer in self.writers:
                writer.change_dirpath(currentdir)
            yield
        finally:
            for writer in self.writers:
                writer.reset_dirpath()


class XMLSelector(XMLBase):
    """Base class for |XMLSubseries| and |XMLVar| responsible for querying the relevant
    |Node| and |Element| objects."""

    master: XMLBase
    root: ElementTree.Element

    @property
    def selections(self) -> selectiontools.Selections:
        """The |Selections| object defined for the respective respective IO series or
        exchange item elements of the actual XML file.

        Property |XMLSelector.selections| of class |XMLSelector| falls back to the
        general property |XMLInterface.selections| of |XMLInterface| if the relevant IO
        series or exchange item element does not define a unique selection:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_selections()
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.selections.names)
        all input data ('from_keywords',)
        precipitation ('headwaters', 'from_devices')
        soilmoisture ('complete',)
        averaged ('from_selections',)

        If property |XMLSelector.selections| does not find any definitions, it raises
        the following error:

        >>> interface.root.remove(interface.find("selections"))
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.selections.names)
        Traceback (most recent call last):
        ...
        AttributeError: Unable to find a XML element named "selections".  Please make \
sure your XML file follows the relevant XML schema.
        """
        selections = self.find("selections")
        master: Optional[XMLBase] = self
        while selections is None:
            master = getattr(master, "master", None)
            if master is None:
                raise AttributeError(
                    'Unable to find a XML element named "selections".  Please make '
                    "sure your XML file follows the relevant XML schema."
                )
            selections = master.find("selections")
        return _query_selections(selections)

    @overload
    def _get_devices(self, attr: Literal["nodes"]) -> Iterator[devicetools.Node]:
        """Extract all nodes."""

    @overload
    def _get_devices(self, attr: Literal["elements"]) -> Iterator[devicetools.Element]:
        """Extract all elements."""

    def _get_devices(
        self, attr: Literal["nodes", "elements"]
    ) -> Union[Iterator[devicetools.Node], Iterator[devicetools.Element]]:
        """Extract all nodes or elements."""
        selections = copy.copy(self.selections)
        devices = set()
        for selection in selections:
            for device in getattr(selection, attr):
                if device not in devices:
                    devices.add(device)
                    yield device

    @property
    def elements(self) -> Iterator[devicetools.Element]:
        """Return the |Element| objects selected by the actual IO series or exchange
        item element.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_selections()
        >>> for element in interface.series_io.writers[0].elements:
        ...     print(element.name)
        land_dill_assl
        land_lahn_marb
        land_lahn_leun
        """
        return self._get_devices("elements")

    @property
    def nodes(self) -> Iterator[devicetools.Node]:
        """Return the |Node| objects selected by the actual IO series or exchange item
        element.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_selections()
        >>> for node in interface.series_io.writers[0].nodes:
        ...     print(node.name)
        dill_assl
        lahn_marb
        """
        return self._get_devices("nodes")


class XMLSubseries(XMLSelector):
    """Helper class for |XMLSeries| responsible for loading and saving time series
    data."""

    def __init__(self, master: XMLSeries, root: ElementTree.Element) -> None:
        self.master: XMLSeries = master
        self.root: ElementTree.Element = root

    @property
    def info(self) -> str:
        """Info attribute of the actual XML `reader` or `writer` element."""
        return self.root.attrib["info"]

    @property
    def _is_reader(self) -> bool:
        if self.name == "reader":
            return True
        if self.name == "writer":
            return False
        assert False

    @property
    def _is_writer(self) -> bool:
        return not self._is_reader

    def prepare_sequencemanager(self, currentdir: Optional[str] = None) -> None:
        """Configure the |SequenceManager| object available in module |pub| following
        the definitions of the actual XML `reader` or `writer` element when available;
        if not, use those of the XML `series_io` element or fall back to the default.

        Compare the following results with `single_run.xml` to see that the first
        `writer` element re-defines the default file type (`asc`), that the second
        `writer` element defines an alternative file type (`npy`), and that the third
        `writer` relies on the general file type.  The base mechanism is the same
        for other options, e.g. the aggregation mode.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> series_io = interface.series_io
        >>> with TestIO():
        ...     series_io.writers[0].prepare_sequencemanager()
        ...     pub.sequencemanager.currentdir
        'default'
        >>> pub.sequencemanager.filetype
        'asc'
        >>> pub.sequencemanager.overwrite
        TRUE
        >>> pub.sequencemanager.aggregation
        'none'
        >>> pub.sequencemanager.convention
        'model-specific'
        >>> with TestIO():
        ...     series_io.writers[1].prepare_sequencemanager()
        ...     pub.sequencemanager.currentdir
        'soildata'
        >>> pub.sequencemanager.filetype
        'nc'
        >>> pub.sequencemanager.overwrite
        FALSE
        >>> pub.sequencemanager.aggregation
        'none'
        >>> pub.sequencemanager.convention
        'model-specific'
        >>> with TestIO():
        ...     series_io.writers[2].prepare_sequencemanager()
        ...     pub.sequencemanager.currentdir
        'averages'
        >>> pub.sequencemanager.filetype
        'npy'
        >>> pub.sequencemanager.aggregation
        'mean'
        >>> pub.sequencemanager.overwrite
        TRUE
        >>> pub.sequencemanager.aggregation
        'mean'
        >>> pub.sequencemanager.convention
        'model-specific'
        """
        sm = hydpy.pub.sequencemanager
        if currentdir is None:
            element = self.find("directory")
            if element is None:
                element = self.master.find("directory")
            if element is None:
                sm.currentdir = "default"
            else:
                assert element.text is not None
                sm.currentdir = element.text
        else:
            sm.currentdir = currentdir

        for option in ("filetype", "aggregation", "convention", "overwrite"):
            delattr(sm, option)
            for element in (self.find(option), self.master.find(option)):
                if element is not None:
                    assert element.text is not None
                    if option == "overwrite":
                        sm.overwrite = objecttools.value2bool(option, element.text)
                    else:
                        setattr(sm, option, element.text)
                    break

    @property
    def _ramflag(self) -> bool:
        """A flag analoge to the |IOSequence.ramflag| of class |IOSequence|."""
        mode = self.find("mode")
        if mode is None:
            mode = self.master.find("mode")
        if mode is None:
            return True
        assert mode.text is not None
        return mode.text == "ram"

    @property
    def model2subs2seqs(
        self,
    ) -> collections.defaultdict[str, collections.defaultdict[str, list[str]]]:
        """A nested |collections.defaultdict| containing the model-specific information
        provided by the XML `sequences` element.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> series_io = interface.series_io
        >>> model2subs2seqs = series_io.writers[2].model2subs2seqs
        >>> for model, subs2seqs in sorted(model2subs2seqs.items()):
        ...     for subs, seq in sorted(subs2seqs.items()):
        ...         print(model, subs, seq)
        hland_96 factors ['tc']
        hland_96 fluxes ['tf']
        hland_96 states ['sm']
        musk_classic states ['discharge']
        """
        model2subs2seqs: collections.defaultdict[
            str, collections.defaultdict[str, list[str]]
        ] = collections.defaultdict(lambda: collections.defaultdict(list))
        for model in self.find("sequences", optional=False):
            model_name = strip(model.tag)
            if model_name == "node":
                continue
            for group in model:
                group_name = strip(group.tag)
                for sequence in group:
                    seq_name = strip(sequence.tag)
                    model2subs2seqs[model_name][group_name].append(seq_name)
        return model2subs2seqs

    @property
    def subs2seqs(self) -> dict[str, list[str]]:
        """A |collections.defaultdict| containing the node-specific information
        provided by XML `sequences` element.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("HydPy-H-Lahn"))
        >>> series_io = interface.series_io
        >>> subs2seqs = series_io.writers[2].subs2seqs
        >>> for subs, seq in sorted(subs2seqs.items()):
        ...     print(subs, seq)
        node ['sim', 'obs']
        """
        subs2seqs: collections.defaultdict[str, list[str]]
        subs2seqs = collections.defaultdict(list)
        nodes = find(self.find("sequences", optional=False), "node")
        if nodes is not None:
            for seq in nodes:
                subs2seqs["node"].append(strip(seq.tag))
        return subs2seqs

    def _iterate_sequences(self) -> Iterator[sequencetools.IOSequence]:
        return itertools.chain(
            self._iterate_model_sequences(), self._iterate_node_sequences()
        )

    def _iterate_model_sequences(self) -> Iterator[sequencetools.IOSequence]:
        m2s2s = self.model2subs2seqs
        for element in self.elements:
            for model in element.model.find_submodels(include_mainmodel=True).values():
                for subseqs_name, seq_names in m2s2s.get(model.name, {}).items():
                    subseqs = getattr(model.sequences, subseqs_name)
                    for seq_name in seq_names:
                        yield getattr(subseqs, seq_name)

    def _iterate_node_sequences(self) -> Iterator[sequencetools.IOSequence]:
        s2s = self.subs2seqs
        for node in self.nodes:
            for seq_names in s2s.values():
                for seq_name in seq_names:
                    yield getattr(node.sequences, seq_name)

    def prepare_series(self) -> None:
        """Call method |IOSequence.prepare_series| of class |IOSequence| for all
        sequences selected by the given element of the actual XML file.

        Method |IOSequence.prepare_series| solves a complex task, as it needs to
        determine the correct arguments for method |IOSequence.prepare_series| of class
        |IOSequence|.  Those arguments depend on whether the respective |XMLSubseries|
        element is for reading or writing data, addresses input or output sequences,
        and if one prefers to handle time series data in RAM or read or write it "just
        in time" during model simulations.  Method |XMLSubseries.prepare_series|
        delegates some of the related logic to the |PrepareSeriesArguments.from_xmldata|
        method of class |PrepareSeriesArguments|.  The following examples demonstrate
        that method |XMLSubseries.prepare_series| implements the remaining logic
        correctly.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_timegrids()
        >>> interface.update_selections()

        First, we check and discuss the proper setting of the properties
        |IOSequence.ramflag|, |IOSequence.diskflag_reading|, and
        |IOSequence.diskflag_writing| for the sequences defined in `single_run.xml`.
        First, we call |XMLSubseries.prepare_series| for available |XMLSubseries|
        objects:

        >>> series_io = interface.series_io
        >>> for reader in series_io.readers:
        ...     reader.prepare_series()
        >>> for writer in series_io.writers:
        ...     writer.prepare_series()

        The following test function prints the options of the specified sequence of
        element "Dill_assl":

        >>> def print_io_options(groupname, sequencename):
        ...     sequences = hp.elements.land_dill_assl.model.sequences
        ...     sequence = sequences[groupname][sequencename]
        ...     print(f"ramflag={sequence.ramflag}")
        ...     print(f"diskflag_reading={sequence.diskflag_reading}")
        ...     print(f"diskflag_writing={sequence.diskflag_writing}")

        The XML file uses the `jit` mode for all non-aggregated time series.  Reader
        elements handle input sequences and writer elements handle output sequences.
        Hence, |IOSequence.ramflag| is generally |False| while
        |IOSequence.diskflag_reading| is |True| for the input sequences and
        |IOSequence.diskflag_writing| is |True| for the output sequences:

        >>> print_io_options("inputs", "p")
        ramflag=False
        diskflag_reading=True
        diskflag_writing=False

        >>> print_io_options("fluxes", "pc")
        ramflag=False
        diskflag_reading=False
        diskflag_writing=True

        Currently, aggregation only works in combination with mode `ram`:

        >>> print_io_options("factors", "tc")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=False

        For sequence |hland_states.SM|, two writers apply.  The writer "soil moisture"
        triggers writing the complete time series "just in time" during the simulation
        run.  In contrast, the writer "averaged" initiates writing averaged time series
        after the simulation run.  The configuration of sequence |hland_states.SM|
        reflects this, with both "ram flag" and "disk flag writing" being "True":

        >>> print_io_options("states", "sm")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=True

        We temporarily convert the single reader element to a writer element and apply
        method |XMLSubseries.prepare_series| again.  At first, this does not work, as
        the affected input sequences have previously been configured for "just in time"
        reading, which does not work in combination with "just in time" writing:

        >>> reader = series_io.readers[0]
        >>> reader.root.tag = reader.root.tag.replace("reader", "writer")
        >>> reader.prepare_series()
        Traceback (most recent call last):
        ...
        ValueError: Reading from and writing into the same NetCDF file "just in time" \
during a simulation run is not supported but tried for sequence `p` of element \
`land_dill_assl`.

        After resetting all |InputSequence| objects and re-applying
        |XMLSubseries.prepare_series|, both |IOSequence.ramflag| and
        |IOSequence.diskflag_writing| are |True|.  This case is the only one where a
        single reader or writer enables two flags  (see the documentation on method
        |PrepareSeriesArguments.from_xmldata| for further information):

        >>> hp.prepare_allseries(allocate_ram=False, jit=False)
        >>> reader.prepare_series()
        >>> reader.root.tag = reader.root.tag.replace("writer", "reader")
        >>> print_io_options("inputs", "p")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=True

        If we prefer the `ram` mode, things are more straightforward.  Then, option
        |IOSequence.ramflag| is |True|, and options |IOSequence.diskflag_reading| and
        |IOSequence.diskflag_writing| are |False| regardless of all other options:

        >>> hp.prepare_allseries(allocate_ram=False, jit=False)
        >>> series_io.find("mode").text = "ram"
        >>> for reader in series_io.readers:
        ...     reader.find("mode").text = "ram"
        ...     reader.prepare_series()
        >>> for writer in series_io.writers:
        ...     mode = writer.find("mode")
        ...     if mode is not None:
        ...         mode.text = "ram"
        ...     writer.prepare_series()

        >>> print_io_options("inputs", "p")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=False

        >>> print_io_options("fluxes", "pc")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=False

        >>> print_io_options("states", "sm")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=False

        >>> reader = series_io.readers[0]
        >>> reader.root.tag = reader.root.tag.replace("reader", "writer")
        >>> reader.prepare_series()
        >>> reader.root.tag = reader.root.tag.replace("writer", "reader")
        >>> print_io_options("inputs", "p")
        ramflag=True
        diskflag_reading=False
        diskflag_writing=False
        """
        input_args = PrepareSeriesArguments.from_xmldata(
            is_reader=self._is_reader, is_input=True, prefer_ram=self._ramflag
        )
        output_args = None
        if self._is_writer:
            output_args = PrepareSeriesArguments.from_xmldata(
                is_reader=False, is_input=False, prefer_ram=self._ramflag
            )
        input_types = (sequencetools.InputSequence, sequencetools.NodeSequence)
        for sequence in self._iterate_sequences():
            args = (
                input_args
                if (output_args is None) or isinstance(sequence, input_types)
                else output_args
            )
            sequence.prepare_series(
                allocate_ram=sequence.ramflag or args.allocate_ram,
                read_jit=sequence.diskflag_reading or args.read_jit,
                write_jit=sequence.diskflag_writing or args.write_jit,
            )

    def load_series(self, currentdir: Optional[str]) -> None:
        """Load time series data as defined by the actual XML `reader` element.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, xml_replace, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     xml_replace("HydPy-H-Lahn/single_run", printflag=False)
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.update_options()
        ...     interface.update_timegrids()
        ...     interface.update_selections()
        ...     series_io = interface.series_io
        ...     series_io.prepare_series()
        ...     series_io.load_series()
        >>> from hydpy import print_vector
        >>> print_vector(hp.elements.land_dill_assl.model.sequences.inputs.t.series[:3])
        0.0, -0.5, -2.4
        """
        if self._is_reader:
            hydpy.pub.sequencemanager.open_netcdfreader()
            self.prepare_sequencemanager(currentdir)
            for sequence in self._iterate_sequences():
                if sequence.ramflag:
                    sequence.load_series()
            hydpy.pub.sequencemanager.close_netcdfreader()

    def save_series(self, currentdir: Optional[str]) -> None:
        """Save time series data as defined by the actual XML `writer` element.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, round_, TestIO, xml_replace, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     xml_replace("HydPy-H-Lahn/single_run", printflag=False)
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_options()
        >>> interface.update_timegrids()
        >>> interface.update_selections()
        >>> series_io = interface.series_io
        >>> series_io.prepare_series()
        >>> hp.elements.land_dill_assl.model.sequences.fluxes.pc.series[2, 3] = 9.0
        >>> hp.nodes.lahn_leun.sequences.sim.series[4] = 7.0
        >>> with TestIO():
        ...     series_io.save_series()
        >>> import numpy
        >>> with TestIO():
        ...     dirpath = "HydPy-H-Lahn/series/default/"
        ...     os.path.exists(f"{dirpath}land_lahn_leun_hland_96_flux_pc.npy")
        ...     os.path.exists(f"{dirpath}land_lahn_kalk_hland_96_flux_pc.npy")
        ...     round_(numpy.load(f"{dirpath}land_dill_assl_hland_96_flux_pc.npy")[13+2, 3])
        ...     round_(numpy.load(f"{dirpath}lahn_leun_sim_q_mean.npy")[13+4])
        True
        False
        9.0
        7.0
        """
        if self.name == "writer":
            hydpy.pub.sequencemanager.open_netcdfwriter()
            self.prepare_sequencemanager(currentdir)
            for sequence in self._iterate_sequences():
                if not sequence.diskflag_writing:
                    sequence.save_series()
            hydpy.pub.sequencemanager.close_netcdfwriter()

    def change_dirpath(self, currentdir: Optional[str]) -> None:
        """Set the |IOSequence.dirpath| of all relevant |IOSequence| objects to the
        |FileManager.currentpath| of the |SequenceManager| object available in the
        |pub| module.

        This "information freezing" is required for those sequences selected for
        reading data  from or writing data to different directories "just in time"
        during a simulation run.
        """
        if not self._ramflag:
            self.prepare_sequencemanager(currentdir)
            currentpath = hydpy.pub.sequencemanager.currentpath
            for sequence in self._iterate_sequences():
                sequence.dirpath = currentpath

    def reset_dirpath(self) -> None:
        """Revert |XMLSubseries.change_dirpath|."""
        if not self._ramflag:
            for sequence in self._iterate_sequences():
                del sequence.dirpath


class XMLExchange(XMLBase):
    """Helper class for |XMLInterface| responsible for interpreting exchange items,
    accessible via different |XMLItemgroup| instances."""

    def __init__(self, master: XMLInterface, root: ElementTree.Element) -> None:
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    def _get_items_of_certain_item_types(
        self, itemgroups: Iterable[str], itemtype: type[_TypeGetOrChangeItem]
    ) -> list[_TypeGetOrChangeItem]:
        """Return either all |GetItem| or all |ChangeItem| objects."""
        items: list[_TypeGetOrChangeItem] = []
        for itemgroup in self.itemgroups:
            if (
                issubclass(itemtype, itemtools.GetItem)
                and (itemgroup.name == "getitems")
            ) or (
                issubclass(itemtype, itemtools.ChangeItem)
                and (itemgroup.name != "getitems")
            ):
                for var in (
                    var
                    for model in itemgroup.models
                    for subvars in model.subvars
                    if subvars.name in itemgroups
                    for var in subvars.vars
                ):
                    item = var.item
                    assert isinstance(item, itemtype)
                    items.append(item)
                if "nodes" in itemgroups:
                    for var in (var for node in itemgroup.nodes for var in node.vars):
                        item = var.item
                        assert isinstance(item, itemtype)
                        items.append(item)
        return items

    @property
    def parameteritems(self) -> list[itemtools.ChangeItem]:
        """Create and return all items for changing control parameter values.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> interface.update_selections()
        >>> for item in interface.exchange.parameteritems:
        ...     print(item.name)
        alpha
        beta
        lag
        damp
        sfcf_1
        sfcf_2
        sfcf_3
        k4
        """
        return self._get_items_of_certain_item_types(
            itemgroups=("control",), itemtype=itemtools.ChangeItem
        )

    @property
    def inputitems(self) -> list[itemtools.SetItem]:
        """Return all items for changing input sequence values.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> interface.update_selections()
        >>> for item in interface.exchange.inputitems:
        ...     print(item.name)
        t_headwaters
        """
        return self._get_items_of_certain_item_types(
            itemgroups=("inputs",), itemtype=itemtools.SetItem
        )

    @property
    def conditionitems(self) -> list[itemtools.SetItem]:
        """Return all items for changing condition sequence values.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> interface.update_selections()
        >>> for item in interface.exchange.conditionitems:
        ...     print(item.name)
        ic_lahn_leun
        ic_lahn_marb
        sm_lahn_leun
        sm_lahn_marb
        quh
        """
        return self._get_items_of_certain_item_types(
            itemgroups=("states", "logs"), itemtype=itemtools.SetItem
        )

    @property
    def outputitems(self) -> list[itemtools.SetItem]:
        """Return all items for querying the current values or the complete time
        series of sequences in the "setitem" style.

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> interface.update_selections()
        >>> for item in interface.exchange.outputitems:
        ...     print(item.name)
        swe_headwaters
        """
        return self._get_items_of_certain_item_types(
            itemgroups=("factors", "fluxes"), itemtype=itemtools.SetItem
        )

    @property
    def getitems(self) -> list[itemtools.GetItem]:
        """Return all items for querying the current values or the complete time
        series of sequences in the "getitem style".

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> interface.update_selections()
        >>> for item in interface.exchange.getitems:
        ...     print(item.target)
        factors_contriarea
        fluxes_qt
        fluxes_qt_series
        states_sm
        states_sm_series
        nodes_sim_series
        """
        return self._get_items_of_certain_item_types(
            itemgroups=(
                "control",
                "inputs",
                "factors",
                "fluxes",
                "states",
                "logs",
                "nodes",
            ),
            itemtype=itemtools.GetItem,
        )

    def prepare_series(self) -> None:
        """Prepare all required |IOSequence.series| arrays via the
        |IOSequence.prepare_series| method.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=exceptiontools.AttributeNotReadyWarning
            )
            for item in itertools.chain(
                self.inputitems, self.conditionitems, self.outputitems, self.getitems
            ):
                for target in item.device2target.values():
                    if item.targetspecs.series:
                        assert isinstance(target, sequencetools.IOSequence)
                        target.prepare_series(
                            allocate_ram=True, read_jit=None, write_jit=None
                        )
                    # for base in getattr(item, "device2base", {}).values():
                    #     if item.basespecs.series and not base.ramflag:
                    #         base.prepare_series()   ToDo

    @property
    def itemgroups(self) -> list[XMLItemgroup]:
        """The relevant |XMLItemgroup| objects."""
        return [XMLItemgroup(self, element) for element in self]


class XMLItemgroup(XMLBase):
    """Helper class for |XMLExchange| responsible for handling the exchange items
    related to model parameters and sequences separately from the exchange items of
    node sequences."""

    def __init__(self, master: XMLExchange, root: ElementTree.Element) -> None:
        self.master: XMLExchange = master
        self.root: ElementTree.Element = root

    @property
    def models(self) -> list[XMLModel]:
        """The required |XMLModel| objects."""
        return [
            XMLModel(self, element) for element in self if strip(element.tag) != "nodes"
        ]

    @property
    def nodes(self) -> list[XMLNode]:
        """The required |XMLNode| objects."""
        return [
            XMLNode(self, element) for element in self if strip(element.tag) == "nodes"
        ]


class XMLModel(XMLBase):
    """Helper class for |XMLItemgroup| responsible for handling the exchange items
    related to different parameter or sequence groups of |Model| objects."""

    def __init__(self, master: XMLItemgroup, root: ElementTree.Element) -> None:
        self.master: XMLItemgroup = master
        self.root: ElementTree.Element = root

    @property
    def subvars(self) -> list[XMLSubvars]:
        """The required |XMLSubVars| objects."""
        return [XMLSubvars(self, element) for element in self]


class XMLSubvars(XMLBase):
    """Helper class for |XMLModel| responsible for handling the exchange items
    related to individual parameters or sequences of |Model| objects."""

    def __init__(self, master: XMLModel, root: ElementTree.Element):
        self.master: XMLModel = master
        self.root: ElementTree.Element = root

    @property
    def vars(self) -> list[XMLVar]:
        """The required |XMLVar| objects."""
        return [XMLVar(self, element) for element in self]


class XMLNode(XMLBase):
    """Helper class for |XMLItemgroup| responsible for handling the exchange items
    related to individual parameters or sequences of |Node| objects."""

    def __init__(self, master: XMLItemgroup, root: ElementTree.Element) -> None:
        self.master: XMLItemgroup = master
        self.root: ElementTree.Element = root

    @property
    def vars(self) -> list[XMLVar]:
        """The required |XMLVar| objects."""
        return [XMLVar(self, element) for element in self]


class XMLVar(XMLSelector):
    """Helper class for |XMLSubvars| and |XMLNode| responsible for creating a defined
    exchange item."""

    def __init__(
        self, master: Union[XMLSubvars, XMLNode], root: ElementTree.Element
    ) -> None:
        self.master: Union[XMLSubvars, XMLNode] = master
        self.root: ElementTree.Element = root

    @property
    def item(self) -> itemtools.ExchangeItem:
        """The defined |ExchangeItem| object.

        We first prepare the `HydPy-H-Lahn` example project and then create the related
        |XMLInterface| object defined by the XML configuration file `multiple_runs`:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import (HydPy, round_, print_matrix, print_vector, pub, TestIO,
        ...                    XMLInterface)
        >>> hp = HydPy("HydPy-H-Lahn")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> interface.update_selections()

        One of the defined |SetItem| objects modifies the values of all
        |hland_control.Alpha| objects of application model |hland_96|.  We demonstrate
        this for the control parameter object handled by the `land_dill_assl` element:

        >>> var = interface.exchange.itemgroups[0].models[0].subvars[0].vars[0]
        >>> item = var.item
        >>> round_(item.value)
        2.0
        >>> hp.elements.land_dill_assl.model.parameters.control.alpha
        alpha(1.0)
        >>> item.update_variables()
        >>> hp.elements.land_dill_assl.model.parameters.control.alpha
        alpha(2.0)

        The second example is comparable but focuses on a |SetItem| modifying control
        parameter |musk_control.NmbSegments| of application model |musk_classic| via
        its keyword argument `lag`:

        >>> var = interface.exchange.itemgroups[0].models[2].subvars[0].vars[0]
        >>> item = var.item
        >>> round_(item.value)
        5.0
        >>> hp.elements.stream_dill_assl_lahn_leun.model.parameters.control.nmbsegments
        nmbsegments(lag=0.0)
        >>> item.update_variables()
        >>> hp.elements.stream_dill_assl_lahn_leun.model.parameters.control.nmbsegments
        nmbsegments(lag=5.0)

        The third discussed |SetItem| assigns the same value to all entries of state
        sequence |hland_states.SM|, resulting in the same soil moisture for all
        individual hydrological response units of element `land_lahn_leun`:

        >>> var = interface.exchange.itemgroups[1].models[0].subvars[0].vars[2]
        >>> item = var.item
        >>> item.name
        'sm_lahn_leun'
        >>> print_vector(item.value)
        123.0
        >>> hp.elements.land_lahn_leun.model.sequences.states.sm
        sm(138.31396, 135.71124, 147.54968, 145.47142, 154.96405, 153.32805,
           160.91917, 159.62434, 165.65575, 164.63255)
        >>> item.update_variables()
        >>> hp.elements.land_lahn_leun.model.sequences.states.sm
        sm(123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0)

        In contrast to the last example, the fourth |SetItem| is 1-dimensional and thus
        allows to assign different values to the individual hydrological response units
        of element `land_lahn_marb`:

        >>> var = interface.exchange.itemgroups[1].models[0].subvars[0].vars[3]
        >>> item = var.item
        >>> item.name
        'sm_lahn_marb'
        >>> print_vector(item.value)
        110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0,
        210.0, 220.0, 230.0
        >>> hp.elements.land_lahn_marb.model.sequences.states.sm
        sm(99.27505, 96.17726, 109.16576, 106.39745, 117.97304, 115.56252,
           125.81523, 123.73198, 132.80035, 130.91684, 138.95523, 137.25983,
           142.84148)
        >>> with pub.options.warntrim(False):
        ...     item.update_variables()
        >>> hp.elements.land_lahn_marb.model.sequences.states.sm
        sm(110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0,
           206.0, 206.0, 206.0)

        Without defining initial values in the XML file, the |ChangeItem.value|
        property of each |SetItem| starts with the averaged (see item `ic_lahn_leun`) or
        original (see item `ic_lahn_marb`) values of the corresponding sequences:

        >>> var = interface.exchange.itemgroups[1].models[0].subvars[0].vars[0]
        >>> item = var.item
        >>> item.name
        'ic_lahn_leun'
        >>> round_(item.value)
        1.184948
        >>> round_(hp.elements.land_lahn_leun.model.sequences.states.ic.average_values())
        1.184948
        >>> var = interface.exchange.itemgroups[1].models[0].subvars[0].vars[1]
        >>> item = var.item
        >>> item.name
        'ic_lahn_marb'
        >>> print_vector(item.value)
        0.96404, 1.36332, 0.96458, 1.46458, 0.96512, 1.46512, 0.96565,
        1.46569, 0.96617, 1.46617, 0.96668, 1.46668, 1.46719
        >>> hp.elements.land_lahn_marb.model.sequences.states.ic
        ic(0.96404, 1.36332, 0.96458, 1.46458, 0.96512, 1.46512, 0.96565,
           1.46569, 0.96617, 1.46617, 0.96668, 1.46668, 1.46719)

        Finally, one |SetItem| addresses the time series if the input sequence
        |hland_inputs.T| of both headwater catchments.  Similar to the example above,
        its initial values stem from its target sequences' initial (time series)
        values:

        >>> var = interface.exchange.itemgroups[2].models[0].subvars[0].vars[0]
        >>> item = var.item
        >>> print_matrix(item.value)
        | 0.0, -0.5, -2.4, -6.8, -7.8 |
        | -0.7, -1.5, -4.6, -8.2, -8.7 |
        >>> print_vector(hp.elements.land_dill_assl.model.sequences.inputs.t.series)
        0.0, -0.5, -2.4, -6.8, -7.8
        >>> print_vector(hp.elements.land_lahn_marb.model.sequences.inputs.t.series)
        -0.7, -1.5, -4.6, -8.2, -8.7
        >>> item.value = [0.0, 1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0, 9.0]
        >>> item.update_variables()
        >>> print_vector(hp.elements.land_dill_assl.model.sequences.inputs.t.series)
        0.0, 1.0, 2.0, 3.0, 4.0
        >>> print_vector(hp.elements.land_lahn_marb.model.sequences.inputs.t.series)
        5.0, 6.0, 7.0, 8.0, 9.0

        |AddItem| `sfcf_1`, `sfcf_2`, and `sfcf_3` serve to demonstrate how a scalar
        value (`sfcf_1` and `sfcf_2`) or a vector of values can be used to change the
        value of a "target" parameter (|hland_control.SfCF|) in relation to a "base"
        parameter (|hland_control.RfCF|):

        >>> for element in pub.selections.headwaters.elements:
        ...     element.model.parameters.control.rfcf(1.1)
        >>> for element in pub.selections.nonheadwaters.elements:
        ...     element.model.parameters.control.rfcf(1.0)

        >>> for subvars in interface.exchange.itemgroups[3].models[0].subvars:
        ...     for var in subvars.vars:
        ...         var.item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, repr(element.model.parameters.control.sfcf))
        land_dill_assl sfcf(1.4)
        land_lahn_kalk sfcf(field=1.1, forest=1.2)
        land_lahn_leun sfcf(1.2)
        land_lahn_marb sfcf(1.4)

        |MultiplyItem| `k4` works similar to the described add items but multiplies
        the current values of the base parameter objects of type |hland_control.K|
        with 10 to gain new values for the target parameter objects of type
        |hland_control.K4|:

        >>> for subvars in interface.exchange.itemgroups[4].models[0].subvars:
        ...     for var in subvars.vars:
        ...         var.item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     control = element.model.parameters.control
        ...     print(element, repr(control.k), repr(control.k4))
        land_dill_assl k(0.005618) k4(0.056177)
        land_lahn_kalk k(0.002571) k4(0.025712)
        land_lahn_leun k(0.005948) k4(0.059481)
        land_lahn_marb k(0.005325) k4(0.053247)

        The final three examples focus on |GetItem| objects.  One |GetItem| object
        queries the actual values of the |hland_states.SM| states of all relevant
        elements:

        >>> var = interface.exchange.itemgroups[5].models[0].subvars[2].vars[0]
        >>> hp.elements.land_dill_assl.model.sequences.states.sm = 1.0
        >>> for name, target in var.item.yield_name2value():
        ...     print(name, target)  # doctest: +ELLIPSIS
        land_dill_assl_states_sm [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        land_lahn_kalk_states_sm [101.3124...]
        land_lahn_leun_states_sm [123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0]
        land_lahn_marb_states_sm [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0, 206.0, 206.0, 206.0]

        Another |GetItem| object queries the actual value of the
        |hland_factors.ContriArea| factor sequence of element `land_dill_assl`:

        >>> hp.elements.land_dill_assl.model.sequences.factors.contriarea(1.0)
        >>> for var in interface.exchange.itemgroups[5].models[0].subvars[0].vars:
        ...     for name, target in var.item.yield_name2value():
        ...         print(name, target)
        land_dill_assl_factors_contriarea 1.0

        Another |GetItem| object queries both the actual and the time series values of
        the |hland_fluxes.QT| flux sequence of element `land_dill_assl`:

        >>> qt = hp.elements.land_dill_assl.model.sequences.fluxes.qt
        >>> qt(1.0)
        >>> qt.series = 2.0
        >>> for var in interface.exchange.itemgroups[5].models[0].subvars[1].vars:
        ...     for name, target in var.item.yield_name2value():
        ...         print(name, target)
        land_dill_assl_fluxes_qt 1.0
        land_dill_assl_fluxes_qt_series [2.0, 2.0, 2.0, 2.0, 2.0]

        Last but not least, one |GetItem| queries the simulated time series values
        available through node `dill_assl`:

        >>> var = interface.exchange.itemgroups[5].nodes[0].vars[0]
        >>> hp.nodes.dill_assl.sequences.sim.series = range(5)
        >>> for name, target in var.item.yield_name2value():
        ...     print(name, target)
        dill_assl_nodes_sim_series [0.0, 1.0, 2.0, 3.0, 4.0]
        >>> for name, target in var.item.yield_name2value(2, 4):
        ...     print(name, target)
        dill_assl_nodes_sim_series [2.0, 3.0]
        """
        target = f"{self.master.name}.{self.name}"
        if self.master.name == "nodes":
            master = self.master.name
            itemgroup = self.master.master.name
        else:
            master = self.master.master.name
            itemgroup = self.master.master.master.name
        itemtype = _ITEMGROUP2ITEMCLASS[itemgroup]
        if itemgroup == "getitems":
            return self._get_getitem(target, master, itemtype)
        return self._get_changeitem(target, master, itemtype)

    def _get_getitem(
        self, target: str, master: str, itemtype: type[itemtools.GetItem]
    ) -> itemtools.GetItem:
        xmlelement = self.find("name", optional=True)
        if xmlelement is None or xmlelement.text is None:
            name = cast(Name, "?")
        else:
            name = cast(Name, xmlelement.text)
        item = itemtype(name, master, target)
        self._collect_variables(item)
        return item

    def _get_changeitem(
        self, target: str, master: str, itemtype: type[_TypeSetOrAddOrMultiplyItem]
    ) -> _TypeSetOrAddOrMultiplyItem:
        name = cast(Name, self.find("name", optional=False).text)
        assert name is not None
        level = self.find("level", optional=False).text
        assert level is not None
        item: _TypeSetOrAddOrMultiplyItem
        # Simplify the following if-clauses after Mypy issue 10989 is fixed?
        if not issubclass(itemtype, itemtools.SetItem):
            item = itemtype(
                name=name,
                master=master,
                target=target,
                base=strip(list(self)[-1].tag),
                level=cast(itemtools.LevelType, level),
            )
        elif not issubclass(itemtype, (itemtools.AddItem, itemtools.MultiplyItem)):
            keyword = self.find("keyword", optional=True)
            item = itemtype(
                name=name,
                master=master,
                target=target,
                keyword=None if keyword is None else keyword.text,
                level=cast(itemtools.LevelType, level),
            )
        self._collect_variables(item)
        element = self.find("init", optional=True)
        if element is not None:
            init = element.text
            assert init is not None
            item.value = eval(",".join(init.split()))
        else:
            assert isinstance(item, itemtools.SetItem)
            item.extract_values()
        return item

    def _collect_variables(self, item: itemtools.ExchangeItem) -> None:
        selections = self.selections
        item.collect_variables(selections)


class XSDWriter:
    """A pure |classmethod| class for writing the actual XML schema file
    `HydPyConfigBase.xsd`, which makes sure that an XML configuration file is
    readable by class |XMLInterface|.

    Unless you are interested in enhancing HydPy's XML functionalities, you should,
    if any, be interested in method |XSDWriter.write_xsd| only.
    """

    confpath: str = conf.__path__[0]
    filepath_source: str = os.path.join(confpath, "HydPyConfigBase" + ".xsdt")
    filepath_target: str = filepath_source[:-1]

    @classmethod
    def write_xsd(cls) -> None:
        """Write the complete base schema file `HydPyConfigBase.xsd` based on the
        template file `HydPyConfigBase.xsdt`.

        Method |XSDWriter.write_xsd| adds model-specific information to the general
        information of template file `HydPyConfigBase.xsdt` regarding reading and
        writing of time series data and exchanging parameter and sequence values, for
        example, during calibration.

        The following example shows that after writing a new schema file, method
        |XMLInterface.validate_xml| does not raise an error when either applied to the
        XML configuration files `single_run.xml` or `multiple_runs.xml` of the
        `HydPy-H-Lahn` example project:

        >>> import os
        >>> from hydpy.auxs.xmltools import XSDWriter, XMLInterface
        >>> if os.path.exists(XSDWriter.filepath_target):
        ...     os.remove(XSDWriter.filepath_target)
        >>> os.path.exists(XSDWriter.filepath_target)
        False
        >>> XSDWriter.write_xsd()
        >>> os.path.exists(XSDWriter.filepath_target)
        True

        >>> from hydpy.data import make_filepath
        >>> for configfile in ("single_run.xml", "multiple_runs.xml"):
        ...     XMLInterface(configfile, make_filepath("HydPy-H-Lahn")).validate_xml()
        """
        with open(cls.filepath_source, encoding=config.ENCODING) as file_:
            template = file_.read()
        template = template.replace(
            "<!--include model sequence groups-->", cls.get_insertion()
        )
        template = template.replace(
            "<!--include exchange items-->", cls.get_exchangeinsertion()
        )
        with open(cls.filepath_target, "w", encoding=config.ENCODING) as file_:
            file_.write(template)

    @staticmethod
    def get_basemodelnames() -> list[str]:
        """Return a sorted |list| containing all base model names.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_basemodelnames())  # doctest: +ELLIPSIS
        ['arma', 'conv', ..., 'wland', 'wq']
        """
        modelspath: str = models.__path__[0]

        def _is_basemodel(dirname: str) -> bool:
            pathname = os.path.join(modelspath, dirname)
            return os.path.isdir(pathname) and ("__init__.py" in os.listdir(pathname))

        return sorted(dn for dn in os.listdir(modelspath) if _is_basemodel(dn))

    @staticmethod
    def get_applicationmodelnames() -> list[str]:
        """Return a sorted |list| containing all application model names.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_applicationmodelnames())  # doctest: +ELLIPSIS
        [...'dam_v001', 'dam_v002', 'dam_v003', 'dam_v004', 'dam_v005',...]
        """
        modelspath: str = models.__path__[0]
        return sorted(
            str(fn.split(".")[0])
            for fn in sorted(os.listdir(modelspath))
            if (fn.endswith(".py") and (fn != "__init__.py"))
        )

    @classmethod
    def get_insertion(cls) -> str:
        """Return the complete string to be inserted into the string of the template
        file.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_insertion())  # doctest: +ELLIPSIS
            <complexType name="dummy_interceptedwater_readerType">
                <sequence>
                    <element name="inputs"
                             minOccurs="0">
                        <complexType>
                            <sequence>
                                <element
                                    name="interceptedwater"
                                    minOccurs="0"/>
                            </sequence>
                        </complexType>
                    </element>
                </sequence>
            </complexType>
        ...
            <complexType name="dummy_snowalbedo_readerType">
                <sequence>
                    <element name="inputs"
                             minOccurs="0">
                        <complexType>
                            <sequence>
                                <element
                                    name="snowalbedo"
                                    minOccurs="0"/>
        ...
                    <element name="wland_wag"
                             type="hpcb:wland_wag_readerType"
                             minOccurs="0"/>
                </sequence>
            </complexType>
        ...
            <complexType name="arma_rimorido_writerType">
                <sequence>
                    <element name="fluxes"
                             minOccurs="0">
                        <complexType>
                            <sequence>
                                <element
                                    name="qin"
        ...
                                <element
                                    name="qout"
                                    minOccurs="0"/>
                            </sequence>
                        </complexType>
                    </element>
                </sequence>
            </complexType>
        ...
            <complexType name="writerType">
                <sequence>
                    <element name="node"
                             type="hpcb:node_writerType"
                             minOccurs="0"/>
                    <element name="arma_rimorido"
                             type="hpcb:arma_rimorido_writerType"
                             minOccurs="0"/>
        ...
                    <element name="wq_trapeze_strickler"
                             type="hpcb:wq_trapeze_strickler_writerType"
                             minOccurs="0"/>
                </sequence>
            </complexType>
        <BLANKLINE>
        """
        indent = 1
        blanks = " " * (indent * 4)
        subs = []
        types_: tuple[Literal["reader", "writer"], ...] = ("reader", "writer")
        for type_ in types_:
            for name in cls.get_applicationmodelnames():
                model = importtools.prepare_model(name)
                modelinsertion = cls.get_modelinsertion(
                    model=model, type_=type_, indent=indent + 2
                )
                if modelinsertion:
                    subs.extend(
                        [
                            f'{blanks}<complexType name="{name}_{type_}Type">',
                            f"{blanks}    <sequence>",
                            modelinsertion,
                            f"{blanks}    </sequence>",
                            f"{blanks}</complexType>",
                            "",
                        ]
                    )
            subs.append(cls.get_readerwriterinsertion(type_=type_, indent=indent))
        return "\n".join(subs)

    @classmethod
    def get_modelinsertion(
        cls, model: modeltools.Model, type_: str, indent: int
    ) -> Optional[str]:
        """Return the insertion string required for the given application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_96")
        >>> print(XSDWriter.get_modelinsertion(
        ...     model=model, type_="reader", indent=1))  # doctest: +ELLIPSIS
            <element name="inputs"
                     minOccurs="0">
                <complexType>
                    <sequence>
                        <element
                            name="p"
                            minOccurs="0"/>
                        <element
                            name="t"
                            minOccurs="0"/>
                    </sequence>
                </complexType>
            </element>
        >>> print(XSDWriter.get_modelinsertion(
        ...     model=model, type_="writer", indent=1))  # doctest: +ELLIPSIS
            <element name="inputs"
                     minOccurs="0">
                <complexType>
                    <sequence>
                        <element
                            name="p"
                            minOccurs="0"/>
        ...
            </element>
            <element name="fluxes"
                     minOccurs="0">
        ...
            </element>
            <element name="states"
                     minOccurs="0">
        ...
            </element>

        >>> model = prepare_model("arma_rimorido")
        >>> XSDWriter.get_modelinsertion(
        ...     model=model, type_="reader", indent=1)  # doctest: +ELLIPSIS
        >>> print(XSDWriter.get_modelinsertion(
        ...     model=model, type_="writer", indent=1))  # doctest: +ELLIPSIS
            <element name="fluxes"
                     minOccurs="0">
                <complexType>
                    <sequence>
                        <element
                            name="qin"
                            minOccurs="0"/>
            ...
                        <element
                            name="qout"
                            minOccurs="0"/>
                    </sequence>
                </complexType>
            </element>
        """
        names: tuple[str, ...] = ("inputs",)
        if type_ == "writer":
            names += "factors", "fluxes", "states"
        texts = []
        return_none = True
        for name in names:
            subsequences = getattr(model.sequences, name, None)
            if subsequences:
                return_none = False
                texts.append(cls.get_subsequencesinsertion(subsequences, indent))
        return None if return_none else "\n".join(texts)

    @classmethod
    def get_subsequencesinsertion(
        cls, subsequences: sequencetools.SubSequences[Any, Any, Any], indent: int
    ) -> str:
        """Return the insertion string required for the given group of sequences.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_96")
        >>> print(XSDWriter.get_subsequencesinsertion(
        ...     model.sequences.factors, 1))  # doctest: +ELLIPSIS
            <element name="factors"
                     minOccurs="0">
                <complexType>
                    <sequence>
                        <element
                            name="tc"
                            minOccurs="0"/>
                        <element
                            name="fracrain"
                            minOccurs="0"/>
        ...
                        <element
                            name="contriarea"
                            minOccurs="0"/>
                    </sequence>
                </complexType>
            </element>

        """
        blanks = " " * (indent * 4)
        lines = [
            f'{blanks}<element name="{subsequences.name}"',
            f'{blanks}         minOccurs="0">',
            f"{blanks}    <complexType>",
            f"{blanks}        <sequence>",
        ]
        for sequence in subsequences:
            lines.append(cls.get_sequenceinsertion(sequence, indent + 3))
        lines.extend(
            [
                f"{blanks}        </sequence>",
                f"{blanks}    </complexType>",
                f"{blanks}</element>",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def get_sequenceinsertion(sequence: sequencetools.Sequence_, indent: int) -> str:
        """Return the insertion string required for the given sequence.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_96")
        >>> print(XSDWriter.get_sequenceinsertion(model.sequences.fluxes.pc, 1))
            <element
                name="pc"
                minOccurs="0"/>
        """
        blanks = " " * (indent * 4)
        return (
            f"{blanks}<element\n"
            f'{blanks}    name="{sequence.name}"\n'
            f'{blanks}    minOccurs="0"/>'
        )

    @classmethod
    def get_readerwriterinsertion(
        cls, type_: Literal["reader", "writer"], indent: int
    ) -> str:
        """Return the insertion all sequences relevant for reading or writing
        time series data.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_readerwriterinsertion("reader", 1)) # doctest: +ELLIPSIS
            <complexType name="readerType">
                <sequence>
                    <element name="node"
                             type="hpcb:node_readerType"
                             minOccurs="0"/>
                    <element name="dummy_interceptedwater"
                             type="hpcb:dummy_interceptedwater_readerType"
                             minOccurs="0"/>
        ...
                    <element name="wland_wag"
                             type="hpcb:wland_wag_readerType"
                             minOccurs="0"/>
                </sequence>
            </complexType>
        <BLANKLINE>
        >>> print(XSDWriter.get_readerwriterinsertion("writer", 1)) # doctest: +ELLIPSIS
            <complexType name="writerType">
                <sequence>
                    <element name="node"
                             type="hpcb:node_writerType"
                             minOccurs="0"/>
                    <element name="arma_rimorido"
                             type="hpcb:arma_rimorido_writerType"
                             minOccurs="0"/>
        ...
                    <element name="wq_trapeze_strickler"
                             type="hpcb:wq_trapeze_strickler_writerType"
                             minOccurs="0"/>
                </sequence>
            </complexType>
        <BLANKLINE>
        """
        blanks = " " * (indent * 4)
        subs = [
            f'{blanks}<complexType name="{type_}Type">',
            f"{blanks}    <sequence>",
            f'{blanks}        <element name="node"',
            f'{blanks}                 type="hpcb:node_{type_}Type"',
            f'{blanks}                 minOccurs="0"/>',
        ]
        for name in cls.get_applicationmodelnames():
            seqs = importtools.prepare_model(name).sequences
            if seqs.inputs or (
                ((type_ == "writer") and (seqs.factors or seqs.fluxes or seqs.states))
            ):
                subs.extend(
                    [
                        f'{blanks}        <element name="{name}"',
                        f'{blanks}                 type="hpcb:{name}_{type_}Type"',
                        f'{blanks}                 minOccurs="0"/>',
                    ]
                )
        subs.extend([f"{blanks}    </sequence>", f"{blanks}</complexType>", ""])
        return "\n".join(subs)

    @classmethod
    def get_exchangeinsertion(cls) -> str:
        """Return the complete string related to the definition of exchange items to
        be inserted into the string of the template file.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_exchangeinsertion())  # doctest: +ELLIPSIS
            <complexType name="arma_rimorido_mathitemType">
        ...
            <element name="setitems">
        ...
            <complexType name="arma_rimorido_setitemsType">
        ...
            <element name="additems">
        ...
            <element name="multiplyitems">
        ...
            <element name="getitems">
        ...
        """
        indent = 1
        subs = [
            cls.get_mathitemsinsertion(indent),
            cls.get_keyworditemsinsertion(indent),
        ]
        for groupname in ("setitems", "additems", "multiplyitems", "getitems"):
            subs.append(cls.get_itemsinsertion(groupname, indent))
            subs.append(cls.get_itemtypesinsertion(groupname, indent))
        return "\n".join(subs)

    @classmethod
    def get_mathitemsinsertion(cls, indent: int) -> str:
        """Return a string defining a model-specific XML type extending `ItemType`.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_mathitemsinsertion(1))  # doctest: +ELLIPSIS
            <complexType name="arma_rimorido_mathitemType">
                <complexContent>
                    <extension base="hpcb:mathitemType">
                        <choice>
                            <element name="control.responses"/>
        ...
                            <element name="fluxes.qout"/>
                        </choice>
                    </extension>
                </complexContent>
            </complexType>
        <BLANKLINE>
            <complexType name="conv_idw_mathitemType">
        ...
        """
        blanks = " " * (indent * 4)
        subs = []
        for modelname in cls.get_applicationmodelnames():
            model = importtools.prepare_model(modelname)
            subs.extend(
                [
                    f'{blanks}<complexType name="{modelname}_mathitemType">',
                    f"{blanks}    <complexContent>",
                    f'{blanks}        <extension base="hpcb:mathitemType">',
                    f"{blanks}            <choice>",
                ]
            )
            for subvars in cls._get_subvars(model, conditions=False):
                for var in subvars:
                    subs.append(
                        f"{blanks}                "
                        f'<element name="{subvars.name}.{var.name}"/>'
                    )
            subs.extend(
                [
                    f"{blanks}            </choice>",
                    f"{blanks}        </extension>",
                    f"{blanks}    </complexContent>",
                    f"{blanks}</complexType>",
                    "",
                ]
            )
        return "\n".join(subs)

    @classmethod
    def get_keyworditemsinsertion(cls, indent: int) -> str:
        """Return a string defining additional types that support modifying parameter
        values by specific keyword arguments.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_keyworditemsinsertion(1))  # doctest: +ELLIPSIS
            <simpleType name="lland_control_kapgrenz_keywordType">
                <restriction base="string">
                    <enumeration value="option"/>
                </restriction>
            </simpleType>
        <BLANKLINE>
            <complexType name="lland_control_kapgrenz_setitemType">
                <complexContent>
                    <extension base="hpcb:setitemType">
                        <sequence>
                            <element name="keyword"
                                     type="hpcb:lland_control_kapgrenz_keywordType"
                                     minOccurs = "0"/>
                        </sequence>
                    </extension>
                </complexContent>
            </complexType>
        ...
        """
        blanks = " " * (indent * 4)
        subs = []
        for modelname in cls.get_basemodelnames():
            model = importtools.prepare_model(modelname)
            for subvars in cls._get_subvars(model, conditions=False):
                for var in subvars:
                    if isinstance(var, parametertools.Parameter) and var.KEYWORDS:
                        prefix = f"{modelname.split('_')[0]}_{subvars.name}_{var.name}_"
                        subs.extend(
                            [
                                f'{blanks}<simpleType name="{prefix}keywordType">',
                                f'{blanks}    <restriction base="string">',
                            ]
                        )
                        for keyword in var.KEYWORDS:
                            subs.append(
                                f'{blanks}        <enumeration value="{keyword}"/>'
                            )
                        subs.extend(
                            [
                                f"{blanks}    </restriction>",
                                f"{blanks}</simpleType>",
                                "",
                                f'{blanks}<complexType name="{prefix}setitemType">',
                                f"{blanks}    <complexContent>",
                                f'{blanks}        <extension base="hpcb:setitemType">',
                                f"{blanks}            <sequence>",
                                f'{blanks}                <element name="keyword"',
                                f"{blanks}                         "
                                f'type="hpcb:{prefix}keywordType"',
                                f'{blanks}                         minOccurs = "0"/>',
                                f"{blanks}            </sequence>",
                                f"{blanks}        </extension>",
                                f"{blanks}    </complexContent>",
                                f"{blanks}</complexType>",
                                "",
                            ]
                        )
        return "\n".join(subs)

    @staticmethod
    def _get_itemstype(modelname: str, itemgroup: str) -> str:
        return f"{modelname}_{itemgroup}Type"

    @classmethod
    def get_itemsinsertion(cls, itemgroup: str, indent: int) -> str:
        """Return a string defining the XML element for the given exchange item group.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_itemsinsertion("setitems", 1))  # doctest: +ELLIPSIS
            <element name="setitems">
                <complexType>
                    <sequence>
                        <element ref="hpcb:selections"
                                 minOccurs="0"/>
        ...
                        <element name="hland_96"
                                 type="hpcb:hland_96_setitemsType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
        ...
                        <element name="nodes"
                                 type="hpcb:nodes_setitemsType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
                    </sequence>
                    <attribute name="info" type="string"/>
                </complexType>
            </element>
        <BLANKLINE>
        """
        blanks = " " * (indent * 4)
        subs = []
        subs.extend(
            [
                f'{blanks}<element name="{itemgroup}">',
                f"{blanks}    <complexType>",
                f"{blanks}        <sequence>",
                f'{blanks}            <element ref="hpcb:selections"',
                f'{blanks}                     minOccurs="0"/>',
            ]
        )
        for modelname in cls.get_applicationmodelnames():
            type_ = cls._get_itemstype(modelname, itemgroup)
            subs.append(f'{blanks}            <element name="{modelname}"')
            subs.append(f'{blanks}                     type="hpcb:{type_}"')
            subs.append(f'{blanks}                     minOccurs="0"')
            subs.append(f'{blanks}                     maxOccurs="unbounded"/>')
        if itemgroup in ("setitems", "getitems"):
            type_ = f"nodes_{itemgroup}Type"
            subs.append(f'{blanks}            <element name="nodes"')
            subs.append(f'{blanks}                     type="hpcb:{type_}"')
            subs.append(f'{blanks}                     minOccurs="0"')
            subs.append(f'{blanks}                     maxOccurs="unbounded"/>')
        subs.extend(
            [
                f"{blanks}        </sequence>",
                f'{blanks}        <attribute name="info" type="string"/>',
                f"{blanks}    </complexType>",
                f"{blanks}</element>",
                "",
            ]
        )
        return "\n".join(subs)

    @classmethod
    def get_itemtypesinsertion(cls, itemgroup: str, indent: int) -> str:
        """Return a string defining the required types for the given exchange item
        group.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_itemtypesinsertion(
        ...     "setitems", 1))  # doctest: +ELLIPSIS
            <complexType name="arma_rimorido_setitemsType">
        ...
            </complexType>
        <BLANKLINE>
            <complexType name="dam_v001_setitemsType">
        ...
            <complexType name="nodes_setitemsType">
        ...
        """
        subs = []
        for modelname in cls.get_applicationmodelnames():
            subs.append(cls.get_itemtypeinsertion(itemgroup, modelname, indent))
        subs.append(cls.get_nodesitemtypeinsertion(itemgroup, indent))
        return "\n".join(subs)

    @classmethod
    def get_itemtypeinsertion(cls, itemgroup: str, modelname: str, indent: int) -> str:
        """Return a string defining the required types for the given combination of
        an exchange item group and an application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_itemtypeinsertion(
        ...     "setitems", "hland_96", 1))  # doctest: +ELLIPSIS
            <complexType name="hland_96_setitemsType">
                <sequence>
                    <element ref="hpcb:selections"
                             minOccurs="0"/>
                    <element name="control"
                             minOccurs="0"
                             maxOccurs="unbounded">
        ...
                </sequence>
            </complexType>
        <BLANKLINE>
        """
        blanks = " " * (indent * 4)
        type_ = cls._get_itemstype(modelname, itemgroup)
        subs = [
            f'{blanks}<complexType name="{type_}">',
            f"{blanks}    <sequence>",
            f'{blanks}        <element ref="hpcb:selections"',
            f'{blanks}                 minOccurs="0"/>',
            cls.get_subgroupsiteminsertion(itemgroup, modelname, indent + 2),
            f"{blanks}    </sequence>",
            f"{blanks}</complexType>",
            "",
        ]
        return "\n".join(subs)

    @classmethod
    def get_nodesitemtypeinsertion(cls, itemgroup: str, indent: int) -> str:
        """Return a string defining the required types for the given combination of
        an exchange item group and |Node| objects.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_nodesitemtypeinsertion(
        ...     "setitems", 1))  # doctest: +ELLIPSIS
            <complexType name="nodes_setitemsType">
                <sequence>
                    <element ref="hpcb:selections"
                             minOccurs="0"/>
                    <element name="sim"
                             type="hpcb:setitemType"
                             minOccurs="0"
                             maxOccurs="unbounded"/>
                    <element name="obs"
                             type="hpcb:setitemType"
                             minOccurs="0"
                             maxOccurs="unbounded"/>
                    <element name="sim.series"
                             type="hpcb:setitemType"
                             minOccurs="0"
                             maxOccurs="unbounded"/>
                    <element name="obs.series"
                             type="hpcb:setitemType"
                             minOccurs="0"
                             maxOccurs="unbounded"/>
                </sequence>
            </complexType>
        <BLANKLINE>
        """
        blanks = " " * (indent * 4)
        subs = [
            f'{blanks}<complexType name="nodes_{itemgroup}Type">',
            f"{blanks}    <sequence>",
            f'{blanks}        <element ref="hpcb:selections"',
            f'{blanks}                 minOccurs="0"/>',
        ]
        type_ = "getitemType" if itemgroup == "getitems" else "setitemType"
        for name in ("sim", "obs", "sim.series", "obs.series"):
            subs.extend(
                [
                    f'{blanks}        <element name="{name}"',
                    f'{blanks}                 type="hpcb:{type_}"',
                    f'{blanks}                 minOccurs="0"',
                    f'{blanks}                 maxOccurs="unbounded"/>',
                ]
            )
        subs.extend([f"{blanks}    </sequence>", f"{blanks}</complexType>", ""])
        return "\n".join(subs)

    @classmethod
    def get_subgroupsiteminsertion(
        cls, itemgroup: str, modelname: str, indent: int
    ) -> str:
        """Return a string defining the required types for the given combination of an
        exchange item group and an application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_subgroupsiteminsertion(
        ...     "setitems", "hland_96", 1))  # doctest: +ELLIPSIS
            <element name="control"
                     minOccurs="0"
                     maxOccurs="unbounded">
        ...
            </element>
            <element name="inputs"
        ...
            <element name="factors"
        ...
            <element name="fluxes"
        ...
            <element name="states"
        ...
        """
        subs = []
        model = importtools.prepare_model(modelname)
        conditions = itemgroup in ("getitems", "setitems")
        for subvars in cls._get_subvars(model, conditions=conditions):
            subs.append(
                cls.get_subgroupiteminsertion(itemgroup, model, subvars, indent)
            )
        return "\n".join(subs)

    @classmethod
    def _get_subvars(
        cls, model: modeltools.Model, conditions: bool
    ) -> Iterator[variabletools.SubVariables[Any, Any, Any]]:
        yield model.parameters.control
        names = ["inputs", "factors", "fluxes"]
        if conditions:
            names.extend(("states", "logs"))
        for name in names:
            subseqs = getattr(model.sequences, name, None)
            if subseqs:
                yield subseqs

    @classmethod
    def get_subgroupiteminsertion(
        cls,
        itemgroup: str,
        model: modeltools.Model,
        subgroup: variabletools.SubVariables[Any, Any, Any],
        indent: int,
    ) -> str:
        """Return a string defining the required types for the given combination of an
        exchange item group and a specific variable subgroup of an application model or
        class |Node|.

        Note that for `setitems` and `getitems` `setitemType` and `getitemType` are
        referenced, respectively, and for all others, the model-specific `mathitemType`:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_96")
        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_subgroupiteminsertion(  # doctest: +ELLIPSIS
        ...     "setitems", model, model.parameters.control, 1))
            <element name="control"
                     minOccurs="0"
                     maxOccurs="unbounded">
                <complexType>
                    <sequence>
                        <element ref="hpcb:selections"
                                 minOccurs="0"/>
                        <element name="area"
                                 type="hpcb:setitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
                        <element name="nmbzones"
        ...
                    </sequence>
                </complexType>
            </element>

        >>> print(XSDWriter.get_subgroupiteminsertion(  # doctest: +ELLIPSIS
        ...     "getitems", model, model.parameters.control, 1))
            <element name="control"
        ...
                        <element name="area"
                                 type="hpcb:getitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
        ...

        >>> print(XSDWriter.get_subgroupiteminsertion(  # doctest: +ELLIPSIS
        ...     "additems", model, model.parameters.control, 1))
            <element name="control"
        ...
                        <element name="area"
                                 type="hpcb:hland_96_mathitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
        ...

        >>> print(XSDWriter.get_subgroupiteminsertion(  # doctest: +ELLIPSIS
        ...     "multiplyitems", model, model.parameters.control, 1))
            <element name="control"
        ...
                        <element name="area"
                                 type="hpcb:hland_96_mathitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
        ...

        For sequence classes, additional "series" elements are added:

        >>> print(XSDWriter.get_subgroupiteminsertion(  # doctest: +ELLIPSIS
        ...     "setitems", model, model.sequences.factors, 1))
            <element name="factors"
        ...
                        <element name="tc"
                                 type="hpcb:setitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
                        <element name="tc.series"
                                 type="hpcb:setitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
                        <element name="fracrain"
        ...
                    </sequence>
                </complexType>
            </element>
        """
        blanks1 = " " * (indent * 4)
        blanks2 = " " * ((indent + 5) * 4 + 1)
        subs = [
            f'{blanks1}<element name="{subgroup.name}"',
            f'{blanks1}         minOccurs="0"',
            f'{blanks1}         maxOccurs="unbounded">',
            f"{blanks1}    <complexType>",
            f"{blanks1}        <sequence>",
            f'{blanks1}            <element ref="hpcb:selections"',
            f'{blanks1}                     minOccurs="0"/>',
        ]
        seriesflags = [False] if subgroup.name == "control" else [False, True]
        for var in subgroup:
            for series in seriesflags:
                name = f"{var.name}.series" if series else var.name
                subs.append(f'{blanks1}            <element name="{name}"')
                if itemgroup == "setitems":
                    if isinstance(var, parametertools.Parameter) and var.KEYWORDS:
                        type_ = (
                            f"{model.name.split('_')[0]}_{subgroup.name}_"
                            f"{var.name}_setitemType"
                        )
                    else:
                        type_ = "setitemType"
                elif itemgroup == "getitems":
                    type_ = "getitemType"
                else:
                    type_ = f"{model.name}_mathitemType"
                subs.append(f'{blanks2}type="hpcb:{type_}"')
                subs.append(f'{blanks2}minOccurs="0"')
                subs.append(f'{blanks2}maxOccurs="unbounded"/>')
        subs.extend(
            [
                f"{blanks1}        </sequence>",
                f"{blanks1}    </complexType>",
                f"{blanks1}</element>",
            ]
        )
        return "\n".join(subs)
