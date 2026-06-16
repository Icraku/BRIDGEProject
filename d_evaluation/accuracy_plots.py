"""
d_evaluation/accuracy_plots.py
================================
Visualisation utilities for evaluation outputs.

All plot functions accept an optional *save_path* parameter.  When provided,
the figure is saved to disk instead of (or as well as) being displayed.
This is important for thesis submission where figures must be reproducible
from a script without a display.

Functions
---------
plot_accuracy_by_document(csv_path, save_path, show)
    Bar chart of per-record average accuracy.

plot_accuracy_by_field_type(csv_path, save_path, show)
    Bar chart of mean accuracy grouped by field type.

plot_f1_comparison(metrics_csvs, save_path, show)
    Side-by-side F1 comparison across models.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helper

def _save_or_show(fig: Figure, save_path: str | Path | None, show: bool) -> None:
    """Save *fig* to *save_path* and/or display it, then close cleanly."""
    if save_path:
        dest = Path(save_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(dest), bbox_inches="tight", dpi=150)
        logger.info("Figure saved: %s", dest)
    if show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Public plots

def plot_accuracy_by_document(
    csv_path: str,
    save_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """Plot mean accuracy per record (document) as a line chart.

    Parameters
    ----------
    csv_path: Path to ``field_accuracy_{model}.csv`` produced by ``run_evaluation``.
    save_path: If provided, the figure is saved here (e.g. ``"figures/acc_by_doc.png"``).
    show: Whether to call ``plt.show()`` after plotting.
    """
    df = pd.read_csv(csv_path)
    df["correct?"] = pd.to_numeric(df["correct?"], errors="coerce")

    doc_accuracy = (
        df.groupby("record_id")["correct?"]
        .mean()
        .reset_index()
        .sort_values("correct?")
    )

    fig, ax = plt.subplots(figsize=(max(8, len(doc_accuracy) * 0.4), 5))
    ax.plot(doc_accuracy["record_id"], doc_accuracy["correct?"], marker="o")
    ax.set_xticklabels(doc_accuracy["record_id"], rotation=90, fontsize=8)
    ax.set_ylabel("Mean Accuracy")
    ax.set_xlabel("Record ID")
    ax.set_title("Model Accuracy per Document")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    _save_or_show(fig, save_path, show)


def plot_accuracy_by_field_type(
    csv_path: str,
    save_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """Plot mean accuracy grouped by field type as a horizontal bar chart.

    Parameters
    ----------
    csv_path: Path to ``field_accuracy_{model}.csv``.
    save_path: Optional output path for the figure.
    show: Whether to call ``plt.show()``.
    """
    df = pd.read_csv(csv_path)
    df["correct?"] = pd.to_numeric(df["correct?"], errors="coerce")

    scored = df[df["scorable"] & df["has_gt"]]
    type_acc = (
        scored.groupby("field_type")["correct?"]
        .mean()
        .sort_values()
    )

    fig, ax = plt.subplots(figsize=(7, max(4, len(type_acc) * 0.5)))
    type_acc.plot.barh(ax=ax)
    ax.set_xlabel("Mean Accuracy")
    ax.set_title("Accuracy by Field Type")
    ax.set_xlim(0, 1.05)
    fig.tight_layout()
    _save_or_show(fig, save_path, show)


def plot_f1_comparison(
    metrics_csvs: dict[str, str],
    save_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """Plot side-by-side macro F1 per field type across multiple models.

    Parameters
    ----------
    metrics_csvs: ``{model_label: path_to_metrics_{model}.csv}`` — one entry per model.
    save_path: Optional output path for the figure.
    show: Whether to call ``plt.show()``.

    Example Usage
    -------
    >>> plot_f1_comparison(
    ...     {"qwen": "metrics_qwen.csv", "gemma": "metrics_gemma.csv"},
    ...     save_path="figures/f1_comparison.png",
    ... )
    """
    frames = []
    for label, path in metrics_csvs.items():
        df = pd.read_csv(path)
        df["model"] = label
        frames.append(df)

    if not frames:
        logger.warning("plot_f1_comparison: no CSV files provided.")
        return

    combined = pd.concat(frames, ignore_index=True)
    pivot = combined.pivot_table(values="f1", index="field_type", columns="model")

    fig, ax = plt.subplots(figsize=(9, max(4, len(pivot) * 0.5)))
    pivot.plot.barh(ax=ax)
    ax.set_xlabel("Macro F1")
    ax.set_title("F1 Comparison by Field Type")
    ax.set_xlim(0, 1.05)
    ax.legend(title="Model")
    fig.tight_layout()
    _save_or_show(fig, save_path, show)