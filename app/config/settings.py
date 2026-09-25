from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    postgres_dsn: str = "postgresql://generate_soal:generate_soal@localhost:5432/generate_soal"
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_model: str = ""
    image_analysis_mode: str = "ocr"
