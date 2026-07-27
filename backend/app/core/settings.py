from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int

    postgres_db: str
    postgres_user: str
    postgres_password: str

    qdrant_host: str
    qdrant_port: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()