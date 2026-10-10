"""Importer + ownership-isolation tests.

SYNTHETIC data: the envelope mirrors exporter v0.4 background.js; inner player
fields are minimal placeholders. Replace/extend with real sanitized fixtures
from fixtures/sanitized_exports/ as soon as one exists.
"""
import json

import pytest

from app.importers.exporter_v04 import ImportError_, parse_bytes
from app.store import SnapshotStore


def make_export(player_names, exported_at="2026-10-01T10:00:00.000Z", xi=None):
    players = [{"id": 1000 + i, "chemistryPoints": 2, "playerDef": {"commonName": n}}
               for i, n in enumerate(player_names)]
    xi = players[:11] if xi is None else xi
    slot = lambda p, g: {"group": g, "ggClubPlayerId": p["id"], "name": p["playerDef"]["commonName"],
                         "chemistryPoints": p["chemistryPoints"]}
    return {
        "exporter": "FC27 Club Exporter", "exporterVersion": "0.4.0", "exportedAt": exported_at,
        "counts": {"players": len(players)},
        "squad": {"title": "Test", "activeFormationId": 1, "managerId": 1,
                  "startingXI": [slot(p, "FIELD") for p in xi],
                  "substitutes": [slot(p, "SUBSTITUTE") for p in players[11:13]]},
        "tactics": {}, "players": players,
    }


def write(tmp_path, name, doc):
    p = tmp_path / name
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


NAMES = [f"Player {i}" for i in range(15)]


def test_parses_envelope():
    snap = parse_bytes(json.dumps(make_export(NAMES)).encode())
    assert len(snap.players) == 15
    assert len(snap.squad.starting_xi) == 11
    assert len(snap.squad.substitutes) == 2
    assert snap.squad.starting_xi[0].name == "Player 0"
    assert not any("not in the exported" in w for w in snap.warnings)


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(exporter="Other"),
    lambda d: d.update(exporterVersion="0.1.0"),
    lambda d: d.pop("exportedAt"),
    lambda d: d.pop("players"),
    lambda d: d["squad"].pop("startingXI"),
])
def test_rejects_invalid(mutate):
    d = make_export(NAMES)
    mutate(d)
    with pytest.raises(ImportError_):
        parse_bytes(json.dumps(d).encode())


def test_warns_when_squad_player_not_owned():
    d = make_export(NAMES)
    d["squad"]["startingXI"][0]["ggClubPlayerId"] = 999999
    snap = parse_bytes(json.dumps(d).encode())
    assert any("not in the exported club players list" in w for w in snap.warnings)


def test_newest_export_alone_defines_ownership(tmp_path):
    store = SnapshotStore(tmp_path / "data")
    old = make_export(NAMES + ["Sold Player"], exported_at="2026-09-01T10:00:00.000Z")
    new = make_export(NAMES, exported_at="2026-10-01T10:00:00.000Z")
    store.import_file(write(tmp_path, "old.json", old))
    _, active = store.import_file(write(tmp_path, "new.json", new))
    assert active
    names = {p.name for p in store.active().players}
    assert "Sold Player" not in names


def test_importing_older_export_later_does_not_become_active(tmp_path):
    store = SnapshotStore(tmp_path / "data")
    store.import_file(write(tmp_path, "new.json", make_export(NAMES, exported_at="2026-10-01T10:00:00.000Z")))
    _, active = store.import_file(write(tmp_path, "old.json",
                                        make_export(NAMES + ["Sold Player"], exported_at="2026-09-01T10:00:00.000Z")))
    assert not active
    assert "Sold Player" not in {p.name for p in store.active().players}
    assert len(store.list()) == 2  # history kept, not merged


def test_reimport_is_idempotent(tmp_path):
    store = SnapshotStore(tmp_path / "data")
    f = write(tmp_path, "a.json", make_export(NAMES))
    store.import_file(f)
    store.import_file(f)
    assert len(store.list()) == 1
