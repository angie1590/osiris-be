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
│       ├── api/              # Endpoints (FastAPI o similar)
│       ├── core/             # Configuración del entorno
│       │   └── config.py
│       ├── db/               # Configuración de la base de datos
│       ├── models/           # Modelos Pydantic / ORM
│       ├── services/         # Servicios de negocio
│       └── __init__.py
├── tests/                    # Pruebas unitarias
│   └── __init__.py
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

## 📦 Requisitos

- [Poetry](https://python-poetry.org/) `>=2.1.1`
- [Docker](https://www.docker.com/) y [Docker Compose](https://docs.docker.com/compose/)
- Python 3.10 (solo si corres sin Docker)

---

## ⚙️ Variables de Entorno

### `.env.development`
```env
ENVIRONMENT=development

# Firma electrónica
FEEC_P12_PATH=conf/archivo.p12
FEEC_P12_PASSWORD=p12_password
FEEC_XSD_PATH=conf/sri_docs/archivo.xsd
FEEC_AMBIENTE=[pruebas,prooduccion]

# Base de datos
POSTGRES_USER=db_user
POSTGRES_PASSWORD=db__pass
POSTGRES_DB=db
DATABASE_URL=postgresql://db_user:db_pass@db:port/db
```

### `.env.production`
Similar al anterior, pero adaptado al ambiente productivo.

---

## ▶️ Uso con Makefile

Estos comandos están disponibles para facilitar tu flujo de trabajo:

```bash
# Construir imagen y levantar contenedores
make build

# Solo levantar servicios sin reconstruir
make up

# Parar contenedores
make stop

# Eliminar contenedores y volúmenes
make clean

# Ejecutar tests
make test

# Ejecutar comandos dentro del contenedor
make bash
```

---

## 🚀 Instalación Local (sin Docker)

```bash
# Instalar dependencias con poetry
poetry install

# Activar entorno
poetry shell

# Ejecutar prueba de entorno
python test.py
```

---

## 📄 Uso de la Librería de Facturación Electrónica

La librería `fe-ec` se instala desde el paquete `.whl` incluido en `lib/`. Está incluida en el `pyproject.toml`:

```toml
dependencies = [
  "fe-ec @ file://./lib/fe_ec-0.1.0-py3-none-any-3.whl"
]
```

Puedes usar sus funcionalidades desde cualquier archivo en `osiris`:

```python
from fe_ec import GeneradorClaveAcceso, ManejadorXML
```

---

## 🧪 Pruebas

```bash
# Dentro del contenedor o en poetry shell:
pytest
```

---

## 🔐 Seguridad

No compartas los archivos `.p12` ni sus contraseñas. Se recomienda usar variables de entorno o un gestor de secretos para producción.

---

## 🧾 Autor

Desarrollado por [OpenLatina].