from __future__ import annotations

from pathlib import Path

from .contracts import ImageAnalyzer, PageContent, ParsedDocument
from .pdf_parser import PdfParser


def ingest_pdf(path: Path, analyzer: ImageAnalyzer) -> ParsedDocument:
    parser = PdfParser()
    document, inputs = parser.parse_inputs(path)
    analyses = {item.image_id: analyzer.analyze(item) for item in inputs}
    pages = []
    for page in document.pages:
        images = tuple(analyses[item.image_id] for item in inputs if item.page_number == page.page_number and analyses[item.image_id].meaningful)
        pages.append(PageContent(**page.model_dump(exclude={"images"}), images=images))
    return ParsedDocument(**document.model_dump(exclude={"pages"}), pages=tuple(pages))
