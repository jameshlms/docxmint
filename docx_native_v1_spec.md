# docx_native — V1 Implementation Spec

## Instructions for Claude Code

There is existing code in this codebase. Use it as a starting point but do not feel obligated to preserve any of it. If the existing structure conflicts with this spec, discard it and start fresh. This spec is the source of truth for v1.

---

## What This Library Is

`docx_native` is a Python library for reading and writing `.docx` files. It binds to a NativeAOT-compiled C# backend via `ctypes` (stdlib only, no third-party FFI dependency). The C# side uses Microsoft's official `DocumentFormat.OpenXml` SDK. No .NET runtime is required at deployment.

**Minimum Python version: 3.12**

---

## Core Design Principles

- C# owns all document data — Python holds proxies
- The context manager is the FFI boundary — GC and disposal are invisible to the user
- Descriptors not if/elif chains — one line per property, routing handled automatically
- `.copy()` is the escape hatch — the only way to take Python ownership of document data
- Document is a collection not a builder — no `add_*` methods on the native Document
- The same model works at every level — Document, Paragraph, Run all follow identical patterns
- Error messages always mention `.copy()` — tell users what to do, not just what went wrong
- v1 is the architecture — features come later, patterns come now

---

## The Three Proxy States

Every proxy object is in one of three states:

**Live proxy** — backed by a C# object:
```python
para = doc.paragraphs.first
para.text = "Hello"    # writes through to C#
para.text              # reads from C#
```

**Construction object** — created by the user, not yet in a document:
```python
para = Paragraph("Hello", style="Heading1")
para.text = "Updated"  # writes to local Python dict, no C# yet
doc.append(para)       # C# object created here, proxy becomes live
```

**Snapshot** — returned by `.copy()`, safe outside context manager:
```python
with Document.open("file.docx") as doc:
    para = doc.paragraphs.first.copy()
para.text   # reads from local Python dict, no FFI, always safe
```

The key rule: the live proxy has an empty local dict and reads everything from C#. The construction object and snapshot have a populated local dict and no C# handle. The same data is never stored on both sides simultaneously.

---

## Proxy Base Class

All proxy types inherit from `ProxyBase`.

- `__setattr__` is overridden to route writes through FFI. Internal attributes (prefixed with `_`) bypass this and go directly to `object.__setattr__`.
- Every proxy `__init__` uses `object.__setattr__` for initialization to avoid triggering routing before the object is ready.
- `__getattr__` is the fallback for properties not covered by a descriptor. Descriptors on the class are found by normal Python attribute lookup before `__getattr__` is ever called.
- `_from_native` is the internal factory method. No docstring — it must not appear in generated API documentation.
- `_check_valid()` is called before every C# access. Raises `DocumentClosedError` if the context has exited, `StaleProxyError` if the element has been removed. Both error messages must mention `.copy()` as the solution.
- `_mark_stale()` is called by the collection when an element is removed. Propagates to child proxies — removing a paragraph marks all its run proxies stale.
- `copy()` materializes the entire subtree below the call site into a snapshot. Returns `Self` — the same type it is called on.

---

## Descriptor System

All proxy properties are declared as class-level descriptors. Adding a new property is one line:

```python
class Run(ProxyBase):
    bold = BoolProperty("bold")
```

**Descriptor types:**

- `BoolProperty` — boolean, stored as int (0/1) on C# side. Default `False`.
- `StringProperty` — string with optional default. Normalizes `None` to default.
- `FloatProperty` — float with optional default. Used for font size, spacing, indentation.
- `ChoiceProperty[L]` — string restricted to a `Literal` type. Validates before writing. Supports `allow_bool` so `True` maps to primary choice and `False` maps to `None`.
- `ColorProperty` — accepts `"#RRGGBB"`, `"RRGGBB"`, `RGBColor`, or `"auto"`. Normalizes to bare hex before writing to C#.
- `ObjectProperty` — for nested proxy objects like `Font` and `Shading`. Wraps C# sub-object handle in the appropriate proxy type on read. Validates type on write.

