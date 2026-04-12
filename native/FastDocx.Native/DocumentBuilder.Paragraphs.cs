using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Wordprocessing;

namespace FastDocx.Native;

internal static unsafe partial class DocumentBuilder
{
    internal static nint AddParagraph(nint handle, byte* style, int styleLen)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return 0;

        try
        {
            var styleStr = styleLen > 0 ? Encoding.UTF8.GetString(style, styleLen) : null;
            var para = new Paragraph();

            if (styleStr is not null)
            {
                para.ParagraphProperties = new ParagraphProperties(
                    new ParagraphStyleId { Val = styleStr });
            }

            state.Document.MainDocumentPart!.Document!.Body!.AppendChild(para);

            var paraHandle = NextHandle();
            SParagraphs[paraHandle] = para;
            return paraHandle;
        }
        catch
        {
            return 0;
        }
    }

    internal static nint AddRun(nint paraHandle, byte* text, int textLen, int bold, int italic, int fontSize)
    {
        if (!SParagraphs.TryGetValue(paraHandle, out var para))
            return 0;

        try
        {
            var textStr = Encoding.UTF8.GetString(text, textLen);

            var runProps = new RunProperties
            {
                // -1 = inherit (omit element), 0 = explicit false, 1 = explicit true
                Bold     = bold   == 1 ? new Bold()   : bold   == 0 ? new Bold   { Val = false } : null,
                Italic   = italic == 1 ? new Italic() : italic == 0 ? new Italic { Val = false } : null,
                FontSize = fontSize > 0 ? new FontSize { Val = fontSize.ToString() } : null,
            };

            var run = new Run { RunProperties = runProps };
            run.AppendChild(new Text(textStr) { Space = SpaceProcessingModeValues.Preserve });
            para.AppendChild(run);

            var runHandle = NextHandle();
            SRuns[runHandle] = run;
            return runHandle;
        }
        catch
        {
            return 0;
        }
    }

    internal static int SetRunBold(nint runHandle, int bold)
    {
        if (!SRuns.TryGetValue(runHandle, out var run)) return -1;
        run.RunProperties ??= new RunProperties();
        run.RunProperties.Bold = bold == 1 ? new Bold() : bold == 0 ? new Bold { Val = false } : null;
        return 0;
    }

    internal static int SetRunItalic(nint runHandle, int italic)
    {
        if (!SRuns.TryGetValue(runHandle, out var run)) return -1;
        run.RunProperties ??= new RunProperties();
        run.RunProperties.Italic = italic == 1 ? new Italic() : italic == 0 ? new Italic { Val = false } : null;
        return 0;
    }

    internal static int SetRunUnderline(nint runHandle, int underline)
    {
        if (!SRuns.TryGetValue(runHandle, out var run)) return -1;
        run.RunProperties ??= new RunProperties();
        run.RunProperties.Underline = underline == 1
            ? new Underline { Val = UnderlineValues.Single }
            : underline == 0 ? new Underline { Val = UnderlineValues.None } : null;
        return 0;
    }

    internal static int SetRunFontSize(nint runHandle, int halfPoints)
    {
        if (!SRuns.TryGetValue(runHandle, out var run)) return -1;
        run.RunProperties ??= new RunProperties();
        run.RunProperties.FontSize = halfPoints > 0 ? new FontSize { Val = halfPoints.ToString() } : null;
        return 0;
    }

    internal static int SetRunFontName(nint runHandle, byte* name, int nameLen)
    {
        if (!SRuns.TryGetValue(runHandle, out var run)) return -1;
        run.RunProperties ??= new RunProperties();
        var nameStr = nameLen > 0 ? Encoding.UTF8.GetString(name, nameLen) : null;
        run.RunProperties.RunFonts = nameStr is not null
            ? new RunFonts { Ascii = nameStr, HighAnsi = nameStr }
            : null;
        return 0;
    }

    internal static nint AddHeading(nint handle, byte* text, int textLen, int level)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return 0;

        try
        {
            var textStr = Encoding.UTF8.GetString(text, textLen);
            var styleId = level switch
            {
                1 => "Heading1",
                2 => "Heading2",
                3 => "Heading3",
                4 => "Heading4",
                5 => "Heading5",
                6 => "Heading6",
                _ => "Heading1"
            };

            var para = new Paragraph(
                new ParagraphProperties(new ParagraphStyleId { Val = styleId }),
                new Run(new Text(textStr) { Space = SpaceProcessingModeValues.Preserve }));

            state.Document.MainDocumentPart!.Document!.Body!.AppendChild(para);

            var paraHandle = NextHandle();
            SParagraphs[paraHandle] = para;
            return paraHandle;
        }
        catch
        {
            return 0;
        }
    }

    internal static int GetParagraphCount(nint handle)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        try
        {
            var body = state.Document.MainDocumentPart!.Document!.Body!;
            return body.Elements<Paragraph>().Count();
        }
        catch
        {
            return -1;
        }
    }

    /// <summary>
    /// Writes the text of the paragraph at <paramref name="index"/> into
    /// <paramref name="buf"/>. Returns the number of bytes written, or -1 on
    /// error.  If the buffer is too small the required byte count is written to
    /// <paramref name="required"/> and 0 is returned so the caller can retry
    /// with a larger buffer.
    /// </summary>
    internal static int GetParagraphText(nint handle, int index, byte* buf, int bufLen, int* required)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        try
        {
            var para = state.Document.MainDocumentPart!.Document!.Body!
                .Elements<Paragraph>()
                .ElementAt(index);

            var text = string.Concat(para.Descendants<Text>().Select(t => t.Text));
            var bytes = Encoding.UTF8.GetBytes(text);

            *required = bytes.Length;
            if (bytes.Length > bufLen)
                return 0;

            bytes.AsSpan().CopyTo(new Span<byte>(buf, bytes.Length));
            return bytes.Length;
        }
        catch
        {
            return -1;
        }
    }

    /// <summary>
    /// Writes the style ID of the paragraph at <paramref name="index"/> into
    /// <paramref name="buf"/>. Returns the number of bytes written, or -1 on
    /// error. Returns 0 with *required == 0 when the paragraph has no explicit
    /// style.
    /// </summary>
    internal static int GetParagraphStyle(nint handle, int index, byte* buf, int bufLen, int* required)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        try
        {
            var para = state.Document.MainDocumentPart!.Document!.Body!
                .Elements<Paragraph>()
                .ElementAt(index);

            var styleId = para.ParagraphProperties?.ParagraphStyleId?.Val?.Value ?? string.Empty;
            var bytes = Encoding.UTF8.GetBytes(styleId);

            *required = bytes.Length;
            if (bytes.Length == 0)
                return 0;
            if (bytes.Length > bufLen)
                return 0;

            bytes.AsSpan().CopyTo(new Span<byte>(buf, bytes.Length));
            return bytes.Length;
        }
        catch
        {
            return -1;
        }
    }

    internal static int RemoveParagraph(nint handle, int index)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        try
        {
            var para = state.Document.MainDocumentPart!.Document!.Body!
                .Elements<Paragraph>()
                .ElementAt(index);

            para.Remove();
            return 0;
        }
        catch (ArgumentOutOfRangeException)
        {
            return -2;
        }
        catch
        {
            return -1;
        }
    }

    internal static nint AddHorizontalLine(nint handle)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return 0;

        try
        {
            var para = new Paragraph(
                new ParagraphProperties(
                    new ParagraphBorders(
                        new BottomBorder
                        {
                            Val = BorderValues.Single,
                            Size = 4,
                            Space = 1,
                            Color = "auto"
                        })));

            state.Document.MainDocumentPart!.Document!.Body!.AppendChild(para);

            var paraHandle = NextHandle();
            SParagraphs[paraHandle] = para;
            return paraHandle;
        }
        catch
        {
            return 0;
        }
    }
}
