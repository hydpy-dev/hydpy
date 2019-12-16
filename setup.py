

# import...
# ...from standard library:
from __future__ import division, print_function
import os
import shutil
import sys
# ...from site-packages:
import Cython.Build
import Cython.Distutils
import numpy

install = 'install' in sys.argv
bdist_wheel = 'bdist_wheel' in sys.argv
bdist_wininst = 'bdist_wininst' in sys.argv
bdist_msi = 'bdist_msi' in sys.argv
bdist_egg = 'bdist_egg' in sys.argv
bdist = bdist_wheel or bdist_wininst or bdist_msi or bdist_egg
debug_cython = 'debug_cython' in sys.argv
if debug_cython:
    sys.argv.remove('debug_cython')
abspath = 'abspath' in sys.argv
if abspath:
    sys.argv.remove('abspath')

if install:
    from distutils.core import setup
    from distutils.extension import Extension
else:
    from setuptools import setup, Extension


def print_(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()


def prep(*folders):
    return os.path.abspath(os.path.join(*folders))


def source2target(source, target, do_copy=True):
    print_(f'  {source}\n    --> {target}')
    if do_copy:
        shutil.copy(source, target)


# Determine the correct type string for integer values in Cython
# compatible with numpy on the respective machine.
int_ = 'numpy.'+str(numpy.array([1]).dtype)+'_t'

print_('\nCollect HydPy packages:')
# Select all framework packages.
packages = ['hydpy']
for name in os.listdir('hydpy'):
    if not (name.startswith('_') or
            os.path.isfile(os.path.join('hydpy', name))):
        packages.append('.'.join(('hydpy', name)))
packages.append('hydpy.conf')
packages.append('hydpy.cythons.autogen')
packages.append('hydpy.docs.figs')
packages.append('hydpy.docs.html_')
packages.append('hydpy.docs.rst')
packages.append('hydpy.docs.sphinx')
packages.append('hydpy.exe')
packages.append('hydpy.tests.iotesting')
# Additionally, select all base model packages.
for name in os.listdir(os.path.join('hydpy', 'models')):
    if not (name.startswith('_') or
            os.path.isfile(os.path.join('hydpy', 'models', name))):
        packages.append('.'.join(('hydpy', 'models', name)))
for package in packages:
    print_('\t' + package)
# Select all data folders.
for dir_, _, _ in os.walk(os.path.join('hydpy', 'data')):
    if not dir_.startswith('_'):
        packages.append('.'.join(dir_.split(os.path.sep)))

# Add package data.
package_data = {
    'hydpy.conf': ['*.npy', '*.xsd', '*.xsdt'],
    'hydpy.cythons': ['*.pyi'],
    'hydpy.docs.figs': ['*.png'],
    'hydpy.docs.rst': ['*.rst'],
    'hydpy.tests': ['.coveragerc']
}
for package in packages:
    if package.startswith('hydpy.data'):
        package_data[package] = ['*.*']

# Add existing compiled extensions for binary arguments and prepare
# compiling extensions otherwise.
ext_modules = []
if bdist:
    package_data['hydpy.cythons.autogen'] = ['*.pyx', '*.pxd', '*.pyd', '*.pyi']
else:
    package_data['hydpy.cythons.autogen'] = ['*.pyx', '*.pxd', '*.pyi']
    print_('\nCollect extension modules:`')
    # Select the required extension modules, except those directly related
    # to the hydrological models.
    ext_names = []
    for name in os.listdir(os.path.join('hydpy', 'cythons')):
        if name.split('.')[-1] == 'pyx':
            ext_names.append(name.split('.')[0])
    for ext_name in ext_names:
        print_(f'\t{ext_name}')

    print_('\nCopy (and eventually modify) extension modules:')
    # Copy the source code of these extension modules from package `cythons` to
    # subpackage `autogen`.  Modify the source code where necessary.
    for ext_name in ext_names:
        for suffix in ('pyx', 'pxd'):
            filename = f'{ext_name}.{suffix}'
            path_in = prep('hydpy', 'cythons', filename)
            path_out = prep('hydpy', 'cythons', 'autogen', filename)
            source2target(path_in, path_out, False)
            if debug_cython:
                cythonoptions = (
                    '# -*- coding: utf-8 -*-\n'
                    '# !python\n'
                    '# cython: boundscheck=True\n'
                    '# cython: wraparound=True\n'
                    '# cython: initializedcheck=True\n'
                    '# cython: linetrace=True\n'
                    '# distutils: define_macros=CYTHON_TRACE=1\n'
                    '# distutils: define_macros=CYTHON_TRACE_NOGIL=1\n'
                )
            else:
                cythonoptions = (
                    '# -*- coding: utf-8 -*-\n'
                    '# !python\n'
                    '# cython: boundscheck=False\n'
                    '# cython: wraparound=False\n'
                    '# cython: initializedcheck=False\n'
                )
            with open(path_in) as file_in:
                text = file_in.read()
                text = text.replace(' int ', ' '+int_+' ')
                text = text.replace(' int[', ' '+int_+'[')
            with open(path_out, 'w') as file_out:
                file_out.write(cythonoptions)
                file_out.write(text)

    print_('\nCopy extension module stub files:')
    for ext_name in ext_names:
        filename = f'{ext_name}.pyi'
        path_in = prep('hydpy', 'cythons', filename)
        path_out = prep('hydpy', 'cythons', 'autogen', filename)
        source2target(path_in, path_out)

    print_('\nPrepare extension modules:')
    for ext_name in ext_names:
        path = prep('hydpy', 'cythons', 'autogen', f'{ext_name}.pyx')
        name = f'hydpy.cythons.autogen.{ext_name}'
        source2target(path, name, False)
        ext_modules.append(Extension(name, [path], extra_compile_args=['-O2']))

print_()

# There seem to be different places where the `build_ext` module can be found:
try:
    build_ext = Cython.Build.build_ext
except AttributeError:
    build_ext = Cython.Distutils.build_ext

with open("README.rst", "r") as readmefile:
    long_description = readmefile.read()

# The usual setup definitions.
setup(name='HydPy',
      version='4.0a11',
      description='A framework for the development and application of '
                  'hydrological models.',
      long_description=long_description,
      author='HydPy Developers',
      author_email='c.tyralla@bjoernsen.de',
      url='https://github.com/hydpy-dev/hydpy',
      license='LGPL-3.0',
      classifiers=[
          'Intended Audience :: Education',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Science/Research',
          ('License :: OSI Approved :: '
           'GNU Lesser General Public License v3 (LGPLv3)'),
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Scientific/Engineering'
      ],
      keywords='hydrology modelling water balance rainfall runoff',
      packages=packages,
      cmdclass={'build_ext': build_ext},
      ext_modules=Cython.Build.cythonize(ext_modules),
      include_dirs=[numpy.get_include()],
      scripts=[os.path.join('hydpy', 'exe', 'hyd.py')],
      package_data=package_data,
      include_package_data=True,
      python_requires='>=3.6',
      install_requires=[
          'networkx',
          'numpy',
          'scipy',
          'typing_extensions',
          'wrapt',
      ],
      )

if install:
    # Priorise site-packages (on Debian-based Linux distributions as Ubuntu
    # also dist-packages) in the import order to make sure, the following
    # imports refer to the newly build hydpy package on the respective
    # computer.
    print_('\nUpdate `sys.path` for importing from site-packages:')
    paths = [path for path in sys.path if path.endswith('-packages')]
    for path in paths:
        path = os.path.abspath(path)
        print_('\tpath')
        sys.path.insert(0, path)

    # insert the path to the Python executable into the shebang line
    # of script `hyd.py`, if given:
    if abspath:
        print_("\nModify the shebang line of 'hyd.py:")
        scriptpath = sys.path[0]
        while not os.path.exists(os.path.join(scriptpath, 'Scripts')):
            scriptpath = os.path.split(scriptpath)[0]
        scriptpath = os.path.join(scriptpath, 'Scripts', 'hyd.py')
        with open(scriptpath) as scriptfile:
            lines = scriptfile.readlines()
        lines[0] = f'#!{sys.executable}\n'
        with open(scriptpath, 'w') as scriptfile:
            scriptfile.writelines(lines)

    # Move `sitecustomize.py` into the site-packages folder for
    # complete measuring code coverage of multiple processes.
    print_(f'\nCopy sitecustomize.py:\n')
    import hydpy
    path_in = prep('.', 'sitecustomize.py')
    path_out = prep(os.path.split(hydpy.__path__[0])[0], 'sitecustomize.py')
    source2target(path_in, path_out)

    # Assure that the actual `debug_cython` option also effects the
    # cythonization of the hydrological models.
    from hydpy import config
    config.FASTCYTHON = not debug_cython

    # Execute all tests.
    oldpath = os.path.abspath('.')
    path = os.path.abspath(hydpy.tests.__path__[0])
    print_(f'\nChange cwd for testing:\n\t{path}')
    os.chdir(path)
    exitcode = int(os.system(f'{sys.executable} test_everything.py'))
    if exitcode:
        print_(f'Use this HydPy version with caution on your system.  At '
               f'least one verification test failed.  You should see in the '
               f'information given above, whether essential features of '
               f'HydPy are broken or perhaps only some typing errors in '
               f'documentation were detected.  (exit code: {exitcode:d})\n')
        sys.exit(1)

    # Copy all extension files (pyx) and all compiled Cython files (pyd or so)
    # into the original `autogen` folder.
    # (Thought for developers only - if it fails, its not that a big deal...)
    print_('\nCopy extension files and dlls backwards:')
    path_autogen = os.path.join(oldpath, 'hydpy', 'cythons', 'autogen')
    for filename in os.listdir(hydpy.cythons.autogen.__path__[0]):
        ending = filename.split('.')[-1]
        if ending in ('pyd', 'so', 'pyx', 'pxd'):
            try:
                path_in = prep(hydpy.cythons.autogen.__path__[0], filename)
                path_out = prep(path_autogen, filename)
                source2target(path_in, path_out)
            except BaseException:
                print_('\t!!! failed !!!')

    # Copy the generated bokeh plots into the original docs subpackage
    # (on Travis-CI: for including them into the online-documentation).
    print_('\nCopy bokeh plots backwards:')
    path_html = os.path.join(oldpath, 'hydpy', 'docs', 'html_')
    import hydpy.docs.html_
    for filename in os.listdir(hydpy.docs.html_.__path__[0]):
        if filename.endswith('.html'):
            path_in = prep(hydpy.docs.html_.__path__[0], filename)
            path_out = prep(path_html, filename)
            source2target(path_in, path_out)

    # Copy the (possibly new) matplotlib plots into the original docs subpackage
    # (on Travis-CI: for including them into the online-documentation).
    print_('\nCopy matplotlib plots backwards:')
    path_figs = os.path.join(oldpath, 'hydpy', 'docs', 'figs')
    import hydpy.docs.figs
    for filename in os.listdir(hydpy.docs.figs.__path__[0]):
        if filename.endswith('.png'):
            path_in = prep(hydpy.docs.figs.__path__[0], filename)
            path_out = prep(path_figs, filename)
            source2target(path_in, path_out)

    # Copy the (possibly new) configuration files into the original subpackage.
    print_('\nCopy configuration data backwards:')
    path_conf = os.path.join(oldpath, 'hydpy', 'conf')
    for filename in os.listdir(hydpy.conf.__path__[0]):
        if not filename.startswith('_'):
            path_in = prep(hydpy.conf.__path__[0], filename)
            path_out = prep(path_conf, filename)
            source2target(path_in, path_out)

    print_('\nNo problems encountered during testing!\n')

    # Check for complete code coverage
    if os.environ.get('COVERAGE_PROCESS_START'):
        print_('\nCheck for complete code coverage:')
        os.system('coverage combine')
        if os.system('coverage report -m --skip-covered --fail-under=100'):
            print('\nTest coverage is incomplete!\n')
            sys.exit(1)
        print('\nTest coverage is complete!\n')
        sys.exit(0)
