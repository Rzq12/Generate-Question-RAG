from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
import pytest

from app.ingestion.contracts import ImageContent, ImageInput, IngestionError
from app.ingestion.pdf_parser import PdfParser
from app.ingestion.pipeline import ingest_pdf


def _image_bytes(text: str | None) -> bytes:
    image = Image.new("RGB", (420, 160), "white")
    if text:
        ImageDraw.Draw(image).text((20, 60), text, fill="black")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _fixture_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Teks biasa dari halaman PDF.")
    page.insert_image(fitz.Rect(72, 100, 300, 180), stream=_image_bytes("Evidence gambar"))
    page.insert_image(fitz.Rect(320, 100, 450, 180), stream=_image_bytes(None))
    document.save(path)
    document.close()


def test_ingestion_keeps_text_and_only_meaningful_images(tmp_path: Path) -> None:
    path = tmp_path / "fixture.pdf"
    _fixture_pdf(path)

    def analyze(image: ImageInput) -> ImageContent:
        meaningful = image.image_id.endswith("i1")
        return ImageContent(
            image_id=image.image_id,
            page_number=image.page_number,
            meaningful=meaningful,
            extracted_text="Evidence gambar" if meaningful else "",
            confidence=1 if meaningful else 0,
            provider="test",
            model="fixture",
        )

    document = ingest_pdf(path, type("Analyzer", (), {"analyze": staticmethod(analyze)})())

    assert document.pages[0].text == "Teks biasa dari halaman PDF."
    assert [image.extracted_text for image in document.pages[0].images] == ["Evidence gambar"]


def test_parser_rejects_missing_and_non_pdf(tmp_path: Path) -> None:
    parser = PdfParser()

    with pytest.raises(IngestionError, match="file_not_found"):
        parser.parse(tmp_path / "missing.pdf")

    text_path = tmp_path / "input.txt"
    text_path.write_text("not a PDF")
    with pytest.raises(IngestionError, match="invalid_extension"):
        parser.parse(text_path)


def test_parser_rejects_corrupt_pdf(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a PDF")

    with pytest.raises(IngestionError, match="pdf_read_error"):
        PdfParser().parse(path)
