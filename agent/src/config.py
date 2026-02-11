from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Configuration
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "groq" # gemini, groq
    GEMINI_MODEL: str = "gemini-1.5-flash" # LLM model name gemini
    GROQ_MODEL: str = "llama-3.3-70b-versatile" # LLM model name groq

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # PostgreSQL Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "automlops"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # DigitalOcean Spaces
    DO_SPACES_KEY: Optional[str] = None
    DO_SPACES_SECRET: Optional[str] = None
    DO_SPACES_REGION: str = "nyc3"
    DO_SPACES_BUCKET: str = "automlops-models"
    
    # S3 Configuration
    S3_BUCKET: str = "automlops-models"
    S3_ENDPOINT: str = "nyc3.digitaloceanspaces.com"
    ENABLE_S3_UPLOAD: bool = False
    
    # Kubernetes & Deployment
    ENABLE_K8S_BUILD: bool = False
    REGISTRY_URL: str = "registry.digitalocean.com/automlops"
    ENABLE_DEPLOYMENT: bool = False
    
    # Training Configuration
    ENABLE_TRAINING: bool = False
    
    # Application
    TEMP_REPO_DIR: str = "/tmp/repos"
    LOG_LEVEL: str = "INFO"
    ORCHESTRATOR_URL: str = "http://localhost:8080"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
