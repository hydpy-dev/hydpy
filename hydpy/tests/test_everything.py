# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:57:25 2017

@author: tyralla
"""


from __future__ import division, print_function
import os
import sys
import importlib
import unittest
import doctest
import warnings
import matplotlib

exitcode = int(os.system('python test_pyplot_backend.py'))
standard_backend_missing = exitcode == 1
if standard_backend_missing:
    matplotlib.use('Agg')
    print('The standard backend of matplotlib does not seem to be available '
          'on the current system.  Possibly, because you are working on a web '
          'server.  Instead, the widely available backend `Agg` is selected.')


# Priorise site-packages (on Debian-based Linux distributions as Ubunte
# also dist-packages) in the import order to make sure, the following
# imports refer to the newly build hydpy package on the respective computer.
paths = [path for path in sys.path if path.endswith('-packages')]
for path in paths:
    sys.path.insert(0, path)

# Import all hydrological models to trigger the automatic cythonization
# mechanism of HydPy.
from hydpy import pub
pub.options.skipdoctests = True
import hydpy.models
for name in [fn.split('.')[0] for fn in os.listdir(hydpy.models.__path__[0])]:
    if name != '__init__':
        importlib.import_module('hydpy.models.'+name)
pub.options.skipdoctests = False

# 1. Perform all "classical" unit tests.

import hydpy.tests
filenames = os.listdir(hydpy.tests.__path__[0])
unittests = {fn.split('.')[0]: None for fn in filenames if
             (fn.startswith('unittest') and fn.endswith('.py'))}
for name in unittests.keys():
    module = importlib.import_module('hydpy.tests.'+name)
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    suite = unittest.TestLoader().loadTestsFromModule(module)
    unittests[name] = runner.run(suite)
    unittests[name].nmbproblems = (len(unittests[name].errors) +
                                   len(unittests[name].failures))

successfulunittests = {name: runner for name, runner in unittests.items()
                       if not runner.nmbproblems}
failedunittests = {name: runner for name, runner in unittests.items()
                   if runner.nmbproblems}

if successfulunittests:
    print()
    print('In the following modules, no unit test failed:')
    for name in sorted(successfulunittests.keys()):
        print('    %s (%d successes)'
              % (name, successfulunittests[name].testsRun))
if failedunittests:
    print()
    print('At least one unit test failed in each of the following modules:')
    for name in sorted(failedunittests.keys()):
        print('    %s (%d failures/errors)'
              % (name, failedunittests[name].nmbproblems))
    for name in sorted(failedunittests.keys()):
        print()
        print('Detailed information on module %s:' % name)
        for idx, problem in enumerate(failedunittests[name].errors +
                                      failedunittests[name].failures):
            print('    Problem no. %d:' % (idx+1))
            print('        %s' % problem[0])
            for line in problem[1].split('\n'):
                print('        %s' % line)

# 2. Perform all doctests (first in Python mode, then in Cython mode)

from hydpy import pub
pub.options.reprcomments = False
import hydpy
from hydpy.core import devicetools
from hydpy.core import parametertools
alldoctests = ({}, {})
allsuccessfuldoctests = ({}, {})
allfaileddoctests = ({}, {})
iterable = zip(('Python', 'Cython'), alldoctests,
               allsuccessfuldoctests, allfaileddoctests)
for (mode, doctests, successfuldoctests, faileddoctests) in iterable:
    pub.options.usecython = mode == 'Cython'
    for dirinfo in os.walk(hydpy.__path__[0]):
        if dirinfo[0].endswith('tests') or '__init__.py' not in dirinfo[2]:
            continue
        packagename = dirinfo[0].replace(os.sep, '.')+'.'
        packagename = packagename[packagename.find('hydpy.'):]
        level = packagename.count('.')-1
        modulenames = [packagename+fn.split('.')[0]
                       for fn in dirinfo[2] if fn.endswith('.py')]
        docfilenames = [os.path.join(dirinfo[0], fn)
                        for fn in dirinfo[2] if fn.endswith('.rst')]
        for name in (modulenames + docfilenames):
            if name.endswith('apidoc'):
                continue
            if not name.endswith('.rst'):
                module = importlib.import_module(name)
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
            suite = unittest.TestSuite()
            try:
                if name.endswith('.rst'):
                    suite.addTest(
                        doctest.DocFileSuite(name, module_relative=False,
                                             optionflags=doctest.ELLIPSIS))
                else:
                    suite.addTest(
                        doctest.DocTestSuite(module,
                                             optionflags=doctest.ELLIPSIS))
            except ValueError as exc:
                if exc.args[-1] != 'has no docstrings':
                    raise(exc)
            else:
                pub.options.usedefaultvalues = False
                pub.options.printprogress = False
                pub.options.printincolor = False
                pub.options.warnsimulationstep = False
                pub.timegrids = None
                pub.options.reprcomments = False
                pub.options.reprdigits = 6
                pub.options.warntrim = False
                devicetools.Node.clearregistry()
                devicetools.Element.clearregistry()
                parametertools.Parameter._simulationstep = None
                if name.endswith('.rst'):
                    name = name[name.find('hydpy'+os.sep):]
                warnings.filterwarnings('error', module='hydpy')
                warnings.filterwarnings('ignore', category=ImportWarning)
                warnings.filterwarnings("ignore",
                                        message="numpy.dtype size changed")
                warnings.filterwarnings("ignore",
                                        message="numpy.ufunc size changed")
                doctests[name] = runner.run(suite)
                warnings.resetwarnings()
                doctests[name].nmbproblems = (len(doctests[name].errors) +
                                              len(doctests[name].failures))
    successfuldoctests.update({name: runner for (name, runner)
                              in doctests.items() if not runner.nmbproblems})
    faileddoctests.update({name: runner for (name, runner)
                          in doctests.items() if runner.nmbproblems})

    if successfuldoctests:
        print()
        print('In the following modules, no doc test failed in %s mode:'
              % mode)
        for name in sorted(successfuldoctests.keys()):
            if name.endswith('.rst'):
                print('    %s' % name)
            else:
                print('    %s (%d successes)'
                      % (name, successfuldoctests[name].testsRun))
    if faileddoctests:
        print()
        print('At least one doc test failed in each of the following modules '
              'in %s mode:' % mode)
        for name in sorted(faileddoctests.keys()):
            print('    %s (%d failures/errors)'
                  % (name, faileddoctests[name].nmbproblems))
        for name in sorted(faileddoctests.keys()):
            print()
            print('Detailed information on module %s:' % name)
            for idx, problem in enumerate(faileddoctests[name].errors +
                                          faileddoctests[name].failures):
                print('    Error no. %d:' % (idx+1))
                print('        %s' % problem[0])
                for line in problem[1].split('\n'):
                    print('        %s' % line)

# 3. Perform integration tests.


# 4. Return the exit code.
print('test_everything.py resulted in %d failing unit test suites, '
      '%d failing doctest suites in Python mode and %d failing '
      'doctest suites in Cython mode.' % (len(failedunittests),
                                          len(allfaileddoctests[0]),
                                          len(allfaileddoctests[1])))
if failedunittests or allfaileddoctests[0] or allfaileddoctests[1]:
    sys.exit(1)
else:
    sys.exit(0)
