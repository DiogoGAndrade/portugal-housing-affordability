import json
from pathlib import Path

import pandas as pd
import pytest

from housing_pt import config, findings

ROOT = Path(__file__).resolve().parents[1]


def _frames():
    key = pd.DataFrame({"geocod": ["1100001", "1100002"], "nuts3_code": ["110", "120"], "nuts3": ["Alfa", "Beta"]})
    rows = []
    for g, (i20, i24, p6, r6) in {"110": (5.0, 6.0, 0.2, 0.1), "120": (7.0, 6.5, -0.1, -0.05)}.items():
        rows.append({"geocod": g, "year": 2020, "i2_years_80m2": i20, "i6_price_vs_income_real": None, "i6_rent_vs_income_real": None})
        rows.append({"geocod": g, "year": 2024, "i2_years_80m2": i24, "i6_price_vs_income_real": p6, "i6_rent_vs_income_real": r6})
    muni = pd.DataFrame({"geocod": ["1100001", "1100002"], "year": 2024, "price_m2": [1000.0, None],
                         "income_hh": [10000.0, 9000.0], "rent_m2": [None, None]})
    p4 = {"moran": [{"variable": "ln_i2", "n": 10, "morans_I": 0.5}, {"variable": "i6_price_vs_income_real", "n": 9, "morans_I": 0.3}],
          "kruskal_nuts2": [{"metric": "i2_years_80m2", "epsilon_sq": 0.4}],
          "sensitivity": [{"variant": v, "spearman_vs_headline": 0.99, "share_changing_quintile": 0.1, "n_both": 5}
                          for v in ("income: gross per tax household", "income: net per taxpayer",
                                    "price: new dwellings only", "price: existing dwellings only")]}
    return pd.DataFrame(rows), muni, key, p4


def test_findings_computed_from_panels_not_hard_coded():
    n3, muni, key, p4 = _frames()
    f = findings.compute(n3, muni, key, p4)
    assert f["i2_2024"]["min"] == ("Alfa", 6.0) and f["i2_2024"]["max"] == ("Beta", 6.5)
    assert f["i2_change"]["up"] == 1 and f["i2_change"]["down"] == 1
    assert f["i6_price"]["pos"] == 1 and f["i6_rent"]["pos"] == 1
    assert f["coverage"]["price"] == 1 and f["coverage"]["both"] == 1 and f["coverage"]["rent"] == 0
    text = findings.render(f)
    assert "6,0" in text and "não um ranking" in text


def test_replace_block_is_idempotent():
    readme = f"a\n{findings.START}\nOLD\n{findings.END}\nb\n"
    once = findings.replace_block(readme, "NEW")
    assert "NEW" in once and "OLD" not in once and findings.replace_block(once, "NEW") == once


def test_readme_has_findings_markers_and_no_bpstat_results():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert findings.START in text and findings.END in text
    block = text[text.index(findings.START):text.index(findings.END)]
    assert block.strip() != findings.START and "12710738" not in text and "I5" not in block


@pytest.mark.skipif(not (config.PROCESSED / "panel_nuts3.parquet").exists(), reason="processed panels not built")
def test_readme_block_matches_current_data():
    assert findings.main(check=True) == 0
