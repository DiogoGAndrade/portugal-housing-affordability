"""Run the dashboard's pure JS logic (CORE block) in Node and compare with the Python metrics.
Skipped when Node is unavailable. Needs no processed data, so it runs in CI."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from housing_pt import metrics

TEMPLATE = Path(__file__).resolve().parents[1] / "src" / "housing_pt" / "dashboard_template.html"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

UNITS = [
    {"id": "A", "name": 'Alfa, "Beta"', "nuts3": "N3", "nuts2": "N2", "P": [1000, 1100, 1200, None, 1400, 1500, 1600],
     "Y": [10000, 10500, 11000, 11500, 12000, 12500, None], "R": [None, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5]},
    {"id": "B", "name": "Beta", "nuts3": "N3", "nuts2": "N2", "P": [None] * 7, "Y": [9000] * 6 + [None], "R": [None] * 7},
]
YEARS = list(range(2019, 2026))
CPI = [83.775, 83.764, 84.825, 91.469, 95.412, 97.717, 100.0]


def run_js(expr: str):
    html = TEMPLATE.read_text(encoding="utf-8")
    core = re.search(r"// ==CORE-START==.*?// ==CORE-END==", html, re.S).group(0)
    prog = f"const DATA={{years:{json.dumps(YEARS)},cpi:{json.dumps(CPI)}}};{core}\nconst U={json.dumps(UNITS)};\n{expr}"
    out = subprocess.run(["node", "-e", prog], capture_output=True, check=True)  # bytes: keep CRLF intact
    return out.stdout.decode("utf-8")


def test_js_metrics_equal_python_formulas():
    res = json.loads(run_js(
        "const o={};for(const k of ['i1','i2','i3','i4','i6p','i6r','pricer'])"
        "o[k]=DATA.years.map((y,i)=>M[k].fn(U[0],i,80));console.log(JSON.stringify(o))"))
    u = UNITS[0]
    df = pd.DataFrame({"P": u["P"], "Y": u["Y"], "R": u["R"], "cpi": CPI}, dtype=float)
    py = {
        "i1": metrics.i1_m2_per_income_year(df.Y, df.P),
        "i2": metrics.i2_years_of_income(df.Y, df.P, 80),
        "i3": 100 * metrics.i3_rent_to_income(df.Y, df.R, 80),
        "i4": 100 * metrics.i4_rent_over_price(df.R, df.P),
        "pricer": metrics.to_real(df.P, df.cpi),
    }
    for k, series in py.items():
        for js, p in zip(res[k], series):
            assert (js is None and pd.isna(p)) or js == pytest.approx(p), k
    # I6: base values 2019 (price) / 2020 (rent); missing base or inputs -> null, never extrapolated
    assert res["i6p"][0] == pytest.approx(0.0) and res["i6p"][3] is None and res["i6p"][6] is None
    assert res["i6r"][0] is None and res["i6r"][1] == pytest.approx(0.0)
    import math
    assert res["i6p"][5] == pytest.approx(math.log(1500 / 1000) - math.log(12500 / 10000))
    # units B has no price/rent: everything null (no zero-fill)
    none = json.loads(run_js("console.log(JSON.stringify(DATA.years.map((y,i)=>M.i2.fn(U[1],i,80))))"))
    assert all(v is None for v in none)


def test_area_changes_levels_not_ratio_structure():
    r = json.loads(run_js("console.log(JSON.stringify([M.i2.fn(U[0],0,60),M.i2.fn(U[0],0,120)]))"))
    assert r[1] == pytest.approx(2 * r[0])


def test_csv_export_quoting_and_missing():
    csv = run_js("process.stdout.write(csvText(U,'municipality','i2',5,80))")
    assert csv.startswith("\ufeffnivel,id,nome,")
    lines = csv.strip().split("\r\n")
    assert len(lines) == 3
    assert '"Alfa, ""Beta"""' in lines[1]            # RFC 4180 quoting of commas and quotes
    cells = lines[2].split(",")
    assert cells[-2] == "" and cells[5] == "2024"     # unit B has no value -> empty cell, year 2024
    assert lines[1].split(",")[-2] != ""
    assert ",80," in lines[1]                         # reference area recorded for area-dependent metrics


