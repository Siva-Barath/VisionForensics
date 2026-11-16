import pytest
from httpx import AsyncClient, ASGITransport
from app import app


@pytest.fixture
async def client():
    from app.database.session import SessionLocal
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password, create_access_token
    with SessionLocal() as db:
        repo = UserRepository(db)
        user = repo.get_by_email("api_fixture@visionforensics.local")
        if user is None:
            user = repo.create_user(email="api_fixture@visionforensics.local", password_hash=hash_password("IsolatedFixture123!"), full_name="Isolated API fixture")
        token = create_access_token(user.id, user.email, user.role)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Authorization": "Bearer " + token}) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_upload_invalid_type(client):
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_png(client):
    # Minimal valid 1x1 PNG (magic bytes: \x89PNG)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\r\xef"
        b"F\xb8\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.png", png_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()

    # Identity fields
    assert "job_id" in data
    assert "document_id" in data
    assert data["job_id"] != data["document_id"]  # must be independent UUIDs

    # File metadata
    assert data["type"] == "png"
    assert data["size_bytes"] > 0
    assert data["original_filename"] == "test.png"

    # Pipeline fields
    assert "processing_status" in data
    assert "pipeline_stage" in data
    assert isinstance(data["warnings"], list)

    # Image upload: single page, no PDF conversion
    assert data["page_count"] == 1


@pytest.mark.asyncio
async def test_upload_oversized_file(client):
    # 21 MB of zeros — exceeds the 20 MB default limit
    big_content = b"\x89PNG" + b"\x00" * (21 * 1024 * 1024)
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("big.png", big_content, "image/png")},
    )
    assert response.status_code == 413
