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
- Each JSONL row is indexed as one complete incident document; no extra text splitting is applied.
- Incident_ID is the canonical identifier everywhere.
"""

import re
import json
import logging
from pathlib import Path

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
from guardrail.input_gaurdrail import InputGuardrail
from agents.incident_classifier import IncidentClassificationAgent


# ============================================================
# RETRIEVAL CONFIGURATION
# ============================================================

DEFAULT_TOP_K = 5

BM25_WEIGHT = 0.4

SEMANTIC_WEIGHT = 0.6

RETRIEVAL_MULTIPLIER = 5
MAX_TOP_K = 50

logger = logging.getLogger(__name__)
SOP_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parent.parent
    / "files_load_context_files"
    / "sop_knowledge.json"
)


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

        self.input_guardrail = InputGuardrail()
        self.classification_agent = IncidentClassificationAgent()
        with SOP_KNOWLEDGE_PATH.open("r", encoding="utf-8") as sop_file:
            self.sop_knowledge = json.load(sop_file)
        self.sops = self.sop_knowledge["sops"]

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

    def classify_scenario(
        self,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Classify live metrics without searching historical incidents."""
        return self.classification_agent.classify_scenario(metrics)

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
        numeric_conditions = []

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

                if field == "state" and len(value) == 2:
                    value_found = re.search(
                        rf"(?<!\w){re.escape(value.upper())}(?!\w)",
                        query,
                    )
                else:
                    value_found = re.search(
                        rf"(?<!\w){re.escape(value)}(?!\w)",
                        query_lower,
                    )

                if value_found:

                    metadata_filters[field] = (
                        value
                    )

                    break

        # ----------------------------------------------------
        # Extract explicit numeric comparisons
        # ----------------------------------------------------

        comparison_operators = {
            ">=": ">=",
            "at least": ">=",
            "no less than": ">=",
            "greater than or equal to": ">=",
            "more than or equal to": ">=",
            "<=": "<=",
            "at most": "<=",
            "no more than": "<=",
            "less than or equal to": "<=",
            "greater than": ">",
            "more than": ">",
            "above": ">",
            "over": ">",
            "exceeds": ">",
            "higher than": ">",
            ">": ">",
            "less than": "<",
            "below": "<",
            "under": "<",
            "lower than": "<",
            "<": "<",
            "equal to": "=",
            "exactly": "=",
            "=": "=",
        }
        comparison_pattern = "|".join(
            re.escape(operator)
            for operator in sorted(
                comparison_operators,
                key=len,
                reverse=True,
            )
        )
        metric_aliases = {
            **FIELD_ALIASES,
            **{
                field.replace("_", " "): field
                for field in NUMERIC_FIELDS
            },
        }
        comparison_matches = []
        for alias, field in sorted(
            metric_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            escaped_alias = re.escape(alias)
            metric_pattern = (
                rf"(?<!\w){escaped_alias}(?!\w)"
            )
            value_pattern = r"(?P<value>-?\d+(?:\.\d+)?)"
            unit_pattern = r"(?:\s*(?:%|percent|ms|mbps|hours?|gb|dbm|users?))?"
            prefix_pattern = re.compile(
                rf"{metric_pattern}\s*(?:(?:is|of|at)\s+)?"
                rf"(?P<operator>{comparison_pattern})\s*"
                rf"{value_pattern}{unit_pattern}",
                flags=re.IGNORECASE,
            )
            suffix_pattern = re.compile(
                rf"(?P<operator>{comparison_pattern})\s*"
                rf"{value_pattern}{unit_pattern}\s*"
                rf"{metric_pattern}",
                flags=re.IGNORECASE,
            )
            for pattern in (prefix_pattern, suffix_pattern):
                for match in pattern.finditer(query_lower):
                    if any(
                        match.start() < end and match.end() > start
                        for start, end, _ in comparison_matches
                    ):
                        continue
                    operator = comparison_operators[
                        match.group("operator").lower()
                    ]
                    numeric_conditions.append(
                        NumericCondition(
                            field=field,
                            operator=operator,
                            value=float(match.group("value")),
                        )
                    )
                    comparison_matches.append(
                        (match.start(), match.end(), field)
                    )

        # ----------------------------------------------------
        # Remove recognized filters from search text
        # ----------------------------------------------------

        search_query = query_lower

        for start, end, _ in sorted(
            comparison_matches,
            reverse=True,
        ):
            search_query = (
                search_query[:start]
                + " "
                + search_query[end:]
            )

        for field, value in (
            metadata_filters.items()
        ):

            search_query = re.sub(
                rf"(?<!\w){re.escape(str(value).lower())}(?!\w)",
                " ",
                search_query,
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
            "and",
            "or",
            "at",
            "least",
            "most",
            "more",
            "less",
            "than",
            "above",
            "below",
            "over",
            "under",
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
            numeric_conditions=numeric_conditions,
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

            matching_values = self.df.loc[
                self.df[field]
                .astype(str)
                .str.lower()
                == str(value).lower(),
                field,
            ]
            if matching_values.empty:
                continue

            conditions.append(
                {
                    field: str(matching_values.iloc[0])
                }
            )

        if not conditions:
            return None

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
        if not ranked_results:
            return final_results

        incident_ids = [
            result["incident_id"]
            for result in ranked_results
        ]
        stored_documents = self.collection.get(
            ids=incident_ids,
            include=["documents"],
        )
        document_by_id = dict(
            zip(
                stored_documents.get("ids", []),
                stored_documents.get("documents", []),
            )
        )

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

                    "document":
                        document_by_id.get(incident_id),
                }
            )

        return final_results

    def select_relevant_sops(
        self,
        query: str,
        query_plan: QueryPlan,
    ) -> List[Dict[str, Any]]:
        """Select synthetic troubleshooting procedures supported by query intent."""
        query_text = f"{query} {query_plan.search_query}".lower()
        query_tokens = set(self._tokenize(query_text))
        requested_fields = {
            condition.field
            for condition in query_plan.numeric_conditions
        }

        for alias, field in FIELD_ALIASES.items():
            if alias in query_text:
                requested_fields.add(field)

        relevant_sops = []
        for sop in self.sops:
            trigger_fields = set()
            for trigger_metric in sop["trigger_metrics"]:
                normalized_metric = re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    trigger_metric.lower(),
                ).strip("_")
                trigger_fields.add(normalized_metric)

            requested_trigger_match = any(
                field in trigger_fields
                for field in requested_fields
            )
            scenario_terms = set(
                self._tokenize(
                    f"{sop['name']} {sop['scenario']}"
                )
            ) - {
                "network",
                "investigation",
                "condition",
                "possible",
                "performance",
            }
            scenario_match = bool(query_tokens & scenario_terms)
            broad_degradation_match = (
                sop["sop_id"] == "SOP_011"
                and bool(
                    query_tokens
                    & {"degraded", "degradation", "poor", "bad", "failure"}
                )
            )
            if requested_trigger_match or scenario_match or broad_degradation_match:
                relevant_sops.append(sop)

        return relevant_sops[:3]

    # ========================================================
    # MAIN RUN METHOD
    # ========================================================

    def run(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> Dict[str, Any]:

        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or top_k < 1
            or top_k > MAX_TOP_K
        ):
            raise ValueError(
                f"top_k must be an integer between 1 and {MAX_TOP_K}."
            )

        guardrail_result = self.input_guardrail.validate(query)

        if not guardrail_result.allowed:
            return {
                "query": query,
                "status": guardrail_result.status.value,
                "query_plan": None,
                "requirements": None,
                "candidate_count": 0,
                "results": [],
                "evidence": [],
                "answer": guardrail_result.reason,
                "answer_status": "not_generated",
                "guardrail": guardrail_result.model_dump(mode="json"),
                "retrieval": {
                    "bm25_used": False,
                    "semantic_used": False,
                    "metadata_filter_used": False,
                    "numeric_filter_used": False,
                },
                "agent": "QueryAgent",
            }

        sanitized_query = guardrail_result.sanitized_query

        # ----------------------------------------------------
        # 1. Parse query
        # ----------------------------------------------------

        query_plan = self.parse_query(
            sanitized_query,
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

        if candidate_ids:
            semantic_scores = self.semantic_search(
                query_plan.search_query,
                query_plan.metadata_filters,
                min(
                    top_k * RETRIEVAL_MULTIPLIER,
                    len(candidate_ids),
                ),
            )
        else:
            semantic_scores = {}

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

        if not query_plan.search_query.strip():
            ranked_results = [
                {
                    "incident_id": incident_id,
                    "bm25_score": 0.0,
                    "semantic_score": 0.0,
                    "hybrid_score": 0.0,
                }
                for incident_id in candidate_ids[:top_k]
            ]

        # ----------------------------------------------------
        # 7. Attach actual incident records
        # ----------------------------------------------------

        final_results = (
            self.attach_records(
                ranked_results
            )
        )
        classification = self.classification_agent.classify_results(
            final_results
        )
        recommendation_evidence = self.select_relevant_sops(
            sanitized_query,
            query_plan,
        )

        if not final_results:
            answer = (
                "No historical incidents matched the supplied "
                "query requirements."
            )
            answer_status = "no_evidence"
        elif self.llm_client is None:
            answer = None
            answer_status = "unavailable"
            logger.warning(
                "Skipping incident analysis because the LLM client "
                "is not configured."
            )
        else:
            analysis_evidence = [
                {
                    "incident_id": item["incident_id"],
                    "hybrid_score": item["scores"]["hybrid"],
                    "bm25_score": item["scores"]["bm25"],
                    "semantic_score": item["scores"]["semantic"],
                    "document": item["document"],
                    "record": item["incident"],
                    "classification": item["classification"],
                }
                for item in final_results
            ]
            answer = self.llm_client.analyze_incidents(
                sanitized_query,
                analysis_evidence,
                sop_evidence=recommendation_evidence,
            )
            if answer:
                answer_status = "generated"
            else:
                answer_status = "unavailable"
                logger.warning(
                    "Incident retrieval succeeded, but LLM analysis "
                    "did not return an answer."
                )

        # ----------------------------------------------------
        # 8. Return agent-friendly result
        # ----------------------------------------------------

        return {

            "query": query,

            "status": "completed",

            "query_plan":
                query_plan.model_dump(),

            "requirements":
                query_plan.model_dump(),

            "candidate_count":
                len(candidate_ids),

            "results":
                final_results,

            "evidence":
                final_results,

            "classification":
                classification,

            "recommendation_evidence":
                recommendation_evidence,

            "answer":
                answer,

            "answer_status":
                answer_status,

            "guardrail":
                guardrail_result.model_dump(mode="json"),

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