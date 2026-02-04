from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from ai_ops_assistant.llm.client import LlmClient
from ai_ops_assistant.llm.schemas import Plan, PlanStep


class PlannerAgent:
    """Creates a structured step-by-step plan using the LLM."""

    def __init__(self, llm: LlmClient) -> None:
        self._llm = llm

    def plan(self, task: str) -> Plan:
        system = (
            "You are a planning agent. Given a task, create a step-by-step plan.\n\n"
            "Available tools:\n"
            "- github_search: Search GitHub repos. Input: {\"query\": \"search term\", \"per_page\": 5}\n"
            "- github_repo_details: Get repo details. Input: {\"full_name\": \"owner/repo\"}\n"
            "- weather_current: Get weather. Input: {\"city\": \"CityName\"}\n\n"
            "Return ONLY a JSON object with this exact structure:\n"
            "{\"steps\": [{\"tool\": \"tool_name\", \"input\": {...}}, ...]}\n\n"
            "Example:\n"
            "{\"steps\": [{\"tool\": \"github_search\", \"input\": {\"query\": \"fastapi\"}}, "
            "{\"tool\": \"weather_current\", \"input\": {\"city\": \"Berlin\"}}]}"
        )
        user = f"Task: {task}\n\nReturn the plan as JSON with 'steps' array:"

        class PlanSchema(BaseModel):
            steps: List[PlanStep] = Field(..., description="Ordered steps to complete the task")

        response = self._llm.chat_json(
            system=system,
            user=user,
            schema=PlanSchema,
        )
        return Plan(steps=response.steps)
