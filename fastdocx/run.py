"""Run proxy."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Literal, Self

from fastdocx._proxy.base import ProxyBase
from fastdocx._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    StringProperty,
)
from fastdocx.formats import RGBColor  # backward-compat re-export
from fastdocx.units import Color

if TYPE_CHECKING:
    pass

__all__ = ["Run", "Color", "RGBColor"]


class Run(ProxyBase):
    """A run element — either a live proxy or a construction object.

    **Construction**::

        run = Run("Hello", bold=True, font_name="Arial", font_size=12)
        para.runs.append(run)

    **Live proxy** (from para.runs[i])::

        run = para.runs[0]
        run.bold = True
        run.color = "#FF0000"

    Mutually exclusive pairs raise ValueError if set together:
    - ``all_caps`` and ``small_caps``
    - ``superscript`` and ``subscript``
    - ``emboss`` and ``imprint``
    """

    _child_type_name = "run"

    # Text
    text = StringProperty("text", default="")

    # Formatting — boolean
    bold = BoolProperty("bold")
    italic = BoolProperty("italic")
    strikethrough = BoolProperty("strikethrough")
    all_caps = BoolProperty("all_caps")
    small_caps = BoolProperty("small_caps")
    superscript = BoolProperty("superscript")
    subscript = BoolProperty("subscript")
    hidden = BoolProperty("hidden")
    emboss = BoolProperty("emboss")
    imprint = BoolProperty("imprint")
    outline = BoolProperty("outline")
    shadow = BoolProperty("shadow")
    no_spell_check = BoolProperty("no_spell_check")
    no_grammar_check = BoolProperty("no_grammar_check")

    # Formatting — underline (bool or named style)
    underline: ChoiceProperty[Literal["single", "double", "dotted", "dashed", "wave"]] = (
        ChoiceProperty(
            "underline",
            ("single", "double", "dotted", "dashed", "wave"),
            allow_bool=True,
        )
    )

    # Formatting — colour and highlight
    color = ColorProperty("color")
    highlight: ChoiceProperty[
        Literal[
            "yellow",
            "green",
            "cyan",
            "magenta",
            "blue",
            "red",
            "dark_blue",
            "dark_cyan",
            "dark_green",
            "dark_magenta",
            "dark_red",
            "dark_yellow",
            "dark_gray",
            "light_gray",
            "black",
            "white",
        ]
    ] = ChoiceProperty(
        "highlight",
        (
            "yellow",
            "green",
            "cyan",
            "magenta",
            "blue",
            "red",
            "dark_blue",
            "dark_cyan",
            "dark_green",
            "dark_magenta",
            "dark_red",
            "dark_yellow",
            "dark_gray",
            "light_gray",
            "black",
            "white",
        ),
    )

    # Formatting — font
    font_name = StringProperty("font_name", default="")
    font_name_eastasia = StringProperty("font_name_eastasia", default="")
    font_name_complex = StringProperty("font_name_complex", default="")
    font_size = FloatProperty("font_size", default=0.0)  # points, 0 = inherit
    font_scale = FloatProperty("font_scale", default=100.0)  # percentage
    character_spacing = FloatProperty("character_spacing", default=0.0)  # points
    kerning = FloatProperty("kerning", default=0.0)  # threshold in points
    baseline = FloatProperty("baseline", default=0.0)  # points, positive = up

    # Miscellaneous
    language = StringProperty("language", default="")

    _MUTEX_PAIRS = (
        ("all_caps", "small_caps"),
        ("superscript", "subscript"),
        ("emboss", "imprint"),
    )

    def __init__(
        self,
        text: str = "",
        *,
        bold: bool = False,
        italic: bool = False,
        strikethrough: bool = False,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] = False,
        all_caps: bool = False,
        small_caps: bool = False,
        superscript: bool = False,
        subscript: bool = False,
        hidden: bool = False,
        emboss: bool = False,
        imprint: bool = False,
        outline: bool = False,
        shadow: bool = False,
        color: str | Color | None = None,
        highlight: str | None = None,
        font_name: str = "",
        font_size: float = 0.0,
        language: str = "",
    ) -> None:
        _check_mutex(
            all_caps=all_caps,
            small_caps=small_caps,
            superscript=superscript,
            subscript=subscript,
            emboss=emboss,
            imprint=imprint,
        )
        super().__init__()
        data: dict[str, Any] = {}
        if text:
            data["text"] = text
        if bold:
            data["bold"] = True
        if italic:
            data["italic"] = True
        if strikethrough:
            data["strikethrough"] = True
        if underline:
            data["underline"] = "single" if underline is True else underline
        if all_caps:
            data["all_caps"] = True
        if small_caps:
            data["small_caps"] = True
        if superscript:
            data["superscript"] = True
        if subscript:
            data["subscript"] = True
        if hidden:
            data["hidden"] = True
        if emboss:
            data["emboss"] = True
        if imprint:
            data["imprint"] = True
        if outline:
            data["outline"] = True
        if shadow:
            data["shadow"] = True
        if color is not None:
            if isinstance(color, Color):
                data["color"] = color.to_hex()
            elif color == "auto":
                data["color"] = "auto"
            else:
                try:
                    data["color"] = Color.from_hex(color).to_hex()
                except ValueError:
                    raise ValueError(
                        f"Invalid color {color!r}. "
                        "Use '#RRGGBB', 'RRGGBB', Color(r, g, b), or 'auto'."
                    ) from None
        if highlight:
            data["highlight"] = highlight
        if font_name:
            data["font_name"] = font_name
        if font_size:
            data["font_size"] = font_size
        if language:
            data["language"] = language
        self._setattr("_data", data)

    def set_bold(self, value: bool = True) -> Self:
        self.bold = value
        return self

    def set_italic(self, value: bool = True) -> Self:
        self.italic = value
        return self

    def set_strikethrough(self, value: bool = True) -> Self:
        self.strikethrough = value
        return self

    def set_underline(self, value: bool | str = True) -> Self:
        self.underline = value  # type: ignore[assignment]
        return self

    def set_all_caps(self, value: bool = True) -> Self:
        self.all_caps = value
        return self

    def set_small_caps(self, value: bool = True) -> Self:
        self.small_caps = value
        return self

    def set_superscript(self, value: bool = True) -> Self:
        self.superscript = value
        return self

    def set_subscript(self, value: bool = True) -> Self:
        self.subscript = value
        return self

    def set_hidden(self, value: bool = True) -> Self:
        self.hidden = value
        return self

    def set_color(self, value: str | Color) -> Self:
        self.color = value
        return self

    def set_highlight(self, value: str) -> Self:
        self.highlight = value  # type: ignore[assignment]
        return self

    def set_font(self, name: str, size: float | None = None) -> Self:
        self.font_name = name
        if size is not None:
            self.font_size = size
        return self

    def set_language(self, tag: str) -> Self:
        self.language = tag
        return self

    # ------------------------------------------------------------------
    # edit() — batch writes into a single set_many call
    # ------------------------------------------------------------------

    @contextlib.contextmanager
    def edit(self):
        """Context manager that batches property writes into a single FFI call."""
        if not self._is_live:
            yield self
            return
        self._check_valid()
        pending: dict[str, Any] = {}
        yield _EditProxy(self, pending)
        if pending:
            self._get_lib().set_many(self._getattr("_native"), pending)

    # ------------------------------------------------------------------
    # split() and __add__
    # ------------------------------------------------------------------

    def split(self, index: int) -> tuple[Run, Run]:
        """Split run at character index. Original is left in an undefined state."""
        text = self.text
        a = Run(text[:index])
        b = Run(text[index:])
        data = self._getattr("_data")
        for k, v in data.items():
            if k != "text":
                a._getattr("_data")[k] = v
                b._getattr("_data")[k] = v
        return a, b

    def __add__(self, other: Run) -> Run:
        if type(other) is not Run:
            return NotImplemented
        a_data = self._getattr("_data")
        b_data = other._getattr("_data")
        # Check formatting compatibility (excluding text)
        a_fmt = {k: v for k, v in a_data.items() if k != "text"}
        b_fmt = {k: v for k, v in b_data.items() if k != "text"}
        if a_fmt != b_fmt:
            raise ValueError(
                "Cannot concatenate Runs with different formatting. "
                "Use str concatenation on .text instead."
            )
        return Run(self.text + other.text, **a_fmt)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._getattr("_data"))
        lib = self._get_lib()
        native = self._getattr("_native")

        def get_bool(name: str) -> bool:
            return lib.get_int(native, name) > 0

        def get_str(name: str) -> str:
            try:
                return lib.get_str(native, name) or ""
            except Exception:
                return ""

        def get_str_or_none(name: str) -> str | None:
            try:
                v = lib.get_str(native, name)
                return v if v else None
            except Exception:
                return None

        def get_float(name: str, default: float = 0.0) -> float:
            try:
                return lib.get_float(native, name)
            except Exception:
                return default

        return dict(
            text=get_str("text"),
            bold=get_bool("bold"),
            italic=get_bool("italic"),
            strikethrough=get_bool("strikethrough"),
            underline=get_str_or_none("underline"),
            all_caps=get_bool("all_caps"),
            small_caps=get_bool("small_caps"),
            superscript=get_bool("superscript"),
            subscript=get_bool("subscript"),
            hidden=get_bool("hidden"),
            emboss=get_bool("emboss"),
            imprint=get_bool("imprint"),
            outline=get_bool("outline"),
            shadow=get_bool("shadow"),
            no_spell_check=get_bool("no_spell_check"),
            no_grammar_check=get_bool("no_grammar_check"),
            color=get_str_or_none("color"),
            highlight=get_str_or_none("highlight"),
            font_name=get_str("font_name"),
            font_name_eastasia=get_str("font_name_eastasia"),
            font_name_complex=get_str("font_name_complex"),
            font_size=get_float("font_size"),
            font_scale=get_float("font_scale", 100.0),
            character_spacing=get_float("character_spacing"),
            kerning=get_float("kerning"),
            baseline=get_float("baseline"),
            language=get_str("language"),
        )

    def __repr__(self) -> str:
        native = self._getattr("_native")
        if native is None:
            data = self._getattr("_data")
            text = data.get("text", "")
            return f"Run({text!r})"
        if self._getattr("_stale"):
            return "Run(<stale>)"
        try:
            return f"Run(text={self.text!r}, handle={native!r})"
        except Exception:
            return f"Run(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        return len(self.text)


class _EditProxy:
    """Accumulates property writes; the context manager flushes them via set_many."""

    def __init__(self, run: Run, pending: dict[str, Any]) -> None:
        object.__setattr__(self, "_run", run)
        object.__setattr__(self, "_pending", pending)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        pending: dict[str, Any] = object.__getattribute__(self, "_pending")
        match value:
            case bool():
                pending[name] = int(value)
            case str():
                pending[name] = value
            case float() | int():
                pending[name] = value
            case _:
                raise TypeError(f"Cannot batch-write {name!r}={value!r}")

    def __getattr__(self, name: str) -> Any:
        run: Run = object.__getattribute__(self, "_run")
        return getattr(run, name)


def _check_mutex(**kwargs: bool) -> None:
    pairs = (
        ("all_caps", "small_caps"),
        ("superscript", "subscript"),
        ("emboss", "imprint"),
    )
    for a, b in pairs:
        if kwargs.get(a) and kwargs.get(b):
            raise ValueError(f"{a!r} and {b!r} are mutually exclusive — set only one at a time.")
