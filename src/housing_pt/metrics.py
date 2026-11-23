"""Affordability metrics I1 and I2 (docs/methodology_proposal.md).

Y = median gross reported income less IRS per tax household (EUR/year)
P = median sales value (EUR/m2)
All values nominal. Not disposable income; not mortgage eligibility.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REFERENCE_AREAS_M2 = (60, 80, 100)  # documented assumption; 80 is the headline, others are sensitivity


def i1_m2_per_income_year(income: pd.Series, price_m2: pd.Series) -> pd.Series:
    """I1: square metres of dwelling per year of median household income (higher = more affordable)."""
    return income / price_m2.where(price_m2 > 0)


def i2_years_of_income(income: pd.Series, price_m2: pd.Series, area_m2: float) -> pd.Series:
    """I2: years of median household income to buy a reference dwelling of `area_m2`."""
    return (area_m2 * price_m2) / income.where(income > 0)


def i3_rent_to_income(income: pd.Series, rent_m2: pd.Series, area_m2: float) -> pd.Series:
    """I3: share of annual median household income needed to rent `area_m2` at the median new-lease
    rent (entry cost of the market; NOT the rent paid by existing tenants)."""
    return (12 * area_m2 * rent_m2) / income.where(income > 0)


def i4_rent_over_price(rent_m2: pd.Series, price_m2: pd.Series) -> pd.Series:
    """I4: annualised rent / price (ratio of medians from differently composed samples; indicative only)."""
    return (12 * rent_m2) / price_m2.where(price_m2 > 0)


def to_real(nominal: pd.Series, cpi: pd.Series) -> pd.Series:
    """Express nominal values in base-year (CPI=100) euros."""
    return nominal * 100.0 / cpi.where(cpi > 0)


def i6_divergence(df: pd.DataFrame, num: str, income: str, base_year: int, by: str = "geocod") -> pd.Series:
    """I6: ln(num_t/num_base) - ln(income_t/income_base), per unit. Positive = num outgrew income.
    Needs both values in the base year; otherwise NaN."""
    def one(g: pd.DataFrame) -> pd.Series:
        b = g[g["year"] == base_year]
        if b.empty or pd.isna(b[num].iloc[0]) or pd.isna(b[income].iloc[0]):
            return pd.Series(np.nan, index=g.index)
        return np.log(g[num] / b[num].iloc[0]) - np.log(g[income] / b[income].iloc[0])
    return df.groupby(by, group_keys=False).apply(one, include_groups=False)


def add_all_metrics(df: pd.DataFrame, cpi_by_year: pd.Series) -> pd.DataFrame:
    """Purchase (I1, I2), rent (I3, I4), real-terms variants and I6. Nominal columns are untouched."""
    out = add_purchase_metrics(df)
    for a in REFERENCE_AREAS_M2:
        out[f"i3_rent_share_{a}m2"] = i3_rent_to_income(out["income_hh"], out["rent_m2"], a)
    out["i4_rent_over_price"] = i4_rent_over_price(out["rent_m2"], out["price_m2"])
    cpi = out["year"].map(cpi_by_year)
    for c in ("price_m2", "rent_m2", "income_hh"):
        out[f"{c}_real2025"] = to_real(out[c], cpi)
    out["i6_price_vs_income_real"] = i6_divergence(out, "price_m2_real2025", "income_hh_real2025",
                                                   2019)
    out["i6_rent_vs_income_real"] = i6_divergence(out, "rent_m2_real2025", "income_hh_real2025",
                                                  2020)
    return out


def add_purchase_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["i1_m2_per_income_year"] = i1_m2_per_income_year(out["income_hh"], out["price_m2"])
    for a in REFERENCE_AREAS_M2:
        out[f"i2_years_{a}m2"] = i2_years_of_income(out["income_hh"], out["price_m2"], a)
    return out
