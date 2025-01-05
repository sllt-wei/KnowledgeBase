def _handle_file_upload(self, e_context):
    """处理文件上传"""
    file = e_context["context"].content
    logger.debug(f"Received file content: {file}")

    if not file:
        logger.error("Received empty file")
        e_context["reply"] = Reply(ReplyType.TEXT, "文件内容为空，请确保上传正确的文件")
        e_context.action = EventAction.BREAK_PASS
        return

    try:
        # 尝试将 JSON 字符串解析为字典
        file = json.loads(file)
        logger.debug(f"Parsed file content: {file}")
    except json.JSONDecodeError as e:
        # 捕获异常并记录
        logger.error(f"Failed to decode JSON: {e}")
        e_context["reply"] = Reply(ReplyType.TEXT, "文件格式错误，请确保上传正确的文件")
        e_context.action = EventAction.BREAK_PASS
        return

    # 检查文件格式是否正确
    if not isinstance(file, dict) or "name" not in file or "content" not in file:
        logger.error(f"File content is not a valid dictionary or missing 'name' or 'content': {file}")
        e_context["reply"] = Reply(ReplyType.TEXT, "文件格式错误，请确保上传正确的文件")
        e_context.action = EventAction.BREAK_PASS
        return

    file_name = file["name"]
    content = file["content"]

    conn = sqlite3.connect(self.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO knowledge (file_name, content) VALUES (?, ?)
    ''', (file_name, content))
    conn.commit()
    conn.close()

    e_context["reply"] = Reply(ReplyType.TEXT, f"文件 {file_name} 已保存到知识库")
    e_context.action = EventAction.BREAK_PASS
