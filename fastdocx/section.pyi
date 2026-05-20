from typing import Literal

from fastdocx._proxy.base import ProxyBase
from fastdocx.collection import DocumentView
from fastdocx.paragraph import Paragraph
from fastdocx.table import Table

class Section(ProxyBase):
    orientation: Literal["portrait", "landscape"]
    page_width: float
    page_height: float
    start_type: Literal["continuous", "newPage", "evenPage", "oddPage"]
    different_first_page: bool

    def __init__(self) -> None: ...
    @property
    def paragraphs(self) -> DocumentView[Paragraph]: ...
    @property
    def tables(self) -> DocumentView[Table]: ...
    def copy(self) -> Section: ...
    def __repr__(self) -> str: ...
