"""OpenAPI contract tests."""

import pytest

pytestmark = pytest.mark.anyio("asyncio")

async def test_openapi_has_addresses_recognize(async_client):
    r = await async_client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()

    path = "/api/v1/addresses/recognize"
    assert path in spec["paths"]
    assert "get" in spec["paths"][path]

    params = spec["paths"][path]["get"].get("parameters", [])
    param_by_name = {p["name"]: p for p in params}

    assert param_by_name["text"].get("required") is True
    # address может быть required: false или отсутствовать — оба ок
    assert param_by_name["address"].get("required") in (False, None)
