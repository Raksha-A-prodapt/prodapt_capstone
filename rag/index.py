# import json
# from pathlib import Path

# from embedding_model import load_embedding_model
# from chromadb_setup import get_chroma_collection


# # ============================================================
# # CONFIGURATION
# # ============================================================

# JSONL_FILE = "D:/raksha/capstone/try2/retieval_sematics/incident_documents.jsonl"

# BATCH_SIZE = 128


# # ============================================================
# # READ JSONL
# # ============================================================

# def read_jsonl(file_path):
#     """
#     Read incident documents from JSONL.

#     Each line represents one complete incident.
#     """

#     with open(
#         file_path,
#         "r",
#         encoding="utf-8"
#     ) as file:

#         for line in file:

#             line = line.strip()

#             if not line:
#                 continue

#             yield json.loads(line)


# # ============================================================
# # BUILD CHROMA INDEX
# # ============================================================

# def build_index():

#     jsonl_path = Path(JSONL_FILE)

#     if not jsonl_path.exists():
#         raise FileNotFoundError(
#             f"JSONL file not found: {jsonl_path}"
#         )

#     print("=" * 60)
#     print("Loading embedding model...")
#     print("=" * 60)

#     model = load_embedding_model()

#     print("Embedding model loaded.")

#     print()
#     print("=" * 60)
#     print("Connecting to ChromaDB...")
#     print("=" * 60)

#     collection = get_chroma_collection()

#     print(
#         f"Existing documents in collection: "
#         f"{collection.count()}"
#     )

#     # --------------------------------------------------------
#     # BATCH STORAGE
#     # --------------------------------------------------------

#     ids = []
#     documents = []
#     metadatas = []

#     total_processed = 0

#     for incident in read_jsonl(JSONL_FILE):

#         incident_id = incident["id"]
#         text = incident["text"]
#         metadata = incident["metadata"]

#         ids.append(incident_id)
#         documents.append(text)
#         metadatas.append(metadata)

#         # Process batch
#         if len(documents) >= BATCH_SIZE:

#             process_batch(
#                 model=model,
#                 collection=collection,
#                 ids=ids,
#                 documents=documents,
#                 metadatas=metadatas
#             )

#             total_processed += len(documents)

#             print(
#                 f"Processed: {total_processed}"
#             )

#             ids = []
#             documents = []
#             metadatas = []

#     # --------------------------------------------------------
#     # PROCESS REMAINING RECORDS
#     # --------------------------------------------------------

#     if documents:

#         process_batch(
#             model=model,
#             collection=collection,
#             ids=ids,
#             documents=documents,
#             metadatas=metadatas
#         )

#         total_processed += len(documents)

#         print(
#             f"Processed: {total_processed}"
#         )

#     print()
#     print("=" * 60)
#     print("INDEXING COMPLETED")
#     print("=" * 60)

#     print(
#         f"Total documents in ChromaDB: "
#         f"{collection.count()}"
#     )

#     print(
#         f"ChromaDB location: ./chroma_db"
#     )


# # ============================================================
# # PROCESS ONE BATCH
# # ============================================================

# def process_batch(
#     model,
#     collection,
#     ids,
#     documents,
#     metadatas
# ):
#     """
#     Generate embeddings for a batch and
#     insert them into ChromaDB.
#     """

#     # Generate embeddings locally
#     embeddings = model.encode(
#         documents,
#         batch_size=128,
#         show_progress_bar=False,
#         normalize_embeddings=True
#     )

#     # Convert numpy arrays to Python lists
#     embeddings = embeddings.tolist()

#     collection.upsert(
#         ids=ids,
#         documents=documents,
#         metadatas=metadatas,
#         embeddings=embeddings
#     )


# # ============================================================
# # MAIN
# # ============================================================

# if __name__ == "__main__":
#     build_index()


import json
import time
from pathlib import Path

from embedding_model import load_embedding_model
from chromadb_setup import get_chroma_collection


# ============================================================
# CONFIGURATION
# ============================================================

JSONL_FILE = "D:/raksha/capstone/try2/retieval_sematics/incident_documents.jsonl"

# Number of documents sent to ChromaDB in one upsert
CHROMA_BATCH_SIZE = 128

# Number of texts processed by SentenceTransformer at once
EMBEDDING_BATCH_SIZE = 128


# ============================================================
# READ JSONL
# ============================================================

def read_jsonl(file_path):
    """
    Read incident documents from JSONL file.
    Each line must contain:
        {
            "id": "...",
            "text": "...",
            "metadata": {...}
        }
    """

    with open(file_path, "r", encoding="utf-8") as file:

        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            if not line:
                continue

            try:
                yield json.loads(line)

            except json.JSONDecodeError as e:
                print(
                    f"WARNING: Invalid JSON on line {line_number}: {e}"
                )


# ============================================================
# PROCESS ONE BATCH
# ============================================================

