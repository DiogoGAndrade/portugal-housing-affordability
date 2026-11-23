"""Dashboard vs pipeline consistency. Needs the processed panels (built locally; skipped in CI)."""
import json
import re

import numpy as np
import pandas as pd
import pytest

from housing_pt import caop, config, dashboard

pytestmark = pytest.mark.skipif(not (config.PROCESSED / "panel_municipality.parquet").exists(),
                                reason="processed panels not built")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = dashboard.build(tmp_path_factory.mktemp("site"))
    html = out.read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA=(\{.*?\});\n// ==CORE-START==", html, re.S).group(1))
    return data, html


def _norm(s):
    return s.replace("\r\n", "\n")


def test_committed_site_is_not_stale(built):
    _, html = built
    committed = (config.ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert _norm(committed) == _norm(html), "site/index.html is stale: rerun python -m housing_pt.dashboard"


def test_embedded_inputs_equal_panel_for_every_unit_and_year(built):
    data, html = built
    assert not re.search(r"""(src|href)=["']https?:""", html) and "<script src" not in html  # no external loads
    panel = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet").set_index(["geocod", "year"])
    assert len(data["municipality"]) == 308 and len(data["nuts3"]) == 26 and data["years"] == list(range(2019, 2026))
    for u in data["municipality"]:
        for col, k in (("price_m2", "P"), ("income_hh", "Y"), ("rent_m2", "R")):
            for i, y in enumerate(data["years"]):
                w = panel[col].get((u["id"], y), np.nan)
                v = u[k][i]
                assert (v is None and pd.isna(w)) or v == pytest.approx(w), (u["id"], k, y)
    assert data["cpi"][-1] == 100.0  # CPI base 2025


def test_dashboard_i2_equals_pipeline_i2(built):
    data, _ = built
    panel = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet").set_index(["geocod", "year"])
    i = data["years"].index(2024)
    for u in data["municipality"]:
        p, y = u["P"][i], u["Y"][i]
        w = panel["i2_years_80m2"].get((u["id"], 2024), np.nan)
        got = 80 * p / y if p is not None and y is not None else None
        assert (got is None and pd.isna(w)) or got == pytest.approx(w)


def test_nuts3_values_are_official_not_averages_of_municipalities(built):
    data, _ = built
    n3 = pd.read_parquet(config.PROCESSED / "panel_nuts3.parquet").set_index(["geocod", "year"])
    i = data["years"].index(2024)
    for r in data["nuts3"]:
        assert r["P"][i] == pytest.approx(n3["price_m2"][(r["id"], 2024)])   # INE-published NUTS III value
    muni = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet")  # carries nuts3_code
    mean = muni[muni["year"] == 2024].groupby("nuts3_code")["price_m2"].mean()
    diffs = [abs(mean[r["id"]] - r["P"][i]) > 1 for r in data["nuts3"] if r["id"] in mean.index]
    assert sum(diffs) >= 10   # official values genuinely differ from unweighted municipal means


def test_geographic_joins(built):
    data, _ = built
    key = pd.read_parquet(config.PROCESSED / "geo_key.parquet")
    assert set(u["id"] for u in data["municipality"]) == set(key["geocod"]) and key["dico"].is_unique
    names = key.set_index("geocod")["nuts3"]
    assert all(u["nuts3"] == names[u["id"]] for u in data["municipality"])
    assert {r["id"] for r in data["nuts3"]} == set(key["nuts3_code"])
    if list(caop.CAOP_DIR.glob("x_*/*.gpkg")):
        res = caop.check_join(key, caop.municipality_attributes())
        assert res["both"] == 308 and res["ine_only"] == 0 and res["caop_only"] == 0 and res["nuts3_name_equal"] == 308


def test_temporal_coverage_bounds():
    """Coverage windows documented in docs/feasibility_audit.md (loose bounds: INE revisions may shift counts)."""
    p = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet")
    cnt = p.groupby("year")[["price_m2", "income_hh", "rent_m2"]].count()
    assert (cnt.loc[2019:2025, "price_m2"] >= 275).all()                      # price from 2019 (Q4 value)
    assert (cnt.loc[2019:2024, "income_hh"] >= 290).all() and cnt.loc[2025, "income_hh"] == 0   # income ends 2024
    assert cnt.loc[2019, "rent_m2"] == 0 and (cnt.loc[2020:2025, "rent_m2"] >= 215).all()          # rent starts 2020
    assert (cnt.loc[2020:2025, "rent_m2"] < 260).all()                                             # not complete
    assert p.duplicated(["geocod", "year"]).sum() == 0
