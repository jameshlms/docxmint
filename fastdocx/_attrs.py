from __future__ import annotations

from typing import Any


class RawAttrMixin:
    """Wraps object.__setattr__/object.__getattribute__ so subclasses skip the boilerplate."""

    def _setattr(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def _getattr(self, name: str) -> Any:
        return object.__getattribute__(self, name)
