from pydantic import AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = ["http://localhost:8000"]
    OPENAPI_CLIENT_ID: str = ""
    APP_CLIENT_ID: str = ""
    APP_CLIENT_SECRET: str = ""
    TENANT_ID: str = ""
    DATABASE_URL: str = ""
    SQL_ECHO: bool = False

    SCOPE_DESCRIPTION: str = "user_impersonation"

    @computed_field
    @property
    def SCOPE_NAME(self) -> str:
        return f"api://{self.APP_CLIENT_ID}/{self.SCOPE_DESCRIPTION}"

    @computed_field
    @property
    def SCOPES(self) -> dict:
        return {
            self.SCOPE_NAME: self.SCOPE_DESCRIPTION,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
