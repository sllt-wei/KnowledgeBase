import os
import json
import sqlite3
from common.log import logger
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *
from typing import Dict, Any

@plugins.register(
    name="KnowledgeBase",
    desc="知识库插件，支持文件上传和查询",
    version="1.0",
    author="sllt",
    desire_priority=500
)
class KnowledgeBase(Plugin):
    # 配置常量
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.db")

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self._initialize_database()
        logger.info(f"[{__class__.__name__}] initialized")

    def _initialize_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                content TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def on_handle_context(self, e_context):
        """处理用户输入的上下文"""
        if e_context['context'].type == ContextType.TEXT:
            content = e_context["context"].content.strip()
            if content == "上传":
                self._handle_upload_request(e_context)
            elif content.startswith("查询"):
                query = content[2:].strip()
                self._handle_query_request(e_context, query)
        elif e_context['context'].type == ContextType.FILE:
            self._handle_file_upload(e_context)

    def _handle_upload_request(self, e_context):
        """处理上传请求"""
        e_context["reply"] = Reply(ReplyType.TEXT, "请上传文件以保存到知识库")
        e_context.action = EventAction.BREAK_PASS

    def _handle_file_upload(self, e_context):
        """处理文件上传"""
        file = e_context["context"].content
        logger.debug(f"Received file content: {file_content}")
        try:
            # 尝试将 JSON 字符串解析为字典
            file = json.loads(file_content)
        except json.JSONDecodeError:
            e_context["reply"] = Reply(ReplyType.TEXT, "文件格式错误，请确保上传正确的文件")
            e_context.action = EventAction.BREAK_PASS
            return
            # 检查文件格式是否正确
        if not isinstance(file, dict) or "name" not in file or "content" not in file:
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

    def _handle_query_request(self, e_context, query):
        """处理查询请求"""
        conn = sqlite3.connect(self.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content FROM knowledge WHERE content LIKE ?
        ''', ('%' + query + '%',))
        results = cursor.fetchall()
        conn.close()

        if results:
            reply_text = "查询结果：\n" + "\n".join([result[0] for result in results])
        else:
            reply_text = "未找到相关结果"

        e_context["reply"] = Reply(ReplyType.TEXT, reply_text)
        e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        """获取插件帮助信息"""
        help_text = """知识库助手
        指令：
        发送"上传"：请求上传文件到知识库
        发送"查询 [关键字]"：查询知识库中的信息
        """
        return help_text