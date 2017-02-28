
# import...
# ...from standard library:
import os
from distutils.core import setup
from distutils.extension import Extension
# ...from site-packages:
import Cython.Build
import numpy

ext_sources = os.path.join('hydpy', 'cythons', 'pointer.pyx')
ext_modules = Extension('hydpy.cythons.pointer', [ext_sources])
setup(name='HydPy',
      version='2.0.0.dev1',
      description='A framework for the development and application of '
                  'hydrological models.',
      author='Christoph Tyralla',
      author_email='Christoph.Tyralla@rub.de',
      license='GPL-3.0',
      keywords='hydrology modelling water balance rainfall runoff',
      packages=['hydpy', 'hydpy.cythons', 'hydpy.framework', 'hydpy.unittests',
                'hydpy.models', 'hydpy.models.hland'],
      cmdclass={'build_ext': Cython.Build.build_ext},
      ext_modules=Cython.Build.cythonize(ext_modules),
      include_dirs=[numpy.get_include()])
