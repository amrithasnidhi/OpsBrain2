# rag_engine/retriever.py
"""
Retrieval layer for the RAG engine.

Queries ChromaDB collection for relevant chunks based on semantic similarity.
Falls back to fixture data when ChromaDB isn't available (early development).
"""

import os
import re
import logging
from typing import List, Optional, Tuple

# Try to import ChromaDB; fall back to fixtures if not available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from shared.schemas import ChunkMetadata
from . import fixtures

logger = logging.getLogger(__name__)


class Chunk:
    """
    Represents a retrieved document chunk with content, metadata, and similarity score.
    """
    def __init__(
        self,
        chunk_id: str,
        content: str,
        metadata: ChunkMetadata,
        similarity_score: float = 0.0
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata
        self.similarity_score = similarity_score

    def __repr__(self):
        return f"Chunk({self.chunk_id}, score={self.similarity_score:.3f})"


# ---------------------------------------------------------------------------
# Equipment tag extraction (matches Person 1's tagger patterns)
# ---------------------------------------------------------------------------

# Common industrial equipment tag patterns
EQUIPMENT_TAG_PATTERNS = [
    r'\b(PSV-\d{3})\b',           # Pressure Safety Valves: PSV-101
    r'\b(PUMP-\d{3})\b',          # Pumps: PUMP-203
    r'\b(HX-\d{3})\b',            # Heat Exchangers: HX-301
    r'\b(C-\d{3})\b',             # Compressors: C-401
    r'\b(V-\d{3})\b',             # Vessels: V-101
    r'\b(T-\d{3})\b',             # Tanks: T-201
    r'\b(FV-\d{3})\b',            # Flow Valves: FV-102
    r'\b(LV-\d{3})\b',            # Level Valves: LV-103
    r'\b(TV-\d{3})\b',            # Temperature Valves: TV-104
    r'\b(PV-\d{3})\b',            # Pressure Valves: PV-105
    r'\b(MOV-\d{3})\b',           # Motor Operated Valves: MOV-201
    r'\b(E-\d{3}[A-Z]?)\b',       # Exchangers: E-101, E-101A
    r'\b(P-\d{3}[A-Z]?)\b',       # Pumps (alternate): P-101, P-101A
    r'\b([A-Z]{2,4}-\d{3,4})\b',  # Generic: XX-000 or XXX-0000
]


def extract_equipment_tags(text: str) -> List[str]:
    """
    Extract equipment tags from text using regex patterns.
    Returns unique tags in the order they appear.
    """
    tags = []
    seen = set()

    for pattern in EQUIPMENT_TAG_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            tag = match.group(1).upper()
            if tag not in seen:
                tags.append(tag)
                seen.add(tag)

    return tags


# ---------------------------------------------------------------------------
# ChromaDB Client
# ---------------------------------------------------------------------------

_chroma_client = None
_chroma_collection = None


def _get_chroma_collection():
    """
    Get or initialize the ChromaDB collection.
    Returns None if ChromaDB isn't available or configured.
    """
    global _chroma_client, _chroma_collection

    if not CHROMADB_AVAILABLE:
        return None

    if _chroma_collection is not None:
        return _chroma_collection

    # Try to connect to ChromaDB
    chroma_path = os.environ.get("CHROMADB_PATH", "./data/chromadb")
    collection_name = os.environ.get("CHROMADB_COLLECTION", "opsbrain_chunks")

    try:
        _chroma_client = chromadb.PersistentClient(path=chroma_path)
        _chroma_collection = _chroma_client.get_collection(name=collection_name)
        logger.info(f"Connected to ChromaDB collection '{collection_name}' at {chroma_path}")
        return _chroma_collection
    except Exception as e:
        logger.warning(f"ChromaDB not available: {e}. Using fixture data.")
        return None


# ---------------------------------------------------------------------------
# Main Retrieval Function
# ---------------------------------------------------------------------------

def retrieve(
    question: str,
    top_k: int = 6,
    equipment_filter: Optional[List[str]] = None
) -> List[Chunk]:
    """
    Retrieve relevant chunks for a question.

    Args:
        question: The user's question
        top_k: Maximum number of chunks to return (default 6)
        equipment_filter: Optional list of equipment tags to filter on

    Returns:
        List of Chunk objects sorted by relevance (highest first)
    """
    # Extract equipment tags from question if no filter provided
    if equipment_filter is None:
        equipment_filter = extract_equipment_tags(question)

    logger.debug(f"Retrieving chunks for: '{question}' with equipment filter: {equipment_filter}")

    # Try ChromaDB first
    collection = _get_chroma_collection()

    if collection is not None:
        return _retrieve_from_chromadb(collection, question, top_k, equipment_filter)
    else:
        return _retrieve_from_fixtures(question, top_k, equipment_filter)


def _retrieve_from_chromadb(
    collection,
    question: str,
    top_k: int,
    equipment_filter: List[str]
) -> List[Chunk]:
    """
    Retrieve chunks from ChromaDB using vector similarity search.
    """
    # Build metadata filter if equipment tags specified
    where_filter = None
    if equipment_filter:
        # ChromaDB uses $in for list membership
        where_filter = {
            "$or": [
                {"equipment_tags": {"$contains": tag}}
                for tag in equipment_filter
            ]
        }

    try:
        results = collection.query(
            query_texts=[question],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata_dict = results['metadatas'][0][i]
                distance = results['distances'][0][i] if results['distances'] else 0

                # Convert distance to similarity score (assuming cosine distance)
                # cosine distance is in [0, 2], similarity = 1 - (distance / 2)
                similarity = 1.0 - (distance / 2.0)

                metadata = ChunkMetadata(**metadata_dict)
                chunk = Chunk(
                    chunk_id=results['ids'][0][i],
                    content=doc,
                    metadata=metadata,
                    similarity_score=similarity
                )
                chunks.append(chunk)

        return chunks

    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}. Falling back to fixtures.")
        return _retrieve_from_fixtures(question, top_k, equipment_filter)


def _retrieve_from_fixtures(
    question: str,
    top_k: int,
    equipment_filter: List[str]
) -> List[Chunk]:
    """
    Retrieve chunks from fixture data using keyword-based similarity.
    Used for development/testing when ChromaDB isn't available.
    """
    logger.debug("Using fixture data for retrieval")

    # Get chunks from fixtures
    fixture_chunks = fixtures.search_chunks_by_similarity(question, top_k=top_k * 2)

    # Apply equipment filter if specified
    if equipment_filter:
        fixture_chunks = [
            c for c in fixture_chunks
            if any(tag in c.metadata.equipment_tags for tag in equipment_filter)
        ] or fixture_chunks  # Fall back to unfiltered if no matches

    # Convert fixture Chunk to our Chunk type
    chunks = []
    for fc in fixture_chunks[:top_k]:
        chunk = Chunk(
            chunk_id=fc.chunk_id,
            content=fc.content,
            metadata=fc.metadata,
            similarity_score=fc.similarity_score
        )
        chunks.append(chunk)

    return chunks


def get_chunk_by_id(chunk_id: str) -> Optional[Chunk]:
    """
    Retrieve a specific chunk by its ID.
    """
    collection = _get_chroma_collection()

    if collection is not None:
        try:
            results = collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"]
            )
            if results and results['documents']:
                metadata = ChunkMetadata(**results['metadatas'][0])
                return Chunk(
                    chunk_id=chunk_id,
                    content=results['documents'][0],
                    metadata=metadata,
                    similarity_score=1.0
                )
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id} from ChromaDB: {e}")

    # Fall back to fixtures
    fc = fixtures.get_chunk_by_id(chunk_id)
    if fc:
        return Chunk(
            chunk_id=fc.chunk_id,
            content=fc.content,
            metadata=fc.metadata,
            similarity_score=fc.similarity_score
        )
    return None


