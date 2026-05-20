"""python-docx compatible wrapper over the native Document.

Differences from the native API:
- No context manager required — document disposed on GC or explicit close().
- doc.add_paragraph(text, style) and similar add_* methods exist.
- doc.paragraphs returns an eager list, not a live view.
- close() method triggers the same dispose logic as context manager exit.
- ResourceWarning is issued if the document is GC'd without close().
"""
from __future__ import annotations

import traceback
import warnings
from typing import Any

from fastdocx.document import Document as _NativeDocument
from fastdocx.paragraph import Paragraph
from fastdocx.run import Run
from fastdocx.table import Table


class Document:
    """python-docx compatible document wrapper.

    Example::

        from fastdocx.compat import Document

        doc = Document()
        para = doc.add_paragraph("Hello, world!")
        doc.save("output.docx")
        doc.close()

    Or open an existing file::

        doc = Document("existing.docx")
    """

    def __init__(self, path: str | None = None) -> None:
        object.__setattr__(self, "_open_traceback", traceback.extract_stack())
        object.__setattr__(self, "_closed", False)
        if path is None:
            object.__setattr__(self, "_doc", _NativeDocument())
        else:
            object.__setattr__(self, "_doc", _NativeDocument.open(path))

    def _native(self) -> _NativeDocument:
        doc: _NativeDocument = object.__getattribute__(self, "_doc")
        return doc

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close and dispose the document."""
        if not object.__getattribute__(self, "_closed"):
            object.__setattr__(self, "_closed", True)
            self._native().close()

    def __del__(self) -> None:
        if not object.__getattribute__(self, "_closed"):
            tb = object.__getattribute__(self, "_open_traceback")
            warnings.warn(
                f"Document opened at:\n{''.join(traceback.format_list(tb))}"
                "was not explicitly closed. Call close() or use the native API "
                "with a context manager to ensure correct disposal.",
                ResourceWarning,
                stacklevel=2,
            )
            try:
                self._native().close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # python-docx compatible properties
    # ------------------------------------------------------------------

    @property
    def paragraphs(self) -> list[Paragraph]:
        return list(self._native().paragraphs)

    @property
    def tables(self) -> list[Table]:
        return list(self._native().tables)

    # ------------------------------------------------------------------
    # python-docx compatible add_* methods
    # ------------------------------------------------------------------

    def add_paragraph(self, text: str = "", style: str | None = None) -> Paragraph:
        """Add a paragraph and return a live proxy."""
        para = Paragraph(text, style=style or "Normal")
        view = self._native().paragraphs
        proxy = view._append_one(para)  # type: ignore[attr-defined]
        return proxy

    def add_heading(self, text: str = "", level: int = 1) -> Paragraph:
        """Add a heading paragraph."""
        style = f"Heading{level}"
        return self.add_paragraph(text, style=style)

    def add_table(self, rows: int, cols: int, style: str = "TableGrid") -> Table:
        """Add a table and return a live proxy."""
        t = Table(rows=rows, cols=cols, style=style)
        view = self._native().tables
        return view._append_one(t)  # type: ignore[attr-defined, return-value]

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Save the document to *path*."""
        self._native().save(path)
