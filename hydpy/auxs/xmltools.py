# -*- coding: utf-8 -*-
"""

>>> from hydpy import pub
>>> pub.options.printprogress = False
>>> pub.options.reprdigits = 6
>>> import warnings
>>> warnings.filterwarnings('ignore')

>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

>>> from hydpy import HydPy, pub, TestIO, XMLInterface
>>> hp = HydPy('LahnHBV')
>>> with TestIO():
...     interface = XMLInterface()
>>> interface.update_options()
>>> pub.timegrids = interface.timegrids

>>> with TestIO():
...     hp.prepare_network()
...     hp.init_models()
...     hp.load_conditions()

>>> series_io = interface.series_io

>>> series_io.prepare_series()
>>> with TestIO():
...     series_io.load_series()

>>> hp.doit()

>>> with TestIO():
...     series_io.save_series()

>>> import numpy
>>> with TestIO():
...     array = numpy.load('LahnHBV/series/output/lahn_1_sim_q_mean.npy')
>>> all(array[13:] == hp.nodes.lahn_1.sequences.sim.series)
True

>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset(
...         'LahnHBV/series/output/hland_v1_state_sm.nc')
>>> chars2str(query_variable(ncfile, 'station_names'))[:3]
['land_dill_0', 'land_dill_1', 'land_dill_2']
>>> query_variable(ncfile, 'state_sm')[2, 3] == \
hp.elements.land_dill.model.sequences.states.sm.series[3, 2]
True

>>> ncfile.close()
>>> TestIO.clear()
"""
# import...
# ...from standard library
from typing import Dict, Iterator, List
import collections
import copy
import itertools
import os
from xml.etree import ElementTree
# ...from HydPy
from hydpy import pub
from hydpy.core import devicetools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import timetools

namespace = \
    '{https://github.com/tyralla/hydpy/tree/master/hydpy/conf/HydPy2FEWS.xsd}'


def find(root, name) -> ElementTree.Element:
    """Return the first xml element with the given name found in the given
    xml root.

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy import data
    >>> înterface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
    >>> find(înterface.root, 'timegrid').tag.endswith('timegrid')
    True
    """
    return root.find(f'{namespace}{name}')


def _query_selections(xmlelement):
    text = xmlelement.text
    if text is None:
        return selectiontools.Selections()
    selections = []
    try:
        for name in text.split():
            selections.append(pub.selections[name])
    except KeyError:
        raise NameError(
            f'The xml configuration file tries to defines a selection '
            f'using the text `{name}`, but the actual project does not '
            f' handle such a `Selection` object.')
    return selectiontools.Selections(*selections)


def _query_devices(xmlelement):
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
                    f'The xml configuration file tries to defines additional '
                    f'devices using the text `{name}`, but the complete '
                    f'selection of the actual project does neither handle a '
                    f'`Node` or `Element` object with such a name or keyword.')
    return selection


def strip(name) -> str:
    """Remove the xml namespace from the given string and return it.

    >>> from hydpy.auxs.xmltools import strip
    >>> strip('{https://github.com/HydPy2FEWS.xsd}something')
    'something'
    """
    return name.split('}')[-1]


class XMLInterface(object):

    def __init__(self, filepath=None):
        if filepath is None:
            filepath = os.path.join(pub.projectname, 'config.xml')
        self.root = ElementTree.parse(filepath).getroot()

    def find(self, name):
        """Apply function |find| for the root of |XMLInterface|."""
        return find(self.root, name)

    def update_options(self):
        """Update the |Options| object available in module |pub| with the
        values defined in the `options` xml element.

        >>> from hydpy.auxs.xmltools import XMLInterface, pub
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> pub.options.printprogress = True
        >>> pub.options.reprdigits = -1
        >>> pub.options.utcoffset = -60
        >>> pub.options.ellipsis = 0
        >>> pub.options.warnsimulationstep = 0
        >>> xml.update_options()
        >>> pub.options
        Options(
            checkseries -> 1
            dirverbose -> 0
            ellipsis -> 0
            fastcython -> 1
            printprogress -> 0
            printincolor -> 1
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

    @property
    def timegrids(self):
        """The |Timegrids| object defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> xml.timegrids
        Timegrids(Timegrid('1996-01-01T00:00:00',
                           '1996-01-06T00:00:00',
                           '1d'))
        """
        timegrid_xml = self.find('timegrid')
        timegrid = timetools.Timegrid(
            *(timegrid_xml[idx].text for idx in range(3)))
        return timetools.Timegrids(timegrid)

    @property
    def selections(self):
        """The |Selections| object defined on the main level of the actual
        xml file.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
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
        NameError: The xml configuration file tries to defines a selection \
using the text `head_waters`, but the actual project does not  handle such \
a `Selection` object.

        """
        return _query_selections(self.find('selections'))

    @property
    def devices(self) -> selectiontools.Selection:
        """The additional devices defined on the main level of the actual
        xml file collected by a |Selection| object.

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
        NameError: The xml configuration file tries to defines additional \
