from __future__ import annotations

from typing import Any

from .contracts import ParsedDocument


class IngestionRepository:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, document: ParsedDocument) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO documents (document_id, filename, file_hash) VALUES (%s, %s, %s) ON CONFLICT (file_hash) DO NOTHING",
                (document.document_id, document.filename, document.file_hash),
            )
            if cursor.rowcount == 0:
                self._connection.commit()
                return
            for page in document.pages:
                cursor.execute(
                    "INSERT INTO pages (document_id, page_number, text_content, source_hash) VALUES (%s, %s, %s, %s)",
                    (document.document_id, page.page_number, page.text, page.source_hash),
                )
                for image in page.images:
                    cursor.execute(
                        "INSERT INTO image_contents (document_id, page_number, image_id, meaningful, extracted_text, description, confidence, provider, model) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (document.document_id, image.page_number, image.image_id, image.meaningful, image.extracted_text, image.description, image.confidence, image.provider, image.model),
                    )
        self._connection.commit()

    def get_by_hash(self, file_hash: str) -> ParsedDocument | None:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT document_id, filename, file_hash FROM documents WHERE file_hash = %s", (file_hash,))
            row = cursor.fetchone()
            if row is None:
                return None
            document_id, filename, digest = row
            cursor.execute("SELECT page_number, text_content, source_hash FROM pages WHERE document_id = %s ORDER BY page_number", (document_id,))
            page_rows = cursor.fetchall()
            cursor.execute("SELECT page_number, image_id, meaningful, extracted_text, description, confidence, provider, model FROM image_contents WHERE document_id = %s ORDER BY page_number, image_id", (document_id,))
            image_rows = cursor.fetchall()
        images_by_page: dict[int, list[dict[str, Any]]] = {}
        for page_number, image_id, meaningful, text, description, confidence, provider, model in image_rows:
            images_by_page.setdefault(page_number, []).append({
                "image_id": image_id, "page_number": page_number, "meaningful": meaningful,
                "extracted_text": text, "description": description, "confidence": confidence,
                "provider": provider, "model": model,
            })
        pages = tuple({
            "document_id": document_id,
            "page_number": page_number,
            "text": text,
            "images": tuple(images_by_page.get(page_number, ())),
            "source_hash": source_hash,
        } for page_number, text, source_hash in page_rows)
        return ParsedDocument(document_id=document_id, filename=filename, file_hash=digest, pages=pages)
