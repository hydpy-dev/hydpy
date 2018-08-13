# -*- coding: utf-8 -*-

# import...
# ...from standard library
import copy
import datetime
import unittest
# ...from HydPy
from hydpy.core import timetools

class Test01DateInitialization(unittest.TestCase):

    def setUp(self):
        self.refdate_day = datetime.datetime(1996, 11, 1)
        self.refdate_hour = datetime.datetime(1996, 11, 1, 12)
        self.refdate_minute = datetime.datetime(1996, 11, 1, 12, 30)
        self.refdate_second = datetime.datetime(1996, 11, 1, 12, 30, 5)

    def test_01_os_style_day(self):
        self.assertEqual(self.refdate_day,
                         timetools.Date('1996_11_01').datetime)
    def test_02_os_style_hour(self):
        self.assertEqual(self.refdate_hour,
                         timetools.Date('1996_11_01_12').datetime)
    def test_03_os_style_minute(self):
        self.assertEqual(self.refdate_minute,
                         timetools.Date('1996_11_01_12_30').datetime)
    def test_03_os_style_second(self):
        self.assertEqual(self.refdate_second,
                         timetools.Date('1996_11_01_12_30_05').datetime)

    def test_04_iso_style_day(self):
        self.assertEqual(self.refdate_day,
                         timetools.Date('1996.11.01').datetime)
    def test_05_iso_style_day(self):
        self.assertEqual(self.refdate_hour,
                         timetools.Date('1996.11.01 12').datetime)
    def test_06_iso_style_minute(self):
        self.assertEqual(self.refdate_minute,
                         timetools.Date('1996.11.01 12:30').datetime)
    def test_07_iso_style_second(self):
        self.assertEqual(self.refdate_second,
                         timetools.Date('1996.11.01 12:30:05').datetime)

    def test_08_din_style_day(self):
        self.assertEqual(self.refdate_day,
                         timetools.Date('01.11.1996').datetime)
    def test_09_din_style_day(self):
        self.assertEqual(self.refdate_hour,
                         timetools.Date('01.11.1996 12').datetime)
    def test_10_din_style_minute(self):
        self.assertEqual(self.refdate_minute,
                         timetools.Date('01.11.1996 12:30').datetime)
    def test_11_din_style_second(self):
        self.assertEqual(self.refdate_second,
                         timetools.Date('01.11.1996 12:30:05').datetime)

    def test_11_datetime_second(self):
        self.assertEqual(self.refdate_second,
                         timetools.Date(self.refdate_second).datetime)


