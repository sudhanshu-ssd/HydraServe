from pydantic_settings import SettingsConfigDict,BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config =  SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

    Secret_key : SecretStr
    Groq_api_key : SecretStr 
    gemini_key : SecretStr
    database_url : SecretStr
    algo : str = 'HS256'
    access_token_expire_minutes : int = 30

    max_profile_pic_size_bytes :int = 5 * 1024 * 1024 # 5 mb

    reset_token_expire_minutes : int = 30

    mail_server : str = "smtp.resend.com"
    mail_port : int = 587
    mail_username : str = "resend"
    mail_from: str = "onboarding@resend.dev"
    mail_use_tls: bool = True

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5500,http://localhost:5173"
    mail_password : SecretStr  #this is your mail password

    s3_bucket_name :str 
    s3_region :str = "ap-south-1"
    s3_access_key : SecretStr | None = None
    s3_secret_access_key : SecretStr | None = None
    s3_endpoint_url: str | None = None

    estimated_tokens :int =  169

    langfuse_secret_key : SecretStr
    langfuse_public_key : SecretStr
    langfuse_base_url : str = "https://hipaa.cloud.langfuse.com"

    OTEL_Exporter_OTLP_Endpoint :str
    OTEL_Exporter_OTLP_Headers : str = ""

    admin_api_key: SecretStr 
    GRAFANA_CLOUD_PROMETHEUS_URL : str
    GRAFANA_CLOUD_PROMETHEUS_USERNAME :str
    GRAFANA_CLOUD_TEMPO_USERNAME :str
    GRAFANA_CLOUD_OTLP_ENDPOINT :str
    GRAFANA_CLOUD_TOKEN : SecretStr

    redis_url : str = "redis://localhost:6379/0"

settings = Settings()