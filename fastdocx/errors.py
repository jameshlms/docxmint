"""Custom exceptions for fastdocx."""


class FastDocxError(Exception):
    """Base error for all fastdocx errors."""


class DocumentClosedError(FastDocxError):
    """Raised when a proxy is accessed after its document context has exited.

    Call snapshot() inside the context manager to retain data outside it.
    """


class StaleProxyError(FastDocxError):
    """Raised when a proxy is accessed after its element was removed from the document.

    Call snapshot() before removing to retain data.
    """


class OwnershipError(FastDocxError):
    """Raised when an element from one document is used in another.

    Call snapshot() to get a document-independent copy.
    """


class NativeRuntimeError(RuntimeError, FastDocxError):
    """Raised when a native FFI call fails or returns an unexpected error code."""


class NonexistentCachedPageCount(RuntimeError, FastDocxError):
    """Raised when a page count is requested for a document that has not been paginated."""
