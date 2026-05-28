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
        self._errors: dict[str, Exception] = {}

    def inject_error(self, method: str, error: Exception) -> None:
        """Cause every call to *method* to raise *error* until cleared."""
        self._errors[method] = error

    def clear_error(self, method: str) -> None:
        """Remove a previously injected error for *method*."""
        self._errors.pop(method, None)

    def _check_error(self, method: str) -> None:
        if method in self._errors:
            raise self._errors[method]

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

    # Collections that contain more than one element type (reserved for future use).
    _MULTI_COLLECTION_TYPES: dict[str, frozenset[str]] = {}

    def _collection_type(self, collection: str) -> str:
        return {
            "paragraphs": "paragraph",
            "tables": "table",
            "rows": "row",
            "cells": "cell",
            "runs": "run",
            "images": "image",
            "hyperlinks": "hyperlink",
            "sections": "section",
            "body": "",
        }.get(collection, collection.rstrip("s"))

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def create_document(self) -> int:
        self._check_error("create_document")
        return self._alloc("document")

    def open_document(self, path: str) -> int:
        self._check_error("open_document")
        h = self._alloc("document")
        self._handles[h]["path"] = path
        return h

    def edit_document(self, path: str) -> int:
        self._check_error("edit_document")
        return self.open_document(path)

    def save_document(self, handle: int, path: str) -> None:
        self._check_error("save_document")
        self._handles[handle]["path"] = path

    def dispose(self, handle: int) -> None:
        self._handles.pop(handle, None)
        self._children.pop(handle, None)
        self._types.pop(handle, None)

    # ------------------------------------------------------------------
    # Generic property access
    # ------------------------------------------------------------------

    def get_int(self, handle: int, name: str) -> int:
        self._check_error("get_int")
        val = self._handles.get(handle, {}).get(name)
        if val is None:
            return -1
        return int(val)

    def set_int(self, handle: int, name: str, value: int) -> None:
        self._check_error("set_int")
        if handle not in self._handles:
            raise RuntimeError(f"Invalid handle {handle}")
        self._handles[handle][name] = value

    def get_float(self, handle: int, name: str) -> float:
        self._check_error("get_float")
        val = self._handles.get(handle, {}).get(name)
        if val is None:
            return 0.0
        return float(val)

    def set_float(self, handle: int, name: str, value: float) -> None:
        self._check_error("set_float")
        if handle not in self._handles:
            raise RuntimeError(f"Invalid handle {handle}")
        self._handles[handle][name] = value

    def get_str(self, handle: int, name: str) -> str:
        self._check_error("get_str")
        if name == "text" and self._types.get(handle) == "paragraph":
            parts = []
            for h in self._children.get(handle, []):
                t = self._types.get(h)
                if t == "run":
                    parts.append(self._handles.get(h, {}).get("text", ""))
                elif t == "break":
                    parts.append("\n")
            return "".join(parts)
        val = self._handles.get(handle, {}).get(name)
        if val is None:
            return ""
        return str(val)

    def set_str(self, handle: int, name: str, value: str) -> None:
        self._check_error("set_str")
        if handle not in self._handles:
            raise RuntimeError(f"Invalid handle {handle}")
        if name == "text" and self._types.get(handle) == "paragraph":
            # Replace all run children with a single run (mirrors native behaviour)
            for child_h in list(self._children.get(handle, [])):
                if self._types.get(child_h) == "run":
                    self._children[handle].remove(child_h)
                    self._handles.pop(child_h, None)
                    self._types.pop(child_h, None)
                    self._parent.pop(child_h, None)
            run_h = self._alloc("run")
            self._children.setdefault(handle, []).append(run_h)
            self._parent[run_h] = handle
            self._handles[run_h]["text"] = value
            return
        self._handles[handle][name] = value

    # ------------------------------------------------------------------
    # Collection operations
    # ------------------------------------------------------------------

    def get_count(self, handle: int, collection: str) -> int:
        self._check_error("get_count")
        if handle not in self._children:
            return 0
        if collection == "body":
            return len(self._children[handle])
        multi = self._MULTI_COLLECTION_TYPES.get(collection)
        if multi is not None:
            return sum(1 for h in self._children[handle] if self._types.get(h) in multi)
        type_name = self._collection_type(collection)
        return sum(
            1 for h in self._children[handle]
            if self._types.get(h) == type_name
        )

    def get_child_handle(self, handle: int, collection: str, index: int) -> int:
        children = self._children.get(handle, [])

        # Named style lookup: "style:{id}" — find by style_id property
        if collection.startswith("style:"):
            style_id = collection[6:]
            for h in children:
                if (
                    self._types.get(h) == "style"
                    and self._handles.get(h, {}).get("style_id") == style_id
                ):
                    return h
            return 0

        # Default style lookup
        if collection == "default_style":
            for h in children:
                if (
                    self._types.get(h) == "style"
                    and self._handles.get(h, {}).get("is_default") == 1
                ):
                    return h
            return 0

        if collection == "body":
            matching = children
        else:
            multi = self._MULTI_COLLECTION_TYPES.get(collection)
            if multi is not None:
                matching = [h for h in children if self._types.get(h) in multi]
            else:
                type_name = self._collection_type(collection)
                matching = [h for h in children if self._types.get(h) == type_name]
        if index < 0:
            index = len(matching) + index
        if 0 <= index < len(matching):
            return matching[index]
        return 0

    def get_element_type(self, handle: int) -> str:
        self._check_error("get_element_type")
        return self._types.get(handle, "unknown")

    def append_child(self, parent: int, child_type: str) -> int:
        self._check_error("append_child")
        h = self._alloc(child_type)
        self._children.setdefault(parent, []).append(h)
        self._parent[h] = parent
        return h

    def remove_child(self, handle: int) -> None:
        self._check_error("remove_child")
        parent = self._parent.pop(handle, None)
        if parent is not None and parent in self._children:
            self._children[parent] = [
                h for h in self._children[parent] if h != handle
            ]
        self._handles.pop(handle, None)
        self._children.pop(handle, None)
        self._types.pop(handle, None)

    def add_image(
        self,
        parent: int,
        data: bytes,
        content_type: str,
        width_emu: int,
        height_emu: int,
    ) -> int:
        self._check_error("add_image")
        h = self._alloc("image")
        self._handles[h]["_image_data"] = data
        self._handles[h]["content_type"] = content_type
        self._handles[h]["width_emu"] = width_emu
        self._handles[h]["height_emu"] = height_emu
        self._handles[h]["width"] = width_emu / 914400
        self._handles[h]["height"] = height_emu / 914400
        self._children.setdefault(parent, []).append(h)
        self._parent[h] = parent
        return h

    def get_image_data(self, handle: int) -> bytes:
        self._check_error("get_image_data")
        return self._handles.get(handle, {}).get("_image_data", b"")

    def add_table(self, doc_handle: int, rows: int, cols: int) -> int:
        self._check_error("add_table")
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
