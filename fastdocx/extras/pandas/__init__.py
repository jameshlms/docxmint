"""Pandas integration for fastdocx.

>>> import fastdocx.extras.pandas as fdx_pd
>>> df = fdx_pd.to_dataframe(table)          # first row → column names
>>> df = fdx_pd.to_dataframe(table, header=False)  # all rows → data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from fastdocx.table import Table


def to_dataframe(table: Table, *, header: bool = True) -> pd.DataFrame:
    """Convert a :class:`~fastdocx.table.Table` to a :class:`pandas.DataFrame`.

    Args:
        table: A live fastdocx table proxy.
        header: If ``True`` (default), treat the first row as column names.
            If ``False``, all rows become data rows with a default integer index.

    Returns:
        A :class:`pandas.DataFrame` whose cells contain the table's plain text.
    """
    import pandas as pd

    data = table.data
    if not data:
        return pd.DataFrame()

    if header:
        return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame(data)
