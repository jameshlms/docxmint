"""CFFI bindings matching the C# [UnmanagedCallersOnly] exports.

The FFI is defined here once and shared across the package.  The actual
shared-library path is resolved by :mod:`fastdocx._native.loader`.
"""

from __future__ import annotations

import cffi  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# C declarations — must mirror NativeExports.cs exactly
# ---------------------------------------------------------------------------

_CDEF = """
/*
 * create_document()
 *   Returns an opaque document handle (non-zero on success, 0 on failure).
 */
intptr_t create_document(void);

/*
 * open_document(path, pathLen)
 *   Opens an existing .docx file and returns an opaque document handle.
 *   Returns 0 on failure.
 */
intptr_t open_document(const uint8_t *path, int pathLen);

/*
 * add_paragraph(handle, style, styleLen)
 *   Creates an empty paragraph with an optional named style.
 *   style may be NULL with styleLen == 0 to use the document default.
 *   Returns an opaque paragraph handle (non-zero), or 0 on failure.
 */
intptr_t add_paragraph(
    intptr_t handle,
    const uint8_t *style, int styleLen
);

/*
 * add_run(paraHandle, text, textLen, bold, italic, fontSize)
 *   Appends a run of text to an existing paragraph.
 *   bold/italic: 1 = explicit on, 0 = explicit off, -1 = inherit from style.
 *   fontSize is in half-points (e.g. 24 = 12pt); 0 = inherit from style.
 *   Returns an opaque run handle (non-zero), or 0 on failure.
 */
intptr_t add_run(
    intptr_t paraHandle,
    const uint8_t *text, int textLen,
    int bold,
    int italic,
    int fontSize
);

int set_run_bold(intptr_t runHandle, int bold);
int set_run_italic(intptr_t runHandle, int italic);
int set_run_underline(intptr_t runHandle, int underline);
int set_run_font_size(intptr_t runHandle, int halfPoints);
int set_run_font_name(intptr_t runHandle, const uint8_t *name, int nameLen);

/*
 * add_heading(handle, text, textLen, level)
 *   level is 1-6.
 *   Returns an opaque paragraph handle (non-zero), or 0 on failure.
 */
intptr_t add_heading(
    intptr_t handle,
    const uint8_t *text, int textLen,
    int level
);

/*
 * add_table(handle, rows, cols)
 *   Returns an opaque table handle (non-zero), or 0 on failure.
 */
intptr_t add_table(intptr_t handle, int rows, int cols);

/*
 * register_paragraph_style(handle, def)
 *   Registers a named paragraph style on the document.
 *   Returns 0 on success, -1 on failure.
 */
typedef struct {
    const uint8_t *style_id;  int style_id_len;
    const uint8_t *based_on;  int based_on_len;
    int bold;
    int italic;
    int font_size;
    const uint8_t *color;     int color_len;
    int alignment;
    int space_before;
    int space_after;
} ParagraphStyleDef;
int register_paragraph_style(intptr_t handle, const ParagraphStyleDef *def);

/*
 * add_table_with_data(handle, cells, rows, cols)
 *   cells is a flat row-major array of ByteSlice, length rows*cols.
 *   Returns an opaque table handle (non-zero), or 0 on failure.
 */
typedef struct { const uint8_t *data; int len; } ByteSlice;
intptr_t add_table_with_data(intptr_t handle, const ByteSlice *cells, int rows, int cols);

/*
 * set_cell_text(tableHandle, row, col, text, textLen)
 *   Returns 0 on success, -1 on failure.
 */
int set_cell_text(
    intptr_t tableHandle,
    int row, int col,
    const uint8_t *text, int textLen
);

/*
 * remove_paragraph(handle, index)
 *   Removes the paragraph at zero-based index from the document body.
 *   Returns 0 on success, -2 if index is out of range, -1 on other failure.
 */
int remove_paragraph(intptr_t handle, int index);

/*
 * get_paragraph_count(handle)
 *   Returns the number of paragraphs in the document body, or -1 on failure.
 */
int get_paragraph_count(intptr_t handle);

/*
 * get_paragraph_text(handle, index, buf, bufLen, required)
 *   Writes the plain text of paragraph[index] into buf.
 *   Returns bytes written on success, 0 if buf is too small (*required holds
 *   the needed byte count), or -1 on error.
 */
int get_paragraph_text(intptr_t handle, int index, uint8_t *buf, int bufLen, int *required);

/*
 * get_paragraph_style(handle, index, buf, bufLen, required)
 *   Writes the style ID of paragraph[index] into buf.
 *   Returns bytes written (0 if no explicit style), or -1 on error.
 */
int get_paragraph_style(intptr_t handle, int index, uint8_t *buf, int bufLen, int *required);

/*
 * save_document(handle, path, pathLen)
 *   path is a UTF-8 encoded file system path.
 *   Returns 0 on success, -1 on failure.
 */
int save_document(intptr_t handle, const uint8_t *path, int pathLen);

/*
 * free_document(handle)
 *   Releases all resources held by the document.
 */
void free_document(intptr_t handle);
"""

_ffi = cffi.FFI()
_ffi.cdef(_CDEF)


