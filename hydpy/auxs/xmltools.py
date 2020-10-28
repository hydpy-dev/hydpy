# -*- coding: utf-8 -*-
"""This module provides features for executing *HydPy* workflows based on
XML configuration files.

.. _HydPy release: https://github.com/hydpy-dev/hydpy/releases

At the heart of module |xmltools| lies function |run_simulation|, which is
thought to be applied via a command line (see the documentation
on script |hyd| for further information).  |run_simulation| expects that
the *HydPy* project you want to work with is available in your current
working directory and contains an XML configuration file (as `single_run.xml`
in the example project folder `LahnH`).  This configuration file must
agree with the XML schema file `HydPyConfigSingleRun.xsd`, which is available
in the :ref:`configuration` subpackage and also downloadable for each
`HydPy release`_.  In case you did implement new or changed existing
models, you have to update this schema file.  *HydPy* does this automatically
through its setup mechanism (see the documentation on class |XSDWriter|).

To show how to apply |run_simulation| via a command line, we first
copy the `LahnH` project into the `iotesting` folder via calling
function |prepare_full_example_1|:

>>> from hydpy.examples import prepare_full_example_1
>>> prepare_full_example_1()

Running the simulation requires defining the main script (`hyd.py`),
the function specifying the actual workflow (`run_simulation`), the
name of the project of interest (`LahnH`), and the name of the
relevant XMK configuration file (`single_run.xml`).  To simulate using
the command line, we pass the required text to function |run_subprocess|:

>>> from hydpy import run_subprocess, TestIO
>>> import subprocess
>>> with TestIO():    # doctest: +ELLIPSIS
...     result = run_subprocess("hyd.py run_simulation LahnH single_run.xml")
Start HydPy project `LahnH` (...).
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

As defined by the XML configuration file, the simulation started on the
first and ended at the sixths January 1996.  The following example shows
the read initial conditions and the written final conditions of
sequence |hland_states.SM| for the 12 hydrological response units of the
subcatchment `land_dill`:

>>> with TestIO():
...     filepath = "LahnH/conditions/init_1996_01_01_00_00_00/land_dill.py"
...     with open(filepath) as file_:
...         print("".join(file_.readlines()[10:12]))
...     filepath = "LahnH/conditions/init_1996_01_06/land_dill.py"
...     with open(filepath) as file_:
...         print("".join(file_.readlines()[9:12]))
sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
   222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)
<BLANKLINE>
sm(183.873078, 179.955801, 198.446011, 195.222634, 210.598689,
   208.064445, 220.611126, 218.630245, 228.741883, 227.152989,
   235.308805, 234.042313)
<BLANKLINE>

The intermediate soil moisture values are stored in a NetCDF file called
`hland_v1_state_sm.nc`:

>>> import numpy
>>> from hydpy import print_values
>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset("LahnH/series/output/hland_v1_state_sm.nc")
...     chars2str(query_variable(ncfile, "station_id"))[:3]
...     print_values(query_variable(ncfile, "state_sm")[:, 0])
['land_dill_0', 'land_dill_1', 'land_dill_2']
184.926173, 184.603966, 184.386666, 184.098541, 183.873078
>>> ncfile.close()

Spatially averaged time series values are stored in files ending with
the suffix `_mean`:

>>> with TestIO(clear_all=True):
...     print_values((numpy.load(
...         "LahnH/series/output/lahn_1_sim_q_mean.npy")[13:]))
9.647824, 8.517795, 7.781311, 7.344944, 7.153142
"""
# import...
# ...from standard library
import collections
import copy
import itertools
import os
from typing import *
from xml.etree import ElementTree
from typing_extensions import Literal  # type: ignore[misc]

# ...from HydPy
import hydpy
from hydpy import conf
from hydpy import models
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import hydpytools
from hydpy.core import importtools
from hydpy.core import itemtools
from hydpy.core import netcdftools
from hydpy.core import objecttools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.exe import commandtools

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    import netCDF4 as netcdf4
    import xmlschema
    from hydpy.core import modeltools
    from hydpy.core import variabletools
else:
    netcdf4 = exceptiontools.OptionalImport(
        "netcdf4", ["netCDF4", "h5netcdf.legacyapi"], locals()
    )
    xmlschema = exceptiontools.OptionalImport("xmlschema", ["xmlschema"], locals())

