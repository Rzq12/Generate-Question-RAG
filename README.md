# Generate Soal

## PDF ingestion MVP

The production path runs in Docker. Build and start it with `docker compose build app` and `docker compose up -d postgres app`.

The container requests one NVIDIA GPU. Docker Desktop must have GPU support enabled and the NVIDIA Container Toolkit must be available to the Docker engine. RTX 3050 4 GB may require CPU offload or smaller batch sizes for BGE-M3.

Start PostgreSQL locally with `docker compose up -d postgres`. The migration runs on first database initialization.

Docling is the document parser. RapidOCR is the local OCR engine. BGE-M3 (`BAAI/bge-m3`) produces 1024-dimensional embeddings; vectors use normalized inner product (`FAISS IndexFlatIP`).

`IMAGE_ANALYSIS_MODE=ocr` uses local analysis. VLM mode requires an OpenAI-compatible base URL, API key, and model, and sends extracted image bytes externally. Do not enable VLM mode for confidential material unless the provider is approved for that data.

The ingestion pipeline extracts page text and embedded images, then keeps only image analyses marked `meaningful`. It does not execute instructions found in document images.

Run tests with `pytest -q`.
