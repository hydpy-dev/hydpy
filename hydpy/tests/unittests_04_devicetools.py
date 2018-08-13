# -*- coding: utf-8 -*-

# import...
# ...from standard library
import unittest
# ...from HydPy
from hydpy.core.devicetools import *
from hydpy.core.connectiontools import *



class Test01NodeCreation(unittest.TestCase):

    def tearDown(self):
        Element.clear_registry()
        Node.clear_registry()

    def test_01_fromstring(self):
        test1a = Node('test1')
        self.assertIsInstance(test1a, Node)
        self.assertEqual(test1a.name, 'test1')
        test1b = Node('test1')
        self.assertIs(test1a, test1b)
        test2 = Node('test2')
        self.assertIsNot(test1a, test2)
    def test_02_fromnode(self):
        test1 = Node('test')
        test2 = Node(test1)
        self.assertIsInstance(test2, Node)
        self.assertIs(test1, test2)
        with self.assertRaises(ValueError):
            Node([test1, test2])
    def test_03_fromwronginput(self):
        with self.assertRaises(ValueError):
            test = Node(['test'])
        with self.assertRaises(ValueError):
            test = Node(5)
        with self.assertRaises(ValueError):
            test = Node({'test': 'test'})
    def test_04_attributes(self):
        test1 = Node('test1')
        self.assertIsInstance(test1.entries, Connections)
        self.assertIsInstance(test1.exits, Connections)
        self.assertEqual(test1.variable, 'Q')
        test2 = Node('test2', 'T')
        self.assertIsInstance(test2.entries, Connections)
        self.assertIsInstance(test2.exits, Connections)
        self.assertEqual(test2.variable, 'T')
    def test_03_wrongredefinition(self):
        test = Node('test')
        with self.assertRaises(ValueError):
            Node('test', 'T')


class Test02ElementCreation(unittest.TestCase):

    def tearDown(self):
        Element.clear_registry()
        Node.clear_registry()

    def test_01_fromstring(self):
        test1a = Element('test1')
        self.assertIsInstance(test1a, Element)
        self.assertEqual(test1a.name, 'test1')
        test1b = Element('test1')
        self.assertIs(test1a, test1b)
        test2 = Element('test2')
        self.assertIsNot(test1a, test2)
    def test_02_fromelement(self):
        test1 = Element('test')
        test2 = Element(test1)
        self.assertIsInstance(test2, Element)
        self.assertIs(test1, test2)
        with self.assertRaises(ValueError):
            Element([test1, test2])
    def test_03_fromwronginput(self):
        with self.assertRaises(ValueError):
            test = Element(['test'])
        with self.assertRaises(ValueError):
            test = Element(5)
        with self.assertRaises(ValueError):
            test = Element({'test': 'test'})
    def test_04_attributes(self):
        test = Element('test')
        self.assertIsInstance(test.inlets, Connections)
        self.assertIsInstance(test.outlets, Connections)
        self.assertIsInstance(test.receivers, Connections)
        self.assertIsInstance(test.senders, Connections)
        self.assertIsNone(test.model)


