# 🏛️ Osiris Backend

Backend del sistema empresarial **Osiris**, desarrollado en **Python 3.10** utilizando **Poetry** para la gestión de dependencias y **Docker** para contenerización. Este servicio maneja información tributaria, usuarios, empleados, clientes, proveedores, compras, ventas e inventario. Incluye una integración modular con la librería de facturación electrónica de Ecuador.

---

## 📁 Estructura del Proyecto

```
osiris-be/
├── conf/                      # Archivos de configuración (.p12, .xsd)
│   └── sri_docs/
│       └── factura_V1_1.xsd
│   └── firma.p12
├── lib/                      # Librería de facturación empaquetada (.whl)
│   └── fe_ec-0.1.0-py3-none-any-3.whl
├── src/
│   └── osiris/
│       ├── api/              # Endpoints REST
│       ├── core/             # Configuración del entorno
│       │   └── config.py
│       ├── db/               # Configuración de la base de datos, Alembic y modelos
│       │   ├── entities/
│       │   ├── repositories/
│       │   └── alembic/
│           └── versions/
│       ├── services/         # Lógica de negocio
│       ├── utils/            # Validaciones generales
│       └── main.py           # Punto de entrada
├── tests/                    # Pruebas unitarias y smoke tests
│   ├── smoke/               # Pruebas de integración y humo
│   │   ├── test_all_endpoints.py
│   │   ├── test_crud_smoke.py
│   │   ├── test_list_only.py
│   │   └── utils.py        # Utilidades para smoke tests
│   └── test_empresa.py     # Pruebas unitarias
├── .env.development          # Variables de entorno (desarrollo)
├── .env.production           # Variables de entorno (producción)
├── pyproject.toml            # Configuración de Poetry
├── poetry.lock
├── dockerfile                # Imagen para backend
├── docker-compose.yml        # Orquestación de contenedores
├── Makefile                  # Comandos útiles para desarrollo
└── README.md
```

---

## ⚙️ Variables de Entorno

Ejemplo `.env.development`:

```env
APP_ENV=development

# Firma electrónica
FEEC_P12_PATH=conf/firma.p12
FEEC_P12_PASSWORD=clave123
FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd
FEEC_AMBIENTE=1

# Base de datos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=osiris_db
DB_URL=postgresql+asyncpg://postgres:dev_password@db:5432/osiris_db
DB_URL_ALEMBIC=postgresql+psycopg2://postgres:dev_password@db:5432/osiris_db
```

---

## ▶️ Comandos con Makefile

```bash
make build      # Construye imagen Docker
make up         # Levanta los contenedores
make stop       # Detiene los servicios
make clean      # Elimina volúmenes y contenedores
make bash       # Acceso al contenedor
make migrate    # Ejecuta las migraciones Alembic
make test       # Ejecuta pruebas unitarias
make smoke      # Ejecuta smoke tests completos
make smoke-ci   # Ejecuta smoke tests seguros para CI (solo list)
```

Nota: en instalaciones modernas de Docker el comando es el plugin `docker compose` (espacio). El `Makefile` ya usa `docker compose --env-file ...`, por lo que los objetivos `make build`/`make up` funcionarán con la CLI moderna. Si tu sistema aún requiere el binario legacy `docker-compose`, instala `docker-compose` o crea un alias local.

---

## 🐳 Levantar el Proyecto desde Cero

```bash
# 1. Instalar dependencias
poetry install

# 2. Iniciar contenedores
make build
make up

# 3. Migrar la base de datos
make migrate

# 4. Ver la documentación Swagger
http://localhost:8000/docs
```

---

## 🌐 Documentación Swagger

Disponible automáticamente al levantar el sistema en:

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧱 Migraciones Alembic

```bash
# Crear una nueva revisión basada en los modelos
PYTHONPATH=src ENVIRONMENT=development poetry run alembic revision --autogenerate -m "mensaje"

# Aplicar migraciones
make migrate
```

---

## 📦 Librería de Facturación Electrónica

Se encuentra en `lib/` como `.whl` y se instala vía `pyproject.toml`:

```toml
fe-ec = { path = "./lib/fe_ec-0.1.0-py3-none-any-3.whl" }
```

Uso típico:

```python
from fe_ec import GeneradorClaveAcceso, ManejadorXML
```

---

## ✅ Pruebas

El proyecto incluye dos tipos de pruebas:

### Pruebas Unitarias

Las pruebas unitarias están en `tests/` (excluyendo `tests/smoke/`) y utilizan `pytest`:

```bash
make test
```

✅ Las pruebas unitarias usan mocks para evitar conexiones reales a la base de datos o al SRI.

### Smoke Tests

Los smoke tests están en `tests/smoke/` y validan la integración completa del sistema:

- `test_all_endpoints.py`: Flujos completos empresa/sucursal/punto_emision
- `test_crud_smoke.py`: Operaciones CRUD en endpoints principales
- `test_list_only.py`: Pruebas seguras para CI (solo GET)

Para ejecutar:

```bash
# Smoke tests completos (requiere sistema levantado)
make smoke

# Solo pruebas seguras para CI
make smoke-ci
```

Los smoke tests incluyen:
- Utilidades de retry y espera en `utils.py`
- Cliente HTTP configurado con timeouts
- Validación de RUC y datos empresariales
- Limpieza automática de recursos creados

⚠️ Requisitos para smoke tests:
- Docker y servicios levantados
- `.env.development` configurado
- Base de datos migrada

---

## 🔐 Seguridad

- No subir archivos `.p12` ni contraseñas al repositorio.
- Usar variables de entorno en `.env.{ambiente}` o secretos externos.

---

## 📞 Contacto

**OpenLatina**
📱 0984228883
📱 0995767370
