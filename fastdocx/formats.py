"""Plain Python format and value types.

These are pure Python data objects — no C# handles, no FFI.
They are used as property values on proxy objects and returned by copy().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from fastdocx.units import Color

# Backward-compatible alias — prefer Color directly.
RGBColor = Color


# ---------------------------------------------------------------------------
# Paragraph format types
# ---------------------------------------------------------------------------

@dataclass
class IndentFormat:
    """Paragraph indentation in inches."""
    left: float = 0.0
    right: float = 0.0
    first_line: float = 0.0


@dataclass
class SpacingFormat:
    """Paragraph spacing."""
    before: float = 0.0   # points
    after: float = 0.0    # points
    line: float = 0.0     # multiplier (1.0 = single, 1.5 = 1.5×, etc.)
    line_rule: Literal["auto", "exact", "atLeast"] = "auto"


@dataclass
class ListFormat:
    """Raw list/numbering info (v1 exposes only the identifiers)."""
    num_id: int = 0
    level: int = 0


# ---------------------------------------------------------------------------
# Border / Shading
# ---------------------------------------------------------------------------

@dataclass
class Border:
    """A single border line."""
    style: Literal["single", "double", "dotted", "dashed", "wave", "none"] = "none"
    width: float = 0.0    # points
    color: str = "auto"   # "auto" or "RRGGBB"
    spacing: float = 0.0  # points from text
    shadow: bool = False


@dataclass
class ParagraphBorders:
    """All four paragraph border sides."""
    top: Border = field(default_factory=Border)
    bottom: Border = field(default_factory=Border)
    left: Border = field(default_factory=Border)
    right: Border = field(default_factory=Border)


@dataclass
class TableBorders:
    """Table outer and inner borders."""
    top: Border = field(default_factory=Border)
    bottom: Border = field(default_factory=Border)
    left: Border = field(default_factory=Border)
    right: Border = field(default_factory=Border)
    inside_h: Border = field(default_factory=Border)
    inside_v: Border = field(default_factory=Border)


@dataclass
class CellBorders:
    """Cell border sides."""
    top: Border = field(default_factory=Border)
    bottom: Border = field(default_factory=Border)
    left: Border = field(default_factory=Border)
    right: Border = field(default_factory=Border)


@dataclass
class Shading:
    """Background shading."""
    fill: str = "auto"     # "auto" or "RRGGBB"
    color: str = "auto"    # "auto" or "RRGGBB"
    pattern: str = "clear" # "clear", "solid", or percent string


# ---------------------------------------------------------------------------
# Section format types
# ---------------------------------------------------------------------------

@dataclass
class PageMargins:
    """Page margins in inches."""
    top: float = 1.0
    bottom: float = 1.0
    left: float = 1.25
    right: float = 1.25
    header: float = 0.5
    footer: float = 0.5


@dataclass
class ColumnFormat:
    """Section column layout."""
    count: int = 1
    spacing: float = 0.5  # inches
    equal_width: bool = True


# ---------------------------------------------------------------------------
# Table/cell format types
# ---------------------------------------------------------------------------

@dataclass
class CellMargin:
    """Cell content margins in points."""
    top: float = 0.0
    bottom: float = 0.0
    left: float = 0.0
    right: float = 0.0
