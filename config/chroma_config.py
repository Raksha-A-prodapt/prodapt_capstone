import chromadb

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "telecom_incidents"


def get_chroma_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description":
                "Telecom historical incident embeddings"
        }
    )