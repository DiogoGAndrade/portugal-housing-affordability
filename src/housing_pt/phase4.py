"""Phase 4 exploratory analysis: sensitivity, NUTS II tests, spatial autocorrelation,
clustering, rent-gap profile, mortgage-payment scenario.

Exploratory and descriptive. Municipal medians have no published sampling error, so p-values
are indicative only (municipalities are not independent draws).
Run:  python -m housing_pt.phase4
"""
from __future__ import annotations

import json
import urllib.request

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats

from . import caop, config, ine, tidy

SEED = 20261122
YEAR = 2024


# --------------------------------------------------------------------------- data
def _annual(ind: config.Indicator, category: str | None, level: str = "municipality") -> pd.DataFrame:
    df = tidy.to_long(ine.load_raw(ind.code), category)
    if ind.frequency == "quarterly":
        df = df[df["quarter"] == 4]
    df = df[df["level"] == level]
    return df[["geocod", "year", "value"]]


def variant_table(year: int = YEAR) -> pd.DataFrame:
    """Municipal inputs for `year` under every sensitivity variant (wide)."""
    out = _annual(config.INCOME, None).rename(columns={"value": "y_net_hh"})
    for name, ind, cat in (("y_gross_hh", config.INCOME_GROSS_HH, None),
                           ("y_net_tp", config.INCOME_NET_TP, None),
                           ("p_total", config.PRICE, "Total"),
                           ("p_new", config.PRICE, "New"),
                           ("p_existing", config.PRICE, "Existing"),
                           ("rent", config.RENT, None)):
        out = out.merge(_annual(ind, cat).rename(columns={"value": name}), on=["geocod", "year"], how="outer")
    return out[out["year"] == year].reset_index(drop=True)


# ----------------------------------------------------------------- sensitivity
def sensitivity(v: pd.DataFrame) -> pd.DataFrame:
    """Rank/quintile robustness of I2 (A=80) under alternative inputs vs the headline
    (net-of-IRS tax-household income, Total price). Area A only rescales I2, so it cannot change ranks."""
    head = 80 * v["p_total"] / v["y_net_hh"]
    rows = []
    for label, num, den in (("income: gross per tax household", "p_total", "y_gross_hh"),
                            ("income: net per taxpayer", "p_total", "y_net_tp"),
                            ("price: new dwellings only", "p_new", "y_net_hh"),
                            ("price: existing dwellings only", "p_existing", "y_net_hh")):
        alt = 80 * v[num] / v[den]
        m = pd.concat([head, alt], axis=1, keys=["h", "a"]).dropna()
        q = lambda s: pd.qcut(s.rank(method="first"), 5, labels=False)
        rows.append({"variant": label, "n_both": len(m),
                     "spearman_vs_headline": stats.spearmanr(m["h"], m["a"])[0],
                     "median_ratio_alt_over_headline": float((m["a"] / m["h"]).median()),
                     "share_changing_quintile": float((q(m["h"]) != q(m["a"])).mean())})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- NUTS II tests
