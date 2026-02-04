from __future__ import annotations

from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic.config import ConfigDict

from ai_ops_assistant.llm.client import LlmClient
from ai_ops_assistant.llm.schemas import FinalResponse, Plan, PlanStep, ToolResult, VerificationResult


class VerifierAgent:
    """Validates results and composes the final response."""

    def __init__(self, llm: LlmClient) -> None:
        self._llm = llm

    def verify(
        self,
        task: str,
        plan: Plan,
        results: List[ToolResult],
    ) -> VerificationResult:
        system = (
            "You are the Verifier Agent. Check if the tool results are complete and correct. "
            "If anything is missing, propose additional steps using available tools. "
            "Return JSON only."
        )
        user = (
            "Task: "
            f"{task}\n\nPlan: {plan.model_dump()}\n\nResults: "
            f"{[r.model_dump() for r in results]}"
        )

        class VerificationSchema(BaseModel):
            model_config = ConfigDict(populate_by_name=True)

            is_complete: bool = Field(
                ...,
                description="True if results satisfy the task",
                validation_alias=AliasChoices(
                    "is_complete",
                    "verification_status",
                    "status",
                    "plan_complete",
                    "completed",
                ),
            )
            missing: List[str] = Field(default_factory=list, description="What is missing")
            suggested_steps: List[PlanStep] = Field(
                default_factory=list,
                description="Extra steps to fill gaps",
            )
            final_response: Optional[FinalResponse] = Field(
                default=None,
                validation_alias=AliasChoices(
                    "final_response",
                    "response",
                    "final",
                    "final_answer",
                    "answer",
                ),
            )

            @field_validator("is_complete", mode="before")
            @classmethod
            def _normalize_status(cls, value):
                if isinstance(value, str):
                    return value.strip().lower() in {"complete", "true", "yes", "ok", "done"}
                return value

        response = self._llm.chat_json(
            system=system,
            user=user,
            schema=VerificationSchema,
        )

        final_response = response.final_response or FinalResponse(
            answer="",
            data={},
            sources=[],
        )
        is_complete = response.is_complete and bool(response.final_response)

        return VerificationResult(
            is_complete=is_complete,
            missing=response.missing,
            suggested_steps=response.suggested_steps,
            final_response=final_response,
        )

    def finalize(
        self,
        task: str,
        plan: Plan,
        results: List[ToolResult],
    ) -> FinalResponse:
        system = (
            "You are a response generator. Use the tool results to answer the user's task.\n\n"
            "Return ONLY a JSON object with this exact structure:\n"
            "{\"answer\": \"human readable summary\", \"data\": {\"key\": \"value\"}, \"sources\": [\"API1\", \"API2\"]}\n\n"
            "Example:\n"
            "{\"answer\": \"Found repo X with 1000 stars. Berlin weather is 10°C.\", "
            "\"data\": {\"repo\": \"owner/name\", \"temp\": 10}, \"sources\": [\"GitHub API\", \"Open-Meteo API\"]}"
        )
        user = (
            f"Task: {task}\n\n"
            f"Tool results: {[r.model_dump() for r in results]}\n\n"
            "Create a final response as JSON:"
        )
        return self._llm.chat_json(system=system, user=user, schema=FinalResponse)
