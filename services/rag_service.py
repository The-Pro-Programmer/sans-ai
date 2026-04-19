from engines.rag.embedder import get_embedding
from engines.rag.vector_store import add_document
from engines.rag.chunker import split_shlokas

def ingest_text(text: str, book="Unknown", chapter=0):

    chunks = split_shlokas(text)

    count = 0

    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()

        if not chunk:
            continue

        emb = get_embedding(chunk)

        metadata = {
            "book": book,
            "chapter": chapter,
            "verse": i + 1
        }

        add_document(chunk, emb, metadata)
        count += 1

    return {
        "status": "ingested",
        "chunks": count
    }