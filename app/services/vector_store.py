import random

# Mocked in-memory vector store
class InMemoryVectorStore:
    def __init__(self):
        self.vectors = {}  # {chunk_id: vector}

    def add_vector(self, chunk_id: int, vector):
        self.vectors[chunk_id] = vector

    def get_vector(self, chunk_id: int):
        return self.vectors.get(chunk_id)

    def search(self, query_vector, top_k=5):
        # Mocked: just return first top_k chunk_ids
        return list(self.vectors.keys())[:top_k]

def mock_embedding(text: str):
    # Return a mock embedding (list of floats)
    random.seed(hash(text))
    return [random.random() for _ in range(8)]

vector_store = InMemoryVectorStore()
