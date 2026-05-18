import pytest
from backend.agents.agent_manager import AgentManager
from backend.db.models import AnalysisSession, User

@pytest.fixture
def mock_session(db_session):
    user = User(email="persist@test.com", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    
    session = AnalysisSession(user_id=user.id, title="Persist Test")
    db_session.add(session)
    db_session.commit()
    return session

def test_session_persistence_after_restart(db_session, mock_session, monkeypatch):
    # We mock ChatGroq to return a deterministic response instead of hitting the real API during testing.
    class MockChatGroq:
        def __init__(self, *args, **kwargs):
            pass
        def bind_tools(self, tools):
            return self
        def invoke(self, messages):
            # If the last message asks about color, reply with the context
            last_msg = messages[-1].content.lower()
            if "what is my favorite color" in last_msg:
                # Check history to find the color
                has_blue = any("blue" in msg.content.lower() for msg in messages)
                if has_blue:
                    from langchain_core.messages import AIMessage
                    return AIMessage(content="Your favorite color is blue.")
                else:
                    from langchain_core.messages import AIMessage
                    return AIMessage(content="I don't know your favorite color.")
            else:
                from langchain_core.messages import AIMessage
                return AIMessage(content="Noted.")

    monkeypatch.setattr("backend.agents.agent_manager.ChatGroq", MockChatGroq)

    agent_manager = AgentManager()
    
    # Send a message
    agent_manager.process_query(
        db=db_session,
        session_id=mock_session.id,
        user_id=mock_session.user_id,
        query="My favorite color is blue."
    )
    
    # Simulate restart by creating a new AgentManager instance
    new_agent_manager = AgentManager()
    
    # Ask a follow up question
    response_2 = new_agent_manager.process_query(
        db=db_session,
        session_id=mock_session.id,
        user_id=mock_session.user_id,
        query="What is my favorite color?"
    )
    
    assert "blue" in response_2["synthesis"].lower()
