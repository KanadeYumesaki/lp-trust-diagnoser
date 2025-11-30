# lp_trust_diagnoser/exceptions.py
from __future__ import annotations


class LPDiagnosisError(Exception):
    """Base exception for LP trust diagnoser."""


class ConfigurationError(LPDiagnosisError):
    """Raised when required configuration is missing or invalid."""


class IngestionError(LPDiagnosisError):
    """Raised when HTML ingestion or section extraction fails."""


class LLMClientError(LPDiagnosisError):
    """Raised when an error occurs while calling the LLM API."""
