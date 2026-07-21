# Ingestion Workstream

Owned by: Amritha
Branch: `amritha/ingestion`

## What it does

Parses industrial documents (PDFs, Excel, OCR images, DOCX), chunks them semantically,
extracts equipment tags via regex, embeds via Voyage AI, and upserts into a persistent
ChromaDB vector store. Also dumps a flat JSON manifest for teammates to inspect offline.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys
export ANTHROPIC_API_KEY=your_key
export VOYAGE_API_KEY=your_key

# 3. Generate synthetic dataset (first time only)
python data/generate_synthetic.py

# 4. Run the pipeline
python -m ingestion.pipeline --input_dir data/raw --collection industrial_docs

# 5. Run tests
pytest tests/ -v
```

## Outputs

| Artifact | Path | Description |
|----------|------|-------------|
| ChromaDB | `./chroma_db/` | Persistent vector store, collection `industrial_docs` |
| Manifest | `data/chunks_manifest.json` | Flat list of `{chunk_id, doc_id, text, metadata}` — use this for offline inspection |
| Contradictions | `data/CONTRADICTIONS.md` | Exact text of the 3 planted contradictions with source file references |

## ChromaDB connection

```python
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("industrial_docs")

# Query example
results = collection.query(
    query_embeddings=[...],
    n_results=5,
    where={"equipment_tags": {"$contains": "Compressor-C1"}},
)
```

**Note:** `equipment_tags` is stored as a comma-joined string in ChromaDB metadata
(e.g. `"Compressor-C1,Valve-V12"`). Split on `","` to get the list back.

## Pipeline behaviour

- **Idempotent:** re-running upserts to the same deterministic chunk IDs — no duplicates.
- **Logging:** every document processed, chunk count, and any embedding failures are logged.
- **Supported file types:** `.pdf`, `.xlsx`, `.xls`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.docx`
- **doc_type inference:** based on filename keywords (`sop`, `manual`, `incident`, etc.) and extension.

## Key decisions

- Chunk size: ~300 tokens max, ~45 tokens overlap (~15%) — preserves enough context for
  multi-sentence numeric specs (the core contradiction evidence).
- Voyage `voyage-3-lite`: cost-effective and fast for hackathon scale; swap to `voyage-3`
  for production.
- ChromaDB cosine space: consistent with typical RAG setups; change `hnsw:space` if the
  RAG engine uses a different metric.
