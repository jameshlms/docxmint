"""Paragraph proxy."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator, Literal, Self

from fastdocx._proxy.base import ProxyBase
from fastdocx._proxy.descriptors import BoolProperty, ChoiceProperty, StringProperty
from fastdocx.collection import DocumentView

if TYPE_CHECKING:
    from fastdocx.run import Run


class Paragraph(ProxyBase):
    """A paragraph element — either a live proxy or a construction object.

    **Construction object** (before appending to a document)::

        para = Paragraph("Hello", style="Heading1", alignment="center")
        doc.paragraphs.append(para)

    **Live proxy** (after appending, or from doc.paragraphs[i])::

        para = doc.paragraphs[0]
        para.text = "Updated"
        para.alignment = "center"
    """

    _child_type_name = "paragraph"

    # Descriptors — one line per property, routing handled automatically
    text = StringProperty("text", default="")
    style = StringProperty("style", default="Normal")
    alignment: ChoiceProperty[Literal["left", "right", "center", "justify"]] = ChoiceProperty(
        "alignment", ("left", "right", "center", "justify")
    )
    keep_together = BoolProperty("keep_together")
    keep_with_next = BoolProperty("keep_with_next")
    page_break_before = BoolProperty("page_break_before")

    def __init__(
        self,
        text: str = "",
        *,
        style: str = "Normal",
        alignment: Literal["left", "right", "center", "justify"] | None = None,
        keep_together: bool = False,
        keep_with_next: bool = False,
        page_break_before: bool = False,
    ) -> None:
        super().__init__()
        data: dict[str, Any] = {}
        if text:
            data["text"] = text
        if style and style != "Normal":
            data["style"] = style
        if alignment is not None:
            data["alignment"] = alignment
        if keep_together:
            data["keep_together"] = True
        if keep_with_next:
            data["keep_with_next"] = True
        if page_break_before:
            data["page_break_before"] = True
        self._setattr("_data", data)

    @classmethod
    def horizontal_line(
        cls,
        style: Literal["single"] = "single",
        width: int = 6,
        color: str = "auto",
    ) -> Paragraph:
        """Create a horizontal rule paragraph."""
        para = cls.__new__(cls)
        para._setattr("_native", None)
        para._setattr("_document", None)
        para._setattr("_stale", False)
        para._setattr("_data", {"_horizontal_line": True})
        return para

    # ------------------------------------------------------------------
    # Runs collection
    # ------------------------------------------------------------------

    @property
    def runs(self) -> DocumentView[Run]:
        if not self._is_live:
            return []  # type: ignore[return-value]  # construction objects have no runs yet
        self._check_valid()
        from fastdocx.run import Run
        return DocumentView(
            self._getattr("_native"),
            self._getattr("_document"),
            self._get_lib(),
            (Run,),
            "runs",
        )

    # ------------------------------------------------------------------
    # Builder methods (return Self for chaining)
    # ------------------------------------------------------------------

    def add_run(self, text: str = "") -> Run:
        """Append a new run and return the live proxy."""
        from fastdocx.collection import DocumentView
        from fastdocx.run import Run
        if not self._is_live:
            raise ValueError("Cannot add_run to a paragraph that is not yet in a document.")
        view = DocumentView(
            self._getattr("_native"),
            self._getattr("_document"),
            self._get_lib(),
            (Run,),
            "runs",
        )
        return view._append_one(Run(text))

    def align(self, alignment: Literal["left", "right", "center", "justify"]) -> Self:
        self.alignment = alignment
        return self

    def set_style(self, style: str) -> Self:
        self.style = style
        return self

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._getattr("_data"))
        return {
            "text": self.text,
            "style": self.style,
            "alignment": self.alignment,
            "keep_together": self.keep_together,
            "keep_with_next": self.keep_with_next,
            "page_break_before": self.page_break_before,
            "runs": [r.copy() for r in self.runs],
        }

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        native = self._getattr("_native")
        if native is None:
            data = self._getattr("_data")
            text = data.get("text", "")
            return f"Paragraph({text!r})"
        if self._getattr("_stale"):
            return "Paragraph(<stale>)"
        try:
            return f"Paragraph(text={self.text!r}, handle={native!r})"
        except Exception:
            return f"Paragraph(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        if not self._is_live:
            data = self._getattr("_data")
            return len(data.get("runs", []))
        try:
            return len(self.runs)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Run]:
        return iter(self.runs)

    def __contains__(self, run: object) -> bool:
        return run in self.runs


