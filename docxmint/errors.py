"""Custom exceptions for docxmint.

All public exceptions are subclasses of :class:`DocxMintError`, so callers can
catch the entire hierarchy with a single ``except DocxMintError`` clause if needed.
"""


class DocxMintError(Exception):
    """Base class for all DocxMint exceptions."""


class DocumentClosedError(DocxMintError):
    """Raised when a proxy property is accessed after its document has been closed.

    This happens when you hold a live proxy outside the context manager::

        with Document.open("f.docx") as doc:
            para = doc.paragraphs[0]
        para.text  # raises DocumentClosedError

    **Fix**: call ``snapshot(para)`` *inside* the context manager to obtain a
    document-independent copy that remains valid after close.
    """


class StaleProxyError(DocxMintError):
    """Raised when a proxy is accessed after its element was removed from the document.

    **Fix**: call ``snapshot(element)`` before removing it if you need the data.
    """


class OwnershipError(DocxMintError):
    """Raised when a live element from document A is appended to document B.

    Each live proxy is bound to the document that created it. To move content
    between documents, snapshot the element first::

        snap = snapshot(src_doc.paragraphs[0])
        dst_doc.paragraphs.append(snap)
    """


class NativeRuntimeError(RuntimeError, DocxMintError):
    """Raised when a native FFI call fails or returns an unexpected error code.

    Inherits from both :exc:`RuntimeError` and :exc:`DocxMintError`.
    The exception message contains the error detail from the C# layer.
    """


class NonexistentCachedPageCount(RuntimeError, DocxMintError):
    """Raised when a page count is requested for a document that has not been paginated.

    Page counts require an explicit pagination step that is not yet exposed in the
    public API (v1 limitation).
    """
