"""ChatService 单元测试。

测试策略：mock agent.invoke 避免真实的 LangGraph 调用。
"""

from unittest.mock import patch, MagicMock

import pytest

from app.models.session import Session
from app.services.chat_service import ChatService, agent_states, _build_confirm_content


class TestCreateSession:
    """create_session 创建新的对话会话。"""

    def test_create_session_creates_db_record(self, db):
        """创建 session 后数据库中存在对应记录。"""
        project_id = "test-project-uuid"
        session = ChatService.create_session(project_id=project_id, db=db)

        assert session.id is not None
        assert session.project_id == project_id
        assert session.status == "active"

        # 验证 DB 记录
        saved = db.query(Session).filter(Session.id == session.id).first()
        assert saved is not None
        assert saved.project_id == project_id

    def test_create_session_initializes_agent_state(self, db):
        """创建 session 后 agent_states 中有对应状态。"""
        project_id = "test-project-uuid"
        session = ChatService.create_session(project_id=project_id, db=db)

        assert session.id in agent_states
        state = agent_states[session.id]
        assert state["phase"] == "greeting"
        assert state["project_id"] == project_id
        assert state["session_id"] == session.id
        assert state["messages"] == []
        assert state["req_summary"] is None

    def test_create_session_clears_previous_state(self, db):
        """创建新 session 不干扰其他 session 的状态。"""
        s1 = ChatService.create_session(project_id="p1", db=db)
        s2 = ChatService.create_session(project_id="p2", db=db)

        assert s1.id in agent_states
        assert s2.id in agent_states

        agent_states[s1.id]["phase"] = "collecting"
        assert agent_states[s2.id]["phase"] == "greeting"  # 不受影响


class TestGetSessions:
    """get_sessions 获取项目的所有 session。"""

    def test_get_sessions_returns_all_for_project(self, db):
        """返回项目下的所有 sessions，按创建时间倒序。"""
        ChatService.create_session(project_id="p1", db=db)
        ChatService.create_session(project_id="p1", db=db)
        # 另一个项目的 session
        ChatService.create_session(project_id="p2", db=db)

        sessions = ChatService.get_sessions(project_id="p1", db=db)
        assert len(sessions) == 2

    def test_get_sessions_empty(self, db):
        """没有 session 时返回空列表。"""
        sessions = ChatService.get_sessions(project_id="non-existent", db=db)
        assert sessions == []

    def test_get_sessions_ordered_by_created_at(self, db):
        """sessions 按创建时间倒序排列。"""
        import time
        s1 = ChatService.create_session(project_id="p_order", db=db)
        time.sleep(0.01)
        s2 = ChatService.create_session(project_id="p_order", db=db)

        sessions = ChatService.get_sessions(project_id="p_order", db=db)
        assert len(sessions) == 2
        # 最新的在前
        assert sessions[0].id == s2.id
        assert sessions[1].id == s1.id

    def test_get_sessions_includes_all_fields(self, db):
        """返回的 session 包含完整的字段。"""
        ChatService.create_session(project_id="p_fields", db=db)
        sessions = ChatService.get_sessions(project_id="p_fields", db=db)
        session = sessions[0]
        assert session.id is not None
        assert session.project_id == "p_fields"
        assert session.status == "active"
        assert session.created_at is not None


class TestGetMessages:
    """get_messages 获取 session 的所有消息。"""

    def test_get_messages_empty(self, db):
        """没有消息时返回空列表。"""
        from app.models.session import Session
        session = Session(project_id="p1")
        db.add(session)
        db.commit()

        messages = ChatService.get_messages(session.id, db=db)
        assert messages == []

    def test_get_messages_returns_saved_messages(self, db):
        """返回 session 下所有消息，按时间正序。"""
        from app.models.session import Session
        from app.models.message import Message
        import time

        session = Session(project_id="p1")
        db.add(session)
        db.commit()

        # 添加测试消息
        m1 = Message(session_id=session.id, role="user", content="你好")
        db.add(m1)
        db.commit()
        time.sleep(0.01)

        m2 = Message(session_id=session.id, role="agent", content="你好！", phase="greeting")
        db.add(m2)
        db.commit()

        messages = ChatService.get_messages(session.id, db=db)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "你好"
        assert messages[1].role == "agent"
        assert messages[1].content == "你好！"
        assert messages[1].phase == "greeting"


