"""Linkage tests between legacy (NUTS 2013 / older methodology) and current series.

Purpose: decide, on evidence, whether legacy series may extend the history. Nothing is spliced
here; this module only measures agreement on the overlap period.
Run:  python -m housing_pt.linkage
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, ine, tidy

# (name, legacy indicator, current indicator, overlap definition)
LEGACY_PRICE = config.Indicator("price_legacy", "0009490",
                                "Median sales value, last 12 months (Methodology 2018, NUTS 2013)",
                                "EUR/m2", "quarterly")
LEGACY_INCOME = config.Indicator("income_legacy", "0009953",
                                 "Median gross income less IRS per tax household (NUTS 2013)",
                                 "EUR/year", "annual")
LEGACY = (LEGACY_PRICE, LEGACY_INCOME)


def _muni(code: str, category: str | None = None) -> pd.DataFrame:
    df = tidy.to_long(ine.load_raw(code), category)
    df = df[df["level"] == "municipality"].copy()
    # The 3-char NUTS III prefix of the INE geocod changes between NUTS versions; the trailing
    # 4 chars (DICO: district + municipality) are the stable municipal key.
    df["dico"] = df["geocod"].str[3:]
    if df.groupby(["dico", "year", "quarter"], dropna=False).size().max() > 1:
        raise ValueError("DICO is not unique within a period")
    return df


def compare(old: pd.DataFrame, new: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Per-period agreement between two municipal long tables."""
    m = old.merge(new, on=["dico", *keys], suffixes=("_old", "_new"))
    m = m.dropna(subset=["value_old", "value_new"])
    rows = []
    for k, g in m.groupby(keys):
        ratio = g["value_new"] / g["value_old"]
        rows.append({
            **dict(zip(keys, k if isinstance(k, tuple) else (k,))),
            "n_matched": len(g),
            "spearman": float(g["value_old"].rank().corr(g["value_new"].rank())),
            "median_ratio_new_old": float(ratio.median()),
            "median_abs_log_diff": float(np.abs(np.log(ratio)).median()),
            "share_diff_gt_5pct": float((np.abs(ratio - 1) > 0.05).mean()),
        })
    return pd.DataFrame(rows)


def geocod_overlap(old: pd.DataFrame, new: pd.DataFrame) -> dict:
    a, b = set(old["dico"]), set(new["dico"])
    return {"legacy": len(a), "current": len(b), "common": len(a & b),
            "only_legacy": sorted(a - b), "only_current": sorted(b - a)}


def run() -> dict:
    out = {}
    p_old = _muni(LEGACY_PRICE.code)
    p_new = _muni(config.PRICE.code, config.PRICE.category)
    out["price_geo"] = geocod_overlap(p_old, p_new)
    out["price"] = compare(p_old, p_new, ["year", "quarter"])
    i_old = _muni(LEGACY_INCOME.code)
    i_new = _muni(config.INCOME.code)
    out["income_geo"] = geocod_overlap(i_old, i_new)
    out["income"] = compare(i_old, i_new, ["year"])
    return out


def main() -> None:
    for ind in LEGACY:
        ine.fetch(ind.code)
    res = run()
    lines = ["# Legacy-series linkage tests (generated)", ""]
    for name in ("price", "income"):
        g = res[f"{name}_geo"]
        lines += [f"## {name}", f"Municipal DICO codes: legacy {g['legacy']}, current {g['current']}, "
                  f"common {g['common']}; only legacy {g['only_legacy']}; only current {g['only_current']}",
                  "Join key: DICO = geocod[3:] (NUTS III prefix differs between NUTS 2013 and 2024).", ""]
        df = res[name]
        lines += ["```", df.round(4).to_string(index=False), "```", ""]
    text = "\n".join(lines)
    (config.REPORTS / "linkage_report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
