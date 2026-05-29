from docxmint._collection import DocumentView as DocumentView
from docxmint._proxy.base import ProxyBase as _ProxyBase
from docxmint.document import Document as Document
from docxmint.errors import (
    DocumentClosedError as DocumentClosedError,
)
from docxmint.errors import (
    DocxMintError as DocxMintError,
)
from docxmint.errors import (
    NativeRuntimeError as NativeRuntimeError,
)
from docxmint.errors import (
    OwnershipError as OwnershipError,
)
from docxmint.errors import (
    StaleProxyError as StaleProxyError,
)
from docxmint.formats import (
    Border as Border,
)
from docxmint.formats import (
    CellBorders as CellBorders,
)
from docxmint.formats import (
    CellMargin as CellMargin,
)
from docxmint.formats import (
    ColumnFormat as ColumnFormat,
)
from docxmint.formats import (
    IndentFormat as IndentFormat,
)
from docxmint.formats import (
    ListFormat as ListFormat,
)
from docxmint.formats import (
    PageMargins as PageMargins,
)
from docxmint.formats import (
    ParagraphBorders as ParagraphBorders,
)
from docxmint.formats import (
    RGBColor as RGBColor,
)
from docxmint.formats import (
    Shading as Shading,
)
from docxmint.formats import (
    SpacingFormat as SpacingFormat,
)
from docxmint.formats import (
    TableBorders as TableBorders,
)
from docxmint.hyperlink import Hyperlink as Hyperlink
from docxmint.image import Image as Image
from docxmint.paragraph import HorizontalRule as HorizontalRule
from docxmint.paragraph import Paragraph as Paragraph
from docxmint.run import Run as Run
from docxmint.section import Section as Section
from docxmint.styles import Style as Style
from docxmint.styles import StyleCollection as StyleCollection
from docxmint.table import Cell as Cell
from docxmint.table import Row as Row
from docxmint.table import Table as Table
from docxmint.units import Color as Color

__version__: str

def snapshot[T: _ProxyBase](elem: T) -> T: ...