class Test02DateProperties(unittest.TestCase):

    def setUp(self):
        self.refdate = datetime.datetime(1996, 11, 1, 12, 30, 5)
        self.testdate = timetools.Date(self.refdate)

    def tearDown(self):
        self.testdate.refmonth = 'November'

    def test_01_get_year(self):
        self.assertEqual(self.refdate.year, self.testdate.year)
    def test_02_get_month(self):
        self.assertEqual(self.refdate.month, self.testdate.month)
    def test_03_get_day(self):
        self.assertEqual(self.refdate.day, self.testdate.day)
    def test_04_get_hour(self):
        self.assertEqual(self.refdate.hour, self.testdate.hour)
    def test_05_get_minute(self):
        self.assertEqual(self.refdate.minute, self.testdate.minute)
    def test_06_get_second(self):
        self.assertEqual(self.refdate.second, self.testdate.second)

    def test_07_set_year(self):
        self.testdate.year = 2000
        refdate = datetime.datetime(2000, 11, 1, 12, 30, 5)
        self.assertEqual(refdate.year, self.testdate.datetime.year)
        with self.assertRaises(TypeError):
            self.testdate.year = 'wrong'
    def test_08_set_month(self):
        self.testdate.month = 5
        refdate = datetime.datetime(1996, 5, 1, 12, 30, 5)
        self.assertEqual(refdate.month, self.testdate.datetime.month)
        with self.assertRaises(TypeError):
            self.testdate.month = 'wrong'
    def test_09_set_day(self):
        self.testdate.day = 30
        refdate = datetime.datetime(1996, 11, 30, 12, 30, 5)
        self.assertEqual(refdate.day, self.testdate.datetime.day)
        with self.assertRaises(TypeError):
            self.testdate.day = 'wrong'
    def test_10_set_hour(self):
        self.testdate.hour = 0
        refdate = datetime.datetime(1996, 11, 1, 0, 30, 5)
        self.assertEqual(refdate.hour, self.testdate.datetime.hour)
        with self.assertRaises(TypeError):
            self.testdate.hour = 'wrong'
    def test_11_set_minute(self):
        self.testdate.minute = 59
        refdate = datetime.datetime(1996, 11, 1, 12, 59, 5)
        self.assertEqual(refdate.minute, self.testdate.datetime.minute)
        with self.assertRaises(TypeError):
            self.testdate.minute = 'wrong'
    def test_12_set_second(self):
        self.testdate.second = 7
        refdate = datetime.datetime(1996, 11, 1, 12, 30, 7)
        self.assertEqual(refdate.second, self.testdate.datetime.second)
        with self.assertRaises(TypeError):
            self.testdate.second = 'wrong'
    def test_13_get_wateryear(self):
        self.assertEqual(self.testdate.wateryear, self.testdate.year+1)
        self.testdate.month = 10
        self.assertEqual(self.testdate.wateryear, self.testdate.year)
    def test_14_set_refmonth(self):
        self.testdate.refmonth = 3
        self.assertEqual(self.testdate.refmonth, 3)
        self.testdate.refmonth = 'July'
        self.assertEqual(self.testdate.refmonth, 7)
        with self.assertRaises(ValueError):
            self.testdate.refmonth = 'Ju'



class Test03DateStyle(unittest.TestCase):

    def setUp(self):
        self.date = timetools.Date('01.11.1996')

    def test_01_remember_style(self):
        self.assertEqual(self.date.style, 'din1')
    def test_02_dontforget_style(self):
        self.date.to_string('iso2')
        self.assertEqual(self.date.style, 'din1')
    def test_03_change_style(self):
        self.date.style = 'iso2'
        self.assertEqual(self.date.style, 'iso2')


class Test05DateComparisons(unittest.TestCase):

    def setUp(self):
        self.early1 = timetools.Date('01.11.1996')
        self.early2 = timetools.Date('01.11.1996')
        self.late = timetools.Date('01.11.1997')

    def test_01_lt(self):
        self.assertTrue(self.early1 < self.late)
        self.assertFalse(self.early1 < self.early2)
        self.assertFalse(self.late < self.early2)
    def test_021_le(self):
        self.assertTrue(self.early1 <= self.late)
        self.assertTrue(self.early1 <= self.early2)
        self.assertFalse(self.late <= self.early2)
    def test_03_eq(self):
        self.assertFalse(self.early1 == self.late)
        self.assertTrue(self.early1 == self.early2)
        self.assertFalse(self.late == self.early2)
    def test_04_ne(self):
        self.assertTrue(self.early1 != self.late)
        self.assertFalse(self.early1 != self.early2)
        self.assertTrue(self.late != self.early2)
    def test_05_gt(self):
        self.assertFalse(self.early1 > self.late)
        self.assertFalse(self.early1 > self.early2)
        self.assertTrue(self.late > self.early2)
    def test_06_ge(self):
        self.assertFalse(self.early1 >= self.late)
        self.assertTrue(self.early1 >= self.early2)
        self.assertTrue(self.late >= self.early2)


class Test06DateArithmetic(unittest.TestCase):

    def setUp(self):
        self.earlydate = timetools.Date('01.11.1996')
        self.latedate = timetools.Date('01.11.1997')
        self.period = timetools.Period('365d')

    def test_01_add(self):
        testdate = self.earlydate + self.period
        self.assertEqual(self.latedate, testdate)
        self.assertEqual(testdate.style, 'din1')
    def test_02_iadd(self):
        self.earlydate += self.period
        self.assertEqual(self.earlydate, self.latedate)
        self.assertEqual(self.earlydate.style, 'din1')
    def test_03_sub(self):
        testdate = self.latedate - self.period
        self.assertEqual(self.earlydate, testdate)
        self.assertEqual(testdate.style, 'din1')
    def test_04_isub(self):
        self.latedate -= self.period
        self.assertEqual(self.latedate, self.earlydate)
        self.assertEqual(self.latedate.style, 'din1')


