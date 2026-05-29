"""DocxMint — Pythonic ``.docx`` manipulation backed by a C# Native AOT library.

All document data lives in the C# layer; Python holds lightweight proxy objects
(handles). The central types are:

- :class:`Document` — open, create, and save ``.docx`` files
- :class:`Paragraph` / :class:`Run` — block text and character-level spans
- :class:`Table` / :class:`Row` / :class:`Cell` — tabular content
- :class:`Section` — page-layout containers
- :class:`Style` / :class:`StyleCollection` — style definitions

Use :func:`snapshot` to capture a document-independent copy of any proxy element
so it can be used after the document is closed.
"""

from docxmint._collection import DocumentView
from docxmint._proxy.base import ProxyBase as _ProxyBase
from docxmint.document import Document
from docxmint.errors import (
    DocumentClosedError,
    DocxMintError,
    NativeRuntimeError,
    OwnershipError,
    StaleProxyError,
)
from docxmint.formats import (
    Border,
    CellBorders,
    CellMargin,
    ColumnFormat,
    IndentFormat,
    ListFormat,
    PageMargins,
    ParagraphBorders,
    RGBColor,
    Shading,
    SpacingFormat,
    TableBorders,
)
from docxmint.hyperlink import Hyperlink
from docxmint.image import Image
from docxmint.paragraph import HorizontalRule, Paragraph
from docxmint.run import Run
from docxmint.section import Section
from docxmint.styles import Style, StyleCollection
from docxmint.table import Cell, Row, Table


def snapshot[T: _ProxyBase](elem: T) -> T:
    """Return a document-independent copy of *elem*.

    The returned object is in *construction state* — it has no native handle and
    can be safely used after the source document is closed. It can also be
    appended to a different document.

    Args:
        elem: Any live or construction-state proxy
            (:class:`Paragraph`, :class:`Run`, :class:`Table`, etc.).

    Returns:
        A new construction-state object of the same type with all properties
        copied from *elem*.

    Example:
        .. code-block:: python

            with Document.open("report.docx") as doc:
                para = doc.paragraphs[0]
                snap = snapshot(para)   # copy data before close

            # doc is closed — snap is still valid
            print(snap.text)
    """
    return elem.__copydocelem__()


__all__ = [
    # Core
    "snapshot",
    "Document",
    "DocumentView",
    "Paragraph",
    "HorizontalRule",
    "Run",
    "Image",
    "Hyperlink",
    "Table",
    "Row",
    "Cell",
    "Section",
    # Styles
    "Style",
    "StyleCollection",
    # Format types
    "RGBColor",
    "Border",
    "ParagraphBorders",
    "TableBorders",
    "CellBorders",
    "Shading",
    "IndentFormat",
    "SpacingFormat",
    "ListFormat",
    "PageMargins",
    "CellMargin",
    "ColumnFormat",
    # Errors
    "DocxMintError",
    "NativeRuntimeError",
    "DocumentClosedError",
    "StaleProxyError",
    "OwnershipError",
]

__version__ = "0.1.0"
