# Generate Soal

## PDF ingestion MVP

The production path runs in Docker. Build and start it with `docker compose build app` and `docker compose up -d postgres app`.

The default container runs on CPU so the first build does not download the CUDA runtime. Set `EMBEDDING_DEVICE=cuda` only after the CPU path works and the Docker engine exposes the NVIDIA GPU.

Start PostgreSQL locally with `docker compose up -d postgres`. The migration runs on first database initialization.

Docling is the document parser. RapidOCR is the local OCR engine. BGE-M3 (`BAAI/bge-m3`) produces 1024-dimensional embeddings; vectors use normalized inner product (`FAISS IndexFlatIP`).

`IMAGE_ANALYSIS_MODE=ocr` uses local analysis. VLM mode requires an OpenAI-compatible base URL, API key, and model, and sends extracted image bytes externally. Do not enable VLM mode for confidential material unless the provider is approved for that data.

The ingestion pipeline extracts page text and embedded images, then keeps only image analyses marked `meaningful`. It does not execute instructions found in document images.

Run tests with `pytest -q`.