def test_every_metric_is_classified_observed_or_derived():
    res = json.loads(run_js(
        "console.log(JSON.stringify(Object.fromEntries(Object.entries(M).map(([k,m])=>[k,[m.kind,!!m.area]]))))"))
    assert set(res) == {"i1", "i2", "i3", "i4", "i6p", "i6r", "price", "pricer", "rent", "income"}
    assert {k for k, (kind, _) in res.items() if kind == "obs"} == {"price", "rent", "income"}
    # exactly the metrics that use the area slider are labelled 'reference-area' (never presented as observed)
    assert {k for k, (kind, area) in res.items() if area} == {k for k, (kind, _) in res.items() if kind == "ref"} == {"i2", "i3"}
    kinds = json.loads(run_js("console.log(JSON.stringify(KINDS))"))
    assert "pressuposto" in kinds["ref"] and kinds["obs"].startswith("Observado")


def test_search_is_accent_and_case_insensitive_and_reports_ambiguity():
    r = json.loads(run_js(
        "const L=[{name:'Faro'},{name:'São João da Madeira'},{name:'Calheta (R.A.M.)'},{name:'Calheta (R.A.A.)'}];"
        "console.log(JSON.stringify([findUnit(L,'FARO'),findUnit(L,'sao joao'),findUnit(L,'calheta'),findUnit(L,'zzz'),findUnit(L,'  ')]))"))
    assert r[0]["match"]["name"] == "Faro" and r[0]["count"] == 1            # case-insensitive exact
    assert r[1]["match"]["name"] == "São João da Madeira"                     # accents ignored, unique partial
    assert r[2]["match"] is None and r[2]["count"] == 2                       # ambiguous: no silent pick
    assert r[3]["count"] == 0 and r[4]["count"] == 0                          # no match / blank query


def test_table_view_is_alphabetical_not_ranked_and_keeps_missing():
    rows = json.loads(run_js(
        "const T=[{id:'z',name:'Zebra',nuts3:'N',nuts2:'M',P:[100,100,100,100,100,100,100],Y:[10,10,10,10,10,10,null],R:[]},"
        "{id:'a',name:'Árvore',nuts3:'N',nuts2:'M',P:[900,900,900,900,900,900,900],Y:[10,10,10,10,10,10,null],R:[]},"
        "{id:'m',name:'Meio',nuts3:'N',nuts2:'M',P:[null,null,null,null,null,null,null],Y:[10,10,10,10,10,10,null],R:[]}];"
        "console.log(JSON.stringify([tableRows(T,'price',5,80),tableRows(T,'i2',6,80),tableRows(T,'price',5,80,'meio')]))"))
    prices = rows[0]
    assert [r["name"] for r in prices] == ["Árvore", "Meio", "Zebra"]         # alphabetical although values are 900/none/100
    assert prices[1]["value"] is None and prices[1]["text"] == "sem dado"
    assert rows[1][0]["value"] is None                                         # 2025 has no income -> no extrapolation
    assert [r["name"] for r in rows[2]] == ["Meio"]                            # filter


def test_glossary_covers_every_indicator_with_definition_unit_and_period():
    res = json.loads(run_js(
        "console.log(JSON.stringify({m:Object.keys(M),g:Object.keys(GLOSS),units:Object.fromEntries(Object.entries(M).map(([k,v])=>[k,v.unit])),"
        "gl:GLOSS}))"))
    assert set(res["m"]) == set(res["g"])
    for k, g in res["gl"].items():
        assert g["def"].strip() and re.search(r"20\d\d", g["ref"]), k
    assert "2024" in res["gl"]["income"]["ref"] and "2025" not in res["gl"]["income"]["ref"]   # income ends 2024
    assert res["gl"]["rent"]["ref"].startswith("2020")                                           # rent starts 2020
    assert res["units"]["i2"] == "anos" and res["units"]["i1"] == "m²/ano" and res["units"]["rent"] == "€/m²/mês"