**C# side exports generic typed dispatchers:**
- `get_int` / `set_int` for booleans
- `get_float` / `set_float` for floats
- `get_str` / `set_str` for strings
- `set_many` for batched writes (used by `Run.edit()`)

Each takes the property name as a string and switches on it internally.

**Descriptor typing requirements:**

Every descriptor must implement `__get__` overloads to distinguish instance vs class access so type checkers see the correct return type:

```python
class BoolProperty:
    @overload
    def __get__(self, obj: None, objtype: type) -> BoolProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> bool: ...
    def __set__(self, obj: ProxyBase, value: bool) -> None: ...
```

`ChoiceProperty` must be generic over a `Literal` type so invalid values are caught statically.

---

## DocumentView and Filtered Collections

`DocumentView[T]` is a single generic class for all filtered views. It is a live view — it holds a reference to the document and filters on access. Nothing is stored in the view itself.

**Access syntax:**
```python
doc[Paragraph]              # DocumentView[Paragraph]
doc[Paragraph | Table]      # DocumentView[Paragraph | Table]  (runtime only, Any to type checker)
doc.group(Paragraph, Table) # DocumentView[Paragraph | Table]  (fully typed via overloads)
```

**Named shortcuts are thin wrappers:**
```python
@property
def paragraphs(self) -> DocumentView[Paragraph]:
    return self[Paragraph]
```

**`group()` overloads for full type safety:**
```python
@overload
def group(self, t1: type[T1]) -> DocumentView[T1]: ...
@overload
def group(self, t1: type[T1], t2: type[T2]) -> DocumentView[T1 | T2]: ...
@overload
def group(self, t1: type[T1], t2: type[T2], t3: type[T3]) -> DocumentView[T1 | T2 | T3]: ...
```

**`DocumentView[T]` members:**

Properties:
```python
view.first: T | None
view.last: T | None
```

Methods:
```python
view.append(element: T) -> None
view.extend(elements: Iterable[T]) -> None
view.insert(index: int, element: T) -> None
view.remove(element: T) -> None
view.pop(index: int = -1) -> T
view.clear() -> None
view.index(element: T) -> int
```

Dunders:
```python
__iter__() -> Iterator[T]
__reversed__() -> Iterator[T]
__len__() -> int
__bool__() -> bool
__contains__(element: object) -> bool
__getitem__(index: int) -> T
__getitem__(index: slice) -> DocumentView[T]   # overloaded
__iadd__(elements: Iterable[T]) -> Self
__or__(other: DocumentView[T2]) -> DocumentView[T | T2]
```

**Type enforcement on filtered collections:**
```python
doc.paragraphs.append(Table(rows=2, cols=2))
# TypeError: DocumentView[Paragraph] only accepts Paragraph elements.
# Use doc.append() or doc[Paragraph | Table] instead.
```

**Append semantics for filtered views:**
`doc.paragraphs.append(para)` inserts after the last `Paragraph` in the body, not at the end of the entire body. `doc.append(element)` always appends to the true end.

---

## Document

`Document` is the collection. There is no `doc.body` — the document itself is the flat sequence of block-level elements. `doc.body` may be provided as an alias returning `self` if desired but is not required.

**Construction:**
```python
Document()                 # new blank document
Document.open(path)        # open existing document
Document.edit(path)        # open for in-place editing, saves back on exit
```

**Properties:**
```python
doc.path: str | None
doc.is_open: bool
doc.styles: StyleCollection
doc.default_style: Style
doc.language: str                  # BCP 47, document default
doc.author: str
doc.title: str
doc.subject: str
doc.description: str
doc.created: datetime
doc.modified: datetime
```

**Filtered views:**
```python
doc.paragraphs: DocumentView[Paragraph]
doc.tables: DocumentView[Table]
doc.images: DocumentView[Image]
doc.sections: DocumentView[Section]
```

**Collection methods (Document is the collection):**
```python
doc.append(element)
doc.extend(elements)
doc.insert(index, element)
doc.remove(element)
doc.pop(index=-1)
doc.clear()
doc.index(element)
doc.first
doc.last
doc.group(...)             # typed overloads up to 3 types
```

