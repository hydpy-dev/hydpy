
# import...
# ...from standard library
from __future__ import division, print_function
import unittest
import sys
# ...from site packages
import numpy
# ...from HydPy
sys.path.insert(0, '..\\..\\..\\..\\HydPy')
from hydpy.core import sequences
from hydpy.cythons import pointer


class Test1Calcs(unittest.TestCase):

    def setUp(self):
        self.test_01_init()
        self.test_02_set_vector()
        self.test_03_set_scalar()
        self.test_04_get_pointer()

    def test_01_init(self):
        self.calcs = sequences.Calcs()
        self.assertIsInstance(self.calcs, sequences.Calcs)
    def test_02_set_vector(self):
        self.calcs.xs = numpy.zeros(5)
        self.calcs.ys = numpy.zeros(5)
        self.assertIsInstance(self.calcs.xs, numpy.ndarray)
    def test_03_set_scalar(self):
        self.calcs.x = pointer.Double(0.)
        self.calcs.y = pointer.Double(0.)
        self.assertIsInstance(self.calcs.x, pointer.Double)
    def test_04_get_pointer(self):
        self.p_x = self.calcs.name2pointer('x')
        self.p_y = self.calcs.name2pointer('y')
        self.assertIsInstance(self.p_x, pointer.P_Double)
    def test_5a_assign_float_to_scalar(self):
        self.calcs.x = 1.
        self.assertIsInstance(self.calcs.x, pointer.Double)
    def test_05b_assign_float_to_scalar(self):
        id_x = id(self.calcs.x)
        self.calcs.x = 3.
        self.assertEqual(id(self.calcs.x), id_x)
    def test_05c_assign_float_to_scalar(self):
        self.calcs.x = 9.
        self.assertEqual(self.calcs.x, 9.)
    def test_05d_assign_float_to_scalar(self):
        self.calcs.x = 2.
        self.assertEqual(self.calcs.x, self.p_x)
    def test_06a_assign_float64_to_scalar(self):
        self.calcs.x = numpy.float64(1.)
        self.assertIsInstance(self.calcs.x, pointer.Double)
    def test_06b_assign_float64_to_scalar(self):
        id_x = id(self.calcs.x)
        self.calcs.x = numpy.float64(3.)
        self.assertEqual(id(self.calcs.x), id_x)
    def test_06c_assign_float64_to_scalar(self):
        self.calcs.x = numpy.float64(2.)
        self.assertEqual(self.calcs.x, 2.)
    def test_06d_assign_float64_to_scalar(self):
        self.calcs.x = numpy.float64(2.)
        self.assertEqual(self.calcs.x, self.p_x)
    def test_07a_add_float_to_scalar(self):
        self.calcs.x += 1.
        self.assertIsInstance(self.calcs.x, pointer.Double)
    def test_07b_add_float_to_scalar(self):
        id_x = id(self.calcs.x)
        self.calcs.x += 3.
        self.assertEqual(id(self.calcs.x), id_x)
    def test_07c_add_float_to_scalar(self):
        x = self.calcs.x + 2.
        self.calcs.x += 2.
        self.assertEqual(self.calcs.x, x)
    def test_07d_add_float_to_scalar(self):
        self.calcs.x += 2.
        self.assertEqual(self.calcs.x, self.p_x)
    def test_08a_add_float64_to_scalar(self):
        self.calcs.x += numpy.float64(1.)
        self.assertIsInstance(self.calcs.x, pointer.Double)
    def test_08b_add_float64_to_scalar(self):
        id_x = id(self.calcs.x)
        self.calcs.x += numpy.float64(3.)
        self.assertEqual(id(self.calcs.x), id_x)
    def test_08c_add_float64_to_scalar(self):
        self.calcs.x += numpy.float64(2.)
        self.assertEqual(self.calcs.x, self.p_x)
    def test_08d_add_float64_to_scalar(self):
        x = self.calcs.x + numpy.float64(2.)
        self.calcs.x += numpy.float64(2.)
        self.assertEqual(self.calcs.x, x)
    def test_09a_sub_double_from_scalar(self):
        self.calcs.x -= pointer.Double(1.)
        self.assertIsInstance(self.calcs.x, pointer.Double)
    def test_09b_sub_double_from_scalar(self):
        id_x = id(self.calcs.x)
        self.calcs.x -= pointer.Double(3.)
        self.assertEqual(id(self.calcs.x), id_x)
    def test_09c_sub_double_from_scalar(self):
        self.calcs.x -= pointer.Double(2.)
        self.assertEqual(self.calcs.x, self.p_x)
    def test_09d_sub_double_from_scalar(self):
        x = self.calcs.x - pointer.Double(2.)
        self.calcs.x -= pointer.Double(2.)
        self.assertEqual(self.calcs.x, x)
    def test_09e_sub_double_from_scalar(self):
        x = pointer.Double(0.0000986423105815)
        self.calcs.x = 0.0000986423105815
        self.calcs.x -= x
        self.assertEqual(x, 0.0000986423105815)
    def test_10_assign_scalar_to_vector(self):
        self.calcs.xs[2] = self.calcs.x
        self.assertEqual(self.calcs.xs[2], self.p_x)
#    def test_10_sub_double_from_double(self):
#        se
