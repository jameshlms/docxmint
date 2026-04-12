using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Wordprocessing;
using FastDocx.Native.Marshalling;

namespace FastDocx.Native;

internal static unsafe partial class DocumentBuilder
{
    internal static nint AddTable(nint handle, int rows, int cols)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return 0;

        try
        {
            var table = new Table();

            table.AppendChild(new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.Single, Size = 4 },
                    new BottomBorder { Val = BorderValues.Single, Size = 4 },
                    new LeftBorder { Val = BorderValues.Single, Size = 4 },
                    new RightBorder { Val = BorderValues.Single, Size = 4 },
                    new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4 },
                    new InsideVerticalBorder { Val = BorderValues.Single, Size = 4 })));

            var grid = new TableGrid();
            for (var c = 0; c < cols; c++)
                grid.AppendChild(new GridColumn());
            table.AppendChild(grid);

            var cells = new TableCell[rows, cols];
            for (var r = 0; r < rows; r++)
            {
                var row = new TableRow();
                for (var c = 0; c < cols; c++)
                {
                    var cell = new TableCell(
                        new Paragraph(new Run(new Text(string.Empty))));
                    cells[r, c] = cell;
                    row.AppendChild(cell);
                }
                table.AppendChild(row);
            }

            var body = state.Document.MainDocumentPart!.Document!.Body!;
            body.AppendChild(table);

            var tableHandle = NextHandle();
            STables[tableHandle] = new TableState(table, cells, rows, cols);
            return tableHandle;
        }
        catch
        {
            return 0;
        }
    }

    internal static nint AddTableWithData(nint handle, ByteSlice* cells, int rows, int cols)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return 0;

        try
        {
            var table = new Table();

            table.AppendChild(new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.Single, Size = 4 },
                    new BottomBorder { Val = BorderValues.Single, Size = 4 },
                    new LeftBorder { Val = BorderValues.Single, Size = 4 },
                    new RightBorder { Val = BorderValues.Single, Size = 4 },
                    new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4 },
                    new InsideVerticalBorder { Val = BorderValues.Single, Size = 4 })));

            var grid = new TableGrid();
            for (var c = 0; c < cols; c++)
                grid.AppendChild(new GridColumn());
            table.AppendChild(grid);

            var tableCells = new TableCell[rows, cols];
            for (var r = 0; r < rows; r++)
            {
                var row = new TableRow();
                for (var c = 0; c < cols; c++)
                {
                    var slice = cells[r * cols + c];
                    var text = slice.Len > 0
                        ? Encoding.UTF8.GetString(slice.Data, slice.Len)
                        : string.Empty;

                    var textElem = new Text(text) { Space = SpaceProcessingModeValues.Preserve };
                    var cell = new TableCell(new Paragraph(new Run(textElem)));
                    tableCells[r, c] = cell;
                    row.AppendChild(cell);
                }
                table.AppendChild(row);
            }

            var body = state.Document.MainDocumentPart!.Document!.Body!;
            body.AppendChild(table);

            var tableHandle = NextHandle();
            STables[tableHandle] = new TableState(table, tableCells, rows, cols);
            return tableHandle;
        }
        catch
        {
            return 0;
        }
    }

    internal static int SetCellText(
        nint tableHandle,
        int row, int col,
        byte* text, int textLen)
    {
        if (!STables.TryGetValue(tableHandle, out var state))
            return -1;

        if (row < 0 || row >= state.Rows || col < 0 || col >= state.Cols)
            return -1;

        try
        {
            var textStr = Encoding.UTF8.GetString(text, textLen);
            var cell = state.Cells[row, col];

            var para = cell.GetFirstChild<Paragraph>();
            if (para is null)
            {
                para = new Paragraph();
                cell.AppendChild(para);
            }

            var run = para.GetFirstChild<Run>();
            if (run is null)
            {
                run = new Run();
                para.AppendChild(run);
            }

            var textElem = run.GetFirstChild<Text>();
            if (textElem is null)
            {
                textElem = new Text();
                run.AppendChild(textElem);
            }

            textElem.Text = textStr;
            textElem.Space = SpaceProcessingModeValues.Preserve;
            return 0;
        }
        catch
        {
            return -1;
        }
    }
}