class NativeLib:
    """Thin wrapper around the loaded CFFI library instance.

    Exposes each export as a callable attribute so call-sites do not need to
    dereference ``lib.lib`` themselves.  Also exposes ``ffi`` for buffer
    construction if callers need it.
    """

    def __init__(self, so_path: str) -> None:
        self._lib = _ffi.dlopen(so_path)
        self.ffi = _ffi

    # --- forwarding helpers -------------------------------------------------

    def create_document(self) -> int:
        result: int = self._lib.create_document()
        return result

    def open_document(self, path: bytes, path_len: int) -> int:
        result: int = self._lib.open_document(path, path_len)
        return result

    def add_paragraph(self, handle: int, style: bytes, style_len: int) -> int:
        result: int = self._lib.add_paragraph(handle, style if style else _ffi.NULL, style_len)
        return result

    def add_run(
        self,
        para_handle: int,
        text: bytes,
        text_len: int,
        bold: int,
        italic: int,
        font_size: int,
    ) -> int:
        result: int = self._lib.add_run(para_handle, text, text_len, bold, italic, font_size)
        return result

    def set_run_bold(self, run_handle: int, bold: int) -> int:
        result: int = self._lib.set_run_bold(run_handle, bold)
        return result

    def set_run_italic(self, run_handle: int, italic: int) -> int:
        result: int = self._lib.set_run_italic(run_handle, italic)
        return result

    def set_run_underline(self, run_handle: int, underline: int) -> int:
        result: int = self._lib.set_run_underline(run_handle, underline)
        return result

    def set_run_font_size(self, run_handle: int, half_points: int) -> int:
        result: int = self._lib.set_run_font_size(run_handle, half_points)
        return result

    def set_run_font_name(self, run_handle: int, name: bytes, name_len: int) -> int:
        result: int = self._lib.set_run_font_name(run_handle, name, name_len)
        return result

    def add_heading(
        self,
        handle: int,
        text: bytes,
        text_len: int,
        level: int,
    ) -> int:
        result: int = self._lib.add_heading(handle, text, text_len, level)
        return result

    def register_paragraph_style(
        self,
        handle: int,
        style_id: str,
        based_on: str | None,
        bold: bool,
        italic: bool,
        font_size: int,
        color: str | None,
        alignment: int,
        space_before: int,
        space_after: int,
    ) -> int:
        sid = style_id.encode("utf-8")
        bon = based_on.encode("utf-8") if based_on else b""
        col = color.encode("utf-8") if color else b""
        def_ = _ffi.new("ParagraphStyleDef *")
        def_.style_id     = _ffi.from_buffer(sid)
        def_.style_id_len = len(sid)
        def_.based_on     = _ffi.from_buffer(bon) if bon else _ffi.NULL
        def_.based_on_len = len(bon)
        def_.bold         = int(bold)
        def_.italic       = int(italic)
        def_.font_size    = font_size
        def_.color        = _ffi.from_buffer(col) if col else _ffi.NULL
        def_.color_len    = len(col)
        def_.alignment    = alignment
        def_.space_before = space_before
        def_.space_after  = space_after
        result: int = self._lib.register_paragraph_style(handle, def_)
        return result

    def add_table(self, handle: int, rows: int, cols: int) -> int:
        result: int = self._lib.add_table(handle, rows, cols)
        return result

    def add_table_with_data(
        self,
        handle: int,
        data: list[list[str]],
        rows: int,
        cols: int,
    ) -> int:
        # Encode every cell up front; keep references alive for the FFI call.
        encoded: list[bytes] = [
            cell.encode("utf-8") for row in data for cell in row
        ]
        buf = _ffi.new("ByteSlice[]", rows * cols)
        for i, b in enumerate(encoded):
            buf[i].data = _ffi.from_buffer(b)
            buf[i].len = len(b)
        result: int = self._lib.add_table_with_data(handle, buf, rows, cols)
        return result

    def set_cell_text(
        self,
        table_handle: int,
        row: int,
        col: int,
        text: bytes,
        text_len: int,
    ) -> int:
        result: int = self._lib.set_cell_text(table_handle, row, col, text, text_len)
        return result

    def remove_paragraph(self, handle: int, index: int) -> int:
        result: int = self._lib.remove_paragraph(handle, index)
        return result

    def get_paragraph_count(self, handle: int) -> int:
        result: int = self._lib.get_paragraph_count(handle)
        return result

    def get_paragraph_text(self, handle: int, index: int) -> str:
        """Return the plain text of paragraph at *index*, retrying if the initial buffer is too small."""
        buf_size = 1024
        while True:
            buf = _ffi.new(f"uint8_t[{buf_size}]")
            required = _ffi.new("int *")
            n = self._lib.get_paragraph_text(handle, index, buf, buf_size, required)
            if n == -1:
                raise RuntimeError(f"get_paragraph_text failed for index {index}")
            if n == 0:
                needed = required[0]
                if needed == 0:
                    return ""
                buf_size = needed
                continue
            return _ffi.unpack(buf, n).decode("utf-8")

    def get_paragraph_style(self, handle: int, index: int) -> str:
        """Return the style ID of paragraph at *index*, or '' if no explicit style."""
        buf_size = 256
        while True:
            buf = _ffi.new(f"uint8_t[{buf_size}]")
            required = _ffi.new("int *")
            n = self._lib.get_paragraph_style(handle, index, buf, buf_size, required)
            if n == -1:
                raise RuntimeError(f"get_paragraph_style failed for index {index}")
            if n == 0:
                needed = required[0]
                if needed == 0:
                    return ""
                buf_size = needed
                continue
            return _ffi.unpack(buf, n).decode("utf-8")

    def save_document(self, handle: int, path: bytes, path_len: int) -> int:
        result: int = self._lib.save_document(handle, path, path_len)
        return result

    def free_document(self, handle: int) -> None:
        self._lib.free_document(handle)
