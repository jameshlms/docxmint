using System.Text;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using FastDocx.Native.Marshalling;

namespace FastDocx.Native;

internal static unsafe partial class DocumentBuilder
{
    internal static int RegisterParagraphStyle(nint handle, ParagraphStyleDef* def)
    {
        if (!SDocuments.TryGetValue(handle, out var state))
            return -1;

        if (def->StyleIdLen <= 0)
            return -1;

        try
        {
            var styleId = Encoding.UTF8.GetString(def->StyleId, def->StyleIdLen);
            var mainPart = state.Document.MainDocumentPart!;
            var stylesPart = mainPart.StyleDefinitionsPart
                ?? mainPart.AddNewPart<StyleDefinitionsPart>();
            stylesPart.Styles ??= new Styles();

            // Remove existing style with the same ID so re-registration is safe.
            var existing = stylesPart.Styles
                .Elements<Style>()
                .FirstOrDefault(s => s.StyleId?.Value == styleId);
            existing?.Remove();

            var style = new Style { Type = StyleValues.Paragraph, StyleId = styleId };
            style.AppendChild(new StyleName { Val = styleId });

            if (def->BasedOnLen > 0)
                style.AppendChild(new BasedOn { Val = Encoding.UTF8.GetString(def->BasedOn, def->BasedOnLen) });

            // --- paragraph properties ---
            var pPr = new StyleParagraphProperties();
            var hasParaProps = false;

            if (def->Alignment > 0)
            {
                var jc = def->Alignment switch
                {
                    1 => JustificationValues.Left,
                    2 => JustificationValues.Center,
                    3 => JustificationValues.Right,
                    4 => JustificationValues.Both,
                    _ => (JustificationValues?)null
                };
                if (jc is not null)
                {
                    pPr.AppendChild(new Justification { Val = jc.Value });
                    hasParaProps = true;
                }
            }

            if (def->SpaceBefore > 0 || def->SpaceAfter > 0)
            {
                var spacing = new SpacingBetweenLines();
                if (def->SpaceBefore > 0) spacing.Before = def->SpaceBefore.ToString();
                if (def->SpaceAfter > 0)  spacing.After  = def->SpaceAfter.ToString();
                pPr.AppendChild(spacing);
                hasParaProps = true;
            }

            if (hasParaProps)
                style.AppendChild(pPr);

            // --- run properties ---
            var rPr = new StyleRunProperties();
            var hasRunProps = false;

            if (def->Bold == 1)    { rPr.AppendChild(new Bold());   hasRunProps = true; }
            if (def->Italic == 1)  { rPr.AppendChild(new Italic()); hasRunProps = true; }
            if (def->FontSize > 0) { rPr.AppendChild(new FontSize { Val = def->FontSize.ToString() }); hasRunProps = true; }
            if (def->ColorLen > 0)
            {
                var colorStr = Encoding.UTF8.GetString(def->Color, def->ColorLen);
                rPr.AppendChild(new Color { Val = colorStr });
                hasRunProps = true;
            }

            if (hasRunProps)
                style.AppendChild(rPr);

            stylesPart.Styles.AppendChild(style);
            return 0;
        }
        catch
        {
            return -1;
        }
    }

    private static void AddHeadingStyles(MainDocumentPart mainPart)
    {
        var stylesPart = mainPart.AddNewPart<StyleDefinitionsPart>();
        var styles = new Styles();

        // Default (Normal) style — required as a base
        styles.AppendChild(new Style(
            new StyleName { Val = "Normal" },
            new PrimaryStyle())
        {
            Type = StyleValues.Paragraph,
            StyleId = "Normal",
            Default = true
        });

        // Heading styles 1–6
        string[] headingNames = ["heading 1", "heading 2", "heading 3", "heading 4", "heading 5", "heading 6"];
        int[] fontSizesHalfPt  = [32, 26, 24, 22, 20, 18];

        for (var i = 0; i < headingNames.Length; i++)
        {
            var level = i + 1;
            var style = new Style(
                new StyleName { Val = headingNames[i] },
                new BasedOn { Val = "Normal" },
                new NextParagraphStyle { Val = "Normal" },
                new PrimaryStyle(),
                new StyleRunProperties(
                    new Bold(),
                    new FontSize { Val = fontSizesHalfPt[i].ToString() }))
            {
                Type = StyleValues.Paragraph,
                StyleId = $"Heading{level}"
            };

            styles.AppendChild(style);
        }

        stylesPart.Styles = styles;
    }
}
