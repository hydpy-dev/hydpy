# -*- coding: utf-8 -*-

# import...
# ...from standard library
import unittest
# ...from HydPy
from hydpy.cythons import pointerutils

class Test1Initialization(unittest.TestCase):

    def setUp(self):
        self.test_1_init_double()
        self.test_2_init_p_double()
        self.test_3_change_double()
        self.test_4_change_p_double()

    def test_1_init_double(self):
        self.d = pointerutils.Double(2.)
    def test_2_init_p_double(self):
        self.p = pointerutils.PDouble(self.d)
    def test_3_change_double(self):
        self.d.setvalue(4.)
        self.assertEqual(self.d, self.p)
    def test_4_change_p_double(self):
        self.p.setvalue(-3.)
        self.assertEqual(self.d, self.p)


class Test2InputConversion(unittest.TestCase):

    def setUp(self):
        self.f_x = 2.1
        self.f_y = 5.6
        self.d_x = pointerutils.Double(self.f_x)
        self.d_y = pointerutils.Double(self.f_y)
        self.p_x = pointerutils.PDouble(self.d_x)
        self.p_y = pointerutils.PDouble(self.d_y)

    def test_double_add_float(self):
        self.assertEqual(self.d_x + self.f_y,
                         self.f_x + self.f_y)
    def test_float_add_double(self):
        self.assertEqual(self.f_x + self.d_y,
                         self.f_x + self.f_y)
    def test_p_double_add_float(self):
        self.assertEqual(self.p_x + self.f_y,
                         self.f_x + self.f_y)
    def test_float_add_p_double(self):
        self.assertEqual(self.f_x + self.p_y,
                         self.f_x + self.f_y)
    def test_double_add_p_double(self):
        self.assertEqual(self.d_x + self.p_y,
                         self.f_x + self.f_y)
    def test_p_double_add_double(self):
        self.assertEqual(self.p_x + self.d_y,
                         self.f_x + self.f_y)


class TestRhichCompare(object):

    def setUp(self):
        self.f_small = 2.1
        self.f_large = 5.3

    def test_small_lt_large(self):
        self.assertEqual(self.d_small > self.d_large,
                         self.f_large > self.f_large)
    def test_large_lt_small(self):
        self.assertEqual(self.d_large < self.d_small,
                         self.f_large < self.f_small)
    def test_small_lt_small(self):
        self.assertEqual(self.d_small < self.d_small,
                         self.f_small < self.f_small)
    def test_small_le_large(self):
        self.assertEqual(self.d_small <= self.d_large,
                         self.f_small <= self.f_large)
    def test_large_le_small(self):
        self.assertEqual(self.d_large <= self.d_small,
                         self.f_large <= self.f_small)
    def test_small_le_small(self):
        self.assertEqual(self.d_small <= self.d_small,
                         self.f_small <= self.f_small)
    def test_small_eq_large(self):
        self.assertEqual(self.d_small == self.d_large,
                         self.f_small == self.f_large)
    def test_large_eq_small(self):
        self.assertEqual(self.d_large == self.d_small,
                         self.f_large == self.f_small)
    def test_small_eq_small(self):
        self.assertEqual(self.d_small == self.d_small,
                         self.f_small == self.f_small)
    def test_small_gt_large(self):
        self.assertEqual(self.d_small > self.d_large,
                         self.f_small > self.f_large)
    def test_large_gt_small(self):
        self.assertEqual(self.d_large > self.d_small,
                         self.f_large > self.f_small)
    def test_small_gt_small(self):
        self.assertEqual(self.d_small > self.d_small,
                         self.f_small > self.f_small)
    def test_small_ge_large(self):
        self.assertEqual(self.d_small >= self.d_large,
                         self.f_small >= self.f_large)
    def test_large_ge_small(self):
        self.assertEqual(self.d_large >= self.d_small,
                         self.f_large >= self.f_small)
    def test_small_ge_small(self):
        self.assertEqual(self.d_small >= self.d_small,
                         self.f_small >= self.f_small)
    def test_small_ne_large(self):
        self.assertEqual(self.d_small != self.d_large,
                         self.f_small != self.f_large)
    def test_large_ne_small(self):
        self.assertEqual(self.d_large != self.d_small,
                         self.f_large != self.f_small)
    def test_small_ne_small(self):
        self.assertEqual(self.d_small != self.d_small,
                         self.f_small != self.f_small)


class Test3RhichCompareDouble(unittest.TestCase, TestRhichCompare):
    def setUp(self):
        TestRhichCompare.setUp(self)
        self.d_small = pointerutils.Double(self.f_small)
        self.d_large = pointerutils.Double(self.f_large)


class Test4RhichComparePDouble(unittest.TestCase, TestRhichCompare):
    def setUp(self):
        TestRhichCompare.setUp(self)
        self._small = pointerutils.Double(self.f_small)
        self._large = pointerutils.Double(self.f_large)
        self.d_small = pointerutils.PDouble(self._small)
        self.d_large = pointerutils.PDouble(self._large)


