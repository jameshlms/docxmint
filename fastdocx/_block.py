"""BlockContainerMixin — paragraph and table collections for body-like containers.

Both ``Document`` and ``Cell`` use this mixin. Concrete classes must implement
``_block_context()`` which returns the ``(handle, lib, document)`` triple needed to
build live ``DocumentView`` objects, or ``None`` when the container is not yet live.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from fastdocx._proxy.base import ProxyBase

if TYPE_CHECKING:
    from fastdocx._native.handle import Handle
    from fastdocx.collection import DocumentView
    from fastdocx.document import Document
    from fastdocx.paragraph import HorizontalRule, Paragraph
    from fastdocx.table import Table

    _BlockCtx = tuple[int, Handle, Document]


class BlockContainerMixin:
    """Mixin that adds ``paragraphs``, ``tables``, and ``add_*`` helpers.

    Concrete classes implement ``_block_context()``; everything else is derived
    from that single hook.
    """

    def _block_context(self) -> _BlockCtx | None:
        """Return ``(handle, lib, document)`` for collection access, or ``None`` when not live."""
        raise NotImplementedError(f"{type(self).__name__} must implement _block_context()")

    def _block_view[T: ProxyBase](
        self,
        elem_type: type[T],
        collection: str,
    ) -> DocumentView[T]:
        from fastdocx.collection import DocumentView

        ctx = self._block_context()
        if ctx is None:
            return DocumentView.empty(elem_type, collection)
        handle, lib, document = ctx
        return DocumentView(handle, document, lib, elem_type, collection)

    def _block_append[T: ProxyBase](self, element: T) -> T:
        ctx = self._block_context()
        if ctx is None:
            raise ValueError(f"Cannot add content to a {type(self).__name__} that is not live.")
        handle, lib, document = ctx
        from fastdocx.collection import DocumentView

        view = DocumentView(handle, document, lib, type(element), "body")
        return view._append_one(element)

    # ------------------------------------------------------------------
    # Filtered views
    # ------------------------------------------------------------------

    @property
    def paragraphs(self) -> DocumentView[Paragraph]:
        from fastdocx.paragraph import Paragraph

        return self._block_view(Paragraph, "paragraphs")

    @paragraphs.setter
    def paragraphs(self, _: object) -> None:
        pass  # absorbs __iadd__ re-assignment

    @property
    def tables(self) -> DocumentView[Table]:
        from fastdocx.table import Table

        return self._block_view(Table, "tables")

    @tables.setter
    def tables(self, _: object) -> None:
        pass  # absorbs __iadd__ re-assignment

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def add_paragraph(self, text: str = "", style: str = "Normal") -> Paragraph:
        """Append a new paragraph and return the live proxy."""
        from fastdocx.paragraph import Paragraph

        return self._block_append(Paragraph(text, style=style))

    def add_heading(self, text: str = "", level: int = 1) -> Paragraph:
        """Append a heading paragraph and return the live proxy."""
        from fastdocx.paragraph import Paragraph

        return self._block_append(Paragraph(text, style=f"Heading{level}"))

    def add_table(self, rows: int, cols: int, style: str = "TableGrid") -> Table:
        """Append a new table and return the live proxy."""
        from fastdocx.table import Table

        return self._block_append(Table(rows, cols, style=style))

    def add_horizontal_rule(
        self,
        *,
        line_style: Literal["single", "double", "dotted", "dashed", "wave"] = "single",
        line_width: float = 6.0,
        line_color: str = "auto",
    ) -> HorizontalRule:
        """Append a horizontal rule and return the live proxy."""
        from fastdocx.paragraph import HorizontalRule

        return self._block_append(
            HorizontalRule(line_style=line_style, line_width=line_width, line_color=line_color)
        )
