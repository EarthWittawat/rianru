from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    vllm_url: str
    vllm_model: str
    vllm_api_key: str

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str


settings = Settings()
