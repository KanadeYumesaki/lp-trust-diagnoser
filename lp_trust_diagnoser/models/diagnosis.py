# lp_trust_diagnoser/models/diagnosis.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


AxisName = str  # e.g. "trust_transparency"


@dataclass
class AxisDiagnosis:
    score: int
    reason: str
    improvement_hint: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AxisDiagnosis":
        return cls(
            score=int(data.get("score", 0)),
            reason=str(data.get("reason", "")),
            improvement_hint=str(data.get("improvement_hint", "")),
        )


@dataclass
class LPDiagnosisResult:
    axes: Dict[AxisName, AxisDiagnosis]
    summary_comment: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LPDiagnosisResult":
        raw_axes = data.get("axes", {}) or {}
        axes: Dict[AxisName, AxisDiagnosis] = {
            axis_name: AxisDiagnosis.from_dict(axis_dict)
            for axis_name, axis_dict in raw_axes.items()
        }
        summary_comment = str(data.get("summary_comment", ""))
        return cls(axes=axes, summary_comment=summary_comment)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "axes": {
                name: {
                    "score": axis.score,
                    "reason": axis.reason,
                    "improvement_hint": axis.improvement_hint,
                }
                for name, axis in self.axes.items()
            },
            "summary_comment": self.summary_comment,
        }
