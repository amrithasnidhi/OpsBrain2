import re
import difflib

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
