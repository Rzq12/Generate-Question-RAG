from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    postgres_dsn: str = "postgresql://generate_soal:generate_soal@localhost:5432/generate_soal"
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_model: str = ""
    image_analysis_mode: str = "ocr"
    ocr_engine: str = "tesseract"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024
    external_image_api_allowed: bool = False
    faiss_index_type: str = "IndexFlatIP"
    embedding_device: str = "cpu"
    max_upload_bytes: int = 52428800
    api_key: str = ""
    require_api_key: bool = False
    faiss_index_path: str = "/workspace/data/faiss"
