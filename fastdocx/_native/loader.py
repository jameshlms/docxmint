"""Platform-aware lazy loader for the FastDOCX native shared library.

The library is loaded on first use; importing this module (or the top-level
``fastdocx`` package) never raises an error even when the binary is absent.
Only the first call to :func:`get_lib` triggers loading, so unit tests that
mock out the native layer can import freely.
"""

from __future__ import annotations

import platform
from pathlib import Path

from fastdocx._native.bindings import NativeLib

# ---------------------------------------------------------------------------
# Platform → RID mapping (matches .NET publish -r RIDs and _libs/ dirs)
# ---------------------------------------------------------------------------

_PLATFORM_TO_LIB_DIR: dict[tuple[str, str], str] = {
    ("Linux", "x86_64"): "linux-x64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Windows", "AMD64"): "win-x64",
    ("Windows", "ARM64"): "win-arm64",
    ("Darwin", "arm64"): "osx-arm64",
    ("Darwin", "x86_64"): "osx-x64",
}

_LIB_NAMES: dict[str, str] = {
    "linux-x64": "FastDocx.Native.so",
    "linux-arm64": "FastDocx.Native.so",
    "win-x64": "FastDocx.Native.dll",
    "win-arm64": "FastDocx.Native.dll",
    "osx-arm64": "FastDocx.Native.dylib",
    "osx-x64": "FastDocx.Native.dylib",
}

# Module-level cache — None means "not yet attempted"
_cached_lib: NativeLib | None = None
_load_attempted: bool = False


def _libs_root() -> Path:
    """Return the absolute path to ``fastdocx/_libs/``."""
    return Path(__file__).parent.parent / "_libs"


def _resolve_lib_path() -> Path:
    """Resolve the platform-specific shared library path.

    Raises:
        RuntimeError: If the current platform is not recognised or the binary
            file does not exist.
    """
    system = platform.system()
    machine = platform.machine()
    key = (system, machine)

    rid = _PLATFORM_TO_LIB_DIR.get(key)
    if rid is None:
        raise RuntimeError(
            f"FastDOCX: unsupported platform {system!r}/{machine!r}. "
            "Supported platforms: linux-x64, linux-arm64, win-x64, win-arm64, osx-arm64, osx-x64."
        )

    lib_name = _LIB_NAMES[rid]
    lib_path = _libs_root() / rid / lib_name

    if not lib_path.exists():
        raise RuntimeError(
            f"FastDOCX native binary not found at {lib_path}.\n"
            f"To fix this, download the pre-built binary for {rid!r} from the "
            "GitHub Releases page and place it at the path above, or build from "
            "source with:\n\n"
            f"  dotnet publish native/FastDocx.Native -r {rid} -c Release\n\n"
            "See README.md for full instructions."
        )

    return lib_path


def get_lib() -> NativeLib:
    """Return the lazily-loaded :class:`~fastdocx._native.bindings.NativeLib`.

    Raises:
        RuntimeError: On unsupported platform or missing binary (only on first
            call; the error is not cached so subsequent calls retry).
    """
    global _cached_lib, _load_attempted

    if _cached_lib is not None:
        return _cached_lib

    lib_path = _resolve_lib_path()
    _cached_lib = NativeLib(str(lib_path))
    return _cached_lib
