"""Stage 1 pipeline: ingest -> tidy -> panels -> coverage QA -> purchase metrics.

Run:  python -m housing_pt.build [--refresh]
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import pandas as pd

from . import config, geo, ine, metrics, tidy

KEYS = ["geocod", "year"]


def _annual(ind: config.Indicator) -> pd.DataFrame:
    df = tidy.to_long(ine.load_raw(ind.code), ind.category)
    if ind.frequency == "quarterly":
        df = df[df["quarter"] == 4]  # 12-month window ending Q4 == calendar year; avoids overlap
    if df.duplicated(KEYS).any():
        raise ValueError(f"Duplicate (geocod, year) rows in {ind.key}")
    return df[["geocod", "name", "level", "year", "value"]].rename(columns={"value": ind.key})


def build_panel(level: str) -> pd.DataFrame:
    frames = [_annual(i) for i in config.INDICATORS]
    names = pd.concat(f[["geocod", "name"]] for f in frames).drop_duplicates("geocod")
    panel = None
    for f in frames:
        f = f[f["level"] == level].drop(columns=["name", "level"])
        panel = f if panel is None else panel.merge(f, on=KEYS, how="outer")
    panel = panel.merge(names, on="geocod", how="left")
    return panel.sort_values(KEYS).reset_index(drop=True)


def coverage(panel: pd.DataFrame, n_units: int) -> pd.DataFrame:
    rows = []
    for year, g in panel.groupby("year"):
        rows.append({
            "year": year,
            "price": int(g["price_m2"].notna().sum()),
            "income": int(g["income_hh"].notna().sum()),
            "rent": int(g["rent_m2"].notna().sum()),
            "purchase_complete": int((g["price_m2"].notna() & g["income_hh"].notna()).sum()),
            "rent_complete": int((g["rent_m2"].notna() & g["income_hh"].notna()).sum()),
            "units": n_units,
        })
    return pd.DataFrame(rows)


def qa_flags(panel: pd.DataFrame) -> dict:
    flags = {}
    for col in ("price_m2", "rent_m2", "income_hh"):
        s = panel[col].dropna()
        flags[col] = {"n": int(s.size), "min": float(s.min()), "median": float(s.median()),
                      "max": float(s.max()), "non_positive": int((s <= 0).sum())}
    return flags


def report(cov_m: pd.DataFrame, cov_n3: pd.DataFrame, flags: dict, manifest: list[dict]) -> str:
    def md(df):
        return "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n" + \
            "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in df.values)
    lines = [
        "# Coverage and quality report (generated)",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} by `python -m housing_pt.build`.",
        "", "Municipal values present per year (308 municipalities); price = 12-month median at Q4.", "",
        md(cov_m), "", "NUTS III values present per year.", "", md(cov_n3), "",
        "## Value ranges (municipal, all years)", "",
        md(pd.DataFrame(flags).T.reset_index().rename(columns={"index": "variable"})), "",
        "## Provenance", "",
        md(pd.DataFrame(manifest)[["code", "ine_last_update", "retrieved_at", "data_sha256"]]), "",
        "Source: Instituto Nacional de Estatistica - Portugal (Statistics Portugal), CC BY 4.0. "
        "Values are unmodified INE medians; derived metrics are the authors' calculations.",
    ]
    return "\n".join(lines) + "\n"


def main(refresh: bool = False) -> None:
    for d in (config.INTERIM, config.PROCESSED, config.MANIFESTS, config.REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    manifest = [ine.fetch(i.code, force=refresh) for i in (*config.INDICATORS, config.CPI)]
    (config.MANIFESTS / "ine_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    long_all = tidy.to_long(ine.load_raw(config.INCOME.code))
    key = geo.build_key(long_all)
    key.to_parquet(config.PROCESSED / "geo_key.parquet", index=False)

    muni = build_panel("municipality")
    nuts3 = build_panel("nuts3")
    muni = muni.merge(key[["geocod", "municipality", "nuts3_code", "nuts2_code"]], on="geocod", how="left")
    if muni["municipality"].isna().any():
        raise ValueError("Municipal geocod missing from geographic key")
    cpi_long = tidy.to_long(ine.load_raw(config.CPI.code), config.CPI.category)
    cpi = cpi_long[cpi_long["geocod"] == "PT"].set_index("year")["value"]
    if cpi.index.max() < 2024 or cpi.loc[2025] != 100:
        raise ValueError("CPI series incomplete or base year not 2025=100")
    muni = metrics.add_all_metrics(muni, cpi)
    nuts3 = metrics.add_all_metrics(nuts3, cpi)
    muni.to_parquet(config.PROCESSED / "panel_municipality.parquet", index=False)
    nuts3.to_parquet(config.PROCESSED / "panel_nuts3.parquet", index=False)

    window = lambda p: p[p["year"].between(2019, 2025)]
    text = report(coverage(window(muni), muni["geocod"].nunique()),
                  coverage(window(nuts3), nuts3["geocod"].nunique()),
                  qa_flags(muni), manifest)
    (config.REPORTS / "coverage_report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download raw INE JSON")
    main(ap.parse_args().refresh)
