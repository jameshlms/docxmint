"""FastDOCX — Pythonic DOCX manipulation via a C# Native AOT shared library."""

from fastdocx._proxy.base import ProxyBase as _ProxyBase
from fastdocx.document import Document
from fastdocx.errors import (
    DocumentClosedError,
    FastDocxError,
    NativeRuntimeError,
    OwnershipError,
    StaleProxyError,
)
from fastdocx.formats import (
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
from fastdocx.paragraph import HorizontalRule, Paragraph
from fastdocx.run import Run
from fastdocx.section import Section
from fastdocx.styles import Style, StyleCollection
from fastdocx.table import Cell, Row, Table


def snapshot[T: _ProxyBase](elem: T) -> T:
    """Return a document-independent snapshot of *elem*.

    Calls ``elem.__copydocelem__()`` and returns the result — a mutable copy
    with no native handle, safe to keep after the document is closed.

        para = doc.paragraphs[0]
        snap = snapshot(para)   # safe to use after ``doc.close()``
    """
    return elem.__copydocelem__()


__all__ = [
    # Core
    "snapshot",
    "Document",
    "Paragraph",
    "HorizontalRule",
    "Run",
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
    "FastDocxError",
    "NativeRuntimeError",
    "DocumentClosedError",
    "StaleProxyError",
    "OwnershipError",
]

__version__ = "0.1.0"
