from __future__ import annotations

from fastapi import APIRouter

from osiris.modules.common.audit_log.router import router as audit_log_router
from osiris.modules.common.cliente.router import router as cliente_router
from osiris.modules.common.empleado.router import router as empleado_router
from osiris.modules.common.empresa.router import router as empresa_router
from osiris.modules.common.modulo.router import router as modulo_router
from osiris.modules.common.persona.router import router as persona_router
from osiris.modules.common.proveedor_persona.router import router as proveedor_persona_router
from osiris.modules.common.proveedor_sociedad.router import router as proveedor_sociedad_router
from osiris.modules.common.punto_emision.router import router as punto_emision_router
from osiris.modules.common.rol.router import router as rol_router
from osiris.modules.common.rol_modulo_permiso.router import router as rol_modulo_permiso_router
from osiris.modules.common.sucursal.router import router as sucursal_router
from osiris.modules.common.tipo_cliente.router import router as tipo_cliente_router
from osiris.modules.common.usuario.router import router as usuario_router


router = APIRouter(tags=["Common"])

router.include_router(rol_router, tags=["Common"])
router.include_router(empresa_router, tags=["Common"])
router.include_router(sucursal_router, tags=["Common"])
router.include_router(punto_emision_router, tags=["Common"])
router.include_router(audit_log_router, prefix="/v1", tags=["Common"])
router.include_router(persona_router, tags=["Common"])
router.include_router(tipo_cliente_router, tags=["Common"])
router.include_router(usuario_router, tags=["Common"])
router.include_router(cliente_router, tags=["Common"])
router.include_router(empleado_router, tags=["Common"])
router.include_router(proveedor_persona_router, tags=["Common"])
router.include_router(proveedor_sociedad_router, tags=["Common"])
router.include_router(modulo_router, tags=["Common"])
router.include_router(rol_modulo_permiso_router, tags=["Common"])
