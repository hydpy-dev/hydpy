
# import...
# ...from standard library:
from __future__ import division, print_function
import os
import sys
import shutil
import importlib
from distutils.core import setup
from distutils.extension import Extension
# ...from site-packages:
import Cython.Build
import numpy

run_tests = 'run_tests' in sys.argv
if run_tests:
    sys.argv.remove('run_tests')



# Select the required extension modules, except those directly related
# to the hydrological models.
ext_sources = os.path.join('hydpy', 'cythons', 'pointer.pyx')
ext_modules = Extension('hydpy.cythons.pointer', [ext_sources])
# The usual setup definitions. Don't forget to update `packages`,
# whenever a new model is implemented as a package.
setup(name='HydPy',
      version='2.0.0',
      description='A framework for the development and application of '
                  'hydrological models.',
      author='Christoph Tyralla',
      author_email='Christoph.Tyralla@rub.de',
      license='GPL-3.0',
      classifiers=[
      'Intended Audience :: Education',
      'Intended Audience :: Science/Research',
      'Intended Audience :: Financial and Insurance Industry',
      'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      'Operating System :: POSIX :: Linux',
      'Operating System :: Microsoft :: Windows',
      'Operating System :: Microsoft :: Windows :: Windows 7',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: Implementation :: CPython',
      'Topic :: Scientific/Engineering'
      ],
      keywords='hydrology modelling water balance rainfall runoff',
      packages=['hydpy', 'hydpy.cythons', 'hydpy.core', 'hydpy.tests',
                'hydpy.models', 'hydpy.models.hland'],
      cmdclass={'build_ext': Cython.Build.build_ext},
      ext_modules=Cython.Build.cythonize(ext_modules),
      include_dirs=[numpy.get_include()])
# Priorise site-packages (on Debian-based Linux distributions as Ubunte
# also dist-packages) in the import order to make sure, the following
# imports refer to the newly build hydpy package on the respective computer.
paths = [path for path in sys.path if path.endswith('-packages')]
for path in paths:
    sys.path.insert(0, path)
# Make all extension definition files available, which are required for
# cythonizing hydrological models.
if 'build' in sys.argv:
    import hydpy.cythons
    for filename in ('pointer.pyx', 'pointer.pxd'):
        shutil.copy(os.path.join('hydpy', 'cythons', filename),
                    os.path.join(hydpy.cythons.__path__[0], filename))

if run_tests:
    # Run all tests, make the coverage report, and prepare it for sphinx.
    oldpath = os.path.abspath('.')
    import hydpy.tests
    os.chdir(os.sep.join(hydpy.tests.__file__.split(os.sep)[:-1]))
    os.system('coverage run --branch --source hydpy test_everything.py')
    os.system('coverage report -m')
    os.system('coverage xml')
    os.system('pycobertura show --format html '
              '--output coverage.html coverage.xml')
    shutil.move('coverage.html',
                os.path.join(oldpath, 'hydpy', 'sphinx', 'coverage.html'))
else:
    # Just import all hydrological models to trigger the automatic
    # cythonization mechanism of HydPy.
    from hydpy import pub
    pub.options.skipdoctests = True
    import hydpy.models
    for name in [fn.split('.')[0] for fn
                 in os.listdir(hydpy.models.__path__[0])]:
        if name != '__init__':
            importlib.import_module('hydpy.models.'+name)
