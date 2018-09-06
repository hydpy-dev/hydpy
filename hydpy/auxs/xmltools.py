# -*- coding: utf-8 -*-
"""

>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

>>> from hydpy import HydPy, pub, TestIO, XMLInterface
>>> hp = HydPy('LahnHBV')
>>> with TestIO():
...     xml = XMLInterface()
>>> pub.timegrids = xml.timegrids
>>> pub.sequencemanager.generalfiletype = 'nc'

>>> pub.options.printprogress = False   # ToDo
>>> import warnings   # ToDo
>>> warnings.filterwarnings('ignore', 'Note that,')   # ToDo

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

>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset('LahnHBV/sequences/node/node_sim_q.nc')
>>> chars2str(query_variable(ncfile, 'station_names'))
['dill', 'lahn_1', 'lahn_2', 'lahn_3']
>>> all(query_variable(ncfile, 'sim_q')[1] == hp.nodes.lahn_1.sequences.sim.series)
True

>>> with TestIO():
...     ncfile = netcdf4.Dataset('LahnHBV/sequences/output/hland_v1_state_sm.nc')
>>> chars2str(query_variable(ncfile, 'station_names'))[:3]
['land_dill_0', 'land_dill_1', 'land_dill_2']
>>> all(query_variable(ncfile, 'state_sm')[2] == hp.elements.land_dill.model.sequences.states.sm.series[:, 2])
True

"""
# import...
# ...from standard library
from typing import Dict, List
import collections
import os
from xml.etree import ElementTree
# ...from HydPy
from hydpy import pub
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
    def outputs(self) -> List[ElementTree.Element]:
        """Return the output elements defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> for output in xml.outputs:
        ...     print(output.info)
        precipitation
        soilmoisture
        """
        return [XMLOutput(_) for _ in self.find('outputs')]

    def prepare_series(self):
        """"""
        memory = {}
        for output in self.outputs:
            output.prepare_series(memory)


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

    @property
    def sequences(self) -> List[str]:
        """List of handled xml sequence names.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> xml.outputs[0].sequences
        ['hland_v1.inputs.p', 'hland_v1.fluxes.pc']
        """
        return [strip(_.tag) for _ in self.find('sequences')]

    @property
    def model2subseqs2seq(self) -> Dict[str, Dict[str, List[str]]]:
        """A nested |collections.defaultdict| containing the information
        provided by |property| |XMLOutput.sequences|.

        ToDo: test different model types

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> result = xml.outputs[0].model2subseqs2seq
        >>> for model, subseqs2seq in sorted(result.items()):
        ...     for subseqs, seq in sorted(subseqs2seq.items()):
        ...         print(model, subseqs, seq)
        hland_v1 fluxes ['pc', 'tf']
        hland_v1 inputs ['p']
        """
        model2subseqs = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for sequence in self.sequences:
            model, subseqs, seqname = sequence.split('.')
            model2subseqs[model][subseqs].append(seqname)
        return model2subseqs

    @property
    def elements(self):
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


    def prepare_series(self, memory):
        """ToDo

        ToDo: add an actual selection mechanism
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
        m2s2s = self.model2subseqs2seq
        for element in self.elements:
            model = element.model
            for name_subseqs, seqnames in m2s2s.get(model.name, {}).items():
                subseqs = getattr(model.sequences, name_subseqs)
                for seqname in seqnames:
                    getattr(subseqs, seqname).activate_ram()
