# guardrails.py - Gruet 2/27/26

from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

# ── Safety Patterns (adapted for returns / RMA) ───────────────────────────────
PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions", "ignore your rules", "forget your rules",
    "you are now", "act as", "new system prompt", "disregard safety",
    "bypass", "jailbreak", " dan ", "do anything now",
    "export all", "delete from", "drop table", "show full database",
    "system prompt", "your instructions are",
    # Returns-specific
    "approve anyway", "override validation", "force refund", "ignore rules", "bypass check",
    "delete rma", "delete record", "change status", "mark as refunded", "give full access",
    "fake return", "refund abuse", "multiple rmas", "free money"
]

PII_SENSITIVE_KEYWORDS = [
    "ssn", "social security", "credit card", "passport", "password",
    "api key", "secret", "token", "private key", "bank account",
]

FRAUD_KEYWORDS = [
    "fraud", "fake", "stolen", "abuse", "multiple returns", "refund scam",
    "free refund", "policy abuse", "launder"
]

# ── Relevance / Scope Patterns (adapted for returns flows) ────────────────────
RETURNS_INTENT_KEYWORDS = [
    "return", "rma", "refund", "replace", "repair", "credit", "status", "track",
    "order number", "invoice number", "customer id", "reason code", "priority",
    "created date", "approved date", "closed date", "source channel", "created by",
    "email", "unread", "latest", "open email", "validate", "insert", "report",
    "pending", "processed"
]

OFF_TOPIC_INDICATORS = [
    "joke", "poem", "story", "recipe", "bake", "cook", "sing", "dance",
    "weather", "temperature", "forecast", "rain", "sunny", "cloudy", "humid", "hot", "cold",
    "time", "what time", "what day", "date today", "clock", "timezone",
    "how to", "how do i", "teach me", "guide", "tutorial", "instructions",
    "drive", "fix", "build", "make", "bypass", "hack", "cheat",
    "news", "stock", "politics", "sports", "movie", "music"
]

# ── Safe extraction helpers ───────────────────────────────────────────────────
def _safe_part_text(part) -> Optional[str]:
    """
    ADK/GenAI parts are not guaranteed to be text parts.
    This safely returns a non-empty string or None.
    """
    txt = getattr(part, "text", None)
    if isinstance(txt, str):
        txt = txt.strip()
        if txt:
            return txt
    return None


def _safe_last_user_text(llm_request: LlmRequest) -> Optional[str]:
    """
    Returns the last user message text if present, else None.
    Does NOT assume parts[0] is text.
    """
    if not getattr(llm_request, "contents", None):
        return None

    last = llm_request.contents[-1]
    if getattr(last, "role", None) != "user":
        return None

    parts = getattr(last, "parts", None)
    if not parts:
        return None

    for p in parts:
        txt = _safe_part_text(p)
        if txt:
            return txt

    return None


# ── Returns-specific Reliability helpers ──────────────────────────────────────
def _has_strong_returns_intent_lower(msg_lower: str) -> bool:
    return any(kw in msg_lower for kw in RETURNS_INTENT_KEYWORDS)


def _is_clearly_off_topic_lower(msg_lower: str) -> bool:
    msg_lower = msg_lower.strip()
    return any(ind in msg_lower for ind in OFF_TOPIC_INDICATORS)


# ── Main combined guardrail (input side) ──────────────────────────────────────
def before_model_guard(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Combined Safety + Relevance guardrail.
    Runs before every model call.

    Returns:
      - None: continue normal LLM call
      - LlmResponse: short-circuit and return this response instead
    """

    last_message_raw = _safe_last_user_text(llm_request)
    if not last_message_raw:
        return None  # nothing to analyze / not a text user message

    last_message = last_message_raw.lower()

    # ── Safety checks first ───────────────────────────────────────────────────
    if any(pat in last_message for pat in PROMPT_INJECTION_PATTERNS):
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(
                    text=(
                        "I'm sorry, but I can't assist with requests that try to override guidelines "
                        "or manipulate the process. How can I help with a valid returns request instead?"
                    )
                )]
            )
        )

    if any(kw in last_message for kw in PII_SENSITIVE_KEYWORDS):
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(
                    text=(
                        "I’m not able to handle or store personal or sensitive information like that. "
                        "If you have a question about returns or RMAs, I’d be glad to help!"
                    )
                )]
            )
        )

    # Uncomment if you want to block fraud-y queries
    # if any(kw in last_message for kw in FRAUD_KEYWORDS):
    #     return LlmResponse(
    #         content=types.Content(
    #             role="model",
    #             parts=[types.Part(
    #                 text=(
    #                     "I can't assist with requests that appear to involve fraud or policy abuse. "
    #                     "If this is a legitimate returns inquiry, please rephrase without those terms."
    #                 )
    #             )]
    #         )
    #     )

    # ── Relevance (optional) ──────────────────────────────────────────────────
    # If you want to enable relevance gating, uncomment this section.

    # history_length = len(getattr(llm_request, "contents", []) or [])
    # if history_length >= 3:  # treat as follow-up; allow
    #     return None

    # if _has_strong_returns_intent_lower(last_message):
    #     return None

    # if _is_clearly_off_topic_lower(last_message):
    #     return LlmResponse(
    #         content=types.Content(
    #             role="model",
    #             parts=[types.Part(
    #                 text="I'm focused on returns and RMA processing. What return-related action or query can I help with?"
    #             )]
    #         )
    #     )

    # # Ambiguous → clarify
    # return LlmResponse(
    #     content=types.Content(
    #         role="model",
    #         parts=[types.Part(
    #             text=(
    #                 "Hi! I'm here to help with returns, RMAs, emails, validation, or reports. "
    #                 "What would you like to do? (e.g., check unread emails, validate an RMA, get a report)"
    #             )
    #         )]
    #     )
    # )

    return None