
# import...
# ...from standard library
from __future__ import division, print_function
import unittest
# ...from HydPy
from hydpy.core.devicetools import *
from hydpy.core.selectiontools import *

class Test01SelectionInitialization(unittest.TestCase):

    def tearDown(self):
        Node.clearregistry()
        Element.clearregistry()

    def test_01_empty(self):
        test = Selection('test')
        self.assertIsInstance(test, Selection)
        self.assertIsInstance(test.nodes, Nodes)
        self.assertIsInstance(test.elements, Elements)
        self.assertFalse(bool(test))
    def test_02_nonempty(self):
        test = Selection('test', nodes='a', elements=('b', 'c'))
        self.assertIsInstance(test, Selection)
        self.assertIsInstance(test.nodes, Nodes)
        self.assertIsInstance(test.elements, Elements)
        self.assertEqual(test.nodes.a.name, 'a')
        self.assertEqual(test.elements.b.name, 'b')
        self.assertEqual(test.elements.c.name, 'c')
        self.assertTrue(bool(test))
    def test_03_copy(self):
        test1 = Selection('test1', nodes='a', elements=('b', 'c'))
        test2 = test1.copy('test2')
        self.assertIsInstance(test2, Selection)
        self.assertEqual(test2.name, 'test2')
        self.assertIsNot(test1, test2)
        self.assertEqual(test2.nodes, test1.nodes)
        self.assertEqual(test2.elements, test1.elements)


class Test02SelectionSelect(unittest.TestCase):

    def setUp(self):
        # e1 + e2 -> n_Q1 -> e3 -> n_Q2 -> e4 + (e7 -> n_Q4 -> e6)-> n_Q3
        # e1 + e2 -> n_T1 -> e3 -> n_T2 -> e5 -> n_T3
        self.n_Q1 = Node('n_Q1', 'Q')
        self.n_T1 = Node('n_T1', 'T')
        self.e1 = Element('e1', outlet='n_Q1')
        self.e1 = Element('e1', outlet='n_T1')
        self.e2 = Element('e2', outlet='n_Q1')
        self.e2 = Element('e2', outlet='n_T1')
        self.n_Q2 = Node('n_Q2', 'Q')
        self.n_T2 = Node('n_T2', 'T')
        self.e3 = Element('e3', inlet='n_Q1', outlet='n_Q2')
        self.e3 = Element('e3', inlet='n_T1', outlet='n_T2')
        self.n_Q3 = Node('n_Q3', 'Q')
        self.e4 = Element('e4', inlet='n_Q2', outlet='n_Q3')
        self.n_T3 = Node('n_T3', 'T')
        self.e5 = Element('e5', inlet='n_T2', outlet='n_T3')
        self.n_Q4 = Node('n_Q4', 'Q')
        self.e6 = Element('e6', inlet='n_Q4', outlet='n_Q3')
        self.e7 = Element('e7', outlet='n_Q4')

        self.complete = Selection('complete',
                                  nodes=Node.registereddevices(),
                                  elements=Element.registereddevices())

    def tearDown(self):
        Node.clearregistry()
        Element.clearregistry()

    def test_01_nextelement(self):
        nodes, elements = self.complete._nextelement(self.e1,
                                                  Nodes(), Elements())
        self.assertEqual(nodes, Nodes())
        self.assertEqual(elements, Elements(self.e1))
    def test_02_nextnode(self):
        nodes, elements = self.complete._nextnode(self.n_Q1,
                                                  Nodes(), Elements())
        self.assertEqual(nodes, Nodes(self.n_Q1))
        self.assertEqual(elements, Elements(self.e1, self.e2))
    def test_03_select_upstream(self):
        test = self.complete.copy('test').select_upstream(self.n_Q3)
        reference = self.complete.copy('reference')
        del(reference.elements.e5)
        del(reference.nodes.n_T2)
        del(reference.nodes.n_T3)
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)
    def test_04_deselect_upstream(self):
        test = self.complete.copy('test').deselect_upstream(self.n_Q3)
        reference = Selection('reference', ['n_T2', 'n_T3'], 'e5')
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)

    def test_05_selectmodelclasses(self):
        with self.assertRaises(RuntimeError):
            self.complete.copy('test').getby_modelclasses('HBV96_zone')
        asdf

    def test_06_select_nodenames(self):
        test = self.complete.copy('test').select_nodenames('n_Q1', 'n_T', 'NO')
        reference = self.complete.copy('test')
        reference.nodes = Nodes('n_Q1', 'n_T1', 'n_T2', 'n_T3')
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)
    def test_07_deselect_nodenames(self):
        test = self.complete.copy('test').deselect_nodenames('n_Q1', 'n_T',
                                                             'NO')
        reference = self.complete.copy('test')
        del(reference.nodes.n_Q1)
        del(reference.nodes.n_T1)
        del(reference.nodes.n_T2)
        del(reference.nodes.n_T3)
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)
    def test_08_select_elementnames(self):
        test = self.complete.copy('test').select_elementnames('e')
        self.assertEqual(test.nodes, self.complete.nodes)
        self.assertEqual(test.elements, self.complete.elements)
        test = self.complete.copy('test').select_elementnames('2')
        reference = self.complete.copy('test')
        reference.elements = Elements('e2')
    def test_09_deselect_elementnames(self):
        test = self.complete.copy('test').deselect_elementnames('e')
        self.assertEqual(test.nodes, self.complete.nodes)
        self.assertEqual(test.elements, Elements())
        test = self.complete.copy('test').deselect_elementnames('2')
        reference = self.complete.copy('test')
        del(reference.elements.e2)
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)


class Test03SelectionMagic(unittest.TestCase):

    def tearDown(self):
        Node.clearregistry()
        Element.clearregistry()

    def test_01_len(self):
        test1 = Selection('test1', ['n1', 'n2'], [])
        self.assertEqual(len(test1), 2)
        test2 = Selection('test2', [], ['e1'])
        self.assertEqual(len(test2), 1)

    def test_02_iadd(self):
        test = Selection('sel',
                         ['n1', 'n2', 'n3'],
                         ['e1', 'e2', 'e3'])
        test += Selection('add', ['n3', 'n4'], [])
        reference = Selection('sel',
                              ['n1', 'n2', 'n3', 'n4'],
                              ['e1', 'e2', 'e3'])
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)
        test += Selection('add', [], ['e4', 'e5'])
        reference = Selection('sel',
                              ['n1', 'n2', 'n3', 'n4'],
                              ['e1', 'e2', 'e3', 'e4', 'e5'])
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)
    def test_03_isub(self):
        test = Selection('sel',
                         ['n1', 'n2', 'n3'],
                         ['e1', 'e2', 'e3'])
        test -= Selection('sub', ['n3', 'n4'], [])
        reference = Selection('sel',
                              ['n1', 'n2'],
                              ['e1', 'e2', 'e3'])
        test -= Selection('sub', [], ['e1', 'e2', 'e3'])
        reference = Selection('sel',
                              ['n1', 'n2'],
                              [])
        self.assertEqual(test.nodes, reference.nodes)
        self.assertEqual(test.elements, reference.elements)
