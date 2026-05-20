"""Mock FFI handle for unit tests.

Stores all document data in Python dicts — no compiled C# binary needed.
"""
from __future__ import annotations

from typing import Any


class MockHandle:
    """In-memory simulation of the native Handle interface."""

    def __init__(self) -> None:
        self._handles: dict[int, dict[str, Any]] = {}
        self._children: dict[int, list[int]] = {}
        self._types: dict[int, str] = {}
        self._parent: dict[int, int] = {}
        self._next = 1

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _alloc(self, type_name: str) -> int:
        h = self._next
        self._next += 1
        self._handles[h] = {}
        self._types[h] = type_name
        self._children[h] = []
        return h

    def _collection_type(self, collection: str) -> str:
        return {
            "paragraphs": "paragraph",
            "tables": "table",
            "rows": "row",
            "cells": "cell",
            "runs": "run",
            "sections": "section",
            "body": "",
        }.get(collection, collection.rstrip("s"))

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def create_document(self) -> int:
        return self._alloc("document")

    def open_document(self, path: str) -> int:
        h = self._alloc("document")
        self._handles[h]["path"] = path
        return h

    def edit_document(self, path: str) -> int:
        return self.open_document(path)

    def save_document(self, handle: int, path: str) -> None:
        self._handles[handle]["path"] = path

    def dispose(self, handle: int) -> None:
        self._handles.pop(handle, None)
        self._children.pop(handle, None)
        self._types.pop(handle, None)

    # ------------------------------------------------------------------
    # Generic property access
    # ------------------------------------------------------------------

    def get_int(self, handle: int, name: str) -> int:
        val = self._handles.get(handle, {}).get(name)
        if val is None:
            return -1
        return int(val)

    def set_int(self, handle: int, name: str, value: int) -> None:
        if handle not in self._handles:
            raise RuntimeError(f"Invalid handle {handle}")
        self._handles[handle][name] = value

    def get_float(self, handle: int, name: str) -> float:
        val = self._handles.get(handle, {}).get(name)
        if val is None:
            return 0.0
        return float(val)

    def set_float(self, handle: int, name: str, value: float) -> None:
        if handle not in self._handles:
            raise RuntimeError(f"Invalid handle {handle}")
        self._handles[handle][name] = value

    def get_str(self, handle: int, name: str) -> str:
        val = self._handles.get(handle, {}).get(name)
        if val is None:
            return ""
        return str(val)

    def set_str(self, handle: int, name: str, value: str) -> None:
        if handle not in self._handles:
            raise RuntimeError(f"Invalid handle {handle}")
        self._handles[handle][name] = value

    # ------------------------------------------------------------------
    # Collection operations
    # ------------------------------------------------------------------

    def get_count(self, handle: int, collection: str) -> int:
        if handle not in self._children:
            return 0
        if collection == "body":
            return len(self._children[handle])
        type_name = self._collection_type(collection)
        return sum(
            1 for h in self._children[handle]
            if self._types.get(h) == type_name
        )

    def get_child_handle(self, handle: int, collection: str, index: int) -> int:
        children = self._children.get(handle, [])
        if collection == "body":
            matching = children
        else:
            type_name = self._collection_type(collection)
            matching = [h for h in children if self._types.get(h) == type_name]
        if index < 0:
            index = len(matching) + index
        if 0 <= index < len(matching):
            return matching[index]
        return 0

    def get_element_type(self, handle: int) -> str:
        return self._types.get(handle, "unknown")

    def append_child(self, parent: int, child_type: str) -> int:
        h = self._alloc(child_type)
        self._children.setdefault(parent, []).append(h)
        self._parent[h] = parent
        return h

    def remove_child(self, handle: int) -> None:
        parent = self._parent.pop(handle, None)
        if parent is not None and parent in self._children:
            self._children[parent] = [
                h for h in self._children[parent] if h != handle
            ]
        self._handles.pop(handle, None)
        self._children.pop(handle, None)
        self._types.pop(handle, None)

    def add_table(self, doc_handle: int, rows: int, cols: int) -> int:
        h = self._alloc("table")
        self._handles[h]["rows"] = rows
        self._handles[h]["cols"] = cols
        self._children.setdefault(doc_handle, []).append(h)
        self._parent[h] = doc_handle
        for r in range(rows):
            row_h = self._alloc("row")
            self._children[h].append(row_h)
            self._parent[row_h] = h
            for c in range(cols):
                cell_h = self._alloc("cell")
                self._children[row_h].append(cell_h)
                self._parent[cell_h] = row_h
        return h

    def set_many(self, handle: int, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if value is None:
                continue
            self._handles.setdefault(handle, {})[name] = value
