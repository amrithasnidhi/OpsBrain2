# knowledge_graph/query.py
"""
Knowledge Graph Query Interface (Person 2's implementation).

This is a STUB file showing the expected interface.
Person 2 should implement these functions to connect to the actual graph.

The RAG engine will import these functions and call them for:
- Looking up claims about specific equipment
- Finding conflicting claims globally
- Getting incidents similar to a query
- Detecting stale/overdue claims
"""

from typing import List, Tuple, Optional
from datetime import date
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Claim, Incident


def get_claims_for_entity(equipment_tag: str) -> List[Claim]:
    """
    Get all claims associated with a specific equipment tag.

    Args:
        equipment_tag: Equipment identifier (e.g., "PSV-101", "PUMP-203")

    Returns:
        List of Claim objects for that equipment

    Example:
        >>> claims = get_claims_for_entity("PSV-101")
        >>> for c in claims:
        ...     print(f"{c.parameter_name}: {c.value}")
    """
    # TODO: Person 2 - implement actual graph query
    # For now, fall back to fixtures
    from rag_engine.fixtures import get_claims_for_entity as fixture_fn
    return fixture_fn(equipment_tag)


def get_claims_for_parameter(parameter_name: str) -> List[Claim]:
    """
    Get all claims for a specific parameter across all equipment.

    Args:
        parameter_name: Parameter name (e.g., "inspection_interval_months")

    Returns:
        List of Claim objects for that parameter

    Example:
        >>> claims = get_claims_for_parameter("relief_pressure_psi")
        >>> for c in claims:
        ...     print(f"{c.equipment_tag}: {c.value}")
    """
    # TODO: Person 2 - implement actual graph query
    from rag_engine.fixtures import get_claims_for_parameter as fixture_fn
    return fixture_fn(parameter_name)


def find_conflicting_claims() -> List[Tuple[Claim, Claim]]:
    """
    Find all pairs of claims that potentially conflict.

    Two claims conflict if they:
    - Share the same equipment_tag AND parameter_name
    - Have different values

    Returns:
        List of (claim_a, claim_b) tuples representing conflicts

    Example:
        >>> conflicts = find_conflicting_claims()
        >>> for a, b in conflicts:
        ...     print(f"{a.equipment_tag}.{a.parameter_name}: {a.value} vs {b.value}")
    """
    # TODO: Person 2 - implement actual graph query
    from rag_engine.fixtures import find_conflicting_claims as fixture_fn
    return fixture_fn()


def get_incidents_similar_to(
    query: str,
    equipment_tags: Optional[List[str]] = None
) -> List[Incident]:
    """
    Find incidents relevant to a query or set of equipment tags.

    Args:
        query: Natural language query
        equipment_tags: Optional list of equipment tags to filter on

    Returns:
        List of relevant Incident objects

    Example:
        >>> incidents = get_incidents_similar_to(
        ...     "pump bearing failure",
        ...     equipment_tags=["PUMP-203"]
        ... )
    """
    # TODO: Person 2 - implement actual graph query with embedding similarity
    from rag_engine.fixtures import get_incidents_similar_to as fixture_fn
    return fixture_fn(query, equipment_tags)


def get_stale_claims(reference_date: Optional[date] = None) -> List[Claim]:
    """
    Find claims that may be stale (e.g., overdue maintenance intervals).

    For claims that specify an interval (e.g., "inspect every 6 months"),
    cross-reference against the most recent matching log entry date
    and flag if the implied next-due-date has passed.

    Args:
        reference_date: Date to check against (default: today)

    Returns:
        List of Claim objects that are overdue

    Example:
        >>> stale = get_stale_claims()
        >>> for c in stale:
        ...     print(f"{c.equipment_tag} {c.parameter_name} is overdue")
    """
    # TODO: Person 2 - implement actual staleness detection
    from rag_engine.fixtures import get_stale_claims as fixture_fn
    return fixture_fn(reference_date)
