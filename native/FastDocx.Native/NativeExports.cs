using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using FastDocx.Native.Marshalling;

namespace FastDocx.Native;

public static unsafe class NativeExports
{
    /// <summary>
    /// Creates a new empty document and returns an opaque handle.
    /// Returns 0 on failure.
    /// </summary>
    /// <returns>Document handle, or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "create_document", CallConvs = [typeof(CallConvCdecl)])]
    public static nint CreateDocument()
    {
        return DocumentBuilder.CreateDocument();
    }

    /// <summary>
    /// Opens an existing document from the given file path and returns an opaque handle.
    /// Returns 0 on failure.
    /// </summary>
    /// <param name="path">UTF-8 encoded file path bytes.</param>
    /// <param name="pathLen">Length of <paramref name="path"/> in bytes.</param>
    /// <returns>Document handle, or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "open_document", CallConvs = [typeof(CallConvCdecl)])]
    public static nint OpenDocument(byte* path, int pathLen)
    {
        return DocumentBuilder.OpenDocument(path, pathLen);
    }

    /// <summary>
    /// Adds an empty paragraph to the document and returns its handle.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="style">UTF-8 encoded style name bytes, or null.</param>
    /// <param name="styleLen">Length of <paramref name="style"/> in bytes; 0 if null.</param>
    /// <returns>Paragraph handle, or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "add_paragraph", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddParagraph(nint handle, byte* style, int styleLen)
    {
        return DocumentBuilder.AddParagraph(handle, style, styleLen);
    }

    /// <summary>
    /// Appends a run of text to an existing paragraph and returns its handle.
    /// </summary>
    /// <param name="paraHandle">Paragraph handle from add_paragraph.</param>
    /// <param name="text">UTF-8 encoded text bytes.</param>
    /// <param name="textLen">Length of <paramref name="text"/> in bytes.</param>
    /// <param name="bold">1 = bold, 0 = explicitly not bold, -1 = inherit from style.</param>
    /// <param name="italic">1 = italic, 0 = explicitly not italic, -1 = inherit from style.</param>
    /// <param name="fontSize">Half-point font size (e.g. 24 = 12pt), or 0 to inherit.</param>
    /// <returns>Run handle (non-zero), or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "add_run", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddRun(nint paraHandle, byte* text, int textLen, int bold, int italic, int fontSize)
    {
        return DocumentBuilder.AddRun(paraHandle, text, textLen, bold, italic, fontSize);
    }

