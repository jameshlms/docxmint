"""Document — the top-level document object and body collection."""

from __future__ import annotations

import contextlib
import os
import tempfile
import threading
import weakref
from collections.abc import Iterable
from typing import IO, TYPE_CHECKING, Any, Self, overload

import navyfox._native.handle as _handle_mod
from navyfox._block import BlockContainerMixin
from navyfox._collection import CollectionMixin
from navyfox._native.handle import Handle
from navyfox._proxy.base import ProxyBase
from navyfox.errors import DocumentClosedError
from navyfox.paragraph import Paragraph
from navyfox.table import Table

if TYPE_CHECKING:
    from navyfox._collection import DocumentView
    from navyfox.formats import PageMargins
    from navyfox.section import Section
    from navyfox.styles import StyleCollection

_PathArg = str | os.PathLike[str] | IO[bytes]

_active_count = 0
_active_count_lock = threading.Lock()


def _resolve_open_path(path: _PathArg) -> tuple[str, str | None]:
    """Return ``(str_path, tmp_path)``.

    For ``str`` / ``PathLike`` inputs *tmp_path* is ``None``.  For ``IO``
    inputs the bytes are written to a temporary file; *tmp_path* is its path
    and the caller must delete it when the native handle is released.
    """
    if isinstance(path, (str, os.PathLike)):
        return os.fspath(path), None
    data = path.read()
    fd, tmp_path = tempfile.mkstemp(suffix=".docx")
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return tmp_path, tmp_path


def _type_name_map() -> dict[type, str]:
    from navyfox.section import Section

    return {
        Paragraph: "paragraphs",
        Table: "tables",
        Section: "sections",
    }


def _collection_for_type(t: type) -> str:
    return _type_name_map().get(t, "body")


