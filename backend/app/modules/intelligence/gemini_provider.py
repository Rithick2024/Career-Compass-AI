"""
Gemini AI Provider for Career Compass AI Intelligence.

Connects to Google Generative Language API (Gemini) using secure asynchronous
HTTP requests, strictly handling rate limits, timeouts, and quota exhaustion.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import (
    AIProviderConfigError,
    AIProviderQuotaError,
    AIProviderServiceError,
    AIProviderTimeoutError,
    ValidationError,
)

logger = logging.getLogger("app.intelligence.gemini")

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider:
    """Encapsulates interaction with the Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        timeout_seconds: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        if fallback_models is not None:
            self.fallback_models = fallback_models
        else:
            raw_fallbacks = getattr(settings, "GEMINI_FALLBACK_MODELS", "")
            self.fallback_models = [
                m.strip()
                for m in raw_fallbacks.split(",")
                if m.strip() and m.strip() != self.model
            ]
        self.last_used_model = self.model
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.GEMINI_TIMEOUT_SECONDS
        )
        self.max_output_tokens = (
            max_output_tokens if max_output_tokens is not None else settings.GEMINI_MAX_OUTPUT_TOKENS
        )
        self._http_client = http_client

    async def generate_response(
        self,
        system_instruction: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Sends an authenticated prompt to the Gemini API and returns the generated text.

        Args:
            system_instruction: Context/role constraints for the mentor.
            user_prompt: Untrusted student message (validated).
            history: Optional list of previous turns [{"role": "user"|"model", "content": "..."}].

        Returns:
            The generated response string.

        Raises:
            AIProviderConfigError: If GEMINI_API_KEY is not configured.
            ValidationError: If input violates character length constraints.
            AIProviderQuotaError: If 429 quota or rate limit is reached.
            AIProviderTimeoutError: If request times out.
            AIProviderServiceError: On upstream HTTP errors or invalid payloads.
        """
        if not self.api_key or not self.api_key.strip():
            logger.error("Gemini provider called but GEMINI_API_KEY is not configured.")
            raise AIProviderConfigError(
                "AI Career Mentor is currently unconfigured. Please configure GEMINI_API_KEY in the environment."
            )

        trimmed_prompt = user_prompt.strip()
        if not trimmed_prompt:
            raise ValidationError("User prompt cannot be empty.")

        if len(trimmed_prompt) > settings.GEMINI_MAX_INPUT_CHARS:
            raise ValidationError(
                f"Prompt length ({len(trimmed_prompt)} chars) exceeds maximum allowed ({settings.GEMINI_MAX_INPUT_CHARS} chars)."
            )

        contents: List[Dict[str, Any]] = []

        if history:
            for item in history:
                role = "user" if item.get("role") in ("user", "student") else "model"
                content_text = item.get("content", "").strip()
                if content_text:
                    contents.append(
                        {
                            "role": role,
                            "parts": [{"text": content_text[:settings.GEMINI_MAX_INPUT_CHARS]}],
                        }
                    )

        contents.append(
            {
                "role": "user",
                "parts": [{"text": trimmed_prompt}],
            }
        )

        payload: Dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": self.max_output_tokens,
            },
        }

        models_to_try = [self.model]
        for fallback in self.fallback_models:
            if fallback and fallback not in models_to_try:
                models_to_try.append(fallback)

        params = {"key": self.api_key}
        last_error: Optional[Exception] = None

        for attempt_idx, current_model in enumerate(models_to_try):
            has_fallback = attempt_idx < len(models_to_try) - 1
            endpoint_url = f"{GEMINI_API_BASE_URL}/models/{current_model}:generateContent"
            start_time = time.perf_counter()

            try:
                if self._http_client:
                    response = await self._http_client.post(
                        endpoint_url,
                        params=params,
                        json=payload,
                        timeout=self.timeout_seconds,
                    )
                else:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        response = await client.post(
                            endpoint_url,
                            params=params,
                            json=payload,
                        )
            except httpx.TimeoutException as exc:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                logger.warning(
                    "Gemini API request timed out after %d ms (model=%s, input_len=%d)",
                    elapsed_ms,
                    current_model,
                    len(trimmed_prompt),
                )
                if has_fallback:
                    next_model = models_to_try[attempt_idx + 1]
                    logger.info("Failing over to fallback model: %s", next_model)
                    last_error = AIProviderTimeoutError(
                        "The AI Career Mentor request timed out. Please try again with a shorter question."
                    )
                    continue
                raise AIProviderTimeoutError(
                    "The AI Career Mentor request timed out. Please try again with a shorter question."
                ) from exc
            except httpx.RequestError as exc:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                logger.error(
                    "Network error connecting to Gemini API after %d ms (model=%s): %s",
                    elapsed_ms,
                    current_model,
                    type(exc).__name__,
                )
                if has_fallback:
                    next_model = models_to_try[attempt_idx + 1]
                    logger.info("Failing over to fallback model: %s", next_model)
                    last_error = AIProviderServiceError(
                        "Unable to establish a secure connection to the AI provider. Please try again later."
                    )
                    continue
                raise AIProviderServiceError(
                    "Unable to establish a secure connection to the AI provider. Please try again later."
                ) from exc

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            if response.status_code == 429:
                logger.warning(
                    "Gemini API rate limit or quota exceeded (429) in %d ms (model=%s)",
                    elapsed_ms,
                    current_model,
                )
                if has_fallback:
                    next_model = models_to_try[attempt_idx + 1]
                    logger.info("Failing over from %s to fallback model %s due to 429", current_model, next_model)
                    last_error = AIProviderQuotaError(
                        "AI Career Mentor quota or rate limit exceeded. Please wait a minute and try again."
                    )
                    continue
                raise AIProviderQuotaError(
                    "AI Career Mentor quota or rate limit exceeded. Please wait a minute and try again."
                )

            if response.status_code != 200:
                logger.error(
                    "Gemini API error: HTTP %d in %d ms (model=%s)",
                    response.status_code,
                    elapsed_ms,
                    current_model,
                )
                if has_fallback:
                    next_model = models_to_try[attempt_idx + 1]
                    logger.info(
                        "Failing over from %s to fallback model %s due to HTTP %d",
                        current_model,
                        next_model,
                        response.status_code,
                    )
                    last_error = AIProviderServiceError(
                        f"AI service provider error (status {response.status_code}). Please try again."
                    )
                    continue

                detail_msg = ""
                try:
                    err_json = response.json()
                    if isinstance(err_json, dict):
                        err_obj = err_json.get("error")
                        if isinstance(err_obj, dict):
                            raw_msg = str(err_obj.get("message", "") or "").strip()
                            if raw_msg:
                                detail_msg = f": {raw_msg}"
                except Exception:
                    pass

                raise AIProviderServiceError(
                    f"AI service provider error (status {response.status_code}){detail_msg}. Please try again."
                )

            try:
                data = response.json()
                candidates = data.get("candidates", []) if isinstance(data, dict) else []
                if not candidates:
                    prompt_feedback = data.get("promptFeedback", {}) if isinstance(data, dict) else {}
                    block_reason = prompt_feedback.get("blockReason")
                    if block_reason:
                        logger.warning("Gemini prompt blocked with reason: %s", block_reason)
                        raise AIProviderServiceError(
                            f"The AI provider was unable to generate a response ({block_reason}). Please rephrase your query."
                        )
                    raise AIProviderServiceError("AI provider returned an empty response.")

                first_candidate = candidates[0]
                parts = first_candidate.get("content", {}).get("parts", [])
                if not parts:
                    raise AIProviderServiceError("AI response contained no message content.")

                text_output = parts[0].get("text", "")
                if not text_output.strip():
                    raise AIProviderServiceError("AI generated an empty response text.")

                self.last_used_model = current_model
                logger.info(
                    "Gemini API response succeeded (model=%s, latency=%dms, output_len=%d)",
                    current_model,
                    elapsed_ms,
                    len(text_output),
                )
                return text_output.strip()

            except (ValueError, KeyError) as exc:
                logger.error("Failed to parse Gemini API JSON response: %s", exc)
                raise AIProviderServiceError("Failed to parse AI provider response.") from exc

        if last_error:
            raise last_error
        raise AIProviderServiceError("AI service provider is currently unavailable. Please try again.")
