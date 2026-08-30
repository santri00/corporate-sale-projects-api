from __future__ import annotations

from tests.conftest import BASE, project_payload


async def _new_project(api, client_id) -> str:
    return (await api.post(f"{BASE}/projects", json=project_payload(client_id))).json()["id"]


async def _patch_financials(api, pid, body, array_mode=None):
    params = {"arrayMode": array_mode} if array_mode else None
    return await api.patch(f"{BASE}/projects/{pid}/financials", json=body, params=params)


async def test_update_scalar_fields(api, client_id):
    pid = await _new_project(api, client_id)
    resp = await _patch_financials(
        api,
        pid,
        {
            "budget": 50000,
            "totalSale": 61250.5,
            "paymentTerms": "50% deposit, balance on delivery",
            "billingAddress": {
                "line1": "500 Market St",
                "city": "SF",
                "state": "CA",
                "postalCode": "94105",
                "country": "USA",
            },
        },
    )
    assert resp.status_code == 200
    fin = resp.json()["financials"]
    assert fin["budget"] == 50000
    assert fin["totalSale"] == 61250.5
    assert fin["billingAddress"]["line1"] == "500 Market St"


async def test_array_replace_is_default(api, client_id):
    pid = await _new_project(api, client_id)
    await _patch_financials(api, pid, {"orderNumbers": ["A", "B"]})
    resp = await _patch_financials(api, pid, {"orderNumbers": ["C"]})
    assert resp.json()["financials"]["orderNumbers"] == ["C"]


async def test_array_append_mode_dedupes(api, client_id):
    pid = await _new_project(api, client_id)
    await _patch_financials(api, pid, {"quoteIds": ["Q1", "Q2"]})
    resp = await _patch_financials(
        api, pid, {"quoteIds": ["Q2", "Q3"]}, array_mode="append"
    )
    assert resp.json()["financials"]["quoteIds"] == ["Q1", "Q2", "Q3"]


async def test_array_remove_mode(api, client_id):
    pid = await _new_project(api, client_id)
    await _patch_financials(api, pid, {"orderNumbers": ["A", "B", "C"]})
    resp = await _patch_financials(
        api, pid, {"orderNumbers": ["B"]}, array_mode="remove"
    )
    assert resp.json()["financials"]["orderNumbers"] == ["A", "C"]


async def test_patch_does_not_touch_unset_fields(api, client_id):
    pid = await _new_project(api, client_id)
    await _patch_financials(api, pid, {"budget": 1000, "orderNumbers": ["X"]})
    resp = await _patch_financials(api, pid, {"totalSale": 2000})
    fin = resp.json()["financials"]
    assert fin["budget"] == 1000
    assert fin["orderNumbers"] == ["X"]
    assert fin["totalSale"] == 2000
