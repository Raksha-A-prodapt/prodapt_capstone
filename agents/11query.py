# import re
# import numpy as np
# import pandas as pd
# import chromadb

# from rank_bm25 import BM25Okapi
# from sentence_transformers import SentenceTransformer

# from config import (
#     CSV_PATH,
#     CHROMA_PATH,
#     CHROMA_COLLECTION_NAME,
#     EMBEDDING_MODEL,
#     DEFAULT_TOP_K,
#     SEMANTIC_WEIGHT,
#     BM25_WEIGHT,
# )


# class QueryAgent:

#     def __init__(self):

#         print("Loading incident dataset...")

#         self.df = pd.read_csv(CSV_PATH)

#         # Normalize column names
#         self.df.columns = [
#             str(col).strip().lower().replace(" ", "_")
#             for col in self.df.columns
#         ]

#         print(f"Loaded {len(self.df)} incidents")

#         # -----------------------------
#         # Load embedding model
#         # -----------------------------

#         print("Loading embedding model...")

#         self.embedding_model = SentenceTransformer(
#             EMBEDDING_MODEL
#         )

#         # -----------------------------
#         # Load ChromaDB
#         # -----------------------------

#         print("Connecting to ChromaDB...")

#         self.chroma_client = chromadb.PersistentClient(
#             path=CHROMA_PATH
#         )

#         self.collection = self.chroma_client.get_collection(
#             name=CHROMA_COLLECTION_NAME
#         )

#         print(
#             f"Chroma collection loaded: "
#             f"{self.collection.name}"
#         )

#         # -----------------------------
#         # BM25 corpus
#         # -----------------------------

#         self.documents = self._build_documents()

#         tokenized_documents = [
#             self._tokenize(text)
#             for text in self.documents
#         ]

#         self.bm25 = BM25Okapi(
#             tokenized_documents
#         )

#         print("BM25 index ready.")

#     # =====================================================
#     # DOCUMENT CREATION
#     # =====================================================

#     def _build_documents(self):

#         documents = []

#         for _, row in self.df.iterrows():

#             parts = []

#             for column, value in row.items():

#                 if pd.isna(value):
#                     continue

#                 parts.append(
#                     f"{column}: {value}"
#                 )

#             documents.append(
#                 " | ".join(parts)
#             )

#         return documents

#     # =====================================================
#     # TOKENIZER
#     # =====================================================

#     def _tokenize(self, text):

#         text = str(text).lower()

#         tokens = re.findall(
#             r"\b[a-zA-Z0-9_.%-]+\b",
#             text
#         )

#         return tokens

#     # =====================================================
#     # QUERY UNDERSTANDING
#     # =====================================================

#     def understand_query(self, query):

#         query_lower = query.lower()

#         filters = {}

#         # -----------------------------
#         # State
#         # -----------------------------

#         states = [
#             "tamil nadu",
#             "kerala",
#             "karnataka",
#             "maharashtra",
#             "delhi",
#             "telangana",
#             "andhra pradesh",
#             "uttar pradesh",
#             "west bengal",
#             "gujarat",
#             "rajasthan",
#         ]

#         for state in states:

#             if state in query_lower:

#                 filters["state"] = state
#                 break

#         # -----------------------------
#         # Major cities
#         # -----------------------------

#         cities = [
#             "chennai",
#             "bangalore",
#             "bengaluru",
#             "mumbai",
#             "delhi",
#             "hyderabad",
#             "kolkata",
#             "pune",
#             "ahmedabad",
#             "jaipur",
#             "kochi",
#         ]

#         for city in cities:

#             if city in query_lower:

#                 filters["city"] = city
#                 break

#         # -----------------------------
#         # Season
#         # -----------------------------

#         seasons = [
#             "summer",
#             "winter",
#             "monsoon",
#             "spring",
#             "autumn",
#             "fall",
#         ]

#         for season in seasons:

#             if season in query_lower:

#                 filters["season"] = season
#                 break

#         # -----------------------------
#         # Network conditions
#         # -----------------------------

#         conditions = [
#             "high latency",
#             "low latency",
#             "packet loss",
#             "network congestion",
#             "congestion",
#             "dropped calls",
#             "poor signal",
#             "weak signal",
#             "handover failure",
#             "service degradation",
#             "network fault",
#         ]

#         detected_conditions = []

#         for condition in conditions:

#             if condition in query_lower:

#                 detected_conditions.append(
#                     condition
#                 )

#         if detected_conditions:

#             filters["network_conditions"] = (
#                 detected_conditions
#             )

#         return {
#             "original_query": query,
#             "semantic_query": query,
#             "filters": filters,
#             "keywords": self._tokenize(query),
#         }

#     # =====================================================
#     # METADATA FILTERING
#     # =====================================================

#     def apply_metadata_filter(
#         self,
#         filters
#     ):

#         filtered_df = self.df.copy()

#         for key, value in filters.items():

#             if key == "network_conditions":
#                 continue

#             if key not in filtered_df.columns:
#                 continue

#             filtered_df = filtered_df[
#                 filtered_df[key]
#                 .astype(str)
#                 .str.lower()
#                 .str.contains(
#                     str(value).lower(),
#                     na=False
#                 )
#             ]

#         return filtered_df

#     # =====================================================
#     # BM25 SEARCH
#     # =====================================================

#     def bm25_search(
#         self,
#         query,
#         filtered_df,
#         top_k
#     ):

#         if len(filtered_df) == 0:

#             return []

#         query_tokens = self._tokenize(query)

#         scores = self.bm25.get_scores(
#             query_tokens
#         )

#         # Map dataframe rows back to original indices
#         valid_indices = filtered_df.index.tolist()

#         ranked = sorted(
#             [
#                 (
#                     idx,
#                     scores[idx]
#                 )
#                 for idx in valid_indices
#             ],
#             key=lambda x: x[1],
#             reverse=True
#         )

#         ranked = ranked[:top_k]

#         results = []

#         for idx, score in ranked:

#             row = self.df.loc[idx]

#             results.append({
#                 "index": int(idx),
#                 "bm25_score": float(score),
#                 "record": row.to_dict()
#             })

#         return results

#     # =====================================================
#     # CHROMADB SEARCH
#     # =====================================================

#     def semantic_search(
#         self,
#         query,
#         filters,
#         top_k
#     ):

#         embedding = self.embedding_model.encode(
#             query,
#             normalize_embeddings=True
#         ).tolist()

#         # Build Chroma metadata filter
#         where = {}

#         for key, value in filters.items():

#             if key == "network_conditions":
#                 continue

#             where[key] = value

#         search_kwargs = {
#             "query_embeddings": [embedding],
#             "n_results": top_k,
#         }

#         if where:
#             search_kwargs["where"] = where

#         try:

#             result = self.collection.query(
#                 **search_kwargs
#             )

#         except Exception as e:

#             print(
#                 "Chroma metadata filtering failed:",
#                 e
#             )

#             # fallback without metadata filter
#             result = self.collection.query(
#                 query_embeddings=[embedding],
#                 n_results=top_k
#             )

#         results = []

#         ids = result.get("ids", [[]])[0]

#         distances = result.get(
#             "distances",
#             [[]]
#         )[0]

#         metadatas = result.get(
#             "metadatas",
#             [[]]
#         )[0]

#         documents = result.get(
#             "documents",
#             [[]]
#         )[0]

#         for i, incident_id in enumerate(ids):

#             distance = (
#                 distances[i]
#                 if i < len(distances)
#                 else 1.0
#             )

#             # Chroma distance -> similarity
#             semantic_score = 1 / (
#                 1 + float(distance)
#             )

#             results.append({

#                 "id": incident_id,

#                 "semantic_score":
#                     semantic_score,

#                 "distance":
#                     float(distance),

#                 "metadata":
#                     metadatas[i]
#                     if i < len(metadatas)
#                     else {},

#                 "document":
#                     documents[i]
#                     if i < len(documents)
#                     else ""
#             })

#         return results

#     # =====================================================
#     # NORMALIZE SCORES
#     # =====================================================

#     def normalize_scores(
#         self,
#         scores
#     ):

#         if not scores:
#             return {}

#         values = np.array(
#             list(scores.values()),
#             dtype=float
#         )

#         min_value = values.min()
#         max_value = values.max()

#         if max_value == min_value:

#             return {
#                 key: 1.0
#                 for key in scores
#             }

#         return {
#             key:
#             (value - min_value)
#             / (max_value - min_value)

#             for key, value
#             in scores.items()
#         }

#     # =====================================================
#     # HYBRID SEARCH
#     # =====================================================

#     def hybrid_search(
#         self,
#         query,
#         filters,
#         top_k=DEFAULT_TOP_K
#     ):

#         # --------------------------------
#         # Metadata filtering
#         # --------------------------------

#         filtered_df = self.apply_metadata_filter(
#             filters
#         )

