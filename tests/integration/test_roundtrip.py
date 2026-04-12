"""Integration round-trip tests.

Generates a real .docx with FastDOCX (requires the native binary), then opens
it with python-docx and asserts on paragraph text and table structure.

Automatically skipped when the native binary is not present.
"""

from __future__ import annotations

import os
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Skip guard — import Document lazily inside each test so that importing this
# module never raises even when the binary is absent.
# ---------------------------------------------------------------------------

_SKIP_REASON = "Native FastDOCX binary not available on this platform"


def _native_available() -> bool:
    """Return True only if loader.get_lib() succeeds without error."""
    try:
        from fastdocx._native.loader import get_lib

        get_lib()
        return True
    except RuntimeError:
        return False


native_only = pytest.mark.skipif(not _native_available(), reason=_SKIP_REASON)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_docx(path: str) -> docx.Document:  # type: ignore[name-defined]
    import docx  # type: ignore[import-untyped]

    return docx.Document(path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@native_only
def test_paragraph_roundtrip() -> None:
    """Paragraphs written by FastDOCX are readable by python-docx."""
    from fastdocx import Document

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = f.name

    try:
        doc = Document()
        doc.add_paragraph("Hello, world!")
        doc.add_paragraph().add_run("Bold text").bold = True
        doc.save(path)

        loaded = _open_docx(path)
        texts = [p.text for p in loaded.paragraphs]
        assert "Hello, world!" in texts
        assert "Bold text" in texts
    finally:
        os.unlink(path)


@native_only
def test_heading_roundtrip() -> None:
    """Headings written by FastDOCX have the correct style in python-docx."""
    from fastdocx import Document

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = f.name

    try:
        doc = Document()
        doc.add_heading("Chapter One", level=1)
        doc.add_heading("Section 1.1", level=2)
        doc.save(path)

        loaded = _open_docx(path)
        headings = {p.text: p.style.name for p in loaded.paragraphs if p.text}
        assert "Chapter One" in headings
        assert "Section 1.1" in headings
        assert "Heading 1" in headings["Chapter One"]
        assert "Heading 2" in headings["Section 1.1"]
    finally:
        os.unlink(path)


@native_only
def test_table_roundtrip() -> None:
    """Tables written by FastDOCX have the correct cell text in python-docx."""
    from fastdocx import Document

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = f.name

    try:
        doc = Document()
        table = doc.add_table(rows=2, cols=2)
        table[0, 0].text = "Region"
        table[0, 1].text = "Revenue"
        table[1, 0].text = "North"
        table[1, 1].text = "$1.2M"
        doc.save(path)

        loaded = _open_docx(path)
        assert len(loaded.tables) == 1
        tbl = loaded.tables[0]
        assert tbl.cell(0, 0).text == "Region"
        assert tbl.cell(0, 1).text == "Revenue"
        assert tbl.cell(1, 0).text == "North"
        assert tbl.cell(1, 1).text == "$1.2M"
    finally:
        os.unlink(path)


@native_only
def test_full_document_roundtrip() -> None:
    """The README quickstart example produces a valid document."""
    from fastdocx import Document

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = f.name

    try:
        doc = Document()
        doc.add_heading("Project Report", level=1)
        doc.add_paragraph().add_run("This report summarises Q1 findings.").bold = True

        table = doc.add_table(rows=3, cols=2)
        table[0, 0].text = "Region"
        table[0, 1].text = "Revenue"
        table[1, 0].text = "North"
        table[1, 1].text = "$1.2M"
        table[2, 0].text = "South"
        table[2, 1].text = "$0.9M"

        doc.save(path)

        loaded = _open_docx(path)
        para_texts = [p.text for p in loaded.paragraphs]
        assert "Project Report" in para_texts
        assert "This report summarises Q1 findings." in para_texts

        assert len(loaded.tables) == 1
        tbl = loaded.tables[0]
        assert tbl.cell(0, 0).text == "Region"
        assert tbl.cell(2, 1).text == "$0.9M"
    finally:
        os.unlink(path)
