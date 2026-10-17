"""文件服务单元测试。"""

from duck2api.services.file_service import FileService


def test_file_service_crud_and_context():
    """测试文件的上传、读取、上下文构建与删除。"""
    service = FileService()

    # 1. 上传文件
    content = b"This is a test document content for Duck2API."
    file_obj = service.upload_file(
        filename="test.txt",
        content=content,
        mime_type="text/plain",
        purpose="assistants",
    )
    assert file_obj.id.startswith("file-")
    assert file_obj.filename == "test.txt"
    assert file_obj.bytes == len(content)

    # 2. 列出文件
    file_list = service.list_files()
    assert len(file_list.data) == 1
    assert file_list.data[0].id == file_obj.id

    # 3. 获取单文件
    stored = service.get_file(file_obj.id)
    assert stored is not None
    assert stored.content == content

    # 4. 构建上下文
    ctx = service.build_file_context([file_obj.id])
    assert "[Attached File: test.txt]" in ctx
    assert "This is a test document content for Duck2API." in ctx

    # 5. 删除文件
    deleted = service.delete_file(file_obj.id)
    assert deleted is True
    assert service.get_file(file_obj.id) is None
    assert len(service.list_files().data) == 0
