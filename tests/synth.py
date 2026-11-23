"""Synthetic INE-shaped fixtures (invented numbers, NOT INE data) with hand-computable values.

Design goals: exercise the same code paths as the real data without licensed files or network:
 * quarterly series with Q3 and Q4 values that differ (annual value must be the Q4 one);
 * category dimension (Total/New/Existing) whose values differ (Total must be selected);
 * suppressed observations (no `valor` key) that must stay missing, never zero-filled;
 * NUTS III rows whose values differ from the mean of their municipalities (official values must be used);
 * a CPI decoy category and a legacy NUTS version whose municipal geocod prefixes differ (join on `dico`).
"""
from __future__ import annotations

import json
from pathlib import Path

# geocod -> (name, dico)
MUNI = {"11A0101": "Alfa Um", "11A0102": "Alfa Dois", "11B0201": "Beta Um", "11B0202": "Beta Dois"}
NUTS3 = {"11A": "Regiao Alfa", "11B": "Regiao Beta"}
NUTS2 = {"11": "Norte"}
LEGACY_PREFIX = {"11A": "16X", "11B": "17Y"}   # NUTS-2013-like prefixes for the legacy vintage
CPI_TOTAL = {2019: 90.0, 2020: 92.0, 2021: 94.0, 2022: 96.0, 2023: 98.0, 2024: 99.0, 2025: 100.0}

# ---- hand-designed values -------------------------------------------------------------------
def income(g: str, y: int):
    return {"11A0101": 10000 + 500 * (y - 2018), "11A0102": 8000,
            "11B0201": None if y == 2019 else 12000, "11B0202": 9000,
            "11A": 9500, "11B": 10500}.get(g)


def price_q4(g: str, y: int, cat: str):
    base = {"11A0101": 1000 * (1 + 0.1 * (y - 2019)), "11A0102": 500.0, "11B0201": 2000.0,
            "11B0202": None if y == 2021 else 1500.0, "11A": 850.0, "11B": 1900.0}.get(g)
    if base is None:
        return None
    return {"Total": base, "New": base * 1.2, "Existing": base * 0.9}[cat]


def rent(g: str, y: int):
    return {"11A0101": 5.0 + 0.5 * (y - 2020), "11A0102": None, "11B0201": 10.0, "11B0202": 8.0,
            "11A": 5.5, "11B": 9.0}.get(g)


# ---- JSON writers ---------------------------------------------------------------------------
def _row(geocod, name, value, cat=None):
    r = {"geocod": geocod, "geodsg": name}
    if cat is not None:
        r["dim_3"] = cat[:1]
        r["dim_3_t"] = cat
    if value is not None:                      # suppressed observations carry no `valor`
        r["valor"] = str(value)
        r["ind_string"] = str(value).replace(".", ",")
    return r


def _all_units():
    return {**MUNI, **NUTS3, **NUTS2}


def _write(raw: Path, code: str, title: str, periods: dict, first: str, last: str, unit: str, periodic: str):
    ok = {"Verdadeiro": [{"Msg": "OK"}]}
    data = [{"IndicadorCod": code, "IndicadorDsg": title, "DataUltimoAtualizacao": "2026-01-01",
             "Dados": periods, "Sucesso": ok}]
    meta = {"IndicadorCod": code, "IndicadorNome": title, "Periodic": periodic, "PrimeiroPeriodo": first,
            "UltimoPeriodo": last, "UnidadeMedida": unit, "DataUltimaAtualizacao": "2026-01-01", "Nota": None,
            "Sucesso": ok}
    (raw / f"ine_{code}_data.json").write_text(json.dumps(data), encoding="utf-8")
    (raw / f"ine_{code}_meta.json").write_text(json.dumps(meta), encoding="utf-8")


def write_raw(raw: Path) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    units = _all_units()
    # income 0012741: annual 2018-2024 (NUTS II row carries only the name used by the geographic key)
    _write(raw, "0012741", "SYNTHETIC median income per tax household",
           {str(y): [_row(g, n, income(g, y)) for g, n in units.items()] for y in range(2018, 2025)},
           "2018", "2024", "EUR", "Annual")
    # price 0012234: quarterly Q3+Q4 2019-2025, three categories. Q3 differs from Q4 on purpose, and the
    # suppressed Q4 of Beta Dois/2021 has a Q3 value that must NOT be used as a fallback.
    ordinal = {3: "3rd", 4: "4th"}
    periods = {}
    for y in range(2019, 2026):
        for q in (3, 4):
            rows = []
            for g, n in units.items():
                if g in NUTS2:
                    continue
                for cat in ("Total", "New", "Existing"):
                    v = price_q4(g, y, cat)
                    if q == 3:
                        v = (v - 50.0) if v is not None else (1450.0 if cat == "Total" else None)
                    rows.append(_row(g, n, v, cat))
            periods[f"{ordinal[q]} Quarter {y}"] = rows
    _write(raw, "0012234", "SYNTHETIC median sales value last 12 months", periods,
           "3rd Quarter 2019", "4th Quarter 2025", "EUR/m2", "Quarterly")
    # rent 0014698: annual 2020-2025
    _write(raw, "0014698", "SYNTHETIC median rent of new leases",
           {str(y): [_row(g, n, rent(g, y)) for g, n in units.items() if g not in NUTS2] for y in range(2020, 2026)},
           "2020", "2025", "EUR/m2/month", "Annual")
    # CPI 0014642: Total (used) and a decoy category (must never be used)
    cpi = {}
    for y, v in CPI_TOTAL.items():
        cpi[str(y)] = [_row("PT", "Portugal", v, "Total"), _row("PT", "Portugal", 50.0, "Total excluding housing"),
                       _row("1", "Continent", v, "Total")]
    _write(raw, "0014642", "SYNTHETIC CPI base 2025", cpi, "2019", "2025", "index", "Annual")
    # legacy vintages (different geocod prefixes; same dico)
    legacy = {f"{LEGACY_PREFIX[g[:3]]}{g[3:]}": n for g, n in MUNI.items()}
    _write(raw, "0009953", "SYNTHETIC legacy income (NUTS 2013-like)",
           {str(y): [_row(lg, MUNI[g], income(g, y))
                     for g, lg in zip(MUNI, legacy)] for y in range(2018, 2022)}, "2018", "2021", "EUR", "Annual")
    leg_p = {}
    for y in range(2019, 2022):
        rows = []
        for g, lg in zip(MUNI, legacy):
            v = price_q4(g, y, "Total")
            if v is not None and g == "11A0102":
                v = v / 1.10                    # 10% level shift in legacy methodology for one municipality
            rows.append(_row(lg, MUNI[g], v))
        leg_p[f"4th Quarter {y}"] = rows
    _write(raw, "0009490", "SYNTHETIC legacy price (NUTS 2013-like)", leg_p, "4th Quarter 2019", "4th Quarter 2021",
           "EUR/m2", "Quarterly")
