"""End-to-end checks on synthetic INE-shaped data: pipeline -> panels -> metrics -> dashboard.
No network, no licensed data, no private files: runs identically in CI and locally."""
import json
import math
import re

import numpy as np
import pandas as pd
import pytest

from housing_pt import build, config, dashboard, linkage

from . import synth

A1, A2, B1, B2 = "11A0101", "11A0102", "11B0201", "11B0202"


@pytest.fixture()
def built(synth_env):
    build.main()
    muni = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet").set_index(["geocod", "year"])
    nuts3 = pd.read_parquet(config.PROCESSED / "panel_nuts3.parquet").set_index(["geocod", "year"])
    key = pd.read_parquet(config.PROCESSED / "geo_key.parquet")
    return muni, nuts3, key


def test_annual_price_is_q4_total_and_suppression_is_not_filled(built):
    muni, _, _ = built
    assert muni.loc[(A1, 2021), "price_m2"] == pytest.approx(1200.0)      # Q4 (not Q3 = 1150), Total (not New/Existing)
    assert muni.loc[(A2, 2023), "price_m2"] == pytest.approx(500.0)
    assert pd.isna(muni.loc[(B2, 2021), "price_m2"])                      # Q4 suppressed; Q3 value 1450 must not leak
    assert pd.isna(muni.loc[(B1, 2019), "income_hh"])                     # suppressed income stays missing
    assert muni.loc[(A2, 2022), "rent_m2"] != muni.loc[(A2, 2022), "rent_m2"]  # never-published rent is NaN, not 0


def test_metrics_match_hand_calculation(built):
    muni, _, _ = built
    r = muni.loc[(A1, 2021)]
    assert r["income_hh"] == 11500 and r["rent_m2"] == pytest.approx(5.5)
    assert r["i1_m2_per_income_year"] == pytest.approx(11500 / 1200)
    assert r["i2_years_80m2"] == pytest.approx(80 * 1200 / 11500)
    assert r["i2_years_60m2"] == pytest.approx(60 * 1200 / 11500)
    assert r["i3_rent_share_80m2"] == pytest.approx(12 * 80 * 5.5 / 11500)
    assert r["i4_rent_over_price"] == pytest.approx(12 * 5.5 / 1200)
    assert r["price_m2_real2025"] == pytest.approx(1200 * 100 / 94.0)      # CPI 'Total' (94), not the decoy category (50)
    base_p, base_y = 1000.0, 10500.0
    assert r["i6_price_vs_income_real"] == pytest.approx(math.log(1200 / base_p) - math.log(11500 / base_y))
    assert muni.loc[(A1, 2019), "i6_price_vs_income_real"] == pytest.approx(0.0)
    assert muni.loc[(A1, 2020), "i6_rent_vs_income_real"] == pytest.approx(0.0)   # rent base year 2020


def test_nuts3_values_are_official_not_averages(built):
    muni, nuts3, _ = built
    assert nuts3.loc[("11A", 2020), "price_m2"] == pytest.approx(850.0)     # INE-published value
    mean_a = np.mean([muni.loc[(A1, 2020), "price_m2"], muni.loc[(A2, 2020), "price_m2"]])
    assert abs(mean_a - 850.0) > 1                                            # the unweighted mean differs
    assert nuts3.loc[("11B", 2024), "income_hh"] == pytest.approx(10500.0)


def test_geographic_key(built):
    _, _, key = built
    assert len(key) == 4 and key["dico"].is_unique
    assert dict(zip(key["geocod"], key["nuts3"]))[B2] == "Regiao Beta"
    assert set(key["dico"]) == {g[3:] for g in synth.MUNI}
    assert set(key["nuts2"]) == {"Norte"}


def test_temporal_coverage_and_reports(built):
    muni, _, _ = built
    cnt = muni.groupby("year")[["price_m2", "income_hh", "rent_m2"]].count()
    assert cnt.loc[2025, "income_hh"] == 0                                    # income ends 2024: no extrapolation
    assert cnt.loc[2019, "rent_m2"] == 0 and cnt.loc[2020, "rent_m2"] == 3     # rent starts 2020; A2 never published
    assert (config.REPORTS / "coverage_report.md").exists()
    manifest = json.loads((config.MANIFESTS / "ine_manifest.json").read_text(encoding="utf-8"))
    assert {m["code"] for m in manifest} == {"0012234", "0014698", "0012741", "0014642"}
    assert all(len(m["data_sha256"]) == 64 and "CC BY 4.0" in m["licence"] for m in manifest)


def test_dashboard_embeds_pipeline_values(built, synth_geometry, tmp_path):
    muni, nuts3, key = built
    out = dashboard.build(tmp_path / "site", geometry=synth_geometry)
    html = out.read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA=(\{.*?\});\n// ==CORE-START==", html, re.S).group(1))
    assert len(data["municipality"]) == 4 and len(data["nuts3"]) == 2
    assert not re.search(r"""(src|href)=["']https?:""", html) and "<script src" not in html
    for u in data["municipality"]:
        for col, k in (("price_m2", "P"), ("income_hh", "Y"), ("rent_m2", "R")):
            for i, y in enumerate(data["years"]):
                w = muni[col].get((u["id"], y), np.nan)
                v = u[k][i]
                assert (v is None and pd.isna(w)) or v == pytest.approx(w), (u["id"], k, y)
    for r in data["nuts3"]:                                                   # official NUTS III values embedded
        assert r["P"][data["years"].index(2020)] == pytest.approx(nuts3.loc[(r["id"], 2020), "price_m2"])
    assert data["cpi"] == [90.0, 92.0, 94.0, 96.0, 98.0, 99.0, 100.0]
    assert "Informação geográfica cedida pela Direção-Geral do Território" in html
    assert "bpstat" not in html.lower()


def test_linkage_joins_on_dico_across_geocod_vintages(built):
    res = linkage.run()
    g = res["price_geo"]
    assert g["common"] == 4 and g["only_legacy"] == [] and g["only_current"] == []   # dico joins all municipalities
    p = res["price"]
    assert (p["n_matched"] >= 2).all()
    assert (p["share_diff_gt_5pct"] > 0).all()                                # one municipality differs by 10%
    assert (res["income"]["share_diff_gt_5pct"] == 0).all()                   # identical income vintages
    assert (res["income"]["median_ratio_new_old"] == 1).all()


def test_site_headers_pin_csp_to_inline_script_and_style(built, synth_geometry, tmp_path):
    import base64
    import hashlib
    out = dashboard.build(tmp_path / "site", geometry=synth_geometry)
    html = out.read_text(encoding="utf-8")
    headers = (out.parent / "_headers").read_text(encoding="utf-8")
    h = lambda t: base64.b64encode(hashlib.sha256(t.encode("utf-8")).digest()).decode()
    script, style = (re.findall(rf"<{t}>(.*?)</{t}>", html, re.S) for t in ("script", "style"))
    assert len(script) == 1 and len(style) == 1
    assert f"script-src 'sha256-{h(script[0])}'" in headers and f"style-src 'sha256-{h(style[0])}'" in headers
    for needed in ("default-src 'none'", "connect-src 'none'", "frame-ancestors 'none'", "X-Content-Type-Options: nosniff",
                   "Referrer-Policy: no-referrer", "Strict-Transport-Security"):
        assert needed in headers
    assert "unsafe-inline" not in headers and "unsafe-eval" not in headers
    assert not re.search(r"""style=["']""", html)             # no inline style attributes: the CSP needs none
    assert b"\r" not in out.read_bytes() and b"\r" not in (out.parent / "_headers").read_bytes()   # served bytes = hashed text