class Test07PeriodInitialization(unittest.TestCase):

    def test_01_string_day(self):
        self.assertEqual(datetime.timedelta(1),
                         timetools.Period('1d').timedelta)
        self.assertEqual(datetime.timedelta(365),
                         timetools.Period('365d').timedelta)
    def test_02_string_hour(self):
        self.assertEqual(datetime.timedelta(0, 60*60),
                         timetools.Period('1h').timedelta)
    def test_03_string_minute(self):
        self.assertEqual(datetime.timedelta(0, 60),
                         timetools.Period('1m').timedelta)
    def test_04_string_second(self):
        self.assertEqual(datetime.timedelta(0, 1),
                         timetools.Period('1s').timedelta)
    def test_05_timedelta(self):
        timedelta = datetime.timedelta(365)
        self.assertEqual(timedelta, timetools.Period(timedelta).timedelta)



class Test08PeriodProperties(unittest.TestCase):

    def setUp(self):
        seconds = int(60*60*24*365*3.2)
        self.refperiod = datetime.timedelta(0, seconds)
        self.testperiod = timetools.Period('%ds' % seconds)

    def test_01_get_days(self):
        self.assertEqual(self.refperiod.total_seconds()/60/60/24,
                         self.testperiod.days)
    def test_02_get_hours(self):
        self.assertEqual(self.refperiod.total_seconds()/60/60,
                         self.testperiod.hours)
    def test_03_get_minutes(self):
        self.assertEqual(self.refperiod.total_seconds()/60,
                         self.testperiod.minutes)
    def test_04_get_seconds(self):
        self.assertEqual(self.refperiod.total_seconds(),
                         self.testperiod.seconds)


class Test09PeriodUnit(unittest.TestCase):

    def test_01_day(self):
        self.assertEqual(timetools.Period('365d').unit, 'd')
        self.assertEqual(timetools.Period('1d').unit, 'd')
        self.assertEqual(timetools.Period('24h').unit, 'd')
        self.assertEqual(timetools.Period('1440m').unit, 'd')
        self.assertEqual(timetools.Period('86400m').unit, 'd')
    def test_02_hour(self):
        self.assertEqual(timetools.Period('25h').unit, 'h')
        self.assertEqual(timetools.Period('1h').unit, 'h')
        self.assertEqual(timetools.Period('60m').unit, 'h')
        self.assertEqual(timetools.Period('3600s').unit, 'h')
    def test_03_minute(self):
        self.assertEqual(timetools.Period('777m').unit, 'm')
        self.assertEqual(timetools.Period('1m').unit, 'm')
        self.assertEqual(timetools.Period('60s').unit, 'm')
    def test_04_second(self):
        self.assertEqual(timetools.Period('999s').unit, 's')
        self.assertEqual(timetools.Period('1s').unit, 's')


class Test11PeriodComparisons(unittest.TestCase):

    def setUp(self):
        self.short1 = timetools.Period('1h')
        self.short2 = timetools.Period('1h')
        self.long = timetools.Period('1d')

    def test_01_lt(self):
        self.assertTrue(self.short1 < self.long)
        self.assertFalse(self.short1 < self.short2)
        self.assertFalse(self.long < self.short2)
    def test_021_le(self):
        self.assertTrue(self.short1 <= self.long)
        self.assertTrue(self.short1 <= self.short2)
        self.assertFalse(self.long <= self.short2)
    def test_03_eq(self):
        self.assertFalse(self.short1 == self.long)
        self.assertTrue(self.short1 == self.short2)
        self.assertFalse(self.long == self.short2)
    def test_04_ne(self):
        self.assertTrue(self.short1 != self.long)
        self.assertFalse(self.short1 != self.short2)
        self.assertTrue(self.long != self.short2)
    def test_05_gt(self):
        self.assertFalse(self.short1 > self.long)
        self.assertFalse(self.short1 > self.short2)
        self.assertTrue(self.long > self.short2)
    def test_06_ge(self):
        self.assertFalse(self.short1 >= self.long)
        self.assertTrue(self.short1 >= self.short2)
        self.assertTrue(self.long >= self.short2)
