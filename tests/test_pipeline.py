import numpy as np
import pandas as pd
import pytest

from housing_pt import geo, metrics, tidy


def payload():
    return {"Dados": {
        "4th Quarter 2019": [
            {"geocod": "1111111", "geodsg": "A", "dim_3": "T", "dim_3_t": "Total", "valor": "1000"},
            {"geocod": "1111111", "geodsg": "A", "dim_3": "N", "dim_3_t": "New", "valor": "2000"},
            {"geocod": "1111112", "geodsg": "B", "dim_3": "T", "dim_3_t": "Total"},  # suppressed
        ]}}


def test_parse_period():
    assert tidy.parse_period("4th Quarter 2019") == (2019, 4)
    assert tidy.parse_period("2024") == (2024, None)
    with pytest.raises(ValueError):
        tidy.parse_period("H1 2024")


def test_category_must_be_explicit():
    with pytest.raises(ValueError):
        tidy.to_long(payload())
    df = tidy.to_long(payload(), "Total")
    assert len(df) == 2 and df["value"].isna().sum() == 1  # suppressed stays NaN, never imputed
    assert df.loc[df.geocod == "1111111", "value"].iloc[0] == 1000


def test_levels():
    df = tidy.to_long(payload(), "Total")
    assert set(df["level"]) == {"municipality"}


def test_metrics_identities():
    income = pd.Series([20000.0, 10000.0, None])
    price = pd.Series([2000.0, 1000.0, 1500.0])
    i1 = metrics.i1_m2_per_income_year(income, price)
    assert i1.iloc[0] == pytest.approx(10.0)
    i2 = metrics.i2_years_of_income(income, price, 80)
    assert i2.iloc[0] == pytest.approx(8.0)
    assert i2.iloc[0] == pytest.approx(80 / i1.iloc[0])  # I2 = A / I1
    assert pd.isna(i2.iloc[2])


def test_geo_key_consistency():
    rows = [("1111111" if False else f"11A{i:04d}", f"M{i}", 2024, None, None, 1.0, "municipality")
            for i in range(308)]
    df = pd.DataFrame(rows, columns=["geocod", "name", "year", "quarter", "category", "value", "level"])
    extra = pd.DataFrame([("11A", "N3", 2024, None, None, 1.0, "nuts3"),
                          ("11", "N2", 2024, None, None, 1.0, "nuts2")], columns=df.columns)
    key = geo.build_key(pd.concat([df, extra]))
    assert len(key) == 308 and (key["nuts3"] == "N3").all()
    with pytest.raises(ValueError):
        geo.build_key(pd.concat([df.iloc[:300], extra]))


def test_dico_is_stable_join_key():
    from housing_pt import linkage
    old = pd.DataFrame({"dico": ["1001", "0101"], "year": [2020, 2020], "value": [100.0, 200.0],
                        "geocod": ["16B1001", "16B0101"]})
    new = pd.DataFrame({"dico": ["1001", "0101"], "year": [2020, 2020], "value": [100.0, 210.0],
                        "geocod": ["1D11001", "1910101"]})
    assert set(old["geocod"]).isdisjoint(new["geocod"])  # raw geocods differ across NUTS versions
    out = linkage.compare(old, new, ["year"])
    assert out["n_matched"].iloc[0] == 2 and out["share_diff_gt_5pct"].iloc[0] == 0.5


def test_caop_join_check():
    from housing_pt import caop
    key = pd.DataFrame({"dico": ["0101", "0102"], "municipality": ["A", "B"], "nuts3": ["X", "X"]})
    cp = pd.DataFrame({"dico": ["0101", "0103"], "municipality_caop": ["a", "C"], "nuts3_caop": ["x", "X"]})
    r = caop.check_join(key, cp)
    assert (r["both"], r["ine_only"], r["caop_only"], r["name_equal"]) == (1, 1, 1, 1)


def test_rent_metrics_and_real_terms():
    assert metrics.i3_rent_to_income(pd.Series([12000.0]), pd.Series([10.0]), 80).iloc[0] == pytest.approx(0.8)
    assert metrics.i4_rent_over_price(pd.Series([10.0]), pd.Series([2400.0])).iloc[0] == pytest.approx(0.05)
    assert metrics.to_real(pd.Series([110.0]), pd.Series([110.0])).iloc[0] == pytest.approx(100.0)


def test_i6_zero_at_base_and_nan_without_base():
    df = pd.DataFrame({"geocod": ["a"] * 3 + ["b"] * 2, "year": [2019, 2020, 2021, 2020, 2021],
                       "p": [100.0, 110.0, 121.0, 50.0, 55.0], "y": [100.0, 100.0, 110.0, 40.0, 40.0]})
    d = metrics.i6_divergence(df, "p", "y", 2019)
    assert d.iloc[0] == pytest.approx(0.0)
    assert d.iloc[2] == pytest.approx(np.log(1.21) - np.log(1.10))
    assert d.iloc[3:].isna().all()  # no 2019 base for b -> NaN, not imputed


def test_payment_scenario_math():
    from housing_pt import phase4
    # 100k at 12%/yr over 1 year: standard annuity payment
    pmt = phase4.monthly_payment(pd.Series([100000.0]), 12.0, years=1).iloc[0]
    assert pmt == pytest.approx(8884.88, abs=0.01)
    assert phase4.monthly_payment(pd.Series([1200.0]), 0.0, years=1).iloc[0] == pytest.approx(100.0)
    i5 = phase4.payment_to_income(pd.Series([1000.0]), pd.Series([12000.0]), 0.0, area=10, ltv=1.0, years=1)
    assert i5.iloc[0] == pytest.approx(10000 / 12 / 1000)


def test_sensitivity_area_free_and_identity():
    from housing_pt import phase4
    v = pd.DataFrame({"p_total": [1000., 2000., 3000., 4000., 5000., 6000.] * 2,
                      "p_new": [1100., 2100., 2900., 4200., 5100., 5900.] * 2,
                      "p_existing": [900., 1900., 3100., 3900., 4900., 6100.] * 2,
                      "y_net_hh": [10000., 11000., 12000., 13000., 14000., 15000.] * 2,
                      "y_gross_hh": [12000., 13200., 14400., 15600., 16800., 18000.] * 2,
                      "y_net_tp": [8000., 8800., 9600., 10400., 11200., 12000.] * 2})
    s = phase4.sensitivity(v)
    g = s[s["variant"].str.contains("gross")].iloc[0]
    assert g["spearman_vs_headline"] == pytest.approx(1.0) and g["median_ratio_alt_over_headline"] == pytest.approx(10000 / 12000)
