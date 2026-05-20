"""ProxyBase — the root class for all C#-backed proxy objects.

Every proxy (Paragraph, Run, Table, Row, Cell, Section) lives in one of four states
represented by ProxyState:

  LIVE         — _native is an int handle; every property access crosses FFI.
  CONSTRUCTION — _native is None; data lives in _data dict; no C# handle yet.
  SNAPSHOT     — _native is None; _data populated by snapshot(); safe outside ctx manager.
  STALE        — element was removed from the document; all access raises StaleProxyError.

Rules:
  1. Always use _setattr() in __init__ — never self.x = y.
  2. Internal attributes start with _ — they bypass proxy routing unconditionally.
  3. _from_native has no docstring — keeps it out of generated API docs.
  4. __copydocelem__() always returns the same type — para.__copydocelem__() returns Paragraph.
  5. Error messages reference snapshot().
"""

from __future__ import annotations

import enum
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Self

from fastdocx._attrs import RawAttrMixin
from fastdocx.errors import DocumentClosedError, StaleProxyError


class ProxyState(enum.Enum):
    """The lifecycle state of a proxy object."""

    CONSTRUCTION = "construction"
    LIVE = "live"
    SNAPSHOT = "snapshot"
    STALE = "stale"


if TYPE_CHECKING:
    from fastdocx._native.handle import Handle
    from fastdocx.document import Document


class ProxyBase(RawAttrMixin):
    """Root class for all objects backed by a C# native handle."""

    _data: dict[str, Any]
    _child_type_name: str

    def __init__(self) -> None:
        self._setattr("_native", None)
        self._setattr("_document", None)
        self._setattr("_stale", False)
        self._setattr("_is_snapshot", False)
        self._setattr("_data", {})

    @classmethod
    def _from_native(cls, native_handle: int, document: Document) -> Self:
        instance = cls.__new__(cls)
        instance._setattr("_native", native_handle)
        instance._setattr("_document", document)
        instance._setattr("_stale", False)
        instance._setattr("_is_snapshot", False)
        instance._setattr("_data", {})
        return instance

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> ProxyState:
        """The current lifecycle state of this proxy."""
        if self._getattr("_stale"):
            return ProxyState.STALE
        if self._getattr("_native") is not None:
            return ProxyState.LIVE
        if self._getattr("_is_snapshot"):
            return ProxyState.SNAPSHOT
        return ProxyState.CONSTRUCTION

    @property
    def is_live(self) -> bool:
        """True when backed by a native handle in an open document."""
        return self.state is ProxyState.LIVE

    @property
    def is_snapshot(self) -> bool:
        """True when this is a document-independent copy made by ``snapshot()``."""
        return self.state is ProxyState.SNAPSHOT

    @property
    def is_construction(self) -> bool:
        """True when this is a manually constructed spec not yet appended to a document."""
        return self.state is ProxyState.CONSTRUCTION

    @property
    def is_stale(self) -> bool:
        """True when the element has been removed from its document."""
        return self.state is ProxyState.STALE

    @property
    def _is_live(self) -> bool:
        return self.is_live

    def _check_valid(self) -> None:
        if self._getattr("_stale"):
            raise StaleProxyError(
                f"This {type(self).__name__} was removed from the document. "
                "Call snapshot() before removing to retain data."
            )
        doc: Document | None = self._getattr("_document")
        if doc is not None and not doc.is_open:
            raise DocumentClosedError(
                f"{type(self).__name__} cannot be accessed after its document has been "
                "closed. Call snapshot() inside the context manager to retain data."
            )

    def _mark_stale(self) -> None:
        self._setattr("_stale", True)

    def _attach(self, native_handle: int, document: Document) -> None:
        self._setattr("_native", native_handle)
        self._setattr("_document", document)

    def _get_lib(self) -> Handle:
        doc: Document = self._getattr("_document")
        return object.__getattribute__(doc, "_lib")

    # ------------------------------------------------------------------
    # Attribute routing
    # ------------------------------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            self._setattr(name, value)
            return
        # Look for a data descriptor (has __set__) on the class MRO
        for klass in type(self).__mro__:
            if name in klass.__dict__:
                desc = klass.__dict__[name]
                if hasattr(desc, "__set__"):
                    desc.__set__(self, value)
                    return
                break
        # No data descriptor found
        native = self._getattr("_native")
        if native is not None:
            self._check_valid()
            raise AttributeError(f"{type(self).__name__!r} has no settable attribute {name!r}")
        self._getattr("_data")[name] = value

    def __getattr__(self, name: str) -> Any:
        # Called only when normal attribute lookup fails.
        # Descriptors are found by normal MRO lookup before __getattr__ is called.
        native = self._getattr("_native")
        if native is not None:
            self._check_valid()
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")
        try:
            return self._getattr("_data")[name]
        except KeyError:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}") from None

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def __copydocelem__(self) -> Self:
        """Return a mutable snapshot with no native handle.

        Safe to use outside the document context manager.
        Modifying the snapshot does not affect the document.
        Called by the module-level ``snapshot()`` function.
        """
        if self._is_live:
            self._check_valid()
        data = self._copy_data()
        instance: Self = type(self).__new__(type(self))
        instance._setattr("_native", None)
        instance._setattr("_document", None)
        instance._setattr("_stale", False)
        instance._setattr("_is_snapshot", True)
        instance._setattr("_data", data)
        return instance

    def copy(self) -> Self:
        """Alias for ``snapshot(self)`` — kept for backward compatibility."""
        return self.__copydocelem__()

    @abstractmethod
    def _copy_data(self) -> dict[str, Any]: ...

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        self_n = self._getattr("_native")
        other_n = object.__getattribute__(other, "_native")
        if self_n is None and other_n is None:
            return self._getattr("_data") == object.__getattribute__(other, "_data")
        return self_n is not None and self_n == other_n

    def __hash__(self) -> int:
        native = self._getattr("_native")
        return hash(native) if native is not None else id(self)

    def __repr__(self) -> str:
        native = self._getattr("_native")
        if native is None:
            if self._getattr("_stale"):
                return f"{type(self).__name__}(<stale>)"
            return f"{type(self).__name__}(spec)"
        return f"{type(self).__name__}(handle={native!r})"
