"""Custom exceptions for fastdocx."""


class FastDocxError(Exception):
    """Base exception for fastdocx errors."""


class NativeRuntimeError(RuntimeError, FastDocxError):
    """Raised when a native call fails or returns an error code."""
