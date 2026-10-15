"""Please execute `prepare_build.py` before starting the build process."""

import os

import Cython.Build
import numpy
import setuptools
from setuptools.command.build_ext import build_ext


class BuildExt(build_ext):
    """Translate all Cython files into C files and compile the C files in parallel.

    By default, we use as many processes (for translating) and threads (for compiling)
    as CPUs are available.  Use the `parallel` option of command `build_ext` to change
    this number.  We translate the Cython files only when actually building the
    extensions so that, for example, building a source distribution does not involve
    translating.
    """

    def initialize_options(self) -> None:
        """Use all available CPUs by default (the `parallel` option can still change
        this)."""
        super().initialize_options()
        self.parallel = os.cpu_count() or 1

    def run(self) -> None:
        """Translate all Cython files into C files and then compile the C files.

        Each extension object describes one extension module to be built, including its
        source files.  Initially, these are the Cython files.  Function `cythonize`
        translates them into C files but returns new extension objects referring to the
        C files instead of changing the existing ones.  However, setuptools has already
        prepared the existing extension objects (in method `finalize_options`) and
        needs these preparations when compiling.  So we keep the existing extension
        objects and replace only their Cython source files with the generated C files.
        """
        extensions: list[setuptools.Extension] = self.extensions
        name2sources = {
            extension.name: extension.sources
            for extension in Cython.Build.cythonize(
                extensions, nthreads=int(self.parallel)
            )
        }
        for extension in extensions:
            extension.sources = name2sources[extension.name]
        super().run()


with open("README.rst", "r", encoding="utf-8") as readmefile:
    long_description = readmefile.read()

extension_dir = os.path.join("hydpy", "cythons", "autogen")
extension_modules = [
    setuptools.Extension(
        name=f"hydpy.cythons.autogen.{name[:-4]}",
        sources=[os.path.join(extension_dir, name)],
        extra_compile_args=["-O2"],
    )
    for name in os.listdir(extension_dir)
    if name.endswith(".pyx")
]

setuptools.setup(
    name="HydPy",
    version="7.0dev0",
    description="A framework for the development and application of hydrological "
    "models.",
    long_description=long_description,
    author="HydPy Developers",
    author_email="c.tyralla@bjoernsen.de",
    url="https://github.com/hydpy-dev/hydpy",
    license_expression="LGPL-3.0-only",
    classifiers=[
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering",
    ],
    keywords="hydrology modelling water balance rainfall runoff",
    cmdclass={"build_ext": BuildExt},
    packages=(
        ["hydpy"] + [f"hydpy.{p}" for p in setuptools.find_namespace_packages("hydpy")]
    ),
    include_package_data=True,
    ext_modules=extension_modules,
    include_dirs=[numpy.get_include()],
    scripts=[os.path.join("hydpy", "exe", "hyd.py")],
    python_requires=">=3.11",
    install_requires=[
        "black",
        "click",
        "cython",
        "inflect",
        "matplotlib",
        "mypy",
        "netcdf4",
        "networkx",
        "numpy",
        "packaging",
        "pandas",
        "plotly",
        "scipy",
        "setuptools",
        "typing_extensions",
        "wrapt",
        "xmlschema",
    ],
)
