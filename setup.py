
# import...
# ...from standard library:
import os
import sys
import shutil
import importlib
from distutils.core import setup
from distutils.extension import Extension
# ...from site-packages:
import Cython.Build
import numpy

# Select the required extension modules, except those directly related
# to the hydrological models.
ext_sources = os.path.join('hydpy', 'cythons', 'pointer.pyx')
ext_modules = Extension('hydpy.cythons.pointer', [ext_sources])
# The usual setup definitions. Don't forget to update `packages`,
# whenever a new model is implemented as a package.
setup(name='HydPy',
      version='2.0.0.dev1',
      description='A framework for the development and application of '
                  'hydrological models.',
      author='Christoph Tyralla',
      author_email='Christoph.Tyralla@rub.de',
      license='GPL-3.0',
      keywords='hydrology modelling water balance rainfall runoff',
      packages=['hydpy', 'hydpy.cythons', 'hydpy.core', 'hydpy.unittests',
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
import hydpy.cythons
from hydpy.cythons import modelutils
for filename in ('pointer.pyx', 'pointer.pxd'):
    shutil.copy(os.path.join('hydpy', 'cythons', filename),
                os.path.join(hydpy.cythons.__path__[0], filename))
for filename in os.listdir(os.path.join(hydpy.cythons.__path__[0])):
    if (filename.startswith('pointer.') and
        filename.endswith(modelutils.dllextension)):
        shutil.copy(os.path.join(hydpy.cythons.__path__[0], filename),
                    os.path.join('hydpy', 'cythons', filename))
        break
# Import all hydrological models to trigger the automatic cythonization
# mechanism of HydPy.
from hydpy import pub
pub.options.skipdoctests = True
import hydpy.models
for name in [fn.split('.')[0] for fn in os.listdir(hydpy.models.__path__[0])]:
    if name != '__init__':
        importlib.import_module('hydpy.models.'+name)
