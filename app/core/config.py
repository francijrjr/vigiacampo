from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "API PNCD - Registro de Atividades"
    PROJECT_DESCRIPTION: str = """
    API para o Sistema de Registro de Atividades para Agentes de Combate às Endemias (PNCD).
    
    Suporta operação offline-first com sincronização em lote, autenticação JWT,
    e relatórios de atividades. O PDF não substitui o formulário oficial.
    Para testar: faça login, copie access_token e cole em Authorize.
    """
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SEED_DEMO: bool = False
    AUTO_CREATE_TABLES: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Security
    SECRET_KEY: str = "pncd-secret-key-change-in-production-please-use-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./pncd.db"
    
    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
