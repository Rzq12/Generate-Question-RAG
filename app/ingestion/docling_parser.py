from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .contracts import ImageAnalyzer, ImageInput, IngestionError, PageContent, ParsedDocument


class DoclingParser:
    """Parse supported office documents through Docling."""

    _extensions = {".pdf", ".docx", ".pptx"}

    def __init__(self, converter: object | None = None, image_analyzer: ImageAnalyzer | None = None) -> None:
        self._image_analyzer = image_analyzer
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
            page_values = []
            for page_number in range(1, doc.num_pages() + 1):
                raw_images = self._images_for_page(doc, page_number, document_id)
                page_values.append(PageContent(
                    document_id=document_id,
                    page_number=page_number,
                    text=doc.export_to_markdown(page_no=page_number).strip(),
                    raw_images=raw_images,
                    source_hash=digest,
                ))
            pages = tuple(page_values)
        except Exception as exc:
            raise IngestionError("docling_read_error", str(exc)) from exc
        parsed = ParsedDocument(
            document_id=document_id,
            filename=path.name,
            file_hash=digest,
            pages=pages,
            docling_document=doc,
        )
        if self._image_analyzer is None:
            return parsed
        pages = []
        for page in parsed.pages:
            images = tuple(self._image_analyzer.analyze(image) for image in page.raw_images)
            pages.append(page.model_copy(update={"images": tuple(item for item in images if item.meaningful)}))
        return parsed.model_copy(update={"pages": tuple(pages)})

    @staticmethod
    def _images_for_page(doc: object, page_number: int, document_id: str) -> tuple[ImageInput, ...]:
        result: list[ImageInput] = []
        for index, picture in enumerate(getattr(doc, "pictures", ())):
            prov = getattr(getattr(picture, "prov", ()), "__iter__", lambda: iter(()))()
            pages = [getattr(item, "page_no", None) for item in prov]
            if page_number not in pages:
                continue
            image = getattr(picture, "get_image", lambda _doc: None)(doc)
            if image is None:
                continue
            from io import BytesIO
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            result.append(ImageInput(page_number=page_number, image_id=f"{document_id}-image-{index}", media_type="image/png", data=buffer.getvalue()))
        return tuple(result)