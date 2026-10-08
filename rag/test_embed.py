
# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# # --------------------------------------------------
# # Configuration
# # --------------------------------------------------

# API_URL = "https://openrouter.ai/api/v1/embeddings"
# MODEL_NAME = "nvidia/nemotron-3-embed-1b:free"

# API_KEY = os.getenv("OPENROUTER_API_KEY")

# # --------------------------------------------------
# # Check API key
# # --------------------------------------------------

# if not API_KEY:
#     raise ValueError(
#         "OPENROUTER_API_KEY not found. "
#         "Check your .env file."
#     )

# print("=" * 60)
# print("OPENROUTER EMBEDDING TEST")
# print("=" * 60)

# print(f"Model: {MODEL_NAME}")
# print("API key: Found")
# print()

# # --------------------------------------------------
# # Test text
# # --------------------------------------------------

# # test_text = (
# #     "Telecom network incident with high latency, "
# #     "packet loss, and poor signal strength."
# # )

# test_texts = [
#     "Telecom network incident with high latency and packet loss.",
#     "Network experienced poor signal strength and dropped calls.",
#     "High alarm count and critical alarms were observed.",
#     "The network had good throughput and low latency.",
#     "Handover success rate was below normal levels.",
#     "A network issue was reported in the affected cell.",
#     "Authentication failures were detected.",
#     "The network experienced configuration changes.",
# ]
# payload = {
#     "model": MODEL_NAME,
#     # "input": [test_text],
#     "input": test_texts,
#     "encoding_format": "float"
# }

# headers = {
#     "Authorization": f"Bearer {API_KEY}",
#     "Content-Type": "application/json"
# }

# # --------------------------------------------------
# # Send request
# # --------------------------------------------------

# print("Sending embedding request to OpenRouter...")
# print()

# try:

#     response = requests.post(
#         API_URL,
#         headers=headers,
#         json=payload,
#         timeout=120,
#         verify=False
#     )

#     print("HTTP Status:", response.status_code)
#     print()

#     # Print response for debugging
#     print("Response:")
#     print(response.text[:2000])
#     print()

#     # --------------------------------------------------
#     # Check response
#     # --------------------------------------------------

#     response.raise_for_status()

#     result = response.json()

#     if "data" not in result:
#         print("❌ No 'data' field found in response.")
#         exit()

#     embedding = result["data"][0]["embedding"]

#     print("=" * 60)
#     print("EMBEDDING SUCCESSFUL")
#     print("=" * 60)

#     print("Embedding type:", type(embedding))
#     print("Embedding dimension:", len(embedding))

#     print()
#     print("First 10 values:")
#     print(embedding[:10])

#     print()
#     print("✅ OpenRouter embedding API is working.")

# except requests.exceptions.Timeout:

#     print("=" * 60)
#     print("❌ REQUEST TIMEOUT")
#     print("=" * 60)

#     print(
#         "OpenRouter did not respond within 120 seconds."
#     )

# except requests.exceptions.SSLError as e:

#     print("=" * 60)
#     print("❌ SSL ERROR")
#     print("=" * 60)

#     print(e)

# except requests.exceptions.HTTPError as e:

#     print("=" * 60)
#     print("❌ HTTP/API ERROR")
#     print("=" * 60)

#     print(e)

# except Exception as e:

#     print("=" * 60)
#     print("❌ UNEXPECTED ERROR")
#     print("=" * 60)

#     print(type(e).__name__)
#     print(e)

from embedding_model import load_embedding_model


texts = [
    "Telecom network incident with high latency and packet loss.",
    "Network experienced poor signal strength and dropped calls.",
    "High alarm count and critical alarms were observed.",
    "The network had good throughput and low latency.",
    "Handover success rate was below normal levels."
]


print("=" * 60)
print("LOCAL EMBEDDING TEST")
print("=" * 60)

model = load_embedding_model()

embeddings = model.encode(
    texts,
    batch_size=5,
    show_progress_bar=True,
    normalize_embeddings=True
)

print()
print("=" * 60)
print("SUCCESS")
print("=" * 60)

print("Number of embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))