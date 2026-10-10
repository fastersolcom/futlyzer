"""Parse and validate a 'FC27 Club Exporter' v0.4.x JSON file.

The envelope shape below is taken from the exporter's own background.js
(extension/existing-working-exporter). Inner FUT.GG player fields are not
assumed beyond what the exporter itself reads.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.models.snapshot import PlayerCard, Snapshot, Squad, SquadSlot
from app.squad.positions import can_play

EXPORTER_NAME = "FC27 Club Exporter"
SUPPORTED_VERSIONS = {"0.4.0"}


class ImportError_(ValueError):
    """The file is not a usable exporter JSON."""


def _player_name(p: dict):
    d = p.get("playerDef") or {}
    return d.get("commonName") or " ".join(x for x in (d.get("firstName"), d.get("lastName")) if x) or None


def _card(p: dict) -> PlayerCard:
    d = p.get("playerDef") or {}
    rarity = d.get("rarity") or {}
    return PlayerCard(
        instance_id=p.get("id"),
        ea_id=d.get("eaId"),
        base_ea_id=d.get("basePlayerEaId"),
        name=_player_name(p),
        overall=d.get("overall"),
        gg_rating=d.get("ggRating"),
        position=d.get("position"),
        alt_positions=d.get("alternativePositionIds") or [],
        nation_id=d.get("nationEaId"),
        league_id=d.get("leagueEaId"),
        club_id=d.get("clubEaId"),
        rarity=rarity.get("name"),
        chemistry_profile=rarity.get("chemistryProfile") or {},
        # Instance-level values; playerDef has a different chemistryStyle scale.
        chemistry_points=p.get("chemistryPoints"),
        chemistry_style=p.get("chemistryStyle"),
        roles_plus=d.get("rolesPlus") or [],
        roles_plus_plus=d.get("rolesPlusPlus") or [],
        playstyles=d.get("playstyles") or [],
        playstyles_plus=d.get("playstylesPlus") or [],
        skill_moves=d.get("skillMoves"),
        weak_foot=d.get("weakFoot"),
        height=d.get("height"),
        attributes={k[len("attribute"):]: v for k, v in d.items() if k.startswith("attribute")},
        is_untradeable=p.get("isUntradeable"),
        loan_duration=d.get("loanDuration"),
        purchased_for=p.get("purchasedFor"),
        market_price=p.get("marketPrice"),
        games=p.get("gamesPlayed"),
        goals=p.get("goals"),
        assists=p.get("assists"),
        raw=p,
    )


def _slot(x: dict, roles_by_idx=None) -> SquadSlot:
    role = (roles_by_idx or {}).get(x.get("positionIdx")) or {}
    return SquadSlot(
        group=x.get("group"),
        position_idx=x.get("positionIdx"),
        instance_id=x.get("ggClubPlayerId"),
        name=x.get("name"),
        chemistry_points=x.get("chemistryPoints"),
        chemistry_style=x.get("chemistryStyle"),
        slot_position_id=role.get("positionUniqueId"),
        role_id=role.get("roleId"),
        focus=role.get("focusName"),
        raw=x,
    )


def _position_roles(doc: dict) -> list:
    # XI positionIdx i corresponds to positionRoles[i] (verified on the aaa fixture:
    # all 11 cards eligible for their slot under this alignment).
    summary = (doc.get("squad") or {}).get("activeTacticSummary") or {}
    decoded = (doc.get("tactics") or {}).get("decoded") or {}
    return summary.get("positionRoles") or decoded.get("positionRoles") or []


def parse_bytes(data: bytes, imported_at: str = None) -> Snapshot:
    file_hash = hashlib.sha256(data).hexdigest()
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ImportError_(f"not valid JSON: {e}") from e
    if not isinstance(doc, dict):
        raise ImportError_("top level must be an object")

    if doc.get("exporter") != EXPORTER_NAME:
        raise ImportError_(f"unexpected exporter: {doc.get('exporter')!r}")
    version = doc.get("exporterVersion")
    if version not in SUPPORTED_VERSIONS:
        raise ImportError_(f"unsupported exporterVersion {version!r}; supported: {sorted(SUPPORTED_VERSIONS)}")
    if not doc.get("exportedAt"):
        raise ImportError_("missing exportedAt")
    if not isinstance(doc.get("players"), list):
        raise ImportError_("missing players list")
    sq = doc.get("squad")
    if not isinstance(sq, dict) or not isinstance(sq.get("startingXI"), list):
        raise ImportError_("missing squad.startingXI")

    players = [_card(p) for p in doc["players"] if isinstance(p, dict)]
    roles_by_idx = dict(enumerate(_position_roles(doc)))
    squad = Squad(
        title=sq.get("title"),
        formation_id=sq.get("activeFormationId"),
        manager_id=sq.get("managerId"),
        manager_nation_id=sq.get("managerNationId"),
        manager_league_id=sq.get("managerLeagueId"),
        starting_xi=[_slot(x, roles_by_idx) for x in sq["startingXI"]],
        substitutes=[_slot(x) for x in sq.get("substitutes") or []],
        tactic_summary=sq.get("activeTacticSummary"),
    )

    warnings = []
    owned = {p.instance_id for p in players}
    if None in owned:
        warnings.append("some players have no id")
    if len(squad.starting_xi) != 11:
        warnings.append(f"starting XI has {len(squad.starting_xi)} players, expected 11")
    for s in squad.starting_xi + squad.substitutes:
        if s.instance_id not in owned:
            # Could be a loan or an unvisited Players page -- never assume which.
            warnings.append(f"squad player {s.name or s.instance_id} is not in the exported club players list")
    by_id = {p.instance_id: p for p in players}
    for s in squad.starting_xi:
        card = by_id.get(s.instance_id)
        ok = can_play(card, s.slot_position_id) if card else None
        if ok is False:
            warnings.append(f"{s.name} cannot play slot {s.slot_position_id}")
        elif ok is None and card:
            warnings.append(f"{s.name}: slot id {s.slot_position_id} is unverified, eligibility not checked")
    counts = doc.get("counts") or {}
    if counts.get("players") not in (None, len(players)):
        warnings.append(f"counts.players={counts.get('players')} but {len(players)} players parsed")

    return Snapshot(
        snapshot_id=file_hash[:12],
        raw_file_hash=file_hash,
        exporter_version=version,
        exported_at=doc["exportedAt"],
        imported_at=imported_at or datetime.now(timezone.utc).isoformat(),
        players=players,
        squad=squad,
        tactic=doc.get("tactics"),
        warnings=warnings,
    )


def parse_file(path) -> Snapshot:
    return parse_bytes(Path(path).read_bytes())
