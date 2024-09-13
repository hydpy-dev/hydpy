# -*- coding: utf-8 -*-
# pylint: skip-file
# due to conforming to the "Sphinx style"
#
# HydPy documentation build configuration file, created by
# sphinx-quickstart on Thu Jun 09 14:33:31 2016.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

from collections.abc import Callable
import dataclasses
import os
import sys
from typing import Any

import pybtex.plugin
from pybtex.database import Person
from pybtex.richtext import Tag, Text
from pybtex.style.formatting.plain import Style as PlainFormattingStyle
from pybtex.style.names.plain import NameStyle as PlainNameStyle
from pybtex.style.names import name_part
from pybtex.style.template import Node

import sphinxcontrib.bibtex.plugin
from sphinxcontrib.bibtex.style.referencing import BracketStyle
from sphinxcontrib.bibtex.style.referencing.author_year import AuthorYearReferenceStyle
from sphinxcontrib.bibtex.style.referencing.basic_author_year import (
    BasicAuthorYearTextualReferenceStyle,
)
from sphinxcontrib.bibtex.style.template import reference, join, year

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("..\\..\\..\\"))
sys.path.insert(0, os.path.abspath("."))

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.mathjax",
    "sphinx.ext.doctest",
    "sphinxcontrib.bibtex",
    "sphinxcontrib.fulltoc",
    "integrationtest_extension",
    "defaultlinks_extension",
    "projectstructure_extension",
    "submodelgraph_extension",
]

autoclass_content = "class"
autodoc_default_options = {"undoc-members": None}
autodoc_member_order = "bysource"

# Napoleon settings
napoleon_google_docstring = False
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = False
napoleon_use_rtype = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/dev", None),
}

mathjax_path = (
    "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"
)
mathjax3_config = {"chtml": {"displayAlign": "left"}}


# Configure sphinxcontrib-bibtex *******************************************************


HYDPYNAMESTYLE = "hydpynamestyle"
HYDPYBIBLIOGRAPHYSTYLE = "hydpybibliographystyle"
HYDPYREFERENCESTYLE = "hydpyreferencestyle"


class HydPyNameStyle(PlainNameStyle):
    """Change compared to the base class: write last names in bold letters."""

    def format(self, person: Person, abbr: bool = False) -> Text:
        text_bold = [Tag("b", Text.from_latex(name)) for name in person.last_names]
        return join[
            name_part(tie=True, abbr=abbr)[
                person.rich_first_names + person.rich_middle_names
            ],
            name_part(tie=True)[person.rich_prelast_names],
            name_part[text_bold],
            name_part(before=", ")[person.rich_lineage_names],
        ]


pybtex.plugin.register_plugin("pybtex.style.names", HYDPYNAMESTYLE, HydPyNameStyle)


class HydPyBibliographyStyle(PlainFormattingStyle):
    """Change compared to the base class: use `HydPyNameStyle`."""

    default_name_style = HYDPYNAMESTYLE


pybtex.plugin.register_plugin(
    "pybtex.style.formatting", HYDPYBIBLIOGRAPHYSTYLE, HydPyBibliographyStyle
)


class HydPyTextualReferenceStyle(BasicAuthorYearTextualReferenceStyle):
    """Change compared to the base class: the hyperlink to the bibliography comprises
    the full reference."""

    def inner(self, role_name: str) -> Node:
        return reference[
            join(sep=self.text_reference_sep)[
                self.person.author_or_editor_or_title(full="s" in role_name),
                join[self.bracket.left, year, self.bracket.right],
            ]
        ]


@dataclasses.dataclass
class HydPyReferenceStyle(AuthorYearReferenceStyle):
    """Changed compared to the base class: use round brackets instead of square
    brackets; use `HydPyTextualReferenceStyle`."""

    _make_bracketstylefield: Callable[[], Any] = lambda: dataclasses.field(
        default_factory=lambda: BracketStyle(left="(", right=")")
    )

    bracket_parenthetical: BracketStyle = _make_bracketstylefield()
    bracket_textual: BracketStyle = _make_bracketstylefield()
    bracket_author: BracketStyle = _make_bracketstylefield()
    bracket_label: BracketStyle = _make_bracketstylefield()
    bracket_year: BracketStyle = _make_bracketstylefield()

    def __post_init__(self) -> None:
        super().__post_init__()
        for style in self.styles:
            if isinstance(style, BasicAuthorYearTextualReferenceStyle):
                style.__class__ = HydPyTextualReferenceStyle


sphinxcontrib.bibtex.plugin.register_plugin(
    "sphinxcontrib.bibtex.style.referencing", HYDPYREFERENCESTYLE, HydPyReferenceStyle
)

bibtex_bibfiles = ["refs.bib"]
bibtex_default_style = HYDPYBIBLIOGRAPHYSTYLE
bibtex_reference_style = HYDPYREFERENCESTYLE


# **************************************************************************************


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "HydPy"
copyright = "2023, HydPy Developers"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = "6.0"
# The full version, including alpha/beta/rc tags.
release = "6.0.1"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "classic_hydpy"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "stickysidebar": True,
    "sidebarwidth": 0,
    "body_max_width": "100%",
}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ["_themes"]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "HydPy_Logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = []
html_extra_path = ["html_"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_domain_indices = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = "HydPydoc"


# -- Options for LaTeX output --------------------------------------------------

latex_elements: dict[str, str] = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ("index", "HydPy.tex", "HydPy Documentation", "HydPy Developers", "manual")
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# If true, show page references after internal links.
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "hydpy", "HydPy Documentation", ["HydPy Developers"], 1)]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "HydPy",
        "HydPy Documentation",
        "HydPy Developers",
        "HydPy",
        "One line description of project.",
        "Miscellaneous",
    )
]

# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'
