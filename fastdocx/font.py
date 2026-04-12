from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastdocx._native.bindings import NativeLib

_SENTINEL = object()


class Font:
    """Proxy for the font formatting of a :class:`~fastdocx.run.Run`.

    Accessed via ``run.font``; not constructed directly.

    All properties default to ``None`` meaning inherit from the applied style.
    Set to ``True``/``False`` to explicitly override, or ``None`` to clear.

    Example::

        run = p.add_run("Hello")
        run.font.bold = True
        run.font.size = 14      # points
        run.font.name = "Arial"
    """

    def __init__(self, *, run_handle: int, lib: NativeLib, _guard: object = None) -> None:
        if _guard is not _SENTINEL:
            raise TypeError("Font cannot be instantiated directly — access via run.font")
        object.__setattr__(self, "_run_handle", run_handle)
        object.__setattr__(self, "_lib", lib)
        object.__setattr__(self, "_bold", None)
        object.__setattr__(self, "_italic", None)
        object.__setattr__(self, "_underline", None)
        object.__setattr__(self, "_size", None)
        object.__setattr__(self, "_name", None)

    @classmethod
    def _create(cls, run_handle: int, lib: NativeLib) -> Font:
        return cls(run_handle=run_handle, lib=lib, _guard=_SENTINEL)

    # ------------------------------------------------------------------
    # bold
    # ------------------------------------------------------------------

    @property
    def bold(self) -> bool | None:
        return self._bold  # type: ignore[return-value]

    @bold.setter
    def bold(self, value: bool | None) -> None:
        from fastdocx.errors import NativeRuntimeError
        val = -1 if value is None else int(value)
        if self._lib.set_run_bold(self._run_handle, val) != 0:  # type: ignore[attr-defined]
            raise NativeRuntimeError("set_run_bold failed")
        object.__setattr__(self, "_bold", value)

    # ------------------------------------------------------------------
    # italic
    # ------------------------------------------------------------------

    @property
    def italic(self) -> bool | None:
        return self._italic  # type: ignore[return-value]

    @italic.setter
    def italic(self, value: bool | None) -> None:
        from fastdocx.errors import NativeRuntimeError
        val = -1 if value is None else int(value)
        if self._lib.set_run_italic(self._run_handle, val) != 0:  # type: ignore[attr-defined]
            raise NativeRuntimeError("set_run_italic failed")
        object.__setattr__(self, "_italic", value)

    # ------------------------------------------------------------------
    # underline
    # ------------------------------------------------------------------

    @property
    def underline(self) -> bool | None:
        return self._underline  # type: ignore[return-value]

    @underline.setter
    def underline(self, value: bool | None) -> None:
        from fastdocx.errors import NativeRuntimeError
        val = -1 if value is None else int(value)
        if self._lib.set_run_underline(self._run_handle, val) != 0:  # type: ignore[attr-defined]
            raise NativeRuntimeError("set_run_underline failed")
        object.__setattr__(self, "_underline", value)

    # ------------------------------------------------------------------
    # size (points)
    # ------------------------------------------------------------------

    @property
    def size(self) -> int | None:
        return self._size  # type: ignore[return-value]

    @size.setter
    def size(self, value: int | None) -> None:
        from fastdocx.errors import NativeRuntimeError
        half_points = value * 2 if value is not None else 0
        if self._lib.set_run_font_size(self._run_handle, half_points) != 0:  # type: ignore[attr-defined]
            raise NativeRuntimeError("set_run_font_size failed")
        object.__setattr__(self, "_size", value)

    # ------------------------------------------------------------------
    # name
    # ------------------------------------------------------------------

    @property
    def name(self) -> str | None:
        return self._name  # type: ignore[return-value]

    @name.setter
    def name(self, value: str | None) -> None:
        from fastdocx.errors import NativeRuntimeError
        encoded = value.encode("utf-8") if value else b""
        if self._lib.set_run_font_name(self._run_handle, encoded, len(encoded)) != 0:  # type: ignore[attr-defined]
            raise NativeRuntimeError("set_run_font_name failed")
        object.__setattr__(self, "_name", value)

    def __repr__(self) -> str:
        return (
            f"Font(bold={self._bold!r}, italic={self._italic!r}, "  # type: ignore[attr-defined]
            f"underline={self._underline!r}, size={self._size!r}, name={self._name!r})"  # type: ignore[attr-defined]
        )
