from __future__ import annotations

from typing import TYPE_CHECKING

from fastdocx.errors import NativeRuntimeError

if TYPE_CHECKING:
    from fastdocx._native.bindings import NativeLib


class Cell:
    """A single cell within a :class:`Table`.

    Assign to ``cell.text`` to update the cell contents.
    """

    def __init__(self, table_handle: int, row: int, col: int, lib: NativeLib) -> None:
        self._table_handle = table_handle
        self._row = row
        self._col = col
        self._lib = lib
        self._text = ""

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        encoded = value.encode("utf-8")
        rc = self._lib.set_cell_text(
            self._table_handle,
            self._row,
            self._col,
            encoded,
            len(encoded),
        )
        if rc != 0:
            raise NativeRuntimeError(f"set_cell_text failed for cell ({self._row}, {self._col})")
        self._text = value

    def __repr__(self) -> str:
        return f"Cell(row={self._row!r}, col={self._col!r}, text={self._text!r})"


class Table:
    """Represents a table element in a DOCX document.

    Use ``table[row, col]`` to retrieve a :class:`Cell` and assign to its
    ``text`` property to set cell content.
    """

    def __init__(self, handle: int, rows: int, cols: int, lib: NativeLib) -> None:
        self._handle = handle
        self._rows = rows
        self._cols = cols
        self._lib = lib
        self._cells: list[Cell | None] = [None] * (rows * cols)

    @property
    def handle(self) -> int:
        return self._handle

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    def __getitem__(self, index: tuple[int, int]) -> Cell:
        row, col = index
        if not (0 <= row < self._rows and 0 <= col < self._cols):
            raise IndexError(
                f"Table index ({row}, {col}) out of range for {self._rows}x{self._cols} table"
            )
        flat = row * self._cols + col
        if self._cells[flat] is None:
            self._cells[flat] = Cell(self._handle, row, col, self._lib)
        return self._cells[flat]  # type: ignore[return-value]

    def __repr__(self) -> str:
        return f"Table(handle={self._handle!r}, rows={self._rows!r}, cols={self._cols!r})"
