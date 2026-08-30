from __future__ import annotations

from tests.conftest import BASE, CLIENT_PAYLOAD

MISSING = "00000000-0000-0000-0000-000000000000"


async def test_create_and_get_client(api):
    resp = await api.post(f"{BASE}/clients", json=CLIENT_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["companyName"] == "Acme Corp"
    assert body["id"]
    assert body["createdAt"]

    resp = await api.get(f"{BASE}/clients/{body['id']}")
    assert resp.status_code == 200
    assert resp.json()["pointOfContact"]["email"] == "jane@acme.com"
    assert resp.json()["address"]["postalCode"] == "94105"


async def test_get_missing_client_returns_404(api):
    resp = await api.get(f"{BASE}/clients/{MISSING}")
    assert resp.status_code == 404


async def test_list_clients_filters_by_company_name(api):
    await api.post(f"{BASE}/clients", json=CLIENT_PAYLOAD)
    await api.post(f"{BASE}/clients", json={**CLIENT_PAYLOAD, "companyName": "Globex"})

    resp = await api.get(f"{BASE}/clients", params={"companyName": "glob"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] == 1
    assert data["items"][0]["companyName"] == "Globex"


async def test_patch_client_updates_only_supplied_fields(api):
    cid = (await api.post(f"{BASE}/clients", json=CLIENT_PAYLOAD)).json()["id"]

    resp = await api.patch(
        f"{BASE}/clients/{cid}", json={"region": "US-East", "remarks": "VIP account"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["region"] == "US-East"
    assert body["remarks"] == "VIP account"
    assert body["companyName"] == "Acme Corp"  # untouched


async def test_patch_missing_client_returns_404(api):
    resp = await api.patch(f"{BASE}/clients/{MISSING}", json={"region": "US-East"})
    assert resp.status_code == 404
