# 🏛️ Osiris Backend

Backend del sistema empresarial **Osiris**, desarrollado en **Python 3.10** utilizando **Poetry** para la gestión de dependencias y **Docker** para contenerización. Este servicio maneja información tributaria, usuarios, empleados, clientes, proveedores, compras, ventas e inventario. Incluye una integración modular con la librería de facturación electrónica de Ecuador.

---

## 📁 Estructura del Proyecto

```
osiris-be/
├── conf/                      # Archivos de configuración (.p12, .xsd, JSON catálogos SRI)
│   ├── aux_impuesto_catalogo.json
│   ├── firma.p12
│   └── sri_docs/
│       └── factura_V1_1.xsd
├── lib/                      # Librería de facturación empaquetada (.whl)
│   └── fe_ec-0.1.0-py3-none-any-3.whl
├── scripts/                  # Scripts de utilidad y seed
│   ├── seed_sample_product.py
│   └── cleanup_test_data.py
├── src/
│   └── osiris/
│       ├── core/            # Configuración (settings, db, security, errors)
│       │   ├── settings.py
│       │   ├── db.py
│       │   └── security.py
│       ├── db/              # Migraciones Alembic
│       │   └── alembic/
│       │       └── versions/
│       ├── domain/          # Modelos base, repositorios, servicios, routers genéricos
│       │   ├── base_models.py
│       │   ├── repository.py
│       │   ├── service.py
│       │   └── router.py
│       ├── modules/         # Módulos de dominio (common, aux, inventario)
│       │   ├── common/      # Entidades comunes (empresa, persona, cliente, etc.)
│       │   ├── aux/         # Catálogos auxiliares (impuestos, tipo_contribuyente)
│       │   └── inventario/  # Módulo de inventario (producto, categoría, etc.)
│       ├── utils/           # Utilidades (validaciones, paginación)
│       └── main.py          # Punto de entrada FastAPI
├── tests/                   # Pruebas unitarias y smoke tests
│   ├── smoke/              # Pruebas de integración
│   │   ├── test_all_endpoints.py
│   │   ├── test_crud_smoke.py
│   │   ├── test_producto_smoke.py
│   │   └── utils.py
│   ├── test_empresa.py     # Pruebas unitarias
│   ├── test_producto.py
│   └── test_impuesto_catalogo.py
├── .env.development         # Variables de entorno (desarrollo)
├── pyproject.toml           # Configuración de Poetry
├── poetry.lock
├── Dockerfile.dev           # Imagen Docker para desarrollo
├── docker-compose.yml       # Orquestación de contenedores
├── Makefile                 # Comandos útiles para desarrollo
└── README.md
```

---

## ⚙️ Variables de Entorno

⚠️ **El archivo `.env.development` NO está en el repositorio por seguridad.** Debes crearlo manualmente en la raíz del proyecto.

Ejemplo `.env.development`:

```env
ENVIRONMENT=development

# Base de datos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=osiris_db
DATABASE_URL=postgresql+psycopg2://postgres:dev_password@postgres/osiris_db
DB_URL_ALEMBIC=postgresql+psycopg2://postgres:dev_password@postgres/osiris_db

# Facturación Electrónica Ecuador
# Rutas relativas al directorio /app dentro del contenedor
FEEC_P12_PATH=conf/firma.p12
FEEC_P12_PASSWORD=clave123
FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd
FEEC_AMBIENTE=pruebas

# Configuraciones adicionales
SQL_ECHO=true
EMP_MIN_AGE=16
```

---

## ▶️ Comandos con Makefile

```bash
# Desarrollo
make build              # Construye imagen Docker
make run                # Levanta los contenedores (build + up -d)
make stop               # Detiene los servicios
make shell              # Acceso al contenedor backend
make logs               # Ver logs en tiempo real

# Base de datos
make db-upgrade         # Ejecuta migraciones Alembic
make db-makemigration   # Crea nueva migración autogenerada (requiere mensaje="...")
make db-recreate        # Recrea base de datos desde cero (⚠️ destruye datos)

# Testing
make test               # Ejecuta pruebas unitarias (169 tests)
make smoke              # Ejecuta smoke tests completos (requiere sistema levantado)
make smoke-ci           # Ejecuta smoke tests seguros para CI (solo GET)

# Utilidades
make lint               # Ejecuta linters (ruff + mypy)
make seed               # Carga datos de ejemplo (producto con impuestos)
make cleanup-test-data  # Limpia datos de prueba
make validate           # Valida configuración del entorno (multiplataforma)
```

Nota: en instalaciones modernas de Docker el comando es el plugin `docker compose` (espacio). El `Makefile` ya usa `docker compose --env-file ...`, por lo que los objetivos `make build`/`make up` funcionarán con la CLI moderna. Si tu sistema aún requiere el binario legacy `docker-compose`, instala `docker-compose` o crea un alias local.

