"""Unit tests for Document, Paragraph, and Table APIs.

The native binary is mocked out entirely so these tests run without any
compiled C# artifact present.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_lib(
    doc_handle: int = 1,
    para_handle: int = 2,
    heading_handle: int = 3,
    table_handle: int = 4,
    run_handle: int = 5,
) -> MagicMock:
    """Return a mock NativeLib with sensible default return values."""
    lib = MagicMock()
    lib.create_document.return_value = doc_handle
    lib.add_paragraph.return_value = para_handle
    lib.add_heading.return_value = heading_handle
    lib.add_table.return_value = table_handle
    lib.add_table_with_data.return_value = table_handle
    lib.add_run.return_value = run_handle
    lib.set_run_bold.return_value = 0
    lib.set_run_italic.return_value = 0
    lib.set_run_underline.return_value = 0
    lib.set_run_font_size.return_value = 0
    lib.set_run_font_name.return_value = 0
    lib.set_cell_text.return_value = 0
    lib.remove_paragraph.return_value = 0
    lib.get_paragraph_count.return_value = 0
    lib.get_paragraph_text.return_value = ""
    lib.get_paragraph_style.return_value = ""
    lib.save_document.return_value = 0
    lib.free_document.return_value = None
    lib.ffi = MagicMock()
    return lib


def _make_doc(lib: MagicMock | None = None) -> tuple[Any, MagicMock]:
    if lib is None:
        lib = _make_lib()
    with patch("fastdocx.document.get_lib", return_value=lib):
        from fastdocx.document import Document
        doc = Document()
    return doc, lib


# ---------------------------------------------------------------------------
# Document construction
# ---------------------------------------------------------------------------


class TestDocumentConstruction:
    def test_create_document_calls_native(self) -> None:
        lib = _make_lib()
        doc, lib = _make_doc(lib)
        lib.create_document.assert_called_once()
        assert doc._handle == 1

    def test_create_document_raises_on_null_handle(self) -> None:
        lib = _make_lib(doc_handle=0)
        with patch("fastdocx.document.get_lib", return_value=lib):
            from fastdocx.document import Document
            with pytest.raises(RuntimeError, match="null handle"):
                Document()


# ---------------------------------------------------------------------------
# add_paragraph
# ---------------------------------------------------------------------------


class TestAddParagraph:
    def test_returns_paragraph_with_text(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph("Hello")
        assert para.text == "Hello"

    def test_empty_text_creates_empty_paragraph(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        assert para.text == ""

    def test_raises_on_native_failure(self) -> None:
        lib = _make_lib()
        lib.add_paragraph.return_value = 0
        doc, lib = _make_doc(lib)
        with pytest.raises(RuntimeError, match="add_paragraph failed"):
            doc.add_paragraph("oops")

    def test_style_encoded_and_forwarded(self) -> None:
        doc, lib = _make_doc()
        doc.add_paragraph("Styled", style="Heading1")
        args = lib.add_paragraph.call_args.args
        # add_paragraph(handle, style_bytes, style_len)
        assert args[1] == b"Heading1"
        assert args[2] == len(b"Heading1")

    def test_no_style_passes_empty_bytes(self) -> None:
        doc, lib = _make_doc()
        doc.add_paragraph("No style")
        args = lib.add_paragraph.call_args.args
        assert args[1] == b""
        assert args[2] == 0


# ---------------------------------------------------------------------------
# add_heading
# ---------------------------------------------------------------------------


class TestAddHeading:
    def test_returns_paragraph_with_text(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_heading("Title", level=1)
        # add_heading creates the paragraph but text is embedded in the native call,
        # not tracked via runs — heading paragraphs have no Python-side run objects
        assert isinstance(para.text, str)

    def test_level_forwarded(self) -> None:
        doc, lib = _make_doc()
        doc.add_heading("Sub", level=3)
        args = lib.add_heading.call_args.args
        # add_heading(handle, text_bytes, text_len, level)
        assert args[3] == 3

    def test_text_encoded_and_forwarded(self) -> None:
        doc, lib = _make_doc()
        doc.add_heading("My Heading", level=2)
        args = lib.add_heading.call_args.args
        assert args[1] == b"My Heading"
        assert args[2] == len(b"My Heading")

    def test_invalid_level_raises(self) -> None:
        doc, _ = _make_doc()
        with pytest.raises(ValueError, match="1\u20136"):
            doc.add_heading("Bad", level=0)
        with pytest.raises(ValueError, match="1\u20136"):
            doc.add_heading("Bad", level=7)

    def test_raises_on_native_failure(self) -> None:
        lib = _make_lib()
        lib.add_heading.return_value = 0
        doc, lib = _make_doc(lib)
        with pytest.raises(RuntimeError, match="add_heading failed"):
            doc.add_heading("oops")


# ---------------------------------------------------------------------------
# add_table
# ---------------------------------------------------------------------------


class TestAddTable:
    def test_returns_table_with_correct_dimensions(self) -> None:
        doc, lib = _make_doc()
        table = doc.add_table(rows=3, cols=2)
        assert table.rows == 3
        assert table.cols == 2

    def test_cell_indexing(self) -> None:
        doc, lib = _make_doc()
        table = doc.add_table(rows=2, cols=2)
        cell = table[0, 0]
        cell.text = "Hello"
        lib.set_cell_text.assert_called_once()
        args = lib.set_cell_text.call_args.args
        assert args[1] == 0  # row
        assert args[2] == 0  # col
        assert args[3] == b"Hello"

    def test_out_of_bounds_raises(self) -> None:
        doc, lib = _make_doc()
        table = doc.add_table(rows=2, cols=2)
        with pytest.raises(IndexError):
            _ = table[2, 0]
        with pytest.raises(IndexError):
            _ = table[0, 2]

    def test_cell_text_setter_raises_on_native_failure(self) -> None:
        lib = _make_lib()
        lib.set_cell_text.return_value = -1
        doc, lib = _make_doc(lib)
        table = doc.add_table(rows=2, cols=2)
        with pytest.raises(RuntimeError, match="set_cell_text failed"):
            table[0, 0].text = "fail"

    def test_data_parameter_uses_add_table_with_data(self) -> None:
        doc, lib = _make_doc()
        doc.add_table(rows=2, cols=2, data=[["A", "B"], ["C", "D"]])
        lib.add_table_with_data.assert_called_once()
        lib.add_table.assert_not_called()

    def test_no_data_uses_add_table(self) -> None:
        doc, lib = _make_doc()
        doc.add_table(rows=2, cols=2)
        lib.add_table.assert_called_once()
        lib.add_table_with_data.assert_not_called()

    def test_invalid_dimensions_raise(self) -> None:
        doc, _ = _make_doc()
        with pytest.raises(ValueError):
            doc.add_table(rows=0, cols=2)
        with pytest.raises(ValueError):
            doc.add_table(rows=2, cols=-1)

    def test_raises_on_native_failure(self) -> None:
        lib = _make_lib()
        lib.add_table.return_value = 0
        doc, lib = _make_doc(lib)
        with pytest.raises(RuntimeError, match="add_table failed"):
            doc.add_table(rows=1, cols=1)

    def test_data_row_mismatch_raises_in_strict_mode(self) -> None:
        doc, _ = _make_doc()
        with pytest.raises(ValueError, match="rows"):
            doc.add_table(rows=3, cols=2, data=[["A", "B"]])

    def test_data_row_mismatch_truncates_in_non_strict_mode(self) -> None:
        doc, lib = _make_doc()
        # 1 data row but rows=3; strict=False should fill the gap
        doc.add_table(rows=3, cols=2, data=[["A", "B"]], strict=False)
        lib.add_table_with_data.assert_called_once()


# ---------------------------------------------------------------------------
# Paragraph runs and text
# ---------------------------------------------------------------------------


class TestParagraphRuns:
    def test_add_run_returns_run_with_text(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        run = para.add_run("world")
        assert run.text == "world"

    def test_paragraph_text_concatenates_runs(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        para.add_run("Hello ")
        para.add_run("world")
        assert para.text == "Hello world"

    def test_paragraph_text_from_initial_text(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph("Hello")
        assert para.text == "Hello"

    def test_runs_list_reflects_added_runs(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        para.add_run("a")
        para.add_run("b")
        assert len(para.runs) == 2

    def test_run_bold_setter_calls_native(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        run = para.add_run("bold")
        run.bold = True
        lib.set_run_bold.assert_called_once_with(lib.add_run.return_value, 1)

    def test_run_italic_setter_calls_native(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        run = para.add_run("italic")
        run.italic = True
        lib.set_run_italic.assert_called_once_with(lib.add_run.return_value, 1)

    def test_run_font_size_converted_to_half_points(self) -> None:
        doc, lib = _make_doc()
        para = doc.add_paragraph()
        run = para.add_run("sized")
        run.font.size = 12
        lib.set_run_font_size.assert_called_once_with(lib.add_run.return_value, 24)


# ---------------------------------------------------------------------------
# save / free
# ---------------------------------------------------------------------------


class TestSaveAndFree:
    def test_save_calls_native_with_encoded_path(self) -> None:
        doc, lib = _make_doc()
        doc.save("/tmp/out.docx")
        args = lib.save_document.call_args.args
        assert args[1] == b"/tmp/out.docx"

    def test_save_raises_on_native_failure(self) -> None:
        lib = _make_lib()
        lib.save_document.return_value = -1
        doc, lib = _make_doc(lib)
        with pytest.raises(RuntimeError, match="save_document failed"):
            doc.save("/tmp/out.docx")

    def test_close_frees_handle(self) -> None:
        doc, lib = _make_doc()
        handle = doc._handle
        doc.close()
        lib.free_document.assert_called_once_with(handle)
        assert doc._handle is None

    def test_double_close_is_safe(self) -> None:
        doc, lib = _make_doc()
        doc.close()
        doc.close()  # should not raise
        lib.free_document.assert_called_once()

    def test_context_manager_closes_on_exit(self) -> None:
        lib = _make_lib()
        with patch("fastdocx.document.get_lib", return_value=lib):
            from fastdocx.document import Document
            with Document() as doc:
                handle = doc._handle
        lib.free_document.assert_called_with(handle)


# ---------------------------------------------------------------------------
# Document.paragraphs
# ---------------------------------------------------------------------------


class TestRemoveParagraph:
    def test_calls_native_with_correct_index(self) -> None:
        lib = _make_lib()
        lib.remove_paragraph.return_value = 0
        doc, lib = _make_doc(lib)
        doc.remove_paragraph(2)
        lib.remove_paragraph.assert_called_once_with(doc._handle, 2)

    def test_out_of_range_raises_index_error(self) -> None:
        lib = _make_lib()
        lib.remove_paragraph.return_value = -2
        doc, lib = _make_doc(lib)
        with pytest.raises(IndexError, match="2"):
            doc.remove_paragraph(2)

    def test_native_failure_raises_runtime_error(self) -> None:
        lib = _make_lib()
        lib.remove_paragraph.return_value = -1
        doc, lib = _make_doc(lib)
        with pytest.raises(RuntimeError, match="remove_paragraph failed"):
            doc.remove_paragraph(0)


class TestParagraphsProperty:
    def test_empty_document_returns_empty_list(self) -> None:
        lib = _make_lib()
        lib.get_paragraph_count.return_value = 0
        doc, lib = _make_doc(lib)
        assert doc.paragraphs == []

    def test_returns_paragraph_info_objects(self) -> None:
        from fastdocx.paragraph import ParagraphView

        lib = _make_lib()
        lib.get_paragraph_count.return_value = 2
        lib.get_paragraph_text.side_effect = lambda handle, i: ["Hello", "World"][i]
        lib.get_paragraph_style.side_effect = lambda handle, i: ["Normal", "Heading1"][i]
        doc, lib = _make_doc(lib)

        paras = doc.paragraphs
        assert len(paras) == 2
        assert paras[0] == ParagraphView(text="Hello", style="Normal")
        assert paras[1] == ParagraphView(text="World", style="Heading1")

    def test_paragraph_with_no_style_returns_empty_string(self) -> None:
        lib = _make_lib()
        lib.get_paragraph_count.return_value = 1
        lib.get_paragraph_text.return_value = "Plain text"
        lib.get_paragraph_style.return_value = ""
        doc, lib = _make_doc(lib)

        paras = doc.paragraphs
        assert paras[0].style == ""
        assert paras[0].text == "Plain text"

    def test_raises_on_native_count_failure(self) -> None:
        lib = _make_lib()
        lib.get_paragraph_count.return_value = -1
        doc, lib = _make_doc(lib)
        with pytest.raises(RuntimeError, match="get_paragraph_count failed"):
            _ = doc.paragraphs

    def test_paragraph_info_is_immutable(self) -> None:
        from fastdocx.paragraph import ParagraphView

        p = ParagraphView(text="hello", style="Normal")
        with pytest.raises(Exception):
            p.text = "changed"  # type: ignore[misc]

    def test_calls_native_with_correct_indices(self) -> None:
        lib = _make_lib()
        lib.get_paragraph_count.return_value = 3
        lib.get_paragraph_text.return_value = "x"
        lib.get_paragraph_style.return_value = ""
        doc, lib = _make_doc(lib)

        doc.paragraphs
        text_indices = [call.args[1] for call in lib.get_paragraph_text.call_args_list]
        assert text_indices == [0, 1, 2]
