"""Assigned tasks — see app/services/task_service.py."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models import User
from app.models.work_tasks import TASK_PRIORITIES, TASK_STATUSES
from app.services import task_service as svc

router = APIRouter(prefix="/tasks", tags=["tasks"])

_PRIORITY = "^(" + "|".join(TASK_PRIORITIES) + ")$"
_STATUS = "^(" + "|".join(TASK_STATUSES) + ")$"


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    assigned_to: int
    due_date: Optional[date] = None
    priority: str = Field(default="medium", pattern=_PRIORITY)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    priority: Optional[str] = Field(default=None, pattern=_PRIORITY)
    status: Optional[str] = Field(default=None, pattern=_STATUS)
    completion_note: Optional[str] = Field(default=None, max_length=1000)


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    assigned_to: int
    assignee_name: str
    assignee_code: Optional[str]
    assigned_by: Optional[int]
    assigner_name: Optional[str]
    due_date: Optional[date]
    priority: str
    status: str
    is_overdue: bool
    completed_at: Optional[datetime]
    completion_note: Optional[str]
    escalation_level: int
    comment_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    can_manage: bool
    is_mine: bool


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class CommentOut(BaseModel):
    id: int
    task_id: int
    user_id: Optional[int]
    author_name: str
    body: str
    created_at: Optional[datetime]


async def _one(db: AsyncSession, acc: svc.Access, task) -> dict:
    return (await svc.serialize(db, [task], acc))[0]


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    view: str = Query(default="mine", pattern="^(mine|given|team)$"),
    task_status: str = Query(default="open", alias="status", pattern="^(open|overdue|all|in_progress|done|cancelled)$"),
    employee_id: Optional[int] = None,
    scope: str = Query(default="all", pattern="^(direct|all)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    tasks = await svc.list_tasks(
        db, acc, view=view, status=task_status, employee_id=employee_id, scope=scope
    )
    return await svc.serialize(db, tasks, acc)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    return await _one(db, acc, await svc.create_task(db, acc, payload.model_dump()))


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    return await _one(db, acc, await svc.get_task(db, acc, task_id))


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    changes = payload.model_dump(exclude_unset=True)
    # Clearing is only meaningful for these; ignore nulls elsewhere.
    changes = {
        k: v for k, v in changes.items()
        if v is not None or k in ("description", "due_date", "completion_note")
    }
    return await _one(db, acc, await svc.update_task(db, acc, task_id, changes))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    await svc.delete_task(db, acc, task_id)


@router.get("/{task_id}/comments", response_model=list[CommentOut])
async def list_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    return [
        CommentOut(
            id=c.id, task_id=c.task_id, user_id=c.user_id,
            author_name=c.author_name, body=c.body, created_at=c.created_at,
        )
        for c in await svc.list_comments(db, acc, task_id)
    ]


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: int,
    payload: CommentIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    acc = await svc.access_for(db, user)
    c = await svc.add_comment(db, acc, task_id, payload.body)
    return CommentOut(
        id=c.id, task_id=c.task_id, user_id=c.user_id,
        author_name=c.author_name, body=c.body, created_at=c.created_at,
    )
