from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, overload

if TYPE_CHECKING:
    from navyfox._proxy.base import ElementState
    from navyfox.document import Document


class RawAttrMixin:
    """Wraps object.__setattr__/object.__getattribute__ so subclasses skip the boilerplate."""

    def _setattr(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    @overload
    def _getattr(self, name: Literal["_data"]) -> dict[str, Any]: ...
    @overload
    def _getattr(self, name: Literal["_native"]) -> int | None: ...
    @overload
    def _getattr(self, name: Literal["_document"]) -> Document | None: ...
    @overload
    def _getattr(self, name: Literal["_state"]) -> ElementState: ...
    @overload
    def _getattr(self, name: str) -> Any: ...
    def _getattr(self, name: str) -> Any:
        return object.__getattribute__(self, name)
