"""FastDOCX — Pythonic DOCX manipulation via a C# Native AOT shared library."""

from fastdocx.document import Document
from fastdocx.errors import FastDocxError, NativeRuntimeError
from fastdocx.paragraph import ParagraphView

__all__ = ["Document", "FastDocxError", "NativeRuntimeError", "ParagraphView"]
__version__ = "0.1.0"
