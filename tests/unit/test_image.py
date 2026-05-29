"""Unit tests for Image — run-level inline image proxy."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.unit.mock_handle import MockHandle

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 56  # minimal fake PNG header


def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("docxmint._native.handle.get_handle", return_value=mock):
        from docxmint.document import Document
        doc = Document()
    return doc, mock


def _add_para(doc, mock):
    from docxmint.paragraph import Paragraph
    view = doc.paragraphs
    return view._append_one(Paragraph())


# ---------------------------------------------------------------------------
# Construction state
# ---------------------------------------------------------------------------

class TestImageConstruction:
    def test_from_bytes(self):
        from docxmint.image import Image
        img = Image(data=_PNG_BYTES, content_type="image/png", width=3.0, height=2.0)
        assert img.is_construction

    def test_from_path(self, tmp_path):
        from docxmint.image import Image
        p = tmp_path / "photo.png"
        p.write_bytes(_PNG_BYTES)
        img = Image(str(p), width=2.0, height=1.5)
        assert img.is_construction
        data = img._getattr("_data")
        assert data["_image_data"] == _PNG_BYTES
        assert data["_content_type"] == "image/png"

    def test_content_type_inferred_from_extension(self, tmp_path):
        from docxmint.image import Image
        p = tmp_path / "photo.jpeg"
        p.write_bytes(_PNG_BYTES)
        img = Image(str(p))
        assert img._getattr("_data")["_content_type"] == "image/jpeg"

    def test_explicit_content_type_overrides_extension(self, tmp_path):
        from docxmint.image import Image
        p = tmp_path / "photo.png"
        p.write_bytes(_PNG_BYTES)
        img = Image(str(p), content_type="image/tiff")
        assert img._getattr("_data")["_content_type"] == "image/tiff"

    def test_raises_if_both_src_and_data(self, tmp_path):
        from docxmint.image import Image
        p = tmp_path / "photo.png"
        p.write_bytes(_PNG_BYTES)
        with pytest.raises(ValueError, match="not both"):
            Image(str(p), data=_PNG_BYTES)

    def test_raises_if_neither_src_nor_data(self):
        from docxmint.image import Image
        with pytest.raises(ValueError):
            Image()

    def test_alt_text_stored(self):
        from docxmint.image import Image
        img = Image(data=_PNG_BYTES, alt_text="Company logo")
        assert img._getattr("_data")["alt_text"] == "Company logo"

    def test_repr_construction(self):
        from docxmint.image import Image
        img = Image(data=_PNG_BYTES, content_type="image/png", width=3.0, height=2.0)
        r = repr(img)
        assert "Image" in r
        assert "image/png" in r


# ---------------------------------------------------------------------------
# Appending to paragraph
# ---------------------------------------------------------------------------

class TestImageAppend:
    def test_append_to_para_images(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", width=2.0, height=1.5)
        para.images.append(img)
        assert img.is_live

    def test_native_handle_created(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", width=2.0, height=1.5)
        para.images.append(img)
        native = img._getattr("_native")
        assert native is not None
        assert mock._types[native] == "image"

    def test_dimensions_stored_as_emu(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", width=2.0, height=1.5)
        para.images.append(img)
        native = img._getattr("_native")
        assert mock._handles[native]["width_emu"] == int(2.0 * 914400)
        assert mock._handles[native]["height_emu"] == int(1.5 * 914400)

    def test_image_data_stored(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png")
        para.images.append(img)
        native = img._getattr("_native")
        assert mock._handles[native]["_image_data"] == _PNG_BYTES

    def test_content_type_stored(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png")
        para.images.append(img)
        native = img._getattr("_native")
        assert mock._handles[native]["content_type"] == "image/png"

    def test_alt_text_set_via_set_str(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", alt_text="Logo")
        para.images.append(img)
        native = img._getattr("_native")
        assert mock._handles[native]["alt_text"] == "Logo"

    def test_add_image_convenience(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = para.add_image(data=_PNG_BYTES, content_type="image/png", width=1.0)
        assert isinstance(img, Image)
        assert img.is_live


# ---------------------------------------------------------------------------
# Live proxy reads
# ---------------------------------------------------------------------------

class TestImageLiveProxy:
    def _make_live_image(self, width=2.0, height=1.5):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", width=width, height=height, alt_text="test")
        para.images.append(img)
        return img, mock

    def test_width_reads_from_native(self):
        img, _ = self._make_live_image(width=2.0)
        assert abs(img.width - 2.0) < 1e-6

    def test_height_reads_from_native(self):
        img, _ = self._make_live_image(height=1.5)
        assert abs(img.height - 1.5) < 1e-6

    def test_alt_text_reads_from_native(self):
        img, _ = self._make_live_image()
        assert img.alt_text == "test"

    def test_alt_text_writable(self):
        img, mock = self._make_live_image()
        img.alt_text = "Updated"
        native = img._getattr("_native")
        assert mock._handles[native]["alt_text"] == "Updated"

    def test_repr_live(self):
        img, _ = self._make_live_image(width=2.0, height=1.5)
        r = repr(img)
        assert "Image" in r
        assert "2.0" in r


# ---------------------------------------------------------------------------
# para.runs vs para.images — strict separation
# ---------------------------------------------------------------------------

class TestRunsImagesAreStrict:
    def test_runs_only_contains_text_runs(self):
        from docxmint.run import Run
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        para.runs.append(Run("hello"))
        para.runs.append(Run("world"))
        items = list(para.runs)
        assert all(isinstance(r, Run) for r in items)
        assert len(items) == 2

    def test_images_only_contains_image_elements(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        para.images.append(Image(data=_PNG_BYTES, content_type="image/png"))
        para.images.append(Image(data=_PNG_BYTES, content_type="image/png"))
        items = list(para.images)
        assert all(isinstance(i, Image) for i in items)
        assert len(items) == 2

    def test_runs_rejects_image_element(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        with pytest.raises(TypeError):
            para.runs.append(Image(data=_PNG_BYTES, content_type="image/png"))

    def test_images_rejects_text_run(self):
        from docxmint.run import Run
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        with pytest.raises(TypeError):
            para.images.append(Run("hello"))

    def test_runs_and_images_are_independent_counts(self):
        from docxmint.image import Image
        from docxmint.run import Run
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        para.runs.append(Run("text"))
        para.images.append(Image(data=_PNG_BYTES, content_type="image/png"))
        assert len(para.runs) == 1
        assert len(para.images) == 1


# ---------------------------------------------------------------------------
# Snapshot / copy
# ---------------------------------------------------------------------------

class TestImageSnapshot:
    def test_snapshot_construction_state(self):
        from docxmint import snapshot
        from docxmint.image import Image
        img = Image(data=_PNG_BYTES, content_type="image/png", width=2.0, height=1.5)
        snap = snapshot(img)
        assert snap.is_snapshot
        data = snap._getattr("_data")
        assert data["_image_data"] == _PNG_BYTES
        assert data["_content_type"] == "image/png"

    def test_snapshot_live_proxy(self):
        from docxmint import snapshot
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", width=2.0, height=1.5)
        para.images.append(img)
        snap = snapshot(img)
        assert snap.is_snapshot
        data = snap._getattr("_data")
        assert data["_image_data"] == _PNG_BYTES

    def test_snapshot_can_be_appended_to_another_paragraph(self):
        from docxmint import snapshot
        from docxmint.image import Image
        doc, mock = _make_doc()
        para1 = _add_para(doc, mock)
        para2 = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png", width=2.0, height=1.5)
        para1.images.append(img)
        snap = snapshot(img)
        para2.images.append(snap)
        assert snap.is_live
        assert len(para2.images) == 1


# ---------------------------------------------------------------------------
# Stale / closed errors
# ---------------------------------------------------------------------------

class TestImageErrors:
    def test_stale_after_remove(self):
        from docxmint.errors import StaleProxyError
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png")
        para.images.append(img)
        para.images.remove(img)
        assert img.is_stale
        with pytest.raises(StaleProxyError):
            _ = img.width

    def test_closed_raises_document_closed_error(self):
        from docxmint.errors import DocumentClosedError
        from docxmint.image import Image
        doc, mock = _make_doc()
        para = _add_para(doc, mock)
        img = Image(data=_PNG_BYTES, content_type="image/png")
        para.images.append(img)
        doc.close()
        with pytest.raises(DocumentClosedError):
            _ = img.width


# ---------------------------------------------------------------------------
# doc.add_image — standalone paragraph shortcut
# ---------------------------------------------------------------------------

class TestDocAddImage:
    def test_returns_image_proxy(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        img = doc.add_image(data=_PNG_BYTES, content_type="image/png")
        assert isinstance(img, Image)
        assert img.is_live

    def test_creates_new_paragraph(self):
        doc, mock = _make_doc()
        doc.add_image(data=_PNG_BYTES, content_type="image/png")
        assert len(doc.paragraphs) == 1

    def test_image_is_inside_new_paragraph(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        doc.add_image(data=_PNG_BYTES, content_type="image/png")
        para = doc.paragraphs[0]
        assert len(para.images) == 1
        assert isinstance(para.images[0], Image)

    def test_width_and_height_passed_through(self):
        doc, mock = _make_doc()
        img = doc.add_image(data=_PNG_BYTES, content_type="image/png", width=4.0, height=3.0)
        assert abs(img.width - 4.0) < 1e-6
        assert abs(img.height - 3.0) < 1e-6

    def test_alt_text_passed_through(self):
        doc, mock = _make_doc()
        img = doc.add_image(data=_PNG_BYTES, content_type="image/png", alt_text="Banner")
        assert img.alt_text == "Banner"

    def test_from_path(self, tmp_path):
        from docxmint.image import Image
        p = tmp_path / "photo.png"
        p.write_bytes(_PNG_BYTES)
        doc, mock = _make_doc()
        img = doc.add_image(str(p), width=2.0)
        assert isinstance(img, Image)
        assert img.is_live

    def test_each_call_creates_separate_paragraph(self):
        doc, mock = _make_doc()
        doc.add_image(data=_PNG_BYTES, content_type="image/png")
        doc.add_image(data=_PNG_BYTES, content_type="image/png")
        assert len(doc.paragraphs) == 2

    def test_paragraph_contains_only_the_image(self):
        from docxmint.image import Image
        doc, mock = _make_doc()
        doc.add_image(data=_PNG_BYTES, content_type="image/png")
        para = doc.paragraphs[0]
        assert len(para.runs) == 0
        assert len(para.images) == 1
        assert isinstance(para.images[0], Image)