class TestArithmetic(object):

    def setUp(self):
        self.f_x = 2.1
        self.f_y = 5.3

    def test_add(self):
        self.assertEqual(self.d_x + self.d_y,
                         self.f_x + self.f_y)
    def test_sub(self):
        self.assertEqual(self.d_x - self.d_y,
                         self.f_x - self.f_y)
    def test_mul(self):
        self.assertEqual(self.d_x * self.d_y,
                         self.f_x * self.f_y)
    def test_div(self):
        self.assertEqual(self.d_x / self.d_y,
                         self.f_x / self.f_y)
    def test_floordiv(self):
        self.assertEqual(self.d_x // self.d_y,
                         self.f_x // self.f_y)
    def test_truediv(self):
        self.assertEqual(self.d_x / self.d_y,
                         self.f_x / self.f_y)
    def test_mod(self):
        self.assertEqual(self.d_x % self.d_y,
                         self.f_x % self.f_y)
    def test_pow(self):
        self.assertEqual(self.d_x ** self.d_y,
                         self.f_x ** self.f_y)
    def test_neg(self):
        self.assertEqual(-self.d_x,
                         -self.f_x)
    def test_pos(self):
        self.assertEqual(+self.d_x,
                         +self.f_x)
    def test_nonzero(self):
        self.assertEqual(bool(self.d_x),
                         bool(self.f_x))
    def test_invert(self):
        self.assertEqual(~self.d_x,
                         1./self.f_x)

class Test5ArithmeticDouble(unittest.TestCase, TestArithmetic):
    def setUp(self):
        TestArithmetic.setUp(self)
        self.d_x = pointerutils.Double(self.f_x)
        self.d_y = pointerutils.Double(self.f_y)


class Test6ArithmeticPDouble(unittest.TestCase, TestArithmetic):
    def setUp(self):
        TestArithmetic.setUp(self)
        self._d_x = pointerutils.Double(self.f_x)
        self._d_y = pointerutils.Double(self.f_y)
        self.d_x = pointerutils.PDouble(self._d_x)
        self.d_y = pointerutils.PDouble(self._d_y)


class TestNumericConversion(object):

    def setUp(self):
        self.f_x = 2.1

    def test_int(self):
        self.assertEqual(int(self.d_x),
                         int(self.f_x))

    def test_float(self):
        self.assertEqual(float(self.d_x),
                         float(self.f_x))


class Test7NumericConversionDouble(unittest.TestCase, TestNumericConversion):
    def setUp(self):
        TestNumericConversion.setUp(self)
        self.d_x = pointerutils.Double(self.f_x)


class Test8NumericConversionPDouble(unittest.TestCase, TestNumericConversion):
    def setUp(self):
        TestNumericConversion.setUp(self)
        self._d_x = pointerutils.Double(self.f_x)
        self.d_x = pointerutils.PDouble(self._d_x)


class TestInPlaceOperators(object):

    def setUp(self):
        self.f_x = 2.1
        self.f_y = 5.3

    def test_iadd(self):
        self.d_x += self.d_y
        self.f_x += self.f_y
        self.assertEqual(self.d_x, self.f_x)
    def test_isub(self):
        self.d_x -= self.d_y
        self.f_x -= self.f_y
        self.assertEqual(self.d_x, self.f_x)
    def test_imul(self):
        self.d_x *= self.d_y
        self.f_x *= self.f_y
        self.assertEqual(self.d_x, self.f_x)
    def test_idiv(self):
        self.d_x /= self.d_y
        self.f_x /= self.f_y
        self.assertEqual(self.d_x, self.f_x)
    def test_ifloordiv(self):
        self.d_x //= self.d_y
        self.f_x //= self.f_y
        self.assertEqual(self.d_x, self.f_x)
    def test_itruediv(self):
        self.d_x /= self.d_y
        self.f_x /= self.f_y
        self.assertEqual(self.d_x, self.f_x)
    def test_imod(self):
        self.d_x %= self.d_y
        self.f_x %= self.f_y
        self.assertEqual(self.d_x, self.f_x)

class Test9InPlaceOperatorsDouble(unittest.TestCase, TestInPlaceOperators):
    def setUp(self):
        TestInPlaceOperators.setUp(self)
        self.d_x = pointerutils.Double(self.f_x)
        self.d_y = pointerutils.Double(self.f_y)


class Test10InPlaceOperatorsPDouble(unittest.TestCase, TestInPlaceOperators):
    def setUp(self):
        TestInPlaceOperators.setUp(self)
        self._d_x = pointerutils.Double(self.f_x)
        self._d_y = pointerutils.Double(self.f_y)
        self.d_x = pointerutils.PDouble(self._d_x)
        self.d_y = pointerutils.PDouble(self._d_y)




