from collections.abc import Iterator
from typing import Literal, Self

from fastdocx._proxy.base import ProxyBase
from fastdocx.collection import DocumentView
from fastdocx.run import Run

class Paragraph(ProxyBase):
    text: str
    style: str
    alignment: Literal["left", "right", "center", "justify"] | None
    keep_together: bool
    keep_with_next: bool
    page_break_before: bool

    def __init__(
        self,
        text: str = ...,
        *,
        style: str = ...,
        alignment: Literal["left", "right", "center", "justify"] | None = ...,
        keep_together: bool = ...,
        keep_with_next: bool = ...,
        page_break_before: bool = ...,
    ) -> None: ...
    @classmethod
    def horizontal_line(
        cls,
        style: Literal["single"] = ...,
        width: int = ...,
        color: str = ...,
    ) -> Paragraph: ...
    @property
    def runs(self) -> DocumentView[Run]: ...
    def add_run(self, text: str = ...) -> Run: ...
    def align(self, alignment: Literal["left", "right", "center", "justify"]) -> Self: ...
    def set_style(self, style: str) -> Self: ...
    def copy(self) -> Paragraph: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Run]: ...
    def __contains__(self, run: object) -> bool: ...
