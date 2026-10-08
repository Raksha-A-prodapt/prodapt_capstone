import chromadb


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "telecom_incidents"


def get_chroma_collection():
    """
    Create/open a persistent ChromaDB collection.
    """

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Telecom historical incident embeddings"
        }
    )

    return collection