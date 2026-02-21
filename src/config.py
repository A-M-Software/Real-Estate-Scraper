# coding=utf-8

from pathlib import Path

from pydantic import BaseModel
from pydantic.fields import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DimRiaConfig(BaseModel):
    """
    Configuration for DimRia service, which provides additional user information.
    """

    api_key: str
    city_ids: list[int]


class OLXConfig(BaseModel):
    """
    Configuration for OLX service, which provides additional user information.
    """

    api_key: str


class TelegramConfig(BaseModel):
    """
    Configuration for Telegram Bot, used for notifications and alerts.
    """

    token: str
    chat_id: str


class LogConfig(BaseModel):
    """
    Configuration for logging, including log level and file path.
    """

    level: str = "INFO"
    path: Path = Path("logs")
    echo: bool = False


class Config(BaseSettings):
    """
    Schema for all script configurations, loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        env_ignore_empty=True,
        extra="ignore",
    )

    # Nested configuration models
    dim_ria: DimRiaConfig = Field(default_factory=DimRiaConfig)
    olx: OLXConfig = Field(default_factory=OLXConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    log: LogConfig = Field(default_factory=LogConfig)


# Load config
config = Config()
