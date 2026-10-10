"""Tests against a real (sanitized) exporter v0.4.0 export.

Expected values were read from the export itself (squad 'aaa', 2026-10-10).
"""
from pathlib import Path

import pytest

from app.importers.exporter_v04 import parse_file
from app.squad.positions import can_play, position_name, slot_position

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sanitized_exports" / "FC27_aaa_2026-10-10.json"

# The fixture is git-ignored (real club data); these tests run only where it exists locally.
pytestmark = pytest.mark.skipif(not FIXTURE.exists(), reason="local fixture not present")


@pytest.fixture(scope="module")
def snap():
    return parse_file(FIXTURE)


def test_counts_and_no_warnings(snap):
    assert len(snap.players) == 99
    assert len(snap.squad.starting_xi) == 11
    assert len(snap.squad.substitutes) == 12
    assert snap.squad.formation_id == "36"
    assert snap.warnings == []


def test_starting_xi_and_slots(snap):
    xi = [(position_name(slot_position(s.slot_position_id)), s.name) for s in snap.squad.starting_xi]
    assert xi == [
        ("GK", "Marco Carnesecchi"), ("RB", "Marcos Llorente"), ("CB", "Éder Militão"),
        ("CB", "Ibrahima Konaté"), ("LB", "Álvaro Carreras"), ("CDM", "Khéphren Thuram"),
        ("CDM", "Nicolò Barella"), ("CAM", "Ademola Lookman"), ("RW", "Lineth Beerensteyn"),
        ("ST", "Lautaro Martínez"), ("LW", "Linda Caicedo"),
    ]


def test_every_xi_card_eligible_for_its_slot(snap):
    for s in snap.squad.starting_xi:
        assert can_play(snap.player(s.instance_id), s.slot_position_id) is True, s.name


def test_exact_card_eligibility_is_enforced(snap):
    lautaro = next(p for p in snap.players if p.name == "Lautaro Martínez")
    assert lautaro.position == 25 and lautaro.alt_positions == []
    assert can_play(lautaro, 25) is True
    assert can_play(lautaro, 23) is False  # cannot play RW
    assert can_play(lautaro, 999) is None  # unknown slot -> not guessed


def test_chemistry_as_exported(snap):
    assert sum(s.chemistry_points for s in snap.squad.starting_xi) == 31
    assert all(s.chemistry_points == 0 for s in snap.squad.substitutes)


def test_loans_and_card_fields(snap):
    assert sorted(p.name for p in snap.players if p.is_loan) == ["Lena Oberdorf", "Saud Abdulhamid"]
    vitinha = next(p for p in snap.players if p.name == "Vitinha")
    assert (vitinha.overall, vitinha.gg_rating, vitinha.position, vitinha.alt_positions) == (90, 86.38, 14, [10])
    assert vitinha.attributes["LongShots"] == 89
    assert vitinha.instance_id in {s.instance_id for s in snap.squad.substitutes}
