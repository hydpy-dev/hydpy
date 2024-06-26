"""Sphinx extension introducing `.. integration-test::` directives."""

# import...
# from standard library
from typing import Any

# ...from site-packages
from docutils import nodes
from sphinx.directives import code


counter = 0

CODE_SHOWHIDE = """\
<script type="text/javascript">
    function showhide(element){
        if (!document.getElementById)
            return
        if (element.style.display == "block")
            element.style.display = "none"
        else
            element.style.display = "block"
    };
</script>\
"""


class IntegrationTestNode(nodes.General, nodes.FixedTextElement):
    """The docutils node for the integration test directive."""


class IntegrationTestBlock(code.CodeBlock):
    """A sphinx directive specialised for integration test code blocks."""

    def run(self) -> list[Any]:  # ToDo: should we subclass from Node?
        """Return only an `IntegrationTestNode` object."""
        content = "\n".join(self.content)
        integrationtestnode = IntegrationTestNode(content, content)
        integrationtestnode.line = self.lineno
        return [integrationtestnode]


def visit_html(self, node):
    """Modify the already generated HTML code.  Add the JavaScript code defined of
    `CODE_SHOWHIDE` between the `test()` call and the result table and include the
    generated HTML file at the bottom."""
    global counter
    counter += 1

    try:
        self.visit_literal_block(node)
    except nodes.SkipNode:
        pass

    divname = f"__hydpy_integrationtest_{counter}__"
    divheader = (
        f"<a href=\"javascript:showhide(document.getElementById('{divname}'))\""
        f">Click to see the table</a><br />"
        f'<div id="{divname}" style="display: none">'
    )
    code_complete = self.body[-1]

    idx0 = code_complete.find('<div class="highlight-default notranslate">')
    idx1 = code_complete.find('<span class="go">')
    code_commands = f"{code_complete[idx0:idx1]}"
    code_commands = code_commands.replace(
        '<div class="highlight-default notranslate">',
        '<div class="doctest highlight-default notranslate">',
    )

    idx0 = code_complete.find('<span class="gp">')
    code_table = f"{code_complete[:idx0]}{code_complete[idx1:]}"
    code_table = code_table.replace("</pre></div>\n</div>\n", "</pre></div></div>")

    try:
        idx0 = code_complete.find('class="s2"')
        filename = code_complete[idx0:].split("quot")[1][1:-1]
        code_graph = (
            f'<a href="{filename}.html" target="_blank" ' ">Click to see the graph</a>"
        )
    except IndexError:
        code_graph = ""

    self.body[-1] = "".join(
        [
            code_commands,
            CODE_SHOWHIDE,
            divheader,
            code_table,
            "</div>",
            code_graph,
            "</pre></div></div>",
        ]
    )
    raise nodes.SkipNode


# noinspection PyUnusedLocal
def depart_html(self, node):  # pylint: disable=unused-argument
    """No need to implement anything."""


def setup(app):
    """Add the defined node `IntegrationTestNode` and directive `IntegrationTestBlock`
    to the sphinx application."""
    app.add_directive("integration-test", IntegrationTestBlock)
    app.add_node(IntegrationTestNode, html=(visit_html, depart_html))
