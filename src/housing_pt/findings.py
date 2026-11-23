"""Generate the README 'main results' block from the processed panels, so published numbers cannot drift
from the data. Descriptive statements only: no causal language, no rankings (only the two extremes).

Run:  python -m housing_pt.findings            # writes reports/findings.md and refreshes README block
      python -m housing_pt.findings --check    # fails if the README block is stale
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from . import config

START, END = "<!-- findings:start -->", "<!-- findings:end -->"


def _n(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def compute(n3: pd.DataFrame, muni: pd.DataFrame, key: pd.DataFrame, p4: dict) -> dict:
    names = key.drop_duplicates("nuts3_code").set_index("nuts3_code")["nuts3"]
    at = lambda y, c: n3[n3["year"] == y].set_index("geocod")[c].dropna()
    f: dict = {}
    m24 = muni[muni["year"] == 2024]
    f["coverage"] = {"n_muni": int(muni["geocod"].nunique()), "price": int(m24["price_m2"].notna().sum()),
                     "income": int(m24["income_hh"].notna().sum()),
                     "both": int((m24["price_m2"].notna() & m24["income_hh"].notna()).sum()),
                     "rent": int(m24["rent_m2"].notna().sum()), "n_nuts3": int(n3["geocod"].nunique())}
    i2 = at(2024, "i2_years_80m2")
    f["i2_2024"] = {"n": len(i2), "min": (names[i2.idxmin()], float(i2.min())), "max": (names[i2.idxmax()], float(i2.max()))}
    d = (at(2024, "i2_years_80m2") - at(2020, "i2_years_80m2")).dropna()
    f["i2_change"] = {"n": len(d), "up": int((d > 0).sum()), "down": int((d < 0).sum()),
                      "max": (names[d.idxmax()], float(d.max())), "min": (names[d.idxmin()], float(d.min()))}
    p = at(2024, "i6_price_vs_income_real")
    f["i6_price"] = {"n": len(p), "pos": int((p > 0).sum()), "max": (names[p.idxmax()], float(p.max())),
                     "min": (names[p.idxmin()], float(p.min()))}
    r = at(2024, "i6_rent_vs_income_real")
    f["i6_rent"] = {"n": len(r), "pos": int((r > 0).sum())}
    mo = {m["variable"]: m for m in p4["moran"]}
    kw = {k["metric"]: k for k in p4["kruskal_nuts2"]}
    f["structure"] = {"moran_i2": mo["ln_i2"]["morans_I"], "moran_n": mo["ln_i2"]["n"],
                      "moran_i6": mo["i6_price_vs_income_real"]["morans_I"],
                      "eps_i2": kw["i2_years_80m2"]["epsilon_sq"]}
    s = {x["variant"]: x for x in p4["sensitivity"]}
    f["robust"] = {"gross": s["income: gross per tax household"]["spearman_vs_headline"],
                   "taxpayer": s["income: net per taxpayer"]["spearman_vs_headline"],
                   "existing": s["price: existing dwellings only"]["spearman_vs_headline"],
                   "new": s["price: new dwellings only"]["spearman_vs_headline"],
                   "new_quintile": s["price: new dwellings only"]["share_changing_quintile"],
                   "new_n": int(s["price: new dwellings only"]["n_both"])}
    return f


def render(f: dict) -> str:
    c, a, ch, p, rr, st, ro = (f[k] for k in ("coverage", "i2_2024", "i2_change", "i6_price", "i6_rent", "structure", "robust"))
    lines = [
        f"- **Cobertura (2024).** Há preço e rendimento em {c['both']} dos {c['n_muni']} municípios "
        f"(preço em {c['price']}, rendimento em {c['income']}); a renda de novos contratos só está publicada em {c['rent']}. "
        f"Nas {c['n_nuts3']} sub-regiões NUTS III (valores oficiais do INE) todas as séries estão completas.",
        f"- **Níveis (I2, 80 m², NUTS III, 2024).** Entre as {a['n']} sub-regiões, os extremos são {a['min'][0]} "
        f"({_n(a['min'][1])} anos de rendimento mediano) e {a['max'][0]} ({_n(a['max'][1])}); são dois valores extremos, não um ranking.",
        f"- **Variação 2020→2024 (I2, NUTS III).** Aumentou em {ch['up']} e diminuiu em {ch['down']} das {ch['n']} sub-regiões; "
        f"maior aumento em {ch['max'][0]} (+{_n(ch['max'][1])} anos) e maior descida em {ch['min'][0]} (−{_n(abs(ch['min'][1]))} anos).",
        f"- **Preço vs. rendimento 2019→2024 (I6, NUTS III).** Em {p['pos']} das {p['n']} sub-regiões o preço mediano cresceu mais do que o "
        f"rendimento mediano (máximo {_n(p['max'][1], 2)} em {p['max'][0]}; mínimo −{_n(abs(p['min'][1]), 2)} em {p['min'][0]}). "
        f"Para a renda de novos contratos (desde 2020) o mesmo sinal ocorre em {rr['pos']} de {rr['n']}.",
        f"- **Estrutura regional e espacial.** O I de Moran de I2 (município, continente, n={st['moran_n']}) é {_n(st['moran_i2'], 2)} e o da divergência "
        f"preço–rendimento {_n(st['moran_i6'], 2)}; a região NUTS II associa-se a uma parte grande da variação de I2 (ε² = {_n(st['eps_i2'], 2)}). "
        f"É descrição de padrões, não explicação.",
        f"- **Robustez.** A ordenação municipal de I2 mantém-se com outro rendimento (ρ de Spearman {_n(ro['gross'], 3)} com rendimento bruto e "
        f"{_n(ro['taxpayer'], 3)} por sujeito passivo), mas é sensível à categoria do alojamento: só com alojamentos novos (n={ro['new_n']}) "
        f"ρ = {_n(ro['new'], 2)} e {round(100 * ro['new_quintile'])} % dos municípios mudam de quintil.",
    ]
    return "\n".join(lines)


def replace_block(readme: str, block: str) -> str:
    a, b = readme.index(START) + len(START), readme.index(END)
    return readme[:a] + "\n" + block + "\n" + readme[b:]


def generate() -> str:
    n3 = pd.read_parquet(config.PROCESSED / "panel_nuts3.parquet")
    muni = pd.read_parquet(config.PROCESSED / "panel_municipality.parquet")
    key = pd.read_parquet(config.PROCESSED / "geo_key.parquet")
    p4 = json.loads((config.REPORTS / "phase4_metrics.json").read_text(encoding="utf-8"))
    return render(compute(n3, muni, key, p4))


def main(check: bool = False) -> int:
    block = generate()
    readme_path = config.ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    new = replace_block(readme, block)
    if check:
        if new.replace("\r\n", "\n") != readme.replace("\r\n", "\n"):
            print("README findings block is stale: run python -m housing_pt.findings")
            return 1
        print("README findings block is current")
        return 0
    (config.REPORTS / "findings.md").write_text(block + "\n", encoding="utf-8")
    readme_path.write_text(new, encoding="utf-8")
    print(block)
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
