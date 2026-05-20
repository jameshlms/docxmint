"""Style and StyleCollection."""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Literal

if TYPE_CHECKING:
    from fastdocx._native.handle import Handle
    from fastdocx.document import Document


class Style:
    """A document style definition (live — backed by a native handle)."""

    def __init__(self, handle: int, doc: Document) -> None:
        self._handle = handle
        self._doc = doc

    def _lib(self) -> Handle:
        return self._doc._lib

    @property
    def name(self) -> str:
        return self._lib().get_str(self._handle, "style_name")

    @property
    def type(self) -> Literal["paragraph", "character", "table", "numbering"]:
        val = self._lib().get_str(self._handle, "style_type")
        return val or "paragraph"  # type: ignore[return-value]

    @property
    def based_on(self) -> str | None:
        val = self._lib().get_str(self._handle, "based_on")
        return val or None

    @property
    def next_style(self) -> str | None:
        val = self._lib().get_str(self._handle, "next_style")
        return val or None

    @property
    def is_default(self) -> bool:
        return bool(self._lib().get_int(self._handle, "is_default"))

    def __repr__(self) -> str:
        try:
            return f"Style({self.name!r})"
        except Exception:
            return "Style(<error>)"


class StyleCollection:
    """Collection of all styles in a document (live view)."""

    def __init__(self, doc_handle: int, doc: Document) -> None:
        self._doc_handle = doc_handle
        self._doc = doc

    def _lib(self) -> Handle:
        return self._doc._lib

    @property
    def default(self) -> Style | None:
        try:
            h = self._lib().get_child_handle(self._doc_handle, "default_style", 0)
            return Style(h, self._doc)
        except Exception:
            return None

    def __getitem__(self, name: str) -> Style:
        try:
            h = self._lib().get_child_handle(self._doc_handle, f"style:{name}", 0)
            return Style(h, self._doc)
        except Exception:
            raise KeyError(name) from None

    def __contains__(self, name: object) -> bool:
        try:
            self[str(name)]
            return True
        except KeyError:
            return False

    def __iter__(self) -> Iterator[Style]:
        try:
            n = self._lib().get_count(self._doc_handle, "styles")
        except Exception:
            return
        for i in range(n):
            try:
                h = self._lib().get_child_handle(self._doc_handle, "styles", i)
                yield Style(h, self._doc)
            except Exception:
                pass

    def __len__(self) -> int:
        try:
            return self._lib().get_count(self._doc_handle, "styles")
        except Exception:
            return 0

    def __repr__(self) -> str:
        try:
            return f"StyleCollection(len={len(self)})"
        except Exception:
            return "StyleCollection(<error>)"
