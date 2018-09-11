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
>>> pub.timegrids = interface.timegrids

>>> pub.sequencemanager.generaloverwrite = True   # ToDo: remove

>>> with TestIO():
...     hp.prepare_network()
...     hp.init_models()
...     hp.load_conditions()

>>> sequences = interface.sequences

>>> sequences.prepare_series()
>>> with TestIO():
...     sequences.load_series()

>>> hp.doit()

>>> with TestIO():
...     sequences.save_series()

>>> import numpy
>>> with TestIO():
...     array = numpy.load('LahnHBV/sequences/node/lahn_1_sim_q.npy')
>>> all(array[13:] == hp.nodes.lahn_1.sequences.sim.series)
True

>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset(
...         'LahnHBV/sequences/output/hland_v1_state_sm.nc')
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
    return selectiontools.Selections(
        *(pub.selections[_] for _ in text.split())) # ToDo: wrong name


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
    def sequences(self):
        """The `sequences` element defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface, strip
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> strip(interface.sequences.root.tag)
        'sequences'
        """
        return XMLSequences(self, self.find('sequences'))


class XMLSequences(object):

    def __init__(self, master, root):
        self.master: XMLInterface = master
        self.root: ElementTree.Element = root

    def find(self, name):
        """Apply function |find| for the root of |XMLInterface|."""
        return find(self.root, name)

    @property
    def filetypes(self) -> Dict[str, str]:
        """A dictionary mapping sequence subgroup names to file types as
        defined in the actual xml file.

        ToDo: finish test (successful try block)

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> interface.sequences.filetypes
        OrderedDict([('inputs', 'npy'), ('fluxes', 'npy'), \
('states', 'npy'), ('nodes', 'npy')])
        """
        root = self.find('filetype')
        filetypes = collections.OrderedDict()
        for subseqs in ('inputs', 'fluxes', 'states', 'nodes'):
            try:
                filetypes[subseqs] = find(root, subseqs).text
            except AttributeError:
                filetypes[subseqs] = find(root, 'general').text
        return filetypes

    @property
    def inputs(self) -> List['XMLSequence']:
        """Return the input elements defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for input_ in interface.sequences.inputs:
        ...     print(input_.info)
        all input data
        """
        return [XMLSequence(self, _) for _ in self.find('inputs')]

    @property
    def outputs(self) -> List['XMLSequence']:
        """Return the output elements defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for output in interface.sequences.outputs:
        ...     print(output.info)
        precipitation
        soilmoisture
        averaged
        """
        return [XMLSequence(self, _) for _ in self.find('outputs')]

    def prepare_series(self):
        """Call |XMLSequence.prepare_series| of all |XMLSequence| objects with
        the same memory |set| object.

        >>> from hydpy.auxs.xmltools import XMLInterface, XMLSequence
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> sequences = interface.sequences
        >>> from unittest import mock
        >>> prepare_series = XMLSequence.prepare_series
        >>> XMLSequence.prepare_series = mock.MagicMock()
        >>> sequences.prepare_series()
        >>> args = XMLSequence.prepare_series.call_args_list
        >>> len(args) == len(sequences.inputs) + len(sequences.outputs)
        True
        >>> args[0][0][0]
        set()
        >>> args[0][0][0] is args[-1][0][0]
        True
        >>> XMLSequence.prepare_series = prepare_series
        """
        memory = set()
        for output in itertools.chain(self.inputs, self.outputs):
            output.prepare_series(memory)

    def _apply_function_on_xmlsequence(self, xmlsequences, func):
        filetypes = self.filetypes
        for xmlsequence in xmlsequences:
            func(xmlsequence, filetypes=filetypes)

    def load_series(self):
        self._apply_function_on_xmlsequence(
            self.inputs, XMLSequence.load_series)

    def save_series(self):
        self._apply_function_on_xmlsequence(
            self.outputs, XMLSequence.save_series)


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

    def get_filetype(self, subseqs, defaults):
        """Return the filetype for the given sequence subgroup name defined
        in the actual xml output element when possible; otherwise return the
        given default value.

        Compare the following results with `config.xml` to see that the
        first output element defines the input file type specifically,
        that the second output element defines a general file type, and
        that the third output element does not define any file type:


        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> sequences = interface.sequences
        >>> sequences.outputs[0].get_filetype('inputs', {'inputs': 'npy'})
        'asc'
        >>> sequences.outputs[1].get_filetype('inputs', {'inputs': 'npy'})
        'nc'
        >>> sequences.outputs[2].get_filetype('inputs', {'inputs': 'npy'})
        'npy'
        """
        root = self.find('filetype')
        if root is not None:
            element = find(root, subseqs)
            if element is None:
                element = find(root, 'general')
            if element is not None:
                return element.text
        return defaults[subseqs]

    @property
    def sequences(self) -> List[str]:
        """List of handled xml sequence names.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> interface.sequences.outputs[0].sequences
        ['hland_v1.inputs.p', 'hland_v1.fluxes.pc', 'hland_v1.fluxes.tf']
        """
        return [strip(_.tag) for _ in self.find('series')]

    @property
    def model2subs2seqs(self) -> Dict[str, Dict[str, List[str]]]:
        """A nested |collections.defaultdict| containing the model specific
        information provided by |property| |XMLSequence.sequences|.

        ToDo: test different model types

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> sequences = interface.sequences
        >>> model2subs2seqs = sequences.outputs[2].model2subs2seqs
        >>> for model, subs2seqs in sorted(model2subs2seqs.items()):
        ...     for subs, seq in sorted(subs2seqs.items()):
        ...         print(model, subs, seq)
        hland_v1 fluxes ['pc', 'tf']
        hland_v1 states ['sm']
        """
        model2subs2seqs = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for sequence in self.sequences:
            try:
                model, subseqs, seqname = sequence.split('.')
            except ValueError:
                continue
            model2subs2seqs[model][subseqs].append(seqname)
        return model2subs2seqs

    @property
    def subs2seqs(self) -> Dict[str, List[str]]:
        """A nested |collections.defaultdict| containing the node specific
        information provided by |property| |XMLSequence.sequences|.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> interface = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> sequences = interface.sequences
        >>> subs2seqs = sequences.outputs[2].subs2seqs
        >>> for subs, seq in sorted(subs2seqs.items()):
        ...     print(subs, seq)
        nodes ['sim', 'obs']
        """
        subs2seqs = collections.defaultdict(list)
        for sequence in self.sequences:
            try:
                subseqs, seqname = sequence.split('.')
            except ValueError:
                continue
            subs2seqs[subseqs].append(seqname)
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
        >>> sequences = interface.sequences
        >>> for seq in (sequences.inputs + sequences.outputs):
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
        >>> sequences = interface.sequences
        >>> for seq in (sequences.inputs + sequences.outputs):
        ...     print(seq.info, seq.devices.nodes, seq.devices.elements)
        all input data Nodes() \
Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")
        precipitation Nodes() Elements("land_lahn_2")
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
        for selection in selections:
            for device in getattr(selection, attr):
                yield device

    @property
    def elements(self) -> devicetools.Elements:
        """Return the selected elements.

        ToDo: add an actual  selection mechanism

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> for element in interface.sequences.outputs[0].elements:
        ...     print(element.name)
        land_dill
        land_lahn_1
        land_lahn_2
        """
        return self._get_devices('elements')

    @property
    def nodes(self) -> devicetools.Nodes:
        """Return the selected nodes.

        ToDo: add an actual  selection mechanism

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     interface = XMLInterface()
        >>> for node in interface.sequences.outputs[0].nodes:
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
        >>> sequences = interface.sequences

        >>> memory = set()
        >>> pc = hp.elements.land_dill.model.sequences.fluxes.pc
        >>> pc.ramflag
        False
        >>> sequences.outputs[0].prepare_series(memory)
        >>> pc in memory
        True
        >>> pc.ramflag
        True

        >>> pc.deactivate_ram()
        >>> pc.ramflag
        False
        >>> sequences.outputs[0].prepare_series(memory)
        >>> pc.ramflag
        False
        """
        for sequence in self._iterate_sequences():
            if sequence not in memory:
                memory.add(sequence)
                sequence.activate_ram()

    def _apply_function_on_sequences(self, func, filetypes) -> None:
        pub.sequencemanager.inputfiletype = self.get_filetype(
            'inputs', filetypes)
        pub.sequencemanager.fluxfiletype = self.get_filetype(
            'fluxes', filetypes)
        pub.sequencemanager.statefiletype = self.get_filetype(
            'states', filetypes)
        pub.sequencemanager.nodefiletype = self.get_filetype(
            'nodes', filetypes)
        for sequence in self._iterate_sequences():
            func(sequence)

    def load_series(self, filetypes) -> None:
        """ToDo

        ToDo: extend configurations

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        ...     pub.timegrids = interface.timegrids
        ...     sequences = interface.sequences
        ...     sequences.prepare_series()
        ...     sequences.load_series()
        >>> from hydpy import print_values
        >>> print_values(
        ...     hp.elements.land_dill.model.sequences.inputs.t.series[:3])
        -0.298846, -0.811539, -2.493848
        """
        pub.sequencemanager.open_netcdf_reader(flatten=True, isolate=True)
        self._apply_function_on_sequences(
            sequencetools.IOSequence.load_ext, filetypes)
        pub.sequencemanager.close_netcdf_reader()

    def save_series(self, filetypes) -> None:
        """ToDo

        ToDo: extend configurations

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> pub.sequencemanager.generaloverwrite = True   # ToDo: remove
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     interface = XMLInterface()
        >>> pub.timegrids = interface.timegrids
        >>> sequences = interface.sequences
        >>> sequences.prepare_series()
        >>> hp.elements.land_dill.model.sequences.fluxes.pc.series[2, 3] = 9.0
        >>> hp.nodes.lahn_2.sequences.sim.series[4] = 7.0
        >>> with TestIO():
        ...     sequences.save_series()
        >>> import numpy
        >>> with TestIO():
        ...     os.path.exists(
        ...         'LahnHBV/sequences/output/land_lahn_2_flux_pc.npy')
        ...     os.path.exists(
        ...         'LahnHBV/sequences/output/land_lahn_3_flux_pc.npy')
        ...     numpy.load(
        ...         'LahnHBV/sequences/output/land_dill_flux_pc.npy')[13+2, 3]
        ...     numpy.load(
        ...         'LahnHBV/sequences/node/lahn_2_sim_q.npy')[13+4]
        True
        False
        9.0
        7.0
        """
        pub.sequencemanager.open_netcdf_writer(flatten=True, isolate=True)
        self._apply_function_on_sequences(
            sequencetools.IOSequence.save_ext, filetypes)
        pub.sequencemanager.close_netcdf_writer()
