"""Please execute `prepare_build.py` before starting the build process."""

import os

import Cython.Distutils
import numpy
import setuptools

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
    version="6.2.0",
    description="A framework for the development and application of hydrological "
    "models.",
    long_description=long_description,
    author="HydPy Developers",
    author_email="c.tyralla@bjoernsen.de",
    url="https://github.com/hydpy-dev/hydpy",
    license="LGPL-3.0",
    classifiers=[
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
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
    cmdclass={"build_ext": Cython.Distutils.build_ext},
    packages=(
        ["hydpy"] + [f"hydpy.{p}" for p in setuptools.find_namespace_packages("hydpy")]
    ),
    include_package_data=True,
    ext_modules=extension_modules,
    include_dirs=[numpy.get_include()],
    scripts=[os.path.join("hydpy", "exe", "hyd.py")],
    python_requires=">=3.11",
    install_requires=[
        "Cython==3.2.3",
        "Pillow==12.0.0",
        "black==25.12.0",
        "build==1.3.0",
        "certifi==2025.11.12",
        "cftime==1.6.5",
        "click==8.3.1",
        "colorama==0.4.6",
        "contourpy==1.3.3",
        "coverage==7.13.0",
        "cycler==0.12.1",
        "cython==3.2.3",
        "docutils==0.22.4",
        "elementpath==5.0.4",
        "fonttools==4.61.1",
        "inflect==7.5.0",
        "kiwisolver==1.4.9",
        "lastversion==3.6.3",
        "matplotlib==3.10.8",
        "more_itertools==10.8.0",
        "mypy==1.19.1",
        "mypy_extensions==1.1.0",
        "narwhals==2.14.0",
        "netCDF4==1.7.3",
        "netcdf4==1.7.3",
        "networkx==3.6.1",
        "nox==2025.11.12",
        "numpy==2.4.0",
        "packaging==25.0",
        "pandas==2.3.3",
        "pathspec==0.12.1",
        "platformdirs==4.5.1",
        "plotly==6.5.0",
        "pylint==4.0.4",
        "pynsist==2.8",
        "pyparsing==3.3.1",
        "pytokens==0.3.0",
        "pytz==2025.2",
        "scipy==1.16.3",
        "setuptools==80.9.0",
        "six==1.17.0",
        "sphinx==9.0.4",
        "sphinxcontrib-bibtex == 2.6.5",
        "sphinxcontrib-fulltoc == 1.2.0",
        "tenacity==9.1.2",
        "typeguard==4.4.4",
        "types-docutils == 0.22.3.20251115",
        "typing_extensions==4.15.0",
        "wheel==0.46.1",
        "wrapt==2.0.1",
        "xmlschema==4.2.0",
    ],
)
