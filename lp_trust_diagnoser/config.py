# lp_trust_diagnoser/config.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    model_name: str = "gemini-2.5-flash"   # PoC用。必要に応じて変更
    temperature: float = 0.3
    max_output_tokens: int = 1024
