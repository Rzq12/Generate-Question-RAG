from __future__ import annotations

from pathlib import Path

from .contracts import ImageAnalyzer, PageContent, ParsedDocument
from .docling_parser import DoclingParser
from .pdf_parser import PdfParser


def ingest_pdf(path: Path, analyzer: ImageAnalyzer) -> ParsedDocument:
    parser = PdfParser()
    document = parser.parse(path)
    inputs = tuple(image for page in document.pages for image in page.raw_images)
    analyses = {item.image_id: analyzer.analyze(item) for item in inputs}
    pages = []
    for page in document.pages:
        images = tuple(analyses[item.image_id] for item in page.raw_images if analyses[item.image_id].meaningful)
        pages.append(PageContent(**page.model_dump(exclude={"images", "raw_images"}), images=images))
    return ParsedDocument(**document.model_dump(exclude={"pages"}), pages=tuple(pages))


def ingest_document(path: Path, analyzer: ImageAnalyzer | None = None) -> ParsedDocument:
    document = DoclingParser().parse(path)
    if analyzer is None:
        return document
    inputs = tuple(image for page in document.pages for image in page.raw_images)
    analyses = {item.image_id: analyzer.analyze(item) for item in inputs}
    pages = [
        PageContent(
            **page.model_dump(exclude={"images", "raw_images"}),
            images=tuple(analyses[item.image_id] for item in page.raw_images if analyses[item.image_id].meaningful),
        )
        for page in document.pages
    ]
    return ParsedDocument(**document.model_dump(exclude={"pages"}), pages=tuple(pages))
