# -*- coding: utf-8 -*-
"""
Visualisasi: grafik perbandingan Random vs DE scalar pada blockchain.
Gaya profesional akademik — warna netral, clean layout.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

RESULTS_DIR = "results"
FIGURES_DIR = "results/figures"
LOG_FILE = "experiment_log.jsonl"

# --- Professional color palette (muted, grayscale-friendly) ---
CLR_RANDOM = "#5B7BA5"   # steel blue
CLR_DE = "#2C2C2C"       # dark charcoal
HATCHES = ["", "///"]    # plain vs hatched for print-friendly distinction


def _setup_style():
    """Apply clean academic style to matplotlib."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#444",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })


def _ensure_fig_dir():
    os.makedirs(FIGURES_DIR, exist_ok=True)


def load_log(results_dir: str = RESULTS_DIR, log_file: str = LOG_FILE) -> pd.DataFrame:
    """Load log JSONL ke DataFrame."""
    path = os.path.join(results_dir, log_file)
    if not os.path.isfile(path):
        return pd.DataFrame()
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(rows)


def plot_entropy_comparison(df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
    """Bar chart: entropy Random vs DE per curve."""
    if df.empty or "entropy" not in df.columns:
        return None
    _ensure_fig_dir()
    _setup_style()

    fig, ax = plt.subplots(figsize=(8, 5))

    curves = df["curve"].unique()
    x = np.arange(len(curves))
    width = 0.32

    random_entropy = []
    de_entropy = []
    for c in curves:
        r = df[(df["curve"] == c) & (df["scalar_type"] == "random")]
        d = df[(df["curve"] == c) & (df["scalar_type"] == "de")]
        random_entropy.append(r["entropy"].mean() if not r.empty else 0)
        de_entropy.append(d["entropy"].mean() if not d.empty else 0)

    bars1 = ax.bar(x - width/2, random_entropy, width, label="Random",
                   color=CLR_RANDOM, edgecolor="#333", linewidth=0.5)
    bars2 = ax.bar(x + width/2, de_entropy, width, label="DE Optimized",
                   color=CLR_DE, edgecolor="#333", linewidth=0.5)

    ax.set_xlabel("ECC Curve")
    ax.set_ylabel("Shannon Entropy")
    ax.set_title("Shannon Entropy: Random vs DE Scalar", fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(curves)
    ax.legend(frameon=True, fancybox=False, edgecolor="#ccc", fontsize=10)
    ax.set_ylim(0.99, 1.002)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.0003,
                f'{bar.get_height():.4f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.0003,
                f'{bar.get_height():.4f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    path = save_path or os.path.join(FIGURES_DIR, "entropy_comparison.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_resource_comparison(df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
    """Grouped bar chart: RAM, CPU, Time per scenario."""
    if df.empty:
        return None
    _ensure_fig_dir()
    _setup_style()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    scenarios = df["scenario"].tolist()
    colors = [CLR_RANDOM if s["scalar_type"] == "random" else CLR_DE
              for _, s in df.iterrows()]

    metrics = [
        ("RAM_MB", "RAM Usage (MB)", "MB"),
        ("CPU_percent", "CPU Usage (%)", "%"),
        ("execution_time_ms", "Execution Time (ms)", "ms"),
    ]
    for ax, (col, title, ylabel) in zip(axes, metrics):
        ax.bar(scenarios, df[col], color=colors, edgecolor="#333", linewidth=0.5)
        ax.set_title(title, fontweight="bold", fontsize=11)
        ax.set_xlabel("Scenario")
        ax.set_ylabel(ylabel)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=CLR_RANDOM, edgecolor="#333", label="Random"),
        Patch(facecolor=CLR_DE, edgecolor="#333", label="DE Optimized"),
    ]
    fig.legend(handles=legend_elements, loc="upper center", ncol=2,
               fontsize=10, frameon=True, fancybox=False, edgecolor="#ccc")

    plt.suptitle("Resource Usage per Scenario", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = save_path or os.path.join(FIGURES_DIR, "resource_comparison.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_statistical_tests(df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
    """Table-style heatmap: pass/fail dari 5 statistical tests per scenario."""
    if df.empty or "statistical_tests" not in df.columns:
        return None
    _ensure_fig_dir()
    _setup_style()

    scenarios = df["scenario"].tolist()
    test_names = []
    matrix = []

    for _, row in df.iterrows():
        tests = row.get("statistical_tests", [])
        results = []
        for t in tests:
            if t["test_name"] not in test_names:
                test_names.append(t["test_name"])
            results.append(1 if t.get("passed", False) else 0)
        matrix.append(results)

    test_names = list(dict.fromkeys(test_names))
    for i in range(len(matrix)):
        while len(matrix[i]) < len(test_names):
            matrix[i].append(0)

    matrix = np.array(matrix)

    fig, ax = plt.subplots(figsize=(9, 5))
    # Professional two-tone: light gray (fail) / medium gray-green (pass)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(["#D4D4D4", "#8FB39A"])
    ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(test_names)))
    ax.set_xticklabels(test_names, rotation=25, ha="right", fontsize=10)
    ax.set_yticks(range(len(scenarios)))
    ax.set_yticklabels(scenarios, fontsize=10)

    for i in range(len(scenarios)):
        for j in range(len(test_names)):
            text = "PASS" if matrix[i, j] == 1 else "FAIL"
            ax.text(j, i, text, ha="center", va="center", fontsize=9,
                    color="#1a1a1a", fontweight="bold" if matrix[i, j] == 1 else "normal")

    ax.set_title("Statistical Randomness Tests", fontweight="bold", pad=12)
    ax.tick_params(top=False, bottom=True, left=True, right=False)
    plt.tight_layout()
    path = save_path or os.path.join(FIGURES_DIR, "statistical_tests.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_timing_breakdown(df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
    """Stacked bar chart: timing breakdown per scenario."""
    if df.empty or "timing" not in df.columns:
        return None
    _ensure_fig_dir()
    _setup_style()

    scenarios = df["scenario"].tolist()
    timing_keys = ["scalar_gen_sec", "keygen_sec", "sign_sec", "verify_sec", "block_build_sec"]
    timing_labels = ["Scalar Gen", "Key Gen", "Signing", "Verification", "Block Build"]
    # Professional grayscale palette
    colors_list = ["#3C3C3C", "#6B6B6B", "#999999", "#BBBBBB", "#DDDDDD"]

    fig, ax = plt.subplots(figsize=(10, 5))

    bottom = np.zeros(len(scenarios))
    for key, label, color in zip(timing_keys, timing_labels, colors_list):
        values = []
        for _, row in df.iterrows():
            timing = row.get("timing", {})
            values.append(timing.get(key, 0))
        ax.bar(scenarios, values, bottom=bottom, label=label,
               color=color, edgecolor="#333", linewidth=0.5)
        bottom += np.array(values)

    ax.set_xlabel("Scenario")
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Timing Breakdown per Scenario", fontweight="bold", pad=12)
    ax.legend(loc="upper left", frameon=True, fancybox=False,
              edgecolor="#ccc", fontsize=9)

    plt.tight_layout()
    path = save_path or os.path.join(FIGURES_DIR, "timing_breakdown.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ============================================================================
# Dashboard HTML — professional academic style
# ============================================================================

def generate_dashboard_html(
    paths: Dict[str, str],
    df: Optional[pd.DataFrame] = None,
    figures_dir: Optional[str] = None,
    open_browser: bool = True,
) -> str:
    """Buat dashboard HTML profesional dengan keterangan interpretasi."""
    if figures_dir is None:
        figures_dir = FIGURES_DIR
    os.makedirs(figures_dir, exist_ok=True)

    descriptions = {
        "entropy_comparison": {
            "interpretation": "Lebih Tinggi = Lebih Baik",
            "badge_class": "badge-up",
            "detail": (
                "Shannon Entropy mengukur kualitas randomness dari representasi bit scalar. "
                "Nilai maksimum = 1.0 (distribusi bit 0 dan 1 seimbang sempurna). "
                "Scalar DE diharapkan memiliki entropy lebih tinggi, "
                "menandakan distribusi bit lebih merata."
            ),
        },
        "resource_comparison": {
            "interpretation": "Lebih Rendah = Lebih Efisien",
            "badge_class": "badge-down",
            "detail": (
                "<b>RAM (MB)</b> — puncak penggunaan memori. "
                "<b>CPU (%)</b> — beban prosesor. "
                "<b>Execution Time (ms)</b> — total waktu eksekusi "
                "(scalar generation + key generation + signing + verification + block building)."
            ),
        },
        "statistical_tests": {
            "interpretation": "PASS = Scalar Random Berkualitas",
            "badge_class": "badge-up",
            "detail": (
                "1. <b>Shannon Entropy</b> — Entropy &ge; 0.95 = PASS<br>"
                "2. <b>Frequency (Monobit)</b> — p-value &ge; 0.01 = PASS<br>"
                "3. <b>Chi-Square</b> — p-value &ge; 0.01 = PASS<br>"
                "4. <b>Runs Test</b> — p-value &ge; 0.01 = PASS<br>"
                "5. <b>Autocorrelation</b> — p-value &ge; 0.01 = PASS"
            ),
        },
        "timing_breakdown": {
            "interpretation": "Lebih Rendah = Lebih Cepat",
            "badge_class": "badge-down",
            "detail": (
                "<b>Scalar Gen</b> — DE lebih lama karena proses optimasi. "
                "<b>Key Gen / Signing / Verification</b> — seharusnya setara antara Random dan DE. "
                "<b>Block Build</b> — pembuatan blok blockchain termasuk Merkle tree."
            ),
        },
    }

    chart_titles = {
        "entropy_comparison": "Shannon Entropy: Random vs DE",
        "resource_comparison": "Resource Usage (RAM, CPU, Time)",
        "statistical_tests": "Pengujian Statistik Randomness",
        "timing_breakdown": "Timing Breakdown",
    }

    # Build summary table
    summary_html = ""
    if df is not None and not df.empty:
        rows_html = ""
        for _, row in df.iterrows():
            row_cls = "row-de" if row.get("scalar_type") == "de" else "row-random"
            rows_html += (
                f"<tr class='{row_cls}'>"
                f"<td>{row.get('scenario','')}</td>"
                f"<td>{row.get('curve','')}</td>"
                f"<td>{row.get('scalar_type','').upper()}</td>"
                f"<td>{row.get('transactions','')}</td>"
                f"<td>{row.get('nodes','')}</td>"
                f"<td>{row.get('RAM_MB',0):.2f}</td>"
                f"<td>{row.get('CPU_percent',0):.1f}</td>"
                f"<td>{row.get('execution_time_ms',0):.1f}</td>"
                f"<td><b>{row.get('entropy',0):.6f}</b></td>"
                f"</tr>\n"
            )
        summary_html = f"""
    <div class="card">
      <div class="card-header">Ringkasan Hasil Eksperimen</div>
      <div class="card-body">
        <table>
          <thead>
            <tr>
              <th>Skenario</th><th>Curve</th><th>Scalar</th><th>TX</th><th>Nodes</th>
              <th>RAM (MB) <span class="arrow-down">&darr;</span></th>
              <th>CPU (%) <span class="arrow-down">&darr;</span></th>
              <th>Waktu (ms) <span class="arrow-down">&darr;</span></th>
              <th>Entropy <span class="arrow-up">&uarr;</span></th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        <p class="legend">
          <span class="swatch swatch-random"></span> Random &nbsp;&nbsp;
          <span class="swatch swatch-de"></span> DE Optimized &nbsp;&nbsp;|&nbsp;&nbsp;
          &uarr; lebih tinggi lebih baik &nbsp;&nbsp; &darr; lebih rendah lebih baik
        </p>
      </div>
    </div>"""

    # Build chart cards
    charts_html = ""
    for name, path_val in paths.items():
        if not path_val or name == "dashboard":
            continue
        rel = os.path.relpath(path_val, figures_dir).replace("\\", "/")
        desc = descriptions.get(name, {})
        title = chart_titles.get(name, name)
        badge = desc.get("interpretation", "")
        badge_cls = desc.get("badge_class", "badge-up")
        detail = desc.get("detail", "")
        charts_html += f"""
    <div class="card">
      <div class="card-header">{title}</div>
      <img src="{rel}" alt="{title}">
      <div class="card-body">
        <span class="badge {badge_cls}">{badge}</span>
        <p class="description">{detail}</p>
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>ECC-DE Blockchain Experiment</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    background: #f0f2f5; color: #333; line-height: 1.65;
  }}
  .container {{ max-width: 980px; margin: 0 auto; padding: 36px 24px; }}

  h1 {{ font-size: 24px; font-weight: 700; color: #1a1a1a; text-align: center; margin-bottom: 6px; }}
  .subtitle {{ text-align: center; color: #777; font-size: 13.5px; margin-bottom: 32px; }}

  .card {{
    background: #fff; border-radius: 10px; margin-bottom: 26px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden;
    border: 1px solid #e8e8e8;
  }}
  .card-header {{
    background: #3d4f5f; color: #fff; padding: 12px 20px;
    font-size: 15px; font-weight: 600; letter-spacing: 0.2px;
  }}
  .card-body {{ padding: 16px 20px; }}
  .card img {{ width: 100%; display: block; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{
    background: #4a5d6e; color: #fff; padding: 9px 10px;
    text-align: center; font-weight: 600; font-size: 12.5px;
  }}
  td {{ padding: 8px 10px; text-align: center; border-bottom: 1px solid #f0f0f0; }}
  .row-random {{ background: #fafafa; }}
  .row-de {{ background: #f4f7fa; }}
  tbody tr:hover td {{ background: #eef2f7; }}

  .arrow-up {{ color: #3a8a5c; font-weight: bold; }}
  .arrow-down {{ color: #4a6fa5; font-weight: bold; }}

  .badge {{
    display: inline-block; padding: 5px 14px; border-radius: 14px;
    font-size: 12px; font-weight: 600; margin-bottom: 8px;
  }}
  .badge-up {{ background: #eaf5ee; color: #2d7a47; }}
  .badge-down {{ background: #eaf1fa; color: #2c5ea0; }}

  .description {{ font-size: 13.5px; color: #666; margin-top: 4px; line-height: 1.75; }}
  .description b {{ color: #444; }}

  .legend {{ font-size: 12px; color: #888; margin-top: 12px; }}
  .swatch {{
    display: inline-block; width: 12px; height: 12px;
    border-radius: 3px; vertical-align: middle; margin-right: 4px;
  }}
  .swatch-random {{ background: #5B7BA5; }}
  .swatch-de {{ background: #2C2C2C; }}

  .footer {{
    text-align: center; color: #aaa; font-size: 12px;
    margin-top: 36px; padding-top: 18px; border-top: 1px solid #e0e0e0;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>ECC-DE Blockchain Experiment</h1>
  <p class="subtitle">Perbandingan Scalar Random vs Differential Evolution pada Blockchain Simulator</p>
{summary_html}
{charts_html}
  <div class="footer">
    ECC-DE Blockchain Simulator &mdash; Kurva: secp192r1 (P-192), secp224r1 (P-224), secp256r1 (P-256)
  </div>
</div>
</body>
</html>"""

    html_path = os.path.join(figures_dir, "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(html_path)}")

    return html_path


def generate_all(
    results_dir: str = RESULTS_DIR,
    log_file: str = LOG_FILE,
    open_browser: bool = True,
) -> Dict[str, str]:
    """Generate semua grafik dan dashboard HTML."""
    df = load_log(results_dir, log_file)
    if df.empty:
        print("Tidak ada data log. Jalankan experiment_runner dulu.")
        return {}

    _ensure_fig_dir()
    paths = {}

    paths["entropy_comparison"] = plot_entropy_comparison(df)
    paths["resource_comparison"] = plot_resource_comparison(df)
    paths["statistical_tests"] = plot_statistical_tests(df)
    paths["timing_breakdown"] = plot_timing_breakdown(df)

    # Remove None entries
    paths = {k: v for k, v in paths.items() if v is not None}

    if paths:
        dash = generate_dashboard_html(
            paths,
            df=df,
            figures_dir=FIGURES_DIR,
            open_browser=open_browser,
        )
        paths["dashboard"] = dash

    return paths


if __name__ == "__main__":
    paths = generate_all(open_browser=True)
    for name, path in paths.items():
        print(f"Saved: {path}")
