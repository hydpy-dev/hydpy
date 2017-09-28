
# import...
# ...from standard library:
from __future__ import division, print_function
import os
import sys
import shutil
from distutils.core import setup
from distutils.extension import Extension
# ...from site-packages:
import Cython.Build
import numpy

install = 'install' in sys.argv
coverage_report = 'coverage_report' in sys.argv
if coverage_report:
    sys.argv.remove('coverage_report')

# Select all framework packages.
packages = ['hydpy']
for name in os.listdir('hydpy'):
    if not (name.startswith('_') or
            os.path.isfile(os.path.join('hydpy', name))):
        packages.append('.'.join(('hydpy', name)))
# Additionally, select all base model packages.
for name in os.listdir(os.path.join('hydpy', 'models')):
    if not (name.startswith('_') or
            os.path.isfile(os.path.join('hydpy', 'models', name))):
        packages.append('.'.join(('hydpy', 'models', name)))
# Select the required extension modules, except those directly related
# to the hydrological models.
ext_names = []
for name in os.listdir(os.path.join('hydpy', 'cythons')):
    if name.split('.')[-1] == 'pxd':
        ext_names.append(name.split('.')[0])
ext_modules = []
for ext_name in ext_names:
    ext_sources = os.path.join('hydpy', 'cythons', '%s.pyx' % ext_name)
    ext_modules.append(Extension('hydpy.cythons.%s' % ext_name, [ext_sources]))
# The usual setup definitions.
setup(name='HydPy',
      version='2.0.0',
      description='A framework for the development and application of '
                  'hydrological models.',
      author='Christoph Tyralla',
      author_email='Christoph.Tyralla@rub.de',
      url='https://github.com/tyralla/hydpy',
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
      packages=packages,
      cmdclass={'build_ext': Cython.Build.build_ext},
      ext_modules=Cython.Build.cythonize(ext_modules),
      include_dirs=[numpy.get_include()],
      include_package_data=True,
      install_requires=['Cython', 'numpy', 'matplotlib'])

if install:
    # Priorise site-packages (on Debian-based Linux distributions as Ubuntu
    # also dist-packages) in the import order to make sure, the following
    # imports refer to the newly build hydpy package on the respective
    # computer.
    paths = [path for path in sys.path if path.endswith('-packages')]
    for path in paths:
        sys.path.insert(0, path)
    # Make all extension definition files available, which are required for
    # cythonizing hydrological models.
    import hydpy.cythons
    for ext_name in ext_names:
        for suffix in ('pyx', 'pxd'):
            filename = '%s.%s' % (ext_name, suffix)
            shutil.copy(os.path.join('hydpy', 'cythons', filename),
                        os.path.join(hydpy.cythons.__path__[0], filename))
    # Make all restructured text documentation files available for doctesting.
    import hydpy.docs
    for filename in os.listdir(os.path.join('hydpy', 'docs')):
        if filename.endswith('.rst') or filename.endswith('.png'):
            shutil.copy(os.path.join('hydpy', 'docs', filename),
                        os.path.join(hydpy.docs.__path__[0], filename))
    # Make all kinds of configuration data available.
    import hydpy.conf
    for filename in os.listdir(os.path.join('hydpy', 'conf')):
        if ((not (filename.endswith('.py') or filename.endswith('.pyc'))) and
                os.path.isfile(os.path.join('hydpy', 'models', filename))):
            shutil.copy(os.path.join('hydpy', 'conf', filename),
                        os.path.join(hydpy.conf.__path__[0], filename))
    # Copy all compiled Cython files (pyd) into the original folder.
    # (Thought for developers only - if it fails, its not that a big deal...)
    for filename in os.listdir(hydpy.cythons.__path__[0]):
        if filename.endswith('.pyd'):
            try:
                shutil.copy(os.path.join(hydpy.cythons.__path__[0], filename),
                            os.path.join('hydpy', 'cythons', filename))
            except BaseException:
                pass
    # Execute all tests.
    oldpath = os.path.abspath('.')
    import hydpy.tests
    os.chdir(os.sep.join(hydpy.tests.__file__.split(os.sep)[:-1]))
    exitcode = int(os.system('coverage run -m --branch '
                             '--source hydpy --omit=test_everything.py '
                             'test_everything'))
    if exitcode:
        print('Use this HydPy version with caution on your system.  At '
              'least one verification test failed.  You should see in the '
              'information given above, whether essential features of '
              'HydPy are broken or perhaps only some typing errors in '
              'documentation were detected.  (exit code: %d)' % exitcode)
        sys.exit(1)
    # Prepare coverage report and prepare it for sphinx.
    if coverage_report:
        os.system('coverage report -m --skip-covered')
        os.system('coverage xml')
        os.system('pycobertura show --format html '
                  '--output coverage.html coverage.xml')
        shutil.move('coverage.html',
                    os.path.join(oldpath, 'hydpy', 'docs', 'coverage.html'))
