from __future__ import annotations

from datetime import datetime, timedelta

from app.models.project import Project
from tests.conftest import BASE, CLIENT_PAYLOAD

MISSING = "00000000-0000-0000-0000-000000000000"


async def _make_client(api, name: str) -> str:
    return (
        await api.post(f"{BASE}/clients", json={**CLIENT_PAYLOAD, "companyName": name})
    ).json()["id"]


async def _make_project(api, client_id: str, name: str) -> str:
    return (
        await api.post(
            f"{BASE}/projects",
            json={"clientId": client_id, "projectName": name, "projectType": "GENERAL_B2B"},
        )
    ).json()["id"]


async def test_pagination(api, client_id):
    for i in range(5):
        await _make_project(api, client_id, f"P-{i}")

    resp = await api.get(f"{BASE}/projects", params={"page": 1, "size": 2})
    data = resp.json()
    assert data["pagination"] == {"page": 1, "size": 2, "total": 5, "pages": 3}
    assert len(data["items"]) == 2

    page3 = await api.get(f"{BASE}/projects", params={"page": 3, "size": 2})
    assert len(page3.json()["items"]) == 1


async def test_filter_by_client_id_and_name(api):
    acme = await _make_client(api, "Acme")
    globex = await _make_client(api, "Globex Industries")
    for i in range(3):
        await _make_project(api, acme, f"A-{i}")
    await _make_project(api, globex, "G-0")

    by_id = await api.get(f"{BASE}/projects", params={"clientId": globex})
    assert by_id.json()["pagination"]["total"] == 1
    assert by_id.json()["items"][0]["companyName"] == "Globex Industries"

    by_name = await api.get(f"{BASE}/projects", params={"clientName": "acme"})
    assert by_name.json()["pagination"]["total"] == 3


async def test_date_range_filter_on_created_at(api, client_id):
    fresh = await _make_project(api, client_id, "Fresh")
    stale = await _make_project(api, client_id, "Stale")

    doc = await Project.get(stale)
    doc.created_at = datetime.now().replace(tzinfo=None) - timedelta(days=10)
    await doc.save()

    cutoff = (datetime.now().date() - timedelta(days=1)).isoformat()

    recent = await api.get(f"{BASE}/projects", params={"dateFrom": cutoff})
    assert {i["id"] for i in recent.json()["items"]} == {fresh}

    older = await api.get(f"{BASE}/projects", params={"dateTo": cutoff})
    assert {i["id"] for i in older.json()["items"]} == {stale}


async def test_invalid_date_range_returns_422(api):
    resp = await api.get(
        f"{BASE}/projects", params={"dateFrom": "2026-05-01", "dateTo": "2026-04-01"}
    )
    assert resp.status_code == 422


async def test_invalid_sort_field_returns_422(api):
    resp = await api.get(f"{BASE}/projects", params={"sort": "-bogus"})
    assert resp.status_code == 422


async def test_client_projects_endpoint(api, client_id):
    await _make_project(api, client_id, "P1")
    await _make_project(api, client_id, "P2")

    resp = await api.get(f"{BASE}/clients/{client_id}/projects")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] == 2


async def test_client_projects_missing_client_returns_404(api):
    resp = await api.get(f"{BASE}/clients/{MISSING}/projects")
    assert resp.status_code == 404
