
# import...
# ...from standard library
import os
import shutil
import sys
import distutils.core
import distutils.extension
import Cython.Build
# ...third party modules
import numpy


sys.argv = [sys.argv[0], 'build_ext', '--build-lib=cythons']
ext_modules = os.path.abspath(os.path.join('cythons', 'pointer.pyx'))
distutils.core.setup(ext_modules=Cython.Build.cythonize(ext_modules),
                     include_dirs=[numpy.get_include()])

shutil.move(os.path.abspath(os.path.join('cythons', 'hydpy', 'cythons', 'pointer.pyd')),
            os.path.abspath(os.path.join('cythons', 'pointer.pyd')))
##
##try:
##    os.remove(os.path.join('cythons', 'hydpy'))
##except OSError:
##    pass
##    
##try:
##    os.remove(os.path.join('build'))
##except OSError:
##    pass
