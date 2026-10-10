"""EA position ids and exact-card slot eligibility.

Only ids seen in a real export are mapped. Names were cross-checked against
well-known cards in fixtures/sanitized_exports/FC27_aaa_2026-10-10.json
(e.g. Carnesecchi 0, Llorente 3, Militão 5, Carreras 7, Barella 14,
Szoboszlai 18, Lautaro 25, Doku 27). Unmapped ids return None -- never guess.
"""
from __future__ import annotations

POSITION_NAMES = {
    0: "GK", 3: "RB", 5: "CB", 7: "LB", 10: "CDM", 12: "RM",
    14: "CM", 16: "LM", 18: "CAM", 23: "RW", 25: "ST", 27: "LW",
}

# Tactic slot ids (positionRoles[].positionUniqueId) -> base position id.
# Seen in formation 36 (4-2-1-3); every XI card was eligible under this map.
# TODO: other formations' slot ids (e.g. RCM/LCM, RS/LS, wing-backs) once seen.
SLOT_TO_POSITION = {
    0: 0, 3: 3, 4: 5, 6: 5, 7: 7, 9: 10, 11: 10, 18: 18, 23: 23, 25: 25, 27: 27,
}


def position_name(position_id):
    return POSITION_NAMES.get(position_id)


def slot_position(slot_id):
    return SLOT_TO_POSITION.get(slot_id)


def can_play(card, slot_id):
    """True/False for the exact card in this slot; None if the slot id is unverified."""
    base = slot_position(slot_id)
    if base is None:
        return None
    return base == card.position or base in card.alt_positions
