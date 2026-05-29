"""Unit tests for Hyperlink — inline hyperlink proxy."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.unit.mock_handle import MockHandle

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("navyfox._native.handle.get_handle", return_value=mock):
        from navyfox.document import Document
        doc = Document()
    return doc, mock


def _add_para(doc, mock):
    from navyfox.paragraph import Paragraph
    return doc.paragraphs._append_one(Paragraph())


# ---------------------------------------------------------------------------
# Construction state
# ---------------------------------------------------------------------------

class TestHyperlinkConstruction:
    def test_is_construction(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("click here", "https://example.com")
        assert link.is_construction

    def test_text_and_url_stored(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("click here", "https://example.com")
        assert link.text == "click here"
        assert link.url == "https://example.com"

    def test_empty_defaults(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink()
        assert link.text == ""
        assert link.url == ""

    def test_text_writable(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("old", "https://example.com")
        link.text = "new"
        assert link.text == "new"

    def test_url_writable(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("text", "https://old.com")
        link.url = "https://new.com"
        assert link.url == "https://new.com"

    def test_repr_construction(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("click", "https://example.com")
        r = repr(link)
        assert "Hyperlink" in r
        assert "click" in r
        assert "https://example.com" in r

    def test_bool_true_when_text(self):
        from navyfox.hyperlink import Hyperlink
        assert bool(Hyperlink("text", ""))

    def test_bool_true_when_url(self):
        from navyfox.hyperlink import Hyperlink
        assert bool(Hyperlink("", "https://example.com"))

    def test_bool_false_when_empty(self):
        from navyfox.hyperlink import Hyperlink
        assert not bool(Hyperlink())

    def test_str_returns_text(self):
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("display text", "https://example.com")
        assert str(link) == "display text"


# ---------------------------------------------------------------------------
# Appending to paragraph
# ---------------------------------------------------------------------------

class TestHyperlinkAppend:
    def test_append_via_hyperlinks_view(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        assert link.is_live

    def test_native_handle_created(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        native = link._getattr("_native")
        assert native is not None
        assert mock._types[native] == "hyperlink"

    def test_text_stored_in_native(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        native = link._getattr("_native")
        assert mock._handles[native]["text"] == "click"

    def test_url_stored_in_native(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        native = link._getattr("_native")
        assert mock._handles[native]["url"] == "https://example.com"

    def test_add_hyperlink_convenience(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = para.add_hyperlink("click", "https://example.com")
        assert isinstance(link, Hyperlink)
        assert link.is_live

    def test_add_hyperlink_raises_if_not_live(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("text")
        with pytest.raises(ValueError, match="not yet in a document"):
            para.add_hyperlink("click", "https://example.com")


# ---------------------------------------------------------------------------
# Live proxy reads and writes
# ---------------------------------------------------------------------------

class TestHyperlinkLiveProxy:
    def _make_live_link(self, text="click here", url="https://example.com"):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink(text, url)
        para.hyperlinks.append(link)
        return link, mock

    def test_text_reads_from_native(self):
        link, _ = self._make_live_link(text="hello")
        assert link.text == "hello"

    def test_url_reads_from_native(self):
        link, _ = self._make_live_link(url="https://example.com")
        assert link.url == "https://example.com"

    def test_text_writable_live(self):
        link, mock = self._make_live_link()
        link.text = "updated"
        native = link._getattr("_native")
        assert mock._handles[native]["text"] == "updated"

    def test_url_writable_live(self):
        link, mock = self._make_live_link()
        link.url = "https://updated.com"
        native = link._getattr("_native")
        assert mock._handles[native]["url"] == "https://updated.com"

    def test_repr_live(self):
        link, _ = self._make_live_link(text="click", url="https://example.com")
        r = repr(link)
        assert "Hyperlink" in r
        assert "click" in r


# ---------------------------------------------------------------------------
# para.hyperlinks — collection behaviour
# ---------------------------------------------------------------------------

class TestHyperlinksCollection:
    def test_count(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        para.hyperlinks.append(Hyperlink("a", "https://a.com"))
        para.hyperlinks.append(Hyperlink("b", "https://b.com"))
        assert len(para.hyperlinks) == 2

    def test_hyperlinks_only_contains_hyperlinks(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        para.hyperlinks.append(Hyperlink("a", "https://a.com"))
        items = list(para.hyperlinks)
        assert all(isinstance(i, Hyperlink) for i in items)

    def test_hyperlinks_rejects_run(self):
        from navyfox.run import Run
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        with pytest.raises(TypeError):
            para.hyperlinks.append(Run("text"))

    def test_runs_rejects_hyperlink(self):
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        with pytest.raises(TypeError):
            para.runs.append(Hyperlink("click", "https://example.com"))

    def test_hyperlinks_and_runs_independent_counts(self):
        from navyfox.hyperlink import Hyperlink
        from navyfox.run import Run
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        para.runs.append(Run("text"))
        para.hyperlinks.append(Hyperlink("link", "https://example.com"))
        assert len(para.runs) == 1
        assert len(para.hyperlinks) == 1

    def test_hyperlinks_empty_in_construction_state(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("text")
        assert len(para.hyperlinks) == 0

    def test_remove_marks_stale(self):
        from navyfox.errors import StaleProxyError
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        para.hyperlinks.remove(link)
        assert link.is_stale
        with pytest.raises(StaleProxyError):
            _ = link.text


# ---------------------------------------------------------------------------
# Snapshot / copy
# ---------------------------------------------------------------------------

class TestHyperlinkSnapshot:
    def test_snapshot_construction(self):
        from navyfox import snapshot
        from navyfox.hyperlink import Hyperlink
        link = Hyperlink("click", "https://example.com")
        snap = snapshot(link)
        assert snap.is_snapshot
        assert snap._getattr("_data")["text"] == "click"
        assert snap._getattr("_data")["url"] == "https://example.com"

    def test_snapshot_live(self):
        from navyfox import snapshot
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        snap = snapshot(link)
        assert snap.is_snapshot
        data = snap._getattr("_data")
        assert data["text"] == "click"
        assert data["url"] == "https://example.com"

    def test_snapshot_can_be_appended_to_another_paragraph(self):
        from navyfox import snapshot
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para1 = _add_para(doc, mock)
        para2 = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para1.hyperlinks.append(link)
        snap = snapshot(link)
        para2.hyperlinks.append(snap)
        assert snap.is_live
        assert len(para2.hyperlinks) == 1


# ---------------------------------------------------------------------------
# Stale / closed errors
# ---------------------------------------------------------------------------

class TestHyperlinkErrors:
    def test_closed_raises_document_closed_error(self):
        from navyfox.errors import DocumentClosedError
        from navyfox.hyperlink import Hyperlink
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        link = Hyperlink("click", "https://example.com")
        para.hyperlinks.append(link)
        doc.close()
        with pytest.raises(DocumentClosedError):
            _ = link.text
