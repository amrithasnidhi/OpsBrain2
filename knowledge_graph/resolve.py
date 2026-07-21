import re
import difflib
from typing import Dict, Any, Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Claim, Citation

# In-memory mapping of normalized keys to canonical names
CANONICAL_ENTITIES = {}

def normalize_tag(tag: str) -> str:
    """
    Normalizes a tag by removing all non-alphanumeric characters and uppercasing.
    E.g., "Valve V-12" -> "VALVEV12"
          "Valve-12"   -> "VALVE12"
    """
    return re.sub(r'[^A-Z0-9]', '', tag.upper())

def resolve_entity(tag: str) -> str:
    """
    Resolves an entity tag to its canonical form using normalization and fuzzy matching.
    """
    norm = normalize_tag(tag)
    
    if not CANONICAL_ENTITIES:
        canonical = tag.strip()
        CANONICAL_ENTITIES[norm] = canonical
        return canonical
        
    # Exact match on normalized string
    if norm in CANONICAL_ENTITIES:
        return CANONICAL_ENTITIES[norm]
        
    # Fuzzy match against known normalized keys
    # Cutoff 0.75 works well for 'VALVE12' vs 'VALVEV12' (similarity ~ 0.93)
    matches = difflib.get_close_matches(norm, CANONICAL_ENTITIES.keys(), n=1, cutoff=0.75)
    
    if matches:
        return CANONICAL_ENTITIES[matches[0]]
    else:
        # Register new canonical entity
        canonical = tag.strip()
        CANONICAL_ENTITIES[norm] = canonical
        return canonical


def resolve_temporal_conflict(claim_a: Claim, claim_b: Claim) -> Dict[str, Any]:
    """
    Resolve a conflict between two claims based on their effective dates.

    If both claims have effective_date set, the newer one supersedes the older.
    Otherwise, the conflict remains unresolved and requires manual review.

    Args:
        claim_a: First claim in the conflict
        claim_b: Second claim in the conflict

    Returns:
        dict with resolution info:
        - resolution: "temporal_supersession" or "unresolved"
        - authoritative_claim: the newer claim (if resolved)
        - superseded_claim: the older claim (if resolved)
        - explanation: human-readable explanation
        - requires_manual_review: True if unresolved
    """
    if claim_a.effective_date and claim_b.effective_date:
        # Both have dates - newer supersedes older
        if claim_a.effective_date > claim_b.effective_date:
            newer, older = claim_a, claim_b
        else:
            newer, older = claim_b, claim_a

        return {
            "resolution": "temporal_supersession",
            "authoritative_claim": newer,
            "superseded_claim": older,
            "explanation": f"{newer.doc_id} ({newer.effective_date}) supersedes {older.doc_id} ({older.effective_date})",
            "requires_manual_review": False
        }

    # At least one claim is missing a date
    missing_dates = []
    if not claim_a.effective_date:
        missing_dates.append(claim_a.doc_id)
    if not claim_b.effective_date:
        missing_dates.append(claim_b.doc_id)

    return {
        "resolution": "unresolved",
        "authoritative_claim": None,
        "superseded_claim": None,
        "explanation": f"Cannot resolve temporally - missing dates in: {', '.join(missing_dates)}",
        "requires_manual_review": True
    }


def claim_to_citation(claim: Claim) -> Citation:
    """Convert a Claim to a Citation for conflict tracking."""
    return Citation(
        doc_id=claim.doc_id,
        source_file=f"Document {claim.doc_id}",
        page_or_row=None,
        excerpt=claim.source_text[:200] if claim.source_text else ""
    )
