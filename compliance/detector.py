# compliance/detector.py
"""
Compliance Gap Detector

Checks claims from the knowledge graph against compliance rules
and classifies each as compliant, gap, or unknown.
"""

import os
import sys
import logging
from typing import List, Optional
from datetime import date

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import ComplianceGap, Claim
from .rules import COMPLIANCE_RULES

logger = logging.getLogger(__name__)


def _get_all_claims() -> List[Claim]:
    """Get all claims from knowledge graph, falling back to fixtures."""
    try:
        from knowledge_graph.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, doc_id, chunk_id, equipment_tag, parameter_name,
                   value, unit, effective_date, source_text, confidence
            FROM claims
        """)
        claims = []
        for row in cursor.fetchall():
            claims.append(Claim(
                id=row[0],
                doc_id=row[1],
                chunk_id=row[2],
                equipment_tag=row[3],
                parameter_name=row[4],
                value=row[5],
                unit=row[6],
                effective_date=row[7],
                source_text=row[8],
                confidence=row[9]
            ))
        conn.close()
        if claims:
            return claims
    except Exception as e:
        logger.debug(f"Knowledge graph unavailable: {e}")

    # Fallback to fixtures
    try:
        from rag_engine.fixtures import MOCK_CLAIMS
        return MOCK_CLAIMS
    except Exception:
        return []


def _parse_frequency_to_months(value: str) -> Optional[int]:
    """Convert frequency strings to months."""
    value_lower = value.lower().strip()
    if "monthly" in value_lower or value_lower == "1":
        return 1
    elif "quarterly" in value_lower or "3" in value_lower:
        return 3
    elif "semi" in value_lower or "6" in value_lower:
        return 6
    elif "annual" in value_lower or "yearly" in value_lower or "12" in value_lower:
        return 12
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _check_rule_against_claims(rule: dict, claims: List[Claim]) -> List[ComplianceGap]:
    """Check a single rule against relevant claims."""
    gaps = []

    # Find claims matching this rule's parameter_name and equipment_pattern
    matching_claims = []
    for claim in claims:
        # Check parameter name match
        if rule["parameter_name"].lower() not in claim.parameter_name.lower():
            continue

        # Check equipment pattern match
        if rule["equipment_pattern"]:
            if rule["equipment_pattern"].upper() not in claim.equipment_tag.upper():
                continue

        matching_claims.append(claim)

    if not matching_claims:
        # No claims found - unknown status
        gaps.append(ComplianceGap(
            standard=rule["standard"],
            requirement=rule["requirement"],
            equipment_tag="(No matching equipment)",
            status="unknown",
            details=f"No claims found for parameter '{rule['parameter_name']}' matching equipment pattern '{rule.get('equipment_pattern', 'any')}'"
        ))
        return gaps

    # Check each matching claim against the rule
    for claim in matching_claims:
        comparison = rule["comparison"]
        threshold = rule["threshold"]
        status = "compliant"
        details = ""

        try:
            if comparison == "max_months":
                # Value should be <= threshold months
                claim_months = _parse_frequency_to_months(claim.value)
                if claim_months is None:
                    status = "unknown"
                    details = f"Could not parse interval value: {claim.value}"
                elif claim_months > threshold:
                    status = "gap"
                    details = f"Interval {claim_months} months exceeds maximum {threshold} months required by {rule['standard']}"
                else:
                    details = f"Interval {claim_months} months complies with {threshold} month maximum"

            elif comparison == "frequency_months":
                # Frequency should be at least threshold (e.g., quarterly = 3 months)
                claim_months = _parse_frequency_to_months(claim.value)
                if claim_months is None:
                    status = "unknown"
                    details = f"Could not parse frequency value: {claim.value}"
                elif claim_months > threshold:
                    status = "gap"
                    details = f"Frequency {claim.value} ({claim_months} months) is less frequent than required {threshold} months"
                else:
                    details = f"Frequency {claim.value} meets or exceeds {threshold} month requirement"

            elif comparison == "max_value":
                # Numeric value should be <= threshold
                try:
                    claim_val = float(claim.value.replace(",", ""))
                    if claim_val > threshold:
                        status = "gap"
                        details = f"Value {claim_val} exceeds maximum {threshold}"
                    else:
                        details = f"Value {claim_val} within limit {threshold}"
                except (ValueError, TypeError):
                    status = "unknown"
                    details = f"Could not parse numeric value: {claim.value}"

            elif comparison == "percent_deviation":
                # For multi-value conflicts - this is checked at conflict level
                # Here we just note that the parameter exists
                details = f"Value {claim.value} found - deviation check performed at conflict detection level"
                status = "compliant"

        except Exception as e:
            status = "unknown"
            details = f"Error checking compliance: {str(e)}"

        gaps.append(ComplianceGap(
            standard=rule["standard"],
            requirement=rule["requirement"],
            equipment_tag=claim.equipment_tag,
            status=status,
            details=details
        ))

    return gaps


def get_compliance_status() -> List[ComplianceGap]:
    """
    Check all compliance rules against knowledge graph claims.

    Returns:
        List of ComplianceGap objects showing status for each rule/equipment combo
    """
    all_claims = _get_all_claims()
    all_gaps = []

    for rule in COMPLIANCE_RULES:
        rule_gaps = _check_rule_against_claims(rule, all_claims)
        all_gaps.extend(rule_gaps)

    # Sort by status (gaps first, then unknown, then compliant)
    status_order = {"gap": 0, "unknown": 1, "compliant": 2}
    all_gaps.sort(key=lambda g: status_order.get(g.status, 3))

    return all_gaps
