from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(
    host="qdrant",
    port=6333,
)

client.recreate_collection(
    collection_name="article_chunks",
    vectors_config=VectorParams(
        size=1024,
        distance=Distance.COSINE,
    ),
)

print("Collection criada com sucesso!")
print(client.get_collections())