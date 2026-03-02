# -*- coding: utf-8 -*-
"""
Visualisasi: grafik RAM vs Iterations, Curve Size, Threads, dan Random vs DE.
Generate matplotlib code/figures untuk penelitian.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analysis import load_log, load_sweep_log

RESULTS_DIR = "results"
FIGURES_DIR = "results/figures"
LOG_FILE = "experiment_log.jsonl"
SWEEP_FILE = "parameter_sweep.jsonl"


def _ensure_fig_dir():
    Path(FIGURES_DIR).mkdir(parents=True, exist_ok=True)


def plot_ram_vs_iterations(
    df: pd.DataFrame,
    curve_name: str = "secp256r1",
    save_path: Optional[str] = None,
) -> str:
    """RAM (peak_memory_mb) vs jumlah operasi (ops)."""
    _ensure_fig_dir()
    if df.empty or "ops" not in df.columns or "peak_memory_mb" not in df.columns:
        return ""
    # Filter by curve if column exists
    if "curve" in df.columns:
        df = df[df["curve"] == curve_name]
    if df.empty:
        return ""
    if "scalar_type" in df.columns:
        for st in df["scalar_type"].unique():
            sub = df[df["scalar_type"] == st].sort_values("ops")
            if sub.empty:
                continue
            label = "DE" if st == "de" else f"Scalar: {st}"
            plt.plot(sub["ops"], sub["peak_memory_mb"], "o-", label=label, markersize=6)
    else:
        sub = df.sort_values("ops")
        plt.plot(sub["ops"], sub["peak_memory_mb"], "o-", label="RAM", markersize=6)
    plt.xlabel("Jumlah operasi (iterations)")
    plt.ylabel("RAM (peak, MB)")
    plt.title(f"RAM vs Iterations (curve: {curve_name})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = save_path or os.path.join(FIGURES_DIR, "ram_vs_iterations.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


def plot_ram_vs_curve_size(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
) -> str:
    """RAM vs ukuran curve (curve_bits)."""
    _ensure_fig_dir()
    if df.empty or "curve_bits" not in df.columns or "peak_memory_mb" not in df.columns:
        return ""
    types = df["scalar_type"].unique() if "scalar_type" in df.columns else [None]
    for st in types:
        sub = df[df["scalar_type"] == st] if st is not None else df
        if sub.empty:
            continue
        grp = sub.groupby("curve_bits")["peak_memory_mb"].mean()
        label = "DE" if st == "de" else (f"Scalar: {st}" if st else "RAM")
        plt.plot(grp.index, grp.values, "o-", label=label, markersize=8)
    plt.xlabel("Curve size (bits)")
    plt.ylabel("RAM (peak, MB)")
    plt.title("RAM vs Curve Size")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = save_path or os.path.join(FIGURES_DIR, "ram_vs_curve_size.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


def plot_ram_vs_threads(
    df: pd.DataFrame,
    curve_name: str = "secp256r1",
    save_path: Optional[str] = None,
) -> str:
    """RAM vs jumlah threads."""
    _ensure_fig_dir()
    if df.empty or "threads" not in df.columns or "peak_memory_mb" not in df.columns:
        return ""
    if "curve" in df.columns:
        df = df[df["curve"] == curve_name]
    types = df["scalar_type"].unique() if "scalar_type" in df.columns else [None]
    for st in types:
        sub = df[df["scalar_type"] == st] if st is not None else df
        if sub.empty:
            continue
        grp = sub.groupby("threads")["peak_memory_mb"].mean()
        label = "DE" if st == "de" else (f"Scalar: {st}" if st else "RAM")
        plt.plot(grp.index, grp.values, "o-", label=label, markersize=8)
    plt.xlabel("Threads")
    plt.ylabel("RAM (peak, MB)")
    plt.title(f"RAM vs Threads (curve: {curve_name})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = save_path or os.path.join(FIGURES_DIR, "ram_vs_threads.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


def plot_de_summary(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
) -> str:
    """Ringkasan DE: memory, time, CPU (rata-rata)."""
    _ensure_fig_dir()
    if df.empty:
        return ""
    metrics = ["peak_memory_mb", "time_sec", "cpu_percent"]
    metrics = [m for m in metrics if m in df.columns]
    if not metrics:
        return ""
    # Hanya DE: gunakan mean seluruh data
    grp = df[metrics].mean()
    x = np.arange(len(metrics))
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(x, grp.values, color="steelblue", alpha=0.8)
    ax.set_ylabel("Nilai rata-rata")
    ax.set_title("DE: Ringkasan Memory, Time, CPU")
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace("_", " ") for m in metrics])
    plt.tight_layout()
    path = save_path or os.path.join(FIGURES_DIR, "de_summary.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


def plot_sensitivity_ranking(
    sensitivity_records: List[Dict[str, Any]],
    save_path: Optional[str] = None,
) -> str:
    """Bar chart: ranking parameter by impact on RAM."""
    _ensure_fig_dir()
    if not sensitivity_records:
        return ""
    params = [r["parameter"] for r in sensitivity_records]
    scores = [r.get("impact_score", r.get("RAM_range_when_varied", 0)) for r in sensitivity_records]
    plt.figure(figsize=(8, 4))
    plt.barh(range(len(params)), scores, color="steelblue", alpha=0.8)
    plt.yticks(range(len(params)), params)
    plt.xlabel("Impact score (pengaruh terhadap RAM)")
    plt.title("Parameter DE yang Paling Mempengaruhi RAM")
    plt.tight_layout()
    path = save_path or os.path.join(FIGURES_DIR, "sensitivity_ranking.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


# Label grafik untuk tampilan dashboard (Bahasa Indonesia)
FIGURE_LABELS = {
    "ram_vs_iterations": "RAM vs Jumlah Operasi (Iterations)",
    "ram_vs_curve_size": "RAM vs Ukuran Curve (bits)",
    "ram_vs_threads": "RAM vs Jumlah Threads",
    "de_summary": "DE: Ringkasan Memory, Time, CPU",
    "sensitivity_ranking": "Parameter DE yang Paling Mempengaruhi RAM",
}


def generate_dashboard_html(
    paths: Dict[str, str],
    analysis_result: Optional[Dict[str, Any]] = None,
    figures_dir: Optional[str] = None,
    open_browser: bool = True,
) -> str:
    """
    Buat dashboard HTML yang menampilkan semua grafik hasil eksperimen.
    Jika open_browser=True, buka file HTML di browser default.
    """
    _ensure_fig_dir()
    figures_dir = figures_dir or FIGURES_DIR
    dashboard_path = os.path.join(figures_dir, "dashboard.html")

    # Hanya nama file (bukan path penuh) agar relatif ke dashboard.html
    def rel(name: str) -> str:
        p = paths.get(name)
        return os.path.basename(p) if p else ""

    rows = []
    for key, label in FIGURE_LABELS.items():
        if key not in paths:
            continue
        fname = rel(key)
        rows.append(
            f'<div class="card">'
            f'<h3>{label}</h3>'
            f'<img src="{fname}" alt="{label}" />'
            f"</div>"
        )

    summary = ""
    if analysis_result:
        param = analysis_result.get("parameter_most_affects_RAM")
        ranking = analysis_result.get("sensitivity_ranking", [])
        if param or ranking:
            summary = "<section class='summary'><h2>Ringkasan Analisis</h2><ul>"
            if param:
                summary += f"<li><strong>Parameter paling mempengaruhi RAM:</strong> {param}</li>"
            for r in ranking[:5]:
                summary += f"<li>{r.get('parameter')}: korelasi={r.get('correlation_with_RAM')}, range RAM={r.get('RAM_range_when_varied')}</li>"
            summary += "</ul></section>"

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hasil Eksperimen ECC + DE - Grafik</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 20px; background: #f5f5f5; }}
    h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 8px; }}
    .summary {{ background: #fff; padding: 16px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .summary ul {{ margin: 8px 0 0 20px; }}
    .cards {{ display: flex; flex-wrap: wrap; gap: 24px; }}
    .card {{ background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 100%; }}
    .card h3 {{ margin: 0 0 12px 0; color: #16213e; font-size: 1.1em; }}
    .card img {{ max-width: 100%; height: auto; display: block; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Hasil Eksperimen ECC + DE — Grafik</h1>
  {summary}
  <div class="cards">
    {chr(10).join(rows)}
  </div>
</body>
</html>"""

    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html)

    if open_browser:
        try:
            import webbrowser
            webbrowser.open("file:///" + os.path.abspath(dashboard_path).replace("\\", "/"))
        except Exception:
            pass

    return dashboard_path


