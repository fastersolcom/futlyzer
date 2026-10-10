"""Normalized models for one imported export.

Field sources are documented in docs/exporter-schema.md and were checked against
the real export fixtures/sanitized_exports/FC27_aaa_2026-10-10.json.
Anything not normalized here is still available in `raw`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class PlayerCard:
    instance_id: str  # FUT.GG gg-club player id (`players[].id`), exact owned card
    ea_id: Optional[int]
    base_ea_id: Optional[int]
    name: Optional[str]
    overall: Optional[int]
    gg_rating: Optional[float]
    position: Optional[int]  # EA position id, see app/squad/positions.py
    alt_positions: list
    nation_id: Optional[int]
    league_id: Optional[int]
    club_id: Optional[int]
    rarity: Optional[str]
    chemistry_profile: dict  # rarity.chemistryProfile, unverified semantics
    chemistry_points: Optional[int]
    chemistry_style: Optional[int]  # instance-level id (e.g. 250); no name map yet
    roles_plus: list
    roles_plus_plus: list
    playstyles: list
    playstyles_plus: list
    skill_moves: Optional[int]
    weak_foot: Optional[int]
    height: Optional[int]
    attributes: dict  # e.g. {"LongShots": 89, ...}
    is_untradeable: Optional[bool]
    loan_duration: Optional[int]  # None = not a loan
    purchased_for: Optional[int]
    market_price: Any
    games: Optional[int]
    goals: Optional[int]
    assists: Optional[int]
    raw: dict = field(repr=False, compare=False)

    @property
    def is_loan(self) -> bool:
        return self.loan_duration is not None


@dataclass(frozen=True)
class SquadSlot:
    group: str  # "FIELD" or "SUBSTITUTE"
    position_idx: Optional[int]
    instance_id: str  # `ggClubPlayerId`
    name: Optional[str]
    chemistry_points: Optional[int]
    chemistry_style: Optional[int]
    # From the tactic's positionRoles[position_idx]; XI only.
    slot_position_id: Optional[int] = None
    role_id: Optional[int] = None  # no verified role-id map yet
    focus: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True)
class Squad:
    title: Optional[str]
    formation_id: Any  # TODO: verified formation-id -> name map
    manager_id: Any
    manager_nation_id: Any
    manager_league_id: Any
    starting_xi: list  # list[SquadSlot]
    substitutes: list  # list[SquadSlot]
    tactic_summary: Any


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    raw_file_hash: str
    exporter_version: str
    exported_at: str
    imported_at: str
    players: list  # list[PlayerCard] -- the ONLY source of current ownership
    squad: Squad
    tactic: Any  # decoded tactic as exported, unnormalized
    warnings: list  # list[str]

    def owned_ids(self) -> set:
        return {p.instance_id for p in self.players}

    def player(self, instance_id):
        return next((p for p in self.players if p.instance_id == instance_id), None)
