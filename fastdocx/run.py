from __future__ import annotations

from typing import TYPE_CHECKING

from fastdocx.font import Font

if TYPE_CHECKING:
    from fastdocx._native.bindings import NativeLib

_SENTINEL = object()


class Run:
    """Represents a run of text within a :class:`~fastdocx.paragraph.Paragraph`.

    Instances are created by :meth:`Paragraph.add_run`; they cannot be
    constructed directly.

    Formatting can be set via convenience properties or through :attr:`font`::

        run = p.add_run("Hello")
        run.bold = True
        run.font.size = 14
        run.font.name = "Arial"
    """

    def __init__(self, *, handle: int, text: str, lib: NativeLib, _guard: object = None) -> None:
        if _guard is not _SENTINEL:
            raise TypeError("Run cannot be instantiated directly — use Paragraph.add_run()")
        self._handle = handle
        self._text = text
        self._lib = lib
        self._font = Font._create(run_handle=handle, lib=lib)

    @classmethod
    def _create(cls, handle: int, text: str, lib: NativeLib) -> Run:
        return cls(handle=handle, text=text, lib=lib, _guard=_SENTINEL)

    @property
    def text(self) -> str:
        return self._text

    @property
    def font(self) -> Font:
        return self._font

    # ------------------------------------------------------------------
    # Convenience shorthands (delegate to font proxy)
    # ------------------------------------------------------------------

    @property
    def bold(self) -> bool | None:
        return self._font.bold

    @bold.setter
    def bold(self, value: bool | None) -> None:
        self._font.bold = value

    @property
    def italic(self) -> bool | None:
        return self._font.italic

    @italic.setter
    def italic(self, value: bool | None) -> None:
        self._font.italic = value

    @property
    def underline(self) -> bool | None:
        return self._font.underline

    @underline.setter
    def underline(self, value: bool | None) -> None:
        self._font.underline = value

    def __repr__(self) -> str:
        return f"Run(text={self._text!r}, font={self._font!r})"
