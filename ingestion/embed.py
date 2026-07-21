"""
Voyage AI batch embedding with exponential-backoff retry.

Model: voyage-3-lite (fast, cost-effective for hackathon scale).
Batch size: 64 texts per API call (within Voyage's documented limit).
Retry: up to 4 attempts with 1.5 × 2^n second backoff.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

log = logging.getLogger(__name__)

_MODEL = "voyage-3-lite"
_BATCH_SIZE = 64
_MAX_RETRIES = 4
_INITIAL_WAIT = 1.5  # seconds; doubles each attempt


def _client():
    import voyageai
    key = os.getenv("VOYAGE_API_KEY")
    if not key:
        raise EnvironmentError(
            "VOYAGE_API_KEY is not set. Export it before running the pipeline:\n"
            "  export VOYAGE_API_KEY=your_key_here\n"
            "or add it to your .env file and `source .env`."
        )
    return voyageai.Client(api_key=key)


def embed_batch(
    texts: list[str],
    model: str = _MODEL,
    input_type: str = "document",
) -> list[list[float]]:
    """
    Embed texts in batches of _BATCH_SIZE using Voyage AI.
    Raises RuntimeError after _MAX_RETRIES failed attempts.
    """
    client = _client()
    all_embeddings: list[list[float]] = []

    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        embeddings = _embed_with_retry(client, batch, model, input_type)
        all_embeddings.extend(embeddings)
        log.debug("Embedded batch %d–%d", start, start + len(batch))

    return all_embeddings


def _embed_with_retry(
    client,
    texts: list[str],
    model: str,
    input_type: str,
) -> list[list[float]]:
    last_exc: Optional[Exception] = None
    wait = _INITIAL_WAIT

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            result = client.embed(texts, model=model, input_type=input_type)
            return result.embeddings
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                log.warning(
                    "Embedding attempt %d/%d failed (%s). Retrying in %.1fs…",
                    attempt, _MAX_RETRIES, exc, wait,
                )
                time.sleep(wait)
                wait *= 2

    log.error("All %d embedding attempts failed for batch of %d texts.", _MAX_RETRIES, len(texts))
    raise RuntimeError(f"Embedding failed after {_MAX_RETRIES} attempts") from last_exc
