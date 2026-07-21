"""
Equipment tag extraction via regex pattern matching.
Runs BEFORE embedding so ChunkMetadata.equipment_tags is populated on every chunk
regardless of whether the downstream LLM claim extractor has run.

Primary pattern targets the naming convention used across all synthetic documents:
  <CapWord>-<OptionalLetter><digits>   e.g. Compressor-C1, Valve-V12, Pump-P3, Turbine-T1

Secondary patterns cover standard ISA/P&ID instrument tag shorthand:
  CV-, PV-, FT-, PT-, LT-, MOV-, etc.
"""
from __future__ import annotations

import re

# Primary: matches Valve-V12, Compressor-C1, Pump-P3, Turbine-T1, HeatExchanger-HE2, etc.
_PRIMARY = re.compile(r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)*-[A-Z]?\d+)\b")

# Secondary: ISA-style instrument tags in ALL-CAPS-NUMBER format
_SECONDARY = [
    re.compile(r"\b(CV-\d+)\b"),    # Control Valve
    re.compile(r"\b(PV-\d+)\b"),    # Pressure Valve / Pressure Vessel
    re.compile(r"\b(FT-\d+)\b"),    # Flow Transmitter
    re.compile(r"\b(PT-\d+)\b"),    # Pressure Transmitter
    re.compile(r"\b(LT-\d+)\b"),    # Level Transmitter
    re.compile(r"\b(TT-\d+)\b"),    # Temperature Transmitter
    re.compile(r"\b(MOV-\d+)\b"),   # Motor Operated Valve
    re.compile(r"\b(PSV-\d+)\b"),   # Pressure Safety Valve
    re.compile(r"\b(FCV-\d+)\b"),   # Flow Control Valve
]


def extract_equipment_tags(text: str) -> list[str]:
    """
    Return a deduplicated, order-preserving list of equipment tags found in text.
    Designed for >90% recall on the planted-contradiction documents.
    """
    found: list[str] = []
    seen: set[str] = set()

    for match in _PRIMARY.finditer(text):
        tag = match.group(1)
        if tag not in seen:
            found.append(tag)
            seen.add(tag)

    for pattern in _SECONDARY:
        for match in pattern.finditer(text):
            tag = match.group(1)
            if tag not in seen:
                found.append(tag)
                seen.add(tag)

    return found
