using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace FastDocx.Native;

internal static partial class DocumentBuilder
{
    // ---------------------------------------------------------------------------
    // Default styles — all use explicit fonts/colors; no theme attributes.
    // ---------------------------------------------------------------------------

    private static readonly string[] HeadingStyleNames =
        ["heading 1", "heading 2", "heading 3", "heading 4", "heading 5", "heading 6"];

    private static readonly int[] HeadingFontSizesHalfPt = [32, 26, 24, 22, 20, 18];

    private static void AddDefaultStyles(MainDocumentPart mainPart)
    {
        var stylesPart = mainPart.AddNewPart<StyleDefinitionsPart>();
        var styles = new Styles();

        // Normal — document default; explicit Calibri 11pt.
        styles.AppendChild(new Style(
            new StyleName { Val = "Normal" },
            new PrimaryStyle(),
            new StyleRunProperties(
                new RunFonts { Ascii = "Calibri", HighAnsi = "Calibri" },
                new FontSize { Val = "22" }))
        {
            Type = StyleValues.Paragraph,
            StyleId = "Normal",
            Default = true
        });

        // Title — Calibri Light 28pt.
        styles.AppendChild(new Style(
            new StyleName { Val = "Title" },
            new BasedOn { Val = "Normal" },
            new PrimaryStyle(),
            new StyleRunProperties(
                new RunFonts { Ascii = "Calibri Light", HighAnsi = "Calibri Light" },
                new FontSize { Val = "56" }))
        {
            Type = StyleValues.Paragraph,
            StyleId = "Title"
        });

        // Subtitle — Calibri 12pt italic, muted grey.
        styles.AppendChild(new Style(
            new StyleName { Val = "Subtitle" },
            new BasedOn { Val = "Normal" },
            new PrimaryStyle(),
            new StyleRunProperties(
                new RunFonts { Ascii = "Calibri", HighAnsi = "Calibri" },
                new Italic(),
                new FontSize { Val = "24" },
                new Color { Val = "595959" }))
        {
            Type = StyleValues.Paragraph,
            StyleId = "Subtitle"
        });

        // Headings 1–6 — Calibri Light bold.
        for (var i = 0; i < HeadingStyleNames.Length; i++)
        {
            var level = i + 1;
            styles.AppendChild(new Style(
                new StyleName { Val = HeadingStyleNames[i] },
                new BasedOn { Val = "Normal" },
                new NextParagraphStyle { Val = "Normal" },
                new PrimaryStyle(),
                new StyleRunProperties(
                    new RunFonts { Ascii = "Calibri Light", HighAnsi = "Calibri Light" },
                    new Bold(),
                    new FontSize { Val = HeadingFontSizesHalfPt[i].ToString() }))
            {
                Type = StyleValues.Paragraph,
                StyleId = $"Heading{level}"
            });
        }

        // TableGrid — simple grid table style.
        styles.AppendChild(new Style(
            new StyleName { Val = "Table Grid" },
            new PrimaryStyle())
        {
            Type = StyleValues.Table,
            StyleId = "TableGrid"
        });

        stylesPart.Styles = styles;
    }

}
