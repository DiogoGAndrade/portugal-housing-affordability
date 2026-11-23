"""Phase 3 descriptive outputs: NUTS III summary tables and static maps.

Descriptive only: no rankings, no composite index, no inference. Every figure states its
metric, year, unit and the number of municipalities with data.
Run:  python -m housing_pt.analysis
"""
from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import caop, config

FIG = config.REPORTS / "figures"
CREDIT = ("Dados: INE (CC BY 4.0), cálculos próprios. "
          "Informação geográfica cedida pela Direção-Geral do Território (CAOP 2025).")
REGION_LAYERS = {
    "continente": ("Continente_CAOP2025.gpkg", "cont_municipios"),
    "acores_oriental": ("ArqAcores_GCentral_GOriental_CAOP2025.gpkg", "raa_cen_ori_municipios"),
    "acores_ocidental": ("ArqAcores_GOcidental_CAOP2025.gpkg", "raa_oci_municipios"),
    "madeira": ("ArqMadeira_CAOP2025.gpkg", "ram_municipios"),
}


def load_geometry() -> gpd.GeoDataFrame:
    parts = []
    for region, (fname, layer) in REGION_LAYERS.items():
        path = next(caop.CAOP_DIR.glob(f"x_*/{fname}"))
        g = gpd.read_file(path, layer=layer, columns=["dtmn"]).to_crs(4326)
        g["geometry"] = g.geometry.simplify(0.002, preserve_topology=True)
        g["region"] = region.split("_")[0]
        parts.append(g.rename(columns={"dtmn": "dico"}))
    out = pd.concat(parts, ignore_index=True)
    if len(out) != 308 or out["dico"].duplicated().any():
        raise ValueError("CAOP municipal geometry incomplete")
    return gpd.GeoDataFrame(out, crs=4326)


def nuts3_table(p3: pd.DataFrame, key: pd.DataFrame) -> pd.DataFrame:
    names = key.drop_duplicates("nuts3_code").set_index("nuts3_code")[["nuts3", "nuts2"]]
    cols = ["income_hh", "price_m2", "rent_m2", "i2_years_80m2", "i3_rent_share_80m2",
            "i4_rent_over_price", "i6_price_vs_income_real", "i6_rent_vs_income_real"]
    rows = []
    for y in (2020, 2024):
        d = p3[p3["year"] == y].set_index("geocod")[cols].add_suffix(f"_{y}")
        rows.append(d)
    t = pd.concat(rows, axis=1).join(names).reset_index().rename(columns={"index": "nuts3_code",
                                                                         "geocod": "nuts3_code"})
    keep = ["nuts3_code", "nuts3", "nuts2", "income_hh_2024", "price_m2_2024", "rent_m2_2024",
            "i2_years_80m2_2020", "i2_years_80m2_2024", "i3_rent_share_80m2_2020",
            "i3_rent_share_80m2_2024", "i4_rent_over_price_2024",
            "i6_price_vs_income_real_2024", "i6_rent_vs_income_real_2024"]
    return t[keep].sort_values(["nuts2", "nuts3"]).reset_index(drop=True)


def _draw(ax, gdf, col, cmap, norm, title=None):
    gdf.plot(ax=ax, color="#d9d9d9", linewidth=0.15, edgecolor="white")  # no data: grey
    g = gdf.dropna(subset=[col])
    g.plot(ax=ax, column=col, cmap=cmap, norm=norm, linewidth=0.15, edgecolor="white")
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=8)


def map_metric(gdf: gpd.GeoDataFrame, col: str, title: str, unit: str, fname: str,
               cmap: str = "YlOrRd", center: float | None = None, n_valid_label: str = "") -> None:
    vals = gdf[col].dropna()
    lo, hi = np.nanpercentile(vals, [2, 98])
    norm = (matplotlib.colors.TwoSlopeNorm(vcenter=center, vmin=min(lo, center - 1e-9), vmax=max(hi, center + 1e-9))
            if center is not None else matplotlib.colors.Normalize(lo, hi))
    fig = plt.figure(figsize=(7.5, 9))
    ax = fig.add_axes([0.02, 0.14, 0.7, 0.78])
    _draw(ax, gdf[gdf["region"] == "continente"], col, cmap, norm)
    for i, (reg, lab) in enumerate((("acores", "Açores"), ("madeira", "Madeira"))):
        a = fig.add_axes([0.62, 0.55 - i * 0.22, 0.36, 0.2])
        _draw(a, gdf[gdf["region"] == reg], col, cmap, norm, lab)
    cax = fig.add_axes([0.1, 0.105, 0.5, 0.015])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_label(unit, fontsize=7)
    cb.ax.tick_params(labelsize=7)
    fig.suptitle(title, fontsize=11, y=0.96)
    fig.text(0.02, 0.06, f"Cinzento = sem dado publicado/suprimido. {n_valid_label}\n{CREDIT}", fontsize=6.5, va="top")
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / fname, dpi=150)
    plt.close(fig)


def main() -> None:
    p = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet")
    p3 = pd.read_parquet(config.PROCESSED / "panel_nuts3.parquet")
    key = pd.read_parquet(config.PROCESSED / "geo_key.parquet")

    t = nuts3_table(p3, key)
    t.to_csv(config.REPORTS / "nuts3_summary.csv", index=False, encoding="utf-8")

    g = load_geometry()
    d24 = p[p["year"] == 2024].merge(key[["geocod", "dico"]], on="geocod")
    d24 = g.merge(d24[["dico", "i2_years_80m2", "i6_price_vs_income_real"]], on="dico", how="left")
    n = int(d24["i2_years_80m2"].notna().sum())
    map_metric(d24, "i2_years_80m2",
               "Anos de rendimento mediano por agregado fiscal\npara um alojamento de 80 m² (2024)",
               "anos de rendimento (I2, área de referência 80 m²)", "i2_years_80m2_2024.png",
               n_valid_label=f"Municípios com dado: {n}/308. Rendimento declarado após IRS ≠ rendimento disponível.")
    n = int(d24["i6_price_vs_income_real"].notna().sum())
    map_metric(d24, "i6_price_vs_income_real",
               "Preço (€/m²) vs. rendimento: crescimento real relativo, 2019→2024",
               "ln(preço₂₀₂₄/preço₂₀₁₉) − ln(rend.₂₀₂₄/rend.₂₀₁₉); >0 = preço cresceu mais", "i6_price_vs_income_2019_2024.png",
               cmap="RdBu_r", center=0.0,
               n_valid_label=f"Municípios com dado: {n}/308. Valores deflacionados pelo IPC nacional.")
    print(t.round(2).to_string())


if __name__ == "__main__":
    main()
