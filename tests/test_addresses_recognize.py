"""Tests for addresses recognize endpoint"""

import json

import pytest

from src.app.main import app
from src.app.api.v1.addresses import get_shipstation_service
from src.app.core.utils.shipstation_client import ShipStationClientError

class FakeShipStationServiceOK:
    async def recognize_address(self, text: str, address=None):
        return {"ok": True, "text": text, "address": address}

class FakeShipStationServiceFail:
    async def recognize_address(self, text: str, address=None):
        raise ShipStationClientError("Upstream error")

@pytest.fixture
def override_shipstation_ok():
    app.dependency_overrides[get_shipstation_service] = lambda: FakeShipStationServiceOK()
    yield
    app.dependency_overrides.pop(get_shipstation_service, None)

@pytest.fixture
def override_shipstation_fail():
    app.dependency_overrides[get_shipstation_service] = lambda: FakeShipStationServiceFail()
    yield
    app.dependency_overrides.pop(get_shipstation_service, None)

@pytest.mark.anyio
async def test_recognize_ok_text_only(async_client, override_shipstation_ok):
    r = await async_client.get("/api/v1/addresses/recognize", params={"text": "Test Address"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["text"] == "Test Address"
    assert body["address"] is None

@pytest.mark.anyio
async def test_recognize_ok_with_address_json(async_client, override_shipstation_ok):
    address = {"city_locality": "Austin", "state_province": "TX"}
    r = await async_client.get(
        "/api/v1/addresses/recognize",
        params={"text": "3800 North Lamar", "address": json.dumps(address)},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["address"] == address

@pytest.mark.anyio
async def test_recognize_text_required_422(async_client, override_shipstation_ok):
    r = await async_client.get("/api/v1/addresses/recognize", params={"text": ""})
    assert r.status_code == 422

@pytest.mark.anyio
async def test_recognize_invalid_address_json_400(async_client, override_shipstation_ok):
    r = await async_client.get(
        "/api/v1/addresses/recognize",
        params={"text": "Test", "address": "{bad json}"},
    )
    assert r.status_code == 400
    assert "Invalid 'adress' JSON" in r.text

@pytest.mark.anyio
async def test_recognize_address_json_not_dict_400(async_client, override_shipstation_ok):
    r = await async_client.get(
        "/api/v1/addresses/recognize",
        params={"text": "Test", "address": '["a","b"]'},
    )
    assert r.status_code == 400
    assert "Json expected" in r.text

@pytest.mark.anyio
async def test_recognize_upstream_error_returns_502(async_client, override_shipstation_fail):
    r = await async_client.get("/api/v1/addresses/recognize", params={"text": "Test"})
    assert r.status_code == 502
    assert "Upstream error" in r.text
