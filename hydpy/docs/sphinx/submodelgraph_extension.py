"""Sphinx extension introducing `.. submodel_graph:: (e.g.) hland_96` directives."""

# import...
# ...from site-packages
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.directives.code import CodeBlock
from sphinx.writers.html5 import HTML5Translator

# ...from HydPy
from hydpy.core import autodoctools
from hydpy.core.typingtools import *


class SubmodelGraphNode(nodes.General, nodes.FixedTextElement):
    """The docutils node for the submodel graph directive."""

    modelname: str | None


class SubmodelGraphBlock(CodeBlock):
    """A sphinx directive specialised for submodel graph code blocks."""

    has_content = False
    required_arguments = 0
    optional_arguments = 1

    def run(self) -> list[Any]:  # ToDo: should we subclass from Node?
        """Prepare a `ProjectStructuSubmodelGraphNodereNode` object."""
        content = "\n".join(self.content)
        node = SubmodelGraphNode(content, content)
        node.line = self.lineno
        node.modelname = self.arguments[0] if len(self.arguments) == 1 else None
        return [node]


def visit_html(
    self: HTML5Translator, node: SubmodelGraphNode  # pylint: disable=unused-argument
) -> None:
    """Generate and insert the HTML code of the selected or of all relevant main
    models."""

    submodelgraph = autodoctools.SubmodelGraph(modelname=None)
    self.body[-1] = submodelgraph.html

    raise nodes.SkipNode


def setup(app: Sphinx) -> None:
    """Add the submodel graph extension to Sphinx."""

    app.add_directive("submodel_graph", SubmodelGraphBlock)
    app.add_node(SubmodelGraphNode, html=(visit_html, None))
