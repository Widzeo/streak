from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+psycopg://dev:dev@localhost:5432/streak"
    logical_day_start_hour: int = 4
    timezone: str = "Europe/Paris"


settings = Settings()
