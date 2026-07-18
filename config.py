from pydantic_settings import SettingsConfigDict,BaseSettings
from pydantic import SecretStr



class Settings(BaseSettings):
    model_config =  SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

    Secret_key : SecretStr
    Groq_api_key : SecretStr 
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

    frontend_url: str = "http://localhost:5500"
    mail_password : SecretStr  #this is your mail password

    s3_bucket_name :str 
    s3_region :str = "ap-south-1"
    s3_access_key : SecretStr | None = None
    s3_secret_access_key : SecretStr | None = None
    s3_endpoint_url: str | None = None




settings = Settings()