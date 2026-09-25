from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .contracts import IngestionError, PageContent, ParsedDocument


class DoclingParser:
    """Parse supported office documents through Docling."""

    _extensions = {".pdf", ".docx", ".pptx"}

    def __init__(self, converter: object | None = None) -> None:
        if converter is not None:
            self._converter = converter
            return
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise IngestionError("docling_unavailable", "Docling is not installed") from exc
        self._converter = DocumentConverter()

    def parse(self, path: Path) -> ParsedDocument:
        if not path.is_file():
            raise IngestionError("file_not_found", f"Document not found: {path}")
        if path.suffix.lower() not in self._extensions:
            raise IngestionError("invalid_extension", "Expected PDF, DOCX, or PPTX")

        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        document_id = str(uuid5(NAMESPACE_URL, digest))
        try:
            result = self._converter.convert(path)
            doc = result.document
            pages = tuple(
                PageContent(
                    document_id=document_id,
                    page_number=page_number,
                    text=doc.export_to_markdown(page_no=page_number).strip(),
                    source_hash=digest,
                )
                for page_number in range(1, doc.num_pages() + 1)
            )
        except Exception as exc:
            raise IngestionError("docling_read_error", str(exc)) from exc
        return ParsedDocument(
            document_id=document_id,
            filename=path.name,
            file_hash=digest,
            pages=pages,
        )