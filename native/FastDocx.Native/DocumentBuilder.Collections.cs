using DocumentFormat.OpenXml.Wordprocessing;

namespace FastDocx.Native;

internal static unsafe partial class DocumentBuilder
{
    // -----------------------------------------------------------------------
    // GetCount — number of children in a named collection
    // -----------------------------------------------------------------------

    internal static int GetCount(nint handle, byte* collection, int collectionLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var col = ReadStr(collection, collectionLen);
        try
        {
            return elem switch
            {
                DocElem d => CountBodyCollection(d, col),
                ParaElem p => col is "runs" ? p.Para.Elements<Run>().Count() : -1,
                TableElem t => col switch
                {
                    "rows" => t.Table.Elements<TableRow>().Count(),
                    "cells" => t.Rows * t.Cols,
                    _ => -1
                },
                RowElem r => col is "cells" ? r.Row.Elements<TableCell>().Count() : -1,
                CellElem c => col is "paragraphs"
                    ? c.Cell.Elements<Paragraph>().Count()
                    : -1,
                _ => -1
            };
        }
        catch { return -1; }
    }

    private static int CountBodyCollection(DocElem d, string col)
    {
        var body = GetBody(d);
        return col switch
        {
            "body" => body.ChildElements.Count(e => e is Paragraph || e is Table),
            "paragraphs" => body.Elements<Paragraph>().Count(),
            "tables" => body.Elements<Table>().Count(),
            "sections" => 0,   // sections not yet implemented
            _ => -1
        };
    }

    // -----------------------------------------------------------------------
    // GetChildHandle — handle for the i-th element of a named collection
    // -----------------------------------------------------------------------

