"""Geographic key derived from INE geocodes (NUTS 2024).

Verified 2026-11-22 on indicator 0012741: all 308 municipal geocods (7 chars) start with a
3-char NUTS III geocod listed by INE, and the first 2 chars give the NUTS II geocod.
NOTE: the 3-char prefix is specific to the NUTS version (2013 vs 2024); only `dico`
(geocod[3:]) is stable across versions - always join across vintages on `dico`.
CAOP 2025 geometry is NOT used here yet (not downloaded; licence is CC BY 4.0 per dados.gov.pt/DGT).
"""
from __future__ import annotations

import pandas as pd

EXPECTED_MUNICIPALITIES = 308


def build_key(long_df: pd.DataFrame) -> pd.DataFrame:
    """Municipality -> NUTS III / NUTS II key with names, from any tidy table."""
    names = long_df.drop_duplicates("geocod").set_index("geocod")["name"]
    nuts3 = {g: n for g, n in names.items() if len(g) == 3}
    nuts2 = {g: n for g, n in names.items() if len(g) == 2 and g != "PT"}
    muni = sorted(g for g in names.index if len(g) == 7)
    key = pd.DataFrame({"geocod": muni})
    key["municipality"] = key["geocod"].map(names)
    key["dico"] = key["geocod"].str[3:]  # stable municipal code (district+municipality); joins to CAOP
    if key["dico"].duplicated().any():
        raise ValueError("DICO not unique")
    key["nuts3_code"] = key["geocod"].str[:3]
    key["nuts2_code"] = key["geocod"].str[:2]
    key["nuts3"] = key["nuts3_code"].map(nuts3)
    key["nuts2"] = key["nuts2_code"].map(nuts2)
    missing = key[key[["nuts3", "nuts2"]].isna().any(axis=1)]
    if len(key) != EXPECTED_MUNICIPALITIES or len(missing):
        raise ValueError(
            f"Geographic key inconsistent: {len(key)} municipalities, {len(missing)} without NUTS parent")
    return key
