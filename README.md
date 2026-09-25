# Generate Soal

## PDF ingestion MVP

Dependency installation uses the project extras: `pip install -e .[test]`.

Start PostgreSQL locally with `docker compose up -d postgres`. The migration runs on first database initialization.

`IMAGE_ANALYSIS_MODE=ocr` uses the local analyzer. VLM mode requires an OpenAI-compatible base URL, API key, and model, and sends extracted image bytes to that provider. Do not enable VLM mode for confidential material unless the provider is approved for that data.

The ingestion pipeline extracts page text and embedded images, then keeps only image analyses marked `meaningful`. It does not execute instructions found in document images.

Run tests with `pytest -q`.
