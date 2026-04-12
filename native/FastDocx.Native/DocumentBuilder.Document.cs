using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace FastDocx.Native;

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

            AddHeadingStyles(mainPart);

            var handle = NextHandle();
            SDocuments[handle] = new DocumentState(wp, stream);
            return handle;
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
            var pathStr = System.Text.Encoding.UTF8.GetString(path, pathLen);
            var bytes = File.ReadAllBytes(pathStr);
            var stream = new MemoryStream(capacity: bytes.Length + 4096);
            stream.Write(bytes, 0, bytes.Length);
            stream.Position = 0;

            var wp = WordprocessingDocument.Open(stream, isEditable: true);

            var handle = NextHandle();
            SDocuments[handle] = new DocumentState(wp, stream);
            return handle;
        }
        catch
        {
            return 0;
        }
    }

    internal static int SaveDocument(nint handle, byte* path, int pathLen)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        try
        {
            var pathStr = System.Text.Encoding.UTF8.GetString(path, pathLen);
            state.Document.Save();
            var bytes = state.Stream.ToArray();
            File.WriteAllBytes(pathStr, bytes);
            return 0;
        }
        catch
        {
            return -1;
        }
    }

    internal static int SetDocumentMargins(nint handle, int top, int right, int bottom, int left)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        try
        {
            var body = state.Document.MainDocumentPart!.Document!.Body!;
            var props = body.GetFirstChild<SectionProperties>() ?? new SectionProperties();
            var margin = props.GetFirstChild<PageMargin>() ?? new PageMargin();

            margin.Top = top;
            margin.Right = (uint)right;
            margin.Bottom = bottom;
            margin.Left = (uint)left;

            if (margin.Parent is null)
                props.AppendChild(margin);

            if (props.Parent is null)
                body.AppendChild(props);

            return 0;
        }
        catch
        {
            return -1;
        }
    }

    internal static void FreeDocument(nint handle)
    {
        if (!SDocuments.TryRemove(handle, out var state)) return;
        state.Document.Dispose();
        state.Stream.Dispose();
    }
}
