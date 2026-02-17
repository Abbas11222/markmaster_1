from sentence_transformers import SentenceTransformer
import hashlib

model = SentenceTransformer("all-MiniLM-L6-v2")
_cache = {}

def embed(texts):
    if isinstance(texts, str):
        texts = [texts]

    vectors = []
    for t in texts:
        key = hashlib.md5(t.encode()).hexdigest()
        if key not in _cache:
            _cache[key] = model.encode(t)
        vectors.append(_cache[key])

    return vectors
