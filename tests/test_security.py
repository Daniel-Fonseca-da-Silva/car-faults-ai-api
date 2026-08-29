import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.security import verify_api_key


def _settings(**overrides):
    return get_settings().model_copy(update=overrides)


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def test_verify_api_key_with_correct_key_passes():
    settings = _settings(API_KEY="correct-key")

    await verify_api_key(_credentials("correct-key"), settings)


async def test_verify_api_key_with_incorrect_key_raises_401():
    settings = _settings(API_KEY="correct-key")

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(_credentials("wrong-key"), settings)

    assert exc_info.value.status_code == 401


async def test_verify_api_key_with_missing_credentials_raises_401():
    settings = _settings(API_KEY="correct-key")

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(None, settings)

    assert exc_info.value.status_code == 401


async def test_verify_api_key_with_different_length_key_raises_401_not_error():
    settings = _settings(API_KEY="a-fairly-long-correct-key")

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(_credentials("short"), settings)

    assert exc_info.value.status_code == 401


async def test_body_over_max_size_returns_413(async_client, auth_headers):
    oversized_value = "A" * (get_settings().MAX_REQUEST_BODY_BYTES + 1)

    response = await async_client.post(
        "/lookup",
        json={"filler": oversized_value},
        headers=auth_headers,
    )

    assert response.status_code == 413
