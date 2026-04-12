from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastdocx.run import Run

if TYPE_CHECKING:
    from fastdocx._native.bindings import NativeLib

_SENTINEL = object()


@dataclass(frozen=True)
class ParagraphView:
    """Read-only view of a paragraph as it exists in the document.

    Returned by :attr:`Document.paragraphs`.  Mirrors the interface of
    ``python-docx``'s ``Paragraph`` for easy migration::

        for para in doc.paragraphs:
            print(para.text, para.style)
    """

    text: str
    """Plain text content (all runs concatenated, no formatting)."""

    style: str
    """Paragraph style ID (e.g. ``"Heading1"``, ``"Normal"``), or ``""`` if none."""


class Paragraph:
    """Represents a paragraph element in a DOCX document.

    Instances are created by :meth:`Document.add_paragraph` and
    :meth:`Document.add_heading`; they cannot be constructed directly.

    Use :meth:`add_run` to append runs of text with independent formatting::

        p = doc.add_paragraph("Intro: ", style="Normal")
        p.add_run("bold part").bold = True
        p.add_run(" normal part")
    """

    def __init__(self, *, handle: int, lib: NativeLib, _guard: object = None) -> None:
        if _guard is not _SENTINEL:
            raise TypeError(
                "Paragraph cannot be instantiated directly — use Document.add_paragraph() "
                "or Document.add_heading()"
            )
        self._handle = handle
        self._lib = lib
        self._runs: list[Run] = []

    @classmethod
    def _create(cls, handle: int, lib: NativeLib) -> Paragraph:
        return cls(handle=handle, lib=lib, _guard=_SENTINEL)

    @property
    def handle(self) -> int:
        return self._handle

    @property
    def text(self) -> str:
        """The full text of the paragraph (concatenation of all run texts)."""
        return "".join(run.text for run in self._runs)

    @property
    def runs(self) -> list[Run]:
        return list(self._runs)

    def add_run(self, text: str = "", style: str | None = None) -> Run:
        """Append a run of text and return the :class:`~fastdocx.run.Run`.

        Set formatting on the returned run::

            run = p.add_run("Hello")
            run.bold = True
            run.font.size = 14

        Args:
            text: The run text.
            style: Optional character style name.
        """
        from fastdocx.errors import NativeRuntimeError

        encoded_text = text.encode("utf-8")
        run_handle = self._lib.add_run(
            self._handle,
            encoded_text,
            len(encoded_text),
            -1,  # bold: inherit
            -1,  # italic: inherit
            0,   # font_size: inherit
        )
        if run_handle == 0:
            raise NativeRuntimeError("native add_run failed")

        run = Run._create(handle=run_handle, text=text, lib=self._lib)
        self._runs.append(run)
        return run

    def __repr__(self) -> str:
        return f"Paragraph(handle={self._handle!r}, runs={len(self._runs)})"