### 🖥️ Compatibilidad Multiplataforma (Mac/Windows/Linux)

El proyecto está configurado para funcionar en **Mac, Windows 11 y Linux** sin cambios:

✅ **Cambios aplicados para compatibilidad:**
- Docker detecta automáticamente la arquitectura (ARM64/AMD64)
- Variables de entorno se pasan con `-e` (compatible con todos los sistemas)
- El PYTHONPATH se define en el Dockerfile (no se redefine en comandos)
- Rutas de archivos usan formato Linux dentro del contenedor

⚠️ **Requisitos por sistema operativo:**
- **Windows**: Docker Desktop con WSL2 habilitado
- **Mac**: Docker Desktop (Intel o Apple Silicon)
- **Linux**: Docker Engine + Docker Compose plugin

💡 **Si usas Windows y tienes errores:**
- Asegúrate de que WSL2 esté activo: `wsl --status`
- Verifica Docker Desktop en modo Linux containers
- Los archivos `.env.development` deben tener line endings LF (no CRLF)

### 🔍 Script de Validación

Antes de iniciar el proyecto, puedes validar tu configuración:

```bash
# Recomendado: Usar Makefile (funciona en Mac/Windows/Linux)
make validate

# O manualmente con Python:
# Mac/Linux:
python3 scripts/validate_setup.py

# Windows PowerShell:
python scripts/validate_setup.py
```

El script verifica:
- ✓ Docker y Docker Compose instalados
- ✓ WSL2 activo (Windows)
- ✓ Archivo `.env.development` presente y completo
- ✓ Configuración correcta de PYTHONPATH
- ✓ Compatibilidad multiplataforma (sin platform hardcodeado)

---

## 🐳 Levantar el Proyecto desde Cero

```bash
# 0. (Recomendado) Validar configuración
make validate

# 1. Instalar dependencias localmente (opcional, útil para IDE)
poetry install

# 2. Iniciar contenedores
make build
make run

# 3. Migrar la base de datos
make db-upgrade

# 4. (Opcional) Seed de datos de ejemplo
make seed
# O manualmente:
# docker compose --env-file .env.development exec osiris-backend poetry run python scripts/seed_sample_product.py

# 5. Ver la documentación Swagger
http://localhost:8000/docs
```

---

## 🧾 Catálogo de Impuestos SRI

El sistema incluye el catálogo oficial de impuestos del SRI (Servicio de Rentas Internas de Ecuador) precargado mediante migraciones:

- **84 registros** de impuestos: 9 IVA + 75 ICE
- Cargados desde `conf/aux_impuesto_catalogo.json`
- Fecha de vigencia por defecto: `2023-02-01`

### Estructura de Impuestos

- `codigo_tipo_impuesto`: Código del tipo de impuesto según SRI (2=IVA, 3=ICE, 5=IRBPNR)
- `codigo_sri`: Código único de tarifa SRI
- `descripcion`: Descripción del impuesto
- **Restricción unique**: Combinación `(codigo_sri, descripcion)` permite códigos ICE repetidos con distintas descripciones

### Endpoint: `GET /api/impuestos-catalogo`

- **Paginación**: `limit` (int) y `offset` (int)
- **Filtro por tipo**: `tipo_impuesto` opcional (`IVA`, `ICE`, `IRBPNR`)
- **Respuesta**:
  - `items`: Lista de impuestos con información completa
  - `meta`: `{ total, limit, offset, page, page_count }`

## 🛒 Productos e Impuestos

### Reglas de Negocio

- **IVA obligatorio**: Todos los productos deben tener exactamente un impuesto IVA
- **Máximo un impuesto por tipo**: Un producto puede tener máximo 1 IVA, 1 ICE, 1 IRBPNR
- **Reemplazo automático**: Asignar un nuevo impuesto del mismo tipo reemplaza el anterior
- **IVA no eliminable**: El IVA solo puede reemplazarse, no eliminarse directamente
- **Compatibilidad tipo**: Los impuestos validan compatibilidad con el tipo de producto (BIEN/SERVICIO)
- **Vigencia**: Solo se pueden asignar impuestos vigentes

### Endpoints de Productos

```
POST   /api/productos                                    # Crear producto
GET    /api/productos                                    # Listar productos (paginado)
GET    /api/productos/{producto_id}                      # Detalle completo con impuestos
PUT    /api/productos/{producto_id}                      # Actualizar producto
DELETE /api/productos/{producto_id}                      # Eliminar (soft delete)
```

### Endpoints de Impuestos de Producto

```
GET    /api/productos/{producto_id}/impuestos            # Listar impuestos del producto
POST   /api/productos/{producto_id}/impuestos            # Asignar impuesto
       ?impuesto_catalogo_id=UUID&usuario_auditoria=str  # (reemplaza si existe mismo tipo)
DELETE /api/productos/impuestos/{producto_impuesto_id}   # Eliminar (excepto IVA)
```

