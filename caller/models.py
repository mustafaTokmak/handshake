"""Typed result of an escalation call.

The voice channel is untrusted input. Nothing here authorizes an action; a
finding is evidence for a human, and the schema is deliberately narrow so a
transcript cannot smuggle instructions into a field that anything acts on.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MAX_TEXT = 600
MAX_ITEMS = 12


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContractChange(StrictModel):
    changed_fields: List[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    affected_parameters: List[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    described_behaviour: str = Field(min_length=1, max_length=MAX_TEXT)
    suggested_action: str = Field(default="", max_length=MAX_TEXT)
    effective_date: str = Field(default="", max_length=64)
    verbatim_quote: str = Field(default="", max_length=MAX_TEXT)


class CallFinding(StrictModel):
    status: Literal["informative", "uninformative", "refused"]
    change: Optional[ContractChange] = None
    summary: str = Field(min_length=1, max_length=MAX_TEXT)


# Gemini function-declaration mirror of CallFinding. Kept beside the model so
# the two cannot drift apart unnoticed.
FINDING_DECLARATION = {
    "name": "report_finding",
    "description": (
        "Record what the provider representative said about the API change. "
        "Call this once, only after you have asked your questions and either "
        "learned something concrete or established that they will not say."
    ),
    "parameters": {
        "type": "OBJECT",
        "required": ["status", "summary"],
        "properties": {
            "status": {
                "type": "STRING",
                "enum": ["informative", "uninformative", "refused"],
                "description": "informative when they described a concrete change; uninformative when they did not know; refused when they would not say.",
            },
            "summary": {"type": "STRING", "description": "One or two sentences on what was established."},
            "change": {
                "type": "OBJECT",
                "required": ["described_behaviour"],
                "properties": {
                    "changed_fields": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "API field names they said changed, added or were removed."},
                    "affected_parameters": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Request parameters whose behaviour changed."},
                    "described_behaviour": {"type": "STRING", "description": "What they said the new behaviour is."},
                    "suggested_action": {"type": "STRING", "description": "What they said the caller should do differently."},
                    "effective_date": {"type": "STRING", "description": "When the change took effect, if stated."},
                    "verbatim_quote": {"type": "STRING", "description": "A short direct quote supporting the above."},
                },
            },
        },
    },
}
