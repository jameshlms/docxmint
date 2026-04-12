from __future__ import annotations

import contextlib
import os
import tempfile
from typing import IO

from fastdocx._native.loader import get_lib
from fastdocx.enums import Alignment
from fastdocx.errors import NativeRuntimeError
from fastdocx.paragraph import Paragraph, ParagraphView
from fastdocx.table import Table


class Document:
    """Top-level DOCX document object.

    Use as a context manager for automatic cleanup::

        with Document() as doc:
            doc.add_heading("My Report", level=1)
            doc.add_paragraph("Hello world", bold=True)
            table = doc.add_table(rows=2, cols=2)
            table[0, 0].text = "Name"
            doc.save("output.docx")

    Or manage the lifecycle explicitly::

        doc = Document()
        doc.add_paragraph("Hello")
        doc.save("output.docx")
        doc.close()

    Pass a file path or file-like object to open an existing document::

        doc = Document("existing.docx")
        with open("existing.docx", "rb") as f:
            doc = Document(f)
    """

    def __init__(self, source: str | os.PathLike[str] | IO[bytes] | None = None) -> None:
        self._lib = get_lib()
        self._handle: int | None = None

        if source is None:
            handle = self._lib.create_document()

            if handle == 0:
                raise NativeRuntimeError("native create_document returned a null handle")

        elif isinstance(source, (str, os.PathLike)):
            encoded = os.fsencode(source)
            handle = self._lib.open_document(encoded, len(encoded))

            if handle == 0:
                raise NativeRuntimeError(f"native open_document failed for path {str(source)!r}")

        elif hasattr(source, "read") and callable(source.read):
            data = source.read()

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                encoded = os.fsencode(tmp_path)
                handle = self._lib.open_document(encoded, len(encoded))

            finally:
                os.unlink(tmp_path)

            if handle == 0:
                raise NativeRuntimeError("native open_document failed for file-like source")

        else:
            raise TypeError(
                "source must be a file path, file-like object, or None, got "
                f"{type(source).__name__!r}"
            )

        self._handle = handle

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Free the native document handle. The document cannot be used after this."""
        if self._handle is not None:
            self._lib.free_document(self._handle)
            self._handle = None

    def __enter__(self) -> Document:
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()

    def _require_open(self) -> int:
        if self._handle is None:
            raise RuntimeError("Document is closed")
        return self._handle

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_paragraph(self, text: str = "", style: str | None = None) -> Paragraph:
        """Add a paragraph and return a :class:`~fastdocx.paragraph.Paragraph`.

        If *text* is provided a single run is added automatically. For multiple
        runs with different formatting, call
        :meth:`~fastdocx.paragraph.Paragraph.add_run` on the returned paragraph::

            p = doc.add_paragraph("Intro: ", style="Normal")
            p.add_run("bold part").bold = True
            p.add_run(" normal part")

        Args:
            text: Paragraph text (creates one implicit run). Pass ``""`` for
                an empty paragraph.
            style: An optional Word paragraph style identifier (e.g. ``"Normal"``).
        """
        encoded_style = style.encode("utf-8") if style else b""
        handle = self._lib.add_paragraph(
            self._require_open(),
            encoded_style,
            len(encoded_style),
        )
        if handle == 0:
            raise NativeRuntimeError("native add_paragraph failed")
        para = Paragraph._create(handle=handle, lib=self._lib)
        if text:
            para.add_run(text)
        return para

    def add_heading(self, text: str, level: int = 1) -> Paragraph:
        """Add a heading paragraph and return a :class:`~fastdocx.paragraph.Paragraph`.

        Args:
            text: The heading text.
            level: Heading level 1-6 (default 1).
        """
        if not 1 <= level <= 6:
            raise ValueError(f"Heading level must be 1–6, got {level!r}")

        encoded_text = text.encode("utf-8")
        handle = self._lib.add_heading(self._require_open(), encoded_text, len(encoded_text), level)
        if handle == 0:
            raise NativeRuntimeError("native add_heading failed")
        return Paragraph._create(handle=handle, lib=self._lib)

    def register_paragraph_style(
        self,
        style_id: str,
        *,
        based_on: str | None = None,
        bold: bool = False,
        italic: bool = False,
        font_size: int | None = None,
        color: str | None = None,
        alignment: Alignment | None = None,
        space_before: int | None = None,
        space_after: int | None = None,
    ) -> str:
        """Register a custom paragraph style and return its style ID.

        Once registered, pass the returned string as the ``style`` argument to
        :meth:`add_paragraph`.

        Args:
            style_id: Unique style identifier (e.g. ``"MyStyle"``).
            based_on: Style ID to inherit from (e.g. ``"Normal"``).
            bold: Whether the style renders text bold.
            italic: Whether the style renders text italic.
            font_size: Font size in points.
            color: RGB hex color string (e.g. ``"FF0000"``).
            alignment: An :class:`~fastdocx.enums.Alignment` member.
            space_before: Space before paragraph in twips.
            space_after: Space after paragraph in twips.
        """
        if alignment is not None and not isinstance(alignment, Alignment):
            raise ValueError(f"alignment must be an Alignment member, got {alignment!r}")

        rc = self._lib.register_paragraph_style(
            self._require_open(),
            style_id,
            based_on,
            bold,
            italic,
            font_size * 2 if font_size is not None else 0,
            color,
            alignment.value if alignment else 0,
            space_before or 0,
            space_after or 0,
        )
        if rc != 0:
            raise NativeRuntimeError(
                f"native register_paragraph_style failed for style {style_id!r}"
            )
        return style_id

    def add_table(
        self,
        rows: int,
        cols: int,
        data: list[list[str]] | None = None,
        *,
        strict: bool = True,
    ) -> Table:
        """Add a table and return a :class:`~fastdocx.table.Table`.

        Args:
            rows: Number of rows.
            cols: Number of columns.
            data: Optional 2-D list of strings used to pre-populate cells.
            strict: If ``True`` (default), raises ``ValueError`` when the number
                of rows in ``data`` does not match ``rows``. If ``False``,
                missing rows are filled with blank cells and extra rows are
                truncated.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError(
                f"rows and cols must be positive integers, got rows={rows!r}, cols={cols!r}"
            )

        if data is not None:
            if len(data) != rows:
                if bool(strict):
                    raise ValueError(f"data has {len(data)} rows but rows={rows!r}")
                data = (data + [[]] * rows)[:rows]
            data = [
                row + [""] * (cols - len(row)) if len(row) < cols else row[:cols] for row in data
            ]

        if data is not None:
            handle = self._lib.add_table_with_data(self._require_open(), data, rows, cols)
            if handle == 0:
                raise NativeRuntimeError("native add_table_with_data failed")
        else:
            handle = self._lib.add_table(self._require_open(), rows, cols)
            if handle == 0:
                raise NativeRuntimeError("native add_table failed")

        return Table(handle=handle, rows=rows, cols=cols, lib=self._lib)

    def remove_paragraph(self, index: int) -> None:
        """Remove the paragraph at *index* from the document body.

        Uses the same zero-based index as :attr:`paragraphs`::

            doc.add_paragraph("Draft line")
            doc.add_paragraph("Keep this")
            doc.remove_paragraph(0)   # removes "Draft line"

        Args:
            index: Zero-based position of the paragraph to remove.

        Raises:
            IndexError: If *index* is out of range.
        """
        handle = self._require_open()
        rc = self._lib.remove_paragraph(handle, index)
        if rc == -2:
            raise IndexError(f"paragraph index {index} is out of range")
        if rc != 0:
            raise NativeRuntimeError(f"native remove_paragraph failed (rc={rc})")

    @property
    def paragraphs(self) -> list[ParagraphView]:
        """Return a snapshot of every paragraph in the document body.

        Each entry is a :class:`~fastdocx.paragraph.ParagraphView` with
        ``text`` and ``style`` attributes, mirroring the ``python-docx``
        interface::

            for para in doc.paragraphs:
                print(para.text, para.style)
        """
        handle = self._require_open()
        count = self._lib.get_paragraph_count(handle)
        if count < 0:
            raise NativeRuntimeError("native get_paragraph_count failed")
        return [
            ParagraphView(
                text=self._lib.get_paragraph_text(handle, i),
                style=self._lib.get_paragraph_style(handle, i),
            )
            for i in range(count)
        ]

    def save(self, path: str | os.PathLike[str]) -> None:
        """Save the document to *path*.

        The document remains open after saving and can continue to be modified.
        Call :meth:`close` (or use a ``with`` block) to release the native handle.

        Args:
            path: Destination file path (will be created or overwritten).
        """
        encoded_path = os.fsencode(path)
        rc = self._lib.save_document(self._require_open(), encoded_path, len(encoded_path))
        if rc != 0:
            raise NativeRuntimeError(f"native save_document failed for path {path!r}")
