from __future__ import annotations

from typing import Dict, List

from ai_ops_assistant.llm.schemas import PlanStep, ToolResult
from ai_ops_assistant.tools.github_tool import GitHubTool
from ai_ops_assistant.tools.weather_tool import WeatherTool


class ExecutorAgent:
    """Executes plan steps by calling tools."""

    def __init__(self, github_tool: GitHubTool, weather_tool: WeatherTool) -> None:
        self._tools = {
            "github_search": github_tool.search_repositories,
            "github_repo_details": github_tool.repo_details,
            "weather_current": weather_tool.current_weather,
        }

    def execute(self, steps: List[PlanStep]) -> List[ToolResult]:
        results: List[ToolResult] = []
        for step in steps:
            tool_fn = self._tools.get(step.tool)
            if not tool_fn:
                results.append(
                    ToolResult(
                        tool=step.tool,
                        input=step.input,
                        success=False,
                        output={"error": "Unknown tool"},
                    )
                )
                continue
            try:
                if step.tool == "weather_current":
                    step.input = self._normalize_weather_input(step.input)
                output = tool_fn(step.input)
                results.append(
                    ToolResult(
                        tool=step.tool,
                        input=step.input,
                        success=True,
                        output=output,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive
                results.append(
                    ToolResult(
                        tool=step.tool,
                        input=step.input,
                        success=False,
                        output={"error": str(exc)},
                    )
                )
        return results

    @staticmethod
    def _normalize_weather_input(payload: Dict[str, str]) -> Dict[str, str]:
        if "city" not in payload and "location" in payload:
            payload = {**payload, "city": payload["location"]}
        return payload
