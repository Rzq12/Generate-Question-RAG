from __future__ import annotations

import argparse
from pathlib import Path

from app.config.settings import Settings
from app.ingestion.chunker import DocumentChunker
from app.ingestion.docling_parser import DoclingParser
from app.ingestion.providers import create_local_ocr_analyzer, create_vlm_analyzer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    parser.add_argument("--without-ocr", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    analyzer = None if args.without_ocr else create_local_ocr_analyzer()
    document = DoclingParser(image_analyzer=analyzer).parse(args.document)
    chunks = DocumentChunker().chunk(document)
    print({"document_id": document.document_id, "filename": document.filename, "pages": len(document.pages), "chunks": len(chunks), "embedding_model": settings.embedding_model})


if __name__ == "__main__":
    main()