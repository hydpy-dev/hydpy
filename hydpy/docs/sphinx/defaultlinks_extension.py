"""Sphinx extension introducing directives as
`.. how_to_understand_model_integration_tests::`.
"""

from docutils import nodes as docutils_nodes
from docutils import statemachine
from docutils.parsers import rst
from sphinx import application
from sphinx.util import nodes as sphinx_nodes


class HowToUnderstandIntegrationTests(rst.Directive):
    """Directive the "How to understand integration tests?" section."""

    def run(self) -> list[docutils_nodes.Node]:
        """Include the text in a `note` block and add a reference via nested parsing."""
        stringlist = statemachine.StringList()
        stringlist.append(
            ".. note:: "
            "When new to *HydPy*, consider reading section "
            ":ref:`Integration Tests <integration_tests>` first.",
            "fakefile.rst",
            1,
        )
        node = docutils_nodes.section()
        node.document = self.state.document
        sphinx_nodes.nested_parse_with_titles(self.state, stringlist, node)
        return node.children


def setup(app: application.Sphinx) -> None:
    """Add the defined directives to the sphinx application."""
    app.add_directive(
        "how_to_understand_integration_tests", HowToUnderstandIntegrationTests
    )
