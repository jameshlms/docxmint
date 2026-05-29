"""Section proxy."""

from __future__ import annotations

from typing import Any, Literal, Self, override

from docxmint._block import BlockContainerMixin
from docxmint._proxy.base import UNSET as _UNSET
from docxmint._proxy.base import ElementState, ProxyBase
from docxmint._proxy.descriptors import BoolProperty, ChoiceProperty, FloatProperty


class Section(BlockContainerMixin, ProxyBase):
    """A document section — controls page layout for a contiguous range of body content.

    Sections are live proxies accessed through :attr:`~docxmint.document.Document.sections`:

    .. code-block:: python

        section = doc.sections[0]
        section.orientation = "landscape"
        section.page_width = 11.0    # inches
        section.page_height = 8.5   # inches

    Properties:

    - ``orientation`` — ``"portrait"`` (default) or ``"landscape"``
    - ``page_width`` — page width in inches (default ``8.5``)
    - ``page_height`` — page height in inches (default ``11.0``)
    - ``start_type`` — how the section begins: ``"continuous"``, ``"newPage"``
      (default), ``"evenPage"``, or ``"oddPage"``
    - ``different_first_page`` — whether the first page has a distinct header/footer
    """

    _child_type_name = "section"

    orientation: ChoiceProperty[Literal["portrait", "landscape"]] = ChoiceProperty(
        "orientation", ("portrait", "landscape"), default="portrait"
    )
    page_width = FloatProperty("page_width", default=8.5)  # inches
    page_height = FloatProperty("page_height", default=11.0)  # inches
    margin_top = FloatProperty("margin_top", default=1.0)  # inches
    margin_bottom = FloatProperty("margin_bottom", default=1.0)  # inches
    margin_left = FloatProperty("margin_left", default=1.25)  # inches
    margin_right = FloatProperty("margin_right", default=1.25)  # inches
    margin_header = FloatProperty("margin_header", default=0.5)  # inches
    margin_footer = FloatProperty("margin_footer", default=0.5)  # inches
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

    # ------------------------------------------------------------------
    # Batch write
    # ------------------------------------------------------------------

    def format(
        self,
        *,
        orientation: Literal["portrait", "landscape"] = _UNSET,
        page_width: float = _UNSET,
        page_height: float = _UNSET,
        margin_top: float = _UNSET,
        margin_bottom: float = _UNSET,
        margin_left: float = _UNSET,
        margin_right: float = _UNSET,
        margin_header: float = _UNSET,
        margin_footer: float = _UNSET,
        start_type: Literal["continuous", "newPage", "evenPage", "oddPage"] = _UNSET,
        different_first_page: bool = _UNSET,
    ) -> Self:
        """Set multiple section properties in a single FFI call and return *self*.

        Only the keyword arguments you pass are changed; omitted properties are
        left untouched.

        Example:
            .. code-block:: python

                section.format(
                    orientation="landscape",
                    page_width=11.0,
                    page_height=8.5,
                    margin_left=0.75,
                    margin_right=0.75,
                )
        """
        changes: dict[str, Any] = {}
        for _name, _val in (
            ("orientation", orientation),
            ("page_width", page_width),
            ("page_height", page_height),
            ("margin_top", margin_top),
            ("margin_bottom", margin_bottom),
            ("margin_left", margin_left),
            ("margin_right", margin_right),
            ("margin_header", margin_header),
            ("margin_footer", margin_footer),
            ("start_type", start_type),
            ("different_first_page", different_first_page),
        ):
            if _val is not _UNSET:
                changes[_name] = _val
        self._apply_changes(changes)
        return self

    @override
    def _block_context(self) -> tuple[int, Any, Any] | None:
        if not self._is_live:
            return None
        self._check_valid()
        return (self._native_handle, self._get_lib(), self._document_ref)

    @override
    def _copy_data(self) -> dict[str, Any]:
        return {
            "orientation": self.orientation,
            "page_width": self.page_width,
            "page_height": self.page_height,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
            "margin_header": self.margin_header,
            "margin_footer": self.margin_footer,
            "start_type": self.start_type,
            "different_first_page": self.different_first_page,
        }

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Section(<stale>)"
        native = self._get_native()
        if native is None:
            return "Section(spec)"
        return f"Section(handle={native!r})"
