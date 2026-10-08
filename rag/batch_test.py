# from embedding_model import load_embedding_model

# print("=" * 60)
# print("BATCH EMBEDDING TEST")
# print("=" * 60)

# model = load_embedding_model()

# texts = [
#     "Telecom network incident with high latency and packet loss.",
#     "Network experienced poor signal strength and dropped calls.",
#     "High alarm count and critical alarms were observed.",
#     "The network had good throughput and low latency.",
#     "Handover success rate was below normal levels.",
#     "A network issue was reported in the affected cell.",
#     "Authentication failures were detected.",
#     "The network experienced configuration changes.",
# ]

# print(f"Texts to embed: {len(texts)}")
# print()

# try:
#     embeddings = model.encode(
#         texts,
#         batch_size=4,
#         show_progress_bar=True,
#         normalize_embeddings=True
#     )

#     print()
#     print("=" * 60)
#     print("SUCCESS")
#     print("=" * 60)

#     print("Number of embeddings:", len(embeddings))
#     print("Embedding dimension:", len(embeddings[0]))

# except Exception as e:
#     print()
#     print("=" * 60)
#     print("FAILED")
#     print("=" * 60)
#     print(type(e).__name__)
#     print(e)


import time
from embedding_model import load_embedding_model

model = load_embedding_model()

texts = [
    "Telecom network incident with high latency and packet loss."
    for _ in range(100)
]

for batch_size in [8, 16, 32, 64, 128]:

    print("\n" + "=" * 50)
    print(f"Testing batch_size = {batch_size}")
    print("=" * 50)

    start = time.time()

    try:
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        elapsed = time.time() - start

        print(f"SUCCESS")
        print(f"Batch size      : {batch_size}")
        print(f"Time            : {elapsed:.2f} seconds")
        print(f"Embeddings      : {len(embeddings)}")
        print(f"Dimension       : {len(embeddings[0])}")

    except Exception as e:
        print(f"FAILED")
        print(f"Batch size      : {batch_size}")
        print(f"Error           : {e}")