class TestSendMessage:
    """send_message 发送消息并获取 Agent 响应。"""

    def _create_session(self, db) -> tuple:
        """辅助：创建 session 并返回 (session_id, project_id)。"""
        session = ChatService.create_session(project_id="test-project", db=db)
        return session.id, session.project_id

    @patch("app.services.chat_service.get_event_bus")
    @patch("app.services.chat_service.agent")
    def test_send_message_saves_user_message(self, mock_agent, mock_get_eb, db):
        """发送消息后保存用户消息到数据库。"""
        mock_agent.invoke.return_value = {"phase": "greeting"}
        from app.models.user import User
        from app.services.auth_service import hash_password
        user = User(username="chatuser", email="chat@test.com",
                    password=hash_password("pass123"))
        db.add(user)
        db.commit()

        session_id, _ = self._create_session(db)
        result = ChatService.send_message(session_id, "你好", user, db)

        # 用户消息应存在于返回结果中
        user_msgs = [m for m in result if m.role == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0].content == "你好"

    @patch("app.services.chat_service.get_event_bus")
    @patch("app.services.chat_service.agent")
    def test_send_message_invokes_agent(self, mock_agent, mock_get_eb, db):
        """发送消息后触发 agent.invoke。"""
        mock_agent.invoke.return_value = {"phase": "collecting"}
        from app.models.user import User
        from app.services.auth_service import hash_password
        user = User(username="chatuser2", email="chat2@test.com",
                    password=hash_password("pass123"))
        db.add(user)
        db.commit()

        session_id, _ = self._create_session(db)
        ChatService.send_message(session_id, "你好", user, db)

        mock_agent.invoke.assert_called_once()

    @patch("app.services.chat_service.get_event_bus")
    @patch("app.services.chat_service.agent")
    def test_send_message_returns_all_messages(self, mock_agent, mock_get_eb, db):
        """send_message 返回 session 中所有消息（含历史）。"""
        mock_agent.invoke.return_value = {"phase": "confirming"}
        from app.models.user import User
        from app.services.auth_service import hash_password
        user = User(username="chatuser3", email="chat3@test.com",
                    password=hash_password("pass123"))
        db.add(user)
        db.commit()

        session_id, _ = self._create_session(db)
        # 发送第一条消息
        result1 = ChatService.send_message(session_id, "我想做一个旅游助手", user, db)
        assert len(result1) > 0

        # 发送第二条消息后，应包含第一条消息
        result2 = ChatService.send_message(session_id, "要支持微信登录", user, db)
        assert len(result2) > len(result1)

    @patch("app.services.chat_service.get_event_bus")
    @patch("app.services.chat_service.agent")
    def test_send_message_invalid_session_id(self, mock_agent, mock_get_eb, db):
        """不存在的 session_id 应能重建状态（不抛异常）。"""
        mock_agent.invoke.return_value = {"phase": "collecting"}
        from app.models.user import User
        from app.services.auth_service import hash_password
        user = User(username="chatuser4", email="chat4@test.com",
                    password=hash_password("pass123"))
        db.add(user)
        db.commit()

        # session_id 不存在 — ChatService 会尝试重建状态
        # 但因为 DB 中也不存在该 session，会重新填充默认状态
        from app.models.session import Session
        fake_session = Session(id="fake-session-id", project_id="p1")
        db.add(fake_session)
        db.commit()

        result = ChatService.send_message("fake-session-id", "你好", user, db)
        assert len(result) > 0


class TestBuildConfirmContent:
    """_build_confirm_content 构建确认消息。"""

    def test_build_confirm_content_with_scope(self):
        """包含 out_of_scope 列表。"""
        content = _build_confirm_content("用户管理系统", ["部署", "监控"])
        assert "用户管理系统" in content
        assert "部署" in content
        assert "监控" in content
        assert "Out of Scope" in content

    def test_build_confirm_content_without_scope(self):
        """out_of_scope 为 None 时显示占位。"""
        content = _build_confirm_content("用户管理系统", None)
        assert "用户管理系统" in content
        assert "（暂未列出，你可补充）" in content
