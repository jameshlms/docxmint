from collections.abc import Iterator
from typing import Any, Literal, Self

from _typeshed import Incomplete

from fastdocx._proxy.base import ProxyBase as ProxyBase
from fastdocx._proxy.base import ProxyState as ProxyState
from fastdocx._proxy.descriptors import BoolProperty as BoolProperty
from fastdocx._proxy.descriptors import ChoiceProperty as ChoiceProperty
from fastdocx._proxy.descriptors import ColorProperty as ColorProperty
from fastdocx._proxy.descriptors import FloatProperty as FloatProperty
from fastdocx._proxy.descriptors import StringProperty as StringProperty
from fastdocx.collection import DocumentView as DocumentView
from fastdocx.run import Run as Run

class Paragraph(ProxyBase):
    _child_type_name: str
    text: Incomplete
    style: Incomplete
    alignment: ChoiceProperty[Literal["left", "right", "center", "justify"]]
    keep_together: Incomplete
    keep_with_next: Incomplete
    page_break_before: Incomplete
    def __init__(
        self,
        text: str = "",
        *,
        style: str = "Normal",
        alignment: Literal["left", "right", "center", "justify"] | None = None,
        keep_together: bool = False,
        keep_with_next: bool = False,
        page_break_before: bool = False,
    ) -> None: ...
    @classmethod
    def horizontal_line(
        cls,
        style: Literal["single", "double", "dotted", "dashed", "wave"] = "single",
        width: float = 6.0,
        color: str = "auto",
    ) -> HorizontalRule: ...
    @property
    def runs(self) -> DocumentView[Run]: ...
    def add_run(self, text: str = "") -> Run: ...
    def align(self, alignment: Literal["left", "right", "center", "justify"]) -> Self: ...
    def set_style(self, style: str) -> Self: ...
    def _copy_data(self) -> dict[str, Any]: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Run]: ...
    def __contains__(self, run: object) -> bool: ...

class HorizontalRule(Paragraph):
    line_style: ChoiceProperty[Literal["single", "double", "dotted", "dashed", "wave"]]
    line_width: Incomplete
    line_color: Incomplete
    def __init__(
        self,
        *,
        line_style: Literal["single", "double", "dotted", "dashed", "wave"] = "single",
        line_width: float = 6.0,
        line_color: str = "auto",
    ) -> None: ...
    def _copy_data(self) -> dict[str, Any]: ...
    def __repr__(self) -> str: ...
