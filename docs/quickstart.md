# Quickstart

## Installation

```bash
pip install navyfox
```

## Creating a document

```python
from navyfox import Document

doc = Document()
doc.add_heading("Project Report", level=1)

para = doc.add_paragraph()
para.add_run("This report summarises Q1 findings.").bold = True

table = doc.add_table(rows=3, cols=2)
table[0, 0].text = "Region"
table[0, 1].text = "Revenue"
table[1, 0].text = "North"
table[1, 1].text = "$1.2M"

doc.save("report.docx")
doc.close()
```

## Using the context manager

Prefer the context manager — it ensures the native handle is released even if an
exception occurs:

```python
with Document() as doc:
    doc.add_paragraph("Hello, world!")
    doc.save("hello.docx")
# doc is automatically closed on exit
```

## Opening an existing document

```python
with Document.open("report.docx") as doc:
    for para in doc.paragraphs:
        print(para.text)
```

## In-place editing

`Document.edit()` opens a document and saves it back to the same path automatically
when the context manager exits:

```python
with Document.edit("report.docx") as doc:
    doc.paragraphs[0].text = "Updated heading"
# saved back to report.docx on __exit__
```

## Document metadata

```python
with Document() as doc:
    doc.title = "Annual Report"
    doc.author = "Jane Smith"
    doc.save("annual.docx")
```

## Paragraphs and runs

A `Paragraph` is a block of text. A `Run` is a contiguous span of text inside a
paragraph that shares the same character formatting:

```python
with Document() as doc:
    para = doc.add_paragraph()

    run1 = para.add_run("This is ")
    run2 = para.add_run("bold")
    run2.bold = True
    run3 = para.add_run(" and this is ")
    run4 = para.add_run("italic.")
    run4.italic = True

    doc.save("runs.docx")
```

You can also set formatting at construction time:

```python
from navyfox import Run

run = Run("Hello", bold=True, font_name="Arial", font_size=14)
```

### Run formatting reference

| Property | Type | Notes |
|---|---|---|
| `bold` | `bool` | |
| `italic` | `bool` | |
| `strikethrough` | `bool` | |
| `underline` | `bool` or `"single"` / `"double"` / `"dotted"` / `"dashed"` / `"wave"` | |
| `all_caps` | `bool` | Mutually exclusive with `small_caps` |
| `small_caps` | `bool` | Mutually exclusive with `all_caps` |
| `superscript` | `bool` | Mutually exclusive with `subscript` |
| `subscript` | `bool` | Mutually exclusive with `superscript` |
| `color` | `str` (`"#RRGGBB"`) or `Color` | |
| `highlight` | `str` (colour name) | |
| `font_name` | `str` | |
| `font_size` | `float` (points) | `0.0` = inherit |

### Batching run edits

Use `run.format()` to send multiple property updates in a single FFI call:

```python
run.format(bold=True, italic=True, color="#CC0000")
```

## Paragraph alignment and style

```python
para = doc.add_paragraph("Centred text")
para.alignment = "center"

heading = doc.add_heading("Chapter 1", level=2)  # applies Heading2 style
```

## Tables

```python
with Document() as doc:
    table = doc.add_table(rows=3, cols=3)

    # Set headers
    for col_i, header in enumerate(["Name", "Dept", "Score"]):
        table[0, col_i].text = header

    # Fill data
    table[1, 0].text = "Alice"
    table[1, 1].text = "Eng"
    table[1, 2].text = "95"

    table[2, 0].text = "Bob"
    table[2, 1].text = "Sales"
    table[2, 2].text = "87"

    doc.save("table.docx")
```

### Iterating table rows and cells

```python
for row in table.rows:
    for cell in row.cells:
        print(cell.text, end="\t")
    print()
```

### Reading table data as a grid

`table.data` returns a generator of rows — handy for dropping into a DataFrame:

```python
import pandas as pd
rows = list(table.data)
df = pd.DataFrame(rows[1:], columns=rows[0])
```

## Horizontal rules

```python
doc.add_horizontal_rule(line_style="double", line_width=3.0, line_color="#888888")
```

Or construct one explicitly and append it:

```python
from navyfox import HorizontalRule

rule = HorizontalRule(line_style="dashed")
doc.paragraphs.append(rule)
```

## Sections

```python
section = doc.sections[0]
section.orientation = "landscape"
section.page_width = 11.0   # inches
section.page_height = 8.5   # inches
```

## Styles

```python
# Access styles by name
style = doc.styles["Heading1"]
print(style.name, style.type, style.based_on)

# Check if a style exists
if "CustomStyle" in doc.styles:
    para.style = "CustomStyle"
```

## Color

```python
from navyfox import Run
from navyfox.units import Color

run.color = Color(0xCC, 0x00, 0x00)   # RGB constructor
run.color = "#CC0000"                  # hex string
run.color = Color.RED                  # named constant
```

## Proxy lifecycle

Objects start in **construction** state before being appended:

```python
from navyfox import Paragraph

para = Paragraph("Hello")      # construction state — data held locally
doc.paragraphs.append(para)    # para transitions to live state
para.text = "Updated"          # crosses FFI immediately — updates the document
```

See {doc}`concepts` for a full explanation.

## Snapshots (using data after document close)

A live proxy becomes invalid once its document is closed. Use `snapshot()` to capture
a document-independent copy:

```python
from navyfox import snapshot

with Document.open("report.docx") as doc:
    para = doc.paragraphs[0]
    snap = snapshot(para)          # document-independent copy

# doc is now closed — snap is still usable
print(snap.text)
```

## Error handling

NavyFox raises specific subclasses of `NavyFoxError`:

```python
from navyfox.errors import DocumentClosedError, StaleProxyError, OwnershipError

try:
    doc.close()
    doc.paragraphs[0].text  # raises DocumentClosedError
except DocumentClosedError:
    print("Document is closed — use snapshot() inside the context manager.")
```

| Exception | When raised |
|---|---|
| `DocumentClosedError` | Accessing a proxy after its document has been closed |
| `StaleProxyError` | Accessing a proxy after its element was removed from the document |
| `OwnershipError` | Using an element from one document in another |
| `NativeRuntimeError` | An FFI call to the native library failed |
