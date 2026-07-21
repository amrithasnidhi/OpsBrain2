# Planted Contradictions — OpsBrain Hackathon Dataset

**CRITICAL DELIVERABLE** — Person 3 (conflict detection) and Person 4 (demo script) depend on
this file being accurate. The "wow" moment of the demo is only provable with these exact values.

---

## Contradiction 1 — Staleness / Decay

**Type:** `decay`
**Entity:** `Valve-V12`
**Parameter:** `inspection_interval_months`

| Role | File | Exact Text |
|------|------|-----------|
| Source A (interval) | `data/raw/valve_v12_maintenance_manual.pdf` | "Valve-V12 shall be inspected every **3 months (90 days)**. Failure to comply voids the OEM warranty and creates a documented safety deviation." (Section 3 — Inspection Schedule) |
| Source B (last event) | `data/raw/maintenance_log.xlsx` | Work order **WO-2025-0031**, date **2025-11-05**, action: "Replaced packing, lubricated stem assembly" — this is the **last** inspection entry for Valve-V12 in the log. No subsequent entry exists. |

**Expected detection:** As of July 21, 2026, **~8.5 months** have elapsed since WO-2025-0031.
This exceeds the 3-month required interval by **5.5 months**.
Expected output → `risk_type: "decay"`, `severity: "high"`.

---

## Contradiction 2 — Direct Numeric Contradiction

**Type:** `direct_contradiction`
**Entity:** `Compressor-C1`
**Parameter:** `max_pressure_psi`

| Role | File | Exact Text |
|------|------|-----------|
| Source A (OEM limit) | `data/raw/compressor_c1_manual.pdf` | "Maximum Operating Pressure: **150 psi**. This value is set by the OEM based on the design limits of the impeller assembly and casing." (Section 2 — Technical Specifications) |
| Source B (SOP limit) | `data/raw/sop_process_safety.pdf` | "Compressor-C1 pressure relief valve shall be set to **180 psi** maximum allowable working pressure (MAWP) as per Process Engineering specification PE-2021-047." (Section 3.2 — Compressor Relief Valve Settings) |

**Expected detection:** OEM manual caps Compressor-C1 at 150 psi; the process safety SOP
mandates a relief valve setting of 180 psi for the same tag — a 30 psi direct contradiction.
Expected output → `risk_type: "direct_contradiction"`, `severity: "high"`.

---

## Contradiction 3 — Conflicting Safety Procedure (Cooldown Period)

**Type:** `direct_contradiction`
**Entity:** `Pump-P3`
**Parameter:** `emergency_cooldown_minutes`

| Role | File | Exact Text |
|------|------|-----------|
| Source A (OEM) | `data/raw/pump_p3_oem_manual.pdf` | "Following emergency shutdown of Pump-P3, a mandatory cooling period of **15 minutes minimum** must elapse before any maintenance personnel access the pump casing or seal area." (Section 4.2 — Emergency Shutdown Procedure) |
| Source B (SOP) | `data/raw/sop_emergency_response.pdf` | "For Pump-P3 post-trip access: a **5-minute cooldown** period is sufficient for routine post-trip inspection checks by a qualified technician." (Section 3.1 — Equipment-Specific Emergency Procedures) |

**Expected detection:** A 3× discrepancy (15 min vs 5 min) in a safety-critical cooldown procedure.
Both documents are authoritative; the conflict creates real injury risk.
Expected output → `risk_type: "direct_contradiction"`, `severity: "high"`.

---

## Quick-Reference Summary Table

| # | Equipment | Parameter | Value A | File A | Value B | File B | risk_type |
|---|-----------|-----------|---------|--------|---------|--------|-----------|
| 1 | Valve-V12 | inspection_interval_months | 3 months | valve_v12_maintenance_manual.pdf | Last insp: 2025-11-05 (WO-2025-0031), 8.5 months ago | maintenance_log.xlsx | decay |
| 2 | Compressor-C1 | max_pressure_psi | 150 psi | compressor_c1_manual.pdf | 180 psi | sop_process_safety.pdf | direct_contradiction |
| 3 | Pump-P3 | emergency_cooldown_minutes | 15 min | pump_p3_oem_manual.pdf | 5 min | sop_emergency_response.pdf | direct_contradiction |

---

## Notes for Integration

- The ChromaDB collection `industrial_docs` will contain chunks from all source files above.
- Each contradiction spans exactly two chunks from two different `doc_id` values — search by
  `equipment_tags` containing the entity tag to retrieve both sides.
- The `ingested_at` timestamp will vary per run; use `doc_id` + `page_or_row` for stable references.
