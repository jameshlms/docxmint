#!/usr/bin/env python3
"""CI guard: every struct in Marshalling/StructLayouts.cs must carry
[StructLayout(LayoutKind.Sequential)].

Exit code 0  — all structs are correctly annotated.
Exit code 1  — one or more structs are missing the attribute (names printed).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STRUCT_LAYOUTS_PATH = (
    Path(__file__).parent.parent
    / "native"
    / "FastDocx.Native"
    / "Marshalling"
    / "StructLayouts.cs"
)

# Matches [StructLayout(LayoutKind.Sequential)] immediately before a struct
# declaration (optional whitespace / access modifiers between them).
_ANNOTATED_STRUCT = re.compile(
    r"\[StructLayout\(LayoutKind\.Sequential\)\]"
    r"(?:\s+(?:public|internal|private|readonly|unsafe|partial))*"
    r"\s+struct\s+(\w+)",
    re.MULTILINE,
)

# Matches any struct declaration
_ANY_STRUCT = re.compile(
    r"(?:^|\s)struct\s+(\w+)",
    re.MULTILINE,
)


def main() -> int:
    source = STRUCT_LAYOUTS_PATH.read_text(encoding="utf-8")

    annotated = {m.group(1) for m in _ANNOTATED_STRUCT.finditer(source)}
    all_structs = {m.group(1) for m in _ANY_STRUCT.finditer(source)}

    missing = all_structs - annotated
    if missing:
        for name in sorted(missing):
            print(
                f"ERROR: struct '{name}' in {STRUCT_LAYOUTS_PATH} is missing "
                "[StructLayout(LayoutKind.Sequential)]",
                file=sys.stderr,
            )
        return 1

    print(
        f"OK: all {len(all_structs)} struct(s) in StructLayouts.cs carry "
        "[StructLayout(LayoutKind.Sequential)]."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
