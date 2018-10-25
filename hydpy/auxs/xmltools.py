# -*- coding: utf-8 -*-
"""This module provides features for executing HydPy workflows based on
XML configuration files.

At the heart of module |xmltools| lies function |exec_xml|, which is
thought to be applied via a command line (see the documentation
on script |hyd| for further information).  |exec_xml| expects that
the HydPy project you want to work with is available in your current
working directory and contains an XML configuration file called `config.xml`
(as in the example project folder `LahnHBV`).  This configuration file
must agree with the XML schema file `config.xsd`, which is available
in the :ref:`configuration` subpackage.  In case you did implement new
or changed existing models, you have to update this schema file.  HydPy
does this automatically through its setup mechanism (see the documentation
on class |XSDWriter|).

To show how to apply |exec_xml| via a command line, we first
copy the `LahnHBV` project into the `iotesting` folder via calling
function |prepare_full_example_1|:

>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

To simulate using the command line, we pass the required text to
function |subprocess.call| of module |subprocess|.  Printing the content
of the resulting log file confirms that something happened:

>>> from hydpy import TestIO, print_latest_logfile
>>> import subprocess
>>> with TestIO():
...     _ = subprocess.run('hyd.py exec_xml LahnHBV', shell=True)
...     print_latest_logfile()    # doctest: +ELLIPSIS
Start HydPy project `LahnHBV` (...).
Read configuration file `conf.xml` (...).
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
<BLANKLINE>

As defined by the XML configuration file, the simulation started on the
first and ended at the sixths January 1996.  The following example shows
the read initial conditions and the written final conditions of
sequence |hland_states.SM| for the 12 hydrological response units of the
subcatchment `land_dill`:

>>> with TestIO():
...     with open('LahnHBV/conditions/init_1996_01_01/land_dill.py') as file_:
...         print(''.join(file_.readlines()[10:12]))
...     with open('LahnHBV/conditions/init_1996_01_06/land_dill.py') as file_:
...         print(''.join(file_.readlines()[9:11]))
sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
   222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)
<BLANKLINE>
sm(183.873078, 179.955801, 198.446011, 195.222634, 210.598689, 208.064445,
   220.611126, 218.630245, 228.741883, 227.152989, 235.308805, 234.042313)
<BLANKLINE>

The intermediate soil moisture values are stored in a NetCDF file called
`hland_v1_state_sm.nc`:

>>> import numpy
>>> from hydpy import print_values
>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset('LahnHBV/series/output/hland_v1_state_sm.nc')
...     chars2str(query_variable(ncfile, 'station_id'))[:3]
...     print_values(query_variable(ncfile, 'state_sm')[0, :])
['land_dill_0', 'land_dill_1', 'land_dill_2']
184.926173, 184.603966, 184.386666, 184.098541, 183.873078
>>> ncfile.close()

Spatially averaged time series values are stored in files ending with
the suffix `_mean`:

>>> with TestIO(clear_all=True):
...     print_values((numpy.load(
...         'LahnHBV/series/output/lahn_1_sim_q_mean.npy')[13:]))
9.621296, 8.503069, 7.774927, 7.34503, 7.15879
"""
# import...
# ...from standard library
from typing import Dict, IO, Iterator, List, Union
import collections
import copy
import datetime
import itertools
import os
from xml.etree import ElementTree
# ...from site-packages
from lxml import etree
# ...from HydPy
from hydpy import conf
from hydpy import models
from hydpy import netcdf4
from hydpy import pub
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import importtools
from hydpy.core import netcdftools
from hydpy.core import objecttools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import timetools


namespace = \
    '{https://github.com/tyralla/hydpy/tree/master/hydpy/conf/config.xsd}'


def find(root, name) -> ElementTree.Element:
    """Return the first XML element with the given name found in the given
    XML root.

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy import data
    >>> înterface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
    >>> find(înterface.root, 'timegrid').tag.endswith('timegrid')
    True
    """
    return root.find(f'{namespace}{name}')


