from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum
from os import getenv
from dotenv import load_dotenv
load_dotenv()   # For another libraries having more security conditions...


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',  # extra=forbid (default)
        frozen=True  
    )

    # Sql Settings
    SQL_HOST: str               = getenv('SQL_HOST', 'localhost')
    SQL_USER: str               = getenv('SQL_USER', 'postgres')
    SQL_PORT: int               = 5432
    SQL_PASSWORD: Optional[str] = getenv('SQL_PASSWORD')
    SQL_DATABASE: str           = getenv('SQL_DATABASE', 'postgres')
    
    # Redis Settings
    REDIS_HOST: str             = getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int             = int(getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD: Optional[str] = getenv('REDIS_PASSWORD')
    REDIS_DATABASE: int         = 0



api_settings = ApiSettings()

