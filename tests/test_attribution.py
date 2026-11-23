"""Source and attribution metadata required by the INE (CC BY 4.0) and DGT (CC BY 4.0) terms."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "src" / "housing_pt" / "dashboard_template.html").read_text(encoding="utf-8")


def test_dashboard_carries_required_credits():
    assert "Instituto Nacional de Estatística – Portugal (Statistics Portugal)" in TEMPLATE
    assert "Informação geográfica cedida pela Direção-Geral do Território" in TEMPLATE
    assert "CC&nbsp;BY&nbsp;4.0" in TEMPLATE
    assert "métricas calculadas pelo autor" in TEMPLATE or "métricas calculadas pelo autor".lower() in TEMPLATE.lower()
    assert "período de referência" in TEMPLATE            # INE: identify the statistic and its reference period


def test_dashboard_excludes_unlicensed_bpstat_data():
    low = TEMPLATE.lower()
    assert "bpstat" not in low and "banco de portugal" not in low and "bportugal" not in low


def test_manifests_record_provenance():
    ine = json.loads((ROOT / "data" / "manifests" / "ine_manifest.json").read_text(encoding="utf-8"))
    assert {m["code"] for m in ine} >= {"0012234", "0014698", "0012741", "0014642"}
    for m in ine:
        assert len(m["data_sha256"]) == 64 and "CC BY 4.0" in m["licence"] and m["ine_last_update"]
    caop = json.loads((ROOT / "data" / "manifests" / "caop_manifest.json").read_text(encoding="utf-8"))
    assert all("CC BY 4.0" in f["licence"] and f["attribution"] == "Informação geográfica cedida pela Direção-Geral do Território"
               for f in caop["files"])
    assert caop["join_check_dico"]["both"] == 308 and caop["join_check_dico"]["caop_only"] == 0
