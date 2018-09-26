
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
import Cython.Distutils
import numpy


install = 'install' in sys.argv
coverage_report = 'coverage_report' in sys.argv
if coverage_report:
    sys.argv.remove('coverage_report')
debug_cython = 'debug_cython' in sys.argv
if debug_cython:
    sys.argv.remove('debug_cython')


def print_(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()


def prep(*folders):
    return os.path.abspath(os.path.join(*folders))


def source2target(source, target, do_copy=True):
    print_('  %s\n    --> %s' % (source, target))
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
packages.append('hydpy.cythons.autogen')
packages.append('hydpy.docs.figs')
packages.append('hydpy.docs.html')
packages.append('hydpy.docs.rst')
packages.append('hydpy.docs.sphinx')
packages.append('hydpy.tests.iotesting')
# Additionally, select all base model packages.
for name in os.listdir(os.path.join('hydpy', 'models')):
    if not (name.startswith('_') or
            os.path.isfile(os.path.join('hydpy', 'models', name))):
        packages.append('.'.join(('hydpy', 'models', name)))
for package in packages:
    print_('\t' + package)

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
ext_modules = []
for ext_name in ext_names:
    for suffix in ('pyx', 'pxd'):
        filename = '%s.%s' % (ext_name, suffix)
        path_in = prep('hydpy', 'cythons', filename)
        path_out = prep('hydpy', 'cythons', 'autogen', filename)
        source2target(path_in, path_out, False)
        text = open(path_in).read()
        text = text.replace(' int ', ' '+int_+' ')
        text = text.replace(' int[', ' '+int_+'[')
        if debug_cython:
            text = text.replace('nogil', '')
            text = text.replace('boundscheck=False',
                                'boundscheck=True')
            text = text.replace('wraparound=False',
                                'wraparound=True')
            text = text.replace('initializedcheck=False',
                                'initializedcheck=True')
        open(path_out, 'w').write(text)

print_('\nPrepare extension modules:`')
for ext_name in ext_names:
    path = prep('hydpy', 'cythons', 'autogen', '%s.pyx' % ext_name)
    name = 'hydpy.cythons.autogen.%s' % ext_name
    source2target(path, name, False)
    ext_modules.append(Extension(name, [path], extra_compile_args=['-O2']))
print_()

# There seem to be different places where the `build_ext` module can be found:
try:
    build_ext = Cython.Build.build_ext
except AttributeError:
    build_ext = Cython.Distutils.build_ext

# The usual setup definitions.
setup(name='HydPy',
      version='3.0-dev',
      description='A framework for the development and application of '
                  'hydrological models.',
      author='Christoph Tyralla',
      author_email='c.tyralla@bjoernsen.de',
      url='https://github.com/tyralla/hydpy',
      license='LGPL-3.0',
      classifiers=[
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          ('License :: OSI Approved :: '
           'GNU Lesser General Public License v3 (LGPLv3)'),
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: Microsoft :: Windows :: Windows 7',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Scientific/Engineering'
      ],
      keywords='hydrology modelling water balance rainfall runoff',
      packages=packages,
      cmdclass={'build_ext': build_ext},
      ext_modules=Cython.Build.cythonize(ext_modules),
      include_dirs=[numpy.get_include()],
      scripts=[os.path.join('hydpy', 'conf', 'hyd.py')],
      include_package_data=True)

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

    # Assure that the actual `debug_cython` option also effects the
    # cythonization of the hydrological models.
    import hydpy.pub
    hydpy.pub.options.fastcython = not debug_cython

    # Make all extension definition files available, which are required for
    # cythonizing hydrological models.
    print_('\nCopy extension modules:')
    import hydpy.cythons
    for ext_name in ext_names:
        for suffix in ('pyx', 'pxd'):
            filename = '%s.%s' % (ext_name, suffix)
            path_in = prep('hydpy', 'cythons', filename)
            path_out = prep(hydpy.cythons.autogen.__path__[0], filename)
            source2target(path_in, path_out, True)
            path_in = prep('hydpy', 'cythons', 'autogen', filename)
            path_out = prep(hydpy.cythons.autogen.__path__[0], filename)
            source2target(path_in, path_out, True)

    # Make all restructured text documentation files available.
    print_('\nCopy documentation files:')
    import hydpy.docs.rst
    for filename in os.listdir(os.path.join('hydpy', 'docs', 'rst')):
        if ((not (filename.endswith('.py') or filename.endswith('.pyc'))) and
                (not filename.startswith('_'))):
            path_in = prep('hydpy', 'docs', 'rst', filename)
            path_out = prep(hydpy.docs.rst.__path__[0], filename)
            source2target(path_in, path_out)

    # Make all additional data files available.
    print_('\nCopy data files:')
    import hydpy.data
    dir_input = os.path.join('hydpy', 'data')
    dir_output = hydpy.data.__path__[0]
    for subdir_input, dirs, files in os.walk(dir_input):
        subdir_output = subdir_input.replace(dir_input, dir_output, 1)
        if not os.path.exists(subdir_output):
            os.makedirs(subdir_output)
        for file_ in files:
            filepath_input = os.path.join(subdir_input, file_)
            filepath_output = os.path.join(subdir_output, file_)
            if os.path.exists(filepath_output):
                os.remove(filepath_output)
            shutil.copy(filepath_input, subdir_output)

    # Make all additional figures available.
    print_('\nCopy figures:')
    import hydpy.docs.figs
    for filename in os.listdir(os.path.join('hydpy', 'docs', 'figs')):
        if ((not (filename.endswith('.py') or filename.endswith('.pyc'))) and
                (not filename.startswith('_'))):
            path_in = prep('hydpy', 'docs', 'figs', filename)
            path_out = prep(hydpy.docs.figs.__path__[0], filename)
            source2target(path_in, path_out)

    # Make the ".coveragerc" file available.
    print_('\nCopy coverage configuration file:')
    import hydpy.tests
    path_in = prep('hydpy', 'tests', '.coveragerc')
    path_out = prep(hydpy.tests.__path__[0], '.coveragerc')
    source2target(path_in, path_out)

    # Make all kinds of configuration data available.
    print_('\nCopy configuration files:')
    import hydpy.conf
    for filename in os.listdir(os.path.join('hydpy', 'conf')):
        if ((not (filename.endswith('.py') or filename.endswith('.pyc'))) and
                os.path.isfile(os.path.join('hydpy', 'conf', filename))):
            path_in = prep('hydpy', 'conf', filename)
            path_out = prep(hydpy.conf.__path__[0], filename)
            source2target(path_in, path_out)

    # Execute all tests.
    oldpath = os.path.abspath('.')
    path = os.path.abspath(hydpy.tests.__path__[0])
    print_('\nChange cwd for testing:\n\t%s' % path)
    os.chdir(path)
    exitcode = int(os.system(
        'coverage run test_everything.py rcfile=.coveragerc '))
    if exitcode:
        print_('Use this HydPy version with caution on your system.  At '
               'least one verification test failed.  You should see in the '
               'information given above, whether essential features of '
               'HydPy are broken or perhaps only some typing errors in '
               'documentation were detected.  (exit code: %d)\n' % exitcode)
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
    path_html = os.path.join(oldpath, 'hydpy', 'docs', 'html')
    import hydpy.docs.html
    for filename in os.listdir(hydpy.docs.html.__path__[0]):
        if filename.endswith('.html'):
            path_in = prep(hydpy.docs.html.__path__[0], filename)
            path_out = prep(path_html, filename)
            source2target(path_in, path_out)

    # Prepare coverage report and prepare it for sphinx.
    if coverage_report:
        print_('\nPrepare coverage html file:')
        os.system('coverage report -m --skip-covered')
        os.system('coverage xml')
        os.system('pycobertura show --format html '
                  '--output coverage.html coverage.xml')
        print_('\nCopy coverage html file backwards:')
        path_in = prep(hydpy.tests.__path__[0], 'coverage.html')
        path_out = prep(oldpath, 'hydpy', 'docs', 'html', 'coverage.html')
        source2target(path_in, path_out)

    print('\nNo problems encountered during testing!\n')
