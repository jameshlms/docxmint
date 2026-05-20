using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Wordprocessing;

namespace FastDocx.Native;

internal static unsafe partial class DocumentBuilder
{
    // -----------------------------------------------------------------------
    // GetInt — read an integer property from any element type
    // -----------------------------------------------------------------------

    internal static int GetInt(nint handle, byte* name, int nameLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -2;
        var n = ReadStr(name, nameLen);
        try
        {
            if (elem is ParaElem p)  return GetParaInt(p.Para, n);
            if (elem is RunElem r)   return GetRunInt(r.Run, n);
            return -2;
        }
        catch { return -2; }
    }

    private static int GetParaInt(Paragraph para, string name)
    {
        var pp = para.ParagraphProperties;
        if (name == "keep_together")     return GetOoxmlBool(pp?.KeepLines);
        if (name == "keep_with_next")    return GetOoxmlBool(pp?.KeepNext);
        if (name == "page_break_before") return GetOoxmlBool(pp?.PageBreakBefore);
        return -2;
    }

    private static int GetRunInt(Run run, string name)
    {
        var rp = run.RunProperties;
        if (name == "bold")          return GetOoxmlBool(rp?.Bold);
        if (name == "italic")        return GetOoxmlBool(rp?.Italic);
        if (name == "strikethrough") return GetOoxmlBool(rp?.Strike);
        if (name == "all_caps")      return GetOoxmlBool(rp?.Caps);
        if (name == "small_caps")    return GetOoxmlBool(rp?.SmallCaps);
        if (name == "hidden")        return GetOoxmlBool(rp?.Vanish);
        if (name == "emboss")        return GetOoxmlBool(rp?.Emboss);
        if (name == "imprint")       return GetOoxmlBool(rp?.Imprint);
        if (name == "outline")       return GetOoxmlBool(rp?.Outline);
        if (name == "shadow")        return GetOoxmlBool(rp?.Shadow);
        if (name == "no_spell_check") return GetOoxmlBool(rp?.NoProof);
        if (name == "superscript")
        {
            var vta = rp?.VerticalTextAlignment?.Val;
            if (vta is null) return -1;
            return vta.Value == VerticalPositionValues.Superscript ? 1 : 0;
        }
        if (name == "subscript")
        {
            var vta = rp?.VerticalTextAlignment?.Val;
            if (vta is null) return -1;
            return vta.Value == VerticalPositionValues.Subscript ? 1 : 0;
        }
        return -2;
    }

    // -----------------------------------------------------------------------
    // SetInt — write an integer property
    // -----------------------------------------------------------------------

