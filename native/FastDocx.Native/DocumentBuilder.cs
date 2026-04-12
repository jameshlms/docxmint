using System.Collections.Concurrent;

namespace FastDocx.Native;

/// <summary>
/// Manages document and table object lifetimes via opaque integer handles,
/// and wires FFI calls to OpenXML operations.
/// </summary>
internal static partial class DocumentBuilder
{
    // --- Handle registries ---

    private static readonly ConcurrentDictionary<nint, DocumentState> SDocuments = new();
    private static readonly ConcurrentDictionary<nint, TableState> STables = new();
    private static readonly ConcurrentDictionary<nint, DocumentFormat.OpenXml.Wordprocessing.Paragraph> SParagraphs = new();
    private static readonly ConcurrentDictionary<nint, DocumentFormat.OpenXml.Wordprocessing.Run> SRuns = new();
    private static long _snextHandle = 1;

    private static nint NextHandle() =>
        (nint)Interlocked.Increment(ref _snextHandle);

    // --- Private state types ---

    private sealed record DocumentState(
        DocumentFormat.OpenXml.Packaging.WordprocessingDocument Document,
        MemoryStream Stream);

    private sealed record TableState(
        DocumentFormat.OpenXml.Wordprocessing.Table Table,
        DocumentFormat.OpenXml.Wordprocessing.TableCell[,] Cells,
        int Rows,
        int Cols);
}
