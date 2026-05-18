import os
import shutil
import pandas as pd
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from backend.db.database import get_db
from backend.db import models
from backend.api.schemas import sessions as schemas
from backend.api.routes.auth import get_current_user
from backend.agents.agent_manager import AgentManager

router = APIRouter(prefix="/sessions", tags=["sessions"])
agent_manager = AgentManager()

UPLOAD_DIR = os.path.abspath("uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=schemas.Session)
def create_session(
    session_in: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session = models.AnalysisSession(
        user_id=current_user.id,
        title=session_in.title,
        dataset_id=session_in.dataset_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/", response_model=List[schemas.Session])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.AnalysisSession).filter(
        models.AnalysisSession.user_id == current_user.id
    ).order_by(models.AnalysisSession.created_at.desc()).all()

@router.post("/upload", response_model=schemas.Dataset)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Analyze CSV for metadata
    df = pd.read_csv(file_path)
    column_info = {col: str(dtype) for col, dtype in df.dtypes.items()}
    
    dataset = models.Dataset(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        column_info=column_info,
        row_count=len(df)
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset

@router.get("/datasets", response_model=List[schemas.Dataset])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Dataset).filter(models.Dataset.user_id == current_user.id).all()

@router.get("/{session_id}", response_model=schemas.SessionDetail)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session = db.query(models.AnalysisSession).filter(
        models.AnalysisSession.id == session_id,
        models.AnalysisSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/query")
async def process_agent_query(
    session_id: int,
    request: schemas.QueryRequest,
    current_user: models.User = Depends(get_current_user)
):
    from backend.tasks import process_agent_query_task
    try:
        # Enqueue the task
        task = process_agent_query_task.delay(
            session_id=session_id,
            user_id=current_user.id,
            query=request.query
        )
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    from backend.celery_app import celery_app
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        return {"status": "processing"}
    elif task_result.state == 'SUCCESS':
        return {"status": "completed", "result": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"status": "failed", "error": str(task_result.info)}
    else:
        return {"status": task_result.state.lower()}
