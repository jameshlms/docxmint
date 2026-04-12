using Xunit;

namespace FastDocx.Native.Tests;

/// <summary>
/// Smoke tests for the DocumentBuilder core logic.
/// These tests call internal APIs directly (no FFI / unmanaged pointers) so
/// they run safely on any platform under dotnet test.
/// </summary>
public sealed class SmokeTests
{
    [Fact]
    public void CreateDocument_ReturnsNonZeroHandle()
    {
        var handle = DocumentBuilder.CreateDocument();
        Assert.NotEqual(0, handle);
        DocumentBuilder.FreeDocument(handle);
    }

    [Fact]
    public void FreeDocument_WithInvalidHandle_DoesNotThrow()
    {
        // Freeing an unknown handle should be a no-op, not an exception.
        DocumentBuilder.FreeDocument(9999);
    }

    [Fact]
    public unsafe void AddParagraph_ReturnsNonZeroHandle()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        Assert.NotEqual(0, docHandle);

        // AddParagraph takes (docHandle, style*, styleLen) — text is added via AddRun.
        var paraHandle = DocumentBuilder.AddParagraph(docHandle, null, 0);
        Assert.NotEqual(0, paraHandle);

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void AddParagraph_WithStyle_ReturnsNonZeroHandle()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        var style = "Normal"u8.ToArray();
        fixed (byte* pStyle = style)
        {
            var paraHandle = DocumentBuilder.AddParagraph(docHandle, pStyle, style.Length);
            Assert.NotEqual(0, paraHandle);
        }

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void AddRun_ReturnsNonZeroHandle()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        var paraHandle = DocumentBuilder.AddParagraph(docHandle, null, 0);
        Assert.NotEqual(0, paraHandle);

        var text = "Hello, world!"u8.ToArray();
        fixed (byte* pText = text)
        {
            var runHandle = DocumentBuilder.AddRun(
                paraHandle, pText, text.Length,
                bold: -1, italic: -1, fontSize: 0);
            Assert.NotEqual(0, runHandle);
        }

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void AddHeading_Level1_ReturnsNonZeroHandle()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        var text = "My Heading"u8.ToArray();
        fixed (byte* pText = text)
        {
            var paraHandle = DocumentBuilder.AddHeading(docHandle, pText, text.Length, level: 1);
            Assert.NotEqual(0, paraHandle);
        }

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void AddTable_And_SetCellText_Succeed()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        var tableHandle = DocumentBuilder.AddTable(docHandle, rows: 2, cols: 2);
        Assert.NotEqual(0, tableHandle);

        var cellText = "North"u8.ToArray();
        fixed (byte* pText = cellText)
        {
            var rc = DocumentBuilder.SetCellText(tableHandle, row: 1, col: 0, pText, cellText.Length);
            Assert.Equal(0, rc);
        }

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void SaveDocument_WritesFile()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        var heading = "Test Doc"u8.ToArray();
        fixed (byte* pHeading = heading)
            DocumentBuilder.AddHeading(docHandle, pHeading, heading.Length, level: 1);

