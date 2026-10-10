"""Local snapshot store.

Raw exports are kept immutable as <data_dir>/snapshots/<snapshot_id>.json.
The active snapshot is the one with the newest exportedAt -- it alone defines
current ownership. Older snapshots are history and are never merged in.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.importers.exporter_v04 import parse_bytes

DEFAULT_DATA_DIR = Path(os.environ.get("FC27_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))


class SnapshotStore:
    def __init__(self, data_dir=DEFAULT_DATA_DIR):
        self.dir = Path(data_dir) / "snapshots"
        self.index_path = Path(data_dir) / "index.json"

    def _index(self) -> list:
        if not self.index_path.exists():
            return []
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def import_file(self, path):
        """Import an export; returns (snapshot, is_active)."""
        data = Path(path).read_bytes()
        index = self._index()
        known = {e["snapshot_id"]: e for e in index}
        snap = parse_bytes(data)
        if snap.snapshot_id not in known:
            self.dir.mkdir(parents=True, exist_ok=True)
            (self.dir / f"{snap.snapshot_id}.json").write_bytes(data)
            index.append({
                "snapshot_id": snap.snapshot_id,
                "raw_file_hash": snap.raw_file_hash,
                "exporter_version": snap.exporter_version,
                "exported_at": snap.exported_at,
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "source_name": Path(path).name,
            })
            self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return snap, self.active_id() == snap.snapshot_id

    def list(self) -> list:
        return sorted(self._index(), key=lambda e: _ts(e["exported_at"]))

    def active_id(self):
        entries = self.list()
        return entries[-1]["snapshot_id"] if entries else None

    def load(self, snapshot_id):
        entry = next(e for e in self._index() if e["snapshot_id"] == snapshot_id)
        data = (self.dir / f"{snapshot_id}.json").read_bytes()
        return parse_bytes(data, imported_at=entry["imported_at"])

    def active(self):
        sid = self.active_id()
        return self.load(sid) if sid else None


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
