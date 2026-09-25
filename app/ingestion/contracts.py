from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IngestionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class ImageInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    page_number: int = Field(ge=1)
    image_id: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    data: bytes = Field(min_length=1)


class ImageContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    image_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    meaningful: bool
    extracted_text: str = ""
    description: str | None = None
    confidence: float = Field(ge=0, le=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)

    @field_validator("extracted_text", "description", mode="before")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class PageContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    document_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    text: str = ""
    images: tuple[ImageContent, ...] = ()
    source_hash: str = Field(min_length=64, max_length=64)


class ParsedDocument(BaseModel):
    model_config = ConfigDict(frozen=True)
    document_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    file_hash: str = Field(min_length=64, max_length=64)
    pages: tuple[PageContent, ...]


class DocumentParser(Protocol):
    def parse(self, path: Path) -> ParsedDocument: ...


class ImageAnalyzer(Protocol):
    def analyze(self, image: ImageInput) -> ImageContent: ...
