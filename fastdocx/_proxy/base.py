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

import contextlib
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


UNSET: Any = object()

if TYPE_CHECKING:
    from fastdocx._native.handle import Handle
    from fastdocx.document import Document


class ProxyBase(RawAttrMixin):
    """Root class for all objects backed by a C# native handle."""

    _data: dict[str, Any]
    _child_type_name: str
    _native: int | None
    _document: Document | None
    _state: ProxyState

    def _get_data(self) -> dict[str, Any]:
        """Return the data dict for this proxy, whether live or snapshot."""
        if self._is_live:
            self._check_valid()
        return self._getattr("_data")

    def _set_data(self, data: dict[str, Any]) -> None:
        """Set all data at once when materialising a snapshot."""
        self._setattr("_data", data)

    def _get_child_type_name(self) -> str:
        """Return the child type name for this proxy, used in error messages."""
        return self._getattr("_child_type_name")

    def _set_child_type_name(self, name: str) -> None:
        """Set the child type name for this proxy, used in error messages."""
        self._setattr("_child_type_name", name)

    def _get_native(self) -> int | None:
        """Return the native handle for this proxy, or None if not live."""
        return self._getattr("_native")

    def _set_native(self, native: int | None) -> None:
        """Set the native handle for this proxy."""
        self._setattr("_native", native)

    def _get_document(self) -> Document | None:
        """Return the associated Document for this proxy, or None if not live."""
        return self._getattr("_document")

    def _set_document(self, document: Document | None) -> None:
        """Set the associated Document for this proxy."""
        self._setattr("_document", document)

    def _get_state(self) -> ProxyState:
        """Return the current ProxyState for this proxy."""
        return self._getattr("_state")

    def _set_state(self, state: ProxyState) -> None:
        """Set the current ProxyState for this proxy."""
        self._setattr("_state", state)

    def __init__(self) -> None:
        self._set_native(None)
        self._set_document(None)
        self._set_state(ProxyState.CONSTRUCTION)
        self._set_data(dict())

    @classmethod
    def _from_native(cls, native_handle: int, document: Document) -> Self:
        instance = cls.__new__(cls)
        instance._set_native(native_handle)
        instance._set_document(document)
        instance._set_state(ProxyState.LIVE)
        instance._set_data(dict())
        return instance

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> ProxyState:
        """The current lifecycle state of this proxy."""
        return self._getattr("_state")

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
        if self._getattr("_state") is ProxyState.STALE:
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
        self._set_state(ProxyState.STALE)

    def _attach(self, native_handle: int, document: Document) -> None:
        self._set_native(native_handle)
        self._set_document(document)
        self._set_state(ProxyState.LIVE)

    def _get_lib(self) -> Handle:
        doc = self._get_document()
        if doc is None:
            raise ValueError(f"{type(self).__name__} has no associated document.")
        return object.__getattribute__(doc, "_lib")

    # ------------------------------------------------------------------
    # Batch write
    # ------------------------------------------------------------------

    def _apply_changes(self, changes: dict[str, Any]) -> None:
        """Apply *changes* in one FFI call, or a dict update in construction state."""
        if not changes:
            return
        if not self._is_live:
            self._getattr("_data").update(changes)
        else:
            self._check_valid()
            pending = {k: int(v) if isinstance(v, bool) else v for k, v in changes.items()}
            self._get_lib().set_many(self._getattr("_native"), pending)

    @contextlib.contextmanager
    def edit(self):
        """Context manager that batches property writes into a single FFI call.

        Prefer the class-specific ``format()`` for straightforward updates.
        Use ``edit()`` when the batch requires conditional logic:

        .. code-block:: python

            with para.edit() as p:
                if urgent:
                    p.space_before = 0.0
                p.alignment = "left"

        On a construction-state proxy ``edit()`` is a no-op — writes already
        go directly to the local data dict, so batching has no cost.
        """
        if not self._is_live:
            yield self
            return
        self._check_valid()
        pending: dict[str, Any] = {}
        yield _EditProxy(self, pending)
        if pending:
            self._get_lib().set_many(self._getattr("_native"), pending)

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
        state = self._get_state()
        if state is ProxyState.LIVE or state is ProxyState.STALE:
            self._check_valid()
            raise AttributeError(f"{type(self).__name__!r} has no settable attribute {name!r}")
        self._get_data()[name] = value

    def __getattr__(self, name: str) -> Any:
        # Called only when normal attribute lookup fails.
        # Descriptors are found by normal MRO lookup before __getattr__ is called.
        state = self._get_state()
        if state is ProxyState.LIVE or state is ProxyState.STALE:
            self._check_valid()
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")
        try:
            return self._get_data()[name]
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
        instance._set_native(None)
        instance._set_document(None)
        instance._set_state(ProxyState.SNAPSHOT)
        instance._set_data(data)
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
        if not isinstance(other, type(self)):
            return NotImplemented
        self_n = self._get_native()
        other_n = object.__getattribute__(other, "_native")
        if self_n is None and other_n is None:
            return self._get_data() == other._get_data()
        return self_n is not None and self_n == other_n

    def __hash__(self) -> int:
        native = self._get_native()
        return hash(native) if native is not None else id(self)

    def __repr__(self) -> str:
        state = self._get_state()
        if state is ProxyState.STALE:
            return f"{type(self).__name__}(<stale>)"
        native = self._get_native()
        if native is None:
            return f"{type(self).__name__}(spec)"
        return f"{type(self).__name__}(handle={native!r})"


class _EditProxy:
    """Accumulates property writes inside an ``edit()`` block; flushed as one ``set_many`` call."""

    def __init__(self, proxy: ProxyBase, pending: dict[str, Any]) -> None:
        object.__setattr__(self, "_proxy", proxy)
        object.__setattr__(self, "_pending", pending)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        pending: dict[str, Any] = object.__getattribute__(self, "_pending")
        match value:
            case bool():
                pending[name] = int(value)
            case str() | float() | int():
                pending[name] = value
            case _:
                raise TypeError(f"Cannot batch-write {name!r}={value!r}")

    def __getattr__(self, name: str) -> Any:
        proxy: ProxyBase = object.__getattribute__(self, "_proxy")
        return getattr(proxy, name)
