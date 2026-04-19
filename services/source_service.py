from engines.rag.embedder import get_embedding
from engines.rag.vector_store import search

def find_source(text: str):

    emb = get_embedding(text)
    results = search(emb)

    formatted = []

    for r in results:
        formatted.append({
            "text": r["text"],
            "book": r["metadata"]["book"],
            "chapter": r["metadata"]["chapter"],
            "verse": r["metadata"]["verse"]
        })

    return {
        "matches": formatted
    }