def get_all_equipment_tags_from_chunks(chunks: List[Chunk]) -> List[str]:
    """
    Extract all unique equipment tags from a list of chunks.
    """
    tags = set()
    for chunk in chunks:
        tags.update(chunk.metadata.equipment_tags)
    return list(tags)


# ---------------------------------------------------------------------------
# Hybrid Retrieval (Feature 4)
# ---------------------------------------------------------------------------

def _claims_to_pseudo_chunks(claims: list) -> List[Chunk]:
    """Convert KG Claim objects into pseudo-Chunks so they can be ranked alongside dense results."""
    pseudo: List[Chunk] = []
    for claim in claims:
        text = (
            f"[Knowledge Graph] {claim.equipment_tag} — {claim.parameter_name}: "
            f"{claim.value}{' ' + claim.unit if claim.unit else ''}. "
            f"Source: {claim.source_text[:200]}"
        )
        try:
            meta = ChunkMetadata(
                doc_id=claim.doc_id,
                doc_type="manual",
                source_file=f"kg:{claim.doc_id}",
                equipment_tags=[claim.equipment_tag],
                ingested_at="",
            )
        except Exception:
            continue
        pseudo.append(Chunk(
            chunk_id=f"kg_{claim.id}",
            content=text,
            metadata=meta,
            similarity_score=claim.confidence,
        ))
    return pseudo


def _dedupe(chunks: List[Chunk]) -> List[Chunk]:
    """Remove duplicate chunks (by chunk_id), preserving order."""
    seen: set[str] = set()
    result: List[Chunk] = []
    for c in chunks:
        if c.chunk_id not in seen:
            seen.add(c.chunk_id)
            result.append(c)
    return result


def hybrid_retrieve(question: str, top_k: int = 6) -> tuple[List[Chunk], str]:
    """
    Hybrid retrieval: combines dense vector search with KG structured claims.

    Returns:
        (chunks, retrieval_mode) where retrieval_mode is "hybrid" or "dense"
    """
    dense_results = retrieve(question, top_k=top_k)

    # Extract tags from question to fetch structured KG data
    tags = extract_equipment_tags(question)
    structured_results: List[Chunk] = []

    if tags:
        try:
            from knowledge_graph.query import get_claims_for_entity
            for tag in tags[:3]:  # cap at 3 tags to avoid overload
                claims = get_claims_for_entity(tag)
                structured_results += _claims_to_pseudo_chunks(claims)
        except Exception as e:
            logger.warning(f"KG structured retrieval failed: {e}")

    if structured_results:
        all_chunks = _dedupe(dense_results + structured_results)
        # Sort by similarity score, keep top_k
        all_chunks.sort(key=lambda c: c.similarity_score, reverse=True)
        return all_chunks[:top_k + 3], "hybrid"  # allow slightly more for hybrid
    else:
        return dense_results, "dense"

