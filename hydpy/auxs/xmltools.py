# -*- coding: utf-8 -*-
"""

>>> from hydpy import pub
>>> pub.options.printprogress = False
>>> import warnings
>>> warnings.filterwarnings('ignore')

>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

>>> from hydpy import HydPy, pub, TestIO, XMLInterface
>>> hp = HydPy('LahnHBV')
>>> with TestIO():
...     xml = XMLInterface()
>>> pub.timegrids = xml.timegrids

>>> pub.sequencemanager.inputfiletype = 'nc'   # ToDo: remove
>>> pub.sequencemanager.fluxoverwrite = True   # ToDo: remove

>>> with TestIO():
...     hp.prepare_network()
...     hp.init_models()
...     hp.load_conditions()
...     hp.prepare_inputseries()
...     pub.sequencemanager.open_netcdf_reader(isolate=True)
...     hp.load_inputseries()
...     pub.sequencemanager.close_netcdf_reader()

>>> xml.prepare_series()

>>> hp.doit()

>>> with TestIO():
...     xml.save_series()

>>> import numpy
>>> with TestIO():
...     array = numpy.load('LahnHBV/sequences/node/lahn_1_sim_q.npy')
>>> all(array[13:] == hp.nodes.lahn_1.sequences.sim.series)
True

>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset('LahnHBV/sequences/output/hland_v1_state_sm.nc')
>>> chars2str(query_variable(ncfile, 'station_names'))[:3]
['land_dill_0', 'land_dill_1', 'land_dill_2']
>>> all(query_variable(ncfile, 'state_sm')[2] == hp.elements.land_dill.model.sequences.states.sm.series[:, 2])
True

>>> ncfile.close()
>>> TestIO.clear()
"""
# import...
# ...from standard library
from typing import Dict, Iterator, List
import collections
import itertools
import os
from xml.etree import ElementTree
# ...from HydPy
from hydpy import pub
from hydpy.core import devicetools
from hydpy.core import sequencetools
from hydpy.core import timetools

namespace = \
    '{https://github.com/tyralla/hydpy/tree/master/hydpy/conf/HydPy2FEWS.xsd}'


def find(root, name) -> ElementTree.Element:
    """Return the first xml element with the given name found in the given
    xml root.

    >>> from hydpy.auxs.xmltools import XMLInterface
    >>> from hydpy import data
    >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
    >>> find(xml.root, 'timegrid').tag.endswith('timegrid')
    True
    """
    return root.find(f'{namespace}{name}')


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
    def filetypes(self) -> Dict[str, str]:
        """A dictionary mapping sequence subgroup names to file types as
        defined in the actual xml file.

        ToDo: finish test (successful try block)

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> xml.filetypes
        OrderedDict([('inputs', 'npy'), ('fluxes', 'npy'), ('states', 'npy')])
        """
        root = self.find('filetype')
        filetypes = collections.OrderedDict()
        for subseqs in ('inputs', 'fluxes', 'states'):
            try:
                filetypes[subseqs] = find(root, subseqs).text
            except AttributeError:
                filetypes[subseqs] = find(root, 'general').text
        return filetypes

    @property
    def outputs(self) -> List['XMLOutput']:
        """Return the output elements defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for output in xml.outputs:
        ...     print(output.info)
        precipitation
        soilmoisture
        averaged
        """
        return [XMLOutput(_) for _ in self.find('outputs')]

    def prepare_series(self):
        """"""
        memory = {}
        for output in self.outputs:
            output.prepare_series(memory)

    def save_series(self):
        filetypes = self.filetypes
        for output in self.outputs:
            output.save_series(filetypes=filetypes)


class XMLOutput(object):

    def __init__(self, root):
        self.root: ElementTree.Element = root

    def find(self, name):
        """Apply function |find| for the root of |XMLOutput|."""
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
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> xml.outputs[0].get_filetype('inputs', {'inputs': 'npy'})
        'asc'
        >>> xml.outputs[1].get_filetype('inputs', {'inputs': 'npy'})
        'nc'
        >>> xml.outputs[2].get_filetype('inputs', {'inputs': 'npy'})
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
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> xml.outputs[0].sequences
        ['hland_v1.inputs.p', 'hland_v1.fluxes.pc', 'hland_v1.fluxes.tf']
        """
        return [strip(_.tag) for _ in self.find('sequences')]

    @property
    def model2subs2seqs(self) -> Dict[str, Dict[str, List[str]]]:
        """A nested |collections.defaultdict| containing the model specific
        information provided by |property| |XMLOutput.sequences|.

        ToDo: test different model types

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> model2subs2seqs = xml.outputs[2].model2subs2seqs
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
    def subs2seqs(self) -> Dict[str, Dict[str, List[str]]]:
        """A nested |collections.defaultdict| containing the node specific
        information provided by |property| |XMLOutput.sequences|.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> subs2seqs = xml.outputs[2].subs2seqs
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
    def elements(self) -> devicetools.Elements:
        """Return the selected elements.

        ToDo: add an actual  selection mechanism

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     xml = XMLInterface()
        >>> xml.outputs[0].elements
        Elements("land_dill", "land_lahn_1", ...,"stream_lahn_1_lahn_2",
                 "stream_lahn_2_lahn_3")
        """
        return pub.selections.complete.elements

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
        ...     xml = XMLInterface()
        >>> xml.outputs[2].nodes
        Nodes("dill", "lahn_1", "lahn_2", "lahn_3")
        """
        return pub.selections.complete.nodes

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
        """ToDo

        ToDo: use "memory"

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface
        >>> hp = HydPy('LahnHBV')
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     xml = XMLInterface()
        >>> pub.timegrids = xml.timegrids
        >>> hp.elements.land_dill.model.sequences.fluxes.pc.ramflag
        False
        >>> xml.prepare_series()
        >>> hp.elements.land_dill.model.sequences.fluxes.pc.ramflag
        True
        """
        for sequence in self._iterate_sequences():
            sequence.activate_ram()

    def save_series(self, filetypes) -> None:
        """ToDo

        ToDo: extend configurations

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy import HydPy, TestIO, XMLInterface, pub
        >>> hp = HydPy('LahnHBV')
        >>> pub.sequencemanager.fluxoverwrite = True   # ToDo: remove
        >>> with TestIO():
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     xml = XMLInterface()
        >>> pub.timegrids = xml.timegrids
        >>> xml.prepare_series()
        >>> hp.elements.land_dill.model.sequences.fluxes.pc.series[2, 3] = 9.0
        >>> hp.nodes.lahn_2.sequences.sim.series[4] = 7.0
        >>> with TestIO():
        ...     xml.save_series()
        >>> import numpy
        >>> with TestIO():
        ...     numpy.load(
        ...         'LahnHBV/sequences/output/land_dill_flux_pc.npy')[13+2, 3]
        ...     numpy.load(
        ...         'LahnHBV/sequences/node/lahn_2_sim_q.npy')[13+4]
        9.0
        7.0
        """
        pub.sequencemanager.inputfiletype = self.get_filetype(
            'inputs', filetypes)
        pub.sequencemanager.fluxfiletype = self.get_filetype(
            'fluxes', filetypes)
        pub.sequencemanager.statefiletype = self.get_filetype(
            'states', filetypes)
        pub.sequencemanager.open_netcdf_writer(flatten=True, isolate=True)
        for sequence in self._iterate_sequences():
            sequence.save_ext()
        pub.sequencemanager.close_netcdf_writer()
