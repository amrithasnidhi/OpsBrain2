"""
Tests for ingestion/tagger.py — equipment tag extraction.
Key requirement: >90% recall on the planted-contradiction documents.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.tagger import extract_equipment_tags

# The three equipment tags that are central to the planted contradictions
CRITICAL_TAGS = ["Compressor-C1", "Valve-V12", "Pump-P3"]


# ----- basic extraction -------------------------------------------------------

def test_extract_primary_tags():
    text = "Compressor-C1 max pressure is 150 psi; Valve-V12 inspection every 3 months."
    tags = extract_equipment_tags(text)
    assert "Compressor-C1" in tags
    assert "Valve-V12" in tags


def test_extract_pump_tag():
    text = "Following emergency shutdown of Pump-P3, allow 15-minute cooling period."
    tags = extract_equipment_tags(text)
    assert "Pump-P3" in tags


def test_extract_turbine_tag():
    text = "Turbine-T1 vibration reading exceeded 5.8 mm/s."
    tags = extract_equipment_tags(text)
    assert "Turbine-T1" in tags


def test_deduplication():
    text = "Compressor-C1 pressure is 150 psi. Compressor-C1 must be inspected."
    tags = extract_equipment_tags(text)
    assert tags.count("Compressor-C1") == 1


def test_order_preserved():
    text = "Valve-V12 and Compressor-C1 are both affected."
    tags = extract_equipment_tags(text)
    assert tags.index("Valve-V12") < tags.index("Compressor-C1")


def test_returns_empty_list_for_plain_text():
    text = "This document describes general safety procedures with no specific equipment."
    tags = extract_equipment_tags(text)
    assert tags == []


def test_no_false_positives_from_numbers():
    text = "Operating at 150 psi and 3 months inspection interval."
    tags = extract_equipment_tags(text)
    assert tags == []


def test_multi_tag_extraction():
    text = (
        "Equipment Compressor-C1, Valve-V12, and Pump-P3 are part of the gas compression train. "
        "Turbine-T1 drives the generator."
    )
    tags = extract_equipment_tags(text)
    assert set(tags) >= {"Compressor-C1", "Valve-V12", "Pump-P3", "Turbine-T1"}


def test_isa_secondary_patterns():
    text = "PSV-101 is set at 180 psi. CV-203 controls flow to Compressor-C1."
    tags = extract_equipment_tags(text)
    assert "PSV-101" in tags
    assert "CV-203" in tags


# ----- >90% recall on planted-contradiction text snippets --------------------

_CONTRADICTION_SNIPPETS = [
    # C1 — Compressor-C1 max pressure (manual side)
    "Maximum Operating Pressure for Compressor-C1 is 150 psi. This value is set by the OEM.",
    # C1 — Compressor-C1 max pressure (SOP side)
    "Compressor-C1 pressure relief valve shall be set to 180 psi maximum allowable working pressure.",
    # C2 — Valve-V12 inspection interval
    "Valve-V12 shall be inspected every 3 months (90 days). Failure to comply voids the OEM warranty.",
    # C2 — maintenance log row for Valve-V12
    "work_order_id: WO-2025-0031 | equipment_tag: Valve-V12 | date: 2025-11-05 | technician: Mike Johnson",
    # C3 — Pump-P3 cooldown (manual side)
    "Following emergency shutdown of Pump-P3, a mandatory cooling period of 15 minutes minimum must elapse.",
    # C3 — Pump-P3 cooldown (SOP side)
    "For Pump-P3 post-trip access: a 5-minute cooldown period is sufficient for routine post-trip inspection.",
]

_EXPECTED_TAGS = {
    0: {"Compressor-C1"},
    1: {"Compressor-C1"},
    2: {"Valve-V12"},
    3: {"Valve-V12"},
    4: {"Pump-P3"},
    5: {"Pump-P3"},
}


@pytest.mark.parametrize("idx,snippet", enumerate(_CONTRADICTION_SNIPPETS))
def test_recall_on_contradiction_snippet(idx, snippet):
    """Each contradiction snippet must yield the expected equipment tag (100% recall)."""
    tags = extract_equipment_tags(snippet)
    expected = _EXPECTED_TAGS[idx]
    missing = expected - set(tags)
    assert not missing, (
        f"Snippet {idx}: missing tags {missing} from extracted {tags}\nText: {snippet}"
    )


def test_overall_recall_above_90_percent():
    """Aggregate recall across all 6 contradiction snippets must exceed 90%."""
    hits = 0
    total = len(_CONTRADICTION_SNIPPETS)
    for idx, snippet in enumerate(_CONTRADICTION_SNIPPETS):
        tags = extract_equipment_tags(snippet)
        if _EXPECTED_TAGS[idx].issubset(set(tags)):
            hits += 1
    recall = hits / total
    assert recall >= 0.90, f"Tag extraction recall {recall:.0%} < 90% on contradiction snippets"
