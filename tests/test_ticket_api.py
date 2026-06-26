import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import get_session
from app.main import app
from app.models.base import Base

test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_session():
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[get_session] = _override_session


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_create_and_get_ticket(client: AsyncClient):
    response = await client.post(
        "/api/tickets/",
        json={"title": "Fix login bug", "description": "Login fails on Safari"},
    )
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["title"] == "Fix login bug"
    assert ticket["status"] == "pending"
    assert ticket["id"]

    response = await client.get(f"/api/tickets/{ticket['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Fix login bug"


async def test_list_tickets(client: AsyncClient):
    await client.post("/api/tickets/", json={"title": "Task 1"})
    await client.post("/api/tickets/", json={"title": "Task 2"})

    response = await client.get("/api/tickets/")
    assert response.status_code == 200
    assert len(response.json()) >= 2


async def test_update_ticket(client: AsyncClient):
    response = await client.post("/api/tickets/", json={"title": "Original"})
    ticket_id = response.json()["id"]

    response = await client.patch(
        f"/api/tickets/{ticket_id}",
        json={"title": "Updated", "status": "in_progress"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["status"] == "in_progress"


async def test_delete_ticket(client: AsyncClient):
    response = await client.post("/api/tickets/", json={"title": "To delete"})
    ticket_id = response.json()["id"]

    response = await client.delete(f"/api/tickets/{ticket_id}")
    assert response.status_code == 200

    response = await client.get(f"/api/tickets/{ticket_id}")
    assert response.status_code == 404


async def test_get_nonexistent_ticket(client: AsyncClient):
    response = await client.get("/api/tickets/nonexistent-id")
    assert response.status_code == 404


async def test_list_projects(client: AsyncClient):
    response = await client.get("/api/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert projects
    assert projects[0]["name"]
    assert projects[0]["path"]


async def test_hard_ticket_requires_review_before_execution(client: AsyncClient):
    response = await client.post(
        "/api/tickets/",
        json={
            "title": "Refactor checkout flow",
            "description": "Please update the checkout orchestration",
            "ticket_type": "request",
            "complexity": "hard",
            "requester_name": "FE",
            "auto_process": True,
        },
    )

    assert response.status_code == 201
    ticket = response.json()
    assert ticket["status"] == "review_required"
    assert ticket["review_status"] == "pending"
    assert ticket["agent_provider"] == "codex_pro_3_1"

    response = await client.get(f"/api/tickets/{ticket['id']}/messages")
    assert response.status_code == 200
    assert [message["role"] for message in response.json()] == ["user", "system"]


async def test_approve_hard_ticket_moves_to_queue(client: AsyncClient):
    response = await client.post(
        "/api/tickets/",
        json={
            "title": "Add audit log",
            "description": "Add audit logging to the API",
            "complexity": "hard",
            "auto_process": True,
        },
    )
    ticket_id = response.json()["id"]

    response = await client.post(
        f"/api/tickets/{ticket_id}/approve",
        json={"actor": "rafael"},
    )

    assert response.status_code == 200
    ticket = response.json()
    assert ticket["status"] == "queued"
    assert ticket["review_status"] == "approved"
    assert ticket["approved_by"] == "rafael"
