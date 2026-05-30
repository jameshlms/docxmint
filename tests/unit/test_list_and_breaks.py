"""Tests for list items (bullet/numbered) and paragraph line breaks."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from navyfox.document import Document
from navyfox.paragraph import Paragraph
from tests.unit.mock_handle import MockHandle


def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("navyfox._native.handle.get_handle", return_value=mock):
        from navyfox.document import Document
        doc = Document()
    return doc, mock


@pytest.fixture()
def doc():
    d, _ = _make_doc()
    return d


@pytest.fixture()
def doc_and_mock():
    return _make_doc()


# ------------------------------------------------------------------
# Line breaks
# ------------------------------------------------------------------

class TestLineBreaks:
    def test_add_break_returns_self(self, doc):
        para = doc.add_paragraph("Hello")
        assert para.add_break() is para

    def test_break_appended_as_child(self, doc_and_mock):
        doc, mock = doc_and_mock
        para = doc.add_paragraph("Hello")
        native = para._native
        before = mock.get_count(native, "body")
        para.add_break()
        assert mock.get_count(native, "body") == before + 1

    def test_text_contains_newline_after_break(self, doc):
        para = doc.add_paragraph("Hello")
        para.add_run("World")
        para.add_break()
        para.add_run("!")
        assert "\n" in para.text

    def test_add_break_raises_in_construction_state(self):
        para = Paragraph("text")
        with pytest.raises(ValueError, match="not yet in a document"):
            para.add_break()

    def test_chaining(self, doc):
        para = doc.add_paragraph("A")
        result = para.add_break().add_break()
        assert result is para


# ------------------------------------------------------------------
# Bullet lists — construction state
# ------------------------------------------------------------------

class TestBulletConstruction:
    def test_list_style_in_data(self):
        para = Paragraph("item", list_style="bullet")
        assert para._data["list_style"] == "bullet"

    def test_list_level_in_data(self):
        para = Paragraph("item", list_style="bullet", list_level=2)
        assert para._data["list_level"] == 2

    def test_numbered_style_in_data(self):
        para = Paragraph("item", list_style="number")
        assert para._data["list_style"] == "number"

    def test_default_level_zero(self):
        para = Paragraph("item", list_style="bullet")
        assert para._data.get("list_level", 0) == 0

    def test_list_style_property_reads_data(self):
        para = Paragraph("item", list_style="bullet")
        assert para.list_style == "bullet"

    def test_list_level_property_reads_data(self):
        para = Paragraph("item", list_style="bullet", list_level=3)
        assert para.list_level == 3


# ------------------------------------------------------------------
# Bullet lists — live state via add_bullet / add_numbered
# ------------------------------------------------------------------

class TestAddBullet:
    def test_add_bullet_returns_paragraph(self, doc: Document):
        para = doc.add_bullet("item")
        assert isinstance(para, Paragraph)

    def test_add_bullet_text(self, doc: Document):
        para = doc.add_bullet("hello")
        assert para.text == "hello"

    def test_add_bullet_list_style_live(self, doc: Document):
        para = doc.add_bullet("item")
        assert para.list_style == "bullet"

    def test_add_bullet_default_level(self, doc: Document):
        para = doc.add_bullet("item")
        assert para.list_level == 0

    def test_add_bullet_custom_level(self, doc: Document):
        para = doc.add_bullet("nested", level=2)
        assert para.list_level == 2

    def test_add_numbered_returns_paragraph(self, doc: Document):
        para = doc.add_numbered("step")
        assert isinstance(para, Paragraph)

    def test_add_numbered_list_style_live(self, doc: Document):
        para = doc.add_numbered("step")
        assert para.list_style == "number"

    def test_add_numbered_custom_level(self, doc: Document):
        para = doc.add_numbered("sub-step", level=1)
        assert para.list_level == 1

    def test_multiple_bullets_all_in_paragraphs(self, doc: Document):
        doc.add_bullet("a")
        doc.add_bullet("b")
        doc.add_bullet("c")
        assert len(doc.paragraphs) == 3

    def test_mixed_bullets_and_numbered(self, doc: Document):
        b = doc.add_bullet("item")
        n = doc.add_numbered("step")
        assert b.list_style == "bullet"
        assert n.list_style == "number"


# ------------------------------------------------------------------
# list_style / list_level property setters in live state
# ------------------------------------------------------------------

class TestListPropertySetters:
    def test_set_list_style_live(self, doc: Document):
        para = doc.add_paragraph("item")
        para.list_style = "bullet"
        assert para.list_style == "bullet"

    def test_set_list_level_live(self, doc: Document):
        para = doc.add_bullet("item")
        para.list_level = 4
        assert para.list_level == 4

    def test_set_list_style_construction(self):
        para = Paragraph("item")
        para.list_style = "number"
        assert para.list_style == "number"

    def test_set_list_level_construction(self):
        para = Paragraph("item")
        para.list_level = 5
        assert para.list_level == 5
