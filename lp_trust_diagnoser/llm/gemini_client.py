# lp_trust_diagnoser/llm/gemini_client.py
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from google import genai
from google.genai import types

from lp_trust_diagnoser.config import LLMConfig
from lp_trust_diagnoser.exceptions import ConfigurationError, LLMClientError
from lp_trust_diagnoser.llm.prompts import SCAN_AND_COACH_SYSTEM_PROMPT_JA

logger = logging.getLogger(__name__)


class GeminiClient:
    """Thin wrapper around Gemini API for LP trust diagnosis."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._config = config or LLMConfig()

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "Gemini API key is not set. "
                "Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
            )

        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as exc:
            logger.exception("Failed to initialize Gemini client")
            raise ConfigurationError(f"Failed to initialize Gemini client: {exc}") from exc

    def diagnose_lp(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Call Scan & Coach prompt with given LP sections and return raw JSON (dict).

        sections must be a dict with keys: hero, pricing, cancel, reviews, raw.
        """
        payload = {
            "task": "lp_trust_scan_and_coach_v0",
            "sections": sections,
        }

        user_text = (
            "以下は1つのLPから抽出したテキストの要約です。"
            "System指示に従い、6軸で診断し、指定のJSONフォーマットのみを返してください。\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )

        # thinking を切って MAX_TOKENS で思考に全部食われるのを防ぐ
        config = types.GenerateContentConfig(
            system_instruction=SCAN_AND_COACH_SYSTEM_PROMPT_JA,
            temperature=self._config.temperature,
            max_output_tokens=self._config.max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            # response_mime_type は使わず、素の text を JSON としてパースする
        )

        try:
            response = self._client.models.generate_content(
                model=self._config.model_name,
                contents=[user_text],
                config=config,
            )
        except Exception as exc:
            logger.exception("Gemini API call failed")
            raise LLMClientError(f"Gemini API call failed: {exc}") from exc

        # 1. 素直に response.text を試す
        text: str | None
        try:
            text = response.text
        except Exception:
            text = None

        # 2. 空なら candidates から組み立てる
        if not text:
            text = self._extract_text_from_candidates(response)
            if not text:
                logger.error(
                    "Empty text in Gemini response. raw=%r",
                    response,
                )
                raise LLMClientError(
                    "Empty response from Gemini API (possibly safety block or max_tokens)."
                )

        # 3. Markdown の ```json ... ``` や前後の説明を剥がして、素の JSON を取り出す
        cleaned = self._normalize_json_text(text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse Gemini text as JSON. Raw (truncated): %s",
                text[:500],
            )
            logger.error(
                "Cleaned JSON candidate (truncated): %s",
                cleaned[:500],
            )
            raise LLMClientError("Failed to parse Gemini response as JSON") from exc

    @staticmethod
    def _extract_text_from_candidates(response: Any) -> str:
        """
        response.candidates[*].content.parts[*].text からテキストを組み立てる。

        GenerateContentResponse は pydantic モデルなので、
        dict に変換せず属性を辿る。
        """
        texts: List[str] = []

        candidates = getattr(response, "candidates", []) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", []) or []
            for part in parts:
                t = getattr(part, "text", None)
                if t:
                    texts.append(t)

        return "\n".join(texts).strip()

    @staticmethod
    def _normalize_json_text(raw: str) -> str:
        """
        LLM が返した「JSONっぽいテキスト」から、本物の JSON 文字列を取り出す。

        - 先頭/末尾の ``` や ```json を除去
        - それでも余計な文が混ざっている場合は、最初の '{' 〜 最後の '}' を抜き出す
        """
        s = raw.strip()

        # 1) コードフェンス除去（```json ... ```）
        if s.startswith("```"):
            lines = s.splitlines()

            # 先頭の ``` / ```json を落とす
            if len(lines) >= 1 and lines[0].lstrip().startswith("```"):
                lines = lines[1:]

            # 末尾の ``` を落とす
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]

            s = "\n".join(lines).strip()

        # 2) まだ何か前置き/後置きがある場合に備えて、外側の {} だけ切り出す
        if "{" in s and "}" in s:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                s = s[start : end + 1].strip()

        return s