class Document(BlockContainerMixin, CollectionMixin[ProxyBase]):
    """A DOCX document backed by the NavyFox native library.

    The document is the body collection — iterate it, append to it, and access
    typed filtered views via ``.paragraphs``, ``.tables``, ``.sections``, etc.

    All document data lives in the C# native layer. Python proxies (Paragraph, Run,
    Table, …) hold only integer handles. Every property access crosses the FFI boundary.

    Prefer the context manager for deterministic cleanup:

    .. code-block:: python

        with Document.open("report.docx") as doc:
            doc.paragraphs[0].text = "Updated"
            doc.save()

    Without a context manager, call ``.close()`` explicitly:

    .. code-block:: python

        doc = Document()
        doc.add_paragraph("Hello")
        doc.save("output.docx")
        doc.close()

    Closing an already-closed document is safe (idempotent). Forgetting to close
    triggers a ``ResourceWarning`` when the object is garbage-collected.
    """

    _lib: Handle
    _handle: int
    _path: str | None
    _edit_path: str | None
    _tmp_path: str | None
    _io_edit: IO[bytes] | None
    _open: bool
    _finalizer: weakref.finalize[[Handle, int, str | None], Any]
    _collection_name = "body"

    @staticmethod
    def _dispose(lib: Handle, handle: int, tmp_path: str | None) -> None:
        with contextlib.suppress(Exception):
            lib.dispose(handle)
        if tmp_path:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)

    def _get_lib(self) -> Handle:
        return object.__getattribute__(self, "_lib")

    def _get_handle(self) -> int:
        return object.__getattribute__(self, "_handle")

    def _get_path(self) -> str | None:
        return object.__getattribute__(self, "_path")

    def _get_edit_path(self) -> str | None:
        return object.__getattribute__(self, "_edit_path")

    def _get_tmp_path(self) -> str | None:
        return object.__getattribute__(self, "_tmp_path")

    def _get_io_edit(self) -> IO[bytes] | None:
        return object.__getattribute__(self, "_io_edit")

    def _get_open(self) -> bool:
        return object.__getattribute__(self, "_open")

    def _get_finalizer(self) -> weakref.finalize[[Handle, int, str | None], Any]:
        return object.__getattribute__(self, "_finalizer")

    def _set_lib(self, lib: Handle) -> None:
        object.__setattr__(self, "_lib", lib)

    def _set_handle(self, handle: int) -> None:
        object.__setattr__(self, "_handle", handle)

    def _set_path(self, path: str | None) -> None:
        object.__setattr__(self, "_path", path)

    def _set_edit_path(self, edit_path: str | None) -> None:
        object.__setattr__(self, "_edit_path", edit_path)

    def _set_tmp_path(self, tmp_path: str | None) -> None:
        object.__setattr__(self, "_tmp_path", tmp_path)

    def _set_io_edit(self, io_edit: IO[bytes] | None) -> None:
        object.__setattr__(self, "_io_edit", io_edit)

    def _set_open(self, open: bool) -> None:
        object.__setattr__(self, "_open", open)

    def _set_finalizer(self, finalizer: weakref.finalize[[Handle, int, str | None], Any]) -> None:
        object.__setattr__(self, "_finalizer", finalizer)

    def __init__(self) -> None:
        lib = _handle_mod.get_handle()
        handle = lib.create_document()
        self._set_path(None)
        self._set_tmp_path(None)
        self._set_lib(lib)
        self._set_handle(handle)
        self._set_edit_path(None)
        self._set_io_edit(None)
        self._set_open(True)
        self._set_finalizer(weakref.finalize(self, Document._dispose, lib, handle, None))

    @classmethod
    def open(cls, path: _PathArg) -> Document:
        """Open an existing ``.docx`` file for reading or writing.

        Args:
            path: Filesystem path (``str`` or :class:`pathlib.Path`) or a
                binary file-like object (``IO[bytes]``).  When an ``IO``
                object is given its current contents are read immediately;
                ``doc.path`` will be ``None``.

        Returns:
            A live ``Document`` backed by the given source.

        Example:
            .. code-block:: python

                with Document.open("report.docx") as doc:
                    for para in doc.paragraphs:
                        print(para.text)

                # from a byte stream
                with open("report.docx", "rb") as f:
                    with Document.open(f) as doc:
                        print(doc.paragraphs[0].text)
        """
        str_path, tmp_path = _resolve_open_path(path)
        lib = _handle_mod.get_handle()
        handle = lib.open_document(str_path)
        doc = cls.__new__(cls)
        doc._set_lib(lib)
        doc._set_handle(handle)
        doc._set_path(None if tmp_path else str_path)
        doc._set_edit_path(None)
        doc._set_tmp_path(tmp_path)
        doc._set_io_edit(None)
        doc._set_open(True)
        doc._set_finalizer(weakref.finalize(doc, Document._dispose, lib, handle, tmp_path))
        return doc

    @classmethod
    def edit(cls, path: _PathArg) -> Document:
        """Open a document for in-place editing.

        Identical to ``open()`` except that the context manager automatically
        saves back to *path* on ``__exit__``.  When *path* is an ``IO``
        object the modified bytes are written back to it on exit.

        Args:
            path: Filesystem path (``str`` or :class:`pathlib.Path`) or a
                binary file-like object (``IO[bytes]``).

        Example:
            .. code-block:: python

                with Document.edit("report.docx") as doc:
                    doc.paragraphs[0].text = "New heading"
                # saved automatically

                # round-trip through a buffer
                buf = io.BytesIO(pathlib.Path("report.docx").read_bytes())
                with Document.edit(buf) as doc:
                    doc.paragraphs[0].text = "New heading"
                buf.seek(0)
                pathlib.Path("report.docx").write_bytes(buf.read())
        """
        str_path, tmp_path = _resolve_open_path(path)
        io_edit = path if not isinstance(path, (str, os.PathLike)) else None
        lib = _handle_mod.get_handle()
        handle = lib.open_document(str_path)
        doc = cls.__new__(cls)
        doc._set_lib(lib)
        doc._set_handle(handle)
        doc._set_path(None if tmp_path else str_path)
        doc._set_edit_path(str_path)
        doc._set_tmp_path(tmp_path)
        doc._set_io_edit(io_edit)
        doc._set_open(True)
        doc._set_finalizer(weakref.finalize(doc, Document._dispose, lib, handle, tmp_path))
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
        from navyfox.paragraph import Paragraph
        from navyfox.table import Table

        return (Paragraph, Table)

    # ------------------------------------------------------------------
    # BlockContainerMixin hook
    # ------------------------------------------------------------------

    def _block_context(self) -> tuple[int, Any, Any]:
        return (self._require_open(), self._get_lib(), self)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        """A boolean indicator of whether the document is still open for operations or not.

        Returns:
            bool: The indicator of whether the document is open or not.
        """
        return bool(self._get_open())

    @property
    def path(self) -> str | None:
        """The filesystem path associated with this document, or ``None`` for new documents.

        Updated after every successful ``save()`` call.
        """
        return self._get_path()

    def close(self) -> None:
        """Release the native document handle. Idempotent."""
        if self._get_open():
            self._set_open(False)
            self._get_finalizer()()

    def __enter__(self) -> Self:
        global _active_count
        with _active_count_lock:
            _active_count += 1
        return self

    def __exit__(self, *_: object) -> None:
        global _active_count
        if self._get_open():
            io_edit: IO[bytes] | None = self._get_io_edit()
            edit_path: str | None = self._get_edit_path()
            if io_edit is not None:
                self.save(io_edit)
            elif edit_path:
                self.save(edit_path)
        self.close()
        with _active_count_lock:
            _active_count -= 1

    def _require_open(self) -> int:
        if not self._get_open():
            raise DocumentClosedError(
                "Document is closed. "
                "Call .copy() inside the context manager to use data outside it."
            )
        return self._get_handle()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, path: _PathArg | None = None) -> None:
        """Save the document.

        Args:
            path: Destination as a ``str``, :class:`pathlib.Path`, or binary
                ``IO[bytes]`` object.  If omitted, saves back to the path the
                document was opened from or last saved to.  An ``IO`` target
                never updates ``doc.path``.

        Raises:
            ValueError: If *path* is ``None`` and no associated path exists.
        """
        target: _PathArg | None = path if path is not None else self._get_path()
        if target is None:
            raise ValueError(
                "No path provided and document has no associated path. Pass a path to save()."
            )
        lib: Handle = self._get_lib()
        if isinstance(target, (str, os.PathLike)):
            str_target = os.fspath(target)
            lib.save_document(self._require_open(), str_target)
            self._set_path(str_target)
        else:
            fd, tmp = tempfile.mkstemp(suffix=".docx")
            os.close(fd)
            try:
                lib.save_document(self._require_open(), tmp)
                with open(tmp, "rb") as f:
                    target.write(f.read())
            finally:
                with contextlib.suppress(OSError):
                    os.unlink(tmp)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def styles(self) -> StyleCollection:
        from navyfox.styles import StyleCollection

        return StyleCollection(self._require_open(), self)

    @property
    def default_style(self) -> object:
        return self.styles.default

    @property
    def author(self) -> str:
        """Core property: document author (``dc:creator``)."""
        lib: Handle = self._get_lib()
        return lib.get_str(self._require_open(), "author")

    @author.setter
    def author(self, value: str) -> None:
        lib: Handle = self._get_lib()
        lib.set_str(self._require_open(), "author", value)

    @property
    def title(self) -> str:
        """Core property: document title (``dc:title``)."""
        lib: Handle = self._get_lib()
        return lib.get_str(self._require_open(), "title")

    @title.setter
    def title(self, value: str) -> None:
        lib: Handle = self._get_lib()
        lib.set_str(self._require_open(), "title", value)

    @property
    def subject(self) -> str:
        """Core property: document subject (``dc:subject``). Read-only."""
        lib: Handle = self._get_lib()
        return lib.get_str(self._require_open(), "subject")

    @property
    def description(self) -> str:
        """Core property: document description / abstract (``dc:description``). Read-only."""
        lib: Handle = self._get_lib()
        return lib.get_str(self._require_open(), "description")

    @property
    def language(self) -> str:
        """Core property: document language tag (``dc:language``), e.g. ``"en-US"``. Read-only."""
        lib: Handle = self._get_lib()
        return lib.get_str(self._require_open(), "language")

    # ------------------------------------------------------------------
    # Filtered views
    # ------------------------------------------------------------------

    @property
    def sections(self) -> DocumentView[Section]:
        from navyfox.section import Section

        return self._block_view(Section, "sections")

    @sections.setter
    def sections(self, _: object) -> None:
        pass  # __iadd__ already mutated the native collection

    @property
    def margins(self) -> PageMargins:
        """Page margins for the document.

        On get: returns the shared :class:`~navyfox.formats.PageMargins` when all
        sections have identical margins, or the defaults if no sections exist.
        Raises :exc:`ValueError` if sections have differing margins — use
        ``doc.sections[i].margin_*`` to read per-section values instead.

        On set: applies the given margins to **all** sections. Accepts:

        - A :class:`~navyfox.formats.PageMargins` instance.
        - A single ``float`` — sets top, bottom, left, and right uniformly.
        - A 2-tuple ``(vertical, horizontal)`` — CSS-style shorthand.
        - A 4-tuple ``(top, bottom, left, right)``.

        Example:
            .. code-block:: python

                doc.margins = 0.75                    # tight, all sides
                doc.margins = (0.75, 1.0)             # 0.75 top/bottom, 1.0 left/right
                doc.margins = PageMargins(left=0.5, right=0.5)
        """
        from navyfox.formats import PageMargins

        secs = self.sections
        if len(secs) == 0:
            return PageMargins()
        first = PageMargins(
            top=secs[0].margin_top,
            bottom=secs[0].margin_bottom,
            left=secs[0].margin_left,
            right=secs[0].margin_right,
            header=secs[0].margin_header,
            footer=secs[0].margin_footer,
        )
        mismatch = any(
            PageMargins(
                top=s.margin_top,
                bottom=s.margin_bottom,
                left=s.margin_left,
                right=s.margin_right,
                header=s.margin_header,
                footer=s.margin_footer,
            )
            != first
            for s in secs[1:]
        )

        if mismatch:
            raise ValueError(
                "Sections have differing margins; cannot return a single value. Read margins from individual sections instead."
            )

        return first

    @margins.setter
    def margins(
        self,
        value: PageMargins | float | tuple[float, float] | tuple[float, float, float, float],
    ) -> None:
        from navyfox.formats import PageMargins

        match value:
            case PageMargins():
                pm = value

            case float() | int():
                v = float(value)
                pm = PageMargins(top=v, bottom=v, left=v, right=v)

            case (float() | int(), float() | int()):
                v, h = float(value[0]), float(value[1])
                pm = PageMargins(top=v, bottom=v, left=h, right=h)

            case (float() | int(), float() | int(), float() | int(), float() | int()):
                pm = PageMargins(
                    top=float(value[0]),
                    bottom=float(value[1]),
                    left=float(value[2]),
                    right=float(value[3]),
                )
            case tuple():
                raise ValueError(
                    f"margins tuple must have 2 or 4 elements, got {len(value)}"
                )
            case _:
                raise TypeError(
                    f"margins must be a PageMargins, float, or tuple; got {type(value).__name__!r}"
                )

        for section in self.sections:
            section.margin_top = pm.top
            section.margin_bottom = pm.bottom
            section.margin_left = pm.left
            section.margin_right = pm.right
            section.margin_header = pm.header
            section.margin_footer = pm.footer

    # ------------------------------------------------------------------
    # group() — typed filtered view builder
    # ------------------------------------------------------------------

    def group[T: ProxyBase](self, types: list[type[T]]) -> DocumentView[T]:
        """Return a live view over the body containing only the given element types.

        Args:
            types: A list of proxy types to include (e.g. ``[Paragraph, Table]``).

        Returns:
            A :class:`~navyfox.collection.DocumentView` that yields only elements
            whose type is in *types*.

        Example:
            .. code-block:: python

                from navyfox import Paragraph, Table
                for elem in doc.group([Paragraph, Table]):
                    print(type(elem).__name__, repr(elem))
        """
        from navyfox._collection import DocumentView

        lib: Handle = self._get_lib()
        return DocumentView(
            self._require_open(),
            self,  # type: ignore[arg-type]  # Self@Document IS Document; Pyright can't resolve the circular stub
            lib,
            tuple(types),
            "body",
        )

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        return bool(self._get_open())

    def __contains__(self, element: object) -> bool:
        from navyfox._proxy.base import ProxyBase

        if not isinstance(element, ProxyBase):
            return False
        native = element._get_native()  # type: ignore
        if native is None:
            return False
        doc = element._get_document()  # type: ignore
        return doc is self

    @overload
    def __getitem__(self, key: int) -> ProxyBase: ...
    @overload
    def __getitem__(self, key: slice) -> DocumentView[ProxyBase]: ...
    @overload
    def __getitem__[T: ProxyBase](self, key: type[T]) -> DocumentView[T]: ...

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
        return self._get_handle() == other._get_handle()

    def __hash__(self) -> int:
        return hash(self._get_handle())

    def __repr__(self) -> str:
        path = self._get_path()
        open_ = self._get_open()
        try:
            n = len(self) if open_ else "?"
        except Exception:
            n = "?"
        return f"<Document path={path!r} elements={n} open={open_}>"
