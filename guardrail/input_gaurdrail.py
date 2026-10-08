"""
Input Guardrail for Telecom Network Operations AI

Purpose
-------
Validate and protect incoming user queries before they reach
the Query Understanding / Routing Agent.

Flow
----
User Query
    ↓
InputGuardrail
    ↓
Approved Query
    ↓
Query Understanding Agent
    ↓
MCP / Synapt Context Layer
    ↓
Downstream Analysis
    ↓
Final Response

The guardrail does NOT:
    - Answer questions
    - Perform RAG
    - Query the database
    - Predict fault risk
    - Predict throughput
    - Perform root-cause analysis
    - Call Synapt
"""

from __future__ import annotations

import logging
import re
from enum import Enum

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Result types
# -------------------------------------------------------------------

class GuardrailStatus(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    REQUIRES_CLARIFICATION = "requires_clarification"


class GuardrailResult(BaseModel):
    """
    Structured result returned by the Input Guardrail.
    """

    status: GuardrailStatus

    allowed: bool

    original_query: str

    sanitized_query: str | None = None

    reason: str | None = None

    triggered_rules: list[str] = Field(
        default_factory=list
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )


# -------------------------------------------------------------------
# Exception
# -------------------------------------------------------------------

class InputGuardrailError(RuntimeError):
    """Raised when the guardrail itself fails unexpectedly."""


# -------------------------------------------------------------------
# Input Guardrail
# -------------------------------------------------------------------

class InputGuardrail:
    """
    Input validation and safety layer for the telecom assistant.

    The guardrail is intentionally lightweight.

    It performs:

        1. Empty-input validation
        2. Input-length validation
        3. Prompt-injection detection
        4. System-prompt extraction detection
        5. Database manipulation detection
        6. Command/code injection detection
        7. Telecom-domain relevance detection
        8. Basic input normalization

    It does NOT perform semantic answering.
    """

    # Maximum query length.
    MAX_QUERY_LENGTH = 2000

    # Minimum useful query length.
    MIN_QUERY_LENGTH = 2

    # ----------------------------------------------------------------
    # Prompt injection patterns
    # ----------------------------------------------------------------

    PROMPT_INJECTION_PATTERNS: list[tuple[str, str]] = [

        (
            r"\bignore\s+(all\s+)?previous\s+instructions\b",
            "prompt_injection"
        ),

        (
            r"\bignore\s+(all\s+)?prior\s+instructions\b",
            "prompt_injection"
        ),

        (
            r"\bforget\s+(all\s+)?previous\s+instructions\b",
            "prompt_injection"
        ),

        (
            r"\bdisregard\s+(all\s+)?previous\s+instructions\b",
            "prompt_injection"
        ),

        (
            r"\boverride\s+(the\s+)?system\s+instructions\b",
            "prompt_injection"
        ),

        (
            r"\bdo\s+not\s+follow\s+(the\s+)?system\b",
            "prompt_injection"
        ),

        (
            r"\bact\s+as\s+(an?\s+)?administrator\b",
            "privilege_escalation"
        ),

        (
            r"\bact\s+as\s+(the\s+)?system\b",
            "prompt_injection"
        ),

        (
            r"\byou\s+are\s+now\s+(an?\s+)?admin\b",
            "privilege_escalation"
        ),
    ]

    # ----------------------------------------------------------------
    # System prompt / secret extraction
    # ----------------------------------------------------------------

    SYSTEM_EXTRACTION_PATTERNS: list[tuple[str, str]] = [

        (
            r"\breveal\s+(your\s+)?system\s+prompt\b",
            "system_prompt_extraction"
        ),

        (
            r"\bshow\s+(me\s+)?(your\s+)?system\s+prompt\b",
            "system_prompt_extraction"
        ),

        (
            r"\bprint\s+(your\s+)?system\s+prompt\b",
            "system_prompt_extraction"
        ),

        (
            r"\bwhat\s+are\s+your\s+system\s+instructions\b",
            "system_prompt_extraction"
        ),

        (
            r"\breveal\s+(your\s+)?hidden\s+instructions\b",
            "system_prompt_extraction"
        ),

        (
            r"\bshow\s+(me\s+)?your\s+internal\s+instructions\b",
            "system_prompt_extraction"
        ),

        (
            r"\breveal\s+(the\s+)?api\s+key\b",
            "secret_extraction"
        ),

        (
            r"\breveal\s+(the\s+)?password\b",
            "secret_extraction"
        ),
    ]

    # ----------------------------------------------------------------
    # Database manipulation / destructive commands
    # ----------------------------------------------------------------

    DATABASE_ATTACK_PATTERNS: list[tuple[str, str]] = [

        (
            r"\bdrop\s+(table|database)\b",
            "database_manipulation"
        ),

        (
            r"\bdelete\s+from\b",
            "database_manipulation"
        ),

        (
            r"\btruncate\s+(table|database)\b",
            "database_manipulation"
        ),

        (
            r"\balter\s+table\b",
            "database_manipulation"
        ),

        (
            r"\bupdate\s+.*\s+set\s+",
            "database_manipulation"
        ),

        (
            r"\binsert\s+into\b",
            "database_manipulation"
        ),
    ]

    # ----------------------------------------------------------------
    # Code / command injection
    # ----------------------------------------------------------------

    CODE_INJECTION_PATTERNS: list[tuple[str, str]] = [

        (
            r"\bimport\s+os\b",
            "code_injection"
        ),

        (
            r"\bimport\s+subprocess\b",
            "code_injection"
        ),

        (
            r"\bos\.system\s*\(",
            "code_execution"
        ),

        (
            r"\bsubprocess\.(run|call|Popen)\s*\(",
            "code_execution"
        ),

        (
            r"\bexec\s*\(",
            "code_execution"
        ),

        (
            r"\beval\s*\(",
            "code_execution"
        ),

        (
            r";\s*(rm|del|shutdown|format)\b",
            "command_injection"
        ),
    ]

    # ----------------------------------------------------------------
    # Sensitive / unauthorized requests
    # ----------------------------------------------------------------

    UNAUTHORIZED_ACCESS_PATTERNS: list[tuple[str, str]] = [

        (
            r"\bshow\s+(me\s+)?all\s+passwords\b",
            "unauthorized_access"
        ),

        (
            r"\bshow\s+(me\s+)?credentials\b",
            "unauthorized_access"
        ),

        (
            r"\bget\s+(me\s+)?api\s+keys\b",
            "unauthorized_access"
        ),

        (
            r"\bshow\s+(me\s+)?authentication\s+tokens\b",
            "unauthorized_access"
        ),

        (
            r"\bsteal\s+.*credentials\b",
            "unauthorized_access"
        ),
    ]

    # ----------------------------------------------------------------
    # Telecom-domain keywords
    # ----------------------------------------------------------------

    TELECOM_KEYWORDS: set[str] = {
        "telecom",
        "telecommunication",
        "network",
        "cell",
        "cellular",
        "tower",
        "base station",
        "bs",
        "signal",
        "latency",
        "packet",
        "packet loss",
        "throughput",
        "jitter",
        "call",
        "calls",
        "handover",
        "handoff",
        "availability",
        "alarm",
        "alarms",
        "fault",
        "failure",
        "incident",
        "network performance",
        "network issue",
        "network problem",
        "mttr",
        "configuration",
        "authentication",
        "security incident",
        "data usage",
        "user count",
        "traffic",
        "weather",
        "temperature",
        "humidity",
        "signal strength",
        "dropped calls",
        "connection setup",
        "fault occurrence",
        "chennai",
        "mumbai",
        "delhi",
        "bengaluru",
        "bangalore",
        "hyderabad",
        "pune",
        "kolkata",
        "ahmedabad",
        "jaipur",
        "lucknow",
        "coimbatore",
        "madurai",
    }

    # ----------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------

    def validate(self, query: str) -> GuardrailResult:
        """
        Validate a user query.

        Returns
        -------
        GuardrailResult
            Structured result indicating whether the query
            can proceed to the Query Agent.
        """

        try:
            # --------------------------------------------------------
            # 1. Basic type validation
            # --------------------------------------------------------

            if not isinstance(query, str):
                return self._blocked(
                    original_query=str(query),
                    reason="Query must be a string.",
                    rule="invalid_input_type",
                )

            original_query = query

            # --------------------------------------------------------
            # 2. Remove surrounding whitespace
            # --------------------------------------------------------

            normalized_query = query.strip()

            # --------------------------------------------------------
            # 3. Empty query
            # --------------------------------------------------------

            if not normalized_query:

                return self._blocked(
                    original_query=original_query,
                    reason="Query is empty.",
                    rule="empty_query",
                )

            # --------------------------------------------------------
            # 4. Minimum length
            # --------------------------------------------------------

            if len(normalized_query) < self.MIN_QUERY_LENGTH:

                return self._blocked(
                    original_query=original_query,
                    reason="Query is too short.",
                    rule="query_too_short",
                )

            # --------------------------------------------------------
            # 5. Maximum length
            # --------------------------------------------------------

            if len(normalized_query) > self.MAX_QUERY_LENGTH:

                return self._blocked(
                    original_query=original_query,
                    reason=(
                        f"Query exceeds the maximum length "
                        f"of {self.MAX_QUERY_LENGTH} characters."
                    ),
                    rule="query_too_long",
                )

            # --------------------------------------------------------
            # 6. Normalize whitespace
            # --------------------------------------------------------

            sanitized_query = self._normalize(
                normalized_query
            )

            lower_query = sanitized_query.lower()

            # --------------------------------------------------------
            # 7. Prompt injection
            # --------------------------------------------------------

            triggered_rules = []

            self._collect_matches(
                lower_query,
                self.PROMPT_INJECTION_PATTERNS,
                triggered_rules,
            )

            # --------------------------------------------------------
            # 8. System prompt / secret extraction
            # --------------------------------------------------------

            self._collect_matches(
                lower_query,
                self.SYSTEM_EXTRACTION_PATTERNS,
                triggered_rules,
            )

            # --------------------------------------------------------
            # 9. Database manipulation
            # --------------------------------------------------------

            self._collect_matches(
                lower_query,
                self.DATABASE_ATTACK_PATTERNS,
                triggered_rules,
            )

            # --------------------------------------------------------
            # 10. Code execution
            # --------------------------------------------------------

            self._collect_matches(
                lower_query,
                self.CODE_INJECTION_PATTERNS,
                triggered_rules,
            )

            # --------------------------------------------------------
            # 11. Unauthorized access
            # --------------------------------------------------------

            self._collect_matches(
                lower_query,
                self.UNAUTHORIZED_ACCESS_PATTERNS,
                triggered_rules,
            )

            # --------------------------------------------------------
            # 12. Block malicious input
            # --------------------------------------------------------

            if triggered_rules:

                logger.warning(
                    "Input blocked. Rules triggered: %s",
                    triggered_rules,
                )

                return GuardrailResult(
                    status=GuardrailStatus.BLOCKED,
                    allowed=False,
                    original_query=original_query,
                    sanitized_query=None,
                    reason=(
                        "The query contains content that "
                        "cannot be processed."
                    ),
                    triggered_rules=sorted(
                        set(triggered_rules)
                    ),
                    confidence=0.98,
                )

            # --------------------------------------------------------
            # 13. Domain relevance
            # --------------------------------------------------------

            telecom_relevant = self._is_telecom_relevant(
                lower_query
            )

            if not telecom_relevant:

                logger.info(
                    "Query appears to be outside telecom domain."
                )

                return GuardrailResult(
                    status=GuardrailStatus.REQUIRES_CLARIFICATION,
                    allowed=False,
                    original_query=original_query,
                    sanitized_query=sanitized_query,
                    reason=(
                        "The query does not appear to relate "
                        "to telecom network operations."
                    ),
                    triggered_rules=[
                        "possible_off_topic_query"
                    ],
                    confidence=0.75,
                )

            # --------------------------------------------------------
            # 14. Approved
            # --------------------------------------------------------

            logger.info(
                "Input guardrail passed."
            )

            return GuardrailResult(
                status=GuardrailStatus.ALLOWED,
                allowed=True,
                original_query=original_query,
                sanitized_query=sanitized_query,
                reason=None,
                triggered_rules=[],
                confidence=0.95,
            )

        except Exception as exc:

            logger.exception(
                "Input guardrail failed unexpectedly."
            )

            raise InputGuardrailError(
                "Input guardrail failed."
            ) from exc

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _normalize(query: str) -> str:
        """
        Normalize whitespace without changing the user's meaning.
        """

        return re.sub(
            r"\s+",
            " ",
            query,
        ).strip()

    @staticmethod
    def _collect_matches(
        query: str,
        patterns: list[tuple[str, str]],
        triggered_rules: list[str],
    ) -> None:

        for pattern, rule_name in patterns:

            if re.search(
                pattern,
                query,
                flags=re.IGNORECASE,
            ):

                triggered_rules.append(
                    rule_name
                )

    def _is_telecom_relevant(
        self,
        query: str,
    ) -> bool:

        # Explicit incident IDs should be allowed even when
        # the rest of the query contains little telecom terminology.
        if re.search(
            r"\bINC\d{6,}\b",
            query,
            flags=re.IGNORECASE,
        ):
            return True

        # ZIP codes alone aren't enough to establish relevance.
        # Search for known telecom terminology.
        for keyword in self.TELECOM_KEYWORDS:

            if keyword in query:
                return True

        return False

    @staticmethod
    def _blocked(
        original_query: str,
        reason: str,
        rule: str,
    ) -> GuardrailResult:

        logger.warning(
            "Input blocked: %s",
            reason,
        )

        return GuardrailResult(
            status=GuardrailStatus.BLOCKED,
            allowed=False,
            original_query=original_query,
            sanitized_query=None,
            reason=reason,
            triggered_rules=[rule],
            confidence=1.0,
        )


# -------------------------------------------------------------------
# Convenience function
# -------------------------------------------------------------------

def run_input_guardrail(
    query: str,
) -> GuardrailResult:
    """
    Simple helper for callers that don't need to instantiate
    InputGuardrail manually.
    """

    guardrail = InputGuardrail()

    return guardrail.validate(query)