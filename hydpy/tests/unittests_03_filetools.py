# -*- coding: utf-8 -*-

# import...
# ...from standard library
#from __future__ import division, print_function
#import os
#import unittest
## ...from HydPy
#from hydpy.core import filetools
#from hydpy import pub
#
#PROJECTNAME = 'projectnamemock'
#
#class NetworkFileMock(filetools.NetworkFile):
#    def checkpath(self):
#        pass
#
#class Test02NetwortFile(unittest.TestCase):
#
#    def setUp(self):
#        pub.projectname = PROJECTNAME
#        self.testdirectory = os.path.abspath('controlfiles')
#
#    def test_01_getdirectory(self):
#        networkfile = NetworkFileMock()
#        self.assertEqual(networkfile.directory, self.testdirectory)
#
#    def test_02_getfilename(self):
#        networkfile = NetworkFileMock()
#        self.assertEqual(networkfile.filename, PROJECTNAME+'_network.py')
#        networkfile._filename = 'testname'
#        self.assertEqual(networkfile.filename, 'testname.py')
#
#    def test_03_setwrongfilename(self):
#        with self.assertRaises(IOError):
#             filetools.NetworkFile('testname')
#
#    def test_04_setcorrectfilename(self):
#        networkfile = NetworkFileMock('testname')
#        self.assertEqual(networkfile.filename, 'testname.py')
#        networkfile = NetworkFileMock('testname.py')
#        self.assertEqual(networkfile.filename, 'testname.py')
#        networkfile.filename = None
#        self.assertEqual(networkfile.filename, PROJECTNAME+'_network.py')
#        networkfile = NetworkFileMock()
#        networkfile.filename = 'testname'
#        self.assertEqual(networkfile.filename, 'testname.py')
#
#    def test_5_savefile(self):
#        pass
