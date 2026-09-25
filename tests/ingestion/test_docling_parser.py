from pathlib import Path
from types import SimpleNamespace

from app.ingestion.docling_parser import DoclingParser


class FakeDocument:
    def num_pages(self) -> int:
        return 2

    def export_to_markdown(self, *, page_no: int) -> str:
        return f"# Page {page_no}"


class FakeConverter:
    def convert(self, path: Path) -> SimpleNamespace:
        return SimpleNamespace(document=FakeDocument())


def test_docling_parser_preserves_hash_name_and_pages(tmp_path: Path) -> None:
    path = tmp_path / "material.docx"
    path.write_bytes(b"document")

    result = DoclingParser(FakeConverter()).parse(path)

    assert result.filename == "material.docx"
    assert len(result.file_hash) == 64
    assert [page.text for page in result.pages] == ["# Page 1", "# Page 2"]