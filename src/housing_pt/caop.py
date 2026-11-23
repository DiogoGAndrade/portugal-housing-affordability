"""CAOP 2025 (DGT) helpers. Licence: CC BY 4.0 - attribution text:
"Informacao geografica cedida pela Direcao-Geral do Territorio".

Files are downloaded manually into data/raw/caop/ (see data/manifests/caop_manifest.json) and
unzipped to x_<zipname>/. Attribute tables are read read-only through stdlib sqlite3, so
no geometry library is needed to validate the join key. Geometry work (maps, Moran's I)
will need geopandas/pyogrio (Phase 3).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from . import config

CAOP_DIR = config.RAW / "caop"
ATTRIBUTION = "Informação geográfica cedida pela Direção-Geral do Território"


def municipality_attributes(caop_dir: Path = CAOP_DIR) -> pd.DataFrame:
    """Return one row per municipality (dtmn == INE `dico`) from every *municipios layer."""
    rows = []
    for gpkg in sorted(caop_dir.glob("x_*/*.gpkg")):
        con = sqlite3.connect(f"file:{gpkg.as_posix()}?mode=ro", uri=True)
        try:
            layers = [r[0] for r in con.execute(
                "select table_name from gpkg_contents where table_name like '%municipios'")]
            for t in layers:
                rows += con.execute(
                    f'select dtmn, municipio, nuts3_cod, nuts3, nuts2 from "{t}"').fetchall()
        finally:
            con.close()
    df = pd.DataFrame(rows, columns=["dico", "municipality_caop", "nuts3_code_caop",
                                     "nuts3_caop", "nuts2_caop"])
    if df["dico"].duplicated().any():
        raise ValueError("Duplicate DICO in CAOP municipalities")
    return df


def check_join(key: pd.DataFrame, caop_df: pd.DataFrame) -> dict:
    """Compare the INE-derived key with CAOP on `dico` (names compared case-insensitively)."""
    m = key.merge(caop_df, on="dico", how="outer", indicator=True)
    both = m[m["_merge"] == "both"]
    return {
        "both": int((m["_merge"] == "both").sum()),
        "ine_only": int((m["_merge"] == "left_only").sum()),
        "caop_only": int((m["_merge"] == "right_only").sum()),
        "name_equal": int((both["municipality"].str.casefold() == both["municipality_caop"].str.casefold()).sum()),
        "nuts3_name_equal": int((both["nuts3"].str.casefold() == both["nuts3_caop"].str.casefold()).sum()),
    }
