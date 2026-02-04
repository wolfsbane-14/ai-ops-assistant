from __future__ import annotations

import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ai_ops_assistant.agents.executor import ExecutorAgent
from ai_ops_assistant.agents.planner import PlannerAgent
from ai_ops_assistant.agents.verifier import VerifierAgent
from ai_ops_assistant.llm.client import LlmClient
from ai_ops_assistant.llm.schemas import FinalResponse
from ai_ops_assistant.tools.github_tool import GitHubTool
from ai_ops_assistant.tools.weather_tool import WeatherTool


class TaskRequest(BaseModel):
    task: str = Field(..., description="Natural language task")
    skip_verification: bool = Field(
        default=True, 
        description="Skip verification step to save LLM calls (faster, uses less quota)"
    )


class TaskResponse(BaseModel):
    result: FinalResponse
    metadata: Dict[str, Any]


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(title="AI Ops Assistant", version="0.1.0")

    @app.post("/run", response_model=TaskResponse)
    def run_task(request: TaskRequest) -> TaskResponse:
        try:
            llm = LlmClient()
            planner = PlannerAgent(llm)
            executor = ExecutorAgent(GitHubTool(), WeatherTool())
            verifier = VerifierAgent(llm)

            # Step 1: Plan (1 LLM call)
            plan = planner.plan(request.task)
            
            # Step 2: Execute tools (no LLM calls)
            results = executor.execute(plan.steps)
            
            # Step 3: Optimize - skip verification for simple tasks
            if request.skip_verification:
                # Only 2 LLM calls total: plan + finalize
                final_response = verifier.finalize(request.task, plan, results)
            else:
                # Full verification (3-4 LLM calls)
                verification = verifier.verify(request.task, plan, results)

                if not verification.is_complete and verification.suggested_steps:
                    extra_results = executor.execute(verification.suggested_steps)
                    results.extend(extra_results)
                    final_response = verifier.finalize(request.task, plan, results)
                elif not verification.final_response.answer:
                    final_response = verifier.finalize(request.task, plan, results)
                else:
                    final_response = verification.final_response

            return TaskResponse(
                result=final_response,
                metadata={
                    "steps": [step.model_dump() for step in plan.steps],
                    "tools_used": [res.tool for res in results],
                    "verification_skipped": request.skip_verification,
                },
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()