**Lifecycle:**
```python
doc.save(path: str | None = None) -> None
```

**Dunders:**
```python
__enter__() -> Self
__exit__(...) -> None      # never suppresses exceptions
__repr__() -> str          # <Document path="report.docx" paragraphs=42 open=True>
__bool__() -> bool         # is open and valid
__contains__(element: ProxyBase) -> bool   # ownership check only
__iter__() -> Iterator[ProxyBase]
__reversed__() -> Iterator[ProxyBase]
__len__() -> int           # total body element count
__getitem__(index: int) -> ProxyBase
__getitem__(index: slice) -> DocumentView[ProxyBase]
__getitem__(key: type[T]) -> DocumentView[T]
__iadd__(elements: Iterable[ProxyBase]) -> Self
__eq__() -> bool           # identity based — same C# handle
__hash__() -> int          # based on native handle identity
```

**Context manager behavior:**

On enter: opens native document, increments active document reference count on C# side.

On exit: calls `dispose()` on native document (deterministic, not GC-dependent), decrements count, triggers `GC.Collect()` if count hits zero, sets native handle to `None`. Never suppresses exceptions.

---

## Paragraph

**Construction:**
```python
Paragraph()
Paragraph("text")
Paragraph("text", style="Heading1", alignment="center")
Paragraph.horizontal_line(style="single", width=6, color="auto")
```

**Properties:**
```python
para.text: str                        # plain text of all runs concatenated
para.style: str
para.alignment: Literal["left", "right", "center", "justify"]
para.keep_together: bool
para.keep_with_next: bool
para.page_break_before: bool
para.indent: IndentFormat             # .left, .right, .first_line (inches)
para.spacing: SpacingFormat           # .before, .after (points), .line, .line_rule
para.borders: ParagraphBorders        # .top, .bottom, .left, .right (Border objects)
para.shading: Shading
para.list: ListFormat                 # .num_id, .level (raw access for v1)
```

**Collection:**
```python
para.runs: DocumentView[Run]
```

**Methods:**
```python
para.copy() -> Self
```

**Builder methods (all return `Self` for chaining):**
```python
para.style("Heading1") -> Self
para.align("center") -> Self
para.indent(left=0.5, right=0.5, first_line=0.25) -> Self
para.spacing(before=12, after=12, line=1.5) -> Self
```

**Dunders:**
```python
__repr__() -> str
__str__() -> str           # plain text
__bool__() -> bool         # has any content
__len__() -> int           # number of runs
__iter__() -> Iterator[Run]
__contains__(run: Run) -> bool
__eq__() -> bool           # identity based
__hash__() -> int
```

**Mutually exclusive property validation:**
Raise `ValueError` with a clear message if conflicting properties are set together. Never silently resolve conflicts. The error message must state which properties conflict and what to do instead.

---

## Run

**Construction:**
```python
Run()
Run("text")
Run("text", bold=True, font_name="Arial", font_size=12)
```

**Properties:**
```python
run.text: str
run.bold: bool
run.italic: bool
run.strikethrough: bool
run.underline: bool | Literal["single", "double", "dotted", "dashed", "wave"]
run.all_caps: bool
run.small_caps: bool
run.superscript: bool
run.subscript: bool
run.baseline: float                   # points, positive is up
run.hidden: bool
run.emboss: bool
run.imprint: bool
run.outline: bool
run.shadow: bool
run.color: ColorValue                 # "#RRGGBB" | "RRGGBB" | RGBColor | "auto"
run.highlight: Literal[
    "yellow", "green", "cyan", "magenta", "blue", "red",
    "dark_blue", "dark_cyan", "dark_green", "dark_magenta",
    "dark_red", "dark_yellow", "dark_gray", "light_gray", "black", "white"
]
run.font_name: str
run.font_name_eastasia: str
run.font_name_complex: str
run.font_size: float                  # points, 0 means inherit
run.font_scale: float                 # percentage
run.character_spacing: float          # points
run.kerning: float                    # threshold in points
run.language: str                     # BCP 47 tag
run.no_spell_check: bool
run.no_grammar_check: bool
run.shading: Shading
```

