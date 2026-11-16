"""
FeatureStatistics — per-feature descriptive statistics, constant-feature
detection, Pearson correlation report, and dataset quality report.

Outputs
-------
feature_statistics.json  — per-feature stats + missing/constant flags
feature_correlation.json — highly correlated feature pairs (|r| >= 0.95)
dataset_quality.json     — overall dataset health summary
"""
from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from app.ml.feature_registry import FEATURE_NAMES
from app.ml.feature_vector import FeatureVector

# Thresholds
_NEARLY_CONSTANT_CV_THRESHOLD = 0.01   # coefficient of variation < 1 %
_HIGH_CORRELATION_THRESHOLD   = 0.95   # |Pearson r| >= this → reported
_HIGH_MISSING_THRESHOLD       = 0.20   # > 20 % missing → flagged in quality


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class FeatureStat:
    name: str
    group: str = ""
    valid_count: int = 0
    missing_count: int = 0
    missing_pct: float = 0.0
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    is_constant: bool = False
    is_nearly_constant: bool = False
    constant_value: float | None = None   # set when is_constant is True


@dataclass
class CorrelationPair:
    feature_a: str
    feature_b: str
    pearson_r: float


@dataclass
class DatasetStatistics:
    total_rows: int = 0
    label_distribution: dict[str, int] = field(default_factory=dict)
    feature_stats: list[FeatureStat] = field(default_factory=list)
    # Pairs with |r| >= _HIGH_CORRELATION_THRESHOLD
    high_correlation_pairs: list[CorrelationPair] = field(default_factory=list)
    # Names of features flagged as constant or nearly constant
    constant_features: list[str] = field(default_factory=list)
    nearly_constant_features: list[str] = field(default_factory=list)
    # Names of features with > 20 % missing values
    high_missing_features: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Rows : {self.total_rows}",
            f"Labels: {self.label_distribution}",
            f"Constant features ({len(self.constant_features)}): {self.constant_features}",
            f"Nearly-constant features ({len(self.nearly_constant_features)}): {self.nearly_constant_features}",
            f"High-missing features (>{_HIGH_MISSING_THRESHOLD:.0%}): {self.high_missing_features}",
            f"Highly correlated pairs (|r|>={_HIGH_CORRELATION_THRESHOLD}): "
            f"{len(self.high_correlation_pairs)}",
            "",
            f"{'Feature':<42} {'Valid':>6} {'Miss%':>6} {'Mean':>10} {'Std':>10} "
            f"{'Min':>10} {'Max':>10} {'Const':>6}",
            "-" * 110,
        ]
        for s in self.feature_stats:
            mean_s = f"{s.mean:.4f}"   if s.mean   is not None else "—"
            std_s  = f"{s.std:.4f}"    if s.std    is not None else "—"
            min_s  = f"{s.min:.4f}"    if s.min    is not None else "—"
            max_s  = f"{s.max:.4f}"    if s.max    is not None else "—"
            flag   = "C" if s.is_constant else ("~C" if s.is_nearly_constant else "")
            lines.append(
                f"{s.name:<42} {s.valid_count:>6} {s.missing_pct:>5.1f}% "
                f"{mean_s:>10} {std_s:>10} {min_s:>10} {max_s:>10} {flag:>6}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class FeatureStatistics:

    def compute(self, vectors: Sequence[FeatureVector]) -> DatasetStatistics:
        ds = DatasetStatistics(total_rows=len(vectors))

        # Label distribution
        for v in vectors:
            key = v.label or ""
            ds.label_distribution[key] = ds.label_distribution.get(key, 0) + 1

        # Build per-feature value lists (finite only)
        value_lists: dict[str, list[float]] = {}
        for name in FEATURE_NAMES:
            vals = [
                v.features[name]
                for v in vectors
                if name in v.features
                and v.features[name] is not None
                and math.isfinite(v.features[name])
            ]
            value_lists[name] = vals

        # Per-feature stats + constant detection
        for name in FEATURE_NAMES:
            vals = value_lists[name]
            n_total   = len(vectors)
            n_valid   = len(vals)
            n_missing = n_total - n_valid
            miss_pct  = (n_missing / n_total * 100.0) if n_total > 0 else 0.0

            stat = FeatureStat(name=name, valid_count=n_valid,
                               missing_count=n_missing, missing_pct=miss_pct)

            if vals:
                stat.mean   = statistics.mean(vals)
                stat.min    = min(vals)
                stat.max    = max(vals)
                stat.median = statistics.median(vals)
                stat.std    = statistics.pstdev(vals) if len(vals) > 1 else 0.0

                # Constant: all values identical
                if stat.min == stat.max:
                    stat.is_constant    = True
                    stat.constant_value = stat.min
                    ds.constant_features.append(name)
                elif stat.mean != 0 and stat.std is not None:
                    cv = abs(stat.std / stat.mean)
                    if cv < _NEARLY_CONSTANT_CV_THRESHOLD:
                        stat.is_nearly_constant = True
                        ds.nearly_constant_features.append(name)

            if miss_pct > _HIGH_MISSING_THRESHOLD * 100:
                ds.high_missing_features.append(name)

            ds.feature_stats.append(stat)

        # Pearson correlation (only features with >= 2 valid values)
        ds.high_correlation_pairs = self._compute_correlations(value_lists, len(vectors))

        return ds

    # ------------------------------------------------------------------
    # JSON export helpers
    # ------------------------------------------------------------------

    def export_statistics(self, ds: DatasetStatistics, path: Path) -> None:
        """Write feature_statistics.json."""
        payload = {
            "total_rows": ds.total_rows,
            "label_distribution": ds.label_distribution,
            "constant_features": ds.constant_features,
            "nearly_constant_features": ds.nearly_constant_features,
            "high_missing_features": ds.high_missing_features,
            "features": [
                {
                    "name":              s.name,
                    "valid_count":       s.valid_count,
                    "missing_count":     s.missing_count,
                    "missing_pct":       round(s.missing_pct, 2),
                    "mean":              _r(s.mean),
                    "median":            _r(s.median),
                    "std":               _r(s.std),
                    "min":               _r(s.min),
                    "max":               _r(s.max),
                    "is_constant":       s.is_constant,
                    "is_nearly_constant":s.is_nearly_constant,
                    "constant_value":    _r(s.constant_value),
                }
                for s in ds.feature_stats
            ],
        }
        _write_json(path, payload)

    def export_correlation(self, ds: DatasetStatistics, path: Path) -> None:
        """Write feature_correlation.json."""
        payload = {
            "threshold": _HIGH_CORRELATION_THRESHOLD,
            "pair_count": len(ds.high_correlation_pairs),
            "pairs": [
                {
                    "feature_a": p.feature_a,
                    "feature_b": p.feature_b,
                    "pearson_r": round(p.pearson_r, 6),
                }
                for p in ds.high_correlation_pairs
            ],
        }
        _write_json(path, payload)

    def export_quality(
        self,
        ds: DatasetStatistics,
        vectors: Sequence[FeatureVector],
        path: Path,
    ) -> None:
        """Write dataset_quality.json."""
        n = len(vectors)

        # Duplicate rows: compare full feature dicts
        row_signatures = [
            tuple(v.features.get(name) for name in FEATURE_NAMES)
            for v in vectors
        ]
        duplicate_rows = n - len(set(row_signatures))

        # Duplicate document IDs
        doc_ids = [v.document_id for v in vectors]
        duplicate_doc_ids = n - len(set(doc_ids))

        # Rows with any NaN
        nan_rows = sum(
            1 for v in vectors
            if any(
                val is not None and isinstance(val, float) and math.isnan(val)
                for val in v.features.values()
            )
        )

        # Rows with any Inf
        inf_rows = sum(
            1 for v in vectors
            if any(
                val is not None and isinstance(val, float) and math.isinf(val)
                for val in v.features.values()
            )
        )

        label_dist = ds.label_distribution
        authentic  = label_dist.get("authentic", 0)
        forged     = label_dist.get("forged", 0)
        balance    = round(authentic / forged, 4) if forged > 0 else None

        payload = {
            "total_samples":          n,
            "authentic_samples":      authentic,
            "forged_samples":         forged,
            "class_balance_ratio":    balance,
            "duplicate_rows":         duplicate_rows,
            "duplicate_document_ids": duplicate_doc_ids,
            "rows_with_nan":          nan_rows,
            "rows_with_inf":          inf_rows,
            "features_high_missing":  ds.high_missing_features,
            "constant_features":      ds.constant_features,
            "nearly_constant_features": ds.nearly_constant_features,
            "high_correlation_pairs": [
                {"feature_a": p.feature_a, "feature_b": p.feature_b,
                 "pearson_r": round(p.pearson_r, 6)}
                for p in ds.high_correlation_pairs
            ],
        }
        _write_json(path, payload)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_correlations(
        value_lists: dict[str, list[float]],
        n_total: int,
    ) -> list[CorrelationPair]:
        names = [n for n in FEATURE_NAMES if len(value_lists[n]) >= 2]
        pairs: list[CorrelationPair] = []

        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                na, nb = names[i], names[j]
                r = _pearson(value_lists[na], value_lists[nb])
                if r is not None and abs(r) >= _HIGH_CORRELATION_THRESHOLD:
                    pairs.append(CorrelationPair(na, nb, r))

        return pairs


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson r computed only over indices where both lists have a value.
    Returns None if fewer than 2 paired observations or zero variance."""
    paired = [(x, y) for x, y in zip(xs, ys)]
    n = len(paired)
    if n < 2:
        return None
    mx = sum(x for x, _ in paired) / n
    my = sum(y for _, y in paired) / n
    num = sum((x - mx) * (y - my) for x, y in paired)
    dx  = math.sqrt(sum((x - mx) ** 2 for x, _ in paired))
    dy  = math.sqrt(sum((y - my) ** 2 for _, y in paired))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def _r(v: float | None) -> float | None:
    """Round to 6 dp for JSON serialisation, or return None."""
    return round(v, 6) if v is not None else None


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
