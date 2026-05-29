"""Generate performance comparison charts from benchmark_results.json.

Reads scripts/benchmark_results.json (produced by scripts/benchmark.py)
and writes PNGs to docs/assets/:

  - docs/assets/perf_time.png      — log-scale wall-clock time per workload
  - docs/assets/perf_speedup.png   — DocxMint speedup factor over python-docx
  - docs/assets/perf_size.png      — installed package size comparison

See notebooks/benchmark.ipynb for the full interactive benchmark.

Usage:
    python scripts/generate_charts.py
"""

from __future__ import annotations

import importlib.util
import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")

DOCXMINT_COLOR = "#581aa8"
DOCX_COLOR = "#1aa897"
DOCXMINT_SCATTER = "#9361d4"
DOCX_SCATTER = "#75cbc1"
GRID_STYLE = {"linestyle": "--", "alpha": 0.4}


def load_results() -> tuple[list[int], list[float], list[float]]:
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    sizes = sorted(int(k) for k in data["python_docx"])
    docx_times = [data["python_docx"][str(s)] * 1000 for s in sizes]  # seconds -> ms
    fast_times = [data["docxmint"][str(s)] * 1000 for s in sizes]
    return sizes, docx_times, fast_times


def _dir_size_mb(path: str) -> float:
    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, files in os.walk(path)
        for f in files
    )
    return total / 1024 / 1024


def _package_root(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec and spec.origin:
        return os.path.dirname(spec.origin)
    raise ImportError(name)


def plot_time(sizes: list[int], docx_times: list[float], fast_times: list[float]) -> None:
    labels = [f"{s:,}" for s in sizes]
    x = np.arange(len(sizes))
    bar_w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.bar(x - bar_w / 2, fast_times, bar_w, label="DocxMint", color=DOCXMINT_COLOR, zorder=3)
    ax.bar(x + bar_w / 2, docx_times, bar_w, label="python-docx", color=DOCX_COLOR, zorder=3)

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.4g} ms"))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Number of paragraphs")
    ax.set_ylabel("Time (ms, log scale)")
    ax.set_title("Build + save time: DocxMint vs python-docx")
    ax.legend(framealpha=0)
    ax.grid(axis="y", **GRID_STYLE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "perf_time.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Wrote {out}")


def plot_speedup(sizes: list[int], docx_times: list[float], fast_times: list[float]) -> None:
    speedups = [d / f for d, f in zip(docx_times, fast_times)]
    labels = [f"{s:,}" for s in sizes]
    x = np.arange(len(sizes))

    colors = ["#2ecc71" if s >= 10 else "#f39c12" if s >= 3 else "#e74c3c" for s in speedups]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.bar(x, speedups, color=colors, width=0.5, zorder=3)
    for bar, s in zip(bars, speedups):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(speedups) * 0.01,
            f"{s:.1f}×",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#333333",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Number of paragraphs")
    ax.set_ylabel("Speedup (× faster than python-docx)")
    ax.set_title("DocxMint speedup over python-docx")
    ax.axhline(1, color="black", linewidth=0.8, linestyle="--")
    ax.grid(axis="y", **GRID_STYLE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "perf_speedup.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Wrote {out}")


def plot_size() -> None:
    docxmint_mb = _dir_size_mb(_package_root("docxmint"))
    pydocx_mb = _dir_size_mb(_package_root("docx"))

    print(f"  docxmint   : {docxmint_mb:.2f} MB")
    print(f"  python-docx: {pydocx_mb:.2f} MB")

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.bar(
        ["DocxMint", "python-docx"],
        [docxmint_mb, pydocx_mb],
        color=[DOCXMINT_COLOR, DOCX_COLOR],
        width=0.45,
        zorder=3,
    )
    for bar, size in zip(bars, [docxmint_mb, pydocx_mb]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(docxmint_mb, pydocx_mb) * 0.01,
            f"{size:.2f} MB",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#333333",
        )

    ax.set_ylabel("Installed size (MB)")
    ax.set_title("Installed package size")
    ax.grid(axis="y", **GRID_STYLE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "perf_size.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Wrote {out}")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    sizes, docx_times, fast_times = load_results()
    plot_time(sizes, docx_times, fast_times)
    plot_speedup(sizes, docx_times, fast_times)
    plot_size()


if __name__ == "__main__":
    main()
