"""Minimal INE JSON API client: polite rate limiting, raw cache, provenance manifest."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import config

_last_call = 0.0
USER_AGENT = "portugal-housing-affordability/0.1 (research)"


def _get(url: str) -> bytes:
    global _last_call
    wait = config.MIN_INTERVAL_S - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = resp.read()
    _last_call = time.monotonic()
    return body


def data_url(code: str, lang: str = "EN") -> str:
    return f"{config.INE_BASE}/pindica.jsp?op=2&varcd={code}&Dim1=T&lang={lang}"


def meta_url(code: str, lang: str = "EN") -> str:
    return f"{config.INE_BASE}/pindicaMeta.jsp?varcd={code}&lang={lang}"


def fetch(code: str, raw_dir: Path | None = None, force: bool = False) -> dict:
    """Download data + metadata for one indicator into raw_dir and return a manifest entry."""
    raw_dir = Path(raw_dir) if raw_dir else config.RAW  # resolved at call time (tests redirect config)
    raw_dir.mkdir(parents=True, exist_ok=True)
    data_path = raw_dir / f"ine_{code}_data.json"
    meta_path = raw_dir / f"ine_{code}_meta.json"
    if force or not data_path.exists():
        data_path.write_bytes(_get(data_url(code)))
    if force or not meta_path.exists():
        meta_path.write_bytes(_get(meta_url(code)))

    data = json.loads(data_path.read_bytes())[0]
    meta = json.loads(meta_path.read_bytes())
    meta = meta[0] if isinstance(meta, list) else meta
    if "Verdadeiro" not in data.get("Sucesso", {}):
        raise RuntimeError(f"INE returned an error for {code}: {data.get('Sucesso')}")
    return {
        "code": code,
        "title": meta.get("IndicadorNome"),
        "unit": meta.get("UnidadeMedida"),
        "first_period": meta.get("PrimeiroPeriodo"),
        "last_period": meta.get("UltimoPeriodo"),
        "ine_last_update": meta.get("DataUltimaAtualizacao"),
        "note": meta.get("Nota"),
        "data_url": data_url(code),
        "meta_url": meta_url(code),
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "retrieved_at": datetime.fromtimestamp(data_path.stat().st_mtime, timezone.utc).isoformat(),
        "licence": "CC BY 4.0 - Source: Instituto Nacional de Estatistica - Portugal (Statistics Portugal)",
    }


def load_raw(code: str, raw_dir: Path | None = None) -> dict:
    raw_dir = Path(raw_dir) if raw_dir else config.RAW
    return json.loads((raw_dir / f"ine_{code}_data.json").read_bytes())[0]
