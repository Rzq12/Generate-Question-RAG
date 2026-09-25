from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

import fitz

from .contracts import ImageInput, IngestionError, ParsedDocument, PageContent


class PdfParser:
    def parse(self, path: Path) -> ParsedDocument:
        if not path.is_file():
            raise IngestionError("file_not_found", f"PDF not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise IngestionError("invalid_extension", "Expected a PDF file")
        try:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            document_id = str(uuid5(NAMESPACE_URL, digest))
            with fitz.open(stream=data, filetype="pdf") as pdf:
                pages = tuple(self._parse_page(page, document_id, digest) for page in pdf)
        except IngestionError:
            raise
        except Exception as exc:
            raise IngestionError("pdf_read_error", str(exc)) from exc
        return ParsedDocument(document_id=document_id, filename=path.name, file_hash=digest, pages=pages)

    @staticmethod
    def _parse_page(page: fitz.Page, document_id: str, digest: str) -> PageContent:
        page_number = page.number + 1
        images = []
        for index, image in enumerate(page.get_images(full=True), start=1):
            xref = image[0]
            extracted = page.parent.extract_image(xref)
            image_id = f"p{page_number}-i{index}"
            images.append(ImageInput(
                page_number=page_number,
                image_id=image_id,
                media_type=f"image/{extracted['ext']}",
                data=extracted["image"],
            ))
        return PageContent(document_id=document_id, page_number=page_number, text=page.get_text().strip(), source_hash=digest)

    def parse_inputs(self, path: Path) -> tuple[ParsedDocument, tuple[ImageInput, ...]]:
        document = self.parse(path)
        with fitz.open(path) as pdf:
            images = tuple(image for page in pdf for image in self._images_for_page(page))
        return document, images

    @staticmethod
    def _images_for_page(page: fitz.Page) -> tuple[ImageInput, ...]:
        result = []
        for index, image in enumerate(page.get_images(full=True), start=1):
            extracted = page.parent.extract_image(image[0])
            result.append(ImageInput(page_number=page.number + 1, image_id=f"p{page.number + 1}-i{index}", media_type=f"image/{extracted['ext']}", data=extracted["image"]))
        return tuple(result)
