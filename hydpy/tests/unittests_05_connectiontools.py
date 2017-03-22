
# import...
# ...from standard library
from __future__ import division, print_function
import unittest
# ...from HydPy
from hydpy.core.devicetools import *
from hydpy.core.connectiontools import *

class Test01Connections(unittest.TestCase):

    def setUp(self):
        self.cons = Connections(None)
        setattr(self.cons, 'test1', 1)
        setattr(self.cons, 'test2', 2)

    def test_01_properties(self):
        self.assertListEqual(sorted(self.cons.names), ['test1', 'test2'])
        self.assertListEqual(sorted(self.cons.slaves), [1, 2])
    def test_02_contains(self):
        self.assertTrue('test1' in self.cons)
        self.assertTrue('test2' in self.cons)
        self.assertTrue(1 in self.cons)
        self.assertTrue(2 in self.cons)
    def test_03_iterable(self):
        names, cons = [], []
        for (name, con) in self.cons:
            names.append(name)
            cons.append(con)
        self.assertListEqual(sorted(names), ['test1', 'test2'])
        self.assertListEqual(sorted(cons), [1, 2])

class Test01Self2Node(unittest.TestCase):

    def tearDown(self):
        Element.clearregistry()

    def test_01_iadd(self):
        test = Connections(None)
        n1 = Node('n1', 'Q')
        test += n1
        self.assertIsInstance(test, Connections)
        self.assertIsInstance(test.n1, Node)
        self.assertIs(test.n1, n1)
        test += n1
        self.assertIsInstance(test, Connections)
        self.assertIsInstance(test.n1, Node)
        self.assertIs(test.n1, n1)
        n2 = Node('n2', 'T')
        test += n2
        self.assertIs(test.n1, n1)
        self.assertIs(test.n2, n2)

    def test_02_variables(self):
        test = Connections(None)
        self.assertListEqual(test.variables, [])
        n1 = Node('n1', 'Q')
        test += n1
        self.assertListEqual(test.variables, ['Q'])
        n2 = Node('n2', 'T')
        test += n2
        self.assertListEqual(sorted(test.variables), ['Q', 'T'])
        with self.assertRaises(AttributeError):
            test.X