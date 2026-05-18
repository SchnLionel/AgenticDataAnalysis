import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage
from backend.agents.agent_manager import AgentManager
from backend.db import models

@pytest.fixture
def agent_manager():
    return AgentManager()

def test_agent_process_query_persists(client, db_session, agent_manager, auth_headers):
    # Setup: Create a session WITHOUT a dataset to avoid CSV loading
    user = db_session.query(models.User).filter(models.User.email == "api@example.com").first()
    
    session = models.AnalysisSession(user_id=user.id, dataset_id=None, title="Test Persistence")
    db_session.add(session)
    db_session.commit()
    
    # Mock LangGraph workflow invoke
    mock_workflow = MagicMock()
    mock_workflow.invoke.return_value = {
        "messages": [AIMessage(content="Hello! I see your dataset has 2 columns.")],
        "output_figures": []
    }
    
    mgr = AgentManager()
    mgr.workflow = mock_workflow
    
    result = mgr.process_query(
        db=db_session,
        session_id=session.id,
        user_id=user.id,
        query="Hello agent"
    )
    
    assert "Hello!" in result["synthesis"]
    
    # Verify persistence in DB
    messages = db_session.query(models.Message).filter(models.Message.session_id == session.id).all()
    assert len(messages) == 2  # User + Assistant
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
