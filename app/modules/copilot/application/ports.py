from __future__ import annotations

from typing import Any, Protocol


class Narrator(Protocol):
    """Optional LLM rephrasing of an already-decided, deterministic draft.

    The narrator only sees the draft text and the facts that produced it; it can
    never change the decision, the score, or whether something was approved."""

    def narrate(self, draft: str, facts: dict[str, Any]) -> str: ...
