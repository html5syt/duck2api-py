"""API 路由接口自动化测试。"""

import pytest
from httpx import ASGITransport, AsyncClient
from duck2api.main import app


@pytest.mark.asyncio
async def test_health_endpoints():
    """测试根路径与心跳健康检查。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Hello, world!"}

        ping_resp = await client.get("/ping")
        assert ping_resp.status_code == 200
        assert ping_resp.json() == {"message": "pong"}


@pytest.mark.asyncio
async def test_files_api():
    """测试 /v1/files 增删查接口。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 上传文件
        files = {"file": ("demo.txt", b"Hello from API test", "text/plain")}
        data = {"purpose": "assistants"}
        upload_resp = await client.post("/v1/files", files=files, data=data)
        assert upload_resp.status_code == 200
        file_data = upload_resp.json()
        assert file_data["filename"] == "demo.txt"
        file_id = file_data["id"]

        # 列出文件
        list_resp = await client.get("/v1/files")
        assert list_resp.status_code == 200
        assert any(f["id"] == file_id for f in list_resp.json()["data"])

        # 查询单文件
        get_resp = await client.get(f"/v1/files/{file_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == file_id

        # 下载文件内容
        content_resp = await client.get(f"/v1/files/{file_id}/content")
        assert content_resp.status_code == 200
        assert content_resp.content == b"Hello from API test"

        # 删除文件
        del_resp = await client.delete(f"/v1/files/{file_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True


@pytest.mark.asyncio
async def test_chat_validation_error():
    """测试请求校验失败场景。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 缺少必填参数 messages
        bad_req = {"model": "gpt-5.4-mini"}
        resp = await client.post("/v1/chat/completions", json=bad_req)
        assert resp.status_code == 422
