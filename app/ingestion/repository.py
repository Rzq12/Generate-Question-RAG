from __future__ import annotations

from typing import Any

from .contracts import ParsedDocument
from .chunker import Chunk


class IngestionRepository:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, document: ParsedDocument, chunks: tuple[Chunk, ...] = ()) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO documents (document_id, filename, file_hash, status) VALUES (%s, %s, %s, 'processing') ON CONFLICT (file_hash) DO NOTHING",
                (document.document_id, document.filename, document.file_hash),
            )
            if cursor.rowcount == 0:
                self._connection.commit()
                return False
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
            for chunk in chunks:
                cursor.execute(
                    "INSERT INTO chunks (chunk_id, document_id, page_number, text_content, source_hash) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (chunk.chunk_id, chunk.document_id, chunk.page_number, chunk.text, chunk.source_hash),
                )
        self._connection.commit()
        return True

    def set_status(self, document_id: str, status: str, error_message: str | None = None) -> None:
        if status not in {"processing", "completed", "failed"}:
            raise ValueError("invalid document status")
        with self._connection.cursor() as cursor:
            cursor.execute("UPDATE documents SET status = %s, error_message = %s WHERE document_id = %s", (status, error_message, document_id))
        self._connection.commit()

    def search_chunks(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        if not chunk_ids:
            return []
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT chunk_id, document_id, page_number, text_content FROM chunks WHERE chunk_id = ANY(%s)", (chunk_ids,))
            rows = cursor.fetchall()
        return [{"chunk_id": row[0], "document_id": row[1], "page_number": row[2], "text": row[3]} for row in rows]

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
