# Concepts

## The proxy model

FastDocx uses a *proxy model*: all document data lives in the C# native layer, and Python
holds lightweight *proxy objects* — wrappers that contain only an integer handle pointing
to a C# object, not any document data themselves.

Every property read or write on a live proxy crosses the FFI boundary. There is no
Python-side cache of document data unless you explicitly call `snapshot()`.

```
C# NativeAOT binary
└── Document (owns all data)
    ├── Body
    │   ├── Paragraph  ←── Python: Paragraph proxy (holds handle)
    │   │   └── Run    ←── Python: Run proxy (holds handle)
    │   └── Table      ←── Python: Table proxy (holds handle)
    └── CoreProperties
```

## Construction state vs. live state

Every proxy type (Paragraph, Run, Table, …) exists in one of two states:

**Construction state** — the object has been created in Python but not yet appended to a
document. Data is held locally in a Python dict, not in the native layer.

```python
from fastdocx import Paragraph

para = Paragraph("Hello", style="Heading1")
# para is in construction state — no FFI has happened yet
```

**Live state** — the object has been appended to a document. From this point on, every
property access crosses the FFI boundary and the native layer is the source of truth.

```python
doc.paragraphs.append(para)
# para is now live — para.text crosses FFI on every access
para.text = "Updated"   # write goes directly to the C# document
```

The transition from construction to live is **one-way and permanent**. An object cannot
return to construction state.

### Why this matters

- A construction-state object can be re-used or passed around without triggering any FFI.
- Once live, every attribute access is a native call. For tight loops, prefer reading
  properties into local variables.
- You cannot append a live object to a second document. Use `snapshot()` first.

## DocumentView

`DocumentView[T]` is a *live view* — it holds a reference to the parent handle and the
collection name, and queries the native layer on every iteration or index access.

```python
paras = doc.paragraphs    # DocumentView[Paragraph] — no FFI yet
first = paras[0]          # FFI: fetch handle at index 0, wrap in Paragraph proxy
n = len(paras)            # FFI: get_count()
```

Because it is a live view, it always reflects the current document state:

```python
n = len(doc.paragraphs)     # 3
doc.add_paragraph("New")
len(doc.paragraphs)         # 4 — the view is live, not a snapshot
```

## The snapshot pattern

A live proxy is tied to its document. Closing the document invalidates all live proxies.
Use `snapshot()` inside the context manager to capture a document-independent copy:

```python
from fastdocx import snapshot

with Document.open("report.docx") as doc:
    para = doc.paragraphs[0]
    snap = snapshot(para)   # copy of data — no native handle

# doc is now closed; para is invalid; snap is still valid
print(snap.text)
```

`snapshot()` calls `__copydocelem__()` on the element, which reads all properties
from the native layer and returns a new construction-state object with no handle. The
returned object can be inspected, modified, and later appended to a different document.

### Ownership rule

A live element belongs to exactly one document. Passing a live element from document A
to document B raises `OwnershipError`. Always snapshot first:

```python
with Document.open("source.docx") as src:
    snap = snapshot(src.paragraphs[0])

with Document() as dst:
    dst.paragraphs.append(snap)    # OK — snap has no native handle
    dst.save("dest.docx")
```

## Error types

| Exception | Cause |
|---|---|
| `DocumentClosedError` | Accessing a proxy after `doc.close()` or after the context manager exits |
| `StaleProxyError` | Accessing a proxy after its element was removed (e.g., `doc.paragraphs.remove(para)`) |
| `OwnershipError` | Passing a live element from one document to another |
| `NativeRuntimeError` | The C# layer returned an error code or threw an exception |

All four are subclasses of `FastDocxError`, so you can catch them all with a single
`except FastDocxError` if needed.

## Performance notes

- Property reads and writes are individual FFI calls. For bulk reads, use
  `run.edit()` to batch writes, or `snapshot()` to read everything at once.
- The native library uses a C# NativeAOT binary — there is no JIT warm-up cost, but
  there *is* a per-call FFI overhead for every property access.
- `table.data` reads the entire table into a `list[list[str]]` in a single pass —
  prefer it over nested iteration when you only need cell text.
