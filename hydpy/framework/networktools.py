
# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from . import pub


class Network(object):
    
    def __init__(self):
        """Read networkfile and store node-element connections."""
        # initialize dictionaries
        self.nodes, self.elements = {}, {}
        # read all lines of network file
        path = pub.filemanager.networkfile.path.replace('_network.py', '.network')
        for line in open(pub.filemanager.networkfile.path):
            # ignore comments and empty lines
            if line.strip().startswith('#') or (line.strip() == ''):
                continue
            # 1: add new node to self.nodes
            if line.startswith('node'):
                # get node id and name
                node_idx1, node_name1 = line.split()[-2:]
                node_idx1 = int(node_idx1)
                # initialize new node subdictionary
                if node_idx1 not in self.nodes:
                    self.nodes[node_idx1] = {'from': [],
                                          'to':   []}
                # add node name to dictionary
                self.nodes[node_idx1]['name'] = node_name1
            # 2: add new element to self.elements and connect to downstream node (1)
            elif line.startswith('\telement'):
                # get element id and name
                element_idx, element_name = line.split()[-2:]
                element_idx = int(element_idx)
                # initialize new dictionary, connect element to the node downstream
                self.elements[element_idx] = {'name': element_name,
                                           'from': [],
                                           'to':   [node_idx1]}
                # connect node downstream to element
                self.nodes[node_idx1]['from'].append(element_idx)
            # 3: connect node to downstream element (2)
            elif line.startswith('\t\tnode'):
                # get node id and name
                node_idx2 = line.split()[-2]
                node_idx2 = int(node_idx2)
                # initialize new node subdictionary
                if node_idx2 not in self.nodes:
                    self.nodes[node_idx2] = {'from': [],
                                          'to':   []}
                # connect node to element downstream
                self.nodes[node_idx2]['to'].append(element_idx)
                # connect element downstream to node
                self.elements[element_idx]['from'].append(node_idx2)
        # convert node and element dictionaries to lists, indices correspond to ids
        self.nodes = [self.nodes[i] for i in
                     range(max(self.nodes.keys())+1)]
        self.elements = [self.elements[i] for i in
                        range(max(self.elements.keys())+1)]
        # check if numbers of nodes and elements fit to general specifications
        if (len(self.nodes) != pub.nmb_nodes):
            raise RuntimeError, ('number of nodes are inconsistent.\n%s: '
                                 '%d\n%s: %d'
                                 %(pub.projectname, len(self.nodes),
                                   pub.filemanager.networkfile.path, 
                                   pub.nmb_nodes))
        if (len(self.elements) != pub.nmb_elements):
            raise RuntimeError, ('number of elements are inconsistent.\n%s: '
                                 '%d\n%s: %d'
                                 %(pub.projectname,len(self.elements),
                                   pub.filemanager.networkfile.path, 
                                   pub.nmb_elements))     