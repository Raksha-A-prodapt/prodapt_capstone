# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()


# MODEL_NAME = "nvidia/nemotron-3-embed-1b:free"

# API_URL = "https://openrouter.ai/api/v1/embeddings"


# class OpenRouterEmbeddingModel:

#     def __init__(self):
#         self.api_key = os.getenv("OPENROUTER_API_KEY")

#         if not self.api_key:
#             raise ValueError(
#                 "OPENROUTER_API_KEY not found in .env"
#             )

#     def encode(
#         self,
#         texts,
#         batch_size=32,
#         show_progress_bar=False,
#         normalize_embeddings=True
#     ):
#         """
#         Same interface as SentenceTransformer.encode()
#         """

#         if isinstance(texts, str):
#             texts = [texts]

#         all_embeddings = []

#         for start in range(0, len(texts), batch_size):

#             batch = texts[start:start + batch_size]

#             headers = {
#                 "Authorization": f"Bearer {self.api_key}",
#                 "Content-Type": "application/json",
#             }

#             payload = {
#                 "model": MODEL_NAME,
#                 "input": batch,
#                 "encoding_format": "float",
#             }

#             # response = requests.post(
#             #     API_URL,
#             #     headers=headers,
#             #     json=payload,
#             #     timeout=120
#             # )
#             response = requests.post(
#     API_URL,
#     headers=headers,
#     json=payload,
#     timeout=120,
#     verify=False
# )

#             response.raise_for_status()

#             result = response.json()

#             # Sort by index to preserve input order
#             data = sorted(
#                 result["data"],
#                 key=lambda x: x["index"]
#             )

#             embeddings = [
#                 item["embedding"]
#                 for item in data
#             ]

#             all_embeddings.extend(embeddings)

#             if show_progress_bar:
#                 print(
#                     f"Embedded "
#                     f"{min(start + batch_size, len(texts))}"
#                     f"/{len(texts)}"
#                 )

#         # Optional normalization
#         if normalize_embeddings:
#             import numpy as np

#             embeddings_array = np.array(
#                 all_embeddings,
#                 dtype=np.float32
#             )

#             norms = np.linalg.norm(
#                 embeddings_array,
#                 axis=1,
#                 keepdims=True
#             )

#             norms[norms == 0] = 1

#             embeddings_array = (
#                 embeddings_array / norms
#             )

#             all_embeddings = embeddings_array

#         return all_embeddings


# def load_embedding_model():
#     """
#     Same function used by index.py
#     """

#     return OpenRouterEmbeddingModel()



from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"


class LocalEmbeddingModel:

    def __init__(self):
        print("=" * 60)
        print("Loading embedding model...")
        print("=" * 60)

        self.model = SentenceTransformer(MODEL_NAME)

        print(f"Model: {MODEL_NAME}")
        print("Embedding model loaded.")

    def encode(
        self,
        texts,
        batch_size=128,
        show_progress_bar=False,
        normalize_embeddings=True
    ):
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize_embeddings
        )


def load_embedding_model():
    return LocalEmbeddingModel()