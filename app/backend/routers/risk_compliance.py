"""
Risk & Compliance API Router

Provides endpoints for:
- GET /api/compliance - Compliance gap status across all rules
"""
import os
import sys
from fastapi import APIRouter, HTTPException
from typing import List

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from shared.schemas import ComplianceGap
from compliance.detector import get_compliance_status

router = APIRouter(prefix="/api", tags=["risk-compliance"])


@router.get("/compliance", response_model=List[ComplianceGap])
def get_compliance():
    """
    Get compliance status for all rules against knowledge base claims.

    Returns a list of ComplianceGap objects showing:
    - standard: The compliance standard (e.g., "OSHA 29 CFR 1910.119")
    - requirement: Human-readable requirement description
    - equipment_tag: The equipment being checked
    - status: "compliant", "gap", or "unknown"
    - details: Explanation of the status
    """
    try:
        gaps = get_compliance_status()
        return gaps
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
