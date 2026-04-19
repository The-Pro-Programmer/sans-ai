import faiss
import numpy as np

index = faiss.IndexFlatL2(384)

documents = []

def add_document(text, embedding, metadata):
    global documents
    documents.append({
        "text": text,
        "metadata": metadata
    })
    index.add(np.array([embedding]).astype("float32"))

def add_document(text, embedding):
    global documents
    documents.append(text)
    index.add(np.array([embedding]).astype("float32"))

def search(query_embedding, k=3):
    D, I = index.search(np.array([query_embedding]).astype("float32"), k)

    results = []
    for idx in I[0]:
        if idx < len(documents):
            results.append(documents[idx])

    return results