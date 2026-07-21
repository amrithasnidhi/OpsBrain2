# Planted Contradictions for Acceptance Testing

This document specifies the 3 planted contradictions that the RAG engine MUST correctly detect
and classify. These are the primary acceptance criteria for the conflict detection feature.

---

## Contradiction #1: PSV-101 Relief Pressure (DIRECT_CONTRADICTION)

**Equipment:** PSV-101 (Pressure Safety Valve)
**Parameter:** Relief/Set Pressure
**Type:** `direct_contradiction`
**Severity:** HIGH (safety-critical)

| Source | Document | Value | Date |
|--------|----------|-------|------|
| A | equipment_manual_psv101.pdf (Page 12) | 150 psi | 2023-01-15 |
| B | sop_psv_testing.pdf (Page 3) | 145 psi | 2024-06-20 |

**Why it's a direct contradiction:**
Both documents claim to state the correct relief pressure. The manual says 150 psi is the set pressure,
while the SOP says to verify 145 psi before returning to service. These cannot both be correct for
normal operations. This requires immediate clarification from engineering.

**Expected detection output:**
- `risk_type`: `direct_contradiction`
- `severity`: `high`
- Explanation should mention both values and recommend verification

---

## Contradiction #2: PUMP-203 Inspection Interval (DECAY)

**Equipment:** PUMP-203 (Centrifugal Pump)
**Parameter:** Bearing Inspection Interval
**Type:** `decay`
**Severity:** MEDIUM (compliance/warranty issue)

| Source | Document | Value | Date |
|--------|----------|-------|------|
| A | pump_maintenance_manual.pdf (Page 45) | Every 6 months | 2022-08-10 |
| B | maintenance_log_2024.xlsx (Row 142) | Last inspection: 2024-10-15 | 2024-10-15 |

**Why it's a decay conflict:**
The manual specifies 6-month inspection intervals. The last inspection was 2024-10-15.
As of today (2025-07-xx), over 9 months have passed, meaning the inspection is OVERDUE.
This is "decay" because it's not two documents disagreeing, but rather the scheduled interval
has elapsed based on the passage of time.

**Expected detection output:**
- `risk_type`: `decay`
- `severity`: `medium`
- Explanation should note that the interval has been exceeded

---

## Contradiction #3: HX-301 Cleaning Frequency (DECAY)

**Equipment:** HX-301 (Heat Exchanger)
**Parameter:** Tube Bundle Cleaning Frequency
**Type:** `decay`
**Severity:** MEDIUM (procedure evolution)

| Source | Document | Value | Date |
|--------|----------|-------|------|
| A | heat_exchanger_sop_v2.pdf (Page 8) | Quarterly (every 3 months) | 2021-03-01 |
| B | maintenance_log_2025.xlsx (Row 89) | Monthly (increased frequency) | 2025-07-01 |

**Why it's a decay conflict:**
The SOP from 2021 says quarterly cleaning. However, the 2025 maintenance log shows that
actual practice has evolved to monthly cleaning due to feedstock changes. The formal SOP
has not been updated to reflect this change (ECR-2025-042 is pending). This is "decay"
because the documented procedure no longer matches actual practice.

**Expected detection output:**
- `risk_type`: `decay`
- `severity`: `medium`
- Explanation should identify the gap between documented procedure and actual practice

---

## Validation Procedure

Run the following to validate detection:

```python
from rag_engine.engine import validate_against_contradictions_md

results = validate_against_contradictions_md()
for test_name, result in results.items():
    print(f"{test_name}: {result['status']}")
    print(f"  Details: {result['details']}")
```

**Acceptance criteria:**
- [ ] All 3 contradictions detected
- [ ] PSV-101 classified as `direct_contradiction`
- [ ] PUMP-203 classified as `decay`
- [ ] HX-301 classified as `decay`
- [ ] Explanations are clear and actionable for plant operators

---

## Notes for Judges

This conflict detection is the **core differentiator** of the Industrial Knowledge Brain.
Traditional RAG systems would simply return documents without noticing that they disagree.

Our system:
1. Actively detects when documents contradict each other
2. Classifies whether it's a direct contradiction or staleness/decay
3. Generates human-readable explanations suitable for plant operators
4. Surfaces these proactively, not just when explicitly asked

This is critical for industrial safety where outdated or conflicting documentation
can lead to equipment damage, process upsets, or personnel injury.
