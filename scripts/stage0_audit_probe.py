"""Stage 0 audit probe (stdlib only).

Reads INE indicator metadata and measures, per period, how many of the 308
municipal rows (7-character geocod) carry a value. Prints a summary only and
writes nothing to disk. Used to produce the numbers in docs/feasibility_audit.md.

Usage:  python -I scripts/stage0_audit_probe.py 0012741 0014698 0012234
Rate limits (INE usage rules, accessed 2026-11-22): <= 15-20 req/s, <= 1,000,000 rows/request.
"""
import collections
import json
import sys
import urllib.request

BASE = "https://www.ine.pt/ine/json_indicador"
HEADERS = {"User-Agent": "portugal-housing-affordability-stage0/0.1"}


def get(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    return json.load(urllib.request.urlopen(req, timeout=180))


def main(codes: list[str]) -> None:
    for code in codes:
        print("=====", code)
        meta = get(f"{BASE}/pindicaMeta.jsp?varcd={code}&lang=EN")
        meta = meta[0] if isinstance(meta, list) else meta
        for k in ("IndicadorNome", "Periodic", "PrimeiroPeriodo", "UltimoPeriodo",
                  "UnidadeMedida", "DataUltimaAtualizacao", "Nota"):
            print(f"  {k}: {meta.get(k)}")
        data = get(f"{BASE}/pindica.jsp?op=2&varcd={code}&Dim1=T&lang=EN")[0]["Dados"]
        periods = list(data)
        cats = sorted({r.get("dim_3_t") for r in data[periods[-1]] if r.get("dim_3_t")})
        if "Total" in cats:  # measure the 'Total' category, not an arbitrary one
            cats = ["Total"]
        print("  geocod lengths (last period):",
              dict(collections.Counter(len(r["geocod"]) for r in data[periods[-1]])))
        for p in periods[:: max(1, len(periods) // 7)] + [periods[-1]]:
            rows = [r for r in data[p] if len(r["geocod"]) == 7
                    and (not cats or r.get("dim_3_t") == cats[0])]
            valued = [r for r in rows if r.get("valor") not in (None, "")]
            print(f"  {p}: municipal rows={len(rows)} valued={len(valued)}")


if __name__ == "__main__":
    main(sys.argv[1:])