def nuts2_tests(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Kruskal-Wallis of municipal metrics across NUTS II (epsilon^2 effect size). Indicative only."""
    rows = []
    for c in cols:
        groups = [g[c].dropna().values for _, g in df.groupby("nuts2") if g[c].notna().sum() >= 3]
        h, p = stats.kruskal(*groups)
        n = sum(len(g) for g in groups)
        rows.append({"metric": c, "n_municipalities": n, "n_groups": len(groups), "H": h, "p_value": p,
                     "epsilon_sq": h / (n - 1)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- spatial
def continent_weights():
    from libpysal import weights
    g = gpd.read_file(next(caop.CAOP_DIR.glob("x_*/Continente_CAOP2025.gpkg")),
                      layer="cont_municipios", columns=["dtmn"]).rename(columns={"dtmn": "dico"})
    w = weights.Queen.from_dataframe(g, ids=g["dico"].tolist(), use_index=False)
    return g, w


def morans(df: pd.DataFrame, col: str, w) -> dict:
    from esda.moran import Moran, Moran_Local
    from libpysal.weights import w_subset
    d = df.dropna(subset=[col]).drop_duplicates("dico").set_index("dico")
    ids = [i for i in w.id_order if i in d.index]
    ws = w_subset(w, ids)
    ws.transform = "r"
    y = d.loc[ids, col].values
    np.random.seed(SEED)
    mi = Moran(y, ws, permutations=999)
    li = Moran_Local(y, ws, permutations=999, seed=SEED)
    sig = li.p_sim < 0.05
    quad = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}
    counts = pd.Series([quad[q] for q in li.q[sig]]).value_counts().to_dict()
    return {"variable": col, "n": len(ids), "islands_after_subset": len(ws.islands),
            "morans_I": float(mi.I), "p_sim": float(mi.p_sim), "lisa_significant_5pct": counts}


# ------------------------------------------------------------------------- clustering
def cluster_exploration(df: pd.DataFrame, feats: list[str], ks=range(2, 9)) -> tuple[pd.DataFrame, pd.DataFrame]:
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score, silhouette_score
    d = df.dropna(subset=feats).copy()
    X = (d[feats] - d[feats].mean()) / d[feats].std(ddof=0)
    rng = np.random.default_rng(SEED)
    rows = []
    for k in ks:
        km = KMeans(k, n_init=20, random_state=SEED).fit(X)
        sil = silhouette_score(X, km.labels_)
        aris = []
        for _ in range(30):  # stability on 80% subsamples
            idx = rng.choice(len(X), int(0.8 * len(X)), replace=False)
            sub = KMeans(k, n_init=10, random_state=int(rng.integers(1e6))).fit(X.iloc[idx])
            aris.append(adjusted_rand_score(km.labels_[idx], sub.labels_))
        rows.append({"k": k, "silhouette": sil, "stability_ARI_mean": float(np.mean(aris))})
    sel = pd.DataFrame(rows)
    return sel, d


def profile_clusters(d: pd.DataFrame, feats: list[str], k: int) -> pd.DataFrame:
    from sklearn.cluster import KMeans
    X = (d[feats] - d[feats].mean()) / d[feats].std(ddof=0)
    d = d.copy()
    d["cluster"] = KMeans(k, n_init=20, random_state=SEED).fit_predict(X)
    prof = d.groupby("cluster").agg(n=("dico", "size"), **{f"median_{f}": (f, "median") for f in feats})
    prof["share_by_nuts2"] = d.groupby("cluster")["nuts2"].agg(lambda s: s.value_counts(normalize=True).round(2).head(3).to_dict())
    return prof.reset_index()


# --------------------------------------------------------------------- rent-gap profile
def rent_gap_profile(v: pd.DataFrame, key: pd.DataFrame) -> dict:
    m = v.merge(key[["geocod", "nuts2"]], on="geocod")
    m["has_rent"] = m["rent"].notna()
    m["ln_price"] = np.log(m["p_total"])
    m["ln_income"] = np.log(m["y_net_hh"])
    out = {"n": len(m), "with_rent": int(m["has_rent"].sum())}
    for c in ("ln_price", "ln_income"):
        a, b = m.loc[m["has_rent"], c].dropna(), m.loc[~m["has_rent"], c].dropna()
        u = stats.mannwhitneyu(a, b)
        out[c] = {"median_with_rent": float(np.exp(a.median())), "median_without_rent": float(np.exp(b.median())),
                  "n_without": len(b), "mannwhitney_p": float(u.pvalue)}
    out["share_with_rent_by_nuts2"] = m.groupby("nuts2")["has_rent"].mean().round(2).to_dict()
    return out


# ------------------------------------------------------------------ payment scenario (I5)
BPSTAT_DATASET = "https://bpstat.bportugal.pt/data/v1/domains/186/datasets/6a83b46f5911d1b086a2891746a2fd9a?lang=EN"
BPSTAT_SERIES = 12710738  # fixed-rate new housing loans, 50th percentile, % (licence not verified)


def bpstat_annual_rate() -> pd.Series:
    """Annual mean of the monthly series (flat index decoded from the JSON-stat-like payload)."""
    req = urllib.request.Request(BPSTAT_DATASET, headers={"User-Agent": ine.USER_AGENT})
    d = json.load(urllib.request.urlopen(req, timeout=90))
    dims = d["dimension"]
    order = d["id"]
    sizes = dict(zip(order, d["size"]))
    ser = next(s for s in d["extension"]["series"] if s["id"] == BPSTAT_SERIES)
    cats = {str(x["dimension_id"]): x["category_id"] for x in ser["dimension_category"]}
    pos = {}
    for dim_id in order:
        if dim_id == "reference_date":
            continue
        idx = dims[dim_id]["category"]["index"]
        idx = {str(c): i for i, c in enumerate(idx)} if isinstance(idx, list) else {str(c): i for c, i in idx.items()}
        pos[dim_id] = idx[str(cats[dim_id])]
    flat = 0
    for dim_id in order:
        flat = flat * sizes[dim_id] + (pos[dim_id] if dim_id != "reference_date" else 0)
    dates = dims["reference_date"]["category"]["index"]
    dates = dates if isinstance(dates, list) else sorted(dates, key=dates.get)
    vals = {pd.Timestamp(dt): d["value"].get(str(flat + j)) for j, dt in enumerate(dates)}
    s = pd.Series(vals, dtype=float).dropna()
    return s.groupby(s.index.year).mean()


def monthly_payment(principal: pd.Series, annual_rate_pct: float, years: int = 30) -> pd.Series:
    r = annual_rate_pct / 100 / 12
    n = years * 12
    return principal * (r / (1 - (1 + r) ** -n)) if r > 0 else principal / n


def payment_to_income(price_m2: pd.Series, income_hh: pd.Series, rate_pct: float,
                      area: float = 80, ltv: float = 0.8, years: int = 30) -> pd.Series:
    """I5: monthly payment on a loan of ltv*area*price over `years` / monthly median household income.
    A scenario, not mortgage eligibility (no DSTI test, deposit, taxes, insurance, variable rates)."""
    return monthly_payment(ltv * area * price_m2, rate_pct, years) / (income_hh.where(income_hh > 0) / 12)


# ------------------------------------------------------------------------------ runner
def _md(df: pd.DataFrame) -> str:
    fence = "`" * 3
    return fence + "\n" + df.round(3).to_string(index=False) + "\n" + fence


def main(with_bpstat: bool = False) -> None:
    panel = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet")
    key = pd.read_parquet(config.PROCESSED / "geo_key.parquet")
    d = panel[panel["year"] == YEAR].merge(key[["geocod", "dico", "nuts2", "nuts3"]], on="geocod")
    v = variant_table()
    out = ["# Phase 4 - exploratory results (generated, preliminary)", "",
           "Descriptive/exploratory. Municipal medians carry no published sampling error; p-values are indicative.", ""]

    sens = sensitivity(v)
    out += ["## 1. Sensitivity of I2 (2024, A=80 m2) to alternative inputs", _md(sens),
            "Area A rescales I2 linearly, so it changes levels but never ranks.", ""]

    kw = nuts2_tests(d, ["i2_years_80m2", "i6_price_vs_income_real"])
    out += ["## 2. Kruskal-Wallis across NUTS II (municipalities, 2024)", _md(kw), ""]

    g, w = continent_weights()
    out += ["## 3. Spatial autocorrelation (mainland municipalities, Queen contiguity, 999 permutations)"]
    d["ln_i2"] = np.log(d["i2_years_80m2"])
    moran_results = []
    for col in ("ln_i2", "i6_price_vs_income_real"):
        r = morans(d, col, w)
        moran_results.append(r)
        out.append(f"- {r}")
    out.append("")

    feats = ["ln_price", "ln_income", "i6_price_vs_income_real"]
    d["ln_price"], d["ln_income"] = np.log(d["price_m2"]), np.log(d["income_hh"])
    sel, dc = cluster_exploration(d, feats)
    best = int(sel.loc[sel["silhouette"].idxmax(), "k"])
    prof = profile_clusters(dc, feats, best)
    out += ["## 4. Clustering exploration (k-means, standardised ln price, ln income, I6 price; 2024)",
            _md(sel), f"Best silhouette at k={best}. Silhouette < 0.25 would indicate weak structure; "
            "interpret as a descriptive typology, not discrete types.", _md(prof), ""]

    gap = rent_gap_profile(v, key)
    out += ["## 5. Who is missing a rent value (2024)", "```", json.dumps(gap, indent=1, ensure_ascii=False), "```", ""]

    if with_bpstat:
        # Local, unpublished analysis only: BPstat reuse terms were not found, so nothing derived from
        # BPstat is written to tracked files (see docs/audit_consolidation.md).
        rates = bpstat_annual_rate()
        rows = []
        for y in range(2019, 2025):
            dy = panel[panel["year"] == y]
            i5 = payment_to_income(dy["price_m2"], dy["income_hh"], float(rates[y]))
            rows.append({"year": y, "rate_pct": float(rates[y]), "n": int(i5.notna().sum()),
                         "median_i5": float(i5.median())})
        # Decomposition: rate effect vs price/income effect on the median municipal I5, 2019 -> 2024
        a, b = panel[panel["year"] == 2019], panel[panel["year"] == 2024]
        cf = []
        for dlab, dd in (("2019 prices/incomes", a), ("2024 prices/incomes", b)):
            for rlab, y in (("2019 rate", 2019), ("2024 rate", 2024)):
                i5 = payment_to_income(dd["price_m2"], dd["income_hh"], float(rates[y]))
                cf.append({"data": dlab, "rate": rlab, "median_i5": float(i5.median())})
        local_out = ["## 6. Payment scenario I5 (80 m2, LTV 80%, 30 years, BPstat series 12710738, annual mean of monthly values)",
                _md(pd.DataFrame(rows)),
                "Median = unweighted median across municipalities (a constructed summary, not an official regional statistic). "
                "Series 12710738: interest rate (percentile 50) on new loans for permanent housing, fixed rate, in percent; "
                "the metadata read does not say whether it is nominal or APR-like (TAEG); the annual value is an unweighted "
                "mean of monthly values.", "",
                "Counterfactual (rate effect vs. price/income effect on the median municipal I5):", _md(pd.DataFrame(cf)),
                "I5 = monthly payment / monthly median household income. Scenario only: not mortgage eligibility "
                "(no DSTI test, deposit, taxes, insurance or variable rates). BPstat licence not verified: not in the dashboard.", ""]
        local_dir = config.REPORTS / "local"
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "phase4_bpstat.md").write_text("\n".join(local_out), encoding="utf-8")
    else:
        out += ["## 6. Payment scenario", "Excluded from the published report: BPstat reuse terms were not found. "
                "The code remains; run `python -m housing_pt.phase4 --with-bpstat` for a local analysis written to "
                "reports/local/ (git-ignored).", ""]

    text = "\n".join(out)
    (config.REPORTS / "phase4_results.md").write_text(text, encoding="utf-8")
    sens.to_csv(config.REPORTS / "phase4_sensitivity.csv", index=False)
    prof.to_csv(config.REPORTS / "phase4_cluster_profiles.csv", index=False)
    metrics_json = {
        "moran": [{k: r[k] for k in ("variable", "n", "morans_I", "p_sim")} for r in moran_results],
        "kruskal_nuts2": kw.round(6).to_dict(orient="records"),
        "clustering": sel.round(4).to_dict(orient="records"),
        "sensitivity": sens.round(4).to_dict(orient="records"),
        "rent_gap": {k: gap[k] for k in ("n", "with_rent")},
    }
    (config.REPORTS / "phase4_metrics.json").write_text(json.dumps(metrics_json, indent=1, ensure_ascii=False),
                                                         encoding="utf-8")
    print(text)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-bpstat", action="store_true",
                    help="local-only payment scenario (BPstat reuse terms not verified; output is git-ignored)")
    main(ap.parse_args().with_bpstat)
