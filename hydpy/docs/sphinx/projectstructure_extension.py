"""Sphinx extension introducing `.. project_structure:: (e.g.) HydPy-H-Lahn`
directives."""

# import...
# from standard library
import os
from typing import Any

# ...from site-packages
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.directives.code import CodeBlock
from sphinx.writers.html5 import HTML5Translator

# ...from HydPy
from hydpy import data
from hydpy.core import autodoctools


class ProjectStructureNode(nodes.General, nodes.FixedTextElement):
    """The docutils node for the project structure directive."""

    projectname: str


class ProjectStructureBlock(CodeBlock):
    """A sphinx directive specialised for project structure code blocks."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0

    def run(self) -> list[Any]:  # ToDo: should we subclass from Node?
        """Prepare a `ProjectStructureNode` object."""
        content = "\n".join(self.content)
        node = ProjectStructureNode(content, content)
        node.line = self.lineno
        node.projectname = self.arguments[0]
        return [node]


def visit_html(self: HTML5Translator, node: ProjectStructureNode) -> None:
    """Generate and insert the HTML code of the selected example project."""

    projectpath = os.path.join(data.__path__[0], node.projectname)
    projectstructure = autodoctools.ProjectStructure(projectpath=projectpath)
    self.body[-1] = projectstructure.html

    raise nodes.SkipNode


def setup(app: Sphinx) -> None:
    """Add the project structure extension to Sphinx."""

    app.add_directive("project_structure", ProjectStructureBlock)
    app.add_node(ProjectStructureNode, html=(visit_html, None))
