"""Indicator registry. Every code was verified against the INE API on 2026-11-22
(see docs/data_sources.md)."""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
MANIFESTS = ROOT / "data" / "manifests"
REPORTS = ROOT / "reports"

INE_BASE = "https://www.ine.pt/ine/json_indicador"
MIN_INTERVAL_S = 0.2  # <= 5 req/s, well inside INE's 15-20 req/s guidance


@dataclass(frozen=True)
class Indicator:
    key: str
    code: str
    description: str
    unit: str
    frequency: str  # "annual" | "quarterly"
    category: str | None = None  # required dim_3_t value, if the indicator has one


PRICE = Indicator("price_m2", "0012234",
                  "Median dwelling sales value, last 12 months (Methodology 2022)",
                  "EUR/m2", "quarterly", category="Total")
RENT = Indicator("rent_m2", "0014698",
                 "Median rent of new leases (Methodology 2026)", "EUR/m2/month", "annual")
INCOME = Indicator("income_hh", "0012741",
                   "Median gross reported income less IRS per tax household", "EUR/year", "annual")

CPI = Indicator("cpi", "0014642", "Consumer price index, annual average, base 2025=100 (Portugal, Total)",
                "index", "annual", category="Total")

# Sensitivity-only income variants (Phase 4)
INCOME_GROSS_HH = Indicator("income_gross_hh", "0012712",
                            "Median gross reported income per tax household", "EUR/year", "annual")
INCOME_NET_TP = Indicator("income_net_taxpayer", "0012757",
                          "Median gross reported income less IRS per taxpayer", "EUR/year", "annual")
SENSITIVITY_INDICATORS = (INCOME_GROSS_HH, INCOME_NET_TP)

INDICATORS = (PRICE, RENT, INCOME)
DEFLATOR = CPI  # fetched separately; used for real (2025 EUR) variants

BASE_YEAR_PURCHASE = 2019
BASE_YEAR_RENT = 2020
HEADLINE_AREA_M2 = 80

PURCHASE_YEARS = range(2019, 2025)  # price + income common window
RENT_YEARS = range(2020, 2025)      # rent + income common window
