# src/domain/router.py
from fastapi import APIRouter, Depends, Query
from fastapi import Body
from typing import Any, Type
from sqlmodel import SQLModel, Session
from src.osiris.core.db import get_session

def register_crud_routes(
    *,
    router: APIRouter,
    prefix: str,
    tags: list[str],
    model_read: Type[SQLModel],
    model_create: Type[SQLModel],
    model_update: Type[SQLModel],
    service: Any,
):
    @router.get(f"/{prefix}", response_model=list[model_read], tags=tags)  # pyright: ignore[reportInvalidTypeForm]
    def list_items(
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        only_active: bool = True,
        session: Session = Depends(get_session),
    ):
        items, _ = service.list(session, only_active=only_active, limit=limit, offset=offset)
        return items

    @router.get(f"/{prefix}" + "/{item_id}", response_model=model_read, tags=tags)  # pyright: ignore[reportInvalidTypeForm]
    def get_item(item_id: str, session: Session = Depends(get_session)):
        return service.get(session, item_id)

    @router.post(f"/{prefix}", response_model=model_read, status_code=201, tags=tags)  # pyright: ignore[reportInvalidTypeForm]
    def create_item(
        payload: model_create = Body(...),  # pyright: ignore[reportInvalidTypeForm]
        session: Session = Depends(get_session),
    ):
        return service.create(session, payload.model_dump(exclude_unset=True))

    @router.patch(f"/{prefix}" + "/{item_id}", response_model=model_read, tags=tags)  # pyright: ignore[reportInvalidTypeForm]
    def update_item(
        item_id: str,
        payload: model_update = Body(...),  # pyright: ignore[reportInvalidTypeForm]
        session: Session = Depends(get_session),
    ):
        return service.update(session, item_id, payload.model_dump(exclude_unset=True))

    @router.delete(f"/{prefix}" + "/{item_id}", status_code=204, tags=tags)
    def delete_item(item_id: str, session: Session = Depends(get_session)):
        service.delete(session, item_id)
        return None
