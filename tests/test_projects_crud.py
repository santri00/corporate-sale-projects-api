from __future__ import annotations

from tests.conftest import BASE, project_payload

MISSING = "00000000-0000-0000-0000-000000000000"


async def test_create_project_requires_existing_client(api):
    resp = await api.post(f"{BASE}/projects", json=project_payload(MISSING))
    assert resp.status_code == 422


async def test_create_and_get_project(api, client_id):
    resp = await api.post(f"{BASE}/projects", json=project_payload(client_id))
    assert resp.status_code == 201
    body = resp.json()
    assert body["workflow"]["status"] == "NEW"
    assert body["financials"]["orderNumbers"] == []
    assert body["team"]["salesLead"] is None
    assert body["designServices"] is None

    resp = await api.get(f"{BASE}/projects/{body['id']}")
    assert resp.status_code == 200
    assert resp.json()["projectName"] == "HQ Refresh"


async def test_get_missing_project_returns_404(api):
    resp = await api.get(f"{BASE}/projects/{MISSING}")
    assert resp.status_code == 404


async def test_create_project_with_nested_objects(api, client_id):
    payload = project_payload(
        client_id,
        projectType="CORPORATE_GIFTING",
        team={"salesLead": "u-123", "artist3D": "u-777"},
        logistics={
            "deliveryType": "WHITE_GLOVE",
            "requirements": {"liftGate": True, "fullInstall": True},
        },
        corporateGifting={"isGiftBoxed": True, "giftMessage": {"content": "Thanks!"}},
    )
    resp = await api.post(f"{BASE}/projects", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["team"]["artist3D"] == "u-777"
    assert body["logistics"]["requirements"]["liftGate"] is True
    assert body["corporateGifting"]["isGiftBoxed"] is True


async def test_create_project_with_design_trigger_creates_subdoc(api, client_id):
    payload = project_payload(
        client_id, workflow={"triggers": {"requiresDesignServices": True}}
    )
    resp = await api.post(f"{BASE}/projects", json=payload)
    assert resp.status_code == 201
    assert resp.json()["designServices"] == {"designPackageId": None}


async def test_create_project_with_quote_trigger_advances_status(api, client_id):
    payload = project_payload(
        client_id, workflow={"triggers": {"isQuoteRequested": True}}
    )
    resp = await api.post(f"{BASE}/projects", json=payload)
    assert resp.status_code == 201
    assert resp.json()["workflow"]["status"] == "QUOTE_REQUESTED"
