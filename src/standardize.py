from __future__ import annotations

import pandas as pd

from src.constants import NEGATIVE_ORIENTATION
from src.utils import inverse_normal_rank


def standardize_role_primitives(role_df: pd.DataFrame, primitive_columns: list[str]) -> pd.DataFrame:
    standardized = pd.DataFrame(index=role_df.index, columns=primitive_columns, dtype=float)
    for primitive in primitive_columns:
        values = role_df[primitive].astype(float)
        if primitive in NEGATIVE_ORIENTATION:
            values = -values
        standardized[primitive] = inverse_normal_rank(values)
    return standardized
