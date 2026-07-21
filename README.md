# OpsBrain2 - Industrial Knowledge Brain

RAG-powered Q&A system with **conflict detection** and **lessons learned surfacing** for industrial plant operations.

## Key Features

1. **RAG Q&A**: Answer questions from industrial documents (manuals, SOPs, maintenance logs, incident reports)
2. **Conflict Detection**: Automatically detect when documents disagree or have gone stale
3. **Lessons Learned**: Proactively surface relevant past incidents

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys (or use .env file)
export GROQ_API_KEY=your-groq-key      # Free tier LLM
export VOYAGE_API_KEY=your-voyage-key  # Embeddings

# Run validation tests
python -m rag_engine.test_engine
```

## Usage

```python
from rag_engine import answer_query, get_all_known_conflicts

# Ask a question
result = answer_query("What is the relief pressure for PSV-101?")
print(result.answer)
print(f"Confidence: {result.confidence}")

# Check for conflicts
if result.conflicts:
    for conflict in result.conflicts:
        print(f"CONFLICT: {conflict.explanation}")

# Get all known conflicts (for dashboard)
all_conflicts = get_all_known_conflicts()
```

## Project Structure

```
OpsBrain2/
├── shared/
│   └── schemas.py          # Frozen contract - data types
├── rag_engine/             # Q&A, conflicts, lessons learned (Person 3)
│   ├── engine.py           # Main entry point
│   ├── retriever.py        # ChromaDB retrieval
│   ├── qa.py               # LLM-powered Q&A
│   ├── conflicts.py        # Conflict detection
│   ├── lessons.py          # Lessons learned surfacing
│   └── fixtures.py         # Dev fixtures
├── knowledge_graph/        # Graph queries (Person 2)
│   └── query.py            # Claim/incident queries
├── data/
│   ├── CONTRADICTIONS.md   # Test cases
│   └── chunks_manifest.json
└── requirements.txt
```

## Conflict Types

| Type | Description | Example |
|------|-------------|---------|
| `direct_contradiction` | Two docs claim different values | Manual says 150 psi, SOP says 145 psi |
| `decay` | Procedure outdated vs actual practice | SOP says quarterly, practice is monthly |

## API Reference

### `answer_query(question: str) -> QueryResult`

Main Q&A function. Returns answer with citations, conflicts, and lessons learned.

### `get_all_known_conflicts() -> List[Conflict]`

Get all detected conflicts for dashboard display.

---

*Built for ET AI Hackathon 2.0 - Industrial Knowledge Brain*
