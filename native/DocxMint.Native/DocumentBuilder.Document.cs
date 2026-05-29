using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace DocxMint.Native;

internal static unsafe partial class DocumentBuilder
{
    internal static nint CreateDocument()
    {
        try
        {
            var stream = new MemoryStream();
            var wp = WordprocessingDocument.Create(stream, WordprocessingDocumentType.Document);
            var mainPart = wp.AddMainDocumentPart();
            mainPart.Document = new Document(new Body());
            AddDefaultStyles(mainPart);

            var h = NextHandle();
            SElements[h] = new DocElem(new DocumentState(wp, stream));
            return h;
        }
        catch
        {
            return 0;
        }
    }

    internal static nint OpenDocument(byte* path, int pathLen)
    {
        try
        {
            var pathStr = ReadStr(path, pathLen);
            var bytes = File.ReadAllBytes(pathStr);
            var stream = new MemoryStream(capacity: bytes.Length + 4096);
            stream.Write(bytes, 0, bytes.Length);
            stream.Position = 0;

            var wp = WordprocessingDocument.Open(stream, isEditable: true);

            var h = NextHandle();
            SElements[h] = new DocElem(new DocumentState(wp, stream));
            return h;
        }
        catch
        {
            return 0;
        }
    }

    // edit_document behaves identically to open_document for handle registration;
    // the Python layer remembers the edit path and saves-on-exit.
    internal static nint EditDocument(byte* path, int pathLen) =>
        OpenDocument(path, pathLen);

    internal static int SaveDocument(nint handle, byte* path, int pathLen)
    {
        if (!SElements.TryGetValue(handle, out var elem) || elem is not DocElem d)
            return -1;

        try
        {
            var pathStr = ReadStr(path, pathLen);
            var body = d.State.Document.MainDocumentPart!.Document!.Body!;
            EnsureTrailingParagraph(body);
            d.State.Document.Save();
            var bytes = d.State.Stream.ToArray();
            File.WriteAllBytes(pathStr, bytes);
            return 0;
        }
        catch
        {
            return -1;
        }
    }

    private static void EnsureTrailingParagraph(Body body)
    {
        var last = body.LastChild;
        bool needsTrailing = last is not Paragraph p
            || p.ParagraphProperties?.ParagraphBorders?.GetFirstChild<BottomBorder>() is not null;
        if (needsTrailing)
            body.AppendChild(new Paragraph());
    }

    internal static void Dispose(nint handle)
    {
        if (!SElements.TryRemove(handle, out var elem) || elem is not DocElem d)
            return;

        // Remove every child element registered under this document handle.
        foreach (var kvp in SElements.ToArray())
        {
            if (kvp.Value.DocHandle == handle)
            {
                if (SElements.TryRemove(kvp.Key, out var child))
                    RemoveReverseMapEntry(child);
            }
        }

        try { d.State.Document.Dispose(); } catch { /* best effort */ }
        try { d.State.Stream.Dispose(); } catch { /* best effort */ }
    }

    private static void RemoveReverseMapEntry(ElemWrapper elem)
    {
        switch (elem)
        {
            case ParaElem p:  SParagraphHandles.TryRemove(p.Para, out _);  break;
            case RunElem r:   SRunHandles.TryRemove(r.Run, out _);         break;
            case TableElem t: STableHandles.TryRemove(t.Table, out _);     break;
            case RowElem row: SRowHandles.TryRemove(row.Row, out _);       break;
            case CellElem c:  SCellHandles.TryRemove(c.Cell, out _);       break;
            case StyleElem s: SStyleHandles.TryRemove(s.Style, out _);     break;
        }
    }
}
