# src/osiris/modules/inventario/producto/router.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from uuid import UUID

from osiris.core.db import get_session
from osiris.domain.schemas import PaginatedResponse
from .models import ProductoCreate, ProductoUpdate, ProductoCompletoRead
from .service import ProductoService

router = APIRouter()
service = ProductoService()

# Endpoint de listado con información completa
@router.get("/productos", response_model=PaginatedResponse[ProductoCompletoRead], tags=["Productos"])
def list_productos(
    limit: int = Query(50, ge=1, le=1000, description="Máximo de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a saltar"),
    only_active: bool = Query(True, description="Filtrar por activo=True/False"),
    session: Session = Depends(get_session),
):
    """Lista productos con toda su información completa (casa comercial, categorías, proveedores, atributos)"""
    items, meta = service.list_paginated_completo(session, only_active=only_active, limit=limit, offset=offset)
    return {"items": items, "meta": meta}


# Endpoint para obtener un producto específico con información completa
@router.get("/productos/{producto_id}", response_model=ProductoCompletoRead, tags=["Productos"])
def get_producto(
    producto_id: UUID,
    session: Session = Depends(get_session),
):
    """Obtiene un producto con toda su información completa"""
    return service.get_producto_completo(session, producto_id)


# Endpoint de creación
@router.post("/productos", response_model=ProductoCompletoRead, status_code=201, tags=["Productos"])
def create_producto(
    payload: ProductoCreate,
    session: Session = Depends(get_session),
):
    """Crea un nuevo producto"""
    producto = service.create(session, payload.model_dump(exclude_unset=True))
    return service.get_producto_completo(session, producto.id)


# Endpoint de actualización
@router.put("/productos/{producto_id}", response_model=ProductoCompletoRead, tags=["Productos"])
def update_producto(
    producto_id: UUID,
    payload: ProductoUpdate,
    session: Session = Depends(get_session),
):
    """Actualiza un producto existente"""
    producto = service.update(session, producto_id, payload.model_dump(exclude_unset=True))
    if not producto:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Producto {producto_id} no encontrado")
    return service.get_producto_completo(session, producto_id)


# Endpoint de eliminación (soft delete)
@router.delete("/productos/{producto_id}", status_code=204, tags=["Productos"])
def delete_producto(
    producto_id: UUID,
    session: Session = Depends(get_session),
):
    """Elimina (desactiva) un producto"""
    service.delete(session, producto_id)
    return None
