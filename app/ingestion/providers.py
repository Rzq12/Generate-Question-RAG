from __future__ import annotations

from openai import OpenAI
from rapidocr_onnxruntime import RapidOCR

from .image_analyzer import LocalOcrAnalyzer, OpenAICompatibleVlmAnalyzer


def create_local_ocr_analyzer() -> LocalOcrAnalyzer:
    engine = RapidOCR()

    def recognize(data: bytes) -> str:
        result, _ = engine(data)
        return "\n".join(str(item[1]) for item in (result or []) if len(item) > 1)

    return LocalOcrAnalyzer(recognize, model="rapidocr-onnxruntime")


def create_vlm_analyzer(base_url: str, api_key: str, model: str) -> OpenAICompatibleVlmAnalyzer:
    return OpenAICompatibleVlmAnalyzer(OpenAI(base_url=base_url, api_key=api_key), model)