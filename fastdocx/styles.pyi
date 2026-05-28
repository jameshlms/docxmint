from collections.abc import Iterator
from typing import Literal

class Style:
    @property
    def name(self) -> str: ...
    @name.setter
    def name(self, value: str) -> None: ...
    @property
    def type(self) -> Literal["paragraph", "character", "table", "numbering"]: ...
    @type.setter
    def type(self, value: Literal["paragraph", "character", "table", "numbering"]) -> None: ...
    @property
    def based_on(self) -> str | None: ...
    @based_on.setter
    def based_on(self, value: str | None) -> None: ...
    @property
    def next_style(self) -> str | None: ...
    @next_style.setter
    def next_style(self, value: str | None) -> None: ...
    @property
    def is_default(self) -> bool: ...
    @is_default.setter
    def is_default(self, value: bool) -> None: ...

    # Character formatting
    @property
    def bold(self) -> bool: ...
    @bold.setter
    def bold(self, value: bool) -> None: ...
    @property
    def italic(self) -> bool: ...
    @italic.setter
    def italic(self, value: bool) -> None: ...
    @property
    def underline(self) -> Literal["single", "double", "dotted", "dashed", "wave"] | None: ...
    @underline.setter
    def underline(
        self,
        value: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None,
    ) -> None: ...
    @property
    def color(self) -> str | None: ...
    @color.setter
    def color(self, value: str | None) -> None: ...

    font_name: str
    font_size: float

    # Paragraph formatting
    @property
    def alignment(self) -> Literal["left", "right", "center", "justify"] | None: ...
    @alignment.setter
    def alignment(self, value: Literal["left", "right", "center", "justify"] | None) -> None: ...

    space_before: float
    space_after: float
    line_spacing: float
    indent_left: float
    indent_right: float
    indent_hanging: float

    def __repr__(self) -> str: ...

class StyleCollection:
    @property
    def default(self) -> Style | None: ...
    def __getitem__(self, name: str) -> Style: ...
    def __contains__(self, name: object) -> bool: ...
    def __iter__(self) -> Iterator[Style]: ...
    def __len__(self) -> int: ...
    def register(
        self,
        name: str,
        *,
        type: Literal["paragraph", "character", "table", "numbering"] = ...,
        based_on: str | None = ...,
        next_style: str | None = ...,
        style_id: str | None = ...,
        bold: bool = ...,
        italic: bool = ...,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None = ...,
        color: str | None = ...,
        font_name: str = ...,
        font_size: float = ...,
        alignment: Literal["left", "right", "center", "justify"] | None = ...,
        space_before: float = ...,
        space_after: float = ...,
        line_spacing: float = ...,
        indent_left: float = ...,
        indent_right: float = ...,
        indent_hanging: float = ...,
    ) -> Style: ...
    def __repr__(self) -> str: ...
