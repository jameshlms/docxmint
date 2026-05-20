"""Document — the top-level document object and body collection."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Self, TypeVar, overload

import fastdocx._native.handle as _handle_mod
from fastdocx._attrs import RawAttrMixin
from fastdocx._block import BlockContainerMixin
from fastdocx._native.handle import Handle
from fastdocx._proxy.base import ProxyBase
from fastdocx.collection import CollectionMixin
from fastdocx.errors import DocumentClosedError

if TYPE_CHECKING:
    from fastdocx.collection import DocumentView
    from fastdocx.section import Section
    from fastdocx.styles import StyleCollection

DocumentElementT = TypeVar("DocumentElementT", bound="ProxyBase")

_active_count = 0
_active_count_lock = threading.Lock()


class Document(BlockContainerMixin, CollectionMixin[ProxyBase], RawAttrMixin):
    """A DOCX document backed by the FastDocx native library.

    The document itself is the body collection — iterate it, append to it,
    and access filtered views via `.paragraphs`, `.tables`, etc.

    Use as a context manager for deterministic cleanup::

        with Document.open("report.docx") as doc:
            doc.paragraphs.first.text = "Updated"
            doc.save()

    Or without a context manager (requires explicit close or GC)::

        doc = Document()
        doc.paragraphs.append(Paragraph("Hello"))
        doc.save("output.docx")
        doc.close()
    """

    _lib: Handle
    _handle: int
    _path: str | None
    _edit_path: str | None
    _open: bool
    _collection_name = "body"

    def __init__(self) -> None:
        lib = _handle_mod.get_handle()
        handle = lib.create_document()
        self._setattr("_lib", lib)
        self._setattr("_handle", handle)
        self._setattr("_path", None)
        self._setattr("_edit_path", None)
        self._setattr("_open", True)

    @classmethod
    def open(cls, path: str) -> Document:
        """Open an existing document for reading or writing."""
        lib = _handle_mod.get_handle()
        handle = lib.open_document(path)
        doc = cls.__new__(cls)
        doc._setattr("_lib", lib)
        doc._setattr("_handle", handle)
        doc._setattr("_path", path)
        doc._setattr("_edit_path", None)
        doc._setattr("_open", True)
        return doc

    @classmethod
    def edit(cls, path: str) -> Document:
        """Open a document for in-place editing; saves back on context manager exit."""
        lib = _handle_mod.get_handle()
        handle = lib.open_document(path)
        doc = cls.__new__(cls)
        doc._setattr("_lib", lib)
        doc._setattr("_handle", handle)
        doc._setattr("_path", path)
        doc._setattr("_edit_path", path)
        doc._setattr("_open", True)
        return doc

    # ------------------------------------------------------------------
    # CollectionMixin interface
    # ------------------------------------------------------------------

    @property
    def _parent_handle(self) -> int:
        return self._require_open()

    @property
    def _document(self) -> Document:
        return self

    @property
    def _elem_types(self) -> tuple[type, ...]:
        from fastdocx.paragraph import Paragraph
        from fastdocx.table import Table

        return (Paragraph, Table)

    # ------------------------------------------------------------------
    # BlockContainerMixin hook
    # ------------------------------------------------------------------

    def _block_context(self) -> tuple[int, Any, Any]:
        return (self._require_open(), self._getattr("_lib"), self)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return bool(self._getattr("_open"))

    @property
    def path(self) -> str | None:
        return self._getattr("_path")

    def close(self) -> None:
        """Release the native document handle. Idempotent."""
        if self._getattr("_open"):
            lib: Handle = self._getattr("_lib")
            handle: int = self._getattr("_handle")
            self._setattr("_open", False)
            lib.dispose(handle)

    def __enter__(self) -> Self:
        global _active_count
        with _active_count_lock:
            _active_count += 1
        return self

    def __exit__(self, *_: object) -> None:
        global _active_count
        edit_path: str | None = self._getattr("_edit_path")
        if edit_path and self._getattr("_open"):
            self.save(edit_path)
        self.close()
        with _active_count_lock:
            _active_count -= 1

    def __del__(self) -> None:
        try:
            if self._getattr("_open"):
                import warnings

                warnings.warn(
                    f"Unclosed {self!r}. Use a context manager or call .close().",
                    ResourceWarning,
                    stacklevel=2,
                    source=self,
                )
        except Exception:
            pass
        with contextlib.suppress(Exception):
            self.close()

    def _require_open(self) -> int:
        if not self._getattr("_open"):
            raise DocumentClosedError(
                "Document is closed. "
                "Call .copy() inside the context manager to use data outside it."
            )
        return self._getattr("_handle")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, path: str | None = None) -> None:
        """Save the document.

        If *path* is None and the document was opened from or saved to a path,
        saves back to that path. Otherwise *path* must be provided.
        """
        target = path or self._getattr("_path")
        if target is None:
            raise ValueError(
                "No path provided and document has no associated path. Pass a path to save()."
            )
        lib: Handle = self._getattr("_lib")
        lib.save_document(self._require_open(), target)
        self._setattr("_path", target)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def styles(self) -> StyleCollection:
        from fastdocx.styles import StyleCollection

        return StyleCollection(self._require_open(), self)

    @property
    def default_style(self) -> object:
        return self.styles.default

    @property
    def author(self) -> str:
        lib: Handle = self._getattr("_lib")
        return lib.get_str(self._require_open(), "author")

    @author.setter
    def author(self, value: str) -> None:
        lib: Handle = self._getattr("_lib")
        lib.set_str(self._require_open(), "author", value)

    @property
    def title(self) -> str:
        lib: Handle = self._getattr("_lib")
        return lib.get_str(self._require_open(), "title")

    @title.setter
    def title(self, value: str) -> None:
        lib: Handle = self._getattr("_lib")
        lib.set_str(self._require_open(), "title", value)

    @property
    def subject(self) -> str:
        lib: Handle = self._getattr("_lib")
        return lib.get_str(self._require_open(), "subject")

    @property
    def description(self) -> str:
        lib: Handle = self._getattr("_lib")
        return lib.get_str(self._require_open(), "description")

    @property
    def language(self) -> str:
        lib: Handle = self._getattr("_lib")
        return lib.get_str(self._require_open(), "language")

    # ------------------------------------------------------------------
    # Filtered views
    # ------------------------------------------------------------------

    @property
    def sections(self) -> DocumentView[Section]:
        from fastdocx.section import Section

        return self._block_view(Section, "sections")

    @sections.setter
    def sections(self, _: object) -> None:
        pass  # __iadd__ already mutated the native collection

    # ------------------------------------------------------------------
    # group() — typed filtered view builder
    # ------------------------------------------------------------------

    def group[T: ProxyBase](self, types: list[type[T]]) -> DocumentView[T]:
        from fastdocx.collection import DocumentView

        lib: Handle = self._getattr("_lib")
        return DocumentView(
            self._require_open(),
            self,
            lib,
            tuple(types),
            "body",
        )

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        return bool(self._getattr("_open"))

    def __contains__(self, element: object) -> bool:
        from fastdocx._proxy.base import ProxyBase

        if not isinstance(element, ProxyBase):
            return False
        native = object.__getattribute__(element, "_native")
        if native is None:
            return False
        doc = object.__getattribute__(element, "_document")
        return doc is self

    @overload
    def __getitem__(self, key: int) -> ProxyBase: ...
    @overload
    def __getitem__(self, key: slice) -> DocumentView[ProxyBase]: ...
    @overload
    def __getitem__(self, key: type[DocumentElementT]) -> DocumentView[DocumentElementT]: ...

    def __getitem__(self, key: int | slice | type) -> ProxyBase | DocumentView[Any]:
        if isinstance(key, type):
            return self._block_view(key, _collection_for_type(key))
        return super().__getitem__(key)  # type: ignore[return-value]

    def __iadd__(self, elements: Iterable[ProxyBase]) -> Self:  # type: ignore[override]
        self.extend(elements)
        return self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return NotImplemented
        return self._getattr("_handle") == other._getattr("_handle")

    def __hash__(self) -> int:
        return hash(self._getattr("_handle"))

    def __repr__(self) -> str:
        path = self._getattr("_path")
        open_ = self._getattr("_open")
        try:
            n = len(self) if open_ else "?"
        except Exception:
            n = "?"
        return f"<Document path={path!r} elements={n} open={open_}>"


def _collection_for_type(t: type) -> str:
    from fastdocx.paragraph import Paragraph
    from fastdocx.section import Section
    from fastdocx.table import Table

    if t is Paragraph:
        return "paragraphs"
    if t is Table:
        return "tables"
    if t is Section:
        return "sections"
    return "body"