**Mutually exclusive pairs — raise `ValueError` if set together:**
- `all_caps` and `small_caps`
- `superscript` and `subscript`
- `emboss` and `imprint`

**Methods:**
```python
run.copy() -> Self
run.split(index: int) -> tuple[Run, Run]   # leaves original in undefined state
run.edit() -> ContextManager               # batches writes into single FFI call via set_many
```

**Builder methods (all return `Self`):**
```python
run.bold(value: bool = True) -> Self
run.italic(value: bool = True) -> Self
run.strikethrough(value: bool = True) -> Self
run.underline(value: bool | str = True) -> Self
run.all_caps(value: bool = True) -> Self
run.small_caps(value: bool = True) -> Self
run.superscript(value: bool = True) -> Self
run.subscript(value: bool = True) -> Self
run.hidden(value: bool = True) -> Self
run.color(value: ColorValue) -> Self
run.highlight(value: str) -> Self
run.font(name: str, size: float | None = None) -> Self
run.language(tag: str) -> Self
```

Mutually exclusive validation fires in both kwargs construction and builder chain.

**Dunders:**
```python
__repr__() -> str
__str__() -> str           # run.text
__bool__() -> bool         # has text content
__len__() -> int           # character count
__add__(other: Run) -> Run # concatenate if same formatting, else ValueError
__eq__() -> bool           # identity based
__hash__() -> int
```

---

## Table

**Construction:**
```python
Table(rows: int, cols: int)
Table(rows: int, cols: int, style: str = "TableGrid")
```

**Properties:**
```python
table.style: str
table.alignment: Literal["left", "right", "center"]
table.width: float                    # inches
table.indent: float                   # left indent inches
table.borders: TableBorders
table.shading: Shading
table.cell_spacing: float             # points
table.cell_margin: CellMargin         # .top, .bottom, .left, .right (points)
table.data: list[list[str]]           # plain text, plugs into DataFrame constructor
```

**Collections:**
```python
table.rows: DocumentView[Row]
table.columns: DocumentView[Column]
table.cells: DocumentView[Cell]       # flat, all cells in reading order
```

**Methods:**
```python
table.copy() -> Self
table.cell(row: int, col: int) -> Cell
```

**Dunders:**
```python
__repr__() -> str
__bool__() -> bool
__len__() -> int                      # number of rows
__iter__() -> Iterator[Row]
__contains__(row: Row) -> bool
__getitem__(index: int) -> Row
__getitem__(index: tuple[int, int]) -> Cell    # table[0, 0]
__eq__() -> bool
__hash__() -> int
```

---

## Row

**Properties:**
```python
row.height: float                     # points
row.height_rule: Literal["auto", "exact", "atLeast"]
row.is_header: bool
row.cant_split: bool
```

**Collection:**
```python
row.cells: DocumentView[Cell]
```

**Methods:**
```python
row.copy() -> Self
```

**Dunders:**
```python
__repr__() -> str
__bool__() -> bool
__len__() -> int
__iter__() -> Iterator[Cell]
__getitem__(index: int) -> Cell
__eq__() -> bool
__hash__() -> int
```

---

## Cell

**Properties:**
```python
cell.text: str                        # plain text of all paragraphs concatenated
cell.width: float                     # inches
cell.vertical_alignment: Literal["top", "center", "bottom"]
cell.borders: CellBorders
cell.shading: Shading
cell.merge_up: bool
cell.merge_left: bool
```

**Collection:**
```python
cell.paragraphs: DocumentView[Paragraph]
```

**Methods:**
```python
cell.copy() -> Self
cell.merge(other: Cell) -> None
```

**Dunders:**
```python
__repr__() -> str
__str__() -> str                      # plain text
__bool__() -> bool
__len__() -> int                      # number of paragraphs
__iter__() -> Iterator[Paragraph]
__eq__() -> bool
__hash__() -> int
```

---

## Section

