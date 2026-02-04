from __future__ import annotations

import json
import os
import time
from typing import Any, Optional, Type, TypeVar

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from pydantic import BaseModel, ValidationError

from ai_ops_assistant.llm.cache import ResponseCache


T = TypeVar("T", bound=BaseModel)


class LlmClient:
    """Gemini client with structured JSON output and rate limit handling."""

    def __init__(self, cache: Optional[ResponseCache] = None) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        genai.configure(api_key=api_key)
        self._model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self._model = genai.GenerativeModel(self._model_name)
        self._max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self._retry_delay = float(os.getenv("LLM_RETRY_DELAY", "2.0"))
        self._cache = cache or ResponseCache(ttl_seconds=int(os.getenv("CACHE_TTL", "3600")))
        self._enable_cache = os.getenv("ENABLE_CACHE", "true").lower() == "true"

    def chat_json(self, system: str, user: str, schema: Type[T]) -> T:
        """Generate structured JSON response with retry logic for rate limits."""
        # Check cache first
        if self._enable_cache:
            cached = self._cache.get(system, user)
            if cached:
                print(f"Cache hit! Saved 1 LLM call")
                return schema.model_validate(cached)
        
        prompt = f"{system}\n\n{user}\n\nReturn ONLY valid JSON matching the schema. No extra text."
        
        for attempt in range(self._max_retries):
            try:
                response = self._model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0,
                        "response_mime_type": "application/json",
                    },
                )
                content = (response.text or "{}").strip()
                
                # Try direct validation first
                try:
                    result = schema.model_validate_json(content)
                    # Cache successful response
                    if self._enable_cache:
                        self._cache.set(system, user, result.model_dump())
                    return result
                except ValidationError as e:
                    # If it's a list when we expect an object with "steps", wrap it
                    try:
                        payload: Any = json.loads(content)
                        if isinstance(payload, list) and "steps" in schema.model_fields:
                            result = schema.model_validate({"steps": payload})
                            if self._enable_cache:
                                self._cache.set(system, user, result.model_dump())
                            return result
                        # If answer/data/sources are missing but other fields exist, extract what we can
                        if hasattr(schema, '__name__') and schema.__name__ == 'FinalResponse':
                            result = self._extract_final_response(payload, schema)
                            if self._enable_cache:
                                self._cache.set(system, user, result.model_dump())
                            return result
                        raise e
                    except json.JSONDecodeError:
                        raise e
                        
            except ResourceExhausted as e:
                # Handle rate limit errors with exponential backoff
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)
                    print(f"Rate limit hit. Retrying in {wait_time}s... (attempt {attempt + 1}/{self._max_retries})")
                    time.sleep(wait_time)
                else:
                    raise ValueError(
                        f"Rate limit exceeded after {self._max_retries} attempts. "
                        "Please wait or upgrade your API quota."
                    ) from e
            except Exception as e:
                # For other errors, don't retry
                if attempt < self._max_retries - 1 and "quota" not in str(e).lower():
                    time.sleep(1)
                    continue
                raise
        
        raise ValueError("Failed to generate response after all retries")
    
    def _extract_final_response(self, payload: Any, schema: Type[T]) -> T:
        """Extract FinalResponse from non-standard Gemini output."""
        if isinstance(payload, dict):
            # Try to find answer-like fields
            answer = (
                payload.get('answer') or 
                payload.get('summary') or 
                payload.get('result') or
                payload.get('response') or
                payload.get('message') or
                str(payload)
            )
            data = payload.get('data', payload.get('details', {}))
            if isinstance(data, list):
                data = {"items": data}
            sources = payload.get('sources', payload.get('tools_used', []))
            
            return schema.model_validate({
                'answer': answer,
                'data': data if isinstance(data, dict) else {},
                'sources': sources if isinstance(sources, list) else []
            })
        return schema.model_validate({'answer': str(payload), 'data': {}, 'sources': []})
