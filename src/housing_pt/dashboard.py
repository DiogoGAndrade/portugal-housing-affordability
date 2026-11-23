"""Phase 5: build a self-contained static dashboard (site/index.html, no external requests).

Data embedded: municipal and NUTS III medians (INE) for 2019-2025, CPI, simplified CAOP 2025
geometry pre-projected to SVG paths. Metrics are computed in the browser from the same formulas
as housing_pt.metrics (verified 2026-11-22: 2024 municipal sums/counts of I1-I4, I6 and real price
identical to the parquet panel; see tests/test_dashboard.py for the embedded-data check). BPstat-based scenario (I5) is intentionally NOT included until its licence is verified.

Run:  python -m housing_pt.dashboard
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

from . import analysis, config

SITE = config.ROOT / "site"
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
YEARS = list(range(2019, 2026))
PANELS = {"mainland": (380, 760), "acores": (250, 150), "madeira": (250, 110)}
GROUP = {"continente": "mainland", "acores": "acores", "madeira": "madeira"}


def _path(geom, tf) -> str:
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        if not isinstance(p, Polygon) or p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = [tf(x, y) for x, y in ring.coords]
            out.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
    return "".join(out)


def _transforms(gdf: gpd.GeoDataFrame) -> dict:
    tfs = {}
    for grp, (w, h) in PANELS.items():
        sub = gdf[gdf["group"] == grp]
        if sub.empty:  # e.g. synthetic test geometry without island groups
            continue
        x0, y0, x1, y1 = sub.total_bounds
        lat0 = math.radians((y0 + y1) / 2)
        k = math.cos(lat0)
        dx, dy = (x1 - x0) * k, (y1 - y0)
        s = min((w - 8) / dx, (h - 8) / dy)
        ox, oy = (w - dx * s) / 2, (h - dy * s) / 2
        tfs[grp] = (lambda x, y, x0=x0, y1=y1, k=k, s=s, ox=ox, oy=oy: ((x - x0) * k * s + ox, (y1 - y) * s + oy))
    return tfs


def _series(df: pd.DataFrame, geocod: str) -> dict:
    d = df[df["geocod"] == geocod].set_index("year")
    f = lambda c: [None if pd.isna(d[c].get(y, np.nan)) else float(d[c].get(y)) for y in YEARS]
    return {"P": f("price_m2"), "Y": f("income_hh"), "R": f("rent_m2")}


def build(out_dir: Path = SITE, geometry: gpd.GeoDataFrame | None = None) -> Path:
    muni = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet")
    n3 = pd.read_parquet(config.PROCESSED / "panel_nuts3.parquet")
    key = pd.read_parquet(config.PROCESSED / "geo_key.parquet")
    geom = geometry if geometry is not None else analysis.load_geometry()
    g = geom.merge(key[["dico", "geocod", "municipality", "nuts3_code", "nuts3", "nuts2"]], on="dico")
    g["group"] = g["region"].map(GROUP)
    tfs = _transforms(g)

    units = []
    for r in g.itertuples():
        units.append({"id": r.geocod, "name": r.municipality, "nuts3": r.nuts3, "nuts2": r.nuts2, "group": r.group,
                      "d": _path(r.geometry, tfs[r.group]), **_series(muni, r.geocod)})
    dis = g.dissolve(by=["nuts3_code", "nuts3", "nuts2", "group"], as_index=False)
    regions = []
    for r in dis.itertuples():
        regions.append({"id": r.nuts3_code, "name": r.nuts3, "nuts2": r.nuts2, "nuts3": r.nuts3, "group": r.group,
                        "d": _path(r.geometry, tfs[r.group]), **_series(n3, r.nuts3_code)})

    payload = json.loads((config.RAW / f"ine_{config.CPI.code}_data.json").read_bytes())[0]["Dados"]
    cpi_by_year = {int(y): float(next(r["valor"] for r in rows if r["geocod"] == "PT" and r.get("dim_3_t") == "Total"))
                   for y, rows in payload.items() if y.isdigit() and int(y) in YEARS}
    manifest = json.loads((config.MANIFESTS / "ine_manifest.json").read_text(encoding="utf-8"))
    data = {"years": YEARS, "cpi": [cpi_by_year[y] for y in YEARS], "municipality": units, "nuts3": regions,
            "panels": {k: list(v) for k, v in PANELS.items()},
            "sources": [{"code": m["code"], "title": m["title"], "updated": m["ine_last_update"],
                         "retrieved": m["retrieved_at"][:10], "first": m["first_period"], "last": m["last_period"]}
                        for m in manifest]}
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False,
                                                                                       separators=(",", ":")))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_bytes(html.encode("utf-8"))  # bytes, LF: the CSP hashes below must match what is served
    (out_dir / "_headers").write_bytes(security_headers(html).encode("utf-8"))
    return out


def _sha256_b64(text: str) -> str:
    return base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")


def security_headers(html: str) -> str:
    """Cloudflare Pages `_headers` file: strict CSP pinned to the page's single inline script and style
    (by SHA-256), no connections, no frames, and the usual hardening headers. The page has no inline
    style attributes and no external resources, so no 'unsafe-inline' is needed."""
    styles = re.findall(r"<style>(.*?)</style>", html, re.S)
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    if len(styles) != 1 or len(scripts) != 1:
        raise ValueError("expected exactly one inline <style> and one inline <script>")
    csp = ("default-src 'none'; "
           f"script-src 'sha256-{_sha256_b64(scripts[0])}'; "
           f"style-src 'sha256-{_sha256_b64(styles[0])}'; "
           "img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
    return "\n".join([
        "/*",
        f"  Content-Security-Policy: {csp}",
        "  X-Content-Type-Options: nosniff",
        "  X-Frame-Options: DENY",
        "  Referrer-Policy: no-referrer",
        "  Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), microphone=(), payment=(), usb=()",
        "  Cross-Origin-Opener-Policy: same-origin",
        "  Cross-Origin-Resource-Policy: same-origin",
        "  Strict-Transport-Security: max-age=31536000",
        "  Cache-Control: public, max-age=0, must-revalidate",
        ""])


if __name__ == "__main__":
    p = build()
    print(p, f"{p.stat().st_size/1e6:.2f} MB")