devices using the text `land_lahn1`, but the complete selection of the \
actual project does neither handle a `Node` or `Element` object with such \
a name or keyword.
        """
        return _query_devices(self.find('devices'))

    @property
    def series_io(self):
        """The `serios_io` element defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> strip(interface.series_io.root.tag)
        'series_io'
        """
        return XMLSequences(self, self.find('series_io'))


class XMLSequences(object):

    def __init__(self, master, root):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    def find(self, name):
        """Apply function |find| for the root of |XMLInterface|."""
        return find(self.root, name)

    @property
    def readers(self) -> List['XMLSequence']:
        """Return the reader elements defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for reader in interface.series_io.readers:
        ...     print(reader.info)
        all input data
        """
        return [XMLSequence(self, _) for _ in self.find('readers')]

    @property
    def writers(self) -> List['XMLSequence']:
        """Return the output elements defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for writer in interface.series_io.writers:
        ...     print(writer.info)
        precipitation
        soilmoisture
        averaged
        """
        return [XMLSequence(self, _) for _ in self.find('writers')]

    def prepare_series(self):
        """Call |XMLSequence.prepare_series| of all |XMLSequence| objects with
        the same memory |set| object.

        >>> from hydpy.auxs.xmltools import XMLInterface, XMLSequence
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> series_io = interface.series_io
        >>> from unittest import mock
        >>> prepare_series = XMLSequence.prepare_series
        >>> XMLSequence.prepare_series = mock.MagicMock()
        >>> series_io.prepare_series()
        >>> args = XMLSequence.prepare_series.call_args_list
        >>> len(args) == len(series_io.readers) + len(series_io.writers)
        True
        >>> args[0][0][0]
        set()
        >>> args[0][0][0] is args[-1][0][0]
        True
        >>> XMLSequence.prepare_series = prepare_series
        """
        memory = set()
        for output in itertools.chain(self.readers, self.writers):
            output.prepare_series(memory)

    def load_series(self):
        for input_ in self.readers:
            input_.load_series()

    def save_series(self):
        for writer in self.writers:
            writer.save_series()


class XMLSequence(object):

    def __init__(self, master, root):
        self.master: XMLSequences = master
        self.root: ElementTree.Element = root

    def find(self, name):
        """Apply function |find| for the root of |XMLSequence|."""
        return find(self.root, name)

    @property
    def info(self) -> str:
        """Info attribute of the xml output element."""
        return self.root.attrib['info']

    def prepare_sequencemanager(self):
        """Configure the |SequenceManager| object available in module |pub|
        in accordance with the definitions of the actual xml input or output
        element when available; if not use those of the xml sequences element.

        Compare the following results with `config.xml` to see that the
        first output element defines the input file type specifically,
        that the second output element defines a general file type, and
        that the third output element does not define any file type (the
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
        information provided by |property| |XMLSequence.series|.

        ToDo: test different model types

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
        """
        model2subs2seqs = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for model in self.find('sequences'):
            model_name = strip(model.tag)
            if model_name == 'nodes':
                continue
            for group in model:
                group_name = strip(group.tag)
                for sequence in group:
                    seq_name = strip(sequence.tag)
                    model2subs2seqs[model_name][group_name].append(seq_name)
        return model2subs2seqs

    @property
    def subs2seqs(self) -> Dict[str, List[str]]:
        """A nested |collections.defaultdict| containing the node specific
        information provided by |property| |XMLSequence.series|.

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
    def selections(self):
        """The |Selections| object defined for the respective input or output
        sequence element of the actual xml file.

        If the input or output element does not define its own selections,
        |XMLInterface.selections| of |XMLInterface| is used.

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
        averaged ('headwaters', 'streams')
        """
        element = self.find('selections')
        if element is None:
            return self.master.master.selections
        return _query_selections(element)

    @property
    def devices(self) -> selectiontools.Selection:
        """The additional devices defined for the respective input or output
        sequence element of the actual xml file collected by a |Selection|
        object.

        If the input or output element does not define its own additional
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

    def _get_devices(self, attr):
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
        """Return the selected elements.

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
        """Return the selected nodes.

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

    def prepare_series(self, memory) -> None:
        """Call |IOSequence.activate_ram| of all sequences selected by
        the given output element of the actual xml file.

        Use the memory argument to pass in sequences within a |set| that
        are prepared already; newly prepared sequences will be added.

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        >>> pub.timegrids = interface.timegrids
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
        """ToDo

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        ...     interface.update_options()
        ...     pub.timegrids = interface.timegrids
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
            isolate=pub.options.isolatenetcdf)
        self.prepare_sequencemanager()
        for sequence in self._iterate_sequences():
            sequence.load_ext()
        pub.sequencemanager.close_netcdf_reader()

    def save_series(self) -> None:
        """ToDo

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        ...     interface.update_options()
        >>> pub.timegrids = interface.timegrids
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