**Properties:**
```python
section.orientation: Literal["portrait", "landscape"]
section.page_width: float             # inches
section.page_height: float            # inches
section.margins: PageMargins          # .top, .bottom, .left, .right, .header, .footer (inches)
section.columns: ColumnFormat         # .count, .spacing, .equal_width
section.start_type: Literal["continuous", "newPage", "evenPage", "oddPage"]
section.different_first_page: bool
```

**Collections:**
```python
section.paragraphs: DocumentView[Paragraph]   # live slice of doc body for this section
section.tables: DocumentView[Table]
```

**Methods:**
```python
section.copy() -> Self
```

---

## Border

```python
border.style: Literal["single", "double", "dotted", "dashed", "wave", "none"]
border.width: float                   # points
border.color: ColorValue
border.spacing: float                 # points from text
border.shadow: bool
```

---

## Shading

```python
shading.fill: ColorValue
shading.color: ColorValue
shading.pattern: str                  # "clear", "solid", or percent value string
```

---

## Style

```python
style.name: str
style.type: Literal["paragraph", "character", "table", "numbering"]
style.based_on: str | None
style.next_style: str | None
style.is_default: bool
style.paragraph_format: ParagraphFormat
style.font: FontFormat
```

---

## RGBColor

```python
class RGBColor:
    r: int    # 0-255
    g: int    # 0-255
    b: int    # 0-255
    
    def __init__(self, r: int, g: int, b: int) -> None: ...
    def __str__(self) -> str: ...     # returns "RRGGBB"
    def __repr__(self) -> str: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
```

---

## Error Types

```python
class DocxNativeError(Exception): ...

class DocumentClosedError(DocxNativeError):
    # raised when a proxy is accessed after context manager exit
    # message must mention .copy() as solution
    ...

class StaleProxyError(DocxNativeError):
    # raised when a proxy is accessed after its element was removed
    # message must mention .copy() as solution
    ...

class OwnershipError(DocxNativeError):
    # raised when an element from one document is used in another without copying
    ...
```

---

## Compat Layer — `docx_native.compat`

Mimics python-docx API exactly. Thin wrapper over native API. No new C# changes required.

**Differences from native API:**
- `Document()` with no args or path — no context manager required
- `doc.add_paragraph(text, style)` and similar `add_*` methods exist
- `doc.paragraphs` returns an eager `list` not a live view
- No context manager required — document disposed on GC or explicit `close()`
- `close()` method triggers same dispose logic as context manager exit

**ResourceWarning on GC without close:**
```python
def __init__(self, path=None):
    object.__setattr__(self, '_open_traceback', traceback.extract_stack())
    object.__setattr__(self, '_closed', False)

def __del__(self):
    if not self._closed:
        warnings.warn(
            f"Document opened at:\n{''.join(traceback.format_list(self._open_traceback))}"
            "was not explicitly closed. Call close() or use the native API "
            "with a context manager to ensure correct disposal.",
            ResourceWarning,
            stacklevel=2
        )
        self._dispose()
```

---

## Typing Requirements

The following must be correct for the type checker — do not leave these as `Any` or untyped:

- All descriptor `__get__` overloads distinguishing instance vs class access
- `ChoiceProperty` generic over `Literal` type
- `copy()` returning `Self` on all proxy types
- `DocumentView[T]` flowing through `first`, `last`, `pop`, `__iter__`, `__reversed__`, `__getitem__`
- `__getitem__` overloads for `int` vs `slice` on `DocumentView`
- `Table.__getitem__` overloads for `int` vs `tuple[int, int]`
- `group()` overloads preserving union type through to return
- `DocumentView.__or__` returning `DocumentView[T1 | T2]`
- `Document.__enter__` returning `Self`
- `Document.__exit__` returning `None` (never suppresses exceptions)
- `Document.__contains__` accepting only `ProxyBase`
- Full error hierarchy explicitly typed

**Package must include `py.typed` marker (PEP 561).**

Use inline annotations for most of the codebase. Consider stub files (`.pyi`) for the core proxy base class and descriptor machinery where runtime implementation is noisy.

---

## What Is Explicitly Deferred to V2

Do not implement any of the following in v1:

