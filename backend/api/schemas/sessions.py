from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class VisualizationBase(BaseModel):
    figure_json: Dict[str, Any]
    title: Optional[str] = None

class MessageBase(BaseModel):
    role: str
    content: str
    created_at: datetime
    visualizations: List[VisualizationBase] = []

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    title: str
    dataset_id: Optional[int] = None

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class SessionDetail(Session):
    messages: List[MessageBase]

class DatasetBase(BaseModel):
    filename: str

class Dataset(DatasetBase):
    id: int
    user_id: int
    file_path: str
    column_info: Optional[Dict[str, Any]]
    row_count: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    synthesis: str
    figures: List[Dict[str, Any]]
