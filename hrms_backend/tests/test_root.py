import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root_returns_company_info() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["company"] == "Jaikalki Technology Pvt Ltd"
    assert body["docs"] == "/docs"
