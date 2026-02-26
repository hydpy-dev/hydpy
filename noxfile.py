"""This module defines different "sessions"; each session tests certain aspects of
HydPy in a newly set up virtual environment using `Nox`.

To execute all sessions, install `Nox`, open a command-line prompt, navigate to the
directory containing this nox file and write "nox".  To run specific sessions, write,
for example:

nox -s doctest -s pylint

See the docstrings of the individual sessions for potential specific configuration
options.
"""

import contextlib
import itertools
import os
import shutil
from typing import Iterator

import nox


def _install_hydpy(session: nox.Session) -> None:
    wheels = [
        os.path.join("dist", fn) for fn in os.listdir("dist") if fn.endswith(".whl")
    ]
    if wheels:
        print("available wheels:")
        for wheel in wheels:
            print(f"\t{wheel}")
    else:
        raise FileNotFoundError("no wheel available")
    if len(wheels) == 1:
        wheel = wheels[0]
        print(f"installing wheel {wheel}")
        session.install(wheel)
    else:
        print("let pip determine the appropriate wheel")
        session.install("hydpy", "--find-links", "dist")


def _get_sitepackagepath(session: nox.Session) -> str:
    root = os.path.split(session.bin)[0]
    for dirpath, dirnames, _ in os.walk(root):
        if ("hydpy" in dirnames) and ("numpy" in dirnames):
            return os.path.abspath(dirpath)
    assert False


@contextlib.contextmanager
def _clean_environment(session: nox.Session) -> Iterator[dict[str, str]]:
    temp = {}
    for key in ("HTTP_PROXY", "HTTPS_PROXY"):
        if key in session.env:
            temp[key] = session.env.pop(key)
    yield session.env
    for key, value in temp.items():
        session.env[key] = value


@nox.session
def doctest(session: nox.Session) -> None:
    """Execute script `run_doctests.py` and measure code coverage.

    You can define arguments specific to the doctest session.  The `doctest` session
    passes them to the `run_doctests.py` script.  For example, to restrict testing to
    module `hland_96.py` in Cython mode and to perform the simulations in the
    multi-threading mode with four additional threads, write:

    nox -s doctest -- --file_doctests=hland_96.py --python-mode=false --threads 4

    Or shorter:

    nox -s doctest -- -f hland_96.py -p f -t 4

    The "doctest" session only measures code coverage when no session-specific
    arguments are given.  Otherwise, the mentioned restrictions would inevitably result
    in incomplete code coverage measurements.
    """

    multithreading = ("-t" in session.posargs) or ("--threads" in session.posargs)
    analyse_coverage = (len(session.posargs) - (2 * multithreading)) == 0

    _install_hydpy(session)
    if analyse_coverage:
        session.install("coverage")
    session.chdir(_get_sitepackagepath(session))
    session.run("python", "hydpy/docs/enable_autodoc.py")
    if analyse_coverage:
        shutil.copy("hydpy/tests/hydpydoctestcustomize.py", "hydpydoctestcustomize.py")
        shutil.copy(
            "hydpy/tests/hydpydoctestcustomize.pth", "hydpydoctestcustomize.pth"
        )
    with _clean_environment(session):
        session.run("python", "hydpy/tests/run_doctests.py", *session.posargs)
    if analyse_coverage:
        session.run("coverage", "combine")
        session.run("coverage", "report", "-m", "--skip-covered", "--fail-under=100")


@nox.session
def installer(session: nox.Session) -> None:
    """Execute the *HydPy* installer and test it via the `run_doctests` script
    function."""
    session.run("python", "call_installer.py")
    with _clean_environment(session):
        session.run("hyd.py", "run_doctests", external=True)


@nox.session
def black(session: nox.Session) -> None:
    """Use `black` to check the source formatting.."""
    session.install("black")
    session.run(
        "black", "hydpy", "--check", "--exclude=hydpy/data/|hydpy/tests/iotesting"
    )


@nox.session
def pylint(session: nox.Session) -> None:
    """Use `pylint` to evaluate the code style."""
    _install_hydpy(session)
    session.install("pylint", "coverage", "ghp_import", "sphinx")
    session.run("pylint", "hydpy")


@nox.session
def mypy(session: nox.Session) -> None:
    """Use "mypy" to check the correctness of all type hints and the source code's type
    safety.

    Our long-term goal is to meet the requirements of Mypy's strict mode.
    """
    _install_hydpy(session)
    session.install("mypy", "types-docutils")
    session.run("mypy", "hydpy")


@nox.session
def mypy_plugin(session: nox.Session) -> None:
    """Use "mypy_plugin" to check that the Mypy plugin helps to infer more precise
    types in some situations."""

    _install_hydpy(session)

    filename_script = "test_case_mypy_plugin.py"
    filename_expected = "expected_results_mypy_plugin.txt"
    filename_results = "test_results_mypy_plugin.txt"

    with session.chdir(session.create_tmp()):
        with open("mypy.ini", "w", encoding="UTF-8") as file_:
            file_.write(
                "[mypy]\n"
                "plugins = hydpy.mypy_plugin\n"
                "[hydpy.mypy_plugin]\n"
                "relevant_sources = hydpy\n"
            )
        dirpath = os.path.join(_get_sitepackagepath(session), "hydpy", "tests")
        shutil.copy(os.path.join(dirpath, f"{filename_script}t"), filename_script)
        with open(filename_results, "w", encoding="UTF-8") as file_:
            session.run("mypy", filename_script, stdout=file_, success_codes=[1])
        filepath_expected = os.path.join(dirpath, filename_expected)
        with (
            open(filepath_expected, encoding="UTF-8") as file_expected,
            open(filename_results, encoding="UTF-8") as file_results,
        ):
            for expected, result in itertools.zip_longest(
                file_expected, file_results, fillvalue=""
            ):
                if (e := expected.strip()) != (r := result.strip()):
                    session.error(f"`{e}` vs `{r}`")


@nox.session
def check_consistency(session: nox.Session) -> None:
    """Run the `check_consistency.py` script."""
    _install_hydpy(session)
    session.run("python", "hydpy/tests/check_consistency.py")


@nox.session
def sphinx(session: nox.Session) -> None:
    """Build the HTML documentation and report warnings as errors.

    The `sphinx` session is more about building than testing.  However, it also checks
    for completeness, substitutions' correctness, and things like that.  Hence, we
    leave it here until we find a strong reason for moving it somewhere else.

    This session passes session-specific arguments to `sphinx-build`.  For example,
    when building the official documentation on Travis-CI, we want to ensure that
    everything is correct, so we pass the `-W` flag to convert warnings into errors:

    nox -s sphinx -- -W
    """
    _install_hydpy(session)
    session.install(
        "docutils",
        "sphinx",
        "sphinxcontrib-fulltoc",
        "sphinxprettysearchresults",
        "sphinxcontrib.bibtex",
    )
    session.chdir(_get_sitepackagepath(session))
    with _clean_environment(session):
        session.run("python", "hydpy/tests/run_doctests.py", "--python-mode=false")
    session.run("python", "hydpy/docs/enable_autodoc.py")
    session.run("python", "hydpy/docs/prepare.py")
    session.run(
        "sphinx-build", "hydpy/docs/auto", "hydpy/docs/auto/build", *session.posargs
    )
    session.run(
        "python", "hydpy/docs/polish_html.py", "--dirpath=hydpy/docs/auto/build"
    )
    shutil.rmtree("hydpy/docs/auto/build/.doctrees")
