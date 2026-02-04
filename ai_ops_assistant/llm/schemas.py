from __future__ import annotations

from typing import Any, Dict, List

from pydantic import AliasChoices, BaseModel, Field
from pydantic.config import ConfigDict


class PlanStep(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tool: str = Field(..., alias="tool_name", description="Tool name")
    input: Dict[str, Any] = Field(default_factory=dict, description="Tool input payload")


class Plan(BaseModel):
    steps: List[PlanStep]


class ToolResult(BaseModel):
    tool: str
    input: Dict[str, Any]
    success: bool
    output: Dict[str, Any]


class FinalResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str = Field(
        ...,
        description="Human-readable response",
        validation_alias=AliasChoices(
            "answer",
            "summary",
            "result",
            "response",
            "final_answer",
            "message",
        ),
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data",
        validation_alias=AliasChoices("data", "results", "details", "info"),
    )
    sources: List[str] = Field(
        default_factory=list,
        description="API sources used",
        validation_alias=AliasChoices("sources", "apis_used", "tools_used"),
    )


class VerificationResult(BaseModel):
    is_complete: bool
    missing: List[str]
    suggested_steps: List[PlanStep]
    final_response: FinalResponse
