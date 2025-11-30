# lp_trust_diagnoser/ingestion/html_parser.py
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict

from bs4 import BeautifulSoup

from lp_trust_diagnoser.exceptions import IngestionError

logger = logging.getLogger(__name__)


PRICE_KEYWORDS = [
    r"¥", r"￥", r"円", r"価格", r"料金", r"月額", r"初月無料", r"割引", r"キャンペーン",
    r"お試し", r"トライアル", r"無料体験",
]

CANCEL_KEYWORDS = [
    r"解約", r"キャンセル", r"退会", r"休会", r"中止", r"返金", r"返金保証",
    r"返品", r"クーリングオフ", r"解約方法", r"解約手続", r"自動更新",
]

REVIEW_KEYWORDS = [
    r"お客様の声", r"ユーザーの声", r"レビュー", r"口コミ", r"評判", r"事例", r"導入事例",
    r"インタビュー", r"体験談", r"実績",
]


@dataclass
class LPSections:
    hero: str
    pricing: str
    cancel: str
    reviews: str
    raw: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "hero": self.hero,
            "pricing": self.pricing,
            "cancel": self.cancel,
            "reviews": self.reviews,
            "raw": self.raw,
        }


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def html_to_text_sections(html: str, max_chars_per_section: int = 1200) -> LPSections:
    """
    Very simple v0 ingestion logic.

    - Parse HTML and extract text.
    - hero: page top (~600 chars).
    - pricing / cancel / reviews: lines containing keywords.
    - raw: full normalized text (truncated).
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as exc:
        logger.exception("Failed to parse HTML with BeautifulSoup")
        raise IngestionError(f"Failed to parse HTML: {exc}") from exc

    raw_text = soup.get_text(separator="\n")
    normalized = _normalize_text(raw_text)

    if not normalized:
        raise IngestionError("Extracted text from HTML is empty.")

    # hero: top 600 chars
    hero = normalized[:600]

    lines = normalized.splitlines()

    def collect_by_keywords(patterns: list[str]) -> str:
        collected: list[str] = []
        combined_pattern = re.compile("|".join(patterns))
        for line in lines:
            if combined_pattern.search(line):
                collected.append(line)
        joined = "\n".join(collected)
        return joined[:max_chars_per_section]

    pricing = collect_by_keywords(PRICE_KEYWORDS)
    cancel = collect_by_keywords(CANCEL_KEYWORDS)
    reviews = collect_by_keywords(REVIEW_KEYWORDS)

    raw_truncated = normalized[: max_chars_per_section * 2]

    logger.debug(
        "Extracted sections lengths -> hero=%d, pricing=%d, cancel=%d, reviews=%d, raw=%d",
        len(hero),
        len(pricing),
        len(cancel),
        len(reviews),
        len(raw_truncated),
    )

    return LPSections(
        hero=hero,
        pricing=pricing,
        cancel=cancel,
        reviews=reviews,
        raw=raw_truncated,
    )