#         # --------------------------------
#         # BM25
#         # --------------------------------

#         bm25_results = self.bm25_search(
#             query,
#             filtered_df,
#             top_k * 3
#         )

#         bm25_scores = {
#             str(item["index"]):
#             item["bm25_score"]

#             for item in bm25_results
#         }

#         bm25_scores = self.normalize_scores(
#             bm25_scores
#         )

#         # --------------------------------
#         # Semantic
#         # --------------------------------

#         semantic_results = self.semantic_search(
#             query,
#             filters,
#             top_k * 3
#         )

#         semantic_scores = {}

#         for item in semantic_results:

#             incident_id = str(
#                 item["id"]
#             )

#             semantic_scores[
#                 incident_id
#             ] = item["semantic_score"]

#         semantic_scores = self.normalize_scores(
#             semantic_scores
#         )

#         # --------------------------------
#         # Fusion
#         # --------------------------------

#         combined = {}

#         # BM25
#         for incident_id, score in bm25_scores.items():

#             combined.setdefault(
#                 incident_id,
#                 {}
#             )

#             combined[
#                 incident_id
#             ]["bm25"] = score

#         # Semantic
#         for incident_id, score in semantic_scores.items():

#             combined.setdefault(
#                 incident_id,
#                 {}
#             )

#             combined[
#                 incident_id
#             ]["semantic"] = score

#         # --------------------------------
#         # Hybrid score
#         # --------------------------------

#         ranked = []

#         for incident_id, scores in combined.items():

#             bm25_score = scores.get(
#                 "bm25",
#                 0.0
#             )

#             semantic_score = scores.get(
#                 "semantic",
#                 0.0
#             )

#             hybrid_score = (
#                 BM25_WEIGHT * bm25_score
#                 +
#                 SEMANTIC_WEIGHT *
#                 semantic_score
#             )

#             ranked.append({

#                 "incident_id":
#                     incident_id,

#                 "bm25_score":
#                     round(
#                         bm25_score,
#                         4
#                     ),

#                 "semantic_score":
#                     round(
#                         semantic_score,
#                         4
#                     ),

#                 "hybrid_score":
#                     round(
#                         hybrid_score,
#                         4
#                     )
#             })

#         ranked.sort(
#             key=lambda x:
#                 x["hybrid_score"],
#             reverse=True
#         )

#         # --------------------------------
#         # Attach actual records
#         # --------------------------------

#         final_results = []

#         for item in ranked[:top_k]:

#             incident_id = item[
#                 "incident_id"
#             ]

#             # Try dataframe index
#             try:

#                 idx = int(
#                     incident_id
#                 )

#                 if idx in self.df.index:

#                     record = self.df.loc[
#                         idx
#                     ].to_dict()

#                 else:

#                     record = {}

#             except:

#                 record = {}

#             item["record"] = record

#             final_results.append(
#                 item
#             )

#         return final_results

#     # =====================================================
#     # MAIN QUERY METHOD
#     # =====================================================

#     def run(
#         self,
#         query,
#         top_k=DEFAULT_TOP_K
#     ):

#         if not query or not query.strip():

#             raise ValueError(
#                 "Query cannot be empty."
#             )

#         # -----------------------------
#         # Understand query
#         # -----------------------------

#         query_info = self.understand_query(
#             query
#         )

#         # -----------------------------
#         # Retrieve
#         # -----------------------------

#         results = self.hybrid_search(
#             query=query,
#             filters=query_info["filters"],
#             top_k=top_k
#         )

#         return {
#             "query": query,
#             "query_understanding": query_info,
#             "results": results,
#             "result_count": len(results)
#         }


# # =========================================================
# # TEST
# # =========================================================

# if __name__ == "__main__":

#     agent = QueryAgent()

#     query = (
#         "Show previous incidents in Chennai "
#         "during summer with high latency "
#         "and packet loss"
#     )

#     result = agent.run(
#         query,
#         top_k=5
#     )

#     print("\nQUERY:")
#     print(result["query"])

#     print("\nFILTERS:")
#     print(
#         result[
#             "query_understanding"
#         ]["filters"]
#     )

#     print("\nRESULTS:")

#     for item in result["results"]:

#         print(
#             "\nIncident:",
#             item["incident_id"]
#         )

#         print(
#             "BM25:",
#             item["bm25_score"]
#         )

#         print(
#             "Semantic:",
#             item["semantic_score"]
#         )

#         print(
#             "Hybrid:",
#             item["hybrid_score"]
#         )

#         print(
#             "Record:",
#             item["record"]
#         )



# """
# Query Agent
# ===========

# Purpose
# -------
# Converts a natural-language telecom query into a structured retrieval plan
# and retrieves relevant historical incidents using:

# 1. LLM-based query parsing
# 2. Metadata filtering
# 3. Numeric condition filtering
# 4. BM25 lexical retrieval
# 5. ChromaDB semantic retrieval
# 6. Hybrid ranking

# Designed to be called later by a multi-agent orchestrator.

# Important:
# - ChromaDB already contains embeddings.
# - This file does NOT rebuild embeddings.
# - Incident_ID is the canonical identifier everywhere.
# """

# import os
# import re
# import json
# from typing import Any, Dict, List, Optional, Literal

# import chromadb
# import numpy as np
# import pandas as pd

# from rank_bm25 import BM25Okapi
# from sentence_transformers import SentenceTransformer

# from dotenv import load_dotenv
# from openai import OpenAI

# from pydantic import BaseModel, Field


# # ============================================================
# # LOAD ENVIRONMENT
# # ============================================================

# load_dotenv()

# from pathlib import Path

# # ============================================================
# # CONFIGURATION
# # ============================================================
# BASE_DIR = Path(__file__).resolve().parent.parent

# DATA_DIR = BASE_DIR / "data"
# RAG_DIR = BASE_DIR / "rag"


# CSV_PATH = DATA_DIR / "telecom_network_incidents_with_id"
# CHROMA_PATH = RAG_DIR / "chromadb" 

# ENV_PATH = BASE_DIR / ".env"

# load_dotenv(ENV_PATH)


# CSV_PATH = os.getenv(
#     "CSV_PATH",
#     "./data/telecom_incidents.csv"
# )

# CHROMA_PATH = os.getenv(
#     "CHROMA_PATH",
#     "./chroma_db"
# )

# CHROMA_COLLECTION_NAME = os.getenv(
#     "CHROMA_COLLECTION_NAME",
#     "telecom_incidents"
# )

