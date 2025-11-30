# diagnose_lp.py
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv  # ★ 追加

from lp_trust_diagnoser.exceptions import (
    ConfigurationError,
    IngestionError,
    LPDiagnosisError,
    LLMClientError,
)
from lp_trust_diagnoser.ingestion.html_parser import html_to_text_sections
from lp_trust_diagnoser.llm.gemini_client import GeminiClient
from lp_trust_diagnoser.logging_config import configure_logging
from lp_trust_diagnoser.models.diagnosis import LPDiagnosisResult


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose LP trust (3 layers x 6 axes) from LP HTML file."
    )
    parser.add_argument(
        "html_path",
        type=str,
        help="Path to LP HTML file.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON result instead of compact JSON.",
    )
    parser.add_argument(
        "--debug-sections",
        action="store_true",
        help="Print extracted sections (hero/pricing/cancel/reviews/raw) to stderr.",
    )
    return parser.parse_args()


def load_html(path_str: str) -> str:
    path = Path(path_str)
    if not path.is_file():
        raise IngestionError(f"HTML file not found: {path}")
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        raise IngestionError(f"Failed to read HTML file: {exc}") from exc


def main() -> int:
    load_dotenv()  # ★ 追加
    configure_logging()

    args = parse_args()

    try:
        html = load_html(args.html_path)
        sections_obj = html_to_text_sections(html)
        sections_dict = sections_obj.to_dict()

        if args.debug_sections:
            print(
                json.dumps(sections_dict, ensure_ascii=False, indent=2),
                file=sys.stderr,
            )

        client = GeminiClient()
        raw_result: Dict[str, Any] = client.diagnose_lp(sections_dict)

        diagnosis = LPDiagnosisResult.from_dict(raw_result)
        output_dict = diagnosis.to_dict()

        if args.pretty:
            print(json.dumps(output_dict, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(output_dict, ensure_ascii=False, separators=(",", ":")))
        return 0

    except (ConfigurationError, IngestionError, LLMClientError) as exc:
        # Known, user-actionable errors
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except LPDiagnosisError as exc:
        # Fallback for other domain errors
        print(f"UNEXPECTED DOMAIN ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        # Hard fallback
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 99


if __name__ == "__main__":
    raise SystemExit(main())