### Flujo de Creación de Producto

Al crear un producto mediante `POST /api/productos`:
1. NO se especifican `impuesto_catalogo_ids` en el payload inicial
2. El producto se crea sin impuestos
3. Se asignan impuestos después mediante `POST /{producto_id}/impuestos`
4. El primer impuesto debe ser un IVA (obligatorio)

---

## 🌐 Documentación Swagger

Disponible automáticamente al levantar el sistema en:

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧱 Migraciones Alembic

```bash
# Crear una nueva revisión basada en los modelos (desde dentro del contenedor)
docker compose --env-file .env.development exec -e ENVIRONMENT=development osiris-backend poetry run alembic revision --autogenerate -m "mensaje"
# O usar el alias:
make db-makemigration mensaje="descripción de la migración"

# Aplicar migraciones pendientes
make db-upgrade

# Revertir última migración
docker compose --env-file .env.development exec osiris-backend poetry run alembic downgrade -1

# Ver historial de migraciones
docker compose --env-file .env.development exec osiris-backend poetry run alembic history
```

⚠️ **Migraciones existentes:**
- `cec1e957113e`: Cambio de restricción única en `aux_impuesto_catalogo` (codigo_sri → codigo_sri + descripcion)
- `20f3d9f4a008`: Carga inicial de 84 registros del catálogo SRI desde JSON

---

## 📦 Librería de Facturación Electrónica (fe-ec)

Librería local en `lib/fe_ec-0.1.0-py3-none-any-3.whl`, instalada vía `pyproject.toml`:

```toml
[tool.poetry.dependencies]
fe-ec = { file = "lib/fe_ec-0.1.0-py3-none-any-3.whl" }
```

**Uso típico:**

```python
from fe_ec import GeneradorClaveAcceso, ManejadorXML

# Generar clave de acceso para factura electrónica
clave = GeneradorClaveAcceso.generar(
    fecha_emision="01/02/2024",
    tipo_comprobante="01",  # Factura
    ruc="1234567890001",
    ambiente="1",  # Pruebas
    serie="001001",
    numero_secuencial="000000001",
    codigo_numerico="12345678",
    tipo_emision="1"
)

# Generar XML firmado
xml_firmado = ManejadorXML.firmar_xml(
    xml_sin_firmar,
    ruta_certificado="conf/firma.p12",
    password_certificado="contraseña"
)
```

⚠️ **Nota:** La librería no está en PyPI, se distribuye como `.whl` local. Requiere certificados `.p12` válidos para firmar documentos electrónicos.

---

## ✅ Pruebas

El proyecto mantiene **169 tests unitarios** pasando. Se dividen en dos categorías:

### Pruebas Unitarias (tests/)

Validan lógica de negocio aisladamente con mocks:

```bash
make test  # Ejecuta pytest con 169 tests
```

**Cobertura:**
- Validaciones (identificación, impuestos, productos)
- Servicios CRUD (cliente, empleado, empresa, proveedor)
- Repositorios (validación de duplicados, catálogo de impuestos)
- Utilidades (paginación, jerarquía de categorías)

✅ No requieren base de datos real (usa mocks).

### Smoke Tests (tests/smoke/)

Validan integración completa contra sistema levantado:

```bash
# Smoke tests completos (POST/PUT/DELETE)
make smoke

# Solo pruebas seguras para CI (GET)
make smoke-ci
```

**Archivos principales:**
- `test_all_endpoints.py`: Flujos empresa → sucursal → punto_emision
- `test_crud_smoke.py`: CRUD completo de endpoints principales
- `test_producto_crud_completo_smoke.py`: Creación de productos con impuestos/categorías/atributos
- `test_list_only.py`: Validación de listados (seguro para CI)
- `utils.py`: Retry automático, cliente HTTP, limpieza de recursos

⚠️ **Requisitos para smoke tests:**
- Sistema levantado (`make run`)
- Base de datos migrada (`make db-upgrade`)
- `.env.development` configurado
- Catálogo de impuestos cargado (84 registros SRI)

---

## 🔐 Seguridad

**Archivos sensibles protegidos:**
- `.env.*` → Excluido en `.gitignore` (nunca versionar credenciales)
- `conf/firma.p12` → Certificado digital (mantener fuera del repo)
- Contraseñas de BD y P12 → Usar secretos externos en producción

**Mejores prácticas:**
- En desarrollo: `.env.development` local (no versionado)
- En producción: Variables de entorno del sistema o secret managers (AWS Secrets Manager, HashiCorp Vault, etc.)
- Rotar certificados `.p12` según políticas de seguridad del SRI

---

## 📞 Contacto

**OpenLatina**
📱 0984228883
📱 0995767370
