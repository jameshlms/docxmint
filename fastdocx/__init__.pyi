from fastdocx._collection import DocumentView as DocumentView
from fastdocx._proxy.base import ProxyBase as _ProxyBase
from fastdocx.document import Document as Document
from fastdocx.errors import (
    DocumentClosedError as DocumentClosedError,
)
from fastdocx.errors import (
    FastDocxError as FastDocxError,
)
from fastdocx.errors import (
    NativeRuntimeError as NativeRuntimeError,
)
from fastdocx.errors import (
    OwnershipError as OwnershipError,
)
from fastdocx.errors import (
    StaleProxyError as StaleProxyError,
)
from fastdocx.formats import (
    Border as Border,
)
from fastdocx.formats import (
    CellBorders as CellBorders,
)
from fastdocx.formats import (
    CellMargin as CellMargin,
)
from fastdocx.formats import (
    ColumnFormat as ColumnFormat,
)
from fastdocx.formats import (
    IndentFormat as IndentFormat,
)
from fastdocx.formats import (
    ListFormat as ListFormat,
)
from fastdocx.formats import (
    PageMargins as PageMargins,
)
from fastdocx.formats import (
    ParagraphBorders as ParagraphBorders,
)
from fastdocx.formats import (
    RGBColor as RGBColor,
)
from fastdocx.formats import (
    Shading as Shading,
)
from fastdocx.formats import (
    SpacingFormat as SpacingFormat,
)
from fastdocx.formats import (
    TableBorders as TableBorders,
)
from fastdocx.hyperlink import Hyperlink as Hyperlink
from fastdocx.image import Image as Image
from fastdocx.paragraph import HorizontalRule as HorizontalRule
from fastdocx.paragraph import Paragraph as Paragraph
from fastdocx.run import Run as Run
from fastdocx.section import Section as Section
from fastdocx.styles import Style as Style
from fastdocx.styles import StyleCollection as StyleCollection
from fastdocx.table import Cell as Cell
from fastdocx.table import Row as Row
from fastdocx.table import Table as Table
from fastdocx.units import Color as Color

__version__: str

def snapshot[T: _ProxyBase](elem: T) -> T: ...