- `DocumentBatch` and GC suppression for single document sessions
- `where()` filtering on collections
- Custom index types (`StyleIndex`, `BookmarkIndex`, `OutlineIndex`)
- `iloc` / `loc` separation
- Concurrent modification detection
- Headers and footers
- Footnotes and endnotes
- Table of contents
- Comments and tracked changes
- Full list and numbering system (v1 exposes raw `num_id` and `level` only)
- Embedded images beyond basic placeholder
- PDF export
- MCP server
- Pandas extra
- Celery / arq extra
- FastAPI extra
- Pydantic extra
- `DocumentBatch`

---

## Repository Structure

```
docx_native/                              # repo root
    native/                               # C# project
        DocxNative.csproj
        src/
            Exports.cs                    # all [UnmanagedCallersOnly] entry points
            Properties.cs                 # get_int/set_int/get_str/set_str/etc dispatch
            Document.cs                   # document open/close/dispose
            Paragraph.cs                  # paragraph operations
            Run.cs                        # run operations
            Table.cs                      # table, row, cell operations
            Section.cs                    # section operations
            Styles.cs                     # style access
        build/                            # NativeAOT compiler output — gitignored
            win-x64/
                docx_native.dll
            linux-x64/
                docx_native.so
            osx-arm64/
                docx_native.dylib
    docx_native/                          # Python package
        py.typed
        __init__.py
        _native/
            __init__.py
            handle.py                     # loads correct binary for platform, all ctypes calls
            gc.py                         # reference counting, GC coordination
        _proxy/
            __init__.py
            base.py                       # ProxyBase
            descriptors.py                # all descriptor types
        document.py                       # Document
        paragraph.py                      # Paragraph
        run.py                            # Run, RGBColor
        table.py                          # Table, Row, Cell
        section.py                        # Section
        collection.py                     # DocumentView
        styles.py                         # Style, StyleCollection
        formats.py                        # Border, Shading, IndentFormat, SpacingFormat, etc.
        errors.py                         # all error types
        compat/
            __init__.py
            document.py                   # compat Document wrapper
    tests/
        test_document.py
        test_paragraph.py
        test_run.py
        test_table.py
        test_collection.py
        test_compat.py
        mock_handle.py                    # mock FFI boundary for unit tests
    pyproject.toml
    README.md
    docx_native_v1_spec.md
```

**`native/build/` is gitignored.** Binaries are compiled per platform in CI and packaged into the wheel at release time.

**`pyproject.toml` must include the binaries as package data** so they are shipped inside the wheel:

```toml
[tool.setuptools.package-data]
docx_native = ["_native/bin/*/*"]
```

**`handle.py` detects platform at import time and loads the correct binary:**

```python
import ctypes, platform, pathlib

_lib_names = {
    ("Windows", "AMD64"):  "_native/bin/win-x64/docx_native.dll",
    ("Linux",   "x86_64"): "_native/bin/linux-x64/docx_native.so",
    ("Darwin",  "arm64"):  "_native/bin/osx-arm64/docx_native.dylib",
}

_key = (platform.system(), platform.machine())
if _key not in _lib_names:
    raise RuntimeError(
        f"docx_native has no prebuilt binary for {_key[0]} {_key[1]}. "
        f"Supported platforms: {list(_lib_names.keys())}"
    )

_lib = ctypes.CDLL(str(pathlib.Path(__file__).parent.parent / _lib_names[_key]))
```

---

## FFI Boundary Rules

All C# calls are isolated to `_native/handle.py`. No other module imports `ctypes` directly. This makes the FFI boundary explicit and testable — the rest of the library can be tested with a mock handle.

The C# side exports:
```
get_int(handle, property_name) -> int
set_int(handle, property_name, value: int) -> void
get_float(handle, property_name) -> float
set_float(handle, property_name, value: float) -> void
get_str(handle, property_name) -> str
set_str(handle, property_name, value: str) -> void
set_many(handle, properties: dict) -> void
dispose(handle) -> void
```

Property names are strings matching the descriptor names exactly. The C# side switches on the property name internally.
