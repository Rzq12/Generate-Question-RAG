from app.ingestion.chunker import DocumentChunker
from app.ingestion.contracts import PageContent, ParsedDocument


def test_chunker_skips_blank_pages_and_preserves_page() -> None:
    document = ParsedDocument(document_id="doc", filename="a.pdf", file_hash="a" * 64, pages=(PageContent(document_id="doc", page_number=1, text="  ", source_hash="a" * 64), PageContent(document_id="doc", page_number=2, text="isi", source_hash="a" * 64)))
    chunks = DocumentChunker().chunk(document)
    assert len(chunks) == 1
    assert chunks[0].page_number == 2