namespace = (
    "{https://github.com/hydpy-dev/hydpy/releases/download/"
    "your-hydpy-version/HydPyConfigBase.xsd}"
)
_ITEMGROUP2ITEMCLASS = {
    "setitems": itemtools.SetItem,
    "additems": itemtools.AddItem,
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


def find(root, name, optional=True):
    """Return the first XML element with the given name found in the given
    XML root.

    >>> from hydpy.auxs.xmltools import find, XMLInterface
    >>> from hydpy.data import make_filepath
    >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
    >>> find(interface.root, "timegrid").tag.endswith("timegrid")
    True

    By default, function |find| returns |None| in case the required element
    is missing:

    >>> find(interface.root, "wrong")

    Set the argument `optional` to |False| to let function |find| raise
    errors instead:

    >>> find(interface.root, "wrong", optional=False)
    Traceback (most recent call last):
    ...
    AttributeError: The actual XML element `config` does not define \
a XML subelement named `wrong`.  Please make sure your XML file \
follows the relevant XML schema.
    """
    element = root.find(f"{namespace}{name}")
    if element is None and not optional:
        raise AttributeError(
            f"The actual XML element `{root.tag.rsplit('}')[-1]}` does "
            f"not define a XML subelement named `{name}`.  Please make "
            f"sure your XML file follows the relevant XML schema."
        )
    return element


def _query_selections(xmlelement: ElementTree.Element) -> selectiontools.Selections:
    text = xmlelement.text
    if text is None:
        return selectiontools.Selections()
    selections = []
    for name in text.split():
        try:
            selections.append(getattr(hydpy.pub.selections, name))
        except AttributeError:
            raise NameError(
                f"The XML configuration file tries to define a selection "
                f"using the text `{name}`, but the actual project does not "
                f" handle such a `Selection` object."
            ) from None
    return selectiontools.Selections(*selections)


def _query_devices(xmlelement: ElementTree.Element) -> selectiontools.Selection:
    selection = selectiontools.Selection("temporary_result_of_xml_parsing")
    text = xmlelement.text
    if text is None:
        return selection
    elements = hydpy.pub.selections.complete.elements
    nodes = hydpy.pub.selections.complete.nodes
    for name in text.split():
        try:
            selection.elements += getattr(elements, name)
            continue
        except AttributeError:
            try:
                selection.nodes += getattr(nodes, name)
            except AttributeError:
                raise NameError(
                    f"The XML configuration file tries to define additional "
                    f"devices using the text `{name}`, but the complete "
                    f"selection of the actual project does neither handle a "
                    f"`Node` or `Element` object with such a name or keyword."
                ) from None
    return selection


def strip(name: str) -> str:
    """Remove the XML namespace from the given string and return it.

    >>> from hydpy.auxs.xmltools import strip
    >>> strip("{https://github.com/something.xsd}something")
    'something'
    """
    return name.split("}")[-1]


def run_simulation(projectname: str, xmlfile: str) -> None:
    """Perform a HydPy workflow in agreement with the given XML configuration
    file available in the directory of the given project. ToDo

    Function |run_simulation| is a "script function" and is normally used as
    explained in the main documentation on module |xmltools|.
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
    hp.prepare_network()
    write("Activate the selected network")
    hp.update_devices(
        selection=interface.fullselection,
    )
    write("Read the required control files")
    hp.prepare_models()
    write("Read the required condition files")
    interface.conditions_io.load_conditions()
    write("Read the required time series files")
    interface.series_io.prepare_series()
    interface.series_io.load_series()
    write("Perform the simulation run")
    hp.simulate()
    write("Write the desired condition files")
    interface.conditions_io.save_conditions()
    write("Write the desired time series files")
    interface.series_io.save_series()


class XMLBase:
    """Base class for the concrete classes |XMLInterface|, |XMLConditions|,
    |XMLSeries|, and |XMLSubseries|.

    Subclasses of |XMLBase| support iterating XML subelements, while
    skipping those named `selections` or `devices`:

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy.data import make_filepath
    >>> interface = XMLInterface("multiple_runs.xml", make_filepath("LahnH"))
    >>> itemgroup = interface.exchange.itemgroups[1]
    >>> for element in itemgroup:
    ...     print(strip(element.tag))
    hland_v1
    >>> for element in itemgroup.models[0].subvars[0].vars[0]:
    ...     print(strip(element.tag))
    alias
    dim
    init
    """

    root: ElementTree.Element

    @property
    def name(self) -> str:
        """Apply function |strip| to the root of the object of the |XMLBase|
        subclass.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
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

    def find(self, name, optional=True):
        """Apply function |find| to the root of the object of the |XMLBase|
        subclass.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> interface.find("timegrid").tag.endswith("timegrid")
        True

        >>> interface.find("wrong")

        >>> interface.find("wrong", optional=False)
        Traceback (most recent call last):
        ...
        AttributeError: The actual XML element `config` does not define \
a XML subelement named `wrong`.  Please make sure your XML file \
follows the relevant XML schema.
        """
        return find(self.root, name, optional)

    def __iter__(self) -> Iterator[ElementTree.Element]:
        for element in self.root:
            name = strip(element.tag)
            if name not in ("selections", "devices"):
                yield element


class XMLInterface(XMLBase):
    """An interface to XML configuration files that are valid concerning
     schema file `HydPyConfigSingleRun.xsd` or `HydPyConfigMultipleRuns.xsd`.

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy.data import make_filepath
    >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
    >>> interface.root.tag
    '{https://github.com/hydpy-dev/hydpy/releases/download/your-hydpy-version/\
HydPyConfigSingleRun.xsd}config'
    >>> interface = XMLInterface('multiple_runs.xml', make_filepath('LahnH'))
    >>> interface.root.tag
    '{https://github.com/hydpy-dev/hydpy/releases/download/your-hydpy-version/\
HydPyConfigMultipleRuns.xsd}config'
    >>> XMLInterface('wrongfilepath.xml', 'wrongdir')    # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to parse the XML configuration \
file ...wrongfilepath.xml, the following error occurred: \
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
        """Raise an error if the actual XML does not agree with one of the
        available schema files.

        # ToDo: should it be accompanied by a script function?

        The first example relies on a distorted version of the configuration
        file `single_run.xml`:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import TestIO, xml_replace
        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> import os
        >>> with TestIO():    # doctest: +ELLIPSIS
        ...     xml_replace("LahnH/single_run",
        ...                 firstdate="1996-01-32T00:00:00")
        template file: LahnH/single_run.xmlt
        target file: LahnH/single_run.xml
        replacements:
          config_start --> <...HydPyConfigBase.xsd"
                      ...HydPyConfigSingleRun.xsd"> (default argument)
          firstdate --> 1996-01-32T00:00:00 (given argument)
          zip_ --> false (default argument)
          zip_ --> false (default argument)
          config_end --> </hpcsr:config> (default argument)
        >>> with TestIO():
        ...     interface = XMLInterface("single_run.xml", "LahnH")
        >>> interface.validate_xml()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        xmlschema.validators.exceptions.XMLSchemaDecodeError: While trying to \
validate XML file `...single_run.xml`, the following error occurred: failed \
validating '1996-01-32T00:00:00' with XsdAtomicBuiltin(name='xs:dateTime')...
        ...
        Reason: day is out of range for month
        ...
        Schema:
        ...
        Instance:
        ...
          <firstdate xmlns="https://github.com/hydpy-dev/hydpy/releases/\
download/your-hydpy-version/HydPyConfigBase.xsd">1996-01-32T00:00:00</firstdate>
        ...
        Path: /hpcsr:config/timegrid/firstdate
        ...

        In the second example, we examine a correct configuration file:

        >>> with TestIO():    # doctest: +ELLIPSIS
        ...     xml_replace("LahnH/single_run")
        ...     interface = XMLInterface("single_run.xml", "LahnH")
        template file: LahnH/single_run.xmlt
        target file: LahnH/single_run.xml
        replacements:
          config_start --> <...HydPyConfigBase.xsd"
                      ...HydPyConfigSingleRun.xsd"> (default argument)
          firstdate --> 1996-01-01T00:00:00 (default argument)
          zip_ --> false (default argument)
          zip_ --> false (default argument)
          config_end --> </hpcsr:config> (default argument)
        >>> interface.validate_xml()

        The XML configuration file must correctly refer to the corresponding
        schema file:

        >>> with TestIO():    # doctest: +ELLIPSIS
        ...     xml_replace("LahnH/single_run",
        ...                 config_start="<config>",
        ...                 config_end="</config>")
        ...     interface = XMLInterface("single_run.xml", "LahnH")
        template file: LahnH/single_run.xmlt
        target file: LahnH/single_run.xml
        replacements:
          config_start --> <config> (given argument)
          firstdate --> 1996-01-01T00:00:00 (default argument)
          zip_ --> false (default argument)
          zip_ --> false (default argument)
          config_end --> </config> (given argument)
        >>> interface.validate_xml()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to validate XML file `...single_run.xml`, \
the following error occurred: Configuration file `single_run.xml` does not \
correctly refer to one of the available XML schema files \
(HydPyConfigSingleRun.xsd and HydPyConfigMultipleRuns.xsd).

        XML files based on `HydPyConfigMultipleRuns.xsd` can be validated
        as well:

        >>> with TestIO():
        ...     interface = XMLInterface("multiple_runs.xml", "LahnH")
        >>> interface.validate_xml()    # doctest: +ELLIPSIS
        """
        try:
            filenames = ("HydPyConfigSingleRun.xsd", "HydPyConfigMultipleRuns.xsd")
            for name in filenames:
                if name in self.root.tag:
                    schemafile = name
                    break
            else:
                raise RuntimeError(
                    f"Configuration file `{os.path.split(self.filepath)[-1]}` "
                    f"does not correctly refer to one of the available XML "
                    f"schema files ({objecttools.enumeration(filenames)})."
                )
            confpath: str = conf.__path__[0]  # type: ignore[attr-defined, name-defined] # pylint: disable=line-too-long
            schemapath = os.path.join(confpath, schemafile)
            schema = xmlschema.XMLSchema(schemapath)
            schema.validate(self.filepath)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to validate XML file `{self.filepath}`"
            )

    def update_options(self) -> None:
        """Update the |Options| object available in module |pub| with the
        values defined in the `options` XML element.

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.timegrids
            >>> del pub.options.simulationstep

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import pub
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> pub.options.ellipsis = 0
        >>> pub.options.parameterstep = "1h"
        >>> pub.options.printprogress = True
        >>> pub.options.printincolor = True
        >>> pub.options.reprdigits = -1
        >>> pub.options.utcoffset = -60
        >>> pub.options.warnsimulationstep = 0
        >>> interface.update_options()
        >>> pub.options
        Options(
            autocompile -> 1
            checkseries -> 1
            dirverbose -> 0
            ellipsis -> 0
            flattennetcdf -> 1
            forcecompiling -> 0
            isolatenetcdf -> 1
            parameterstep -> Period("1d")
            printprogress -> 0
            printincolor -> 0
            reprcomments -> 0
            reprdigits -> 6
            simulationstep -> Period()
            skipdoctests -> 0
            timeaxisnetcdf -> 0
            trimvariables -> 1
            usecython -> 1
            usedefaultvalues -> 0
            utclongitude -> 15
            utcoffset -> 60
            warnmissingcontrolfile -> 0
            warnmissingobsfile -> 1
            warnmissingsimfile -> 1
            warnsimulationstep -> 0
            warntrim -> 1
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
        options.printincolor = False

    def update_timegrids(self) -> None:
        """Update the |Timegrids| object available in module |pub| with the
        values defined in the `timegrid` XML element.

        Usually, one would prefer to define `firstdate`, `lastdate`, and
        `stepsize` elements as in the XML configuration file of the
        `LahnH` example project:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> from hydpy.auxs.xmltools import XMLInterface

        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     XMLInterface("single_run.xml").update_timegrids()
        >>> pub.timegrids
        Timegrids(Timegrid("1996-01-01T00:00:00",
                           "1996-01-06T00:00:00",
                           "1d"))

        Alternatively, one can provide the file path to a `seriesfile`,
        which must be a valid NetCDF file.  The |XMLInterface| object
        then interprets the file's time information:

        >>> name = "LahnH/series/input/hland_v1_input_p.nc"
        >>> with TestIO():
        ...     with open("LahnH/single_run.xml") as file_:
        ...         lines = file_.readlines()
        ...     for idx, line in enumerate(lines):
        ...         if "<timegrid>" in line:
        ...             break
        ...     with open("LahnH/single_run.xml", "w") as file_:
        ...         _ = file_.write("".join(lines[:idx+1]))
        ...         _ = file_.write(
        ...             f"        <seriesfile>{name}</seriesfile>\\n")
        ...         _ = file_.write("".join(lines[idx+4:]))
        ...     XMLInterface("single_run.xml").update_timegrids()
        >>> pub.timegrids
        Timegrids(Timegrid("1996-01-01 00:00:00",
                           "2007-01-01 00:00:00",
                           "1d"))
        """
        timegrid_xml = self.find("timegrid", optional=False)
        try:
            hydpy.pub.timegrids = (
                timegrid_xml[0].text,
                timegrid_xml[1].text,
                timegrid_xml[2].text,
            )
        except IndexError:
            seriesfile = find(timegrid_xml, "seriesfile", optional=False).text
            with netcdf4.Dataset(seriesfile) as ncfile:
                hydpy.pub.timegrids = timetools.Timegrids(
                    netcdftools.query_timegrid(ncfile)
                )

    @property
    def selections(self) -> selectiontools.Selections:
        # noinspection PyUnresolvedReferences
        """The |Selections| object defined on the main level of the actual
        XML file.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.find("selections").text = "headwaters streams"
        >>> selections = interface.selections
        >>> for selection in selections:
        ...     print(selection.name)
        headwaters
        streams
        >>> selections.headwaters
        Selection("headwaters",
                  nodes=("dill", "lahn_1"),
                  elements=("land_dill", "land_lahn_1"))
        >>> interface.find("selections").text = "head_waters"
        >>> interface.selections
        Traceback (most recent call last):
        ...
        NameError: The XML configuration file tries to define a selection \
using the text `head_waters`, but the actual project does not  handle such \
a `Selection` object.
        """
        return _query_selections(self.find("selections", optional=False))

    @property
    def devices(self) -> selectiontools.Selection:
        """The additional devices defined on the main level of the actual
        XML file collected by a |Selection| object.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.devices
        Selection("temporary_result_of_xml_parsing",
                  nodes="dill",
                  elements=("land_dill", "land_lahn_1"))
        >>> interface.find("devices").text = "land_lahn1"
        >>> interface.devices
        Traceback (most recent call last):
        ...
        NameError: The XML configuration file tries to define additional \
devices using the text `land_lahn1`, but the complete selection of the \
actual project does neither handle a `Node` or `Element` object with such \
a name or keyword.
        """
        return _query_devices(self.find("devices", optional=False))

    @property
    def elements(self) -> Iterator[devicetools.Element]:
        """Yield all |Element| objects returned by |XMLInterface.selections|
        and |XMLInterface.devices| without duplicates.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.find("selections").text = "headwaters streams"
        >>> for element in interface.elements:
        ...      print(element.name)
        land_dill
        land_lahn_1
        stream_dill_lahn_2
        stream_lahn_1_lahn_2
        stream_lahn_2_lahn_3
        """
        selections = copy.copy(self.selections)
        selections += self.devices
        elements: Set[devicetools.Element] = set()
        for selection in selections:
            for element in selection.elements:
                if element not in elements:
                    elements.add(element)
                    yield element

    @property
    def fullselection(self) -> selectiontools.Selection:
        """A |Selection| object containing all |Element| and |Node| objects
        defined by |XMLInterface.selections| and |XMLInterface.devices|.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.find("selections").text = "nonheadwaters"
        >>> interface.fullselection
        Selection("fullselection",
                  nodes=("dill", "lahn_2", "lahn_3"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3"))
        """
        fullselection = selectiontools.Selection("fullselection")
        for selection in self.selections:
            fullselection += selection
        fullselection += self.devices
        return fullselection

    @property
    def conditions_io(self) -> "XMLConditions":
        """The `condition_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLConditions(self, self.find("conditions_io", optional=False))

    @property
    def series_io(self) -> "XMLSeries":
        """The `series_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLSeries(self, self.find("series_io", optional=False))

    @property
    def exchange(self) -> "XMLExchange":
        """The `exchange` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface(
        ...     "multiple_runs.xml", make_filepath("LahnH"))
        >>> strip(interface.exchange.root.tag)
        'exchange'
        """
        return XMLExchange(self, self.find("exchange", optional=False))


class XMLConditions(XMLBase):
    """Helper class for |XMLInterface| responsible for loading and
    saving initial conditions."""

    def __init__(self, master: XMLInterface, root: ElementTree.Element):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    def load_conditions(self) -> None:
        """Load the condition files of the |Model| objects of all |Element|
        objects returned by |XMLInterface.elements|:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.find("selections").text = "headwaters"
        ...     interface.conditions_io.load_conditions()
        >>> hp.elements.land_lahn_1.model.sequences.states.lz
        lz(8.18711)
        >>> hp.elements.land_lahn_2.model.sequences.states.lz
        lz(nan)
        """
        hydpy.pub.conditionmanager.currentdir = str(
            self.find("inputdir", optional=False).text
        )
        for element in self.master.elements:
            element.model.sequences.load_conditions()

    def save_conditions(self) -> None:
        """Save the condition files of the |Model| objects of all |Element|
        objects returned by |XMLInterface.elements|:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> import os
        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     hp.elements.land_dill.model.sequences.states.lz = 999.0
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.find("selections").text = "headwaters"
        ...     interface.conditions_io.save_conditions()
        ...     dirpath = "LahnH/conditions/init_1996_01_06"
        ...     with open(os.path.join(dirpath, "land_dill.py")) as file_:
        ...         print(file_.readlines()[11].strip())
        ...     os.path.exists(os.path.join(dirpath, "land_lahn_2.py"))
        lz(999.0)
        False
        >>> from hydpy import xml_replace
        >>> with TestIO():
        ...     xml_replace("LahnH/single_run", printflag=False, zip_="true")
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.find("selections").text = "headwaters"
        ...     os.path.exists("LahnH/conditions/init_1996_01_06.zip")
        ...     interface.conditions_io.save_conditions()
        ...     os.path.exists("LahnH/conditions/init_1996_01_06.zip")
        False
        True
        """
        hydpy.pub.conditionmanager.currentdir = str(
            self.find("outputdir", optional=False).text
        )
        for element in self.master.elements:
            element.model.sequences.save_conditions()
        if self.find("zip", optional=False).text == "true":
            hydpy.pub.conditionmanager.zip_currentdir()


class XMLSeries(XMLBase):
    """Helper class for |XMLInterface| responsible for loading and
    saving time series data, which is further delegated to suitable
    instances of class |XMLSubseries|."""

    def __init__(self, master: XMLInterface, root: ElementTree.Element):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    @property
    def readers(self) -> List["XMLSubseries"]:
        """The reader XML elements defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> for reader in interface.series_io.readers:
        ...     print(reader.info)
        all input data
        """
        return [XMLSubseries(self, _) for _ in self.find("readers", optional=False)]

    @property
    def writers(self) -> List["XMLSubseries"]:
        """The writer XML elements defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> for writer in interface.series_io.writers:
        ...     print(writer.info)
        precipitation
        soilmoisture
        averaged
        """
        return [XMLSubseries(self, _) for _ in self.find("writers", optional=False)]

    def prepare_series(self) -> None:
        # noinspection PyUnresolvedReferences
        """Call |XMLSubseries.prepare_series| of all |XMLSubseries|
        objects with the same memory |set| object.

        >>> from hydpy.auxs.xmltools import XMLInterface, XMLSubseries
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> series_io = interface.series_io
        >>> from unittest import mock
        >>> prepare_series = XMLSubseries.prepare_series
        >>> XMLSubseries.prepare_series = mock.MagicMock()
        >>> series_io.prepare_series()
        >>> args = XMLSubseries.prepare_series.call_args_list
        >>> len(args) == len(series_io.readers) + len(series_io.writers)
        True
        >>> args[0][0][0]
        set()
        >>> args[0][0][0] is args[-1][0][0]
        True
        >>> XMLSubseries.prepare_series = prepare_series
        """
        memory: Set[sequencetools.IOSequence] = set()
        for output in itertools.chain(self.readers, self.writers):
            output.prepare_series(memory)

    def load_series(self) -> None:
        """Call |XMLSubseries.load_series| of all |XMLSubseries| objects
        handles as "readers"."""
        for input_ in self.readers:
            input_.load_series()

    def save_series(self) -> None:
        """Call |XMLSubseries.load_series| of all |XMLSubseries| objects
        handles as "writers"."""
        for writer in self.writers:
            writer.save_series()


class XMLSelector(XMLBase):
    """ToDo"""

    master: XMLBase
    root: ElementTree.Element

    @property
    def selections(self) -> selectiontools.Selections:
        """The |Selections| object defined for the respective `reader`
        or `writer` element of the actual XML file. ToDo

        If the `reader` or `writer` element does not define a special
        selections element, the general |XMLInterface.selections| element
        of |XMLInterface| is used.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.selections.names)
        all input data ()
        precipitation ('headwaters',)
        soilmoisture ('complete',)
        averaged ('complete',)

        If property |XMLSelector.selections| does not find the definition
        of a |Selections| object, it raises the following error:

        >>> interface.root.remove(interface.find("selections"))
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.selections.names)
        Traceback (most recent call last):
        ...
        AttributeError: Unable to find a XML element named "selections".  \
Please make sure your XML file follows the relevant XML schema.
        """
        selections = self.find("selections")
        master: XMLBase = self
        while selections is None:
            master = getattr(master, "master", None)
            if master is None:
                raise AttributeError(
                    'Unable to find a XML element named "selections".  '
                    "Please make sure your XML file follows the "
                    "relevant XML schema."
                )
            selections = master.find("selections")
        return _query_selections(selections)

    @property
    def devices(self) -> selectiontools.Selection:
        """The additional devices defined for the respective `reader`
        or `writer` element contained within a |Selection| object. ToDo

        If the `reader` or `writer` element does not define its own additional
        devices, |XMLInterface.devices| of |XMLInterface| is used.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.devices.nodes, seq.devices.elements)
        all input data Nodes() \
Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")
        precipitation Nodes() Elements("land_lahn_1", "land_lahn_2")
        soilmoisture Nodes("dill") Elements("land_dill", "land_lahn_1")
        averaged Nodes() Elements()

        If property |XMLSelector.selections| does not find the definition
        of a |Selections| object, it raises the following error:

        >>> interface.root.remove(interface.find("devices"))
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.devices.nodes, seq.devices.elements)
        Traceback (most recent call last):
        ...
        AttributeError: Unable to find a XML element named "devices".  \
Please make sure your XML file follows the relevant XML schema.
        """
        devices = self.find("devices")
        master: XMLBase = self
        while devices is None:
            master = getattr(master, "master", None)
            if master is None:
                raise AttributeError(
                    'Unable to find a XML element named "devices".  '
                    "Please make sure your XML file follows the "
                    "relevant XML schema."
                )
            devices = master.find("devices")
        return _query_devices(devices)

    @overload
    def _get_devices(self, attr: Literal["nodes"]) -> Iterator[devicetools.Node]:
        """Extract all nodes."""

    @overload
    def _get_devices(self, attr: Literal["elements"]) -> Iterator[devicetools.Element]:
        """Extract all elements."""

    def _get_devices(self, attr):
        """Extract all nodes or elements."""
        selections = copy.copy(self.selections)
        selections += self.devices
        devices: Set[devicetools.Device] = set()
        for selection in selections:
            for device in getattr(selection, attr):
                if device not in devices:
                    devices.add(device)
                    yield device

    @property
    def elements(self) -> Iterator[devicetools.Element]:
        """Return the |Element| objects selected by the actual
        `reader` or `writer` element. ToDo

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> for element in interface.series_io.writers[0].elements:
        ...     print(element.name)
        land_dill
        land_lahn_1
        land_lahn_2
        """
        return self._get_devices("elements")

    @property
    def nodes(self) -> Iterator[devicetools.Node]:
        """Return the |Node| objects selected by the actual
        `reader` or `writer` element. ToDo

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> for node in interface.series_io.writers[0].nodes:
        ...     print(node.name)
        dill
        lahn_1
        """
        return self._get_devices("nodes")


class XMLSubseries(XMLSelector):
    """Helper class for |XMLSeries| responsible for loading and
    saving time series data."""

    def __init__(self, master: XMLSeries, root: ElementTree.Element):
        self.master: XMLSeries = master
        self.root: ElementTree.Element = root

    @property
    def info(self) -> str:
        """Info attribute of the actual XML `reader` or `writer` element."""
        return self.root.attrib["info"]

    def prepare_sequencemanager(self) -> None:
        """Configure the |SequenceManager| object available in module
        |pub| following the definitions of the actual XML `reader` or
        `writer` element when available; if not use those of the XML
        `series_io` element.

        Compare the following results with `single_run.xml` to see that the
        first `writer` element defines the input file type specifically,
        that the second `writer` element defines a general file type, and
        that the third `writer` element does not define any file type (the
        principle mechanism is the same for other options, e.g. the
        aggregation mode):

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy("LahnH")
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface("single_run.xml")
        >>> series_io = interface.series_io
        >>> with TestIO():
        ...     series_io.writers[0].prepare_sequencemanager()
        >>> pub.sequencemanager.inputfiletype
        'asc'
        >>> pub.sequencemanager.fluxfiletype
        'npy'
        >>> pub.sequencemanager.fluxaggregation
        'none'
        >>> with TestIO():
        ...     series_io.writers[1].prepare_sequencemanager()
        >>> pub.sequencemanager.statefiletype
        'nc'
        >>> pub.sequencemanager.stateoverwrite
        False
        >>> with TestIO():
        ...     series_io.writers[2].prepare_sequencemanager()
        >>> pub.sequencemanager.statefiletype
        'npy'
        >>> pub.sequencemanager.fluxaggregation
        'mean'
        >>> pub.sequencemanager.inputoverwrite
        True
        >>> pub.sequencemanager.inputdirpath
        'LahnH/series/input'
        """
        for config, convert in (
            ("filetype", lambda x: x),
            ("aggregation", lambda x: x),
            ("overwrite", lambda x: x.lower() == "true"),
            ("dirpath", lambda x: x),
        ):
            xml_special = self.find(config)
            xml_general = self.master.find(config)
            for name_manager, name_xml in zip(
                ("input", "flux", "state", "node"),
                ("inputs", "fluxes", "states", "nodes"),
            ):
                value: Optional[str] = None
                for xml, attr_xml in zip(
                    (xml_special, xml_special, xml_general, xml_general),
                    (name_xml, "general", name_xml, "general"),
                ):
                    if xml is not None:
                        element = find(xml, attr_xml)
                        if element is not None:
                            value = element.text
                            break
                setattr(
                    hydpy.pub.sequencemanager, f"{name_manager}{config}", convert(value)
                )

    @property
    def model2subs2seqs(self) -> Dict[str, Dict[str, List[str]]]:
        """A nested |collections.defaultdict| containing the model specific
        information provided by the XML `sequences` element.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> series_io = interface.series_io
        >>> model2subs2seqs = series_io.writers[2].model2subs2seqs
        >>> for model, subs2seqs in sorted(model2subs2seqs.items()):
        ...     for subs, seq in sorted(subs2seqs.items()):
        ...         print(model, subs, seq)
        hland_v1 fluxes ['pc', 'tf']
        hland_v1 states ['sm']
        hstream_v1 states ['qjoints']
        """
        model2subs2seqs: Dict[str, Dict[str, List[str]]] = collections.defaultdict(
            lambda: collections.defaultdict(list)
        )
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
    def subs2seqs(self) -> Dict[str, List[str]]:
        """A |collections.defaultdict| containing the node-specific
        information provided by XML `sequences` element.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy.data import make_filepath
        >>> interface = XMLInterface("single_run.xml", make_filepath("LahnH"))
        >>> series_io = interface.series_io
        >>> subs2seqs = series_io.writers[2].subs2seqs
        >>> for subs, seq in sorted(subs2seqs.items()):
        ...     print(subs, seq)
        node ['sim', 'obs']
        """
        subs2seqs: Dict[str, List[str]] = collections.defaultdict(list)
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
            model = element.model
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

    def prepare_series(self, memory: Set[sequencetools.IOSequence]) -> None:
        """Call |IOSequence.activate_ram| of all sequences selected by
        the given output element of the actual XML file.

        Use the memory argument to pass in already prepared sequences;
        newly prepared sequences will be added.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        >>> interface.update_timegrids()
        >>> series_io = interface.series_io

        >>> memory = set()
        >>> pc = hp.elements.land_dill.model.sequences.fluxes.pc
        >>> pc.ramflag
        False
        >>> series_io.writers[0].prepare_series(memory)
        >>> pc in memory
        True
        >>> pc.ramflag
        True

        >>> pc.deactivate_ram()
        >>> pc.ramflag
        False
        >>> series_io.writers[0].prepare_series(memory)
        >>> pc.ramflag
        False
        """
        for sequence in self._iterate_sequences():
            if sequence not in memory:
                memory.add(sequence)
                sequence.activate_ram()

    def load_series(self) -> None:
        """Load time series data as defined by the actual XML `reader`
        element.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.update_options()
        ...     interface.update_timegrids()
        ...     series_io = interface.series_io
        ...     series_io.prepare_series()
        ...     series_io.load_series()
        >>> from hydpy import print_values
        >>> print_values(
        ...     hp.elements.land_dill.model.sequences.inputs.t.series[:3])
        -0.298846, -0.811539, -2.493848
        """
        hydpy.pub.sequencemanager.open_netcdfreader()
        self.prepare_sequencemanager()
        for sequence in self._iterate_sequences():
            sequence.load_ext()
        hydpy.pub.sequencemanager.close_netcdfreader()

    def save_series(self) -> None:
        """Save time series data as defined by the actual XML `writer`
        element.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        ...     interface = XMLInterface("single_run.xml")
        ...     interface.update_options()
        >>> interface.update_timegrids()
        >>> series_io = interface.series_io
        >>> series_io.prepare_series()
        >>> hp.elements.land_dill.model.sequences.fluxes.pc.series[2, 3] = 9.0
        >>> hp.nodes.lahn_2.sequences.sim.series[4] = 7.0
        >>> with TestIO():
        ...     series_io.save_series()
        >>> import numpy
        >>> with TestIO():
        ...     os.path.exists(
        ...         "LahnH/series/output/land_lahn_2_flux_pc.npy")
        ...     os.path.exists(
        ...         "LahnH/series/output/land_lahn_3_flux_pc.npy")
        ...     numpy.load(
        ...         "LahnH/series/output/land_dill_flux_pc.npy")[13+2, 3]
        ...     numpy.load(
        ...         "LahnH/series/output/lahn_2_sim_q_mean.npy")[13+4]
        True
        False
        9.0
        7.0
        """
        hydpy.pub.sequencemanager.open_netcdfwriter()
        self.prepare_sequencemanager()
        for sequence in self._iterate_sequences():
            sequence.save_ext()
        hydpy.pub.sequencemanager.close_netcdfwriter()


class XMLExchange(XMLBase):
    """Helper class for |XMLInterface| responsible for interpreting exchange
    items, accessible via different instances of class |XMLItemgroup|."""

    def __init__(self, master: XMLInterface, root: ElementTree.Element):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    @overload
    def _get_items_of_certain_item_types(
        self, itemgroups: Iterable[str], getitems: Literal[True]
    ) -> List[itemtools.GetItem]:
        """Return |GetItem| objects only."""

    @overload
    def _get_items_of_certain_item_types(
        self, itemgroups: Iterable[str], getitems: Literal[False]
    ) -> List[itemtools.ChangeItem]:
        """Return |ChangeItem| objects only."""

    def _get_items_of_certain_item_types(self, itemgroups, getitems):
        """Return either all |GetItem| or all |ChangeItem| objects."""
        items: List[itemtools.ExchangeItem] = []
        for itemgroup in self.itemgroups:
            if getitems == (itemgroup.name == "getitems"):
                for model in itemgroup.models:
                    for subvars in model.subvars:
                        if subvars.name in itemgroups:
                            items.extend(var.item for var in subvars.vars)
                if "nodes" in itemgroups:
                    for node in itemgroup.nodes:
                        items.extend(var.item for var in node.vars)
        return items

    @property
    def parameteritems(self) -> List[itemtools.ChangeItem]:
        """Create and return all items for changing control parameter values.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> for item in interface.exchange.parameteritems:
        ...     print(item.name)
        alpha
        beta
        lag
        damp
        sfcf_1
        sfcf_2
        sfcf_3
        """
        return self._get_items_of_certain_item_types(["control"], False)

    @property
    def conditionitems(self) -> List[itemtools.ChangeItem]:
        """Return all items for changing condition sequence values.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> for item in interface.exchange.conditionitems:
        ...     print(item.name)
        sm_lahn_2
        sm_lahn_1
        quh
        """
        return self._get_items_of_certain_item_types(["states", "logs"], False)

    @property
    def getitems(self) -> List[itemtools.GetItem]:
        """Return all items for querying the current values or the complete
        time series of sequences.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")
        >>> for item in interface.exchange.getitems:
        ...     print(item.target)
        fluxes_qt
        fluxes_qt_series
        states_sm
        states_sm_series
        nodes_sim_series
        """
        return self._get_items_of_certain_item_types(
            ["control", "inputs", "fluxes", "states", "logs", "nodes"], True
        )

    def prepare_series(self) -> None:
        """Prepare all required |IOSequence.series| arrays via calling method
        |IOSequence.activate_ram|.
        """
        for item in itertools.chain(self.conditionitems, self.getitems):
            for target in item.device2target.values():
                if item.targetspecs.series and not target.ramflag:
                    target.activate_ram()
                # for base in getattr(item, "device2base", {}).values():
                #     if item.basespecs.series and not base.ramflag:
                #         base.activate_ram()   ToDo

    @property
    def itemgroups(self) -> List["XMLItemgroup"]:
        """The relevant |XMLItemgroup| objects."""
        return [XMLItemgroup(self, element) for element in self]


class XMLItemgroup(XMLBase):
    """Helper class for |XMLExchange| responsible for handling the exchange
    items related to model parameter and sequences separately from the
    exchange items of node sequences."""

    def __init__(self, master: XMLExchange, root: ElementTree.Element):
        self.master: XMLExchange = master
        self.root: ElementTree.Element = root

    @property
    def models(self) -> List["XMLModel"]:
        """The required |XMLModel| objects."""
        return [
            XMLModel(self, element) for element in self if strip(element.tag) != "nodes"
        ]

    @property
    def nodes(self) -> List["XMLNode"]:
        """The required |XMLNode| objects."""
        return [
            XMLNode(self, element) for element in self if strip(element.tag) == "nodes"
        ]


class XMLModel(XMLBase):
    """Helper class for |XMLItemgroup| responsible for handling the exchange
    items related to different parameter or sequence groups of |Model|
    objects."""

    def __init__(self, master: XMLItemgroup, root: ElementTree.Element):
        self.master: XMLItemgroup = master
        self.root: ElementTree.Element = root

    @property
    def subvars(self) -> List["XMLSubvars"]:
        """The required |XMLSubVars| objects."""
        return [XMLSubvars(self, element) for element in self]


class XMLSubvars(XMLBase):
    """Helper class for |XMLModel| responsible for handling the exchange
    items related to individual parameters or sequences of |Model| objects."""

    def __init__(self, master: XMLModel, root: ElementTree.Element):
        self.master: XMLModel = master
        self.root: ElementTree.Element = root

    @property
    def vars(self) -> List["XMLVar"]:
        """The required |XMLVar| objects."""
        return [XMLVar(self, element) for element in self]


class XMLNode(XMLBase):
    """Helper class for |XMLItemgroup| responsible for handling the exchange
    items related to individual parameters or sequences of |Node| objects."""

    def __init__(self, master: XMLItemgroup, root: ElementTree.Element):
        self.master: XMLItemgroup = master
        self.root: ElementTree.Element = root

    @property
    def vars(self) -> List["XMLVar"]:
        """The required |XMLVar| objects."""
        return [XMLVar(self, element) for element in self]


class XMLVar(XMLSelector):
    """Helper class for |XMLSubvars| and |XMLNode| responsible for creating
    a defined exchange item."""

    def __init__(self, master: Union[XMLSubvars, XMLNode], root: ElementTree.Element):
        self.master: Union[XMLSubvars, XMLNode] = master
        self.root: ElementTree.Element = root

    @property
    def item(self) -> itemtools.ExchangeItem:
        """The actually defined |ExchangeItem| object.

        We first prepare the `LahnH` example project and then create
        the related |XMLInterface| object defined by the XML configuration
        file `multiple_runs`:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, pub, TestIO, XMLInterface
        >>> hp = HydPy("LahnH")
        >>> pub.timegrids = "1996-01-01", "1996-01-06", "1d"
        >>> with TestIO():
        ...     hp.prepare_everything()
        ...     interface = XMLInterface("multiple_runs.xml")

        One of the defined |SetItem| objects modifies the values of all
        |hland_control.Alpha| objects of application model |hland_v1|.
        We demonstrate this for the control parameter object handled by
        element `land_dill`:

        >>> var = interface.exchange.itemgroups[0].models[0].subvars[0].vars[0]
        >>> item = var.item
        >>> item.value
        array(2.0)
        >>> hp.elements.land_dill.model.parameters.control.alpha
        alpha(1.0)
        >>> item.update_variables()
        >>> hp.elements.land_dill.model.parameters.control.alpha
        alpha(2.0)

        The second example is comparable but focusses on a |SetItem|
        modifying control parameter |hstream_control.Lag| of application
        model |hstream_v1|:

        >>> var = interface.exchange.itemgroups[0].models[2].subvars[0].vars[0]
        >>> item = var.item
        >>> item.value
        array(5.0)
        >>> hp.elements.stream_dill_lahn_2.model.parameters.control.lag
        lag(0.0)
        >>> item.update_variables()
        >>> hp.elements.stream_dill_lahn_2.model.parameters.control.lag
        lag(5.0)

        The third discussed |SetItem| assigns the same value to all entries
        of state sequence |hland_states.SM|, resulting in the some soil
        moisture for all individual hydrological response units of element
        `land_lahn_2`:

        >>> var = interface.exchange.itemgroups[1].models[0].subvars[0].vars[0]
        >>> item = var.item
        >>> item.name
        'sm_lahn_2'
        >>> item.value
        array(123.0)
        >>> hp.elements.land_lahn_2.model.sequences.states.sm
        sm(138.31396, 135.71124, 147.54968, 145.47142, 154.96405, 153.32805,
           160.91917, 159.62434, 165.65575, 164.63255)
        >>> item.update_variables()
        >>> hp.elements.land_lahn_2.model.sequences.states.sm
        sm(123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0, 123.0)

        The fourth |SetItem| is, in contrast to the last example,
        1-dimensional and thus allows to assign different values to the
        individual hydrological response units of element `land_lahn_1`:

        >>> var = interface.exchange.itemgroups[1].models[0].subvars[0].vars[1]
        >>> item = var.item
        >>> item.name
        'sm_lahn_1'
        >>> item.value
        array([ 110.,  120.,  130.,  140.,  150.,  160.,  170.,  180.,  190.,
                200.,  210.,  220.,  230.])
        >>> hp.elements.land_lahn_1.model.sequences.states.sm
        sm(99.27505, 96.17726, 109.16576, 106.39745, 117.97304, 115.56252,
           125.81523, 123.73198, 132.80035, 130.91684, 138.95523, 137.25983,
           142.84148)
        >>> from hydpy import pub
        >>> with pub.options.warntrim(False):
        ...     item.update_variables()
        >>> hp.elements.land_lahn_1.model.sequences.states.sm
        sm(110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0,
           206.0, 206.0, 206.0)

        |AddItem| `sfcf_1`, `sfcf_2`, and `sfcf_3` serve to demonstrate
        how a scalar value (`sfcf_1` and `sfcf_2`) or a vector of values
        can be used to change the value of a "target" parameter
        (|hland_control.SfCF|) in relation to a "base" parameter
        (|hland_control.RfCF|):

        >>> for element in pub.selections.headwaters.elements:
        ...     element.model.parameters.control.rfcf(1.1)
        >>> for element in pub.selections.nonheadwaters.elements:
        ...     element.model.parameters.control.rfcf(1.0)

        >>> for subvars in interface.exchange.itemgroups[2].models[0].subvars:
        ...     for var in subvars.vars:
        ...         var.item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, repr(element.model.parameters.control.sfcf))
        land_dill sfcf(1.4)
        land_lahn_1 sfcf(1.4)
        land_lahn_2 sfcf(1.2)
        land_lahn_3 sfcf(field=1.1, forest=1.2)

        The final three examples focus on |GetItem| objects.  One |GetItem|
        object queries the actual values of the |hland_states.SM| states
        of all relevant elements:

        >>> var = interface.exchange.itemgroups[3].models[0].subvars[1].vars[0]
        >>> hp.elements.land_dill.model.sequences.states.sm = 1.0
        >>> for name, target in var.item.yield_name2value():
        ...     print(name, target)    # doctest: +ELLIPSIS
        land_dill_states_sm [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
1.0, 1.0, 1.0]
        land_lahn_1_states_sm [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, \
170.0, 180.0, 190.0, 200.0, 206.0, 206.0, 206.0]
        land_lahn_2_states_sm [123.0, 123.0, 123.0, 123.0, 123.0, 123.0, \
123.0, 123.0, 123.0, 123.0]
        land_lahn_3_states_sm [101.3124...]

        Another |GetItem| object queries both the actual and the time
        series values of the |hland_fluxes.QT| flux sequence of element
        `land_dill`:

        >>> vars_ = interface.exchange.itemgroups[3].models[0].subvars[0].vars
        >>> qt = hp.elements.land_dill.model.sequences.fluxes.qt
        >>> qt(1.0)
        >>> qt.series = 2.0
        >>> for var in vars_:
        ...     for name, target in var.item.yield_name2value():
        ...         print(name, target)    # doctest: +ELLIPSIS
        land_dill_fluxes_qt 1.0
        land_dill_fluxes_qt_series [2.0, 2.0, 2.0, 2.0, 2.0]

        Last but not least, one |GetItem| queries the simulated time
        series values avaiable through node `dill`:

        >>> var = interface.exchange.itemgroups[3].nodes[0].vars[0]
        >>> hp.nodes.dill.sequences.sim.series = range(5)
        >>> for name, target in var.item.yield_name2value():
        ...     print(name, target)    # doctest: +ELLIPSIS
        dill_nodes_sim_series [0.0, 1.0, 2.0, 3.0, 4.0]
        >>> for name, target in var.item.yield_name2value(2, 4):
        ...     print(name, target)    # doctest: +ELLIPSIS
        dill_nodes_sim_series [2.0, 3.0]
        """
        target = f"{self.master.name}.{self.name}"
        if self.master.name == "nodes":
            master = self.master.name
            itemgroup = self.master.master.name
        else:
            master = self.master.master.name
            itemgroup = self.master.master.master.name
        itemclass = _ITEMGROUP2ITEMCLASS[itemgroup]
        if itemgroup == "getitems":
            return self._get_getitem(target, master, itemclass)
        if itemgroup == "setitems":
            return self._get_changeitem(target, master, itemclass, True)
        return self._get_changeitem(target, master, itemclass, False)

    def _get_getitem(
        self, target: str, master: str, itemclass: Type[itemtools.GetItem]
    ) -> itemtools.GetItem:
        item = itemclass(master, target)
        self._collect_variables(item)
        return item

    @overload
    def _get_changeitem(
        self,
        target: str,
        master: str,
        itemclass: Type[itemtools.ChangeItem],
        setitems: Literal[True],
    ) -> itemtools.SetItem:
        """Get a |SetItem| object."""

    @overload
    def _get_changeitem(
        self,
        target: str,
        master: str,
        itemclass: Type[itemtools.ChangeItem],
        setitems: Literal[False],
    ) -> itemtools.MathItem:
        """Get a |MathItem| object."""

    def _get_changeitem(self, target, master, itemclass, setitems):
        dim = self.find("dim", optional=False).text
        init = ",".join(self.find("init", optional=False).text.split())
        alias = self.find("alias", optional=False).text
        if setitems:
            item = itemclass(alias, master, target, ndim=dim)
        else:
            base = strip(list(self)[-1].tag)
            item = itemclass(alias, master, target, base, ndim=dim)
        self._collect_variables(item)
        item.value = eval(init)
        return item

    def _collect_variables(self, item: itemtools.ExchangeItem) -> None:
        selections = self.selections
        selections += self.devices
        item.collect_variables(selections)


class XSDWriter:
    """A pure |classmethod| class for writing the actual XML schema file
    `HydPyConfigBase.xsd`, which makes sure that an XML configuration file
    is readable by class |XMLInterface|.

    Unless you are interested in enhancing HydPy's XML functionalities,
    you should, if any, be interested in method |XSDWriter.write_xsd| only.
    """

    confpath: str = conf.__path__[0]  # type: ignore[attr-defined, name-defined]
    filepath_source: str = os.path.join(confpath, "HydPyConfigBase" + ".xsdt")
    filepath_target: str = filepath_source[:-1]

    @classmethod
    def write_xsd(cls) -> None:
        """Write the complete base schema file `HydPyConfigBase.xsd` based
        on the template file `HydPyConfigBase.xsdt`.

        Method |XSDWriter.write_xsd| adds model specific information to the
        general information of template file `HydPyConfigBase.xsdt` regarding
        reading and writing of time series data and exchanging parameter
        and sequence values e.g. during calibration.

        The following example shows that after writing a new schema file,
        method |XMLInterface.validate_xml| does not raise an error when
        either applied on the XML configuration files `single_run.xml` or
        `multiple_runs.xml` of the `LahnH` example project:

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
        ...     XMLInterface(configfile, make_filepath("LahnH")).validate_xml()
        """
        with open(cls.filepath_source) as file_:
            template = file_.read()
        template = template.replace(
            "<!--include model sequence groups-->", cls.get_insertion()
        )
        template = template.replace(
            "<!--include exchange items-->", cls.get_exchangeinsertion()
        )
        with open(cls.filepath_target, "w") as file_:
            file_.write(template)

    @staticmethod
    def get_modelnames() -> List[str]:
        """Return a sorted |list| containing all application model names.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_modelnames())    # doctest: +ELLIPSIS
        [...'dam_v001', 'dam_v002', 'dam_v003', 'dam_v004', 'dam_v005',...]
        """
        modelspath: str = models.__path__[0]  # type: ignore[attr-defined, name-defined] # pylint: disable=line-too-long
        return sorted(
            str(fn.split(".")[0])
            for fn in os.listdir(modelspath)
            if (fn.endswith(".py") and (fn != "__init__.py"))
        )

    @classmethod
    def get_insertion(cls) -> str:
        """Return the complete string to be inserted into the string of the
        template file.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_insertion())    # doctest: +ELLIPSIS
             <element name="arma_v1"
                      substitutionGroup="hpcb:sequenceGroup"
                      type="hpcb:arma_v1Type"/>
        <BLANKLINE>
             <complexType name="arma_v1Type">
                 <complexContent>
                     <extension base="hpcb:sequenceGroupType">
                         <sequence>
                            <element name="fluxes"
                                     minOccurs="0">
                                <complexType>
                                    <sequence>
                                        <element
                                            name="qin"
                                            minOccurs="0"/>
        ...
                                </complexType>
                            </element>
                         </sequence>
                     </extension>
                 </complexContent>
             </complexType>
        <BLANKLINE>
        """
        indent = 1
        blanks = " " * (indent + 4)
        subs = []
        for name in cls.get_modelnames():
            subs.extend(
                [
                    f'{blanks}<element name="{name}"',
                    f'{blanks}         substitutionGroup="hpcb:sequenceGroup"',
                    f'{blanks}         type="hpcb:{name}Type"/>',
                    "",
                    f'{blanks}<complexType name="{name}Type">',
                    f"{blanks}    <complexContent>",
                    f'{blanks}        <extension base="hpcb:sequenceGroupType">',
                    f"{blanks}            <sequence>",
                ]
            )
            model = importtools.prepare_model(name)
            subs.append(cls.get_modelinsertion(model, indent + 4))
            subs.extend(
                [
                    f"{blanks}            </sequence>",
                    f"{blanks}        </extension>",
                    f"{blanks}    </complexContent>",
                    f"{blanks}</complexType>",
                    "",
                ]
            )
        return "\n".join(subs)

    @classmethod
    def get_modelinsertion(cls, model: "modeltools.Model", indent: int) -> str:
        """Return the insertion string required for the given application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_v1")
        >>> print(XSDWriter.get_modelinsertion(model, 1))   # doctest: +ELLIPSIS
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
        """
        texts = []
        for name in ("inputs", "fluxes", "states"):
            subsequences = getattr(model.sequences, name, None)
            if subsequences:
                texts.append(cls.get_subsequencesinsertion(subsequences, indent))
        return "\n".join(texts)

    @classmethod
    def get_subsequencesinsertion(
        cls, subsequences: sequencetools.SubSequences, indent: int
    ) -> str:
        """Return the insertion string required for the given group of
        sequences.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_v1")
        >>> print(XSDWriter.get_subsequencesinsertion(
        ...     model.sequences.fluxes, 1))    # doctest: +ELLIPSIS
            <element name="fluxes"
                     minOccurs="0">
                <complexType>
                    <sequence>
                        <element
                            name="tmean"
                            minOccurs="0"/>
                        <element
                            name="tc"
                            minOccurs="0"/>
        ...
                        <element
                            name="qt"
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
        >>> model = prepare_model("hland_v1")
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
    def get_exchangeinsertion(cls) -> str:
        """Return the complete string related to the definition of exchange
        items to be inserted into the string of the template file.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_exchangeinsertion())    # doctest: +ELLIPSIS
            <complexType name="arma_v1_mathitemType">
        ...
            <element name="setitems">
        ...
            <complexType name="arma_v1_setitemsType">
        ...
            <element name="additems">
        ...
            <element name="getitems">
        ...
        """
        indent = 1
        subs = [cls.get_mathitemsinsertion(indent)]
        for groupname in ("setitems", "additems", "getitems"):
            subs.append(cls.get_itemsinsertion(groupname, indent))
            subs.append(cls.get_itemtypesinsertion(groupname, indent))
        return "\n".join(subs)

    @classmethod
    def get_mathitemsinsertion(cls, indent: int) -> str:
        """Return a string defining a model specific XML type extending
        `ItemType`.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_mathitemsinsertion(1))    # doctest: +ELLIPSIS
            <complexType name="arma_v1_mathitemType">
                <complexContent>
                    <extension base="hpcb:setitemType">
                        <choice>
                            <element name="control.responses"/>
        ...
                            <element name="logs.logout"/>
                        </choice>
                    </extension>
                </complexContent>
            </complexType>
        <BLANKLINE>
            <complexType name="conv_v001_mathitemType">
        ...
        """
        blanks = " " * (indent * 4)
        subs = []
        for modelname in cls.get_modelnames():
            model = importtools.prepare_model(modelname)
            subs.extend(
                [
                    f'{blanks}<complexType name="{modelname}_mathitemType">',
                    f"{blanks}    <complexContent>",
                    f'{blanks}        <extension base="hpcb:setitemType">',
                    f"{blanks}            <choice>",
                ]
            )
            for subvars in cls._get_subvars(model):
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

    @staticmethod
    def _get_itemstype(modelname: str, itemgroup: str) -> str:
        return f"{modelname}_{itemgroup}Type"

    @classmethod
    def get_itemsinsertion(cls, itemgroup: str, indent: int) -> str:
        """Return a string defining the XML element for the given
        exchange item group.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_itemsinsertion(
        ...     "setitems", 1))    # doctest: +ELLIPSIS
            <element name="setitems">
                <complexType>
                    <sequence>
                        <element ref="hpcb:selections"
                                 minOccurs="0"/>
                        <element ref="hpcb:devices"
                                 minOccurs="0"/>
        ...
                        <element name="hland_v1"
                                 type="hpcb:hland_v1_setitemsType"
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
                f'{blanks}            <element ref="hpcb:devices"',
                f'{blanks}                     minOccurs="0"/>',
            ]
        )
        for modelname in cls.get_modelnames():
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
        """Return a string defining the required types for the given
        exchange item group.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_itemtypesinsertion(
        ...     "setitems", 1))    # doctest: +ELLIPSIS
            <complexType name="arma_v1_setitemsType">
        ...
            </complexType>
        <BLANKLINE>
            <complexType name="dam_v001_setitemsType">
        ...
            <complexType name="nodes_setitemsType">
        ...
        """
        subs = []
        for modelname in cls.get_modelnames():
            subs.append(cls.get_itemtypeinsertion(itemgroup, modelname, indent))
        subs.append(cls.get_nodesitemtypeinsertion(itemgroup, indent))
        return "\n".join(subs)

    @classmethod
    def get_itemtypeinsertion(cls, itemgroup: str, modelname: str, indent: int) -> str:
        """Return a string defining the required types for the given
        combination of an exchange item group and an application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_itemtypeinsertion(
        ...     "setitems", "hland_v1", 1))    # doctest: +ELLIPSIS
            <complexType name="hland_v1_setitemsType">
                <sequence>
                    <element ref="hpcb:selections"
                             minOccurs="0"/>
                    <element ref="hpcb:devices"
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
            f'{blanks}        <element ref="hpcb:devices"',
            f'{blanks}                 minOccurs="0"/>',
            cls.get_subgroupsiteminsertion(itemgroup, modelname, indent + 2),
            f"{blanks}    </sequence>",
            f"{blanks}</complexType>",
            "",
        ]
        return "\n".join(subs)

    @classmethod
    def get_nodesitemtypeinsertion(cls, itemgroup: str, indent: int) -> str:
        """Return a string defining the required types for the given
        combination of an exchange item group and |Node| objects.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_nodesitemtypeinsertion(
        ...     "setitems", 1))    # doctest: +ELLIPSIS
            <complexType name="nodes_setitemsType">
                <sequence>
                    <element ref="hpcb:selections"
                             minOccurs="0"/>
                    <element ref="hpcb:devices"
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
            f'{blanks}        <element ref="hpcb:devices"',
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
        """Return a string defining the required types for the given
        combination of an exchange item group and an application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_subgroupsiteminsertion(
        ...     "setitems", "hland_v1", 1))    # doctest: +ELLIPSIS
            <element name="control"
                     minOccurs="0"
                     maxOccurs="unbounded">
        ...
            </element>
            <element name="inputs"
        ...
            <element name="fluxes"
        ...
            <element name="states"
        ...
            <element name="logs"
        ...
        """
        subs = []
        model = importtools.prepare_model(modelname)
        for subvars in cls._get_subvars(model):
            subs.append(
                cls.get_subgroupiteminsertion(itemgroup, model, subvars, indent)
            )
        return "\n".join(subs)

    @classmethod
    def _get_subvars(
        cls, model: "modeltools.Model"
    ) -> Iterator["variabletools.SubVariables"]:
        yield model.parameters.control
        for name in ("inputs", "fluxes", "states", "logs"):
            subseqs = getattr(model.sequences, name, None)
            if subseqs:
                yield subseqs

    @classmethod
    def get_subgroupiteminsertion(
        cls,
        itemgroup: str,
        model: "modeltools.Model",
        subgroup: "variabletools.SubVariables",
        indent: int,
    ) -> str:
        """Return a string defining the required types for the given
        combination of an exchange item group and a specific variable
        subgroup of an application model or class |Node|.

        Note that for `setitems` and `getitems` `setitemType` and
        `getitemType` are referenced, respectively, and for all others
        the model specific `mathitemType`:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("hland_v1")
        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_subgroupiteminsertion(    # doctest: +ELLIPSIS
        ...     "setitems", model, model.parameters.control, 1))
            <element name="control"
                     minOccurs="0"
                     maxOccurs="unbounded">
                <complexType>
                    <sequence>
                        <element ref="hpcb:selections"
                                 minOccurs="0"/>
                        <element ref="hpcb:devices"
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

        >>> print(XSDWriter.get_subgroupiteminsertion(    # doctest: +ELLIPSIS
        ...     "getitems", model, model.parameters.control, 1))
            <element name="control"
        ...
                        <element name="area"
                                 type="hpcb:getitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
        ...

        >>> print(XSDWriter.get_subgroupiteminsertion(    # doctest: +ELLIPSIS
        ...     "additems", model, model.parameters.control, 1))
            <element name="control"
        ...
                        <element name="area"
                                 type="hpcb:hland_v1_mathitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
        ...

        For sequence classes, additional "series" elements are added:

        >>> print(XSDWriter.get_subgroupiteminsertion(    # doctest: +ELLIPSIS
        ...     "setitems", model, model.sequences.fluxes, 1))
            <element name="fluxes"
        ...
                        <element name="tmean"
                                 type="hpcb:setitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
                        <element name="tmean.series"
                                 type="hpcb:setitemType"
                                 minOccurs="0"
                                 maxOccurs="unbounded"/>
                        <element name="tc"
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
            f'{blanks1}            <element ref="hpcb:devices"',
            f'{blanks1}                     minOccurs="0"/>',
        ]
        seriesflags = [False] if subgroup.name == "control" else [False, True]
        for variable in subgroup:
            for series in seriesflags:
                name = f"{variable.name}.series" if series else variable.name
                subs.append(f'{blanks1}            <element name="{name}"')
                if itemgroup == "setitems":
                    subs.append(f'{blanks2}type="hpcb:setitemType"')
                elif itemgroup == "getitems":
                    subs.append(f'{blanks2}type="hpcb:getitemType"')
                else:
                    subs.append(f'{blanks2}type="hpcb:{model.name}_mathitemType"')
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
