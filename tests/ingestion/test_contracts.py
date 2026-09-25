import pytest
from pydantic import ValidationError

from app.ingestion.contracts import ImageContent


def test_image_content_is_immutable_and_normalized() -> None:
    content = ImageContent(
        image_id="p1-i1",
        page_number=1,
        meaningful=True,
        extracted_text="  Judul  ",
        confidence=0.8,
        provider="test",
        model="test-model",
    )
    assert content.extracted_text == "Judul"
    with pytest.raises(ValidationError):
        content.confidence = 2


def test_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        ImageContent(image_id="i", page_number=1, confidence=2, provider="p", model="m")
