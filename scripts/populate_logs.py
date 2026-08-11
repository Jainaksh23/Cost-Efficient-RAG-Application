import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.routes import api_query
from api.schemas import QueryRequest
import storage.sqlite_store as sql_store
from embedding.embedder import embed

def populate():
    # Make sure DB and models are loaded
    sql_store.init_db()
    embed(["test"])
    
    questions_path = Path("eval/questions.jsonl")
    with open(questions_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                q = json.loads(line)
                req = QueryRequest(
                    question=q["question"],
                    filters=q.get("filters", {})
                )
                # Call api_query to trigger logging
                api_query(req)
                print(f"Processed: {q['id']}")

if __name__ == "__main__":
    populate()