# EMBEDDING_MODEL = os.getenv(
#     "EMBEDDING_MODEL",
#     "all-MiniLM-L6-v2"
# )

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OPENROUTER_MODEL = os.getenv(
#     "OPENROUTER_MODEL",
#     "openai/gpt-4o-mini"
# )

# DEFAULT_TOP_K = int(
#     os.getenv("DEFAULT_TOP_K", "5")
# )

# BM25_WEIGHT = float(
#     os.getenv("BM25_WEIGHT", "0.4")
# )

# SEMANTIC_WEIGHT = float(
#     os.getenv("SEMANTIC_WEIGHT", "0.6")
# )

# RETRIEVAL_MULTIPLIER = int(
#     os.getenv("RETRIEVAL_MULTIPLIER", "5")
# )


# # ============================================================
# # FIELD DEFINITIONS
# # ============================================================

# METADATA_FIELDS = [
#     "incident_id",
#     "city",
#     "state",
#     "zip",
#     "season",
#     "weather",
#     "issue_reported",
# ]


# NUMERIC_FIELDS = [
#     "cell_availability",
#     "mttr_hours",
#     "throughput_mbps",
#     "latency_ms",
#     "packet_loss_rate",
#     "call_drop_rate",
#     "handover_success_rate",
#     "alarm_count",
#     "critical_alarm_count",
#     "parameter_changes",
#     "successful_configuration_changes",
#     "data_usage_gb",
#     "user_count",
#     "signal_strength_dbm",
#     "jitter_ms",
#     "connection_setup_success_rate",
#     "security_incidents",
#     "authentication_failures",
#     "temperature_c",
#     "humidity_percent",
#     "fault_occurrence_rate",
# ]


# # ============================================================
# # HUMAN-FRIENDLY METRIC ALIASES
# # ============================================================

# FIELD_ALIASES = {

#     "latency": "latency_ms",
#     "delay": "latency_ms",

#     "packet loss": "packet_loss_rate",
#     "packet loss rate": "packet_loss_rate",

#     "call drops": "call_drop_rate",
#     "dropped calls": "call_drop_rate",
#     "call drop": "call_drop_rate",

#     "signal": "signal_strength_dbm",
#     "signal strength": "signal_strength_dbm",
#     "poor signal": "signal_strength_dbm",

#     "jitter": "jitter_ms",

#     "throughput": "throughput_mbps",

#     "availability": "cell_availability",
#     "cell availability": "cell_availability",

#     "mttr": "mttr_hours",
#     "repair time": "mttr_hours",
#     "mean time to repair": "mttr_hours",

#     "handover": "handover_success_rate",
#     "handover success": "handover_success_rate",

#     "alarms": "alarm_count",
#     "alarm count": "alarm_count",

#     "critical alarms": "critical_alarm_count",

#     "parameter changes": "parameter_changes",

#     "configuration success":
#         "successful_configuration_changes",

#     "data usage": "data_usage_gb",

#     "users": "user_count",
#     "user count": "user_count",

#     "connection setup":
#         "connection_setup_success_rate",

#     "security incidents":
#         "security_incidents",

#     "authentication failures":
#         "authentication_failures",

#     "temperature":
#         "temperature_c",

#     "humidity":
#         "humidity_percent",

#     "fault occurrence":
#         "fault_occurrence_rate",
# }


# # ============================================================
# # QUERY PLAN SCHEMA
# # ============================================================

# class NumericCondition(BaseModel):

#     field: str

#     operator: Literal[
#         ">",
#         ">=",
#         "<",
#         "<=",
#         "="
#     ]

#     value: float


# class QueryPlan(BaseModel):

#     metadata_filters: Dict[str, Any] = Field(
#         default_factory=dict
#     )

#     numeric_conditions: List[NumericCondition] = Field(
#         default_factory=list
#     )

#     search_query: str = ""

#     top_k: int = DEFAULT_TOP_K


# # ============================================================
# # QUERY AGENT
# # ============================================================

# class QueryAgent:

#     def __init__(
#         self,
#         csv_path: str = CSV_PATH,
#         chroma_path: str = CHROMA_PATH,
#         collection_name: str = CHROMA_COLLECTION_NAME,
#         embedding_model: str = EMBEDDING_MODEL,
#     ):

#         print("Initializing Query Agent...")

#         # ----------------------------------------------------
#         # Load CSV
#         # ----------------------------------------------------

#         self.df = pd.read_csv(csv_path)

#         self._normalize_dataframe()

#         # ----------------------------------------------------
#         # Build lookup by Incident ID
#         # ----------------------------------------------------

#         self.df_by_incident = {
#             str(row["incident_id"]): row.to_dict()
#             for _, row in self.df.iterrows()
#         }

#         # ----------------------------------------------------
#         # Load embedding model
#         # ----------------------------------------------------

#         self.embedding_model = SentenceTransformer(
#             embedding_model
#         )

#         # ----------------------------------------------------
#         # Connect Chroma
#         # ----------------------------------------------------

#         self.chroma_client = chromadb.PersistentClient(
#             path=chroma_path
#         )

#         self.collection = (
#             self.chroma_client.get_collection(
#                 name=collection_name
#             )
#         )

#         # ----------------------------------------------------
#         # Build BM25
#         # ----------------------------------------------------

#         self._build_bm25()

#         # ----------------------------------------------------
#         # Metadata values
#         # ----------------------------------------------------

#         self.metadata_values = {}

#         for field in METADATA_FIELDS:

#             if field in self.df.columns:

#                 values = (
#                     self.df[field]
#                     .dropna()
#                     .astype(str)
#                     .str.lower()
#                     .unique()
#                     .tolist()
#                 )

#                 self.metadata_values[field] = values

#         # ----------------------------------------------------
#         # OpenRouter client
#         # ----------------------------------------------------

#         self.llm_client = None

#         if OPENROUTER_API_KEY:

#             self.llm_client = OpenAI(
#                 api_key=OPENROUTER_API_KEY,
#                 base_url="https://openrouter.ai/api/v1"
#             )

#         print("Query Agent ready.")

#     # ========================================================
#     # DATAFRAME NORMALIZATION
#     # ========================================================

#     def _normalize_dataframe(self):

#         rename_map = {

#             "Incident_ID": "incident_id",

#             "Season": "season",

#             "Cell Availability (%)":
#                 "cell_availability",

#             "MTTR (hours)":
#                 "mttr_hours",

#             "Throughput (Mbps)":
#                 "throughput_mbps",

#             "Latency (ms)":
#                 "latency_ms",

#             "Packet Loss Rate (%)":
#                 "packet_loss_rate",

#             "Call Drop Rate (%)":
#                 "call_drop_rate",

#             "Handover Success Rate (%)":
#                 "handover_success_rate",

#             "Alarm Count":
#                 "alarm_count",

#             "Critical Alarm Count":
#                 "critical_alarm_count",

#             "Parameter Changes":
#                 "parameter_changes",

#             "Successful Configuration Changes (%)":
#                 "successful_configuration_changes",

#             "Data Usage (GB)":
#                 "data_usage_gb",

#             "User Count":
#                 "user_count",

#             "Signal Strength (dBm)":
#                 "signal_strength_dbm",

#             "Jitter (ms)":
#                 "jitter_ms",

#             "Connection Setup Success Rate (%)":
#                 "connection_setup_success_rate",

#             "Security Incidents":
#                 "security_incidents",

#             "Authentication Failures":
#                 "authentication_failures",

#             "Temperature (°C)":
#                 "temperature_c",

#             "Humidity (%)":
#                 "humidity_percent",

#             "Weather":
#                 "weather",

#             "Issue Reported":
#                 "issue_reported",

#             "City":
#                 "city",

#             "State":
#                 "state",

#             "Zip":
#                 "zip",

#             "Fault Occurrence Rate (%)":
#                 "fault_occurrence_rate",
#         }

#         self.df.rename(
#             columns=rename_map,
#             inplace=True
#         )

#         # Normalize categorical values

#         for column in [
#             "city",
#             "state",
#             "season",
#             "weather",
#             "issue_reported",
#         ]:

#             if column in self.df.columns:

#                 self.df[column] = (
#                     self.df[column]
#                     .astype(str)
#                     .str.strip()
#                 )

#         # Normalize Incident ID

#         self.df["incident_id"] = (
#             self.df["incident_id"]
#             .astype(str)
#             .str.strip()
#         )

#     # ========================================================
#     # BM25 INDEX
#     # ========================================================

#     def _build_bm25(self):

#         self.bm25_incident_ids = []

#         corpus = []

#         for _, row in self.df.iterrows():

#             incident_id = str(
#                 row["incident_id"]
#             )

#             text_parts = []

#             for column in self.df.columns:

#                 value = row[column]

#                 if pd.isna(value):
#                     continue

#                 text_parts.append(
#                     f"{column} {value}"
#                 )

#             text = " ".join(text_parts)

#             tokens = self._tokenize(text)

#             corpus.append(tokens)

#             self.bm25_incident_ids.append(
#                 incident_id
#             )

#         self.bm25 = BM25Okapi(corpus)

#     # ========================================================
#     # TOKENIZER
#     # ========================================================

#     @staticmethod
#     def _tokenize(text: str):

#         return re.findall(
#             r"\b[a-zA-Z0-9_.%-]+\b",
#             text.lower()
#         )

#     # ========================================================
#     # LLM QUERY PARSER
#     # ========================================================

#     def parse_query(
#         self,
#         query: str,
#         top_k: int = DEFAULT_TOP_K,
#     ) -> QueryPlan:

#         # ----------------------------------------------------
#         # No LLM available
#         # ----------------------------------------------------

#         if not self.llm_client:

#             return self._fallback_parser(
#                 query,
#                 top_k
#             )

#         system_prompt = f"""
# You are the query parser for a telecom network
# incident retrieval system.

# Your job is ONLY to convert a user's natural-language
# query into a structured retrieval plan.

# You MUST NOT answer the user's question.

# Available exact metadata fields:

# {json.dumps(METADATA_FIELDS, indent=2)}

# Available numeric fields:

# {json.dumps(NUMERIC_FIELDS, indent=2)}

# Field aliases:

# {json.dumps(FIELD_ALIASES, indent=2)}

# Rules:

# 1. Exact location/time/category constraints go into
#    metadata_filters.

# 2. Numeric requirements go into numeric_conditions.

# 3. Network concepts that are better handled by semantic
#    or lexical retrieval go into search_query.

# 4. NEVER invent a field.

# 5. NEVER invent a metadata value.

# 6. Use the exact field names provided above.

# 7. If the user says "high latency", map it to
#    latency_ms rather than inventing "high_latency".

# 8. If the user says "poor signal", map it to
#    signal_strength_dbm.

# 9. If the query does not provide an exact numeric
#    threshold, you may use a reasonable condition only
#    when the meaning is clear. Otherwise put the concept
#    into search_query.

# 10. Keep search_query concise and meaningful.

# 11. Do not put generic words such as:
#     "show", "give", "find", "incidents", "previous"
#     into search_query unless they add retrieval meaning.

# 12. The output MUST be valid JSON.

# Return exactly:

# {{
#     "metadata_filters": {{}},
#     "numeric_conditions": [],
#     "search_query": "",
#     "top_k": {top_k}
# }}
# """

#         try:

#             response = self.llm_client.chat.completions.create(

#                 model=OPENROUTER_MODEL,

#                 temperature=0,

#                 messages=[
#                     {
#                         "role": "system",
#                         "content": system_prompt,
#                     },
#                     {
#                         "role": "user",
#                         "content": query,
#                     },
#                 ],
#             )

#             content = (
#                 response
#                 .choices[0]
#                 .message
#                 .content
#             )

#             content = self._clean_json_response(
#                 content
#             )

#             data = json.loads(content)

#             plan = QueryPlan.model_validate(
#                 data
#             )

#             return self._validate_query_plan(
#                 plan,
#                 query
#             )

#         except Exception as e:

#             print(
#                 f"[Query Parser] LLM parsing failed: {e}"
#             )

#             return self._fallback_parser(
#                 query,
#                 top_k
#             )

#     # ========================================================
#     # CLEAN LLM JSON
#     # ========================================================

#     @staticmethod
#     def _clean_json_response(
#         content: str
#     ):

#         content = content.strip()

#         if content.startswith("```"):

#             content = re.sub(
#                 r"^```(?:json)?",
#                 "",
#                 content,
#                 flags=re.IGNORECASE
#             )

#             content = re.sub(
#                 r"```$",
#                 "",
#                 content
#             )

#         return content.strip()

#     # ========================================================
#     # VALIDATE QUERY PLAN
#     # ========================================================

#     def _validate_query_plan(
#         self,
#         plan: QueryPlan,
#         original_query: str,
#     ) -> QueryPlan:

#         # ----------------------------------------------------
#         # Validate metadata fields
#         # ----------------------------------------------------

#         valid_metadata = {}

#         for field, value in (
#             plan.metadata_filters.items()
#         ):

#             if field not in METADATA_FIELDS:
#                 continue

#             valid_metadata[field] = value

#         plan.metadata_filters = valid_metadata

#         # ----------------------------------------------------
#         # Validate numeric conditions
#         # ----------------------------------------------------

#         valid_conditions = []

#         for condition in plan.numeric_conditions:

#             if condition.field not in NUMERIC_FIELDS:
#                 continue

#             valid_conditions.append(
#                 condition
#             )

#         plan.numeric_conditions = (
#             valid_conditions
#         )

#         # ----------------------------------------------------
#         # Validate metadata values against dataset
#         # ----------------------------------------------------

#         validated_metadata = {}

#         for field, value in (
#             plan.metadata_filters.items()
#         ):

#             if field not in self.metadata_values:
#                 continue

#             value_string = str(value).lower().strip()

#             allowed_values = (
#                 self.metadata_values[field]
#             )

#             # Exact match

#             if value_string in allowed_values:

#                 validated_metadata[field] = (
#                     value_string
#                 )

#         plan.metadata_filters = (
#             validated_metadata
#         )

#         # ----------------------------------------------------
#         # Normalize search query
#         # ----------------------------------------------------

#         plan.search_query = (
#             plan.search_query
#             .strip()
#         )

#         if not plan.search_query:

#             plan.search_query = (
#                 original_query
#             )

#         return plan

#     # ========================================================
#     # FALLBACK PARSER
#     # ========================================================

#     def _fallback_parser(
#         self,
#         query: str,
#         top_k: int,
#     ) -> QueryPlan:

#         """
#         Deterministic fallback.

#         This is NOT the primary parser.

#         It exists so the Query Agent continues working
#         if OpenRouter/LLM is unavailable.
#         """

#         query_lower = query.lower()

#         metadata_filters = {}

#         # ----------------------------------------------------
#         # Detect known metadata values
#         # ----------------------------------------------------

#         for field, values in (
#             self.metadata_values.items()
#         ):

#             # longest first prevents partial collisions

#             sorted_values = sorted(
#                 values,
#                 key=len,
#                 reverse=True
#             )

#             for value in sorted_values:

#                 if value in query_lower:

#                     metadata_filters[field] = (
#                         value
#                     )

#                     break

#         # ----------------------------------------------------
#         # Remove metadata values from search text
#         # ----------------------------------------------------

#         search_query = query_lower

#         for field, value in (
#             metadata_filters.items()
#         ):

#             search_query = (
#                 search_query
#                 .replace(
#                     str(value).lower(),
#                     ""
#                 )
#             )

#         # ----------------------------------------------------
#         # Remove generic words
#         # ----------------------------------------------------

#         stop_words = {

#             "show",
#             "give",
#             "find",
#             "get",
#             "retrieve",
#             "previous",
#             "historical",
#             "incidents",
#             "incident",
#             "records",
#             "network",
#             "in",
#             "during",
#             "from",
#             "with",
#             "where",
#             "the",
#             "for",
#             "me",
#         }

#         tokens = self._tokenize(
#             search_query
#         )

#         tokens = [
#             token
#             for token in tokens
#             if token not in stop_words
#         ]

#         search_query = " ".join(tokens)

#         return QueryPlan(
#             metadata_filters=metadata_filters,
#             numeric_conditions=[],
#             search_query=search_query,
#             top_k=top_k,
#         )

#     # ========================================================
#     # BUILD CANDIDATE IDS FROM METADATA
#     # ========================================================

#     def get_metadata_candidates(
#         self,
#         metadata_filters: Dict[str, Any],
#     ) -> List[str]:

#         if not metadata_filters:

#             return self.df[
#                 "incident_id"
#             ].astype(str).tolist()

#         mask = pd.Series(
#             True,
#             index=self.df.index
#         )

#         for field, value in (
#             metadata_filters.items()
#         ):

#             if field not in self.df.columns:
#                 continue

#             mask &= (
#                 self.df[field]
#                 .astype(str)
#                 .str.lower()
#                 ==
#                 str(value).lower()
#             )

#         return (
#             self.df.loc[
#                 mask,
#                 "incident_id"
#             ]
#             .astype(str)
#             .tolist()
#         )

#     # ========================================================
#     # APPLY NUMERIC CONDITIONS
#     # ========================================================

#     def apply_numeric_conditions(
#         self,
#         candidate_ids: List[str],
#         conditions: List[NumericCondition],
#     ) -> List[str]:

#         if not conditions:
#             return candidate_ids

#         if not candidate_ids:
#             return []

#         candidate_df = self.df[
#             self.df["incident_id"]
#             .astype(str)
#             .isin(candidate_ids)
#         ].copy()

#         mask = pd.Series(
#             True,
#             index=candidate_df.index
#         )

#         for condition in conditions:

#             field = condition.field

#             if field not in candidate_df.columns:
#                 continue

#             values = pd.to_numeric(
#                 candidate_df[field],
#                 errors="coerce"
#             )

#             value = condition.value

#             if condition.operator == ">":

#                 mask &= values > value

#             elif condition.operator == ">=":

#                 mask &= values >= value

#             elif condition.operator == "<":

#                 mask &= values < value

#             elif condition.operator == "<=":

#                 mask &= values <= value

#             elif condition.operator == "=":

#                 mask &= np.isclose(
#                     values,
#                     value
#                 )

#         return (
#             candidate_df.loc[
#                 mask,
#                 "incident_id"
#             ]
#             .astype(str)
#             .tolist()
#         )

#     # ========================================================
#     # BUILD CHROMA WHERE
#     # ========================================================

#     def build_chroma_where(
#         self,
#         metadata_filters: Dict[str, Any],
#     ):

#         if not metadata_filters:

#             return None

#         conditions = []

#         for field, value in (
#             metadata_filters.items()
#         ):

#             conditions.append(
#                 {
#                     field: str(value).lower()
#                 }
#             )

#         if len(conditions) == 1:

#             return conditions[0]

#         return {
#             "$and": conditions
#         }

#     # ========================================================
#     # SEMANTIC SEARCH
#     # ========================================================

#     def semantic_search(
#         self,
#         search_query: str,
#         metadata_filters: Dict[str, Any],
#         top_k: int,
#     ) -> Dict[str, float]:

#         if not search_query.strip():

#             return {}

#         query_embedding = (
#             self.embedding_model.encode(
#                 search_query
#             ).tolist()
#         )

#         where = self.build_chroma_where(
#             metadata_filters
#         )

#         kwargs = {

#             "query_embeddings": [
#                 query_embedding
#             ],

#             "n_results": top_k,
#         }

#         if where:

#             kwargs["where"] = where

#         results = self.collection.query(
#             **kwargs
#         )

#         ids = results.get(
#             "ids",
#             [[]]
#         )[0]

#         distances = results.get(
#             "distances",
#             [[]]
#         )[0]

#         semantic_scores = {}

#         for incident_id, distance in zip(
#             ids,
#             distances
#         ):

#             incident_id = str(
#                 incident_id
#             )

#             # Chroma distance -> similarity

#             similarity = (
#                 1.0 /
#                 (1.0 + float(distance))
#             )

#             semantic_scores[
#                 incident_id
#             ] = similarity

#         return semantic_scores

#     # ========================================================
#     # BM25 SEARCH
#     # ========================================================

#     def bm25_search(
#         self,
#         search_query: str,
#         candidate_ids: List[str],
#         top_k: int,
#     ) -> Dict[str, float]:

#         if not search_query.strip():

#             return {}

#         query_tokens = self._tokenize(
#             search_query
#         )

#         if not query_tokens:

#             return {}

#         scores = self.bm25.get_scores(
#             query_tokens
#         )

#         candidate_set = set(
#             candidate_ids
#         )

#         results = []

#         for index, score in enumerate(
#             scores
#         ):

#             incident_id = (
#                 self.bm25_incident_ids[
#                     index
#                 ]
#             )

#             if incident_id not in candidate_set:
#                 continue

#             results.append(
#                 (
#                     incident_id,
#                     float(score)
#                 )
#             )

#         results.sort(
#             key=lambda x: x[1],
#             reverse=True
#         )

#         results = results[:top_k]

#         return dict(results)

#     # ========================================================
#     # NORMALIZE SCORES
#     # ========================================================

#     @staticmethod
#     def normalize_scores(
#         scores: Dict[str, float]
#     ) -> Dict[str, float]:

#         if not scores:

#             return {}

#         values = np.array(
#             list(scores.values()),
#             dtype=float
#         )

#         minimum = values.min()
#         maximum = values.max()

#         if np.isclose(
#             minimum,
#             maximum
#         ):

#             return {
#                 key: 1.0
#                 for key in scores
#             }

#         normalized = {}

#         for key, value in (
#             scores.items()
#         ):

#             normalized[key] = (
#                 (value - minimum)
#                 /
#                 (maximum - minimum)
#             )

#         return normalized

#     # ========================================================
#     # HYBRID RANKING
#     # ========================================================

#     def hybrid_rank(
#         self,
#         bm25_scores: Dict[str, float],
#         semantic_scores: Dict[str, float],
#         top_k: int,
#     ) -> List[Dict[str, Any]]:

#         bm25_normalized = (
#             self.normalize_scores(
#                 bm25_scores
#             )
#         )

#         semantic_normalized = (
#             self.normalize_scores(
#                 semantic_scores
#             )
#         )

#         all_ids = set(
#             bm25_normalized.keys()
#         ) | set(
#             semantic_normalized.keys()
#         )

#         ranked = []

#         for incident_id in all_ids:

#             bm25_score = (
#                 bm25_normalized
#                 .get(incident_id, 0.0)
#             )

#             semantic_score = (
#                 semantic_normalized
#                 .get(incident_id, 0.0)
#             )

#             hybrid_score = (
#                 BM25_WEIGHT * bm25_score
#                 +
#                 SEMANTIC_WEIGHT * semantic_score
#             )

#             ranked.append(
#                 {
#                     "incident_id":
#                         incident_id,

#                     "bm25_score":
#                         bm25_score,

#                     "semantic_score":
#                         semantic_score,

#                     "hybrid_score":
#                         hybrid_score,
#                 }
#             )

#         ranked.sort(
#             key=lambda x:
#                 x["hybrid_score"],
#             reverse=True
#         )

#         return ranked[:top_k]

#     # ========================================================
#     # ATTACH INCIDENT DATA
#     # ========================================================

#     def attach_records(
#         self,
#         ranked_results: List[Dict[str, Any]]
#     ) -> List[Dict[str, Any]]:

#         final_results = []

#         for result in ranked_results:

#             incident_id = (
#                 result["incident_id"]
#             )

#             record = self.df_by_incident.get(
#                 incident_id
#             )

#             if not record:
#                 continue

#             final_results.append(
#                 {
#                     "incident_id":
#                         incident_id,

#                     "scores": {
#                         "hybrid":
#                             result["hybrid_score"],

#                         "bm25":
#                             result["bm25_score"],

#                         "semantic":
#                             result["semantic_score"],
#                     },

#                     "incident": record,
#                 }
#             )

#         return final_results

#     # ========================================================
#     # MAIN RUN METHOD
#     # ========================================================

#     def run(
#         self,
#         query: str,
#         top_k: int = DEFAULT_TOP_K,
#     ) -> Dict[str, Any]:

#         # ----------------------------------------------------
#         # 1. Parse query
#         # ----------------------------------------------------

#         query_plan = self.parse_query(
#             query,
#             top_k
#         )

#         # ----------------------------------------------------
#         # 2. Metadata filtering
#         # ----------------------------------------------------

#         candidate_ids = (
#             self.get_metadata_candidates(
#                 query_plan.metadata_filters
#             )
#         )

#         # ----------------------------------------------------
#         # 3. Numeric filtering
#         # ----------------------------------------------------

#         candidate_ids = (
#             self.apply_numeric_conditions(
#                 candidate_ids,
#                 query_plan.numeric_conditions
#             )
#         )

#         # ----------------------------------------------------
#         # 4. Semantic search
#         #
#         # Chroma handles exact metadata filters.
#         #
#         # Numeric filtering is additionally enforced
#         # after retrieval.
#         # ----------------------------------------------------

#         semantic_scores = (
#             self.semantic_search(
#                 query_plan.search_query,
#                 query_plan.metadata_filters,
#                 top_k * RETRIEVAL_MULTIPLIER
#             )
#         )

#         # Only retain numeric-condition candidates

#         candidate_set = set(
#             candidate_ids
#         )

#         semantic_scores = {
#             incident_id: score
#             for incident_id, score
#             in semantic_scores.items()
#             if incident_id in candidate_set
#         }

#         # ----------------------------------------------------
#         # 5. BM25
#         # ----------------------------------------------------

#         bm25_scores = (
#             self.bm25_search(
#                 query_plan.search_query,
#                 candidate_ids,
#                 top_k * RETRIEVAL_MULTIPLIER
#             )
#         )

#         # ----------------------------------------------------
#         # 6. Hybrid ranking
#         # ----------------------------------------------------

#         ranked_results = (
#             self.hybrid_rank(
#                 bm25_scores,
#                 semantic_scores,
#                 top_k
#             )
#         )

#         # ----------------------------------------------------
#         # 7. Attach actual incident records
#         # ----------------------------------------------------

#         final_results = (
#             self.attach_records(
#                 ranked_results
#             )
#         )

#         # ----------------------------------------------------
#         # 8. Return agent-friendly result
#         # ----------------------------------------------------

#         return {

#             "query": query,

#             "query_plan":
#                 query_plan.model_dump(),

#             "candidate_count":
#                 len(candidate_ids),

#             "results":
#                 final_results,

#             "retrieval": {

#                 "bm25_used":
#                     bool(bm25_scores),

#                 "semantic_used":
#                     bool(semantic_scores),

#                 "metadata_filter_used":
#                     bool(
#                         query_plan.metadata_filters
#                     ),

#                 "numeric_filter_used":
#                     bool(
#                         query_plan.numeric_conditions
#                     ),

#             },

#             "agent":
#                 "QueryAgent",
#         }


# # ============================================================
# # TEST
# # ============================================================

# if __name__ == "__main__":

#     agent = QueryAgent()

#     query = (
#         "Give me winter incidents around "
#         "Chennai where performance degraded badly"
#     )

#     result = agent.run(
#         query,
#         top_k=5
#     )

#     print("\n" + "=" * 70)
#     print("QUERY")
#     print("=" * 70)

#     print(result["query"])

#     print("\n" + "=" * 70)
#     print("QUERY PLAN")
#     print("=" * 70)

#     print(
#         json.dumps(
#             result["query_plan"],
#             indent=2
#         )
#     )

#     print("\n" + "=" * 70)
#     print("RESULTS")
#     print("=" * 70)

#     for item in result["results"]:

#         print(
#             f"\nIncident: "
#             f"{item['incident_id']}"
#         )

#         print(
#             f"Hybrid: "
#             f"{item['scores']['hybrid']:.4f}"
#         )

#         print(
#             f"BM25: "
#             f"{item['scores']['bm25']:.4f}"
#         )

#         print(
#             f"Semantic: "
#             f"{item['scores']['semantic']:.4f}"
#         )

########################
             ##################################3
############################
                    ########################################
                                      ############################################3
"""
Query Agent
===========

Purpose
-------
Converts a natural-language telecom query into a structured retrieval plan
and retrieves relevant historical incidents using:

1. LLM-based query parsing
2. Metadata filtering
3. Numeric condition filtering
4. BM25 lexical retrieval
5. ChromaDB semantic retrieval
6. Hybrid ranking

Designed to be called later by a multi-agent orchestrator.

Important:
- ChromaDB already contains embeddings.
- This file does NOT rebuild embeddings.
- Incident_ID is the canonical identifier everywhere.
"""

import re
import json

from typing import Any, Dict, List, Literal

import chromadb
import numpy as np
import pandas as pd

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from pydantic import BaseModel, Field


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

from config.config import (
    CSV_PATH,
    CHROMA_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
)

# ============================================================
# LLM CLIENT
# ============================================================

from llm.llm_client import LLMClient


# ============================================================
# RETRIEVAL CONFIGURATION
# ============================================================

DEFAULT_TOP_K = 5

BM25_WEIGHT = 0.4

SEMANTIC_WEIGHT = 0.6

RETRIEVAL_MULTIPLIER = 5


# ============================================================
# FIELD DEFINITIONS
# ============================================================

METADATA_FIELDS = [
    "incident_id",
    "city",
    "state",
    "zip",
    "season",
    "weather",
    "issue_reported",
]


NUMERIC_FIELDS = [
    "cell_availability",
    "mttr_hours",
    "throughput_mbps",
    "latency_ms",
    "packet_loss_rate",
    "call_drop_rate",
    "handover_success_rate",
    "alarm_count",
    "critical_alarm_count",
    "parameter_changes",
    "successful_configuration_changes",
    "data_usage_gb",
    "user_count",
    "signal_strength_dbm",
    "jitter_ms",
    "connection_setup_success_rate",
    "security_incidents",
    "authentication_failures",
    "temperature_c",
    "humidity_percent",
    "fault_occurrence_rate",
]


# ============================================================
# HUMAN-FRIENDLY METRIC ALIASES
# ============================================================

FIELD_ALIASES = {

    "latency": "latency_ms",
    "delay": "latency_ms",

    "packet loss": "packet_loss_rate",
    "packet loss rate": "packet_loss_rate",

    "call drops": "call_drop_rate",
    "dropped calls": "call_drop_rate",
    "call drop": "call_drop_rate",

    "signal": "signal_strength_dbm",
    "signal strength": "signal_strength_dbm",
    "poor signal": "signal_strength_dbm",

    "jitter": "jitter_ms",

    "throughput": "throughput_mbps",

    "availability": "cell_availability",
    "cell availability": "cell_availability",

    "mttr": "mttr_hours",
    "repair time": "mttr_hours",
    "mean time to repair": "mttr_hours",

    "handover": "handover_success_rate",
    "handover success": "handover_success_rate",

    "alarms": "alarm_count",
    "alarm count": "alarm_count",

    "critical alarms": "critical_alarm_count",

    "parameter changes": "parameter_changes",

    "configuration success":
        "successful_configuration_changes",

    "data usage":
        "data_usage_gb",

    "users": "user_count",
    "user count": "user_count",

    "connection setup":
        "connection_setup_success_rate",

    "security incidents":
        "security_incidents",

    "authentication failures":
        "authentication_failures",

    "temperature":
        "temperature_c",

    "humidity":
        "humidity_percent",

    "fault occurrence":
        "fault_occurrence_rate",
}


# ============================================================
# QUERY PLAN SCHEMA
# ============================================================

class NumericCondition(BaseModel):

    field: str

    operator: Literal[
        ">",
        ">=",
        "<",
        "<=",
        "="
    ]

    value: float


class QueryPlan(BaseModel):

    metadata_filters: Dict[str, Any] = Field(
        default_factory=dict
    )

    numeric_conditions: List[NumericCondition] = Field(
        default_factory=list
    )

    search_query: str = ""

    top_k: int = DEFAULT_TOP_K


# ============================================================
# QUERY AGENT
# ============================================================

class QueryAgent:

    def __init__(
        self,
        csv_path=CSV_PATH,
        chroma_path=CHROMA_PATH,
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_model=EMBEDDING_MODEL,
    ):

        print("=" * 70)
        print("Initializing Query Agent...")
        print("=" * 70)

        # ----------------------------------------------------
        # Show configuration
        # ----------------------------------------------------

        print(f"[QueryAgent] CSV Path       : {csv_path}")
        print(f"[QueryAgent] Chroma Path    : {chroma_path}")
        print(f"[QueryAgent] Collection     : {collection_name}")
        print(f"[QueryAgent] Embedding Model: {embedding_model}")

        # ----------------------------------------------------
        # Load CSV
        # ----------------------------------------------------

        self.df = pd.read_csv(csv_path)

        self._normalize_dataframe()

        # ----------------------------------------------------
        # Build lookup by Incident ID
        # ----------------------------------------------------

        self.df_by_incident = {
            str(row["incident_id"]): row.to_dict()
            for _, row in self.df.iterrows()
        }

        # ----------------------------------------------------
        # Load embedding model
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # This does NOT create new embeddings.
        #
        # It only loads the SAME embedding model that was used
        # to create the existing ChromaDB embeddings.
        #
        # ----------------------------------------------------

        print(
            "[QueryAgent] Loading embedding model..."
        )

        self.embedding_model = SentenceTransformer(
            embedding_model
        )

        print(
            "[QueryAgent] Embedding model loaded."
        )

        # ----------------------------------------------------
        # Connect to EXISTING ChromaDB
        # ----------------------------------------------------

        print(
            "[QueryAgent] Connecting to ChromaDB..."
        )

        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path)
        )

        self.collection = (
            self.chroma_client.get_collection(
                name=collection_name
            )
        )

        print(
            "[QueryAgent] ChromaDB collection connected."
        )

        # ----------------------------------------------------
        # Build BM25
        # ----------------------------------------------------

        print(
            "[QueryAgent] Building BM25 index..."
        )

        self._build_bm25()

        print(
            "[QueryAgent] BM25 index ready."
        )

        # ----------------------------------------------------
        # Metadata values
        # ----------------------------------------------------

        self.metadata_values = {}

        for field in METADATA_FIELDS:

            if field in self.df.columns:

                values = (
                    self.df[field]
                    .dropna()
                    .astype(str)
                    .str.lower()
                    .unique()
                    .tolist()
                )

                self.metadata_values[field] = values

        # ----------------------------------------------------
        # Centralized LLM Client
        # ----------------------------------------------------
        #
        # QueryAgent does NOT know:
        # - API keys
        # - OpenRouter URL
        # - model authentication
        #
        # LLMClient handles all of that.
        #
        # ----------------------------------------------------

        try:

            self.llm_client = LLMClient()

            print(
                "[QueryAgent] LLM client ready."
            )

        except ValueError as e:

            print(
                f"[QueryAgent] LLM client unavailable: {e}"
            )

            self.llm_client = None

        print("=" * 70)
        print("Query Agent ready.")
        print("=" * 70)

    # ========================================================
    # DATAFRAME NORMALIZATION
    # ========================================================

    def _normalize_dataframe(self):

        rename_map = {

            "Incident_ID":
                "incident_id",

            "Season":
                "season",

            "Cell Availability (%)":
                "cell_availability",

            "MTTR (hours)":
                "mttr_hours",

            "Throughput (Mbps)":
                "throughput_mbps",

            "Latency (ms)":
                "latency_ms",

            "Packet Loss Rate (%)":
                "packet_loss_rate",

            "Call Drop Rate (%)":
                "call_drop_rate",

            "Handover Success Rate (%)":
                "handover_success_rate",

            "Alarm Count":
                "alarm_count",

            "Critical Alarm Count":
                "critical_alarm_count",

            "Parameter Changes":
                "parameter_changes",

            "Successful Configuration Changes (%)":
                "successful_configuration_changes",

            "Data Usage (GB)":
                "data_usage_gb",

            "User Count":
                "user_count",

            "Signal Strength (dBm)":
                "signal_strength_dbm",

            "Jitter (ms)":
                "jitter_ms",

            "Connection Setup Success Rate (%)":
                "connection_setup_success_rate",

            "Security Incidents":
                "security_incidents",

            "Authentication Failures":
                "authentication_failures",

            "Temperature (°C)":
                "temperature_c",

            "Humidity (%)":
                "humidity_percent",

            "Weather":
                "weather",

            "Issue Reported":
                "issue_reported",

            "City":
                "city",

            "State":
                "state",

            "Zip":
                "zip",

            "Fault Occurrence Rate (%)":
                "fault_occurrence_rate",
        }

        self.df.rename(
            columns=rename_map,
            inplace=True
        )

        # ----------------------------------------------------
        # Normalize categorical values
        # ----------------------------------------------------

        for column in [
            "city",
            "state",
            "season",
            "weather",
            "issue_reported",
        ]:

            if column in self.df.columns:

                self.df[column] = (
                    self.df[column]
                    .astype(str)
                    .str.strip()
                )

        # ----------------------------------------------------
        # Normalize Incident ID
        # ----------------------------------------------------

        self.df["incident_id"] = (
            self.df["incident_id"]
            .astype(str)
            .str.strip()
        )

    # ========================================================
    # BM25 INDEX
    # ========================================================

    def _build_bm25(self):

        self.bm25_incident_ids = []

        corpus = []

        for _, row in self.df.iterrows():

            incident_id = str(
                row["incident_id"]
            )

            text_parts = []

            for column in self.df.columns:

                value = row[column]

                if pd.isna(value):
                    continue

                text_parts.append(
                    f"{column} {value}"
                )

            text = " ".join(text_parts)

            tokens = self._tokenize(text)

            corpus.append(tokens)

            self.bm25_incident_ids.append(
                incident_id
            )

        self.bm25 = BM25Okapi(corpus)

    # ========================================================
    # TOKENIZER
    # ========================================================

    @staticmethod
    def _tokenize(text: str):

        return re.findall(
            r"\b[a-zA-Z0-9_.%-]+\b",
            text.lower()
        )

    # ========================================================
    # LLM QUERY PARSER
    # ========================================================

    def parse_query(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> QueryPlan:

        # ----------------------------------------------------
        # No LLM available
        # ----------------------------------------------------

        if not self.llm_client:

            return self._fallback_parser(
                query,
                top_k
            )

        system_prompt = f"""
You are the query parser for a telecom network
incident retrieval system.

Your job is ONLY to convert a user's natural-language
query into a structured retrieval plan.

You MUST NOT answer the user's question.

Available exact metadata fields:

{json.dumps(METADATA_FIELDS, indent=2)}

Available numeric fields:

{json.dumps(NUMERIC_FIELDS, indent=2)}

Field aliases:

{json.dumps(FIELD_ALIASES, indent=2)}

Rules:

1. Exact location/time/category constraints go into
   metadata_filters.

2. Numeric requirements go into numeric_conditions.

3. Network concepts that are better handled by semantic
   or lexical retrieval go into search_query.

4. NEVER invent a field.

5. NEVER invent a metadata value.

6. Use the exact field names provided above.

7. If the user says "high latency", map it to
   latency_ms rather than inventing "high_latency".

8. If the user says "poor signal", map it to
   signal_strength_dbm.

9. If the query does not provide an exact numeric
   threshold, you may use a reasonable condition only
   when the meaning is clear. Otherwise put the concept
   into search_query.

10. Keep search_query concise and meaningful.

11. Do not put generic words such as:
    "show", "give", "find", "incidents", "previous"
    into search_query unless they add retrieval meaning.

12. The output MUST be valid JSON.

Return exactly:

{{
    "metadata_filters": {{}},
    "numeric_conditions": [],
    "search_query": "",
    "top_k": {top_k}
}}
"""

        try:

            # ------------------------------------------------
            # Centralized LLM call
            # ------------------------------------------------
            #
            # Previously this was:
            #
            # self.llm_client.chat.completions.create(...)
            #
            # Now QueryAgent calls the centralized LLMClient.
            #
            # ------------------------------------------------

            content = self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=query
            )

            # ------------------------------------------------
            # If all API keys failed
            # ------------------------------------------------

            if not content:

                print(
                    "[Query Parser] LLM unavailable."
                )

                print(
                    "[Query Parser] Using deterministic fallback."
                )

                return self._fallback_parser(
                    query,
                    top_k
                )

            # ------------------------------------------------
            # Clean JSON response
            # ------------------------------------------------

            content = self._clean_json_response(
                content
            )

            data = json.loads(content)

            # ------------------------------------------------
            # Validate QueryPlan
            # ------------------------------------------------

            plan = QueryPlan.model_validate(
                data
            )

            return self._validate_query_plan(
                plan,
                query
            )

        except Exception as e:

            print(
                f"[Query Parser] LLM parsing failed: {e}"
            )

            print(
                "[Query Parser] Using deterministic fallback."
            )

            return self._fallback_parser(
                query,
                top_k
            )

    # ========================================================
    # CLEAN LLM JSON
    # ========================================================

    @staticmethod
    def _clean_json_response(
        content: str
    ):

        content = content.strip()

        if content.startswith("```"):

            content = re.sub(
                r"^```(?:json)?",
                "",
                content,
                flags=re.IGNORECASE
            )

            content = re.sub(
                r"```$",
                "",
                content
            )

        return content.strip()

    # ========================================================
    # VALIDATE QUERY PLAN
    # ========================================================

    def _validate_query_plan(
        self,
        plan: QueryPlan,
        original_query: str,
    ) -> QueryPlan:

        # ----------------------------------------------------
        # Validate metadata fields
        # ----------------------------------------------------

        valid_metadata = {}

        for field, value in (
            plan.metadata_filters.items()
        ):

            if field not in METADATA_FIELDS:
                continue

            valid_metadata[field] = value

        plan.metadata_filters = valid_metadata

        # ----------------------------------------------------
        # Validate numeric conditions
        # ----------------------------------------------------

        valid_conditions = []

        for condition in plan.numeric_conditions:

            if condition.field not in NUMERIC_FIELDS:
                continue

            valid_conditions.append(
                condition
            )

        plan.numeric_conditions = (
            valid_conditions
        )

        # ----------------------------------------------------
        # Validate metadata values against dataset
        # ----------------------------------------------------

        validated_metadata = {}

        for field, value in (
            plan.metadata_filters.items()
        ):

            if field not in self.metadata_values:
                continue

            value_string = (
                str(value)
                .lower()
                .strip()
            )

            allowed_values = (
                self.metadata_values[field]
            )

            # Exact match

            if value_string in allowed_values:

                validated_metadata[field] = (
                    value_string
                )

        plan.metadata_filters = (
            validated_metadata
        )

        # ----------------------------------------------------
        # Normalize search query
        # ----------------------------------------------------

        plan.search_query = (
            plan.search_query
            .strip()
        )

        if not plan.search_query:

            plan.search_query = (
                original_query
            )

        return plan

    # ========================================================
    # FALLBACK PARSER
    # ========================================================

    def _fallback_parser(
        self,
        query: str,
        top_k: int,
    ) -> QueryPlan:

        """
        Deterministic fallback.

        This is NOT the primary parser.

        It exists so the Query Agent continues working
        if OpenRouter/LLM is unavailable.
        """

        query_lower = query.lower()

        metadata_filters = {}

        # ----------------------------------------------------
        # Detect known metadata values
        # ----------------------------------------------------

        for field, values in (
            self.metadata_values.items()
        ):

            # longest first prevents partial collisions

            sorted_values = sorted(
                values,
                key=len,
                reverse=True
            )

            for value in sorted_values:

                if value in query_lower:

                    metadata_filters[field] = (
                        value
                    )

                    break

        # ----------------------------------------------------
        # Remove metadata values from search text
        # ----------------------------------------------------

        search_query = query_lower

        for field, value in (
            metadata_filters.items()
        ):

            search_query = (
                search_query
                .replace(
                    str(value).lower(),
                    ""
                )
            )

        # ----------------------------------------------------
        # Remove generic words
        # ----------------------------------------------------

        stop_words = {

            "show",
            "give",
            "find",
            "get",
            "retrieve",
            "previous",
            "historical",
            "incidents",
            "incident",
            "records",
            "network",
            "in",
            "during",
            "from",
            "with",
            "where",
            "the",
            "for",
            "me",
        }

        tokens = self._tokenize(
            search_query
        )

        tokens = [
            token
            for token in tokens
            if token not in stop_words
        ]

        search_query = " ".join(tokens)

        return QueryPlan(
            metadata_filters=metadata_filters,
            numeric_conditions=[],
            search_query=search_query,
            top_k=top_k,
        )

    # ========================================================
    # BUILD CANDIDATE IDS FROM METADATA
    # ========================================================

    def get_metadata_candidates(
        self,
        metadata_filters: Dict[str, Any],
    ) -> List[str]:

        if not metadata_filters:

            return self.df[
                "incident_id"
            ].astype(str).tolist()

        mask = pd.Series(
            True,
            index=self.df.index
        )

        for field, value in (
            metadata_filters.items()
        ):

            if field not in self.df.columns:
                continue

            mask &= (
                self.df[field]
                .astype(str)
                .str.lower()
                ==
                str(value).lower()
            )

        return (
            self.df.loc[
                mask,
                "incident_id"
            ]
            .astype(str)
            .tolist()
        )

    # ========================================================
    # APPLY NUMERIC CONDITIONS
    # ========================================================

    def apply_numeric_conditions(
        self,
        candidate_ids: List[str],
        conditions: List[NumericCondition],
    ) -> List[str]:

        if not conditions:

            return candidate_ids

        if not candidate_ids:

            return []

        candidate_df = self.df[
            self.df["incident_id"]
            .astype(str)
            .isin(candidate_ids)
        ].copy()

        mask = pd.Series(
            True,
            index=candidate_df.index
        )

        for condition in conditions:

            field = condition.field

            if field not in candidate_df.columns:
                continue

            values = pd.to_numeric(
                candidate_df[field],
                errors="coerce"
            )

            value = condition.value

            if condition.operator == ">":

                mask &= values > value

            elif condition.operator == ">=":

                mask &= values >= value

            elif condition.operator == "<":

                mask &= values < value

            elif condition.operator == "<=":

                mask &= values <= value

            elif condition.operator == "=":

                mask &= np.isclose(
                    values,
                    value
                )

        return (
            candidate_df.loc[
                mask,
                "incident_id"
            ]
            .astype(str)
            .tolist()
        )

    # ========================================================
    # BUILD CHROMA WHERE
    # ========================================================

    def build_chroma_where(
        self,
        metadata_filters: Dict[str, Any],
    ):

        if not metadata_filters:

            return None

        conditions = []

        for field, value in (
            metadata_filters.items()
        ):

            conditions.append(
                {
                    field: str(value).lower()
                }
            )

        if len(conditions) == 1:

            return conditions[0]

        return {
            "$and": conditions
        }

    # ========================================================
    # SEMANTIC SEARCH
    # ========================================================

    def semantic_search(
        self,
        search_query: str,
        metadata_filters: Dict[str, Any],
        top_k: int,
    ) -> Dict[str, float]:

        if not search_query.strip():

            return {}

        query_embedding = (
            self.embedding_model.encode(
                search_query
            ).tolist()
        )

        where = self.build_chroma_where(
            metadata_filters
        )

        kwargs = {

            "query_embeddings": [
                query_embedding
            ],

            "n_results": top_k,
        }

        if where:

            kwargs["where"] = where

        results = self.collection.query(
            **kwargs
        )

        ids = results.get(
            "ids",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        semantic_scores = {}

        for incident_id, distance in zip(
            ids,
            distances
        ):

            incident_id = str(
                incident_id
            )

            # Chroma distance -> similarity

            similarity = (
                1.0 /
                (
                    1.0 +
                    float(distance)
                )
            )

            semantic_scores[
                incident_id
            ] = similarity

        return semantic_scores

    # ========================================================
    # BM25 SEARCH
    # ========================================================

    def bm25_search(
        self,
        search_query: str,
        candidate_ids: List[str],
        top_k: int,
    ) -> Dict[str, float]:

        if not search_query.strip():

            return {}

        query_tokens = self._tokenize(
            search_query
        )

        if not query_tokens:

            return {}

        scores = self.bm25.get_scores(
            query_tokens
        )

        candidate_set = set(
            candidate_ids
        )

        results = []

        for index, score in enumerate(
            scores
        ):

            incident_id = (
                self.bm25_incident_ids[
                    index
                ]
            )

            if incident_id not in candidate_set:
                continue

            results.append(
                (
                    incident_id,
                    float(score)
                )
            )

        results.sort(
            key=lambda x: x[1],
            reverse=True
        )

        results = results[:top_k]

        return dict(results)

    # ========================================================
    # NORMALIZE SCORES
    # ========================================================

    @staticmethod
    def normalize_scores(
        scores: Dict[str, float]
    ) -> Dict[str, float]:

        if not scores:

            return {}

        values = np.array(
            list(scores.values()),
            dtype=float
        )

        minimum = values.min()
        maximum = values.max()

        if np.isclose(
            minimum,
            maximum
        ):

            return {
                key: 1.0
                for key in scores
            }

        normalized = {}

        for key, value in (
            scores.items()
        ):

            normalized[key] = (
                (value - minimum)
                /
                (maximum - minimum)
            )

        return normalized

    # ========================================================
    # HYBRID RANKING
    # ========================================================

    def hybrid_rank(
        self,
        bm25_scores: Dict[str, float],
        semantic_scores: Dict[str, float],
        top_k: int,
    ) -> List[Dict[str, Any]]:

        bm25_normalized = (
            self.normalize_scores(
                bm25_scores
            )
        )

        semantic_normalized = (
            self.normalize_scores(
                semantic_scores
            )
        )

        all_ids = set(
            bm25_normalized.keys()
        ) | set(
            semantic_normalized.keys()
        )

        ranked = []

        for incident_id in all_ids:

            bm25_score = (
                bm25_normalized
                .get(incident_id, 0.0)
            )

            semantic_score = (
                semantic_normalized
                .get(incident_id, 0.0)
            )

            hybrid_score = (
                BM25_WEIGHT * bm25_score
                +
                SEMANTIC_WEIGHT * semantic_score
            )

            ranked.append(
                {
                    "incident_id":
                        incident_id,

                    "bm25_score":
                        bm25_score,

                    "semantic_score":
                        semantic_score,

                    "hybrid_score":
                        hybrid_score,
                }
            )

        ranked.sort(
            key=lambda x:
                x["hybrid_score"],
            reverse=True
        )

        return ranked[:top_k]

    # ========================================================
    # ATTACH INCIDENT DATA
    # ========================================================

    def attach_records(
        self,
        ranked_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        final_results = []

        for result in ranked_results:

            incident_id = (
                result["incident_id"]
            )

            record = self.df_by_incident.get(
                incident_id
            )

            if not record:
                continue

            final_results.append(
                {
                    "incident_id":
                        incident_id,

                    "scores": {
                        "hybrid":
                            result["hybrid_score"],

                        "bm25":
                            result["bm25_score"],

                        "semantic":
                            result["semantic_score"],
                    },

                    "incident": record,
                }
            )

        return final_results

    # ========================================================
    # MAIN RUN METHOD
    # ========================================================

    def run(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> Dict[str, Any]:

        # ----------------------------------------------------
        # 1. Parse query
        # ----------------------------------------------------

        query_plan = self.parse_query(
            query,
            top_k
        )

        # ----------------------------------------------------
        # 2. Metadata filtering
        # ----------------------------------------------------

        candidate_ids = (
            self.get_metadata_candidates(
                query_plan.metadata_filters
            )
        )

        # ----------------------------------------------------
        # 3. Numeric filtering
        # ----------------------------------------------------

        candidate_ids = (
            self.apply_numeric_conditions(
                candidate_ids,
                query_plan.numeric_conditions
            )
        )

        # ----------------------------------------------------
        # 4. Semantic search
        #
        # Chroma handles exact metadata filters.
        #
        # Numeric filtering is additionally enforced
        # after retrieval.
        # ----------------------------------------------------

        semantic_scores = (
            self.semantic_search(
                query_plan.search_query,
                query_plan.metadata_filters,
                top_k * RETRIEVAL_MULTIPLIER
            )
        )

        # ----------------------------------------------------
        # Only retain numeric-condition candidates
        # ----------------------------------------------------

        candidate_set = set(
            candidate_ids
        )

        semantic_scores = {
            incident_id: score
            for incident_id, score
            in semantic_scores.items()
            if incident_id in candidate_set
        }

        # ----------------------------------------------------
        # 5. BM25
        # ----------------------------------------------------

        bm25_scores = (
            self.bm25_search(
                query_plan.search_query,
                candidate_ids,
                top_k * RETRIEVAL_MULTIPLIER
            )
        )

        # ----------------------------------------------------
        # 6. Hybrid ranking
        # ----------------------------------------------------

        ranked_results = (
            self.hybrid_rank(
                bm25_scores,
                semantic_scores,
                top_k
            )
        )

        # ----------------------------------------------------
        # 7. Attach actual incident records
        # ----------------------------------------------------

        final_results = (
            self.attach_records(
                ranked_results
            )
        )

        # ----------------------------------------------------
        # 8. Return agent-friendly result
        # ----------------------------------------------------

        return {

            "query": query,

            "query_plan":
                query_plan.model_dump(),

            "candidate_count":
                len(candidate_ids),

            "results":
                final_results,

            "retrieval": {

                "bm25_used":
                    bool(bm25_scores),

                "semantic_used":
                    bool(semantic_scores),

                "metadata_filter_used":
                    bool(
                        query_plan.metadata_filters
                    ),

                "numeric_filter_used":
                    bool(
                        query_plan.numeric_conditions
                    ),

            },

            "agent":
                "QueryAgent",
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    agent = QueryAgent()

    query = (
        "Give me winter incidents around "
        "Chennai where performance degraded badly"
    )

    result = agent.run(
        query,
        top_k=5
    )

    print("\n" + "=" * 70)
    print("QUERY")
    print("=" * 70)

    print(result["query"])

    print("\n" + "=" * 70)
    print("QUERY PLAN")
    print("=" * 70)

    print(
        json.dumps(
            result["query_plan"],
            indent=2
        )
    )

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    for item in result["results"]:

        print(
            f"\nIncident: "
            f"{item['incident_id']}"
        )

        print(
            f"Hybrid: "
            f"{item['scores']['hybrid']:.4f}"
        )

        print(
            f"BM25: "
            f"{item['scores']['bm25']:.4f}"
        )

        print(
            f"Semantic: "
            f"{item['scores']['semantic']:.4f}"
        )