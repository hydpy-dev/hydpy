# import...
# ...from standard library
from __future__ import division, print_function
import unittest
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import indextools
from hydpy.core import timetools

class Test01MonthOfYear(unittest.TestCase):

    def setUp(self):
        self.indexer = indextools.Indexer()

    def tearDown(self):
        pub.timegrids = None

    def test_01_manual_mode(self):
        with self.assertRaises(BaseException):
            self.indexer.monthofyear = 'a'
        with self.assertRaises(BaseException):
            self.indexer.monthofyear = ['a', 'b']
        with self.assertRaises(ValueError):
            self.indexer.monthofyear = [[1, 2], [3, 4]]
        self.indexer.monthofyear = [1,2]
        self.assertIsInstance(self.indexer.monthofyear, numpy.ndarray)
        self.assertTupleEqual(tuple(self.indexer.monthofyear), (1, 2))
        del(self.indexer.monthofyear)
        self.assertIsNone(self.indexer._monthofyear)
        pub.timegrids = timetools.Timegrids(timetools.Timegrid('01.01.2004',
                                                               '1.01.2005',
                                                               '1d'))
        with self.assertRaises(ValueError):
            self.indexer.monthofyear = [1,2]

    def test_02_automatic_mode(self):
        with self.assertRaises(RuntimeError):
            self.indexer.monthofyear
        pub.timegrids = timetools.Timegrids(timetools.Timegrid('01.01.2004',
                                                               '1.01.2005',
                                                               '1d'))
        self.assertIsInstance(self.indexer.monthofyear, numpy.ndarray)
        self.assertEqual(len(self.indexer.monthofyear), 366)
        self.assertTupleEqual(tuple(self.indexer.monthofyear),
                              tuple(31*[0]+29*[1]+31*[2]+30*[3]+
                                    31*[4]+30*[5]+31*[6]+31*[7]+
                                    30*[8]+31*[9]+30*[10]+31*[11]))
        self.assertIs(self.indexer.monthofyear, self.indexer.monthofyear)


class Test02DayOfYear(unittest.TestCase):

    def setUp(self):
        self.indexer = indextools.Indexer()

    def tearDown(self):
        pub.timegrids = None

    def test_01_manual_mode(self):
        with self.assertRaises(BaseException):
            self.indexer.dayofyear = 'a'
        with self.assertRaises(BaseException):
            self.indexer.dayofyear = ['a', 'b']
        with self.assertRaises(ValueError):
            self.indexer.dayofyear = [[1, 2], [3, 4]]
        self.indexer.dayofyear = [1,2]
        self.assertIsInstance(self.indexer.dayofyear, numpy.ndarray)
        self.assertTupleEqual(tuple(self.indexer.dayofyear), (1, 2))
        del self.indexer.dayofyear
        self.assertIsNone(self.indexer._dayofyear)
        pub.timegrids = timetools.Timegrids(timetools.Timegrid('01.01.2004',
                                                               '1.01.2005',
                                                               '1d'))
        with self.assertRaises(ValueError):
            self.indexer.dayofyear = [1,2]

    def test_02_automatic_mode(self):
        with self.assertRaises(RuntimeError):
            self.indexer.dayofyear
        pub.timegrids = timetools.Timegrids(timetools.Timegrid('01.01.2004',
                                                               '1.01.2005',
                                                               '1d'))
        self.assertIsInstance(self.indexer.dayofyear, numpy.ndarray)
        self.assertEqual(len(self.indexer.dayofyear), 366)
        self.assertTupleEqual(tuple(self.indexer.dayofyear),
                              tuple(range(366)))
        pub.timegrids = timetools.Timegrids(timetools.Timegrid('01.01.2005',
                                                               '1.01.2006',
                                                               '1d'))
        del self.indexer.dayofyear
        self.assertIsInstance(self.indexer.dayofyear, numpy.ndarray)
        self.assertEqual(len(self.indexer.dayofyear), 365)
        self.assertTupleEqual(tuple(self.indexer.dayofyear),
                              tuple(range(31+28)+range(31+28+1, 366)))
        self.assertIs(self.indexer.dayofyear, self.indexer.dayofyear)