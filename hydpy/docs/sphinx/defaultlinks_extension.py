"""Sphinx extension introducing directives as
`.. how_to_understand_model_integration_tests::`.
"""
# import...
from typing import *

# ...from hydpy
from hydpy.core import exceptiontools

docutils_nodes = exceptiontools.OptionalImport(
    "nodes",
    ["docutils.nodes"],
    locals(),
)
statemachine = exceptiontools.OptionalImport(
    "nodes",
    ["docutils.statemachine"],
    locals(),
)
sphinx_nodes = exceptiontools.OptionalImport(
    "nodes",
    ["sphinx.util.nodes"],
    locals(),
)
rst = exceptiontools.OptionalImport(
    "rst",
    ["docutils.parsers.rst"],
    locals(),
)

if TYPE_CHECKING:
    from docutils import nodes as docutils_nodes
    from docutils import statemachine
    from docutils.parsers import rst
    from sphinx.util import nodes as sphinx_nodes


class HowToUnderstandIntegrationTests(rst.Directive):
    """Directive the "How to understand integration tests?" section."""

    def run(self):
        """Include the text in a `note` block and add a reference via
        nested parsing."""
        viewlist = statemachine.ViewList()
        viewlist.append(
            ".. note:: "
            "When new to *HydPy*, consider reading section "
            ":ref:`How to understand integration tests? "
            "<understand_integration_tests>` first.",
            "fakefile.rst",
            1,
        )
        node = docutils_nodes.section()
        node.document = self.state.document
        sphinx_nodes.nested_parse_with_titles(
            self.state,
            viewlist,
            node,
        )
        return node.children


def setup(app):
    """Add the defined directives to the sphinx application."""
    app.add_directive(
        "how_to_understand_integration_tests",
        HowToUnderstandIntegrationTests,
    )