#    def test_07_true(self):
#        self.assertTrue(self.short1)
#        self.assertTrue(self.long)
#        self.assertFalse(timetools.Period('0d'))


class Test12PeriodArithmetic(unittest.TestCase):

    def setUp(self):
        self.year97 = timetools.Date('01.11.1996')
        self.year98 = timetools.Date('01.11.1997')
        self.oneyear = timetools.Period('365d')
        self.oneday = timetools.Period('1d')

    def test_01_add(self):
        testdate = self.oneyear + self.year97
        self.assertEqual(self.year98, testdate)
        self.assertEqual(testdate.style, 'din1')
        self.assertEqual(self.oneyear + self.oneday, timetools.Period('366d'))
    def test_02_iadd(self):
        self.oneyear += self.oneday
        self.assertEqual(self.oneyear, timetools.Period('366d'))
    def test_03_sub(self):
        testdate = self.year98 - self.oneyear
        self.assertEqual(self.year97, testdate)
    def test_04_isub(self):
        self.oneyear -= self.oneday
        self.assertEqual(self.oneyear, timetools.Period('364d'))
    def test_05_mul(self):
        testperiod = self.oneday * 365
        self.assertEqual(testperiod, self.oneyear)
    def test_06_rmul(self):
        testperiod = 365 * self.oneday
        self.assertEqual(testperiod, self.oneyear)
    def test_07_imul(self):
        self.oneday *= 365
        self.assertEqual(self.oneday, self.oneyear)
    def test_08_div(self):
        testperiod = self.oneyear / self.oneday
        self.assertEqual(testperiod, 365)
        testinteger = self.oneyear / 365
        self.assertEqual(testinteger, self.oneday)
    def test_09_idiv(self):
        self.oneyear /= 365
        self.assertEqual(self.oneyear,  self.oneday)
    def test_10_mod(self):
        self.assertFalse(self.oneyear % self.oneday)
        self.assertTrue(self.oneyear % timetools.Period('360d'))
    def test_11_floordiv(self):
        self.assertTrue(self.oneyear // self.oneday)
        self.assertFalse(self.oneyear // timetools.Period('360d'))


class Test13TimegridInitialization(unittest.TestCase):

    def setUp(self):
        self.year97 = timetools.Date('01.11.1996')
        self.year98 = timetools.Date('01.11.1997')
        self.oneday = timetools.Period('1d')

    def test_01_right(self):
        timetools.Timegrid(self.year97, self.year98, self.oneday)
    def test_02_wrong(self):
        with self.assertRaises(ValueError):
            timetools.Timegrid(self.year97, self.year97, self.oneday)
        with self.assertRaises(ValueError):
            timetools.Timegrid(self.year98, self.year97, self.oneday)
        with self.assertRaises(ValueError):
            timetools.Timegrid(self.year97, self.year98,
                               timetools.Period('360d'))


class Test14TimegridIterable(unittest.TestCase):

    def setUp(self):
        self.year97 = timetools.Date('01.11.1996')
        self.year98 = timetools.Date('01.11.1997')
        self.oneday = timetools.Period('1d')
        self.timegrid = timetools.Timegrid(self.year97, self.year98,
                                           self.oneday)

    def test_01_indexing_with_integers(self):
        self.assertEqual(self.timegrid[0], self.year97)
        self.assertEqual(self.timegrid[365], self.year98)
        self.assertEqual(self.timegrid[1], self.year97+self.oneday)
        self.assertEqual(self.timegrid[-1], self.year97-self.oneday)
        self.assertEqual(self.timegrid[366], self.year98+self.oneday)
        self.assertEqual(self.timegrid[364], self.year98-self.oneday)

    def test_02_indexing_with_dates(self):
        self.assertEqual(self.timegrid[self.year97], 0)
        self.assertEqual(self.timegrid[self.year98], 365)
        self.assertEqual(self.timegrid[self.year97+self.oneday], 1)
        self.assertEqual(self.timegrid[self.year97-self.oneday], -1)
        self.assertEqual(self.timegrid[self.year98+self.oneday], 366)
        self.assertEqual(self.timegrid[self.year98-self.oneday], 364)

    def test_03_indexing_errors(self):
        with self.assertRaises(TypeError):
            self.timegrid[0.]
        with self.assertRaises(ValueError):
            self.timegrid[self.year97 + '1m']

    def test_04_iteration(self):
        self.assertEqual(list(self.timegrid)[1], self.year97+self.oneday)

    def test_05_len(self):
        self.assertEqual(len(self.timegrid), 365)


class Test15TimegridComparisons(unittest.TestCase):

    def setUp(self):
        self.year97 = timetools.Date('01.11.1996')
        self.year98 = timetools.Date('01.11.1997')
        self.oneday = timetools.Period('1d')
        self.onehour = timetools.Period('1h')
        self.timegrid = timetools.Timegrid(self.year97, self.year98,
                                           self.oneday)

    def test_01_eq(self):
        timegridtest = copy.deepcopy(self.timegrid)
        self.assertTrue(timegridtest == self.timegrid)
        timegridtest.firstdate.year = 1995
        self.assertFalse(timegridtest == self.timegrid)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.lastdate.year = 1998
        self.assertFalse(timegridtest == self.timegrid)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.stepsize = self.onehour
        self.assertFalse(timegridtest == self.timegrid)

    def test_02_ne(self):
        timegridtest = copy.deepcopy(self.timegrid)
        self.assertFalse(timegridtest != self.timegrid)
        timegridtest.firstdate.year = 1995
        self.assertTrue(timegridtest != self.timegrid)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.lastdate.year = 1998
        self.assertTrue(timegridtest != self.timegrid)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.stepsize = self.onehour
        self.assertTrue(timegridtest != self.timegrid)

    def test_03_date_in(self):
        self.assertTrue(self.year97 in self.timegrid)
        self.assertTrue(self.year98 in self.timegrid)
        self.assertTrue(self.year97+'1d' in self.timegrid)
        self.assertFalse(self.year97-'1d' in self.timegrid)
        self.assertTrue(self.year98-'1d' in self.timegrid)
        self.assertFalse(self.year98+'1d' in self.timegrid)
        self.assertFalse(self.year97+'12h' in self.timegrid)
        self.assertFalse(self.year97-'12h' in self.timegrid)
        self.assertFalse(self.year98-'12h' in self.timegrid)
        self.assertFalse(self.year98+'12h' in self.timegrid)

    def test_04_timegrid_in(self):
        timegridtest = copy.deepcopy(self.timegrid)
        self.assertTrue(timegridtest in self.timegrid)
        self.assertTrue(self.timegrid in timegridtest)
        timegridtest.firstdate -= '1d'
        self.assertFalse(timegridtest in self.timegrid)
        self.assertTrue(self.timegrid in timegridtest)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.lastdate += '1d'
        self.assertFalse(timegridtest in self.timegrid)
        self.assertTrue(self.timegrid in timegridtest)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.firstdate -= '1d'
        timegridtest.lastdate += '1d'
        self.assertFalse(timegridtest in self.timegrid)
        self.assertTrue(self.timegrid in timegridtest)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.firstdate += '12h'
        timegridtest.lastdate -= '12d'
        self.assertFalse(timegridtest in self.timegrid)
        self.assertFalse(self.timegrid in timegridtest)
        timegridtest = copy.deepcopy(self.timegrid)
        timegridtest.stepsize /= 24
        self.assertFalse(timegridtest in self.timegrid)
        self.assertFalse(self.timegrid in timegridtest)