class Test03ElementInitialization(unittest.TestCase):

    def setUp(self):
        self.n1Q = Node('n1Q', 'Q')
        self.n2Q = Node('n2Q', 'Q')
        self.n3W = Node('n3W', 'W')
        self.n4T = Node('n4T', 'T')

    def tearDown(self):
        Element.clear_registry()
        Node.clear_registry()

    def test_01_inlet(self):
        e = Element('e', inlets=self.n1Q)
        self.assertIsInstance(e, Element)
        self.assertIs(e.inlets.n1Q, self.n1Q)
        self.assertIsInstance(self.n1Q.exits.e, Element)
        self.assertIs(self.n1Q.exits.e, e)
        self.assertIs(e.inlets.n1Q, self.n1Q)
        e = Element('e', inlets=self.n1Q)
        self.assertIs(e.inlets.n1Q, self.n1Q)
        e = Element('e', inlets=self.n4T)
        self.assertIs(e.inlets.n1Q, self.n1Q)
        self.assertIs(e.inlets.n4T, self.n4T)
        e = Element('e', inlets=self.n3W)
        self.assertIs(e.inlets.n3W, self.n3W)
        with self.assertRaises(ValueError):
            e = Element('e', outlets=self.n2Q)
            e = Element('e', inlets=self.n2Q)

    def test_02_outlet(self):
        e = Element('e', outlets=self.n1Q)
        self.assertIsInstance(e, Element)
        self.assertIs(e.outlets.n1Q, self.n1Q)
        self.assertIsInstance(self.n1Q.entries.e, Element)
        self.assertIs(self.n1Q.entries.e, e)
        e = Element('e', outlets=self.n1Q)
        self.assertIs(e.outlets.n1Q, self.n1Q)
        e = Element('e', outlets=self.n4T)
        self.assertIs(e.outlets.n1Q, self.n1Q)
        self.assertIs(e.outlets.n4T, self.n4T)
        e = Element('e', outlets=self.n3W)
        self.assertIs(e.outlets.n3W, self.n3W)
        with self.assertRaises(ValueError):
            e = Element('e', inlets=self.n2Q)
            e = Element('e', outlets=self.n2Q)

    def test_03_receiver(self):
        e = Element('e', receivers=self.n1Q)
        self.assertIsInstance(e, Element)
        self.assertIs(e.receivers.n1Q, self.n1Q)
        self.assertIsInstance(self.n1Q.exits.e, Element)
        self.assertIs(self.n1Q.exits.e, e)
        e = Element('e', receivers=self.n1Q)
        self.assertIs(e.receivers.n1Q, self.n1Q)
        e = Element('e', receivers=self.n4T)
        self.assertIs(e.receivers.n1Q, self.n1Q)
        self.assertIs(e.receivers.n4T, self.n4T)
        e = Element('e', receivers=self.n3W)
        self.assertIs(e.receivers.n3W, self.n3W)
        with self.assertRaises(ValueError):
            e = Element('e', senders=self.n2Q)
            e = Element('e', receivers=self.n2Q)

    def test_04_sender(self):
        e = Element('e', senders=self.n1Q)
        self.assertIsInstance(e, Element)
        self.assertIs(e.senders.n1Q, self.n1Q)
        self.assertIsInstance(self.n1Q.entries.e, Element)
        self.assertIs(self.n1Q.entries.e, e)
        e = Element('e', senders=self.n1Q)
        self.assertIs(e.senders.n1Q, self.n1Q)
        e = Element('e', senders=self.n4T)
        self.assertIs(e.senders.n1Q, self.n1Q)
        self.assertIs(e.senders.n4T, self.n4T)
        e = Element('e', senders=self.n3W)
        self.assertIs(e.senders.n3W, self.n3W)
        with self.assertRaises(ValueError):
            e = Element('e', receivers=self.n2Q)
            e = Element('e', senders=self.n2Q)

    def test_05_inletandoutlet(self):
        e1 = Element('e1', inlets=self.n1Q, outlets=self.n2Q)
        self.assertIs(e1.inlets.n1Q, self.n1Q)
        self.assertIs(e1.outlets.n2Q, self.n2Q)
        e2 = Element('e2', inlets=self.n1Q)
        with self.assertRaises(ValueError):
            Element('e2', outlets=self.n1Q)
        e3 = Element('e3', outlets=self.n1Q)
        with self.assertRaises(ValueError):
            Element('e3', inlets=self.n1Q)
        with self.assertRaises(ValueError):
            Element('e4', inlets=self.n1Q, outlets=self.n1Q)

    def test_06_receiverandsender(self):
        e1 = Element('e1', receivers=self.n1Q, senders=self.n2Q)
        self.assertIs(e1.receivers.n1Q, self.n1Q)
        self.assertIs(e1.senders.n2Q, self.n2Q)
        e2 = Element('e2', receivers=self.n1Q)
        with self.assertRaises(ValueError):
            Element('e2', senders=self.n1Q)
        e3 = Element('e3', senders=self.n1Q)
        with self.assertRaises(ValueError):
            Element('e3', receivers=self.n1Q)
        with self.assertRaises(ValueError):
            Element('e4', receivers=self.n1Q, senders=self.n1Q)


#class Test04NodesCreation(unittest.TestCase):
#
#    def setUp(self):
#        asdf

