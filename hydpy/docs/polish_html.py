"""Improve the headers and the in-text tables of content for all base and application
models."""

import importlib
import os

import click

from hydpy.core import modeltools
from hydpy.exe import xmltools


def _replace_toc(dirpath: str, name: str, docname: modeltools.DocName) -> None:
    html = os.path.join(dirpath, f"{docname.family}.html")
    with open(html, encoding="utf-8") as file_:
        text = file_.read()
    template = '"toctree-l1"><a class="reference internal" href="%s.html">%s</a><'
    old = template % (name, name)
    new = template % (name, f"{name} &raquo; {docname.complete}")
    text = text.replace(old, new)
    with open(html, "w", encoding="utf-8") as file_:
        file_.write(text)


def _replace_header(dirpath: str, name: str, docname: modeltools.DocName) -> None:
    html = os.path.join(dirpath, f"{name}.html")
    with open(html, encoding="utf-8") as file_:
        text = file_.read()
    template = '<h1>%s<a class="headerlink"'
    text = text.replace(template % name, template % docname.complete)
    with open(html, "w", encoding="utf-8") as file_:
        file_.write(text)


@click.command()
@click.option(
    "-d",
    "--dirpath",
    type=str,
    required=False,
    default="auto/build",
    help="Path of the directory containing the HTML files.",
)
def _polish_html(dirpath: str) -> None:
    for name in xmltools.XSDWriter.get_basemodelnames():
        module = importlib.import_module(f"hydpy.models.{name}.{name}_model")
        _replace_header(dirpath=dirpath, name=name, docname=module.Model.DOCNAME)
        _replace_toc(dirpath=dirpath, name=name, docname=module.Model.DOCNAME)

    for name in xmltools.XSDWriter.get_applicationmodelnames():
        module = importlib.import_module(f"hydpy.models.{name}")
        _replace_header(dirpath=dirpath, name=name, docname=module.Model.DOCNAME)
        _replace_toc(dirpath=dirpath, name=name, docname=module.Model.DOCNAME)


if __name__ == "__main__":
    _polish_html()  # pylint: disable=no-value-for-parameter
