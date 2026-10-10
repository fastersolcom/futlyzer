"""Debug CLI.

    python -m app.cli import path/to/FC27_export.json
    python -m app.cli show            # current (newest) snapshot
    python -m app.cli history
"""
from __future__ import annotations

import argparse
import sys

from app.importers.exporter_v04 import ImportError_
from app.squad.positions import position_name, slot_position
from app.store import SnapshotStore


def _chem(v):
    return "?" if v is None else str(v)


def _pos(position_id):
    return position_name(position_id) or f"#{position_id}"


def _card_line(card) -> str:
    if card is None:
        return "(not in owned players!)"
    alts = "/".join(_pos(p) for p in card.alt_positions)
    loan = f"  LOAN {card.loan_duration}" if card.is_loan else ""
    return (f"OVR {card.overall}  GG {card.gg_rating}  {_pos(card.position)}"
            f"{' (' + alts + ')' if alts else ''}{loan}")


def summary(snap) -> str:
    sq = snap.squad
    xi_chem = [s.chemistry_points for s in sq.starting_xi]
    total = "?" if None in xi_chem else str(sum(xi_chem))
    loans = sum(p.is_loan for p in snap.players)
    lines = [
        f"Snapshot {snap.snapshot_id}  (exporter {snap.exporter_version}, exported {snap.exported_at})",
        f"Owned players: {len(snap.players)}  (loans: {loans})",
        f"Squad: {sq.title!r}  formation id {sq.formation_id}  manager id {sq.manager_id} "
        f"(nation {sq.manager_nation_id}, league {sq.manager_league_id})",
        "",
        f"Starting XI  (exported chemistry total: {total}/{3 * len(sq.starting_xi)})",
    ]
    for s in sq.starting_xi:
        slot = position_name(slot_position(s.slot_position_id)) or f"slot#{s.slot_position_id}"
        lines.append(f"  {slot:<4} {s.name or s.instance_id:<26} chem {_chem(s.chemistry_points)}  "
                     f"{_card_line(snap.player(s.instance_id))}  [role {s.role_id}, {s.focus}]")
    lines.append(f"Bench ({len(sq.substitutes)})")
    for s in sq.substitutes:
        lines.append(f"       {s.name or s.instance_id:<26}         {_card_line(snap.player(s.instance_id))}")
    t = sq.tactic_summary or {}
    lines.append("")
    lines.append(f"Tactic: {t.get('title')!r} code {t.get('code')}  build-up {t.get('buildUpStyleId')}  "
                 f"defensive {t.get('defensiveApproachId')}  "
                 f"line {t.get('customDefensiveApproachValue') if t.get('isCustomDefensiveApproach') else '-'}")
    if snap.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"  ! {w}" for w in snap.warnings)
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import").add_argument("path")
    sub.add_parser("show")
    sub.add_parser("history")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # accented names on Windows consoles
    store = SnapshotStore()

    if args.cmd == "import":
        try:
            snap, is_active = store.import_file(args.path)
        except ImportError_ as e:
            print(f"Import failed: {e}", file=sys.stderr)
            return 1
        if not is_active:
            print(f"NOTE: imported as history only; a newer export ({store.active_id()}) is active.\n")
        print(summary(snap))
    elif args.cmd == "show":
        snap = store.active()
        if not snap:
            print("No snapshots imported yet.")
            return 1
        print(summary(snap))
    elif args.cmd == "history":
        active = store.active_id()
        for e in store.list():
            mark = "*" if e["snapshot_id"] == active else " "
            print(f"{mark} {e['snapshot_id']}  exported {e['exported_at']}  ({e['source_name']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
