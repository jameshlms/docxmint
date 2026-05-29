import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "DocxMint"
author = "James Holmes"
release = "0.1.0"
copyright = f"2026, {author}"

extensions = [
    "autoapi.extension",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# sphinx-autoapi: reads source without importing the package.
# Safe when the native binary may not be present (CI, ReadTheDocs, etc.).
autoapi_dirs = ["../docxmint"]
autoapi_root = "api"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_python_use_implicit_namespaces = False
autoapi_keep_files = True
autoapi_add_toctree_entry = True
suppress_warnings = [
    "autoapi.python_import_resolution",
    "ref.python",  # autoapi cross-reference ambiguity on Style.type
]

# MyST — lets us write docs in Markdown
myst_enable_extensions = ["colon_fence", "deflist"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

html_theme = "furo"
html_static_path = ["_static"]
html_title = "DocxMint"

exclude_patterns = ["_build", "_static", "Thumbs.db", ".DS_Store", "DESIGN.md"]
