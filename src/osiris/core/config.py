import os
import sys
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError, field_validator


# 📁 Cargar base de ruta del proyecto
BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    # 🌐 Entorno general
    ENVIRONMENT: str = Field("development")

    # 🔐 Configuración de la firma electrónica
    FEEC_P12_PATH: Path = Field(..., description="Ruta al archivo .p12")
    FEEC_P12_PASSWORD: str = Field(..., description="Contraseña del archivo .p12")
    FEEC_XSD_PATH: Path = Field(..., description="Ruta al archivo XSD del SRI")
    FEEC_AMBIENTE: str = Field("pruebas", description="Ambiente del SRI: pruebas o produccion")

    # 🗄️ Configuración de base de datos
    DATABASE_URL: str = Field("postgresql://postgres:postgres@localhost/osiris", description="URL de conexión a la base de datos")

    # ✅ Validación de rutas de archivos
    @field_validator("FEEC_P12_PATH", "FEEC_XSD_PATH")
    @classmethod
    def validate_file_exists(cls, v: Path, info):
        if not v.exists():
            raise ValueError(f"❌ El archivo definido en `{info.name}` no existe: {v}")
        return v

    # ✅ Validación del ambiente
    @field_validator("FEEC_AMBIENTE")
    @classmethod
    def validate_ambiente(cls, v: str):
        if v not in ("pruebas", "produccion"):
            raise ValueError("⚠️ FEEC_AMBIENTE debe ser 'pruebas' o 'produccion'")
        return v


# 🧪 Cargar configuración desde el archivo `.env.<environment>`
env_name = os.getenv("ENVIRONMENT", "development")
env_file_path = BASE_DIR / f".env.{env_name}"
env_values = dotenv_values(env_file_path)

try:
    settings = Settings(**env_values)
except ValidationError as e:
    print(f"\n❌ Error al cargar configuración del entorno `{env_file_path.name}`:\n")
    for err in e.errors():
        loc = " » ".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        print(f"  ❗ {loc}: {msg}")
    print(f"\n📁 Verifica que el archivo `{env_file_path.name}` esté completo y que las rutas existan y los valores sean válidos.")
    sys.exit(1)
