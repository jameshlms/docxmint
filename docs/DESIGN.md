# docx_native — Design Document

This document describes the architecture, API design, and implementation decisions for
`docx_native`. It should be treated as the source of truth when reworking existing code.
Where existing code conflicts with this document, this document wins.

---

## Core Architecture

### Overview

`docx_native` is a Python library that binds to a NativeAOT-compiled C# backend via FFI.
The C# backend uses the DocumentFormat.OpenXml SDK as its document engine. Python never
owns document data directly — it holds lightweight proxy objects backed by C# objects.
The C# side owns all document state for the lifetime of the document context.

### Technology Stack

- **Backend**: C# compiled via NativeAOT, exporting a plain C ABI
- **Binding**: Python `ctypes` or `cffi` calling into the native library
- **Document engine**: DocumentFormat.OpenXml SDK (Microsoft's official OpenXML implementation)
- **Python binding layer**: Proxy objects with `__getattr__` / `__setattr__` / `__delattr__`

### Memory and Ownership Model

```
C# NativeAOT binary
└── Document (owns all document state)
    ├── Body (sequence of block elements)
    │   ├── Paragraph → Python holds Paragraph proxy
    │   │   └── Runs  → Python holds Run proxy
    │   ├── Table     → Python holds Table proxy
    │   ├── Image     → Python holds Image proxy
    │   └── Section   → Python holds Section proxy
    └── CoreProperties

Python side
└── Proxy objects (handles only — no data ownership)
    ├── ParagraphProxy  → wraps a C# object reference
    ├── RunProxy        → wraps a C# object reference
    ├── TableProxy      → wraps a C# object reference
    └── ImageProxy      → wraps a C# object reference
```

**Rule**: All document data lives in C#. Python proxies are handles. Accessing a proxy
property crosses the FFI boundary. There are no Python-side caches of document data
unless the user explicitly calls `.copy()`.

---

## Context Manager

The document context manager is the single seam where all FFI and GC concerns are handled.
Users never interact with GC or FFI directly.

### Behaviour on `__enter__`

1. Open the native document via FFI
2. Increment the active document reference count on the C# side
3. While `active_documents > 0`, C# suppresses GC pauses where possible
4. Return `self`

### Behaviour on `__exit__`

1. Save if no exception and `autosave=True` (default `False`)
2. Call `dispose()` on the native document — deterministic cleanup, not GC-dependent
3. Decrement active document reference count
4. If count reaches zero, trigger `GC.Collect()` — user is now idle
5. Set `self._native = None`
6. Do not suppress exceptions — always return `False`

### Usage

```python
# Standard usage
with Document.open("report.docx") as doc:
    doc.paragraphs[0].text = "Hello"
    doc.save("output.docx")

# New document
with Document.new() as doc:
    doc.body.append(Paragraph("Hello world"))
    doc.save("new.docx")

# Async
async with Document.open("report.docx") as doc:
    await process(doc)
```

### Nested Documents

Multiple open documents are supported. GC is suppressed until all are closed.

```python
with Document.open("a.docx") as doc_a:
    with Document.open("b.docx") as doc_b:
        pass
    # doc_b closed — doc_a still open, GC still suppressed
# doc_a closed — GC.Collect() fires here
```

### Batch Context

For servers processing many documents in sequence, an optional batch context defers
GC collection until the entire batch is complete:

```python
with DocumentBatch() as batch:
    for path in paths:
        with Document.open(path) as doc:
            process(doc)
        # doc disposed but GC deferred — batch still active
# single GC.Collect() here
```

---

## Proxy Model

### All Proxies Follow the Same Contract

Every proxy object — Paragraph, Run, Table, Image, Section — follows these rules:

1. **C# owns the data** — proxy is a handle, not a copy
2. **`__getattr__` reads from C#** — every property access crosses FFI
3. **`__setattr__` writes to C#** — every property assignment crosses FFI
4. **Stale detection** — proxy raises `StaleProxyError` if its backing object was removed
5. **Document closed detection** — proxy raises `DocumentClosedError` if context exited
6. **`.copy()` materializes** — returns a plain Python dataclass, fully Python-owned

### Implementation Pattern

```python
class Paragraph:
    def __init__(self, native_handle, document):
        # Use object.__setattr__ to avoid triggering our own __setattr__
        object.__setattr__(self, "_native", native_handle)
        object.__setattr__(self, "_document", document)
        object.__setattr__(self, "_stale", False)

    def __getattr__(self, name):
        self._check_valid()
        match name:
            case "text":
                return self._native.getText()
            case "style":
                return self._native.getStyle()
            case "runs":
                return RunView(self._native.getRuns(), self._document, self)
            case _:
                raise AttributeError(f"Paragraph has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Internal attributes bypass the proxy
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self._check_valid()
        match name:
            case "text":
                self._native.setText(value)
            case "style":
                self._native.setStyle(value)
            case _:
                raise AttributeError(f"Paragraph has no attribute '{name}'")

    def __delattr__(self, name):
        match name:
            case "text":
                raise AttributeError("Cannot delete text — set to empty string instead")
            case _:
                object.__delattr__(self, name)

    def _check_valid(self):
        if self._document._is_disposed:
            raise DocumentClosedError(
                "Paragraph's document has been closed. "
                "Call .copy() inside the context manager to use data outside it."
            )
        if self._stale:
            raise StaleProxyError(
                "This paragraph has been removed from the document. "
                "Call .copy() before removing to retain data."
            )

    def copy(self):
        self._check_valid()
        return ParagraphData(
            text=self._native.getText(),
            style=self._native.getStyle(),
            runs=[r.copy() for r in self.runs]
        )
```

### Proxy Invalidation

When an element is removed from the document, its proxy is marked stale:

```python
# Removing a paragraph marks its proxy stale
doc.body.remove(para)
para.text   # StaleProxyError

# Removing a paragraph also marks all its run proxies stale
para_runs = list(para.runs)
doc.body.remove(para)
para_runs[0].bold   # StaleProxyError — parent paragraph gone

# Document closed marks all proxies stale
run = doc.paragraphs[0].runs[0]
# (context exits)
run.bold   # DocumentClosedError
```

### The `.copy()` Escape Hatch

When users need to retain data outside the context manager, `.copy()` materializes
to a plain Python dataclass:

```python
with Document.open("file.docx") as doc:
    para_data = doc.paragraphs[0].copy()   # ParagraphData — plain Python
    run_data = doc.paragraphs[0].runs[0].copy()  # RunData — plain Python
    doc_data = doc.copy()                  # DocumentData — full snapshot

# All safe to use here — no FFI, no proxies, fully Python-owned
para_data.text       # plain string attribute
para_data.runs[0]    # RunData object, not a proxy
```

`.copy()` materializes the entire subtree below the call site:
- `run.copy()` → `RunData` with all formatting properties
- `para.copy()` → `ParagraphData` with `runs: list[RunData]`
- `doc.copy()` → `DocumentData` with full body snapshot

**Error message guidance**: When `DocumentClosedError` or `StaleProxyError` is raised,
the message should always mention `.copy()` as the solution.

---

## Document Body and Views

### doc.body — The Source of Truth

`doc.body` is a live `BodyView` representing the document's block-level element sequence.
It directly mirrors the OpenXML `<w:body>` element order. All other views are filtered
windows over `doc.body`.

```
doc.body  →  [Paragraph, Paragraph, Table, Paragraph, Image, Paragraph, Section]
```

### Filtered Views

All filtered views are **live** — they reflect the current state of `doc.body` on every
access. They are never copies.

```python
doc.paragraphs   # ParagraphView  — live filtered view of body, Paragraph elements only
doc.tables       # TableView      — live filtered view of body, Table elements only
doc.images       # ImageView      — live filtered view of body, Image elements only
doc.sections     # SectionView    — live filtered view of body, Section elements only
```

### View Contract (applies to all views)

All views implement the same base interface:

```python
# Indexing
view[0]          # first element — returns proxy
view[-1]         # last element
view[1:3]        # slice — returns a new view over that range, NOT a list

# Length
len(view)        # count of elements in this view

# Iteration
for element in view: ...

# Unambiguous positional access regardless of active index type
view.iloc[0]     # always integer positional
view.iloc[-1]
view.iloc[1:3]

# Filtering — returns a new view, stays on C# side
view.where(style="Heading1")
view.where(lambda e: e.word_count > 100)

# Bulk operations — single C# call, never O(n) FFI calls
view.where(style="OldStyle").set_style("NewStyle")

# Materialization — explicit opt-in to snapshot
list(view)         # list of proxies at this moment
view.copy()        # list of plain Python data objects — no proxies

# Concurrent modification guard
for element in view:
    view.remove(element)   # RuntimeError — same as dict during iteration
# Correct pattern:
for element in list(view):   # materialize first
    view.remove(element)
```

### Custom Index Types

Views support swappable index types, following the pandas mental model:

```python
from docx_native.indexes import RangeIndex, StyleIndex, BookmarkIndex, OutlineIndex

# Default — integer positional
doc.paragraphs[0]

# Style index
doc.paragraphs.reindex(StyleIndex)
doc.paragraphs["Heading1"]        # all Heading1 paragraphs — returns ParagraphView
doc.paragraphs["Heading1"][0]     # first Heading1

# Bookmark index
doc.paragraphs.reindex(BookmarkIndex)
doc.paragraphs["introduction"]

# Outline index
doc.paragraphs.reindex(OutlineIndex)
doc.paragraphs["1.2.3"]

# Create view with index without mutating original
view = doc.paragraphs.with_index(StyleIndex)

# iloc always available regardless of active index
doc.paragraphs.iloc[0]   # always first paragraph, ignores active index
```

**Non-unique keys always return a view, never a single element.** This is consistent
regardless of how many elements match. `doc.paragraphs["Heading1"]` always returns a
`ParagraphView`, even if only one Heading1 exists. This keeps the return type predictable.

### doc.group() — Multi-Type Views

`doc.group()` returns a `GroupView` — a live filtered view over `doc.body` scoped to
the specified types, in document order:

```python
# By type objects (preferred — IDE friendly, refactor safe)
doc.group(Paragraph, Image)
doc.group(Paragraph, Table, Image)

# By string aliases (convenience)
doc.group("paragraphs", "images")

# Do not allow mixing — raise TypeError
doc.group("paragraphs", Image)   # TypeError

# GroupView iteration yields mixed types in document order
for element in doc.group(Paragraph, Table):
    match element:
        case Paragraph(): print(element.text)
        case Table():     print(len(element.rows))

# GroupView exposes typed sub-views
view = doc.group(Paragraph, Image)
view.paragraphs   # ParagraphView — only paragraphs within this group
view.images       # ImageView — only images within this group

# GroupView supports the full view contract
view[0]
view.iloc[1:4]
view.where(...)
list(view)
```

### Adding Elements — `.append()` and `.insert()`

**Use `.paragraphs.append()` not `.add_paragraph()`.**

The document object is a collection, not a builder. All mutation goes through the views.
`.add_paragraph()` does not exist on the document object. It exists only in the compat
layer.

```python
# Correct — via views
doc.body.append(Paragraph("New"))
doc.body.append(Table(rows=3, cols=4))
doc.paragraphs.append(Paragraph("New"))

# Does not exist on native API
doc.add_paragraph("New")   # AttributeError — use doc.body.append() or doc.paragraphs.append()
```

**Semantic difference between body and filtered view append:**

```python
# Document body: [Para, Para, Table]

doc.body.append(Paragraph("New"))
# Result: [Para, Para, Table, Para]  ← after table, absolute end of body

doc.paragraphs.append(Paragraph("New"))
# Result: [Para, Para, Para, Table]  ← after last paragraph, before table
```

**Insert:**

```python
# body.insert — position among ALL body elements
doc.body.insert(0, Paragraph("First"))
doc.body.insert(after=some_table, item=Paragraph("After table"))
doc.body.insert(before=some_image, item=Table(rows=2, cols=2))

# paragraphs.insert — position among paragraphs only
doc.paragraphs.insert(0, Paragraph("First paragraph"))
doc.paragraphs.insert(after=existing_para, item=Paragraph("After this para"))

# iloc insert — always unambiguous integer position
doc.paragraphs.iloc.insert(0, Paragraph("First paragraph"))
```

**Type enforcement on filtered views:**

```python
doc.paragraphs.append(Table(rows=2, cols=2))
# TypeError: ParagraphView only accepts Paragraph elements. Use doc.body.append() instead.
```

---

## Paragraph API

```python
para = doc.paragraphs[0]

# Text
para.text = "Hello world"
para.text                      # "Hello world"

# Style
para.style = "Heading1"
para.style                     # "Heading1"

# Alignment
para.alignment = "left"        # left | right | center | justify

# Indentation (inches)
para.indent.left = 1.0
para.indent.right = 0.5
para.indent.first_line = 0.25

# Spacing (points)
para.spacing.before = 12
para.spacing.after = 6
para.spacing.line = 1.5        # multiplier

# Page control
para.keep_together = True
para.keep_with_next = True
para.page_break_before = True

# Runs
para.runs[0]
para.runs[-1]
para.runs[1:3]                 # RunView slice
para.runs.append(Run("bold text", bold=True))
para.runs.insert(0, Run("first"))
para.runs.insert(after=existing_run, item=Run("after"))

# Bulk run operations
para.runs.where(bold=True).set(bold=False)
para.runs.where(font="Arial").set(font="Calibri")

# Search within paragraph
para.find("revenue")           # list of (run_index, char_index)
para.find_runs("revenue")      # RunView of runs containing the text
```

---

## Run API

Runs are the leaf nodes of the document tree. They should feel like the simplest layer.
The proxy model applies identically to runs as to paragraphs.

### Text and Basic Formatting

```python
run = para.runs[0]

run.text = "Hello"
run.bold = True
run.italic = True
run.underline = True           # True = single underline
run.underline = "single"       # single | double | dotted | dashed | wave
run.strikethrough = True
```

### Capitalisation

```python
run.all_caps = True            # displays as ALL CAPS — stored as mixed case
run.small_caps = True          # displays as SMALL CAPS
run.capitalize = True          # first letter of each word
```

### Vertical Positioning

```python
run.superscript = True         # x²
run.subscript = True           # H₂O
run.baseline = 10              # manual baseline shift in points, positive = up
```

### Font

```python
run.font.name = "Arial"
run.font.name_eastasia = "MS Mincho"
run.font.name_complex = "Arial"
run.font.size = 12             # points
run.font.color = "#FF0000"
run.font.color = RGBColor(255, 0, 0)
run.font.color = "auto"
run.font.spacing = 2.0         # character spacing in points
run.font.kerning = 12          # kerning threshold in points
run.font.scale = 150           # horizontal scale percentage
```

### Highlight and Shading

```python
run.highlight = "yellow"
run.shading.fill = "#FFFF00"
run.shading.color = "#000000"
run.shading.pattern = "clear"
```

### Effects

```python
run.emboss = True
run.imprint = True
run.outline = True
run.shadow = True
run.hidden = True
```

### Language and Spell Check

```python
run.language = "en-US"
run.no_spell_check = True
run.no_grammar_check = True
```

### Run Construction

```python
# Keyword args
run = Run(
    text="Hello",
    bold=True,
    italic=False,
    all_caps=True,
    font=Font(name="Arial", size=12),
    color="#FF0000"
)

# Builder pattern
run = (Run("Hello")
    .bold()
    .font("Arial", size=12)
    .color("#FF0000")
    .superscript()
)
```

### Run Stale Detection

Runs check their own staleness only. If the parent paragraph is removed, the run's
native handle is already invalid and the C# side surfaces the error. Do not implement
multi-level chain checking — it adds complexity without benefit.

```python
run = para.runs[0]
para.runs.remove(run)
run.bold   # StaleProxyError
```

### Run Split and Merge

Split and merge return new proxies. The original proxy behaviour after a split is
undefined — document this clearly rather than tracking it:

```python
left, right = run.split(5)    # returns two new Run proxies
merged = para.runs[0:3].merge()  # returns one new Run proxy
```

### FFI Batching for Runs

When multiple properties need to be set on a run, use the `edit()` context manager
to batch into a single FFI call:

```python
# Without batching — three FFI calls
run.bold = True
run.italic = True
run.all_caps = True

# With batching — one FFI call
with run.edit() as r:
    r.bold = True
    r.italic = True
    r.all_caps = True
```

---

## Practical Examples

### Chemical Formula

```python
with Document.open("paper.docx") as doc:
    para = doc.paragraphs[0]
    para.runs.append(Run("H"))
    para.runs.append(Run("2", subscript=True))
    para.runs.append(Run("SO"))
    para.runs.append(Run("4", subscript=True))
```

### Bulk Style Update

```python
with Document.open("report.docx") as doc:
    doc.paragraphs \
       .where(style="Heading2") \
       .set_style("Heading3")
```

### Font Replacement

```python
with Document.open("report.docx") as doc:
    doc.paragraphs \
       .runs \
       .where(font="Times New Roman") \
       .set(font="Calibri", font_size=11)
```

### Extracting Data Safely

```python
with Document.open("report.docx") as doc:
    # copy() at any level materializes that subtree
    headings = [
        p.copy()
        for p in doc.paragraphs.where(style="Heading1")
    ]
# headings is a list of ParagraphData — safe to use anywhere
```

### Section Content Extraction

```python
with Document.open("report.docx") as doc:
    view = doc.group(Paragraph, Table, Image)
    headings = [e for e in view if isinstance(e, Paragraph) and e.style == "Heading1"]

    sections = {}
    for i, heading in enumerate(headings):
        start = view.index(heading)
        end = view.index(headings[i + 1]) if i + 1 < len(headings) else len(view)
        sections[heading.text] = view[start:end].copy()
```

---

## Compat Layer

The compat layer mimics `python-docx` exactly. It is a thin wrapper over the native API.

```python
from docx_native.compat import Document

# No context manager required — matches python-docx
doc = Document("file.docx")
doc.add_paragraph("Hello", style="Heading1")
doc.paragraphs[0].text
doc.save("out.docx")
```

### Implementation Principles

- `.add_paragraph()` exists **only** in the compat layer, not the native API
- Compat layer materializes eagerly — `doc.paragraphs` returns a `list`, not a view
- Compat layer opens and holds the document without a context manager — user calls
  `.save()` and the document is disposed on garbage collection
- No new concepts should leak from the native API into the compat layer
- The compat layer should be entirely implementable as a wrapper with no C# changes

```python
# compat/document.py
class Document:
    def __init__(self, path=None):
        self._native = NativeDocument.open(path) if path else NativeDocument.new()
        self._native.__enter__()   # open context manually

    def add_paragraph(self, text="", style=None):
        return self._native.paragraphs.append(Paragraph(text=text, style=style))

    @property
    def paragraphs(self):
        return list(self._native.paragraphs)   # eager — matches python-docx

    def save(self, path):
        self._native.save(path)

    def __del__(self):
        if self._native:
            self._native.__exit__(None, None, None)
```

---

## Error Types

```python
class DocxNativeError(Exception):
    """Base error for all docx_native errors"""

class DocumentClosedError(DocxNativeError):
    """Raised when a proxy is accessed after its document context has exited.
    Call .copy() inside the context manager to retain data outside it."""

class StaleProxyError(DocxNativeError):
    """Raised when a proxy is accessed after its element was removed.
    Call .copy() before removing to retain data."""

class OwnershipError(DocxNativeError):
    """Raised when an element from one document is used in another.
    Call .copy() to get a document-independent copy."""

class ViewMutationError(RuntimeError):
    """Raised when a view is mutated during iteration."""
```

---

## What Does Not Exist on the Native API

These exist **only** in the compat layer. They must not be added to the native API:

- `doc.add_paragraph()`
- `doc.add_table()`
- `doc.add_image()`
- `doc.add_heading()`
- `doc.add_run()`

If a user calls these on a native `Document` object they should get a clear `AttributeError`
pointing them to the correct native API equivalent.

---

## Design Principles Summary

1. **C# owns all document data** — Python holds proxies
2. **Context manager is the FFI boundary** — GC and disposal are invisible to the user
3. **Views are live** — they always reflect the current document state
4. **`.copy()` is the explicit escape hatch** — the only way to take Python ownership of data
5. **`doc` is a collection, not a builder** — mutation goes through views, not `add_*` methods
6. **Consistency over convenience** — the same model works at document, paragraph, and run level
7. **Errors are helpful** — every `StaleProxyError` and `DocumentClosedError` mentions `.copy()`
8. **Compat layer is a wrapper** — it adds no new concepts, only wraps the native API
9. **`iloc` is always available** — unambiguous integer access regardless of active index type
10. **Bulk operations stay on C# side** — `view.where(...).set(...)` is one FFI call, not O(n)