    internal static int SetInt(nint handle, byte* name, int nameLen, int value)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        try
        {
            if (elem is ParaElem p) return SetParaInt(p.Para, n, value);
            if (elem is RunElem r)  return SetRunInt(r.Run, n, value);
            return -1;
        }
        catch { return -1; }
    }

    private static int SetParaInt(Paragraph para, string name, int value)
    {
        para.ParagraphProperties ??= new ParagraphProperties();
        var pp = para.ParagraphProperties;
        if (name == "keep_together")     { pp.KeepLines      = value == 1 ? new KeepLines()      : null; return 0; }
        if (name == "keep_with_next")    { pp.KeepNext       = value == 1 ? new KeepNext()       : null; return 0; }
        if (name == "page_break_before") { pp.PageBreakBefore = value == 1 ? new PageBreakBefore() : null; return 0; }
        return -1;
    }

    private static int SetRunInt(Run run, string name, int value)
    {
        run.RunProperties ??= new RunProperties();
        var rp = run.RunProperties;
        if (name == "bold")
        { rp.Bold = value switch { 1 => new Bold(), 0 => new Bold { Val = false }, _ => null }; return 0; }
        if (name == "italic")
        { rp.Italic = value switch { 1 => new Italic(), 0 => new Italic { Val = false }, _ => null }; return 0; }
        if (name == "strikethrough")
        { rp.Strike = value switch { 1 => new Strike(), 0 => new Strike { Val = false }, _ => null }; return 0; }
        if (name == "all_caps")
        { rp.Caps = value switch { 1 => new Caps(), 0 => new Caps { Val = false }, _ => null }; return 0; }
        if (name == "small_caps")
        { rp.SmallCaps = value switch { 1 => new SmallCaps(), 0 => new SmallCaps { Val = false }, _ => null }; return 0; }
        if (name == "hidden")
        { rp.Vanish = value switch { 1 => new Vanish(), 0 => new Vanish { Val = false }, _ => null }; return 0; }
        if (name == "emboss")
        { rp.Emboss = value switch { 1 => new Emboss(), 0 => new Emboss { Val = false }, _ => null }; return 0; }
        if (name == "imprint")
        { rp.Imprint = value switch { 1 => new Imprint(), 0 => new Imprint { Val = false }, _ => null }; return 0; }
        if (name == "outline")
        { rp.Outline = value switch { 1 => new Outline(), 0 => new Outline { Val = false }, _ => null }; return 0; }
        if (name == "shadow")
        { rp.Shadow = value switch { 1 => new Shadow(), 0 => new Shadow { Val = false }, _ => null }; return 0; }
        if (name == "no_spell_check")
        { rp.NoProof = value switch { 1 => new NoProof(), 0 => new NoProof { Val = false }, _ => null }; return 0; }
        if (name == "superscript")
        {
            rp.VerticalTextAlignment = value == 1
                ? new VerticalTextAlignment { Val = VerticalPositionValues.Superscript }
                : null;
            return 0;
        }
        if (name == "subscript")
        {
            rp.VerticalTextAlignment = value == 1
                ? new VerticalTextAlignment { Val = VerticalPositionValues.Subscript }
                : null;
            return 0;
        }
        return -1;
    }

    // -----------------------------------------------------------------------
    // GetFloat — read a float property
    // -----------------------------------------------------------------------

    internal static double GetFloat(nint handle, byte* name, int nameLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return double.NaN;
        var n = ReadStr(name, nameLen);
        try
        {
            if (elem is RunElem r) return GetRunFloat(r.Run, n);
            return double.NaN;
        }
        catch { return double.NaN; }
    }

    private static double GetRunFloat(Run run, string name)
    {
        var rp = run.RunProperties;
        if (name == "font_size")
        {
            var sizeStr = rp?.FontSize?.Val?.Value;
            if (sizeStr is null) return 0.0;
            return double.TryParse(sizeStr, out var v) ? v / 2.0 : 0.0;
        }
        return double.NaN;
    }

    // -----------------------------------------------------------------------
    // SetFloat — write a float property
    // -----------------------------------------------------------------------

    internal static int SetFloat(nint handle, byte* name, int nameLen, double value)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        try
        {
            if (elem is RunElem r) return SetRunFloat(r.Run, n, value);
            return -1;
        }
        catch { return -1; }
    }

    private static int SetRunFloat(Run run, string name, double value)
    {
        run.RunProperties ??= new RunProperties();
        var rp = run.RunProperties;
        if (name == "font_size")
        {
            var halfPt = (int)Math.Round(value * 2);
            rp.FontSize = halfPt > 0 ? new FontSize { Val = halfPt.ToString() } : null;
            return 0;
        }
        return -1;
    }

    // -----------------------------------------------------------------------
    // GetStr — read a string property into a caller-supplied buffer
    // -----------------------------------------------------------------------

    internal static int GetStr(
        nint handle, byte* name, int nameLen, byte* buf, int bufLen, int* required)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        try
        {
            string? val;
            if (elem is ParaElem p)  val = GetParaStr(p.Para, n);
            else if (elem is RunElem r)   val = GetRunStr(r.Run, n);
            else if (elem is TableElem t) val = GetTableStr(t.Table, n);
            else if (elem is RowElem row) val = GetRowStr(row.Row, n);
            else if (elem is CellElem c)  val = GetCellStr(c.Cell, n);
            else if (elem is DocElem d)   val = GetDocStr(d, n);
            else val = null;

            if (val is null) return -1;
            return WriteStr(val, buf, bufLen, required);
        }
        catch { return -1; }
    }

    private static string? GetParaStr(Paragraph para, string name)
    {
        if (name == "text") return string.Concat(para.Descendants<Text>().Select(t => t.Text));

        var pp = para.ParagraphProperties;
        if (name == "style") return pp?.ParagraphStyleId?.Val?.Value ?? "";

        if (name == "alignment")
        {
            var jcVal = pp?.Justification?.Val;
            if (jcVal is null) return "";
            if (jcVal.Value == JustificationValues.Left)   return "left";
            if (jcVal.Value == JustificationValues.Center) return "center";
            if (jcVal.Value == JustificationValues.Right)  return "right";
            if (jcVal.Value == JustificationValues.Both)   return "justify";
            return "";
        }
        return null;
    }

    private static string? GetRunStr(Run run, string name)
    {
        var rp = run.RunProperties;
        if (name == "text") return string.Concat(run.Descendants<Text>().Select(t => t.Text));
        if (name == "font_name") return rp?.RunFonts?.Ascii ?? "";
        if (name == "font_name_eastasia") return rp?.RunFonts?.EastAsia ?? "";
        if (name == "font_name_complex") return rp?.RunFonts?.ComplexScript ?? "";
        if (name == "color") return rp?.Color?.Val?.Value ?? "";
        if (name == "language") return rp?.Languages?.Val?.Value ?? "";

        if (name == "underline")
        {
            var ulVal = rp?.Underline?.Val;
            if (ulVal is null) return "";
            if (ulVal.Value == UnderlineValues.Single) return "single";
            if (ulVal.Value == UnderlineValues.Double) return "double";
            if (ulVal.Value == UnderlineValues.Dotted) return "dotted";
            if (ulVal.Value == UnderlineValues.Dash)   return "dashed";
            if (ulVal.Value == UnderlineValues.Wave)   return "wave";
            return "";
        }
        return null;
    }

    private static string? GetTableStr(Table table, string name)
    {
        var tp = table.GetFirstChild<TableProperties>();
        if (name == "style") return tp?.TableStyle?.Val?.Value ?? "";

        if (name == "alignment")
        {
            var tjVal = tp?.TableJustification?.Val;
            if (tjVal is null) return "";
            if (tjVal.Value == TableRowAlignmentValues.Left)   return "left";
            if (tjVal.Value == TableRowAlignmentValues.Center) return "center";
            if (tjVal.Value == TableRowAlignmentValues.Right)  return "right";
            return "";
        }
        return null;
    }

    private static string? GetRowStr(TableRow row, string name)
    {
        if (name == "height_rule") return "auto";  // simplified for v1
        return null;
    }

    private static string? GetCellStr(TableCell cell, string name)
    {
        if (name == "text") return string.Concat(cell.Descendants<Text>().Select(t => t.Text));

        if (name == "vertical_alignment")
        {
            var vaVal = cell.TableCellProperties?.TableCellVerticalAlignment?.Val;
            if (vaVal is null) return "top";
            if (vaVal.Value == TableVerticalAlignmentValues.Top)    return "top";
            if (vaVal.Value == TableVerticalAlignmentValues.Center) return "center";
            if (vaVal.Value == TableVerticalAlignmentValues.Bottom) return "bottom";
            return "top";
        }
        return null;
    }

    private static string? GetDocStr(DocElem d, string name)
    {
        var cp = d.State.Document.PackageProperties;
        if (name == "author")      return cp.Creator     ?? "";
        if (name == "title")       return cp.Title       ?? "";
        if (name == "subject")     return cp.Subject     ?? "";
        if (name == "description") return cp.Description ?? "";
        return null;
    }

    // -----------------------------------------------------------------------
    // SetStr — write a string property
    // -----------------------------------------------------------------------

    internal static int SetStr(
        nint handle, byte* name, int nameLen, byte* value, int valueLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        var v = ReadStr(value, valueLen);
        try
        {
            if (elem is ParaElem p)  return SetParaStr(p.Para, n, v);
            if (elem is RunElem r)   return SetRunStr(r.Run, n, v);
            if (elem is TableElem t) return SetTableStr(t.Table, n, v);
            if (elem is RowElem row) return SetRowStr(row.Row, n, v);
            if (elem is CellElem c)  return SetCellStr(c.Cell, n, v);
            if (elem is DocElem d)   return SetDocStr(d, n, v);
            return -1;
        }
        catch { return -1; }
    }

    private static int SetParaStr(Paragraph para, string name, string value)
    {
        if (name == "text")
        {
            foreach (var r in para.Elements<Run>().ToList()) r.Remove();
            para.AppendChild(new Run(
                new Text(value) { Space = SpaceProcessingModeValues.Preserve }));
            return 0;
        }

        if (name == "style")
        {
            para.ParagraphProperties ??= new ParagraphProperties();
            para.ParagraphProperties.ParagraphStyleId = string.IsNullOrEmpty(value)
                ? null
                : new ParagraphStyleId { Val = value };
            return 0;
        }

        if (name == "alignment")
        {
            para.ParagraphProperties ??= new ParagraphProperties();
            if (string.IsNullOrEmpty(value))
            {
                para.ParagraphProperties.Justification = null;
            }
            else
            {
                JustificationValues? jv = value switch
                {
                    "left"    => JustificationValues.Left,
                    "center"  => JustificationValues.Center,
                    "right"   => JustificationValues.Right,
                    "justify" => JustificationValues.Both,
                    _         => null
                };
                para.ParagraphProperties.Justification = jv.HasValue
                    ? new Justification { Val = jv.Value }
                    : null;
            }
            return 0;
        }

        return -1;
    }

    private static int SetRunStr(Run run, string name, string value)
    {
        run.RunProperties ??= new RunProperties();
        var rp = run.RunProperties;

        if (name == "text")
        {
            foreach (var t in run.Elements<Text>().ToList()) t.Remove();
            run.AppendChild(new Text(value) { Space = SpaceProcessingModeValues.Preserve });
            return 0;
        }

        if (name == "font_name")
        {
            rp.RunFonts ??= new RunFonts();
            rp.RunFonts.Ascii = value;
            rp.RunFonts.HighAnsi = value;
            return 0;
        }

        if (name == "font_name_eastasia")
        {
            rp.RunFonts ??= new RunFonts();
            rp.RunFonts.EastAsia = value;
            return 0;
        }

        if (name == "font_name_complex")
        {
            rp.RunFonts ??= new RunFonts();
            rp.RunFonts.ComplexScript = value;
            return 0;
        }

        if (name == "color")
        {
            rp.Color = string.IsNullOrEmpty(value) ? null : new Color { Val = value };
            return 0;
        }

        if (name == "underline")
        {
            if (string.IsNullOrEmpty(value))
            {
                rp.Underline = null;
            }
            else
            {
                UnderlineValues? uv = value switch
                {
                    "single" => UnderlineValues.Single,
                    "double" => UnderlineValues.Double,
                    "dotted" => UnderlineValues.Dotted,
                    "dashed" => UnderlineValues.Dash,
                    "wave"   => UnderlineValues.Wave,
                    _        => null
                };
                rp.Underline = uv.HasValue ? new Underline { Val = uv.Value } : null;
            }
            return 0;
        }

        if (name == "language")
        {
            rp.Languages = string.IsNullOrEmpty(value) ? null : new Languages { Val = value };
            return 0;
        }

        return -1;
    }

    private static int SetTableStr(Table table, string name, string value)
    {
        var tp = table.GetFirstChild<TableProperties>()
            ?? table.PrependChild(new TableProperties());

        if (name == "style")
        {
            tp.TableStyle = string.IsNullOrEmpty(value) ? null : new TableStyle { Val = value };
            return 0;
        }

        if (name == "alignment")
        {
            TableRowAlignmentValues? tv = value switch
            {
                "left"   => TableRowAlignmentValues.Left,
                "center" => TableRowAlignmentValues.Center,
                "right"  => TableRowAlignmentValues.Right,
                _        => null
            };
            tp.TableJustification = tv.HasValue
                ? new TableJustification { Val = tv.Value }
                : null;
            return 0;
        }

        return -1;
    }

    private static int SetRowStr(TableRow row, string name, string value) =>
        name switch { _ => -1 };

    private static int SetCellStr(TableCell cell, string name, string value)
    {
        if (name == "text")
        {
            var para = cell.GetFirstChild<Paragraph>() ?? cell.AppendChild(new Paragraph());
            foreach (var r in para.Elements<Run>().ToList()) r.Remove();
            para.AppendChild(new Run(
                new Text(value) { Space = SpaceProcessingModeValues.Preserve }));
            return 0;
        }

        if (name == "vertical_alignment")
        {
            cell.TableCellProperties ??= new TableCellProperties();
            TableVerticalAlignmentValues? vv = value switch
            {
                "top"    => TableVerticalAlignmentValues.Top,
                "center" => TableVerticalAlignmentValues.Center,
                "bottom" => TableVerticalAlignmentValues.Bottom,
                _        => null
            };
            cell.TableCellProperties.TableCellVerticalAlignment = vv.HasValue
                ? new TableCellVerticalAlignment { Val = vv.Value }
                : null;
            return 0;
        }

        return -1;
    }

    private static int SetDocStr(DocElem d, string name, string value)
    {
        var cp = d.State.Document.PackageProperties;
        if (name == "author")      { cp.Creator     = value; return 0; }
        if (name == "title")       { cp.Title       = value; return 0; }
        if (name == "subject")     { cp.Subject     = value; return 0; }
        if (name == "description") { cp.Description = value; return 0; }
        return -1;
    }
}
