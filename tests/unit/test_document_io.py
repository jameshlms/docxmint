"""Tests for the IO / PathLike overloads on Document.open(), edit(), and save()."""
from __future__ import annotations

import io
import os
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from tests.unit.mock_handle import MockHandle


def _patch_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    return patch("fastdocx._native.handle.get_handle", return_value=mock), mock


# ---------------------------------------------------------------------------
# Document.open()
# ---------------------------------------------------------------------------

class TestOpenIO:
    def test_open_bytesio_is_open(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.open(io.BytesIO(b"fake")) as doc:
                assert doc.is_open

    def test_open_bytesio_path_is_none(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.open(io.BytesIO(b"fake")) as doc:
                assert doc.path is None

    def test_open_bytesio_temp_file_exists_while_open(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            doc = Document.open(io.BytesIO(b"fake"))
            assert doc._tmp_path is not None
            assert os.path.exists(doc._tmp_path)
            doc.close()

    def test_open_bytesio_temp_file_cleaned_up_on_close(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            doc = Document.open(io.BytesIO(b"fake"))
            tmp = doc._tmp_path
        doc.close()
        assert not os.path.exists(tmp)

    def test_open_bytesio_temp_file_cleaned_up_by_context_manager(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.open(io.BytesIO(b"fake")) as doc:
                tmp = doc._tmp_path
        assert not os.path.exists(tmp)

    def test_open_bytesio_reads_at_open_time(self):
        """Seeking or closing the source IO after open has no effect on the document."""
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            buf = io.BytesIO(b"fake")
            doc = Document.open(buf)
        buf.seek(0)
        buf.close()
        assert doc.is_open
        doc.close()

    def test_open_pathlib_sets_path(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            doc = Document.open(pathlib.Path("/tmp/report.docx"))
        assert doc.path == "/tmp/report.docx"
        assert doc._tmp_path is None
        doc.close()

    def test_open_pathlib_no_temp_file(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            doc = Document.open(pathlib.Path("/tmp/report.docx"))
        assert doc._tmp_path is None
        doc.close()

    def test_open_str_unchanged(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            doc = Document.open("/tmp/report.docx")
        assert doc.path == "/tmp/report.docx"
        doc.close()


# ---------------------------------------------------------------------------
# Document.save()
# ---------------------------------------------------------------------------

class TestSaveIO:
    def _make_doc(self, mock=None):
        ctx, mock = _patch_doc(mock)
        with ctx:
            from fastdocx.document import Document
            doc = Document()
        return doc, mock

    def test_save_bytesio_calls_write(self):
        doc, _ = self._make_doc()
        buf = MagicMock(spec=io.BytesIO)
        doc.save(buf)
        buf.write.assert_called_once()

    def test_save_bytesio_does_not_update_path(self):
        doc, _ = self._make_doc()
        doc.save("/tmp/initial.docx")
        doc.save(io.BytesIO())
        assert doc.path == "/tmp/initial.docx"

    def test_save_bytesio_temp_file_cleaned_up(self):
        """The intermediate temp file used to save to IO is removed afterwards."""
        doc, _ = self._make_doc()
        buf = io.BytesIO()
        created_tmps: list[str] = []

        real_mkstemp = __import__("tempfile").mkstemp

        def tracking_mkstemp(**kwargs):
            fd, path = real_mkstemp(**kwargs)
            created_tmps.append(path)
            return fd, path

        with patch("fastdocx.document.tempfile.mkstemp", side_effect=tracking_mkstemp):
            doc.save(buf)

        for path in created_tmps:
            assert not os.path.exists(path)

    def test_save_pathlib_updates_path(self):
        doc, _ = self._make_doc()
        doc.save(pathlib.Path("/tmp/out.docx"))
        assert doc.path == "/tmp/out.docx"

    def test_save_pathlib_stores_str(self):
        doc, _ = self._make_doc()
        doc.save(pathlib.Path("/tmp/out.docx"))
        assert isinstance(doc.path, str)


# ---------------------------------------------------------------------------
# Document.edit()
# ---------------------------------------------------------------------------

class TestEditIO:
    def test_edit_bytesio_path_is_none(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.edit(io.BytesIO(b"fake")) as doc:
                assert doc.path is None

    def test_edit_bytesio_writes_back_on_exit(self):
        ctx, mock = _patch_doc()
        buf = MagicMock(spec=io.RawIOBase)
        buf.read.return_value = b"fake"
        with ctx:
            from fastdocx.document import Document
            with Document.edit(buf):
                pass
        buf.write.assert_called_once()

    def test_edit_bytesio_temp_cleaned_up_on_exit(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.edit(io.BytesIO(b"fake")) as doc:
                tmp = doc._tmp_path
        assert tmp is not None
        assert not os.path.exists(tmp)

    def test_edit_pathlib_saves_on_exit(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.edit(pathlib.Path("/tmp/report.docx")) as doc:
                pass
        assert doc.path == "/tmp/report.docx"

    def test_edit_pathlib_no_temp_file(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.edit(pathlib.Path("/tmp/report.docx")) as doc:
                assert doc._tmp_path is None

    def test_edit_str_unchanged(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            with Document.edit("/tmp/report.docx") as doc:
                pass
        assert doc.path == "/tmp/report.docx"

    def test_edit_bytesio_io_edit_is_stored(self):
        ctx, mock = _patch_doc()
        buf = io.BytesIO(b"fake")
        with ctx:
            from fastdocx.document import Document
            doc = Document.edit(buf)
        assert doc._io_edit is buf
        doc.close()

    def test_edit_str_io_edit_is_none(self):
        ctx, mock = _patch_doc()
        with ctx:
            from fastdocx.document import Document
            doc = Document.edit("/tmp/report.docx")
        assert doc._io_edit is None
        doc.close()
