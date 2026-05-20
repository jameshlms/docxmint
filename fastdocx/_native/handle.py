"""All FFI calls live here. The only module that imports ctypes."""

from __future__ import annotations

import ctypes
import platform
from pathlib import Path
from typing import Any

from fastdocx.errors import NativeRuntimeError

_PLATFORM_TO_LIB: dict[tuple[str, str], str] = {
    ("Linux", "x86_64"): "_libs/linux-x64/FastDocx.Native.so",
    ("Linux", "aarch64"): "_libs/linux-arm64/FastDocx.Native.so",
    ("Windows", "AMD64"): "_libs/win-x64/FastDocx.Native.dll",
    ("Windows", "ARM64"): "_libs/win-arm64/FastDocx.Native.dll",
    ("Darwin", "arm64"): "_libs/osx-arm64/FastDocx.Native.dylib",
    ("Darwin", "x86_64"): "_libs/osx-x64/FastDocx.Native.dylib",
}

_BUF_INIT = 256
_cached: Handle | None = None


class Handle:
    """Thin ctypes wrapper around the FastDocx native shared library.

    Exposes the generic property and collection API defined in the spec.
    All other modules call through this class — no ctypes elsewhere.
    """

    def __init__(self, lib_path: str) -> None:
        self._lib = ctypes.CDLL(lib_path)
        self._setup()

    def _setup(self) -> None:
        c = self._lib

        # Document lifecycle
        c.create_document.argtypes = []
        c.create_document.restype = ctypes.c_ssize_t

        c.open_document.argtypes = [ctypes.c_char_p, ctypes.c_int]
        c.open_document.restype = ctypes.c_ssize_t

        c.edit_document.argtypes = [ctypes.c_char_p, ctypes.c_int]
        c.edit_document.restype = ctypes.c_ssize_t

        c.save_document.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int]
        c.save_document.restype = ctypes.c_int

        c.dispose.argtypes = [ctypes.c_ssize_t]
        c.dispose.restype = None

        # Generic property access
        c.get_int.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int]
        c.get_int.restype = ctypes.c_int

        c.set_int.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        c.set_int.restype = ctypes.c_int

        c.get_float.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int]
        c.get_float.restype = ctypes.c_double

        c.set_float.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int, ctypes.c_double]
        c.set_float.restype = ctypes.c_int

        c.get_str.argtypes = [
            ctypes.c_ssize_t,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
        ]
        c.get_str.restype = ctypes.c_int

        c.set_str.argtypes = [
            ctypes.c_ssize_t,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        c.set_str.restype = ctypes.c_int

        # Collection operations
        c.get_count.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int]
        c.get_count.restype = ctypes.c_int

        c.get_child_handle.argtypes = [
            ctypes.c_ssize_t,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_int,
        ]
        c.get_child_handle.restype = ctypes.c_ssize_t

        c.append_child.argtypes = [ctypes.c_ssize_t, ctypes.c_char_p, ctypes.c_int]
        c.append_child.restype = ctypes.c_ssize_t

        c.remove_child.argtypes = [ctypes.c_ssize_t]
        c.remove_child.restype = ctypes.c_int

        c.get_element_type.argtypes = [
            ctypes.c_ssize_t,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
        ]
        c.get_element_type.restype = ctypes.c_int

        # Table-specific (tables require rows/cols at creation)
        c.add_table.argtypes = [ctypes.c_ssize_t, ctypes.c_int, ctypes.c_int]
        c.add_table.restype = ctypes.c_ssize_t

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def create_document(self) -> int:
        h = int(self._lib.create_document())
        if h == 0:
            raise NativeRuntimeError("create_document returned null handle")
        return h

    def open_document(self, path: str) -> int:
        enc = path.encode("utf-8")
        h = int(self._lib.open_document(enc, len(enc)))
        if h == 0:
            raise NativeRuntimeError(f"open_document failed for {path!r}")
        return h

    def edit_document(self, path: str) -> int:
        enc = path.encode("utf-8")
        h = int(self._lib.edit_document(enc, len(enc)))
        if h == 0:
            raise NativeRuntimeError(f"edit_document failed for {path!r}")
        return h

    def save_document(self, handle: int, path: str) -> None:
        enc = path.encode("utf-8")
        rc = int(self._lib.save_document(handle, enc, len(enc)))
        if rc != 0:
            raise NativeRuntimeError(f"save_document failed for {path!r}")

    def dispose(self, handle: int) -> None:
        self._lib.dispose(handle)

    # ------------------------------------------------------------------
    # Generic property access
    # ------------------------------------------------------------------

    def get_int(self, handle: int, name: str) -> int:
        enc = name.encode()
        return int(self._lib.get_int(handle, enc, len(enc)))

    def set_int(self, handle: int, name: str, value: int) -> None:
        enc = name.encode()
        rc = int(self._lib.set_int(handle, enc, len(enc), value))
        if rc != 0:
            raise NativeRuntimeError(f"set_int({name!r}={value}) failed")

    def get_float(self, handle: int, name: str) -> float:
        enc = name.encode()
        val = float(self._lib.get_float(handle, enc, len(enc)))
        if val != val:  # NaN signals error
            raise NativeRuntimeError(f"get_float({name!r}) failed")
        return val

    def set_float(self, handle: int, name: str, value: float) -> None:
        enc = name.encode()
        rc = int(self._lib.set_float(handle, enc, len(enc), value))
        if rc != 0:
            raise NativeRuntimeError(f"set_float({name!r}={value}) failed")

    def get_str(self, handle: int, name: str) -> str:
        enc = name.encode()
        buf_size = _BUF_INIT
        while True:
            buf = ctypes.create_string_buffer(buf_size)
            required = ctypes.c_int(0)
            n = int(self._lib.get_str(handle, enc, len(enc), buf, buf_size, ctypes.byref(required)))
            if n < 0:
                raise NativeRuntimeError(f"get_str({name!r}) failed (rc={n})")
            if n == 0:
                needed = required.value
                if needed == 0:
                    return ""
                buf_size = needed + 1
                continue
            return buf.raw[:n].decode("utf-8")

    def set_str(self, handle: int, name: str, value: str) -> None:
        enc_name = name.encode()
        enc_val = value.encode("utf-8")
        rc = int(self._lib.set_str(handle, enc_name, len(enc_name), enc_val, len(enc_val)))
        if rc != 0:
            raise NativeRuntimeError(f"set_str({name!r}) failed")

    # ------------------------------------------------------------------
    # Collection operations
    # ------------------------------------------------------------------

    def get_count(self, handle: int, collection: str) -> int:
        enc = collection.encode()
        n = int(self._lib.get_count(handle, enc, len(enc)))
        if n < 0:
            raise NativeRuntimeError(f"get_count({collection!r}) failed (rc={n})")
        return n

    def get_child_handle(self, handle: int, collection: str, index: int) -> int:
        enc = collection.encode()
        h = int(self._lib.get_child_handle(handle, enc, len(enc), index))
        if h == 0:
            raise NativeRuntimeError(f"get_child_handle({collection!r}, {index}) failed")
        return h

    def append_child(self, handle: int, child_type: str) -> int:
        enc = child_type.encode()
        h = int(self._lib.append_child(handle, enc, len(enc)))
        if h == 0:
            raise NativeRuntimeError(f"append_child({child_type!r}) failed")
        return h

    def remove_child(self, handle: int) -> None:
        rc = int(self._lib.remove_child(handle))
        if rc != 0:
            raise NativeRuntimeError("remove_child failed")

    def get_element_type(self, handle: int) -> str:
        buf = ctypes.create_string_buffer(64)
        required = ctypes.c_int(0)
        n = int(self._lib.get_element_type(handle, buf, 64, ctypes.byref(required)))
        if n <= 0:
            return "unknown"
        return buf.raw[:n].decode("utf-8")

    def add_table(self, doc_handle: int, rows: int, cols: int) -> int:
        h = int(self._lib.add_table(doc_handle, rows, cols))
        if h == 0:
            raise NativeRuntimeError("add_table failed")
        return h

    # ------------------------------------------------------------------
    # Batch write (used by Run.edit())
    # ------------------------------------------------------------------
    def set_many(self, handle: int, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if value is None:
                continue
            match value:
                case bool():
                    self.set_int(handle, name, int(value))
                case int():
                    self.set_int(handle, name, value)
                case float() if value != 0.0:
                    self.set_float(handle, name, value)
                case str() if value:
                    self.set_str(handle, name, value)
                case _:
                    raise ValueError(f"Unsupported value type for {name!r}: {type(value).__name__}")


def get_handle() -> Handle:
    """Return the lazily-loaded native library handle."""
    global _cached
    if _cached is not None:
        return _cached

    key = (platform.system(), platform.machine())
    rel = _PLATFORM_TO_LIB.get(key)
    if rel is None:
        supported = list(_PLATFORM_TO_LIB.keys())
        raise RuntimeError(
            f"fastdocx: unsupported platform {key[0]!r}/{key[1]!r}. Supported: {supported}"
        )

    lib_path = Path(__file__).parent.parent / rel
    if not lib_path.exists():
        raise RuntimeError(
            f"fastdocx: native binary not found at {lib_path}.\n"
            f"Build with: dotnet publish native/FastDocx.Native -r <rid> -c Release"
        )

    _cached = Handle(str(lib_path))
    return _cached
