# OpsBrain2 Backend

FastAPI backend wrapping the RAG Engine and Knowledge Graph.

## Running

1. Activate your virtual environment and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   uvicorn app.backend.main:app --reload
   ```

The API runs on `http://127.0.0.1:8000`.
