from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    azure_tenant_id: str = Field(default="", alias="AZURE_TENANT_ID")
    azure_client_id: str = Field(default="", alias="AZURE_CLIENT_ID")
    azure_client_secret: str = Field(default="", alias="AZURE_CLIENT_SECRET")
    outlook_user_id: str = Field(default="me", alias="OUTLOOK_USER_ID")

    @property
    def is_configured(self) -> bool:
        return all([self.azure_tenant_id, self.azure_client_id, self.azure_client_secret])


def get_settings() -> Settings:
    return Settings()
