from __future__ import annotations

from tests.conftest import BASE, project_payload


async def _new_project(api, client_id) -> str:
    return (await api.post(f"{BASE}/projects", json=project_payload(client_id))).json()["id"]


async def _patch_workflow(api, pid, body):
    return await api.patch(f"{BASE}/projects/{pid}/workflow", json=body)


async def test_legal_transition(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_workflow(api, pid, {"status": "QUOTE_REQUESTED"})
    assert resp.status_code == 200
    assert resp.json()["workflow"]["status"] == "QUOTE_REQUESTED"


async def test_illegal_transition_returns_409(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_workflow(api, pid, {"status": "COMPLETE"})
    assert resp.status_code == 409


async def test_hold_resumes_only_to_held_from(api, client_id):
    pid = await _new_project(api, client_id)
    assert (await _patch_workflow(api, pid, {"status": "HOLD"})).status_code == 200

    # held from NEW -> may only resume to NEW
    bad = await _patch_workflow(api, pid, {"status": "QUOTE_REQUESTED"})
    assert bad.status_code == 409

    good = await _patch_workflow(api, pid, {"status": "NEW"})
    assert good.status_code == 200
    assert good.json()["workflow"]["status"] == "NEW"
    assert good.json()["workflow"]["heldFrom"] is None


async def test_trigger_automation_advances_status(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_workflow(api, pid, {"triggers": {"isQuoteRequested": True}})
    assert resp.json()["workflow"]["status"] == "QUOTE_REQUESTED"

    resp = await _patch_workflow(api, pid, {"triggers": {"isProductFinalized": True}})
    assert resp.json()["workflow"]["status"] == "PRODUCT_FINALIZED"


async def test_requires_design_services_trigger_creates_subdoc(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_workflow(
        api, pid, {"triggers": {"requiresDesignServices": True}}
    )
    assert resp.json()["designServices"] == {"designPackageId": None}


async def test_reaching_complete_sets_close_dates(api, client_id):
    pid = await _new_project(api, client_id)
    for target in ("QUOTE_REQUESTED", "PRODUCT_FINALIZED", "COMPLETE"):
        resp = await _patch_workflow(api, pid, {"status": target})
        assert resp.status_code == 200

    body = resp.json()
    assert body["workflow"]["status"] == "COMPLETE"
    assert body["closedAt"] is not None
    assert body["financials"]["projectCloseDate"] is not None


async def test_cancel_sets_closed_at_but_not_close_date(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_workflow(api, pid, {"status": "CANCELLED"})
    assert resp.status_code == 200
    assert resp.json()["closedAt"] is not None
    assert resp.json()["financials"]["projectCloseDate"] is None


async def test_delivery_need_by_date_update(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_workflow(api, pid, {"deliveryNeedByDate": "2026-12-01"})
    assert resp.status_code == 200
    assert resp.json()["workflow"]["deliveryNeedByDate"] == "2026-12-01"
