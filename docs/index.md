# DocxMint

**DocxMint** is a Python library for creating and editing `.docx` files, backed by a C# Native AOT shared library. All document state lives in the native layer; Python holds lightweight proxy objects that cross the FFI boundary on every read and write.

```{toctree}
:maxdepth: 2
:caption: Contents

quickstart
concepts
api/index
```

## Features

- Create, open, and save `.docx` documents
- Paragraphs, runs, tables, sections, and styles
- Live proxy model — mutations to a proxy cross the FFI boundary immediately and update the underlying document
- `snapshot()` — capture a document-independent copy of any element for use after the document is closed
- Cross-platform: Linux x64/ARM64, Windows x64/ARM64, macOS ARM64/x64

## At a glance

```python
from docxmint import Document

with Document() as doc:
    doc.title = "Q1 Report"
    doc.add_heading("Executive Summary", level=1)

    para = doc.add_paragraph()
    run = para.add_run("Revenue grew 18 % year-on-year.")
    run.bold = True

    table = doc.add_table(rows=2, cols=2)
    table[0, 0].text = "Region"
    table[0, 1].text = "Revenue"
    table[1, 0].text = "North"
    table[1, 1].text = "$1.2 M"

    doc.save("report.docx")
```

## Architecture

DocxMint uses a *proxy model*: the C# backend owns all document data; Python holds integer handles that reference C# objects. Every property access crosses the FFI boundary — there is no Python-side cache unless you call `snapshot()`.

See {doc}`concepts` for a full explanation of the proxy lifecycle, construction state, live state, and the snapshot pattern.
