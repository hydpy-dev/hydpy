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
import os
import shutil
from typing import Iterator, Literal
from typing_extensions import assert_never

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
@nox.parametrize("numpy", ["1", "2"])
def doctest(session: nox.Session, numpy: Literal["1", "2"]) -> None:
    """Execute script `run_doctests.py` and measure code coverage.

    You can define arguments specific to the doctest session.  The `doctest` session
    passes them to the `run_doctests.py` script.  For example, to restrict testing to
    module `armatools.py` in Cython mode, write:

    nox -s doctest -- --file_doctests=armatools.py --python-mode=false

    Or shorter:

    nox -s doctest -- -f armatools.py -p f

    The `doctest` session only measures code coverage when no session-specific
    arguments are given, due to the mentioned restrictions inevitably resulting in
    incomplete code coverage measurements.

    By default, the `doctest` session runs subsequentially with the NumPy versions 1.x
    and 2.x.  Use the following command to select only one version:

    nox -s "doctest(numpy='2')"
    """
    _install_hydpy(session)
    session.install("coverage")
    session.chdir(_get_sitepackagepath(session))
    session.run("python", "hydpy/docs/enable_autodoc.py")
    if not session.posargs:
        shutil.copy("hydpy/tests/hydpydoctestcustomize.py", "hydpydoctestcustomize.py")
        shutil.copy(
            "hydpy/tests/hydpydoctestcustomize.pth", "hydpydoctestcustomize.pth"
        )
    if numpy == "1":
        session.run("pip", "install", "numpy<2")
    elif numpy == "2":
        session.run("pip", "install", "numpy>1,<3")
    else:
        assert_never(numpy)
    with _clean_environment(session):
        session.run("python", "hydpy/tests/run_doctests.py", *session.posargs)
    if not session.posargs:
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

    We currently generally apply Mypy in the non-strict mode and handle the `models`
    subpackage even less strictly.  However, our long term-goal is to meet the
    requirements of the strict mode, which requires much additional effort regarding
    the typing of numpy arrays, model parameters and so on.
    """
    _install_hydpy(session)
    session.run("pip", "install", "numpy<2.2")
    session.install("mypy", "types-docutils")
    session.run("mypy", "hydpy")


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
