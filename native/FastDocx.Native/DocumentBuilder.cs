using System.Collections.Concurrent;
using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace FastDocx.Native;

// ---------------------------------------------------------------------------
// DocumentState — lifetime-managed wrapper around an open WordprocessingDocument
// ---------------------------------------------------------------------------

internal sealed record DocumentState(WordprocessingDocument Document, MemoryStream Stream);

// ---------------------------------------------------------------------------
// Element wrappers — one sealed class per element type
// ---------------------------------------------------------------------------

internal abstract class ElemWrapper(nint docHandle)
{
    public readonly nint DocHandle = docHandle;
    public abstract string TypeName { get; }
}

internal sealed class DocElem(DocumentState state) : ElemWrapper(0)
{
    public override string TypeName => "document";
    public readonly DocumentState State = state;
}

internal sealed class ParaElem(Paragraph para, nint docHandle) : ElemWrapper(docHandle)
{
    public override string TypeName => "paragraph";
    public readonly Paragraph Para = para;
}

internal sealed class RunElem : ElemWrapper
{
    public override string TypeName => "run";
    public readonly Run Run;
    public RunElem(Run run, nint docHandle) : base(docHandle) => Run = run;
}

internal sealed class TableElem : ElemWrapper
{
    public override string TypeName => "table";
    public readonly Table Table;
    public readonly TableCell[,] Cells;
    public readonly int Rows;
    public readonly int Cols;
    public TableElem(Table table, TableCell[,] cells, int rows, int cols, nint docHandle)
        : base(docHandle)
    {
        Table = table;
        Cells = cells;
        Rows = rows;
        Cols = cols;
    }
}

internal sealed class RowElem : ElemWrapper
{
    public override string TypeName => "row";
    public readonly TableRow Row;
    public readonly int RowIdx;
    public readonly nint TableHandle;
    public RowElem(TableRow row, int rowIdx, nint tableHandle, nint docHandle)
        : base(docHandle)
    {
        Row = row;
        RowIdx = rowIdx;
        TableHandle = tableHandle;
    }
}

internal sealed class CellElem : ElemWrapper
{
    public override string TypeName => "cell";
    public readonly TableCell Cell;
    public readonly int RowIdx;
    public readonly int ColIdx;
    public readonly nint RowHandle;
    public CellElem(TableCell cell, int rowIdx, int colIdx, nint rowHandle, nint docHandle)
        : base(docHandle)
    {
        Cell = cell;
        RowIdx = rowIdx;
        ColIdx = colIdx;
        RowHandle = rowHandle;
    }
}

// ---------------------------------------------------------------------------
// DocumentBuilder — unified handle registry and static helpers
// ---------------------------------------------------------------------------

internal static unsafe partial class DocumentBuilder
{
    // Unified element registry
    private static readonly ConcurrentDictionary<nint, ElemWrapper> SElements = new();

    // Reverse maps for stable handles (OpenXml object → handle integer)
    private static readonly ConcurrentDictionary<Paragraph, nint> SParagraphHandles = new();
    private static readonly ConcurrentDictionary<Run, nint> SRunHandles = new();
    private static readonly ConcurrentDictionary<Table, nint> STableHandles = new();
    private static readonly ConcurrentDictionary<TableRow, nint> SRowHandles = new();
    private static readonly ConcurrentDictionary<TableCell, nint> SCellHandles = new();

    private static long _sNextHandle = 1;
    private static nint NextHandle() => (nint)Interlocked.Increment(ref _sNextHandle);

    // --- String helpers ---

    private static string ReadStr(byte* ptr, int len) =>
        Encoding.UTF8.GetString(ptr, len);

    private static int WriteStr(string s, byte* buf, int bufLen, int* required)
    {
        var bytes = Encoding.UTF8.GetBytes(s);
        *required = bytes.Length;
        if (bytes.Length == 0) return 0;
        if (bytes.Length > bufLen) return 0;
        bytes.AsSpan().CopyTo(new Span<byte>(buf, bytes.Length));
        return bytes.Length;
    }

    // --- Body helper ---

    private static Body GetBody(DocElem d) =>
        d.State.Document.MainDocumentPart!.Document!.Body!;

    // --- Handle factory methods (lazy, stable) ---

    internal static nint GetOrCreateParagraphHandle(Paragraph para, nint docHandle)
    {
        if (SParagraphHandles.TryGetValue(para, out var h)) return h;
        h = NextHandle();
        SParagraphHandles[para] = h;
        SElements[h] = new ParaElem(para, docHandle);
        return h;
    }

    internal static nint GetOrCreateRunHandle(Run run, nint docHandle)
    {
        if (SRunHandles.TryGetValue(run, out var h)) return h;
        h = NextHandle();
        SRunHandles[run] = h;
        SElements[h] = new RunElem(run, docHandle);
        return h;
    }

    internal static nint GetOrCreateTableHandle(
        Table table, TableCell[,] cells, int rows, int cols, nint docHandle)
    {
        if (STableHandles.TryGetValue(table, out var h)) return h;
        h = NextHandle();
        STableHandles[table] = h;
        SElements[h] = new TableElem(table, cells, rows, cols, docHandle);
        return h;
    }

    internal static nint GetOrCreateRowHandle(
        TableRow row, int rowIdx, nint tableHandle, nint docHandle)
    {
        if (SRowHandles.TryGetValue(row, out var h)) return h;
        h = NextHandle();
        SRowHandles[row] = h;
        SElements[h] = new RowElem(row, rowIdx, tableHandle, docHandle);
        return h;
    }

    internal static nint GetOrCreateCellHandle(
        TableCell cell, int rowIdx, int colIdx, nint rowHandle, nint docHandle)
    {
        if (SCellHandles.TryGetValue(cell, out var h)) return h;
        h = NextHandle();
        SCellHandles[cell] = h;
        SElements[h] = new CellElem(cell, rowIdx, colIdx, rowHandle, docHandle);
        return h;
    }

    // --- OpenXml bool helper ---
    // Returns -1 (unset), 0 (explicit false), or 1 (true/present).

    private static int GetOoxmlBool(OpenXmlElement? elem)
    {
        if (elem is null) return -1;
        foreach (var attr in elem.GetAttributes())
        {
            if (attr.LocalName == "val")
            {
                return string.Equals(attr.Value, "false", StringComparison.OrdinalIgnoreCase)
                    || attr.Value == "0"
                    ? 0 : 1;
            }
        }
        return 1; // element present, no val → true
    }
}
