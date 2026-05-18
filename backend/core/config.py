from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Data Analysis API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/datastream"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "datastream"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # AI Keys
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost",
        "http://127.0.0.1",
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

    def __init__(self, **values):
        super().__init__(**values)
        import os
        import sys
        # Skip validation during tests
        is_test = "pytest" in sys.modules or "pytest" in os.environ.get("PYTEST_CURRENT_TEST", "") or "test" in os.environ.get("DATABASE_URL", "")
        if is_test and not self.SECRET_KEY:
            self.SECRET_KEY = "test-secret-key-for-testing-purposes-only"
            
        if not is_test:
            if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-for-jwt" or len(self.SECRET_KEY) < 16:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: SECRET_KEY is missing, set to the insecure default, or is too short! "
                    "You must configure a strong, unique SECRET_KEY (e.g. via environment variables) for production/real-use."
                )
            if not self.GROQ_API_KEY:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: GROQ_API_KEY is missing! "
                    "This environment variable must be defined for the Agentic Data Analysis platform to perform LLM reasoning."
                )

settings = Settings()