    internal static nint GetChildHandle(
        nint handle, byte* collection, int collectionLen, int index)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return 0;
        var col = ReadStr(collection, collectionLen);
        try
        {
            return elem switch
            {
                DocElem d => GetBodyChild(d, handle, col, index),
                ParaElem p when col is "runs" => GetRunChild(p, handle, index),
                TableElem t when col is "rows" => GetRowChild(t, handle, index),
                TableElem t when col is "cells" => GetFlatCellChild(t, handle, index),
                RowElem r when col is "cells" => GetCellChild(r, handle, index),
                CellElem c when col is "paragraphs" => GetCellParaChild(c, handle, index),
                _ => 0
            };
        }
        catch { return 0; }
    }

    private static nint GetBodyChild(DocElem d, nint docHandle, string col, int index)
    {
        var body = GetBody(d);
        if (col == "body")
        {
            var all = body.ChildElements.Where(e => e is Paragraph || e is Table).ToList();
            if (index < 0) index = all.Count + index;
            if (index < 0 || index >= all.Count) return 0;
            return all[index] switch
            {
                Paragraph p => GetOrCreateParagraphHandle(p, docHandle),
                Table t => GetOrCreateTableHandle(t, GetTableCells(t), GetTableRows(t), GetTableCols(t), docHandle),
                _ => 0
            };
        }
        if (col == "paragraphs")
        {
            var paras = body.Elements<Paragraph>().ToList();
            if (index < 0) index = paras.Count + index;
            if (index < 0 || index >= paras.Count) return 0;
            return GetOrCreateParagraphHandle(paras[index], docHandle);
        }
        if (col == "tables")
        {
            var tables = body.Elements<Table>().ToList();
            if (index < 0) index = tables.Count + index;
            if (index < 0 || index >= tables.Count) return 0;
            var table = tables[index];
            return GetOrCreateTableHandle(
                table, GetTableCells(table), GetTableRows(table), GetTableCols(table), docHandle);
        }
        return 0;
    }

    private static nint GetRunChild(ParaElem p, nint docHandle, int index)
    {
        var runs = p.Para.Elements<Run>().ToList();
        if (index < 0) index = runs.Count + index;
        if (index < 0 || index >= runs.Count) return 0;
        return GetOrCreateRunHandle(runs[index], docHandle);
    }

    private static nint GetRowChild(TableElem t, nint tableHandle, int index)
    {
        var rows = t.Table.Elements<TableRow>().ToList();
        if (index < 0) index = rows.Count + index;
        if (index < 0 || index >= rows.Count) return 0;
        return GetOrCreateRowHandle(rows[index], index, tableHandle, t.DocHandle);
    }

    private static nint GetFlatCellChild(TableElem t, nint tableHandle, int index)
    {
        // Flat access: table[i] → row = i/cols, col = i%cols
        if (t.Cols == 0) return 0;
        var row = index / t.Cols;
        var col = index % t.Cols;
        if (row < 0 || row >= t.Rows) return 0;
        var rowElem = t.Table.Elements<TableRow>().ElementAtOrDefault(row);
        if (rowElem is null) return 0;
        var rowHandle = GetOrCreateRowHandle(rowElem, row, tableHandle, t.DocHandle);
        var cellElem = rowElem.Elements<TableCell>().ElementAtOrDefault(col);
        if (cellElem is null) return 0;
        return GetOrCreateCellHandle(cellElem, row, col, rowHandle, t.DocHandle);
    }

    private static nint GetCellChild(RowElem r, nint rowHandle, int index)
    {
        var cells = r.Row.Elements<TableCell>().ToList();
        if (index < 0) index = cells.Count + index;
        if (index < 0 || index >= cells.Count) return 0;
        return GetOrCreateCellHandle(cells[index], r.RowIdx, index, rowHandle, r.DocHandle);
    }

    private static nint GetCellParaChild(CellElem c, nint docHandle, int index)
    {
        var paras = c.Cell.Elements<Paragraph>().ToList();
        if (index < 0) index = paras.Count + index;
        if (index < 0 || index >= paras.Count) return 0;
        return GetOrCreateParagraphHandle(paras[index], docHandle);
    }

    // -----------------------------------------------------------------------
    // AppendChild — create and append a new child element
    // -----------------------------------------------------------------------

    internal static nint AppendChild(nint handle, byte* childType, int childTypeLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return 0;
        var ct = ReadStr(childType, childTypeLen);
        try
        {
            return (elem, ct) switch
            {
                (DocElem d, "paragraph") => AppendParagraphToDoc(d, handle),
                (ParaElem p, "run") => AppendRunToParagraph(p),
                (CellElem c, "paragraph") => AppendParagraphToCell(c),
                _ => 0
            };
        }
        catch { return 0; }
    }

    private static nint AppendParagraphToDoc(DocElem d, nint docHandle)
    {
        var para = new Paragraph();
        GetBody(d).AppendChild(para);
        return GetOrCreateParagraphHandle(para, docHandle);
    }

    private static nint AppendRunToParagraph(ParaElem p)
    {
        var run = new Run();
        p.Para.AppendChild(run);
        return GetOrCreateRunHandle(run, p.DocHandle);
    }

    private static nint AppendParagraphToCell(CellElem c)
    {
        var para = new Paragraph();
        c.Cell.AppendChild(para);
        return GetOrCreateParagraphHandle(para, c.DocHandle);
    }

    // -----------------------------------------------------------------------
    // RemoveChild — remove an element and clean up registrations
    // -----------------------------------------------------------------------

    internal static int RemoveChild(nint handle)
    {
        if (!SElements.TryRemove(handle, out var elem)) return -1;
        try
        {
            switch (elem)
            {
                case ParaElem p:
                    SParagraphHandles.TryRemove(p.Para, out _);
                    RemoveRunRegistrations(p.Para);
                    p.Para.Remove();
                    return 0;

                case RunElem r:
                    SRunHandles.TryRemove(r.Run, out _);
                    r.Run.Remove();
                    return 0;

                case TableElem t:
                    STableHandles.TryRemove(t.Table, out _);
                    RemoveTableRegistrations(t.Table);
                    t.Table.Remove();
                    return 0;

                case RowElem r:
                    SRowHandles.TryRemove(r.Row, out _);
                    RemoveCellRegistrations(r.Row);
                    r.Row.Remove();
                    return 0;

                case CellElem c:
                    SCellHandles.TryRemove(c.Cell, out _);
                    return 0;

                default:
                    return -1;
            }
        }
        catch { return -1; }
    }

    private static void RemoveRunRegistrations(Paragraph para)
    {
        foreach (var run in para.Elements<Run>())
        {
            if (SRunHandles.TryRemove(run, out var rh))
                SElements.TryRemove(rh, out _);
        }
    }

    private static void RemoveTableRegistrations(Table table)
    {
        foreach (var row in table.Elements<TableRow>())
        {
            RemoveCellRegistrations(row);
            if (SRowHandles.TryRemove(row, out var rh))
                SElements.TryRemove(rh, out _);
        }
    }

    private static void RemoveCellRegistrations(TableRow row)
    {
        foreach (var cell in row.Elements<TableCell>())
        {
            if (SCellHandles.TryRemove(cell, out var ch))
                SElements.TryRemove(ch, out _);
        }
    }

    // -----------------------------------------------------------------------
    // GetElementType — write the type name string to a caller-supplied buffer
    // -----------------------------------------------------------------------

    internal static int GetElementType(nint handle, byte* buf, int bufLen, int* required)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        return WriteStr(elem.TypeName, buf, bufLen, required);
    }

    // -----------------------------------------------------------------------
    // AddTable — table creation requires rows/cols at construction time
    // -----------------------------------------------------------------------

    internal static nint AddTable(nint docHandle, int rows, int cols)
    {
        if (!SElements.TryGetValue(docHandle, out var elem) || elem is not DocElem d)
            return 0;
        try
        {
            var table = BuildTable(rows, cols, out var cells);
            GetBody(d).AppendChild(table);
            var tableHandle = GetOrCreateTableHandle(table, cells, rows, cols, docHandle);

            // Pre-register all rows and cells so they get stable handles.
            var rowList = table.Elements<TableRow>().ToList();
            for (var r = 0; r < rowList.Count; r++)
            {
                var rowHandle = GetOrCreateRowHandle(rowList[r], r, tableHandle, docHandle);
                var cellList = rowList[r].Elements<TableCell>().ToList();
                for (var c = 0; c < cellList.Count; c++)
                    GetOrCreateCellHandle(cellList[c], r, c, rowHandle, docHandle);
            }

            return tableHandle;
        }
        catch { return 0; }
    }

    private static int GetTableRows(Table table) => table.Elements<TableRow>().Count();
    private static int GetTableCols(Table table) =>
        table.Elements<TableRow>().FirstOrDefault()?.Elements<TableCell>().Count() ?? 0;

    private static TableCell[,] GetTableCells(Table table)
    {
        var rowList = table.Elements<TableRow>().ToList();
        var rows = rowList.Count;
        var cols = rows > 0 ? rowList[0].Elements<TableCell>().Count() : 0;
        var cells = new TableCell[rows, cols];
        for (var r = 0; r < rows; r++)
        {
            var cellList = rowList[r].Elements<TableCell>().ToList();
            for (var c = 0; c < Math.Min(cols, cellList.Count); c++)
                cells[r, c] = cellList[c];
        }
        return cells;
    }
}