def _query_selections(xmlelement) -> selectiontools.Selections:
    text = xmlelement.text
    if text is None:
        return selectiontools.Selections()
    selections = []
    try:
        for name in text.split():
            selections.append(pub.selections[name])
    except KeyError:
        raise NameError(
            f'The XML configuration file tries to defines a selection '
            f'using the text `{name}`, but the actual project does not '
            f' handle such a `Selection` object.')
    return selectiontools.Selections(*selections)


def _query_devices(xmlelement) -> selectiontools.Selection:
    selection = selectiontools.Selection('temporary_result_of_xml_parsing')
    text = xmlelement.text
    if text is None:
        return selection
    elements = pub.selections.complete.elements
    nodes = pub.selections.complete.nodes
    for name in text.split():
        try:
            selection.elements += getattr(elements, name)
            continue
        except AttributeError:
            try:
                selection.nodes += getattr(nodes, name)
            except AttributeError:
                raise NameError(
                    f'The XML configuration file tries to defines additional '
                    f'devices using the text `{name}`, but the complete '
                    f'selection of the actual project does neither handle a '
                    f'`Node` or `Element` object with such a name or keyword.')
    return selection


def strip(name) -> str:
    """Remove the XML namespace from the given string and return it.

    >>> from hydpy.auxs.xmltools import strip
    >>> strip('{https://github.com/something.xsd}something')
    'something'
    """
    return name.split('}')[-1]


def exec_xml(projectname: str, *, logfile: IO):
    """Perform a HydPy workflow in agreement with the configuration file
    `conf.xml` available in the directory of the given project.

    Function |exec_xml| is a "script function" and is normally used as
    explained in the main documentation on module |xmltools|.  The
    following doctests ensure that calling |exec_xml| directly gives
    the same results as calling it by the command line and that
    the log dates are written correctly:

    >>> from hydpy import pub, TestIO, print_latest_logfile, print_values
    >>> pub.scriptfunctions['exec_xml'].__name__
    'exec_xml'
    >>> pub.scriptfunctions['exec_xml'].__module__
    'hydpy.auxs.xmltools'
    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy.auxs.xmltools import exec_xml
    >>> from hydpy.exe.hyd import prepare_logfile
    >>> from hydpy.core.testtools import mock_datetime_now
    >>> from datetime import datetime
    >>> import numpy
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     with mock_datetime_now(datetime(2000, 1, 1, 12, 30, 0, 123456)):
    ...         logfilepath = prepare_logfile()
    ...         with open(logfilepath, 'a') as logfile:
    ...             exec_xml('LahnHBV', logfile=logfile)
    ...     print_values((numpy.load(
    ...         'LahnHBV/series/output/lahn_1_sim_q_mean.npy')[13:]))
    ...     print_latest_logfile()
    9.621296, 8.503069, 7.774927, 7.34503, 7.15879
    Start HydPy project `LahnHBV` (2000-01-01 12:30:00.123456).
    ...
    """
    def write(text):
        """Write the given text eventually."""
        logfile.flush()
        timestring = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        logfile.write(f'{text} ({timestring}).\n')
        logfile.flush()

    pub.options.printprogress = False
    write(f'Start HydPy project `{projectname}`')
    hp = hydpytools.HydPy(projectname)
    write('Read configuration file `conf.xml`')
    interface = XMLInterface()
    write('Interpret the defined options')
    interface.update_options()
    pub.options.printprogress = False
    write('Interpret the defined period')
    interface.update_timegrids()
    write('Read all network files')
    hp.prepare_network()
    write('Activate the selected network')
    hp.update_devices(interface.fullselection)
    write('Read the required control files')
    hp.init_models()
    write('Read the required condition files')
    interface.conditions_io.load_conditions()
    write('Read the required time series files')
    interface.series_io.prepare_series()
    interface.series_io.load_series()
    write('Perform the simulation run')
    hp.doit()
    write('Write the desired condition files')
    interface.conditions_io.save_conditions()
    write('Write the desired time series files')
    interface.series_io.save_series()


