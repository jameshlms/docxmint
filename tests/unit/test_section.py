"""Unit tests for Section — page layout proxy."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.unit.mock_handle import MockHandle


def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("navyfox._native.handle.get_handle", return_value=mock):
        from navyfox.document import Document
        doc = Document()
    return doc, mock


def _add_section(doc, mock):
    from navyfox.section import Section
    return doc.sections._append_one(Section())


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestSectionDefaults:
    def test_margin_top_default(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_top == 1.0

    def test_margin_bottom_default(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_bottom == 1.0

    def test_margin_left_default(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_left == 1.25

    def test_margin_right_default(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_right == 1.25

    def test_margin_header_default(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_header == 0.5

    def test_margin_footer_default(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_footer == 0.5


# ---------------------------------------------------------------------------
# Construction-state reads and writes
# ---------------------------------------------------------------------------

class TestSectionConstruction:
    def test_margins_readable_in_construction_state(self):
        from navyfox.section import Section
        s = Section()
        assert s.margin_top == 1.0
        assert s.margin_left == 1.25

    def test_margins_writable_in_construction_state(self):
        from navyfox.section import Section
        s = Section()
        s.margin_top = 0.75
        s.margin_bottom = 0.75
        s.margin_left = 0.5
        s.margin_right = 0.5
        assert s.margin_top == 0.75
        assert s.margin_bottom == 0.75
        assert s.margin_left == 0.5
        assert s.margin_right == 0.5

    def test_margin_header_footer_writable(self):
        from navyfox.section import Section
        s = Section()
        s.margin_header = 0.3
        s.margin_footer = 0.4
        assert s.margin_header == 0.3
        assert s.margin_footer == 0.4


# ---------------------------------------------------------------------------
# Live proxy — reads from native
# ---------------------------------------------------------------------------

class TestSectionLive:
    def _make_live_section(self):
        doc, mock = _make_doc()
        sec = _add_section(doc, mock)
        return sec, mock

    def test_margin_top_round_trips(self):
        sec, mock = self._make_live_section()
        sec.margin_top = 0.5
        assert abs(sec.margin_top - 0.5) < 1e-9

    def test_margin_bottom_round_trips(self):
        sec, mock = self._make_live_section()
        sec.margin_bottom = 0.75
        assert abs(sec.margin_bottom - 0.75) < 1e-9

    def test_margin_left_round_trips(self):
        sec, mock = self._make_live_section()
        sec.margin_left = 0.6
        assert abs(sec.margin_left - 0.6) < 1e-9

    def test_margin_right_round_trips(self):
        sec, mock = self._make_live_section()
        sec.margin_right = 0.6
        assert abs(sec.margin_right - 0.6) < 1e-9

    def test_margin_header_round_trips(self):
        sec, mock = self._make_live_section()
        sec.margin_header = 0.3
        assert abs(sec.margin_header - 0.3) < 1e-9

    def test_margin_footer_round_trips(self):
        sec, mock = self._make_live_section()
        sec.margin_footer = 0.4
        assert abs(sec.margin_footer - 0.4) < 1e-9

    def test_margins_stored_in_mock_handle(self):
        sec, mock = self._make_live_section()
        sec.margin_top = 0.5
        sec.margin_left = 0.75
        native = sec._native
        assert mock._handles[native]["margin_top"] == 0.5
        assert mock._handles[native]["margin_left"] == 0.75

    def test_all_four_margins_independent(self):
        sec, mock = self._make_live_section()
        sec.margin_top = 0.5
        sec.margin_bottom = 0.6
        sec.margin_left = 0.7
        sec.margin_right = 0.8
        assert abs(sec.margin_top - 0.5) < 1e-9
        assert abs(sec.margin_bottom - 0.6) < 1e-9
        assert abs(sec.margin_left - 0.7) < 1e-9
        assert abs(sec.margin_right - 0.8) < 1e-9


# ---------------------------------------------------------------------------
# _copy_data includes margins
# ---------------------------------------------------------------------------

class TestSectionCopyData:
    def test_copy_data_includes_margins_construction(self):
        from navyfox.section import Section
        s = Section()
        s.margin_top = 0.5
        s.margin_left = 0.75
        data = s._copy_data()
        assert data["margin_top"] == 0.5
        assert data["margin_left"] == 0.75

    def test_copy_data_includes_margins_live(self):
        doc, mock = _make_doc()
        sec = _add_section(doc, mock)
        sec.margin_top = 0.5
        sec.margin_bottom = 0.6
        data = sec._copy_data()
        assert abs(data["margin_top"] - 0.5) < 1e-9
        assert abs(data["margin_bottom"] - 0.6) < 1e-9

    def test_copy_data_all_margin_keys_present(self):
        from navyfox.section import Section
        s = Section()
        data = s._copy_data()
        for key in ("margin_top", "margin_bottom", "margin_left", "margin_right",
                    "margin_header", "margin_footer"):
            assert key in data


# ---------------------------------------------------------------------------
# doc.margins shorthand
# ---------------------------------------------------------------------------

class TestDocMargins:
    def _make_doc_with_section(self):
        doc, mock = _make_doc()
        _add_section(doc, mock)
        return doc, mock

    def test_getter_returns_page_margins(self):
        from navyfox.formats import PageMargins
        doc, mock = self._make_doc_with_section()
        assert isinstance(doc.margins, PageMargins)

    def test_getter_reflects_section_values(self):
        doc, mock = self._make_doc_with_section()
        doc.sections[0].margin_top = 0.5
        assert abs(doc.margins.top - 0.5) < 1e-9

    def test_getter_no_sections_returns_defaults(self):
        from navyfox.formats import PageMargins
        doc, mock = _make_doc()
        m = doc.margins
        assert m == PageMargins()

    def test_set_float_applies_to_all_sides(self):
        doc, mock = self._make_doc_with_section()
        doc.margins = 0.75
        m = doc.margins
        assert abs(m.top - 0.75) < 1e-9
        assert abs(m.bottom - 0.75) < 1e-9
        assert abs(m.left - 0.75) < 1e-9
        assert abs(m.right - 0.75) < 1e-9

    def test_set_2tuple_vertical_horizontal(self):
        doc, mock = self._make_doc_with_section()
        doc.margins = (0.5, 1.0)
        m = doc.margins
        assert abs(m.top - 0.5) < 1e-9
        assert abs(m.bottom - 0.5) < 1e-9
        assert abs(m.left - 1.0) < 1e-9
        assert abs(m.right - 1.0) < 1e-9

    def test_set_4tuple(self):
        doc, mock = self._make_doc_with_section()
        doc.margins = (0.5, 0.6, 0.7, 0.8)
        m = doc.margins
        assert abs(m.top - 0.5) < 1e-9
        assert abs(m.bottom - 0.6) < 1e-9
        assert abs(m.left - 0.7) < 1e-9
        assert abs(m.right - 0.8) < 1e-9

    def test_set_page_margins_object(self):
        from navyfox.formats import PageMargins
        doc, mock = self._make_doc_with_section()
        doc.margins = PageMargins(top=0.5, bottom=0.5, left=0.75, right=0.75)
        m = doc.margins
        assert abs(m.top - 0.5) < 1e-9
        assert abs(m.left - 0.75) < 1e-9

    def test_set_applies_to_all_sections(self):
        doc, mock = self._make_doc_with_section()
        _add_section(doc, mock)
        doc.margins = 0.5
        for sec in doc.sections:
            assert abs(sec.margin_top - 0.5) < 1e-9

    def test_set_also_applies_header_footer_from_page_margins(self):
        from navyfox.formats import PageMargins
        doc, mock = self._make_doc_with_section()
        doc.margins = PageMargins(header=0.3, footer=0.4)
        sec = doc.sections[0]
        assert abs(sec.margin_header - 0.3) < 1e-9
        assert abs(sec.margin_footer - 0.4) < 1e-9

    def test_invalid_tuple_length_raises(self):
        doc, mock = self._make_doc_with_section()
        with pytest.raises(ValueError):
            doc.margins = (0.5, 0.5, 0.5)  # type: ignore[assignment]

    def test_invalid_type_raises(self):
        doc, mock = self._make_doc_with_section()
        with pytest.raises(TypeError):
            doc.margins = "0.75"  # type: ignore[assignment]