        var tmpPath = Path.GetTempFileName() + ".docx";
        try
        {
            var pathBytes = System.Text.Encoding.UTF8.GetBytes(tmpPath);
            fixed (byte* pPath = pathBytes)
            {
                var rc = DocumentBuilder.SaveDocument(docHandle, pPath, pathBytes.Length);
                Assert.Equal(0, rc);
            }

            Assert.True(File.Exists(tmpPath), "Expected output file to exist after save.");
            Assert.True(new FileInfo(tmpPath).Length > 0, "Expected non-empty .docx file.");
        }
        finally
        {
            if (File.Exists(tmpPath))
                File.Delete(tmpPath);

            DocumentBuilder.FreeDocument(docHandle);
        }
    }

    [Fact]
    public unsafe void AddParagraph_WithInvalidHandle_ReturnsZero()
    {
        var result = DocumentBuilder.AddParagraph(9999, null, 0);
        Assert.Equal(0, result);
    }

    [Fact]
    public void GetParagraphCount_EmptyDocument_ReturnsZero()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        var count = DocumentBuilder.GetParagraphCount(docHandle);
        Assert.Equal(0, count);
        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void GetParagraphCount_AfterAddingParagraphs_ReturnsCorrectCount()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        DocumentBuilder.AddParagraph(docHandle, null, 0);
        DocumentBuilder.AddParagraph(docHandle, null, 0);

        var heading = "Title"u8.ToArray();
        fixed (byte* pHeading = heading)
            DocumentBuilder.AddHeading(docHandle, pHeading, heading.Length, level: 1);

        var count = DocumentBuilder.GetParagraphCount(docHandle);
        Assert.Equal(3, count);

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void GetParagraphText_ReturnsCorrectText()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        var paraHandle = DocumentBuilder.AddParagraph(docHandle, null, 0);

        var text = "Hello FastDOCX"u8.ToArray();
        fixed (byte* pText = text)
            DocumentBuilder.AddRun(paraHandle, pText, text.Length, -1, -1, 0);

        var buf = new byte[256];
        var required = 0;
        int written;
        fixed (byte* pBuf = buf)
        {
            written = DocumentBuilder.GetParagraphText(docHandle, 0, pBuf, buf.Length, &required);
        }

        Assert.True(written > 0);
        var result = System.Text.Encoding.UTF8.GetString(buf, 0, written);
        Assert.Equal("Hello FastDOCX", result);

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void GetParagraphStyle_ReturnsStyleId()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        var styleBytes = "Normal"u8.ToArray();
        fixed (byte* pStyle = styleBytes)
            DocumentBuilder.AddParagraph(docHandle, pStyle, styleBytes.Length);

        var buf = new byte[256];
        var required = 0;
        int written;
        fixed (byte* pBuf = buf)
        {
            written = DocumentBuilder.GetParagraphStyle(docHandle, 0, pBuf, buf.Length, &required);
        }

        Assert.True(written > 0);
        var result = System.Text.Encoding.UTF8.GetString(buf, 0, written);
        Assert.Equal("Normal", result);

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void GetParagraphStyle_NoStyle_ReturnsEmpty()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        DocumentBuilder.AddParagraph(docHandle, null, 0);

        var buf = new byte[256];
        var required = 0;
        int written;
        fixed (byte* pBuf = buf)
        {
            written = DocumentBuilder.GetParagraphStyle(docHandle, 0, pBuf, buf.Length, &required);
        }

        // No style set — written should be 0 and required should be 0.
        Assert.Equal(0, written);
        Assert.Equal(0, required);

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void GetParagraphText_BufferTooSmall_ReturnsZeroAndRequired()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        var paraHandle = DocumentBuilder.AddParagraph(docHandle, null, 0);

        var text = "Hello"u8.ToArray();
        fixed (byte* pText = text)
            DocumentBuilder.AddRun(paraHandle, pText, text.Length, -1, -1, 0);

        // Provide a 2-byte buffer — too small for "Hello" (5 bytes).
        var buf = new byte[2];
        var required = 0;
        int written;
        fixed (byte* pBuf = buf)
        {
            written = DocumentBuilder.GetParagraphText(docHandle, 0, pBuf, buf.Length, &required);
        }

        Assert.Equal(0, written);
        Assert.Equal(5, required); // "Hello" = 5 bytes

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public void GetParagraphCount_WithInvalidHandle_ReturnsNegativeOne()
    {
        var count = DocumentBuilder.GetParagraphCount(9999);
        Assert.Equal(-1, count);
    }

    [Fact]
    public unsafe void RemoveParagraph_DecreasesCount()
    {
        var docHandle = DocumentBuilder.CreateDocument();

        DocumentBuilder.AddParagraph(docHandle, null, 0);
        DocumentBuilder.AddParagraph(docHandle, null, 0);
        Assert.Equal(2, DocumentBuilder.GetParagraphCount(docHandle));

        var rc = DocumentBuilder.RemoveParagraph(docHandle, 0);
        Assert.Equal(0, rc);
        Assert.Equal(1, DocumentBuilder.GetParagraphCount(docHandle));

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public unsafe void RemoveParagraph_OutOfRange_ReturnsMinusTwo()
    {
        var docHandle = DocumentBuilder.CreateDocument();
        DocumentBuilder.AddParagraph(docHandle, null, 0);

        var rc = DocumentBuilder.RemoveParagraph(docHandle, 5);
        Assert.Equal(-2, rc);

        DocumentBuilder.FreeDocument(docHandle);
    }

    [Fact]
    public void RemoveParagraph_WithInvalidHandle_ReturnsMinusOne()
    {
        var rc = DocumentBuilder.RemoveParagraph(9999, 0);
        Assert.Equal(-1, rc);
    }
}