pub.scriptfunctions['exec_xml'] = exec_xml


class XMLBase(object):
    """Base class for the concrete classes |XMLInterface|, |XMLConditions|,
    |XMLSeries|, and |XMLSubseries|."""

    root: ElementTree.Element

    def find(self, name) -> ElementTree.Element:
        """Apply function |find| for the root of the object of the |XMLBase|
        subclass.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> interface.find('timegrid').tag.endswith('timegrid')
        True
        """
        return find(self.root, name)


class XMLInterface(XMLBase):
    """An interface to the XML configuration files that are valid concerning
     schema file `config.xsd`.

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy import data
    >>> _ = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
    >>> XMLInterface('wrongfilepath.xml')    # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to read parse the XML configuration \
file ...wrongfilepath.xml, the following error occurred: \
[Errno 2] No such file or directory: 'wrongfilepath.xml'
     """

    def __init__(self, filepath=None):
        if filepath is None:
            filepath = os.path.join(pub.projectname, 'config.xml')
        self.filepath = filepath
        try:
            self.root = ElementTree.parse(filepath).getroot()
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to read parse the XML configuration file '
                f'{os.path.abspath(filepath)}')

    def validate_xml(self) -> None:
        """Raise an error if the actual XML does not agree with the XML
        schema file `config.xsd`.

        # ToDo: should it be accompanied by a script function?

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> with open(interface.filepath) as xml:
        ...     text = xml.read()
        >>> with open(interface.filepath, 'w') as xml:
        ...     _ = xml.write(text.replace('1996-01-01', '1996-01-32'))
        >>> interface.validate_xml()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        hydpy.core.objecttools.lxml.etree.XMLSyntaxError: While trying to \
parse XML file `...config.xml`, the following error occurred: Element \
'{...config.xsd}firstdate': '1996-01-32T00:00:00' is not a valid value \
of the atomic type 'xs:dateTime'. (<string>, line 0)

        >>> with open(interface.filepath, 'w') as xml:
        ...     _ = xml.write(text)
        >>> interface.validate_xml()
        """
        schema = etree.XMLSchema(
            file=os.path.join(conf.__path__[0], 'config.xsd'))
        parser = etree.XMLParser(schema=schema)
        try:
            etree.parse(source=self.filepath, parser=parser)
        except Exception:
            objecttools.augment_excmessage(
                f'While trying to parse XML file `{self.filepath}`')

    def update_options(self) -> None:
        """Update the |Options| object available in module |pub| with the
        values defined in the `options` XML element.

        >>> from hydpy.auxs.xmltools import XMLInterface, pub
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> pub.options.printprogress = True
        >>> pub.options.printincolor = True
        >>> pub.options.reprdigits = -1
        >>> pub.options.utcoffset = -60
        >>> pub.options.ellipsis = 0
        >>> pub.options.warnsimulationstep = 0
        >>> interface.update_options()
        >>> pub.options
        Options(
            autocompile -> 1
            checkseries -> 1
            dirverbose -> 0
            ellipsis -> 0
            fastcython -> 1
            forcecompiling -> 0
            printprogress -> 0
            printincolor -> 0
            reprcomments -> 0
            reprdigits -> 6
            skipdoctests -> 0
            usecython -> 1
            usedefaultvalues -> 0
            utcoffset -> 60
            warnmissingcontrolfile -> 0
            warnmissingobsfile -> 1
            warnmissingsimfile -> 1
            warnsimulationstep -> 0
            warntrim -> 1
            flattennetcdf -> True
            isolatenetcdf -> True
            timeaxisnetcdf -> 0
        )
        >>> pub.options.printprogress = False
        >>> pub.options.reprdigits = 6
        """
        options = pub.options
        for option in self.find('options'):
            value = option.text
            if value in ('true', 'false'):
                value = value == 'true'
            setattr(options, strip(option.tag), value)
        options.printprogress = False
        options.printincolor = False

    def update_timegrids(self) -> None:
        """Update the |Timegrids| object available in module |pub| with the
        values defined in the `timegrid` XML element.

        Usually, one would prefer to define `firstdate`, `lastdate`, and
        `stepsize` elements as in the XML configuration file of the
        `LahnHBV` example project:

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> from hydpy.auxs.xmltools import XMLInterface

        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     XMLInterface().update_timegrids()
        >>> pub.timegrids
        Timegrids(Timegrid('1996-01-01T00:00:00',
                           '1996-01-06T00:00:00',
                           '1d'))

        Alternatively, one can provide the file path to a `seriesfile`,
        which must be a valid NetCDF file.  The |XMLInterface| object
        then interprets the file's time information:

        >>> name = 'LahnHBV/series/input/hland_v1_input_p.nc'
        >>> with TestIO():
        ...     with open('LahnHBV/config.xml') as file_:
        ...         lines = file_.readlines()
        ...     for idx, line in enumerate(lines):
        ...         if '<timegrid>' in line:
        ...             break
        ...     with open('LahnHBV/config.xml', 'w') as file_:
        ...         _ = file_.write(''.join(lines[:idx+1]))
        ...         _ = file_.write(
        ...             f'        <seriesfile>{name}</seriesfile>\\n')
        ...         _ = file_.write(''.join(lines[idx+4:]))
        ...     XMLInterface().update_timegrids()
        >>> pub.timegrids
        Timegrids(Timegrid('1996-01-01 00:00:00',
                           '2007-01-01 00:00:00',
                           '1d'))
        """
        timegrid_xml = self.find('timegrid')
        try:
            timegrid = timetools.Timegrid(
                *(timegrid_xml[idx].text for idx in range(3)))
            pub.timegrids = timetools.Timegrids(timegrid)
        except IndexError:
            seriesfile = find(timegrid_xml, 'seriesfile').text
            with netcdf4.Dataset(seriesfile) as ncfile:
                pub.timegrids = timetools.Timegrids(
                    netcdftools.query_timegrid(ncfile))

    @property
    def selections(self) -> selectiontools.Selections:
        """The |Selections| object defined on the main level of the actual
        XML file.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> interface.find('selections').text = 'headwaters streams'
        >>> selections = interface.selections
        >>> for selection in selections:
        ...     print(selection.name)
        headwaters
        streams
        >>> selections.headwaters
        Selection("headwaters",
                  elements=("land_dill", "land_lahn_1"),
                  nodes=("dill", "lahn_1"))
        >>> interface.find('selections').text = 'head_waters'
        >>> interface.selections
        Traceback (most recent call last):
        ...
        NameError: The XML configuration file tries to defines a selection \
using the text `head_waters`, but the actual project does not  handle such \
a `Selection` object.
        """
        return _query_selections(self.find('selections'))

    @property
    def devices(self) -> selectiontools.Selection:
        """The additional devices defined on the main level of the actual
        XML file collected by a |Selection| object.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> interface.devices
        Selection("temporary_result_of_xml_parsing",
                  elements=("land_dill", "land_lahn_1"),
                  nodes="dill")
        >>> interface.find('devices').text = 'land_lahn1'
        >>> interface.devices
        Traceback (most recent call last):
        ...
        NameError: The XML configuration file tries to defines additional \
devices using the text `land_lahn1`, but the complete selection of the \
actual project does neither handle a `Node` or `Element` object with such \
a name or keyword.
        """
        return _query_devices(self.find('devices'))

    @property
    def elements(self) -> Iterator[devicetools.Element]:
        """Yield all |Element| objects returned by |XMLInterface.selections|
        and |XMLInterface.devices| without duplicates.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> interface.find('selections').text = 'headwaters streams'
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
        elements = set()
        for selection in selections:
            for element in selection.elements:
                if element not in elements:
                    elements.add(element)
                    yield element

    @property
    def fullselection(self) -> selectiontools.Selection:
        """A |Selection| object containing all |Element| and |Node| objects
        defined by |XMLInterface.selections| and |XMLInterface.devices|.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> interface.find('selections').text = 'nonheadwaters'
        >>> interface.fullselection
        Selection("fullselection",
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3"),
                  nodes=("dill", "lahn_2", "lahn_3"))
        """
        fullselection = selectiontools.Selection('fullselection')
        for selection in self.selections:
            fullselection += selection
        fullselection += self.devices
        return fullselection

    @property
    def conditions_io(self) -> 'XMLConditions':
        """The `condition_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLConditions(self, self.find('conditions_io'))

    @property
    def series_io(self) -> 'XMLSeries':
        """The `series_io` element defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLSeries(self, self.find('series_io'))


class XMLConditions(XMLBase):
    """Helper class for |XMLInterface| responsible for loading and
    saving initial conditions."""

    def __init__(self, master, root):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    def load_conditions(self) -> None:
        """Load the condition files of the |Model| objects of all |Element|
        objects returned by |XMLInterface.elements|:

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        ...     interface.update_timegrids()
        ...     interface.find('selections').text = 'headwaters'
        ...     interface.conditions_io.load_conditions()
        >>> hp.elements.land_lahn_1.model.sequences.states.lz
        lz(8.18711)
        >>> hp.elements.land_lahn_2.model.sequences.states.lz
        lz(nan)
        """
        pub.conditionmanager.currentdir = strip(self.find('inputdir').text)
        for element in self.master.elements:
            element.model.sequences.load_conditions()

    def save_conditions(self) -> None:
        """Save the condition files of the |Model| objects of all |Element|
        objects returned by |XMLInterface.elements|:

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> import os
        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     hp.elements.land_dill.model.sequences.states.lz = 999.0
        ...     interface = XMLInterface()
        ...     interface.update_timegrids()
        ...     interface.find('selections').text = 'headwaters'
        ...     interface.conditions_io.save_conditions()
        ...     dirpath = 'LahnHBV/conditions/init_1996_01_06'
        ...     with open(os.path.join(dirpath, 'land_dill.py')) as file_:
        ...         print(file_.readlines()[11].strip())
        ...     os.path.exists(os.path.join(dirpath, 'land_lahn_2.py'))
        lz(999.0)
        False
        """
        pub.conditionmanager.currentdir = strip(self.find('outputdir').text)
        for element in self.master.elements:
            element.model.sequences.save_conditions()
        if strip(self.find('zip').text) == 'true':
            pub.conditionmanager.zip_currentdir()   # ToDo: test it


class XMLSeries(XMLBase):
    """Helper class for |XMLInterface| responsible for loading and
    saving time series data, which is further delegated to suitable
    instances of class |XMLSubseries|."""

    def __init__(self, master, root):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    @property
    def readers(self) -> List['XMLSubseries']:
        """The reader XML elements defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for reader in interface.series_io.readers:
        ...     print(reader.info)
        all input data
        """
        return [XMLSubseries(self, _) for _ in self.find('readers')]

    @property
    def writers(self) -> List['XMLSubseries']:
        """The writer XML elements defined in the actual XML file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for writer in interface.series_io.writers:
        ...     print(writer.info)
        precipitation
        soilmoisture
        averaged
        """
        return [XMLSubseries(self, _) for _ in self.find('writers')]

    def prepare_series(self) -> None:
        """Call |XMLSubseries.prepare_series| of all |XMLSubseries|
        objects with the same memory |set| object.

        >>> from hydpy.auxs.xmltools import XMLInterface, XMLSubseries
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
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
        memory = set()
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


class XMLSubseries(XMLBase):
    """Helper class for |XMLSeries| responsible for loading and
    saving time series data."""

    def __init__(self, master, root):
        self.master: XMLSeries = master
        self.root: ElementTree.Element = root

    @property
    def info(self) -> str:
        """Info attribute of the actual XML `reader` or `writer` element."""
        return self.root.attrib['info']

    def prepare_sequencemanager(self) -> None:
        """Configure the |SequenceManager| object available in module
        |pub| following the definitions of the actual XML `reader` or
        `writer` element when available; if not use those of the XML
        `series_io` element.

        Compare the following results with `config.xml` to see that the
        first `writer` element defines the input file type specifically,
        that the second `writer` element defines a general file type, and
        that the third `writer` element does not define any file type (the
        principle mechanism is the same for other options, e.g. the
        aggregation mode):

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
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
        'LahnHBV/series/input'
        """
        for config, convert in (
                ('filetype', lambda x: x),
                ('aggregation', lambda x: x),
                ('overwrite', lambda x: x.lower() == 'true'),
                ('dirpath', lambda x: x)):
            xml_special = self.find(config)
            xml_general = self.master.find(config)
            for name_manager, name_xml in zip(
                    ('input', 'flux', 'state', 'node'),
                    ('inputs', 'fluxes', 'states', 'nodes')):
                value = None
                for xml, attr_xml in zip(
                        (xml_special, xml_special, xml_general, xml_general),
                        (name_xml, 'general', name_xml, 'general')):
                    try:
                        value = find(xml, attr_xml).text
                    except AttributeError:
                        continue
                    break
                setattr(pub.sequencemanager,
                        f'{name_manager}{config}',
                        convert(value))

    @property
    def model2subs2seqs(self) -> Dict[str, Dict[str, List[str]]]:
        """A nested |collections.defaultdict| containing the model specific
        information provided by the XML `sequences` element.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> series_io = interface.series_io
        >>> model2subs2seqs = series_io.writers[2].model2subs2seqs
        >>> for model, subs2seqs in sorted(model2subs2seqs.items()):
        ...     for subs, seq in sorted(subs2seqs.items()):
        ...         print(model, subs, seq)
        hland_v1 fluxes ['pc', 'tf']
        hland_v1 states ['sm']
        hstream_v1 states ['qjoints']
        """
        model2subs2seqs = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for model in self.find('sequences'):
            model_name = strip(model.tag)
            if model_name == 'node':
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
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> series_io = interface.series_io
        >>> subs2seqs = series_io.writers[2].subs2seqs
        >>> for subs, seq in sorted(subs2seqs.items()):
        ...     print(subs, seq)
        node ['sim', 'obs']
        """
        subs2seqs = collections.defaultdict(list)
        nodes = find(self.find('sequences'), 'node')
        if nodes is not None:
            for seq in nodes:
                subs2seqs['node'].append(strip(seq.tag))
        return subs2seqs

    @property
    def selections(self) -> selectiontools.Selections:
        """The |Selections| object defined for the respective `reader`
        or `writer` element of the actual XML file.

        If the `reader` or `writer` element does not define a special
        selections element, the general |XMLInterface.selections| element
        of |XMLInterface| is used.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.selections.names)
        all input data ()
        precipitation ('headwaters',)
        soilmoisture ('complete',)
        averaged ('complete',)
        """
        element = self.find('selections')
        if element is None:
            return self.master.master.selections
        return _query_selections(element)

    @property
    def devices(self) -> selectiontools.Selection:
        """The additional devices defined for the respective `reader`
        or `writer` element contained within a |Selection| object.

        If the `reader` or `writer` element does not define its own additional
        devices, |XMLInterface.devices| of |XMLInterface| is used.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> series_io = interface.series_io
        >>> for seq in (series_io.readers + series_io.writers):
        ...     print(seq.info, seq.devices.nodes, seq.devices.elements)
        all input data Nodes() \
Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")
        precipitation Nodes() Elements("land_lahn_1", "land_lahn_2")
        soilmoisture Nodes("dill") Elements("land_dill", "land_lahn_1")
        averaged Nodes() Elements()
        """
        devices = self.find('devices')
        if devices is None:
            return self.master.master.devices
        return _query_devices(devices)

    def _get_devices(self, attr) \
            -> Union[Iterator[devicetools.Node],
                     Iterator[devicetools.Element]]:
        selections = copy.copy(self.selections)
        selections += self.devices
        devices = set()
        for selection in selections:
            for device in getattr(selection, attr):
                if device not in devices:
                    devices.add(device)
                    yield device

    @property
    def elements(self) -> Iterator[devicetools.Element]:
        """Return the |Element| objects selected by the actual
        `reader` or `writer` element.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> for element in interface.series_io.writers[0].elements:
        ...     print(element.name)
        land_dill
        land_lahn_1
        land_lahn_2
        """
        return self._get_devices('elements')

    @property
    def nodes(self) -> Iterator[devicetools.Node]:
        """Return the |Node| objects selected by the actual
        `reader` or `writer` element.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> for node in interface.series_io.writers[0].nodes:
        ...     print(node.name)
        dill
        lahn_1
        """
        return self._get_devices('nodes')

    def _iterate_sequences(self) -> Iterator[sequencetools.IOSequence]:
        return itertools.chain(
            self._iterate_model_sequences(), self._iterate_node_sequences())

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
            for subseqs_name, seq_names in s2s.items():
                for seq_name in seq_names:
                    yield getattr(node.sequences, seq_name)

    def prepare_series(self, memory: set) -> None:
        """Call |IOSequence.activate_ram| of all sequences selected by
        the given output element of the actual XML file.

        Use the memory argument to pass in already prepared sequences;
        newly prepared sequences will be added.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
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

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
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
        pub.sequencemanager.open_netcdf_reader(
            flatten=pub.options.flattennetcdf,
            isolate=pub.options.isolatenetcdf,
            timeaxis=pub.options.timeaxisnetcdf)
        self.prepare_sequencemanager()
        for sequence in self._iterate_sequences():
            sequence.load_ext()
        pub.sequencemanager.close_netcdf_reader()

    def save_series(self) -> None:
        """Save time series data as defined by the actual XML `writer`
        element.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
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
        ...         'LahnHBV/series/output/land_lahn_2_flux_pc.npy')
        ...     os.path.exists(
        ...         'LahnHBV/series/output/land_lahn_3_flux_pc.npy')
        ...     numpy.load(
        ...         'LahnHBV/series/output/land_dill_flux_pc.npy')[13+2, 3]
        ...     numpy.load(
        ...         'LahnHBV/series/output/lahn_2_sim_q_mean.npy')[13+4]
        True
        False
        9.0
        7.0
        """
        pub.sequencemanager.open_netcdf_writer(
            flatten=pub.options.flattennetcdf,
            isolate=pub.options.isolatenetcdf)
        self.prepare_sequencemanager()
        for sequence in self._iterate_sequences():
            sequence.save_ext()
        pub.sequencemanager.close_netcdf_writer()


class XSDWriter(object):
    """Pure |classmethod| class for writing the actual XML schema file
    `config.xsd`, which makes sure that an XML configuration file is
    readable by class |XMLInterface|.

    Unless you are interested in enhancing HydPy's XML functionalities,
    you should, if any, be interested in method |XSDWriter.write_xsd| only.
    """

    filepath_source: str = os.path.join(
        conf.__path__[0], 'config' + '.xsdt')
    filepath_target: str = filepath_source[:-1]

    @classmethod
    def write_xsd(cls) -> None:
        """Write the complete schema file based on the template file
        `config.xsdt`, including the input, flux, and state sequences
        of all application models available at the moment.

        The following example shows that after writing a new schema file,
        method |XMLInterface.validate_xml| does not raise an error when
        applied on the XML configuration file of the `LahnHBV` example
        project:

        >>> from hydpy.auxs.xmltools import XSDWriter, XMLInterface
        >>> from hydpy import data
        >>> xmlpath = data.get_path('LahnHBV', 'config.xml')

        >>> import os
        >>> if os.path.exists(XSDWriter.filepath_target):
        ...     os.remove(XSDWriter.filepath_target)

        >>> XMLInterface(xmlpath).validate_xml()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        lxml.etree.XMLSchemaParseError: \
Failed to locate the main schema resource at '...config.xsd'.

        >>> XSDWriter.write_xsd()
        >>> XMLInterface(xmlpath).validate_xml()
        """
        with open(cls.filepath_source) as file_:
            template = file_.read()
        template = template.replace(
            '<!--include model sequence groups-->', cls.get_insertion())
        with open(cls.filepath_target, 'w') as file_:
            file_.write(template)

    @classmethod
    def get_insertion(cls) -> str:
        """Return the complete string to be inserted into the string of the
        template file.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> print(XSDWriter.get_insertion())    # doctest: +ELLIPSIS
             <element name="arma_v1"
                      substitutionGroup="fews:sequenceGroup"
                      type="fews:arma_v1Type"/>
        <BLANKLINE>
             <complexType name="arma_v1Type">
                 <complexContent>
                     <extension base="fews:sequenceGroupType">
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
        blanks = ' ' * (indent+4)
        subs = []
        filenames = (
            fn.split('.')[0] for fn in os.listdir(models.__path__[0])
            if (fn.endswith('.py') and (fn != '__init__.py')))
        for name in sorted(filenames):
            subs.extend([
                f'{blanks}<element name="{name}"',
                f'{blanks}         substitutionGroup="fews:sequenceGroup"',
                f'{blanks}         type="fews:{name}Type"/>',
                f'',
                f'{blanks}<complexType name="{name}Type">',
                f'{blanks}    <complexContent>',
                f'{blanks}        <extension base="fews:sequenceGroupType">',
                f'{blanks}            <sequence>'])
            model = importtools.prepare_model(name)
            subs.append(cls.get_modelinsertion(model, indent + 4))
            subs.extend([
                f'{blanks}            </sequence>',
                f'{blanks}        </extension>',
                f'{blanks}    </complexContent>',
                f'{blanks}</complexType>',
                f''
            ])
        return '\n'.join(subs)

    @classmethod
    def get_modelinsertion(cls, model, indent) -> str:
        """Return the insertion string required for the given application model.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model('hland_v1')
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
        for name in ('inputs', 'fluxes', 'states'):
            subsequences = getattr(model.sequences, name, None)
            if subsequences:
                texts.append(
                    cls.get_subsequencesinsertion(subsequences, indent))
        return '\n'.join(texts)

    @classmethod
    def get_subsequencesinsertion(cls, subsequences, indent) -> str:
        """Return the insertion string required for the given group of
        sequences.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model('hland_v1')
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
        blanks = ' ' * (indent*4)
        lines = [f'{blanks}<element name="{subsequences.name}"',
                 f'{blanks}         minOccurs="0">',
                 f'{blanks}    <complexType>',
                 f'{blanks}        <sequence>']
        for sequence in subsequences:
            lines.append(cls.get_sequenceinsertion(sequence, indent + 3))
        lines.extend([f'{blanks}        </sequence>',
                      f'{blanks}    </complexType>',
                      f'{blanks}</element>'])
        return '\n'.join(lines)

    @staticmethod
    def get_sequenceinsertion(sequence, indent) -> str:
        """Return the insertion string required for the given sequence.

        >>> from hydpy.auxs.xmltools import XSDWriter
        >>> from hydpy import prepare_model
        >>> model = prepare_model('hland_v1')
        >>> print(XSDWriter.get_sequenceinsertion(model.sequences.fluxes.pc, 1))
            <element
                name="pc"
                minOccurs="0"/>
        """
        blanks = ' ' * (indent*4)
        return (f'{blanks}<element\n'
                f'{blanks}    name="{sequence.name}"\n'
                f'{blanks}    minOccurs="0"/>')
