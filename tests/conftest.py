import geopandas as gpd
import pytest
from shapely.geometry import box

from housing_pt import config, geo
from . import synth


@pytest.fixture()
def synth_env(tmp_path, monkeypatch):
    """Redirect every data/report directory to a temp dir holding synthetic INE-shaped raw files."""
    for name in ("RAW", "INTERIM", "PROCESSED", "MANIFESTS", "REPORTS"):
        monkeypatch.setattr(config, name, tmp_path / name.lower())
    monkeypatch.setattr(geo, "EXPECTED_MUNICIPALITIES", len(synth.MUNI))
    synth.write_raw(config.RAW)
    return tmp_path


@pytest.fixture()
def synth_geometry():
    """Four unit squares keyed by dico, as the CAOP-derived geometry frame the dashboard builder expects."""
    dicos = [g[3:] for g in synth.MUNI]
    return gpd.GeoDataFrame({"dico": dicos, "region": "continente",
                             "geometry": [box(i, 0, i + 1, 1) for i in range(len(dicos))]}, crs=4326)
