"""Table, Row, and Cell proxy types."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Literal, overload

from fastdocx._block import BlockContainerMixin
from fastdocx._proxy.base import ProxyBase
from fastdocx._proxy.descriptors import ChoiceProperty, FloatProperty, StringProperty
from fastdocx.collection import DocumentView

if TYPE_CHECKING:
    from fastdocx.paragraph import Paragraph


class Cell(BlockContainerMixin, ProxyBase):
    """A single table cell."""

    _child_type_name = "cell"

    text = StringProperty("text", default="")
    width = FloatProperty("width", default=0.0)  # inches
    vertical_alignment: ChoiceProperty[Literal["top", "center", "bottom"]] = ChoiceProperty(
        "vertical_alignment", ("top", "center", "bottom"), default="top"
    )
    merge_up = StringProperty("merge_up", default="")  # "restart" | "continue" | ""
    merge_left = StringProperty("merge_left", default="")

    def __init__(self) -> None:
        super().__init__()

    def _block_context(self) -> tuple[int, Any, Any] | None:
        if not self._is_live:
            return None
        self._check_valid()
        return (self._getattr("_native"), self._get_lib(), self._getattr("_document"))

    @property
    def tables(self) -> DocumentView[Table]:  # type: ignore[override]
        return []  # type: ignore[return-value]  # nested tables not yet wired in v1

    @tables.setter
    def tables(self, _: object) -> None:
        pass

    def add_table(self, rows: int, cols: int, style: str = "TableGrid") -> Table:  # type: ignore[override]
        raise NotImplementedError("Nested tables inside cells are not yet supported in v1.")

    def merge(self, other: Cell) -> None:
        raise NotImplementedError("Cell.merge() is not yet implemented in v1.")

    def _copy_data(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "width": self.width,
            "vertical_alignment": self.vertical_alignment,
        }

    def __repr__(self) -> str:
        native = self._getattr("_native")
        if native is None:
            return "Cell(spec)"
        if self._getattr("_stale"):
            return "Cell(<stale>)"
        try:
            return f"Cell(text={self.text!r}, handle={native!r})"
        except Exception:
            return f"Cell(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        try:
            return len(self.paragraphs)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Paragraph]:
        return iter(self.paragraphs)


class Row(ProxyBase):
    """A table row."""

    _child_type_name = "row"

    height = FloatProperty("height", default=0.0)  # points, 0 = auto
    height_rule: ChoiceProperty[Literal["auto", "exact", "atLeast"]] = ChoiceProperty(
        "height_rule", ("auto", "exact", "atLeast"), default="auto"
    )
    is_header = StringProperty("is_header", default="")
    cant_split = StringProperty("cant_split", default="")

    def __init__(self) -> None:
        super().__init__()

    @property
    def cells(self) -> DocumentView[Cell]:
        if not self._is_live:
            return []  # type: ignore[return-value]
        self._check_valid()
        return DocumentView(
            self._getattr("_native"),
            self._getattr("_document"),
            self._get_lib(),
            (Cell,),
            "cells",
        )

    def _copy_data(self) -> dict[str, Any]:
        return {
            "height": self.height,
            "height_rule": self.height_rule,
        }

    def __repr__(self) -> str:
        native = self._getattr("_native")
        if native is None:
            return "Row(spec)"
        if self._getattr("_stale"):
            return "Row(<stale>)"
        return f"Row(handle={native!r})"

    def __bool__(self) -> bool:
        try:
            return len(self.cells) > 0
        except Exception:
            return False

    def __len__(self) -> int:
        try:
            return len(self.cells)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Cell]:
        return iter(self.cells)

    def __getitem__(self, index: int) -> Cell:
        return self.cells[index]


class Table(ProxyBase):
    """A table element — either a live proxy or a construction object.

    **Construction**::

        table = Table(rows=3, cols=4, style="TableGrid")
        doc.tables.append(table)

    **Live proxy** (from doc.tables[i])::

        table = doc.tables[0]
        table.cell(0, 0).text = "Header"
    """

    _child_type_name = "table"

    style = StringProperty("style", default="TableGrid")
    alignment: ChoiceProperty[Literal["left", "center", "right"]] = ChoiceProperty(
        "alignment", ("left", "center", "right")
    )
    width = FloatProperty("width", default=0.0)  # inches
    indent = FloatProperty("indent", default=0.0)  # left indent, inches
    cell_spacing = FloatProperty("cell_spacing", default=0.0)  # points

    def __init__(
        self,
        rows: int,
        cols: int,
        *,
        style: str = "TableGrid",
    ) -> None:
        super().__init__()
        data: dict[str, Any] = {"rows": rows, "cols": cols}
        if style != "TableGrid":
            data["style"] = style
        self._setattr("_data", data)

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    @property
    def rows(self) -> DocumentView[Row]:
        if not self._is_live:
            return []  # type: ignore[return-value]
        self._check_valid()
        return DocumentView(
            self._getattr("_native"),
            self._getattr("_document"),
            self._get_lib(),
            (Row,),
            "rows",
        )

    @property
    def columns(self) -> DocumentView[Row]:
        raise NotImplementedError("Table.columns is not yet implemented in v1.")

    @property
    def cells(self) -> DocumentView[Cell]:
        if not self._is_live:
            return []  # type: ignore[return-value]
        self._check_valid()
        return DocumentView(
            self._getattr("_native"),
            self._getattr("_document"),
            self._get_lib(),
            (Cell,),
            "cells",
        )

    @property
    def data(self) -> list[list[str]]:
        """Plain text grid — plug directly into a DataFrame constructor."""
        if not self._is_live:
            return []
        result: list[list[str]] = []
        for row in self.rows:
            result.append([cell.text for cell in row.cells])
        return result

    def cell(self, row: int, col: int) -> Cell:
        """Return the cell at (row, col)."""
        if not self._is_live:
            raise ValueError("Cannot access cell on a construction-object Table.")
        self._check_valid()
        return self.rows[row].cells[col]

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._getattr("_data"))
        return {
            "style": self.style,
            "alignment": self.alignment,
        }

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        native = self._getattr("_native")
        if native is None:
            d = self._getattr("_data")
            return f"Table(rows={d.get('rows')}, cols={d.get('cols')})"
        if self._getattr("_stale"):
            return "Table(<stale>)"
        try:
            return f"Table(rows={len(self.rows)}, handle={native!r})"
        except Exception:
            return f"Table(handle={native!r})"

    def __bool__(self) -> bool:
        try:
            return len(self.rows) > 0
        except Exception:
            return False

    def __len__(self) -> int:
        try:
            return len(self.rows)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Row]:
        return iter(self.rows)

    def __contains__(self, row: object) -> bool:
        return row in self.rows

    @overload
    def __getitem__(self, index: int) -> Row: ...
    @overload
    def __getitem__(self, index: tuple[int, int]) -> Cell: ...

    def __getitem__(self, index: int | tuple[int, int]) -> Row | Cell:
        if isinstance(index, tuple):
            row, col = index
            return self.cell(row, col)
        return self.rows[index]
