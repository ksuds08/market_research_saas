import os
from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    serpapi_key: str = Field(..., env="SERPAPI_KEY")
    openai_key: str = Field(..., env="OPENAI_API_KEY")

    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")
    broker_url: str = redis_url
    result_backend: str = redis_url

    api_title: str = "Market‑Research SaaS"
    api_version: str = "0.1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
