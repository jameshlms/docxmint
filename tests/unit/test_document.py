"""Unit tests for the fastdocx proxy model, DocumentView, and Document.

The native binary is mocked at the Handle level — no compiled C# needed.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.unit.mock_handle import MockHandle


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("fastdocx._native.handle.get_handle", return_value=mock):
        from fastdocx.document import Document
        doc = Document()
    return doc, mock


# ---------------------------------------------------------------------------
# Document construction
# ---------------------------------------------------------------------------

class TestDocumentConstruction:
    def test_creates_handle_on_init(self):
        mock = MockHandle()
        doc, _ = _make_doc(mock)
        assert doc._handle in mock._handles

    def test_is_open_after_creation(self):
        doc, _ = _make_doc()
        assert doc.is_open

    def test_close_marks_not_open(self):
        doc, _ = _make_doc()
        doc.close()
        assert not doc.is_open

    def test_double_close_is_safe(self):
        doc, mock = _make_doc()
        doc.close()
        doc.close()  # should not raise

    def test_context_manager_closes_on_exit(self):
        mock = MockHandle()
        with patch("fastdocx._native.handle.get_handle", return_value=mock):
            from fastdocx.document import Document
            with Document() as doc:
                handle = doc._handle
        assert doc.is_open is False

    def test_require_open_raises_after_close(self):
        from fastdocx.errors import DocumentClosedError
        doc, _ = _make_doc()
        doc.close()
        with pytest.raises(DocumentClosedError):
            doc._require_open()

    def test_document_open_classmethod(self):
        mock = MockHandle()
        mock.open_document = lambda path: mock.create_document()
        with patch("fastdocx._native.handle.get_handle", return_value=mock):
            from fastdocx.document import Document
            doc = Document.open("test.docx")
        assert doc.is_open


# ---------------------------------------------------------------------------
# Document as collection
# ---------------------------------------------------------------------------

class TestDocumentAsCollection:
    def test_len_is_zero_initially(self):
        doc, _ = _make_doc()
        assert len(doc) == 0

    def test_append_paragraph(self):
        from fastdocx.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("Hello"))
        assert len(doc) == 1

    def test_append_sets_text(self):
        from fastdocx.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("Hello"))
        para = doc.paragraphs[0]
        assert para.text == "Hello"

    def test_iter_yields_paragraphs(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("First"))
        doc.paragraphs.append(Paragraph("Second"))
        texts = [str(p) for p in doc.paragraphs]
        assert texts == ["First", "Second"]

    def test_paragraphs_first_last(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("First"))
        doc.paragraphs.append(Paragraph("Last"))
        assert doc.paragraphs.first.text == "First"
        assert doc.paragraphs.last.text == "Last"

    def test_paragraphs_first_is_none_when_empty(self):
        doc, _ = _make_doc()
        assert doc.paragraphs.first is None

    def test_remove_marks_proxy_stale(self):
        from fastdocx.errors import StaleProxyError
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("Temp"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        with pytest.raises(StaleProxyError, match=r"snapshot\(\)"):
            _ = para.text

    def test_pop_removes_and_returns(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        popped = doc.paragraphs.pop()
        assert popped.text == "B"
        assert len(doc.paragraphs) == 1

    def test_append_table(self):
        from fastdocx.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=3))
        assert len(doc.tables) == 1

    def test_type_error_on_wrong_type_in_filtered_view(self):
        from fastdocx.paragraph import Paragraph
        from fastdocx.table import Table
        doc, _ = _make_doc()
        with pytest.raises(TypeError, match="DocumentView"):
            doc.paragraphs.append(Table(rows=1, cols=1))  # type: ignore

    def test_getitem_by_type_returns_filtered_view(self):
        from fastdocx.collection import DocumentView
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        view = doc[Paragraph]
        assert isinstance(view, DocumentView)

    def test_group_two_types(self):
        from fastdocx.collection import DocumentView
        from fastdocx.paragraph import Paragraph
        from fastdocx.table import Table
        doc, _ = _make_doc()
        view = doc.group([Paragraph, Table])
        assert isinstance(view, DocumentView)


# ---------------------------------------------------------------------------
# Paragraph proxy
# ---------------------------------------------------------------------------

class TestParagraphProxy:
    def test_text_roundtrip_live(self):
        from fastdocx.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("hello"))
        para = doc.paragraphs[0]
        assert para.text == "hello"
        para.text = "world"
        assert para.text == "world"

    def test_style_roundtrip_live(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("hi", style="Heading1"))
        para = doc.paragraphs[0]
        assert para.style == "Heading1"
        para.style = "Normal"
        assert para.style == "Normal"

    def test_alignment_roundtrip_live(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("hi", alignment="center"))
        para = doc.paragraphs[0]
        assert para.alignment == "center"
        para.alignment = "right"
        assert para.alignment == "right"

    def test_alignment_rejects_invalid(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("hi"))
        para = doc.paragraphs[0]
        with pytest.raises(ValueError, match="alignment"):
            para.alignment = "diagonal"  # type: ignore

    def test_spec_reads_from_data(self):
        from fastdocx.paragraph import Paragraph
        para = Paragraph("spec text", style="Heading2")
        assert para.text == "spec text"
        assert para.style == "Heading2"
        assert not para._is_live

    def test_copy_returns_snapshot(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("snapshot me"))
        para = doc.paragraphs[0]
        snap = para.copy()
        assert isinstance(snap, Paragraph)
        assert not snap._is_live
        assert snap.text == "snapshot me"

    def test_document_closed_raises_on_access(self):
        from fastdocx.errors import DocumentClosedError
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("bye"))
        para = doc.paragraphs[0]
        doc.close()
        with pytest.raises(DocumentClosedError, match=r"snapshot\(\)"):
            _ = para.text

    def test_stale_proxy_raises_on_access(self):
        from fastdocx.errors import StaleProxyError
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("gone"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        with pytest.raises(StaleProxyError, match=r"snapshot\(\)"):
            _ = para.text

    def test_unknown_attribute_raises(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        with pytest.raises(AttributeError):
            _ = para.no_such_attr


# ---------------------------------------------------------------------------
# Run proxy
# ---------------------------------------------------------------------------

class TestRunProxy:
    def _para_with_run(self, text: str = "hello", **run_kwargs):
        from fastdocx.paragraph import Paragraph
        from fastdocx.run import Run
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run(text, **run_kwargs))
        run = para.runs[0]
        return run, mock

    def test_text_roundtrip(self):
        run, _ = self._para_with_run("hello")
        assert run.text == "hello"
        run.text = "world"
        assert run.text == "world"

    def test_bold_roundtrip(self):
        run, _ = self._para_with_run(bold=True)
        assert run.bold is True
        run.bold = False
        assert run.bold is False

    def test_italic_roundtrip(self):
        run, _ = self._para_with_run(italic=True)
        assert run.italic is True

    def test_font_size_roundtrip(self):
        run, _ = self._para_with_run(font_size=12.0)
        assert run.font_size == 12.0

    def test_font_name_roundtrip(self):
        run, _ = self._para_with_run(font_name="Arial")
        assert run.font_name == "Arial"

    def test_color_roundtrip(self):
        from fastdocx.run import Run
        doc, _ = _make_doc()
        from fastdocx.paragraph import Paragraph
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x"))
        run = para.runs[0]
        run.color = "#FF0000"
        # mock stores bare hex (after # strip in ColorProperty)
        assert run.color in ("#FF0000", "FF0000")

    def test_mutex_all_caps_small_caps(self):
        from fastdocx.run import Run
        with pytest.raises(ValueError, match="mutually exclusive"):
            Run("x", all_caps=True, small_caps=True)

    def test_mutex_superscript_subscript(self):
        from fastdocx.run import Run
        with pytest.raises(ValueError, match="mutually exclusive"):
            Run("x", superscript=True, subscript=True)

    def test_copy_returns_snapshot(self):
        from fastdocx.run import Run
        run, _ = self._para_with_run("copy me", bold=True)
        snap = run.copy()
        assert isinstance(snap, Run)
        assert not snap._is_live
        assert snap.text == "copy me"
        assert snap.bold is True

    def test_stale_run_raises(self):
        from fastdocx.errors import StaleProxyError
        run, _ = self._para_with_run("temp")
        object.__setattr__(run, "_stale", True)
        with pytest.raises(StaleProxyError, match=r"snapshot\(\)"):
            _ = run.text

    def test_spec_run_has_correct_data(self):
        from fastdocx.run import Run
        run = Run("spec", bold=True, italic=False)
        assert run.text == "spec"
        assert run.bold is True
        assert not run._is_live


# ---------------------------------------------------------------------------
# Table proxy
# ---------------------------------------------------------------------------

class TestTableProxy:
    def test_table_append_and_access(self):
        from fastdocx.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=3))
        assert len(doc.tables) == 1
        table = doc.tables[0]
        assert isinstance(table, Table)

    def test_table_rows_count(self):
        from fastdocx.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=3, cols=2))
        table = doc.tables[0]
        assert len(table.rows) == 3

    def test_table_cell_access(self):
        from fastdocx.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=2))
        table = doc.tables[0]
        cell = table.cell(0, 0)
        cell.text = "R0C0"
        assert table.cell(0, 0).text == "R0C0"

    def test_table_getitem_tuple(self):
        from fastdocx.table import Table
        doc, _ = _make_doc()
        doc.tables.append(Table(rows=2, cols=2))
        table = doc.tables[0]
        table[1, 0].text = "R1C0"
        assert table[1, 0].text == "R1C0"


# ---------------------------------------------------------------------------
# DocumentView
# ---------------------------------------------------------------------------

class TestDocumentView:
    def test_slice_returns_view(self):
        from fastdocx.collection import DocumentView
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        for i in range(4):
            doc.paragraphs.append(Paragraph(f"Para {i}"))
        sliced = doc.paragraphs[1:3]
        assert isinstance(sliced, DocumentView)
        assert len(sliced) == 2

    def test_bool_false_when_empty(self):
        doc, _ = _make_doc()
        assert not doc.paragraphs

    def test_bool_true_when_not_empty(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        assert doc.paragraphs

    def test_iadd_extends(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs += [Paragraph("A"), Paragraph("B")]
        assert len(doc.paragraphs) == 2

    def test_contains_true_for_live_element(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        assert para in doc.paragraphs

    def test_contains_false_for_spec(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        assert Paragraph("x") not in doc.paragraphs

    def test_reversed_order(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        texts = [p.text for p in reversed(doc.paragraphs)]
        assert texts == ["B", "A"]


# ---------------------------------------------------------------------------
# Document.save
# ---------------------------------------------------------------------------

class TestDocumentSave:
    def test_save_stores_path(self):
        doc, mock = _make_doc()
        doc.save("/tmp/out.docx")
        assert doc.path == "/tmp/out.docx"

    def test_save_without_path_raises(self):
        doc, _ = _make_doc()
        with pytest.raises(ValueError, match="path"):
            doc.save()

    def test_save_after_close_raises(self):
        from fastdocx.errors import DocumentClosedError
        doc, _ = _make_doc()
        doc.close()
        with pytest.raises(DocumentClosedError):
            doc.save("/tmp/out.docx")


# ---------------------------------------------------------------------------
# Proxy lifecycle — CONSTRUCTION → LIVE transition (_attach)
# ---------------------------------------------------------------------------

class TestProxyLifecycle:
    def test_proxy_is_construction_before_append(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.paragraph import Paragraph
        para = Paragraph("hello")
        assert para.state is ProxyState.CONSTRUCTION

    def test_proxy_is_live_after_append(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("hello")
        doc.paragraphs.append(para)
        assert para.state is ProxyState.LIVE

    def test_append_returns_same_object(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("hello")
        returned = doc.paragraphs._append_one(para)
        assert returned is para

    def test_post_append_mutation_reflects_in_document(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("original")
        doc.paragraphs.append(para)
        para.text = "mutated"
        assert doc.paragraphs[0].text == "mutated"

    def test_double_append_raises(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("hello")
        doc.paragraphs.append(para)
        with pytest.raises(ValueError, match="already in a document"):
            doc.paragraphs.append(para)

    def test_append_live_proxy_to_different_doc_raises_ownership_error(self):
        from fastdocx.errors import OwnershipError
        from fastdocx.paragraph import Paragraph
        doc1, _ = _make_doc()
        doc2, _ = _make_doc()
        para = Paragraph("hello")
        doc1.paragraphs.append(para)
        with pytest.raises(OwnershipError):
            doc2.paragraphs.append(para)

    def test_extend_transitions_all_to_live(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        p1, p2 = Paragraph("A"), Paragraph("B")
        doc.paragraphs.extend([p1, p2])
        assert p1.state is ProxyState.LIVE
        assert p2.state is ProxyState.LIVE

    def test_iadd_transitions_all_to_live(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        p1, p2 = Paragraph("A"), Paragraph("B")
        doc.paragraphs += [p1, p2]
        assert p1.state is ProxyState.LIVE
        assert p2.state is ProxyState.LIVE

    def test_snapshot_can_be_appended_and_becomes_live(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("original"))
        snap = doc.paragraphs[0].copy()
        assert snap.state is ProxyState.SNAPSHOT
        doc2, _ = _make_doc()
        doc2.paragraphs.append(snap)
        assert snap.state is ProxyState.LIVE

    def test_copy_of_spec_appended_independently(self):
        """copy() creates a fresh CONSTRUCTION proxy that can be appended separately."""
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        template = Paragraph("template")
        doc.paragraphs.append(template.copy())
        doc.paragraphs.append(template.copy())
        assert len(doc.paragraphs) == 2
        assert template.is_construction  # original spec untouched

    def test_table_transitions_to_live_after_append(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.table import Table
        doc, _ = _make_doc()
        tbl = Table(rows=2, cols=2)
        doc.tables.append(tbl)
        assert tbl.state is ProxyState.LIVE

    def test_table_double_append_raises(self):
        from fastdocx.table import Table
        doc, _ = _make_doc()
        tbl = Table(rows=2, cols=2)
        doc.tables.append(tbl)
        with pytest.raises(ValueError, match="already in a document"):
            doc.tables.append(tbl)

    def test_closed_doc_raises_document_closed_not_stale(self):
        """Accessing a LIVE proxy after its doc closes raises DocumentClosedError, not StaleProxyError."""
        from fastdocx.errors import DocumentClosedError, StaleProxyError
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("bye")
        doc.paragraphs.append(para)
        doc.close()
        with pytest.raises(DocumentClosedError):
            _ = para.text
        # confirm it is NOT a stale error
        assert not para.is_stale

    def test_para_accessed_after_context_manager_raises_document_closed(self):
        """Paragraph appended inside a context manager; reference held outside raises DocumentClosedError."""
        from fastdocx.errors import DocumentClosedError
        from fastdocx.paragraph import Paragraph
        mock = MockHandle()
        with patch("fastdocx._native.handle.get_handle", return_value=mock):
            from fastdocx.document import Document
            para = Paragraph("inside")
            with Document() as doc:
                doc.paragraphs.append(para)
        with pytest.raises(DocumentClosedError):
            _ = para.text

    def test_run_transitions_to_live_after_append(self):
        from fastdocx._proxy.base import ProxyState
        from fastdocx.paragraph import Paragraph
        from fastdocx.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        run = Run("hello", bold=True)
        doc.paragraphs[0].runs.append(run)
        assert run.state is ProxyState.LIVE

    def test_post_append_run_mutation_reflects_in_document(self):
        from fastdocx.paragraph import Paragraph
        from fastdocx.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        run = Run("original")
        doc.paragraphs[0].runs.append(run)
        run.text = "mutated"
        assert doc.paragraphs[0].runs[0].text == "mutated"


# ---------------------------------------------------------------------------
# Collection edge cases
# ---------------------------------------------------------------------------

class TestCollectionEdgeCases:
    def test_getitem_negative_index(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        assert doc.paragraphs[-1].text == "B"
        assert doc.paragraphs[-2].text == "A"

    def test_getitem_out_of_range_raises(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with pytest.raises(IndexError):
            _ = doc.paragraphs[5]

    def test_clear_empties_collection(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        doc.paragraphs.clear()
        assert len(doc.paragraphs) == 0

    def test_index_returns_correct_position(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        para = doc.paragraphs[1]
        assert doc.paragraphs.index(para) == 1

    def test_index_raises_for_unknown_element(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        other = doc.paragraphs[0].copy()
        with pytest.raises(ValueError):
            doc.paragraphs.index(other)  # type: ignore

    def test_pop_with_explicit_index(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        doc.paragraphs.append(Paragraph("C"))
        popped = doc.paragraphs.pop(1)
        assert popped.text == "B"
        assert len(doc.paragraphs) == 2

    def test_pop_out_of_range_raises(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with pytest.raises(IndexError):
            doc.paragraphs.pop(5)

    def test_remove_construction_proxy_raises(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        spec = Paragraph("never appended")
        with pytest.raises(ValueError, match="not in a document"):
            doc.paragraphs.remove(spec)  # type: ignore

    def test_contains_false_after_remove(self):
        from fastdocx.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        assert para not in doc.paragraphs
