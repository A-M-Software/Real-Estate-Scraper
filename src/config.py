# coding=utf-8

from pathlib import Path

from pydantic import BaseModel
from pydantic.fields import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseClientConfig(BaseModel):
    """
    Base configuration for API clients, including common parameters.
    """

    api_key: str
    data_file: Path


class DimRiaConfig(BaseClientConfig):
    """
    Configuration for DimRia service, which provides additional user information.
    """

    city_ids: list[int]


class OLXConfig(BaseClientConfig):
    """
    Configuration for OLX service, which provides additional user information.
    """

    api_key: str = None  # We're not using their API at the moment
    client_id: str = None
    client_secret: str = None


class TelegramConfig(BaseModel):
    """
    Configuration for Telegram Bot, used for notifications and alerts.
    """

    token: str
    chat_id: str


class BotConfig(BaseModel):
    """
    Configuration for the bot's behavior, such as polling intervals and retry settings.
    """

    employees_file: Path



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
    bot: BotConfig = Field(default=BotConfig)
    log: LogConfig = Field(default_factory=LogConfig)

    # Other settings
    advertisements_file: Path


# Load config
config = Config()