    [UnmanagedCallersOnly(EntryPoint = "set_run_bold", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetRunBold(nint runHandle, int bold)
        => DocumentBuilder.SetRunBold(runHandle, bold);

    [UnmanagedCallersOnly(EntryPoint = "set_run_italic", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetRunItalic(nint runHandle, int italic)
        => DocumentBuilder.SetRunItalic(runHandle, italic);

    [UnmanagedCallersOnly(EntryPoint = "set_run_underline", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetRunUnderline(nint runHandle, int underline)
        => DocumentBuilder.SetRunUnderline(runHandle, underline);

    [UnmanagedCallersOnly(EntryPoint = "set_run_font_size", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetRunFontSize(nint runHandle, int halfPoints)
        => DocumentBuilder.SetRunFontSize(runHandle, halfPoints);

    [UnmanagedCallersOnly(EntryPoint = "set_run_font_name", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetRunFontName(nint runHandle, byte* name, int nameLen)
        => DocumentBuilder.SetRunFontName(runHandle, name, nameLen);

    /// <summary>
    /// Adds a heading paragraph to the document.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="text">UTF-8 encoded heading text bytes.</param>
    /// <param name="textLen">Length of <paramref name="text"/> in bytes.</param>
    /// <param name="level">Heading level 1–6.</param>
    /// <returns>Paragraph handle, or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "add_heading", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddHeading(
        nint handle,
        byte* text,
        int textLen,
        int level)
    {
        return DocumentBuilder.AddHeading(handle, text, textLen, level);
    }

    /// <summary>
    /// Registers a custom paragraph style on the document.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="def">Pointer to a <see cref="ParagraphStyleDef"/> describing the style.</param>
    /// <returns>0 on success, -1 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "register_paragraph_style", CallConvs = [typeof(CallConvCdecl)])]
    public static int RegisterParagraphStyle(nint handle, ParagraphStyleDef* def)
    {
        return DocumentBuilder.RegisterParagraphStyle(handle, def);
    }

    /// <summary>
    /// Adds a table to the document.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="rows">Number of rows.</param>
    /// <param name="cols">Number of columns.</param>
    /// <returns>Table handle, or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "add_table", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddTable(nint handle, int rows, int cols)
    {
        return DocumentBuilder.AddTable(handle, rows, cols);
    }

    /// <summary>
    /// Adds a pre-populated table to the document.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="cells">
    /// Flat array of <c>rows * cols</c> UTF-8 string slices in row-major order.
    /// </param>
    /// <param name="rows">Number of rows.</param>
    /// <param name="cols">Number of columns.</param>
    /// <returns>Table handle, or 0 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "add_table_with_data", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddTableWithData(nint handle, ByteSlice* cells, int rows, int cols)
    {
        return DocumentBuilder.AddTableWithData(handle, cells, rows, cols);
    }

    /// <summary>
    /// Sets the text content of a table cell.
    /// </summary>
    /// <param name="tableHandle">Table handle from add_table.</param>
    /// <param name="row">Zero-based row index.</param>
    /// <param name="col">Zero-based column index.</param>
    /// <param name="text">UTF-8 encoded cell text bytes.</param>
    /// <param name="textLen">Length of <paramref name="text"/> in bytes.</param>
    /// <returns>0 on success, -1 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "set_cell_text", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetCellText(
        nint tableHandle,
        int row,
        int col,
        byte* text,
        int textLen)
    {
        return DocumentBuilder.SetCellText(tableHandle, row, col, text, textLen);
    }

    /// <summary>
    /// Returns the number of paragraphs in the document body, or -1 on failure.
    /// </summary>
    /// <param name="handle">Document handle from create_document or open_document.</param>
    [UnmanagedCallersOnly(EntryPoint = "get_paragraph_count", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetParagraphCount(nint handle)
    {
        return DocumentBuilder.GetParagraphCount(handle);
    }

    /// <summary>
    /// Writes the plain text of the paragraph at <paramref name="index"/> into
    /// <paramref name="buf"/>. Returns bytes written on success, 0 if the buffer
    /// is too small (required byte count is written to <paramref name="required"/>),
    /// or -1 on error.
    /// </summary>
    [UnmanagedCallersOnly(EntryPoint = "get_paragraph_text", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetParagraphText(nint handle, int index, byte* buf, int bufLen, int* required)
    {
        return DocumentBuilder.GetParagraphText(handle, index, buf, bufLen, required);
    }

    /// <summary>
    /// Writes the style ID of the paragraph at <paramref name="index"/> into
    /// <paramref name="buf"/>. Returns bytes written (0 if no explicit style),
    /// or -1 on error.
    /// </summary>
    [UnmanagedCallersOnly(EntryPoint = "get_paragraph_style", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetParagraphStyle(nint handle, int index, byte* buf, int bufLen, int* required)
    {
        return DocumentBuilder.GetParagraphStyle(handle, index, buf, bufLen, required);
    }

    /// <summary>
    /// Removes the paragraph at <paramref name="index"/> from the document body.
    /// </summary>
    /// <param name="handle">Document handle from create_document or open_document.</param>
    /// <param name="index">Zero-based paragraph index.</param>
    /// <returns>0 on success, -2 if index is out of range, -1 on other failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "remove_paragraph", CallConvs = [typeof(CallConvCdecl)])]
    public static int RemoveParagraph(nint handle, int index)
    {
        return DocumentBuilder.RemoveParagraph(handle, index);
    }

    /// <summary>
    /// Adds a horizontal line to the document.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <returns>0 on success, -1 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "add_horizontal_line", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddHorizontalLine(nint handle)
    {
        return DocumentBuilder.AddHorizontalLine(handle);
    }

    /// <summary>
    /// Saves the document to the given file path.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="path">UTF-8 encoded file path bytes.</param>
    /// <param name="pathLen">Length of <paramref name="path"/> in bytes.</param>
    /// <returns>0 on success, -1 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "save_document", CallConvs = [typeof(CallConvCdecl)])]
    public static int SaveDocument(nint handle, byte* path, int pathLen)
    {
        return DocumentBuilder.SaveDocument(handle, path, pathLen);
    }

    /// <summary>
    /// Sets the page margins on the document.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    /// <param name="top">Top margin in twips (twentieths of a point).</param>
    /// <param name="right">Right margin in twips.</param>
    /// <param name="bottom">Bottom margin in twips.</param>
    /// <param name="left">Left margin in twips.</param>
    /// <returns>0 on success, -1 on failure.</returns>
    [UnmanagedCallersOnly(EntryPoint = "set_document_margins", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetDocumentMargins(nint handle, int top, int right, int bottom, int left)
    {
        return DocumentBuilder.SetDocumentMargins(handle, top, right, bottom, left);
    }

    /// <summary>
    /// Frees all resources associated with the document handle.
    /// </summary>
    /// <param name="handle">Document handle from create_document.</param>
    [UnmanagedCallersOnly(EntryPoint = "free_document", CallConvs = [typeof(CallConvCdecl)])]
    public static void FreeDocument(nint handle)
    {
        DocumentBuilder.FreeDocument(handle);
    }
}
