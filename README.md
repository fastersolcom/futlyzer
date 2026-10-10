# FC27 Squad Assistant

Local-first EA FC 27 Ultimate Team squad assistant. See `PROJECT_CONTEXT.md` for the full brief.

**Rule #1:** the newest imported export is the only source of current ownership.

## Layout
- `extension/existing-working-exporter/` — FC27 Club Exporter v0.4.0, copied unchanged. Do not edit; version a copy instead.
- `backend/` — Python core (no AI, no network).
- `fixtures/sanitized_exports/` — sanitized real exports for tests. Raw exports (`FC27_*.json`, `fixtures/raw/`) are git-ignored.
- `docs/` — schema notes and roadmap.

## Setup (Windows, Python 3.9+)
```
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest
```

## CLI
```
cd backend
.venv\Scripts\python -m app.cli import path\to\FC27_<squad>_<date>.json
.venv\Scripts\python -m app.cli show       # newest snapshot
.venv\Scripts\python -m app.cli history    # * marks the active snapshot
```
Imported raw files are stored immutably under `backend/data/snapshots/` (override with `FC27_DATA_DIR`).

## Status
- [x] M0 bootstrap
- [x] M1 importer — validated against a real v0.4.0 export (`fixtures/sanitized_exports/`, local only — git-ignored)
  - New fixture: `python tools/sanitize_export.py <raw.json> ../fixtures/sanitized_exports/<name>.json` (from `backend/`)
- [ ] M2+ see `PROJECT_CONTEXT.md` §24