def process_batch(
    model,
    collection,
    ids,
    documents,
    metadatas
):
    """
    Generate embeddings locally and store them in ChromaDB.
    """

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    embeddings = model.encode(
        documents,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True
    )

    # SentenceTransformer returns numpy array.
    # ChromaDB expects regular Python lists.
    embeddings = embeddings.tolist()

    # --------------------------------------------------------
    # Store in ChromaDB
    # --------------------------------------------------------

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )


# ============================================================
# BUILD INDEX
# ============================================================

def build_index():

    start_time = time.time()

    # --------------------------------------------------------
    # Check JSONL file
    # --------------------------------------------------------

    jsonl_path = Path(JSONL_FILE)

    if not jsonl_path.exists():

        raise FileNotFoundError(
            f"\nJSONL file not found:\n{jsonl_path}"
        )

    print("=" * 70)
    print("TELECOM INCIDENT VECTOR INDEXING")
    print("=" * 70)

    print(f"JSONL file : {jsonl_path}")
    print(f"Chroma batch size : {CHROMA_BATCH_SIZE}")
    print(f"Embedding batch size : {EMBEDDING_BATCH_SIZE}")
    print()

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------

    print("=" * 70)
    print("STEP 1: LOADING EMBEDDING MODEL")
    print("=" * 70)

    model = load_embedding_model()

    print()
    print("Embedding model ready.")
    print("Model: BAAI/bge-small-en-v1.5")
    print("Embedding dimension: 384")
    print()

    # --------------------------------------------------------
    # Connect to ChromaDB
    # --------------------------------------------------------

    print("=" * 70)
    print("STEP 2: CONNECTING TO CHROMADB")
    print("=" * 70)

    collection = get_chroma_collection()

    existing_count = collection.count()

    print(f"Existing documents in ChromaDB: {existing_count}")
    print()

    # --------------------------------------------------------
    # Prepare batch containers
    # --------------------------------------------------------

    ids = []
    documents = []
    metadatas = []

    total_processed = 0

    batch_number = 0

    indexing_start = time.time()

    # --------------------------------------------------------
    # Read JSONL and process batches
    # --------------------------------------------------------

    print("=" * 70)
    print("STEP 3: INDEXING INCIDENTS")
    print("=" * 70)

    for incident in read_jsonl(JSONL_FILE):

        # ----------------------------------------------------
        # Extract fields
        # ----------------------------------------------------

        incident_id = incident["id"]

        text = incident["text"]

        metadata = incident["metadata"]

        # ----------------------------------------------------
        # Add to current batch
        # ----------------------------------------------------

        ids.append(incident_id)

        documents.append(text)

        metadatas.append(metadata)

        # ----------------------------------------------------
        # Process when batch is full
        # ----------------------------------------------------

        if len(documents) >= CHROMA_BATCH_SIZE:

            batch_number += 1

            batch_start = time.time()

            process_batch(
                model=model,
                collection=collection,
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            batch_time = time.time() - batch_start

            total_processed += len(documents)

            print(
                f"Batch {batch_number:>4} | "
                f"Processed: {total_processed:>7} | "
                f"Batch size: {len(documents):>3} | "
                f"Time: {batch_time:>6.2f}s"
            )

            # ------------------------------------------------
            # Clear batch
            # ------------------------------------------------

            ids = []

            documents = []

            metadatas = []

    # --------------------------------------------------------
    # Process remaining documents
    # --------------------------------------------------------

    if documents:

        batch_number += 1

        batch_start = time.time()

        process_batch(
            model=model,
            collection=collection,
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        batch_time = time.time() - batch_start

        total_processed += len(documents)

        print(
            f"Batch {batch_number:>4} | "
            f"Processed: {total_processed:>7} | "
            f"Batch size: {len(documents):>3} | "
            f"Time: {batch_time:>6.2f}s"
        )

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    indexing_time = time.time() - indexing_start

    total_time = time.time() - start_time

    final_count = collection.count()

    print()
    print("=" * 70)
    print("INDEXING COMPLETED")
    print("=" * 70)

    print(f"Documents processed : {total_processed}")
    print(f"Documents in Chroma : {final_count}")
    print(f"Total batches       : {batch_number}")

    print(f"Indexing time       : {indexing_time / 60:.2f} minutes")
    print(f"Total runtime       : {total_time / 60:.2f} minutes")

    print()
    print("Embedding model     : BAAI/bge-small-en-v1.5")
    print("Embedding dimension : 384")
    print("Vector database     : ChromaDB")
    print("Collection          : telecom_incidents")

    print()
    print("ChromaDB location   : ./chroma_db")

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        build_index()

    except KeyboardInterrupt:

        print()
        print("=" * 70)
        print("INDEXING INTERRUPTED BY USER")
        print("=" * 70)

    except Exception as e:

        print()
        print("=" * 70)
        print("INDEXING FAILED")
        print("=" * 70)

        print(f"Error: {e}")

        raise