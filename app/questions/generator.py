from __future__ import annotations

import hashlib
import re
from typing import Any


class GroundedQuestionGenerator:
    def generate(self, sources: list[dict[str, Any]], count: int = 3, question_type: str = "essay") -> list[dict[str, Any]]:
        valid = [source for source in sources if str(source.get("text", "")).strip() and source.get("chunk_id")]
        if not valid:
            raise ValueError("sources must contain non-empty text and chunk_id")
        questions: list[dict[str, Any]] = []
        seen: set[str] = set()
        for source in valid:
            text = re.sub(r"\s+", " ", str(source["text"])).strip()
            subject = text[:160].rstrip(" .,:;")
            question = f"Apa inti informasi yang dijelaskan dalam sumber: {subject}?"
            key = hashlib.sha256(question.casefold().encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            item: dict[str, Any] = {
                "type": "essay",
                "question": question,
                "answer": text,
                "explanation": "Jawaban diringkas langsung dari teks sumber yang dirujuk.",
                "difficulty": "medium",
                "references": [{"chunk_id": source["chunk_id"], "document_id": source.get("document_id"), "page_number": source.get("page_number")}],
            }
            if question_type == "multiple_choice":
                item["type"] = "multiple_choice"
                item["options"] = [text, "Informasi tidak tersedia dalam sumber", "Kesimpulan yang bertentangan dengan sumber", "Pernyataan tanpa dukungan sumber"]
                item["correct_option"] = 0
            questions.append(item)
            if len(questions) >= max(1, min(count, 50)):
                break
        return questions
