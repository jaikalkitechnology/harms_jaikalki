from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class ApprovalActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: int
    approver_id: int
    action: str
    comments: Optional[str] = None
    delegated_to: Optional[int] = None
    action_at: datetime


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_type: str
    request_id: int
    employee_id: Optional[int]
    request_data: dict
    title: str
    summary: Optional[str]
    current_level: int
    max_levels: int
    status: str
    initiated_by: Optional[int]
    initiated_at: datetime
    final_status: Optional[str]
    final_decision_at: Optional[datetime]
    actions: List[ApprovalActionOut] = []


class ApprovalDecisionRequest(BaseModel):
    comments: Optional[str] = None


class ApprovalDelegateRequest(BaseModel):
    to_user_id: int
    comments: Optional[str] = None


class ApprovalCountByType(BaseModel):
    request_type: str
    count: int


class ApprovalWorkflowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    name: str
    description: Optional[str]
    levels_config: list
    conditions_json: Optional[dict]
    is_active: bool
