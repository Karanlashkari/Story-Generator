from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):

    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: Optional[str] = None
    ALLOWED_ORIGINS: str = ""

    OPENAI_API_KEY: Optional[str] = None

    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(",") if v else []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "forbid"  

settings = Settings()
