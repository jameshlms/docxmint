from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


class Color:
    """Represents a color in RGB format."""

    def __init__(self, r: int, g: int, b: int) -> None:
        if not all(isinstance(c, int) and 0 <= c <= 255 for c in (r, g, b)):
            raise ValueError(
                f"Color components must be integers in the range 0-255, got ({r}, {g}, {b})"
            )

        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def from_hex(hex_str: str | Sequence[int]) -> Color:
        """Create a Color from a hex string like '#RRGGBB'."""
        if isinstance(hex_str, str):
            if not hex_str.startswith("#") or len(hex_str) != 7:
                raise ValueError(
                    f"Hex color must be a string in the format '#RRGGBB', got {hex_str!r}"
                )
            try:
                return Color(int(hex_str[1:3], 16), int(hex_str[3:5], 16), int(hex_str[5:7], 16))
            except ValueError as e:
                raise ValueError(f"Invalid hex color string: {hex_str!r}") from e
        elif isinstance(hex_str, Sequence):
            if len(hex_str) != 3:
                raise ValueError(f"Hex color must be a sequence of 3 integers, got {hex_str!r}")
            return Color(*hex_str)
        else:
            raise TypeError(
                f"Hex color must be a string or sequence of integers, got {type(hex_str)!r}"
            )

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b})"


def _positive_float(name: str, value: float) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} value must be a number, got {type(value)!r}")
    if value < 0:
        raise ValueError(f"{name} value cannot be negative, got {value}")
    return float(value)


@dataclass(frozen=True)
class _Length:
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _positive_float(type(self).__name__, self.value))

    @property
    def points(self) -> float:
        raise NotImplementedError

    @property
    def twips(self) -> int:
        return round(self.points * 20)

    @property
    def emu(self) -> int:
        return round(self.points * 12700)


@dataclass(frozen=True)
class Inches(_Length):
    """Represents a length in inches."""

    @property
    def points(self) -> float:
        return self.value * 72.0


@dataclass(frozen=True)
class Centimeters(_Length):
    """Represents a length in centimeters."""

    @property
    def points(self) -> float:
        return self.value * 28.3464567


@dataclass(frozen=True)
class Millimeters(_Length):
    """Represents a length in millimeters."""

    @property
    def points(self) -> float:
        return self.value * 2.83464567


@dataclass(frozen=True)
class Twips(_Length):
    """Represents a length in twips (1/20 of a point)."""

    @property
    def points(self) -> float:
        return self.value * 0.05

    @property
    def twips(self) -> int:
        return round(self.value)


@dataclass(frozen=True)
class Points(_Length):
    """Represents a length in points."""

    @property
    def points(self) -> float:
        return self.value


Length = Inches | Centimeters | Millimeters | Twips | Points