class Test05ElementsCreation(unittest.TestCase):

    def setUp(self):
        self.element1 = Element('element1')
        self.element2 = Element('element2')

    def tearDown(self):
        Element.clear_registry()
        Node.clear_registry()

    def test_00_fromnone(self):
        test = Elements(None)
        self.assertIsInstance(test, Elements)

    def test_01_fromelements(self):
        test = Elements(self.element1)
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        test = Elements(self.element1, self.element2)
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        self.assertIsInstance(test.element2, Element)
        self.assertIs(test.element2, self.element2)

    def test_02_fromstrings(self):
        test = Elements('element1')
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        test = Elements('element1', 'element2')
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        self.assertIsInstance(test.element2, Element)
        self.assertIs(test.element2, self.element2)

    def test_03_fromelements(self):
        test1 = Elements('element1')
        test2 = Elements(test1)
        self.assertIsInstance(test2, Elements)

    def test_04_fromemptycontainer(self):
        test = Elements([])
        self.assertIsInstance(test, Elements)

    def test_05_fromcontaineredelements1(self):
        test = Elements([self.element1])
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        test = Elements([self.element1, self.element2])
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIsInstance(test.element2, Element)
        self.assertIs(test.element1, self.element1)
        self.assertIs(test.element2, self.element2)

    def test_06_fromcontaineredelements1(self):
        test = Elements(Elements([self.element1]))
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        test = Elements(Elements([self.element1, self.element2]))
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIsInstance(test.element2, Element)
        self.assertIs(test.element1, self.element1)
        self.assertIs(test.element2, self.element2)

    def test_07_fromcontaineredstrings(self):
        test = Elements(['element1'])
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIs(test.element1, self.element1)
        test = Elements(['element1', 'element2'])
        self.assertIsInstance(test, Elements)
        self.assertIsInstance(test.element1, Element)
        self.assertIsInstance(test.element2, Element)
        self.assertIs(test.element1, self.element1)
        self.assertIs(test.element2, self.element2)

    def test_07_fromwrongtype(self):
        with self.assertRaises(TypeError):
            Elements(1.)

class Test06ElementsArithmetic(unittest.TestCase):

    def setUp(self):
        self.element1 = Element('element1')
        self.element2 = Element('element2')
        self.element3 = Element('element3')
        self.element4 = Element('element3')
        self.elements12 = Elements(self.element1, self.element2)
        self.elements34 = Elements(self.element3, self.element4)

    def tearDown(self):
        Element.clear_registry()
        Node.clear_registry()

    def test_01_iadd_element(self):
        self.elements12 += self.element3
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        self.assertIs(self.elements12.element3, self.element3)
    def test_02_iadd_elements(self):
        self.elements12 += self.elements34
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        self.assertIs(self.elements12.element3, self.element3)
    def test_03a_iadd_emptylist(self):
        elements12 = self.elements12.copy()
        self.elements12 += []
        self.assertIsInstance(self.elements12, Elements)
        self.assertEqual(self.elements12, elements12)
    def test_04a_iadd_elementlist(self):
        self.elements12 += [self.element3]
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        self.assertIs(self.elements12.element3, self.element3)
    def test_04b_iadd_elementlist(self):
        self.elements12 += [self.element3, self.element4]
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        self.assertIs(self.elements12.element3, self.element3)
    def test_05a_iadd_stringlist(self):
        self.elements12 += ['element3']
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        self.assertIs(self.elements12.element3, self.element3)
    def test_05b_iadd_stringlist(self):
        self.elements12 += ['element3', 'element4']
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        self.assertIs(self.elements12.element3, self.element3)

    def test_06_isub_element(self):
        self.elements12 -= self.element2
        self.assertIsInstance(self.elements12, Elements)
        self.assertIs(self.elements12.element1, self.element1)
        with self.assertRaises(AttributeError):
            self.elements12.element2

    def test_07_add_element(self):
        elements12 = self.elements12.copy()
        elements123 = self.elements12 + self.element3
        self.assertEqual(self.elements12, elements12)
        self.assertIsInstance(elements123, Elements)
        self.assertIs(elements123.element1, self.element1)
        self.assertIs(elements123.element3, self.element3)

    def test_08_sub_element(self):
        elements12 = self.elements12.copy()
        elements1 = self.elements12 - self.element2
        self.assertEqual(self.elements12, elements12)
        self.assertIsInstance(elements1, Elements)
        self.assertIs(elements1.element1, self.element1)
        with self.assertRaises(AttributeError):
            self.elements1.element2


class Test07ElementsComparisons(unittest.TestCase):

    def tearDown(self):
        Element.clear_registry()
        Node.clear_registry()

    def test_01_bool(self):
        self.assertFalse(Elements())
        self.assertTrue(Elements('a'))
        self.assertTrue(Elements('a', 'b'))