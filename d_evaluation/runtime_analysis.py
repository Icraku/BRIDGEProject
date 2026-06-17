"""
d_evaluation/runtime_analysis.py
========================================
Aggregates runtime metrics from structured database records
produced by run_structuring_pipeline.py.

This module analyzes per-record execution timing for LLM
inference and full pipeline execution.

Input fields (Surreal database)
-------------------------------
- llm_runtime_seconds
    Time spent on LLM inference only.

- total_record_runtime_seconds
    End-to-end runtime per record (fetch + inference + save).

Outputs
-------
- runtime_summary_{model}.csv
    Per-record runtime metrics with aggregated statistics.

- runtime_by_model.csv
    Cross-model comparison of runtime distributions.
"""

from __future__ import annotations

import logging
import pandas as pd
import numpy as np
from database_utils.db_utils import fetch_records

logger = logging.getLogger(__name__)

# ------------------------
# LOAD TIMING FROM DB

def load_runtimes(table_name: str) -> pd.DataFrame:
    """
    Load llm_runtime_seconds and total_record_runtime_seconds
    from a structured output table.
    """
    records = fetch_records(table_name)
    rows = []
    for r in records:
        raw_id = r.get("id")
        if not raw_id:
            continue
        record_id = str(raw_id).split(":")[-1]
        rows.append({
            "record_id":     record_id,
            "llm_runtime_s": r.get("llm_runtime_seconds"),
            "total_runtime_s": r.get("total_record_runtime_seconds"),
            "run_id":        r.get("run_id", ""),
        })
    return pd.DataFrame(rows)

# ------------------------
# STATS HELPER

def _stats(series: pd.Series, label: str) -> dict:
    s = series.dropna()
    if s.empty:
        return {f"{label}_mean": None, f"{label}_median": None,
                f"{label}_std": None, f"{label}_min": None, f"{label}_max": None,
                f"{label}_p25": None, f"{label}_p75": None}
    return {
        f"{label}_mean":   round(s.mean(),   2),
        f"{label}_median": round(s.median(), 2),
        f"{label}_std":    round(s.std(),    2),
        f"{label}_min":    round(s.min(),    2),
        f"{label}_max":    round(s.max(),    2),
        f"{label}_p25":    round(s.quantile(0.25), 2),
        f"{label}_p75":    round(s.quantile(0.75), 2),
    }

# ------------------------
# ENTRY POINT

def run_runtime_analysis(
    model_configs: list[dict],
) -> pd.DataFrame:
    """
    Args:
        model_configs: list of dicts, each with keys:
            model_label   — e.g. "qwen", "gemma", "medgemma"
            table_name    — DB table holding structured outputs
            stage         — "extraction" | "structuring" (default: "structuring")

    Example:
        run_runtime_analysis([
            {"model_label": "qwen",     "table_name": "structured_Q"},
            {"model_label": "gemma",    "table_name": "structured_gemma"},
            {"model_label": "medgemma", "table_name": "structured_medgemma"},
        ])

    Returns a combined DataFrame with per-record timings for all models.
    Saves runtime_summary_{model}.csv per model, and runtime_by_model.csv
    for the cross-model comparison.
    """
    logger.info("\n" + "=" * 60)
    logger.info(f"  RUNTIME ANALYSIS — {[c['model_label'] for c in model_configs]}")
    logger.info("=" * 60)

    all_stats  = []
    all_frames = []

    for cfg in model_configs:
        label = cfg["model_label"]
        table = cfg["table_name"]

        df = load_runtimes(table)
        if df.empty:
            logger.warning(f"[{label}] No records found in '{table}', skipping.")
            continue

        df["model"] = label
        n = len(df)

        llm_stats   = _stats(df["llm_runtime_s"],   "llm_s")
        total_stats = _stats(df["total_runtime_s"], "total_s")

        row = {"model": label, "n_records": n, **llm_stats, **total_stats}
        all_stats.append(row)
        all_frames.append(df)

        # per-record CSV
        outf = f"runtime_summary_{label}.csv"
        df.to_csv(outf, index=False)

        logger.info(f"\n[{label}] n={n}  table={table}")
        logger.info(
            f"    LLM inference : mean={llm_stats['llm_s_mean']}s  "
            f"median={llm_stats['llm_s_median']}s  "
            f"max={llm_stats['llm_s_max']}s"
        )
        logger.info(
            f"    Total pipeline: mean={total_stats['total_s_mean']}s  "
            f"median={total_stats['total_s_median']}s  "
            f"max={total_stats['total_s_max']}s"
        )
        logger.info(f"    Saved: {outf}")

    if not all_stats:
        logger.warning("No runtime data found.")
        return pd.DataFrame()

    # Cross-model comparison
    comparison = pd.DataFrame(all_stats)
    comparison.to_csv("runtime_by_model.csv", index=False)

    logger.info("\nCross-model comparison:")
    cols = [
        "model", "n_records",
        "llm_s_mean", "llm_s_median", "llm_s_std",
        "total_s_mean", "total_s_median", "total_s_std"
    ]
    logger.info(
        "\n" + comparison[[c for c in cols if c in comparison.columns]]
        .to_string(index=False)
    )
    logger.info("Saved: runtime_by_model.csv")

    combined = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
    return combined