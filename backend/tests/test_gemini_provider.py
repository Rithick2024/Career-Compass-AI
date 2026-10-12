"""
Unit tests for GeminiProvider class.
"""

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

from app.core.exceptions import (
    AIProviderConfigError,
    AIProviderQuotaError,
    AIProviderServiceError,
    AIProviderTimeoutError,
    ValidationError,
)
from app.modules.intelligence.gemini_provider import GeminiProvider


@pytest.mark.asyncio
async def test_provider_missing_key_raises_config_error():
    provider = GeminiProvider(api_key="")
    with pytest.raises(AIProviderConfigError):
        await provider.generate_response("system", "hello")


@pytest.mark.asyncio
async def test_provider_empty_prompt_raises_validation_error():
    provider = GeminiProvider(api_key="valid-key")
    with pytest.raises(ValidationError):
        await provider.generate_response("system", "   ")


@pytest.mark.asyncio
async def test_provider_too_long_prompt_raises_validation_error():
    provider = GeminiProvider(api_key="valid-key")
    with pytest.raises(ValidationError):
        await provider.generate_response("system", "x" * 2000)


@pytest.mark.asyncio
async def test_provider_success_response():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello, here is career advice."}]
                }
            }
        ]
    }
    mock_client.post.return_value = mock_resp

    provider = GeminiProvider(api_key="valid-key", http_client=mock_client)
    res = await provider.generate_response("system", "How do I become a backend engineer?")
    assert res == "Hello, here is career advice."


@pytest.mark.asyncio
async def test_provider_429_quota_raises_quota_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_client.post.return_value = mock_resp

    provider = GeminiProvider(api_key="valid-key", http_client=mock_client)
    with pytest.raises(AIProviderQuotaError):
        await provider.generate_response("system", "hello")


@pytest.mark.asyncio
async def test_provider_timeout_raises_timeout_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.TimeoutException("Read timed out")

    provider = GeminiProvider(api_key="valid-key", http_client=mock_client)
    with pytest.raises(AIProviderTimeoutError):
        await provider.generate_response("system", "hello")


@pytest.mark.asyncio
async def test_provider_server_error_raises_service_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 503
    mock_client.post.return_value = mock_resp

    provider = GeminiProvider(api_key="valid-key", http_client=mock_client)
    with pytest.raises(AIProviderServiceError):
        await provider.generate_response("system", "hello")
