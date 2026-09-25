from __future__ import annotations

import argparse
from pathlib import Path

from app.config.settings import Settings
from app.ingestion.pipeline import ingest_pdf
from app.ingestion.providers import create_local_ocr_analyzer, create_vlm_analyzer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--mode", choices=("ocr", "vlm"), default=Settings().image_analysis_mode)
    args = parser.parse_args()
    settings = Settings()
    analyzer = create_local_ocr_analyzer() if args.mode == "ocr" else create_vlm_analyzer(settings.vlm_base_url, settings.vlm_api_key, settings.vlm_model)
    document = ingest_pdf(args.pdf, analyzer)
    print(document.model_dump_json(indent=2))


if __name__ == "__main__":
    main()