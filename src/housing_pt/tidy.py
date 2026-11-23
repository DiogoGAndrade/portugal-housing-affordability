"""Convert INE JSON payloads into tidy tables. No imputation; suppressed values stay NaN."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

_QUARTER = re.compile(r"^(\d)(?:st|nd|rd|th) Quarter (\d{4})$")

# INE geocod length -> level
LEVELS = {1: "country_or_nuts1", 2: "nuts2", 3: "nuts3", 7: "municipality", 9: "parish"}


def parse_period(label: str) -> tuple[int, int | None]:
    """'2024' -> (2024, None); '4th Quarter 2019' -> (2019, 4)."""
    label = label.strip()
    m = _QUARTER.match(label)
    if m:
        return int(m.group(2)), int(m.group(1))
    if re.fullmatch(r"\d{4}", label):
        return int(label), None
    raise ValueError(f"Unrecognised INE period label: {label!r}")


def to_long(payload: dict, category: str | None = None) -> pd.DataFrame:
    """Flatten the 'Dados' block. If `category` is given, keep only rows whose dim_3_t equals it
    and fail loudly if the indicator has no such dimension (never silently mix categories)."""
    rows = []
    for period_label, records in payload["Dados"].items():
        year, quarter = parse_period(period_label)
        for r in records:
            rows.append((r["geocod"], r["geodsg"], year, quarter, r.get("dim_3_t"), r.get("valor")))
    df = pd.DataFrame(rows, columns=["geocod", "name", "year", "quarter", "category", "value"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["level"] = df["geocod"].str.len().map(LEVELS)
    if category is not None:
        if df["category"].isna().all():
            raise ValueError("Category requested but indicator has no category dimension")
        if category not in set(df["category"].dropna()):
            raise ValueError(f"Category {category!r} not found")
        df = df[df["category"] == category]
    elif df["category"].notna().any():
        raise ValueError("Indicator has a category dimension; select one explicitly")
    return df.drop(columns="category").reset_index(drop=True)
