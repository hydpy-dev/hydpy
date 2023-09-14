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
    version="5.0.3",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
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
    python_requires=">=3.8",
    install_requires=[
        "black",
        "click",
        "matplotlib",
        "netcdf4",
        "networkx",
        "numpy",
        "pandas",
        "plotly",
        "scipy",
        "setuptools",
        "typing_extensions",
        "wrapt",
        "xmlschema",
    ],
)