def generate_all(
    results_dir: str = RESULTS_DIR,
    scenario_log: str = LOG_FILE,
    sweep_log: str = SWEEP_FILE,
    open_browser: bool = True,
) -> Dict[str, str]:
    """
    Generate semua grafik dan dashboard HTML.
    Jika open_browser=True, buka dashboard di browser setelah selesai.
    Return dict nama figure -> path file.
    """
    from analysis import run_analysis
    df_scenario = load_log(results_dir, scenario_log)
    df_sweep = load_sweep_log(results_dir, sweep_log)
    df = df_sweep if not df_sweep.empty else df_scenario
    # Hanya DE: buang baris random agar grafik web hanya menampilkan DE
    if not df.empty and "scalar_type" in df.columns:
        df = df[df["scalar_type"] == "de"].copy()
    paths = {}
    if not df.empty:
        p1 = plot_ram_vs_iterations(df)
        if p1:
            paths["ram_vs_iterations"] = p1
        p2 = plot_ram_vs_curve_size(df)
        if p2:
            paths["ram_vs_curve_size"] = p2
        p3 = plot_ram_vs_threads(df)
        if p3:
            paths["ram_vs_threads"] = p3
        p4 = plot_de_summary(df)
        if p4:
            paths["de_summary"] = p4
    res = run_analysis(results_dir, scenario_log, sweep_log)
    ranking = res.get("sensitivity_ranking", [])
    if ranking:
        p5 = plot_sensitivity_ranking(ranking)
        if p5:
            paths["sensitivity_ranking"] = p5

    if paths:
        dashboard_path = generate_dashboard_html(
            paths, analysis_result=res, figures_dir=os.path.join(results_dir, "figures"), open_browser=open_browser
        )
        paths["dashboard"] = dashboard_path

    return paths


if __name__ == "__main__":
    paths = generate_all(open_browser=True)
    for name, path in paths.items():
        print(f"Saved: {path}")
