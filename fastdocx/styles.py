"""Style and StyleCollection."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from fastdocx._native.handle import Handle
    from fastdocx.document import Document


class Style:
    """A document style definition — always live, backed by a native handle.

    Obtained from :class:`StyleCollection` via ``doc.styles["Heading1"]`` or
    by iterating ``doc.styles``, or created via ``doc.styles.register("My Style")``.

    Metadata properties (read/write):

    - ``name`` — display name (e.g. ``"Heading 1"``)
    - ``type`` — ``"paragraph"``, ``"character"``, ``"table"``, or ``"numbering"``
    - ``based_on`` — parent style name/id, or ``None``
    - ``next_style`` — style for the following paragraph, or ``None``
    - ``is_default`` — ``True`` if this is the document's default paragraph style

    Character formatting (read/write, stored in the style's ``<w:rPr>``):

    - ``bold``, ``italic``, ``underline``, ``color``, ``font_name``, ``font_size``

    Paragraph formatting (read/write, stored in the style's ``<w:pPr>``):

    - ``alignment``, ``space_before``, ``space_after``, ``line_spacing``
    - ``indent_left``, ``indent_right``, ``indent_hanging``
    """

    def __init__(self, handle: int, doc: Document) -> None:
        self._handle = handle
        self._doc = doc

    def _lib(self) -> Handle:
        return self._doc._lib

    # ------------------------------------------------------------------
    # Metadata — read/write
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._lib().get_str(self._handle, "style_name")

    @name.setter
    def name(self, value: str) -> None:
        self._lib().set_str(self._handle, "style_name", value)

    @property
    def type(self) -> Literal["paragraph", "character", "table", "numbering"]:
        val = self._lib().get_str(self._handle, "style_type")
        return val or "paragraph"  # type: ignore[return-value]

    @type.setter
    def type(self, value: Literal["paragraph", "character", "table", "numbering"]) -> None:
        self._lib().set_str(self._handle, "style_type", value)

    @property
    def based_on(self) -> str | None:
        val = self._lib().get_str(self._handle, "based_on")
        return val or None

    @based_on.setter
    def based_on(self, value: str | None) -> None:
        self._lib().set_str(self._handle, "based_on", value or "")

    @property
    def next_style(self) -> str | None:
        val = self._lib().get_str(self._handle, "next_style")
        return val or None

    @next_style.setter
    def next_style(self, value: str | None) -> None:
        self._lib().set_str(self._handle, "next_style", value or "")

    @property
    def is_default(self) -> bool:
        return bool(self._lib().get_int(self._handle, "is_default"))

    @is_default.setter
    def is_default(self, value: bool) -> None:
        self._lib().set_int(self._handle, "is_default", int(bool(value)))

    # ------------------------------------------------------------------
    # Character formatting — read/write
    # ------------------------------------------------------------------

    @property
    def bold(self) -> bool:
        rc = self._lib().get_int(self._handle, "bold")
        return bool(rc) if rc >= 0 else False

    @bold.setter
    def bold(self, value: bool) -> None:
        self._lib().set_int(self._handle, "bold", int(bool(value)))

    @property
    def italic(self) -> bool:
        rc = self._lib().get_int(self._handle, "italic")
        return bool(rc) if rc >= 0 else False

    @italic.setter
    def italic(self, value: bool) -> None:
        self._lib().set_int(self._handle, "italic", int(bool(value)))

    @property
    def underline(self) -> Literal["single", "double", "dotted", "dashed", "wave"] | None:
        val = self._lib().get_str(self._handle, "underline")
        return val or None  # type: ignore[return-value]

    @underline.setter
    def underline(
        self,
        value: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None,
    ) -> None:
        if value is True:
            value = "single"
        elif value is False:
            value = None
        self._lib().set_str(self._handle, "underline", value or "")

    @property
    def color(self) -> str | None:
        val = self._lib().get_str(self._handle, "color")
        if not val:
            return None
        return f"#{val}" if val != "auto" else "auto"

    @color.setter
    def color(self, value: str | None) -> None:
        from fastdocx.units import Color

        normalized = Color._normalize(value) if value is not None else ""
        self._lib().set_str(self._handle, "color", normalized)

    @property
    def font_name(self) -> str:
        return self._lib().get_str(self._handle, "font_name")

    @font_name.setter
    def font_name(self, value: str) -> None:
        self._lib().set_str(self._handle, "font_name", value)

    @property
    def font_size(self) -> float:
        return self._lib().get_float(self._handle, "font_size")

    @font_size.setter
    def font_size(self, value: float) -> None:
        self._lib().set_float(self._handle, "font_size", float(value))

    # ------------------------------------------------------------------
    # Paragraph formatting — read/write
    # ------------------------------------------------------------------

    @property
    def alignment(self) -> Literal["left", "right", "center", "justify"] | None:
        val = self._lib().get_str(self._handle, "alignment")
        return val or None  # type: ignore[return-value]

    @alignment.setter
    def alignment(self, value: Literal["left", "right", "center", "justify"] | None) -> None:
        self._lib().set_str(self._handle, "alignment", value or "")

    @property
    def space_before(self) -> float:
        return self._lib().get_float(self._handle, "space_before")

    @space_before.setter
    def space_before(self, value: float) -> None:
        self._lib().set_float(self._handle, "space_before", float(value))

    @property
    def space_after(self) -> float:
        return self._lib().get_float(self._handle, "space_after")

    @space_after.setter
    def space_after(self, value: float) -> None:
        self._lib().set_float(self._handle, "space_after", float(value))

    @property
    def line_spacing(self) -> float:
        return self._lib().get_float(self._handle, "line_spacing")

    @line_spacing.setter
    def line_spacing(self, value: float) -> None:
        self._lib().set_float(self._handle, "line_spacing", float(value))

    @property
    def indent_left(self) -> float:
        return self._lib().get_float(self._handle, "indent_left")

    @indent_left.setter
    def indent_left(self, value: float) -> None:
        self._lib().set_float(self._handle, "indent_left", float(value))

    @property
    def indent_right(self) -> float:
        return self._lib().get_float(self._handle, "indent_right")

    @indent_right.setter
    def indent_right(self, value: float) -> None:
        self._lib().set_float(self._handle, "indent_right", float(value))

    @property
    def indent_hanging(self) -> float:
        return self._lib().get_float(self._handle, "indent_hanging")

    @indent_hanging.setter
    def indent_hanging(self, value: float) -> None:
        self._lib().set_float(self._handle, "indent_hanging", float(value))

    def __repr__(self) -> str:
        try:
            return f"Style({self.name!r})"
        except Exception:
            return "Style(<error>)"


class StyleCollection:
    """Live view over all styles defined in a document.

    Obtained via :attr:`~fastdocx.document.Document.styles`:

    .. code-block:: python

        styles = doc.styles
        heading = styles["Heading1"]
        for style in styles:
            print(style.name, style.type)

    Supports ``len()``, iteration, ``in`` (by style name/id), dict-style
    lookup by name/id, and :meth:`add` for creating new styles.

    Raises:
        KeyError: When a style name is not found.
    """

    def __init__(self, doc_handle: int, doc: Document) -> None:
        self._doc_handle = doc_handle
        self._doc = doc

    def _lib(self) -> Handle:
        return self._doc._get_lib()

    @property
    def default(self) -> Style | None:
        try:
            h = self._lib().get_child_handle(self._doc_handle, "default_style", 0)
            return Style(h, self._doc)
        except Exception:
            return None

    def __getitem__(self, name: str) -> Style:
        try:
            h = self._lib().get_child_handle(self._doc_handle, f"style:{name}", 0)
            return Style(h, self._doc)
        except Exception:
            raise KeyError(name) from None

    def __contains__(self, name: object) -> bool:
        try:
            self[str(name)]
            return True
        except KeyError:
            return False

    def __iter__(self) -> Iterator[Style]:
        try:
            n = self._lib().get_count(self._doc_handle, "styles")
        except Exception:
            return
        for i in range(n):
            try:
                h = self._lib().get_child_handle(self._doc_handle, "styles", i)
                yield Style(h, self._doc)
            except Exception:
                pass

    def __len__(self) -> int:
        try:
            return self._lib().get_count(self._doc_handle, "styles")
        except Exception:
            return 0

    def register(
        self,
        name: str,
        *,
        type: Literal["paragraph", "character", "table", "numbering"] = "paragraph",
        based_on: str | None = None,
        next_style: str | None = None,
        style_id: str | None = None,
        # Character formatting
        bold: bool = False,
        italic: bool = False,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None = None,
        color: str | None = None,
        font_name: str = "",
        font_size: float = 0.0,
        # Paragraph formatting
        alignment: Literal["left", "right", "center", "justify"] | None = None,
        space_before: float = 0.0,
        space_after: float = 0.0,
        line_spacing: float = 0.0,
        indent_left: float = 0.0,
        indent_right: float = 0.0,
        indent_hanging: float = 0.0,
    ) -> Style:
        """Create and register a new style in the document.

        Args:
            name: Display name for the style (e.g. ``"My Heading"``).
            type: Style type — ``"paragraph"`` (default), ``"character"``,
                ``"table"``, or ``"numbering"``.
            based_on: Style name or id to inherit from (e.g. ``"Normal"``).
            next_style: Style applied to the next paragraph when Enter is
                pressed (paragraph styles only).
            style_id: Internal id used in markup; defaults to *name* with
                spaces removed.
            bold: Bold weight.
            italic: Italic style.
            underline: ``True`` for single underline, or a named style
                (``"single"``, ``"double"``, ``"dotted"``, ``"dashed"``, ``"wave"``).
            color: Text colour as ``"#RRGGBB"`` or ``"auto"``.
            font_name: Font family name.
            font_size: Font size in points.
            alignment: Paragraph alignment — ``"left"``, ``"right"``,
                ``"center"``, or ``"justify"``.
            space_before: Space before paragraph in points.
            space_after: Space after paragraph in points.
            line_spacing: Line spacing multiplier (e.g. ``1.5``).
            indent_left: Left indent in inches.
            indent_right: Right indent in inches.
            indent_hanging: Hanging indent in inches.

        Returns:
            The newly created :class:`Style` object.
        """
        lib = self._lib()
        h = lib.append_child(self._doc_handle, "style")
        if style_id is None:
            style_id = name.replace(" ", "")
        lib.set_str(h, "style_id", style_id)
        lib.set_str(h, "style_name", name)
        lib.set_str(h, "style_type", type)
        if based_on is not None:
            lib.set_str(h, "based_on", based_on)
        if next_style is not None:
            lib.set_str(h, "next_style", next_style)

        style = Style(h, self._doc)

        if bold:
            style.bold = True
        if italic:
            style.italic = True
        if underline is not None and underline is not False:
            style.underline = underline
        if color is not None:
            style.color = color
        if font_name:
            style.font_name = font_name
        if font_size:
            style.font_size = font_size
        if alignment is not None:
            style.alignment = alignment
        if space_before:
            style.space_before = space_before
        if space_after:
            style.space_after = space_after
        if line_spacing:
            style.line_spacing = line_spacing
        if indent_left:
            style.indent_left = indent_left
        if indent_right:
            style.indent_right = indent_right
        if indent_hanging:
            style.indent_hanging = indent_hanging

        return style

    def __repr__(self) -> str:
        try:
            return f"StyleCollection(len={len(self)})"
        except Exception:
            return "StyleCollection(<error>)"
