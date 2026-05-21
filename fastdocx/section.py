"""Section proxy."""

from __future__ import annotations

from typing import Any, Literal

from fastdocx._block import BlockContainerMixin
from fastdocx._proxy.base import ProxyBase, ProxyState
from fastdocx._proxy.descriptors import BoolProperty, ChoiceProperty, FloatProperty


class Section(BlockContainerMixin, ProxyBase):
    """A document section."""

    _child_type_name = "section"

    orientation: ChoiceProperty[Literal["portrait", "landscape"]] = ChoiceProperty(
        "orientation", ("portrait", "landscape"), default="portrait"
    )
    page_width = FloatProperty("page_width", default=8.5)  # inches
    page_height = FloatProperty("page_height", default=11.0)  # inches
    start_type: ChoiceProperty[Literal["continuous", "newPage", "evenPage", "oddPage"]] = (
        ChoiceProperty(
            "start_type",
            ("continuous", "newPage", "evenPage", "oddPage"),
            default="newPage",
        )
    )
    different_first_page = BoolProperty("different_first_page")

    def __init__(self) -> None:
        super().__init__()

    def _block_context(self) -> tuple[int, Any, Any] | None:
        if not self._is_live:
            return None
        self._check_valid()
        return (self._getattr("_native"), self._get_lib(), self._getattr("_document"))

    def _copy_data(self) -> dict[str, Any]:
        return {
            "orientation": self.orientation,
            "page_width": self.page_width,
            "page_height": self.page_height,
            "start_type": self.start_type,
            "different_first_page": self.different_first_page,
        }

    def __repr__(self) -> str:
        if self.state is ProxyState.STALE:
            return "Section(<stale>)"
        native = self._getattr("_native")
        if native is None:
            return "Section(spec)"
        return f"Section(handle={native!r})"
