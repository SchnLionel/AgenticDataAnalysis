import json
from celery.utils.log import get_task_logger
from backend.celery_app import celery_app
from backend.agents.agent_manager import AgentManager
from backend.db.database import SessionLocal

logger = get_task_logger(__name__)

# Initialize AgentManager once per worker process to save memory
agent_manager = AgentManager()

@celery_app.task(bind=True, name="process_agent_query_task")
def process_agent_query_task(self, session_id: int, user_id: int, query: str):
    logger.info(f"Starting agent query for session {session_id}, user {user_id}")
    db = SessionLocal()
    try:
        result = agent_manager.process_query(
            db=db,
            session_id=session_id,
            user_id=user_id,
            query=query
        )
        # Ensure figures are serializable
        # figures are already JSON strings from pio.to_json
        return result
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise e
    finally:
        db.close()
