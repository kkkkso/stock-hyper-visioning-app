from antic_extensions import (
    RedisService, 
    PsqlDBClient
)
from ..settings import api_settings

__all__ = (
    'get_redis_service_client',
    'get_psql_client',
    'RedisService',
    'PsqlDBClient'
)

def get_redis_service_client() -> RedisService:
    """Redis Service Client를 전역적으로 관리하며 반환합니다."""
    if api_settings.REDIS_PASSWORD is None:
        raise EnvironmentError("REDIS_PASSWORD is not provided.")
    if not hasattr(get_redis_service_client, '_redis_service'):
        instance = RedisService(
            api_settings.REDIS_HOST, 
            api_settings.REDIS_PORT,
            api_settings.REDIS_PASSWORD,
            api_settings.REDIS_DATABASE
        )
        setattr(get_redis_service_client, 
                '_redis_service', instance)
    return getattr(get_redis_service_client,
                   '_redis_service')


def get_psql_client() -> PsqlDBClient:
    """PostgreSQL 관리 Client를 전역적으로 관리하며 반환합니다."""
    if api_settings.SQL_PASSWORD is None:
        raise EnvironmentError("SQL_PASSWORD is not provided.")
    if not hasattr(get_psql_client, '_sql_client'):
        instance = PsqlDBClient(
            api_settings.SQL_HOST, 
            api_settings.SQL_USER,
            api_settings.SQL_PASSWORD,
            api_settings.SQL_DATABASE
        )
        setattr(get_psql_client, 
                '_sql_client', instance)
    return getattr(get_psql_client,
                   '_sql_client')

