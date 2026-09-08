from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    vllm_url: str
    vllm_model: str
    vllm_api_key: str

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # Personal progress lives in SQLite, separate from the course knowledge
    # graph. Relative to the server/ directory the app is launched from.
    progress_db_path: str = "data/progress.db"

    # Page-image retrieval. ColSmol-500M is the default because it costs about
    # 1 GB of VRAM against colqwen2-v1.0's 4.5 GB, and the machine running this
    # also has to render PDFs. Set colpali_model to vidore/colqwen2-v1.0 for
    # the stronger model; an index built by one is unusable by the other, so
    # rebuild after changing it.
    colpali_model: str = "vidore/colSmol-500M"


settings = Settings()
