from __future__ import annotations

from openai import OpenAI
import pytesseract
from PIL import Image

from .image_analyzer import LocalOcrAnalyzer, OpenAICompatibleVlmAnalyzer


def create_local_ocr_analyzer() -> LocalOcrAnalyzer:
    return LocalOcrAnalyzer(lambda data: pytesseract.image_to_string(Image.open(__import__("io").BytesIO(data))))


def create_vlm_analyzer(base_url: str, api_key: str, model: str) -> OpenAICompatibleVlmAnalyzer:
    return OpenAICompatibleVlmAnalyzer(OpenAI(base_url=base_url, api_key=api_key), model)