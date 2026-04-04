# -*- coding: utf-8 -*-
"""
Visualisasi: grafik perbandingan dan dashboard web interaktif.
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


def _setup_style():
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
    df = pd.DataFrame(rows)
    if not df.empty and "scenario" in df.columns:
        df = df.drop_duplicates(subset=["scenario"], keep="last")
    return df


def generate_dashboard_html(
    df: Optional[pd.DataFrame] = None,
    figures_dir: Optional[str] = None,
    open_browser: bool = True,
) -> str:
    """Buat dashboard HTML interaktif dengan pagination, search, dan comparison."""
    if figures_dir is None:
        figures_dir = FIGURES_DIR
    os.makedirs(figures_dir, exist_ok=True)

    # Convert dataframe to JSON for embedding
    data_json = "[]"
    if df is not None and not df.empty:
        records = []
        for _, row in df.iterrows():
            rec = {
                "scenario": row.get("scenario", ""),
                "curve": row.get("curve", ""),
                "scalar_type": row.get("scalar_type", ""),
                "transactions": int(row.get("transactions", 0)),
                "nodes": int(row.get("nodes", 0)),
                "RAM_MB": round(float(row.get("RAM_MB", 0)), 4),
                "CPU_percent": round(float(row.get("CPU_percent", 0)), 2),
                "execution_time_ms": round(float(row.get("execution_time_ms", 0)), 2),
                "entropy": round(float(row.get("entropy", 0)), 6),
                "chi_square": row.get("chi_square", 0),
                "timing": row.get("timing", {}),
                "blockchain": row.get("blockchain", {}),
                "statistical_tests": row.get("statistical_tests", []),
            }
            records.append(rec)
        data_json = json.dumps(records, default=str)

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ECC Blockchain Experiment Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-primary: #0f1117;
    --bg-secondary: #1a1d27;
    --bg-card: #21242f;
    --bg-card-hover: #282c3a;
    --border-color: #2d3142;
    --text-primary: #e8eaed;
    --text-secondary: #9aa0b0;
    --text-muted: #6b7280;
    --accent-blue: #4f8fff;
    --accent-green: #34d399;
    --accent-orange: #fb923c;
    --accent-red: #f87171;
    --accent-purple: #a78bfa;
    --accent-cyan: #22d3ee;
    --gradient-1: linear-gradient(135deg, #4f8fff 0%, #a78bfa 100%);
    --gradient-2: linear-gradient(135deg, #34d399 0%, #22d3ee 100%);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
    --radius: 12px;
    --radius-sm: 8px;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* ===== HEADER ===== */
  .header {{
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    padding: 20px 0;
    position: sticky; top: 0; z-index: 100;
    backdrop-filter: blur(12px);
  }}
  .header-inner {{
    max-width: 1280px; margin: 0 auto; padding: 0 24px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .logo {{
    display: flex; align-items: center; gap: 12px;
  }}
  .logo-icon {{
    width: 36px; height: 36px; background: var(--gradient-1);
    border-radius: 10px; display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 800; color: #fff;
  }}
  .logo-text {{ font-size: 18px; font-weight: 700; }}
  .logo-text span {{ color: var(--accent-blue); }}

  /* ===== NAV TABS ===== */
  .nav-tabs {{
    display: flex; gap: 4px; background: var(--bg-primary);
    padding: 4px; border-radius: 10px;
  }}
  .nav-tab {{
    padding: 8px 20px; border-radius: 8px; border: none;
    background: transparent; color: var(--text-secondary);
    font-family: inherit; font-size: 13px; font-weight: 500;
    cursor: pointer; transition: all 0.2s;
  }}
  .nav-tab:hover {{ color: var(--text-primary); background: var(--bg-card); }}
  .nav-tab.active {{
    background: var(--accent-blue); color: #fff;
  }}

  /* ===== MAIN ===== */
  .container {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}

  .page {{ display: none; }}
  .page.active {{ display: block; }}

  /* ===== SEARCH & FILTERS ===== */
  .toolbar {{
    display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; align-items: center;
  }}
  .search-box {{
    flex: 1; min-width: 200px; position: relative;
  }}
  .search-box input {{
    width: 100%; padding: 10px 16px 10px 40px;
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: var(--radius-sm); color: var(--text-primary);
    font-family: inherit; font-size: 14px; outline: none;
    transition: border-color 0.2s;
  }}
  .search-box input:focus {{ border-color: var(--accent-blue); }}
  .search-box::before {{
    content: "\\1F50D"; position: absolute; left: 14px; top: 50%;
    transform: translateY(-50%); font-size: 14px; opacity: 0.5;
  }}

  .filter-select {{
    padding: 10px 16px; background: var(--bg-card);
    border: 1px solid var(--border-color); border-radius: var(--radius-sm);
    color: var(--text-primary); font-family: inherit; font-size: 13px;
    cursor: pointer; outline: none;
  }}

  .pagination {{
    display: flex; gap: 6px; align-items: center; justify-content: center;
    margin-top: 20px;
  }}
  .pagination button {{
    padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border-color);
    background: var(--bg-card); color: var(--text-secondary);
    font-family: inherit; font-size: 13px; cursor: pointer; transition: all 0.2s;
  }}
  .pagination button:hover {{ background: var(--bg-card-hover); color: var(--text-primary); }}
  .pagination button.active {{ background: var(--accent-blue); color: #fff; border-color: var(--accent-blue); }}
  .pagination button:disabled {{ opacity: 0.3; cursor: not-allowed; }}
  .page-info {{ color: var(--text-muted); font-size: 13px; }}

  /* ===== EXPERIMENT CARDS ===== */
  .exp-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 16px;
  }}
  .exp-card {{
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: var(--radius); padding: 20px; cursor: pointer;
    transition: all 0.25s ease; position: relative; overflow: hidden;
  }}
  .exp-card::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--gradient-1); opacity: 0;
    transition: opacity 0.25s;
  }}
  .exp-card:hover {{
    border-color: var(--accent-blue);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }}
  .exp-card:hover::before {{ opacity: 1; }}
  .exp-card.selected {{
    border-color: var(--accent-green);
    box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.3);
  }}
  .exp-card.selected::before {{
    background: var(--gradient-2); opacity: 1;
  }}

  .exp-card-top {{
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 14px;
  }}
  .exp-id {{
    font-size: 20px; font-weight: 700;
  }}
  .exp-algo {{
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .algo-random {{ background: rgba(79,143,255,0.15); color: var(--accent-blue); }}
  .algo-de {{ background: rgba(251,146,60,0.15); color: var(--accent-orange); }}
  .algo-ga {{ background: rgba(167,139,250,0.15); color: var(--accent-purple); }}
  .algo-ga_de {{ background: rgba(52,211,153,0.15); color: var(--accent-green); }}
  .algo-eg_de {{ background: rgba(34,211,238,0.15); color: var(--accent-cyan); }}

  .exp-meta {{
    display: flex; gap: 16px; margin-bottom: 14px;
    color: var(--text-secondary); font-size: 13px;
  }}
  .exp-meta span {{ display: flex; align-items: center; gap: 4px; }}

  .exp-stats {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }}
  .stat-item {{
    text-align: center; padding: 8px 4px;
    background: var(--bg-secondary); border-radius: 8px;
  }}
  .stat-value {{
    font-size: 15px; font-weight: 700; color: var(--text-primary);
  }}
  .stat-label {{
    font-size: 10px; color: var(--text-muted); text-transform: uppercase;
    letter-spacing: 0.5px; margin-top: 2px;
  }}

  .select-hint {{
    display: flex; align-items: center; gap: 8px; padding: 12px 16px;
    background: rgba(79,143,255,0.08); border: 1px solid rgba(79,143,255,0.2);
    border-radius: var(--radius-sm); margin-bottom: 20px;
    color: var(--accent-blue); font-size: 13px; font-weight: 500;
  }}

  /* ===== COMPARISON PAGE ===== */
  .compare-container {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 24px;
  }}
  .compare-panel {{
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: var(--radius); overflow: hidden;
  }}
  .compare-panel-header {{
    padding: 16px 20px; font-weight: 700; font-size: 16px;
    display: flex; align-items: center; gap: 12px;
  }}
  .compare-panel-header.left {{ background: linear-gradient(135deg, rgba(79,143,255,0.15), transparent); }}
  .compare-panel-header.right {{ background: linear-gradient(135deg, rgba(52,211,153,0.15), transparent); }}
  .compare-panel-body {{ padding: 20px; }}

  .compare-row {{
    display: flex; justify-content: space-between; padding: 10px 0;
    border-bottom: 1px solid var(--border-color);
    font-size: 14px;
  }}
  .compare-row:last-child {{ border-bottom: none; }}
  .compare-label {{ color: var(--text-secondary); }}
  .compare-value {{ font-weight: 600; }}
  .compare-value.better {{ color: var(--accent-green); }}
  .compare-value.worse {{ color: var(--accent-red); }}

  .compare-empty {{
    text-align: center; padding: 60px 20px; color: var(--text-muted);
  }}
  .compare-empty p {{ font-size: 15px; margin-top: 8px; }}

  /* ===== STAT TEST TABLE ===== */
  .test-table {{
    width: 100%; border-collapse: collapse; margin-top: 16px;
  }}
  .test-table th {{
    text-align: left; padding: 8px 12px; font-size: 12px;
    color: var(--text-muted); text-transform: uppercase;
    letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color);
  }}
  .test-table td {{
    padding: 8px 12px; font-size: 13px;
    border-bottom: 1px solid var(--border-color);
  }}
  .badge-pass {{
    display: inline-block; padding: 2px 10px; border-radius: 10px;
    background: rgba(52,211,153,0.15); color: var(--accent-green);
    font-size: 11px; font-weight: 600;
  }}
  .badge-fail {{
    display: inline-block; padding: 2px 10px; border-radius: 10px;
    background: rgba(248,113,113,0.15); color: var(--accent-red);
    font-size: 11px; font-weight: 600;
  }}

  /* ===== DIFF BAR ===== */
  .diff-section {{
    margin-top: 24px; background: var(--bg-card);
    border: 1px solid var(--border-color); border-radius: var(--radius);
    padding: 20px;
  }}
  .diff-section h3 {{
    font-size: 15px; font-weight: 600; margin-bottom: 16px;
    color: var(--text-primary);
  }}
  .diff-bar-row {{
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 12px;
  }}
  .diff-bar-label {{
    width: 120px; font-size: 13px; color: var(--text-secondary); text-align: right;
  }}
  .diff-bar-track {{
    flex: 1; height: 28px; background: var(--bg-secondary);
    border-radius: 6px; overflow: hidden; position: relative;
    display: flex;
  }}
  .diff-bar-a {{
    height: 100%; background: var(--accent-blue);
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600; color: #fff;
    min-width: 40px; transition: width 0.5s ease;
  }}
  .diff-bar-b {{
    height: 100%; background: var(--accent-green);
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600; color: #fff;
    min-width: 40px; transition: width 0.5s ease;
  }}

  /* ===== RESPONSIVE ===== */
  @media (max-width: 768px) {{
    .exp-grid {{ grid-template-columns: 1fr; }}
    .compare-container {{ grid-template-columns: 1fr; }}
    .exp-stats {{ grid-template-columns: repeat(2, 1fr); }}
    .header-inner {{ flex-direction: column; gap: 12px; }}
  }}

  /* ===== ANIMATION ===== */
  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  .exp-card {{ animation: fadeIn 0.3s ease forwards; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div class="logo">
      <div class="logo-icon">E</div>
      <div class="logo-text">ECC <span>Experiment</span> Dashboard</div>
    </div>
    <div class="nav-tabs">
      <button class="nav-tab active" onclick="switchPage('list')">Daftar Percobaan</button>
      <button class="nav-tab" onclick="switchPage('compare')">Perbandingan</button>
    </div>
  </div>
</div>

<div class="container">
  <!-- PAGE: LIST -->
  <div id="page-list" class="page active">
    <div class="select-hint" id="select-hint">
      Klik card untuk memilih percobaan. Pilih 2 percobaan lalu buka tab <b>Perbandingan</b> untuk membandingkan.
      <span id="selected-count" style="margin-left:auto; font-weight:700;">0/2 dipilih</span>
    </div>
    <div class="toolbar">
      <div class="search-box">
        <input type="text" id="search-input" placeholder="Cari skenario, curve, algoritma..." oninput="applyFilters()">
      </div>
      <select class="filter-select" id="filter-algo" onchange="applyFilters()">
        <option value="">Semua Algoritma</option>
        <option value="random">Random</option>
        <option value="de">DE</option>
        <option value="ga">GA</option>
        <option value="ga_de">GA + DE</option>
        <option value="eg_de">EG + DE</option>
      </select>
      <select class="filter-select" id="filter-curve" onchange="applyFilters()">
        <option value="">Semua Curve</option>
        <option value="secp192r1">secp192r1</option>
        <option value="secp224r1">secp224r1</option>
        <option value="secp256r1">secp256r1</option>
      </select>
    </div>
    <div class="exp-grid" id="exp-grid"></div>
    <div class="pagination" id="pagination"></div>
  </div>

  <!-- PAGE: COMPARE -->
  <div id="page-compare" class="page">
    <div id="compare-content"></div>
  </div>
</div>

<script>
const DATA = {data_json};
const ITEMS_PER_PAGE = 6;
let currentPage = 1;
let filteredData = [...DATA];
let selectedItems = [];

const ALGO_LABELS = {{
  'random': 'Random',
  'de': 'Differential Evolution',
  'ga': 'Genetic Algorithm',
  'ga_de': 'GA + DE',
  'eg_de': 'Entropy Guided + DE'
}};

function switchPage(page) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.querySelectorAll('.nav-tab').forEach(t => {{
    if ((page === 'list' && t.textContent.includes('Daftar')) ||
        (page === 'compare' && t.textContent.includes('Perbandingan')))
      t.classList.add('active');
  }});
  if (page === 'compare') renderCompare();
}}

function toggleSelect(scenario) {{
  const idx = selectedItems.indexOf(scenario);
  if (idx >= 0) {{
    selectedItems.splice(idx, 1);
  }} else if (selectedItems.length < 2) {{
    selectedItems.push(scenario);
  }} else {{
    // replace oldest
    selectedItems.shift();
    selectedItems.push(scenario);
  }}
  document.getElementById('selected-count').textContent = selectedItems.length + '/2 dipilih';
  renderGrid();
}}

function applyFilters() {{
  const q = document.getElementById('search-input').value.toLowerCase();
  const algo = document.getElementById('filter-algo').value;
  const curve = document.getElementById('filter-curve').value;

  filteredData = DATA.filter(d => {{
    const matchQ = !q || d.scenario.toLowerCase().includes(q) ||
                   d.curve.toLowerCase().includes(q) ||
                   d.scalar_type.toLowerCase().includes(q) ||
                   (ALGO_LABELS[d.scalar_type] || '').toLowerCase().includes(q);
    const matchAlgo = !algo || d.scalar_type === algo;
    const matchCurve = !curve || d.curve === curve;
    return matchQ && matchAlgo && matchCurve;
  }});
  currentPage = 1;
  renderGrid();
}}

function renderGrid() {{
  const grid = document.getElementById('exp-grid');
  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);
  const start = (currentPage - 1) * ITEMS_PER_PAGE;
  const pageData = filteredData.slice(start, start + ITEMS_PER_PAGE);

  grid.innerHTML = pageData.map((d, i) => {{
    const isSel = selectedItems.includes(d.scenario);
    const algoClass = 'algo-' + d.scalar_type;
    const algoLabel = ALGO_LABELS[d.scalar_type] || d.scalar_type;
    return `
      <div class="exp-card ${{isSel ? 'selected' : ''}}" onclick="toggleSelect('${{d.scenario}}')" style="animation-delay: ${{i*0.05}}s">
        <div class="exp-card-top">
          <div class="exp-id">${{d.scenario}}</div>
          <div class="exp-algo ${{algoClass}}">${{algoLabel}}</div>
        </div>
        <div class="exp-meta">
          <span>${{d.curve}}</span>
          <span>${{d.transactions}} TX</span>
          <span>${{d.nodes}} Node${{d.nodes > 1 ? 's' : ''}}</span>
        </div>
        <div class="exp-stats">
          <div class="stat-item">
            <div class="stat-value">${{d.entropy.toFixed(4)}}</div>
            <div class="stat-label">Entropy</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${{d.RAM_MB.toFixed(2)}}</div>
            <div class="stat-label">RAM (MB)</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${{(d.execution_time_ms/1000).toFixed(1)}}s</div>
            <div class="stat-label">Waktu</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${{d.CPU_percent.toFixed(1)}}%</div>
            <div class="stat-label">CPU</div>
          </div>
        </div>
      </div>`;
  }}).join('');

  // Pagination
  const pag = document.getElementById('pagination');
  if (totalPages <= 1) {{ pag.innerHTML = ''; return; }}
  let html = `<button onclick="goPage(${{currentPage-1}})" ${{currentPage===1?'disabled':''}}>Prev</button>`;
  for (let i = 1; i <= totalPages; i++) {{
    html += `<button class="${{i===currentPage?'active':''}}" onclick="goPage(${{i}})">${{i}}</button>`;
  }}
  html += `<button onclick="goPage(${{currentPage+1}})" ${{currentPage===totalPages?'disabled':''}}>Next</button>`;
  html += `<span class="page-info">${{filteredData.length}} hasil</span>`;
  pag.innerHTML = html;
}}

function goPage(p) {{
  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);
  if (p < 1 || p > totalPages) return;
  currentPage = p;
  renderGrid();
}}

function getDataByScenario(id) {{
  return DATA.find(d => d.scenario === id);
}}

function renderCompare() {{
  const ct = document.getElementById('compare-content');

  if (selectedItems.length < 2) {{
    ct.innerHTML = `
      <div class="compare-empty">
        <div style="font-size:48px; margin-bottom:12px;">&#9878;</div>
        <p>Pilih <b>2 percobaan</b> dari tab Daftar Percobaan untuk membandingkan.</p>
        <p style="color:var(--text-muted); font-size:13px; margin-top:8px;">
          Sudah dipilih: ${{selectedItems.length}}/2
        </p>
      </div>`;
    return;
  }}

  const a = getDataByScenario(selectedItems[0]);
  const b = getDataByScenario(selectedItems[1]);
  if (!a || !b) return;

  const algoA = ALGO_LABELS[a.scalar_type] || a.scalar_type;
  const algoB = ALGO_LABELS[b.scalar_type] || b.scalar_type;

  function cmpRow(label, va, vb, fmt, higherBetter) {{
    let clsA = '', clsB = '';
    const na = parseFloat(va), nb = parseFloat(vb);
    if (!isNaN(na) && !isNaN(nb) && na !== nb) {{
      if (higherBetter) {{
        clsA = na > nb ? 'better' : 'worse';
        clsB = nb > na ? 'better' : 'worse';
      }} else {{
        clsA = na < nb ? 'better' : 'worse';
        clsB = nb < na ? 'better' : 'worse';
      }}
    }}
    const fva = typeof fmt === 'function' ? fmt(va) : va;
    const fvb = typeof fmt === 'function' ? fmt(vb) : vb;
    return `<div class="compare-row">
      <span class="compare-value ${{clsA}}">${{fva}}</span>
      <span class="compare-label">${{label}}</span>
      <span class="compare-value ${{clsB}}">${{fvb}}</span>
    </div>`;
  }}

  const fmtN = (v,d=2) => typeof v === 'number' ? v.toFixed(d) : v;

  // Statistical test comparison
  function renderTests(tests) {{
    if (!tests || !tests.length) return '<p style="color:var(--text-muted)">Tidak ada data</p>';
    return `<table class="test-table">
      <thead><tr><th>Test</th><th>Statistic</th><th>P-Value</th><th>Status</th></tr></thead>
      <tbody>${{tests.map(t => `
        <tr>
          <td>${{t.test_name}}</td>
          <td>${{typeof t.statistic === 'number' ? t.statistic.toFixed(4) : t.statistic}}</td>
          <td>${{t.p_value !== null && t.p_value !== undefined ? parseFloat(t.p_value).toFixed(4) : '-'}}</td>
          <td><span class="${{String(t.passed).toLowerCase()==='true'||t.passed===true ? 'badge-pass':'badge-fail'}}">${{String(t.passed).toLowerCase()==='true'||t.passed===true ? 'PASS':'FAIL'}}</span></td>
        </tr>`).join('')}}</tbody>
    </table>`;
  }}

  // Diff bars
  const metrics = [
    {{ label: 'Entropy', a: a.entropy, b: b.entropy, higher: true }},
    {{ label: 'RAM (MB)', a: a.RAM_MB, b: b.RAM_MB, higher: false }},
    {{ label: 'Waktu (ms)', a: a.execution_time_ms, b: b.execution_time_ms, higher: false }},
    {{ label: 'CPU (%)', a: a.CPU_percent, b: b.CPU_percent, higher: false }},
  ];

  let diffBarsHtml = metrics.map(m => {{
    const total = m.a + m.b || 1;
    const pctA = Math.max(5, (m.a / total) * 100);
    const pctB = Math.max(5, (m.b / total) * 100);
    return `<div class="diff-bar-row">
      <div class="diff-bar-label">${{m.label}}</div>
      <div class="diff-bar-track">
        <div class="diff-bar-a" style="width:${{pctA}}%">${{typeof m.a === 'number' ? m.a.toFixed(2) : m.a}}</div>
        <div class="diff-bar-b" style="width:${{pctB}}%">${{typeof m.b === 'number' ? m.b.toFixed(2) : m.b}}</div>
      </div>
    </div>`;
  }}).join('');

  // Timing breakdown
  const timingKeys = ['scalar_gen_sec','keygen_sec','sign_sec','verify_sec','block_build_sec'];
  const timingLabels = ['Scalar Gen','Key Gen','Signing','Verification','Block Build'];
  let timingBarsHtml = timingKeys.map((k,i) => {{
    const va = (a.timing && a.timing[k]) || 0;
    const vb = (b.timing && b.timing[k]) || 0;
    const total = va + vb || 1;
    const pctA = Math.max(5, (va / total) * 100);
    const pctB = Math.max(5, (vb / total) * 100);
    return `<div class="diff-bar-row">
      <div class="diff-bar-label">${{timingLabels[i]}}</div>
      <div class="diff-bar-track">
        <div class="diff-bar-a" style="width:${{pctA}}%">${{va.toFixed(3)}}s</div>
        <div class="diff-bar-b" style="width:${{pctB}}%">${{vb.toFixed(3)}}s</div>
      </div>
    </div>`;
  }}).join('');

  ct.innerHTML = `
    <div class="compare-container">
      <div class="compare-panel">
        <div class="compare-panel-header left">
          <div class="exp-algo algo-${{a.scalar_type}}" style="font-size:12px">${{algoA}}</div>
          ${{a.scenario}} - ${{a.curve}}
        </div>
        <div class="compare-panel-body">
          <div class="compare-row"><span class="compare-label">Transactions</span><span class="compare-value">${{a.transactions}}</span></div>
          <div class="compare-row"><span class="compare-label">Nodes</span><span class="compare-value">${{a.nodes}}</span></div>
          <div class="compare-row"><span class="compare-label">Entropy</span><span class="compare-value">${{a.entropy.toFixed(6)}}</span></div>
          <div class="compare-row"><span class="compare-label">RAM</span><span class="compare-value">${{a.RAM_MB.toFixed(2)}} MB</span></div>
          <div class="compare-row"><span class="compare-label">CPU</span><span class="compare-value">${{a.CPU_percent.toFixed(1)}}%</span></div>
          <div class="compare-row"><span class="compare-label">Waktu</span><span class="compare-value">${{a.execution_time_ms.toFixed(1)}} ms</span></div>
          <div class="compare-row"><span class="compare-label">Blocks</span><span class="compare-value">${{a.blockchain ? a.blockchain.total_blocks : '-'}}</span></div>
          <h4 style="margin-top:16px; font-size:13px; color:var(--text-muted);">Statistical Tests</h4>
          ${{renderTests(a.statistical_tests)}}
        </div>
      </div>
      <div class="compare-panel">
        <div class="compare-panel-header right">
          <div class="exp-algo algo-${{b.scalar_type}}" style="font-size:12px">${{algoB}}</div>
          ${{b.scenario}} - ${{b.curve}}
        </div>
        <div class="compare-panel-body">
          <div class="compare-row"><span class="compare-label">Transactions</span><span class="compare-value">${{b.transactions}}</span></div>
          <div class="compare-row"><span class="compare-label">Nodes</span><span class="compare-value">${{b.nodes}}</span></div>
          <div class="compare-row"><span class="compare-label">Entropy</span><span class="compare-value">${{b.entropy.toFixed(6)}}</span></div>
          <div class="compare-row"><span class="compare-label">RAM</span><span class="compare-value">${{b.RAM_MB.toFixed(2)}} MB</span></div>
          <div class="compare-row"><span class="compare-label">CPU</span><span class="compare-value">${{b.CPU_percent.toFixed(1)}}%</span></div>
          <div class="compare-row"><span class="compare-label">Waktu</span><span class="compare-value">${{b.execution_time_ms.toFixed(1)}} ms</span></div>
          <div class="compare-row"><span class="compare-label">Blocks</span><span class="compare-value">${{b.blockchain ? b.blockchain.total_blocks : '-'}}</span></div>
          <h4 style="margin-top:16px; font-size:13px; color:var(--text-muted);">Statistical Tests</h4>
          ${{renderTests(b.statistical_tests)}}
        </div>
      </div>
    </div>

    <div class="diff-section">
      <h3>Perbandingan Metrik Utama
        <span style="font-size:12px; font-weight:400; color:var(--text-muted); margin-left:12px;">
          <span style="color:var(--accent-blue);">&#9632;</span> ${{a.scenario}} (${{algoA}})
          &nbsp;&nbsp;
          <span style="color:var(--accent-green);">&#9632;</span> ${{b.scenario}} (${{algoB}})
        </span>
      </h3>
      ${{diffBarsHtml}}
    </div>

    <div class="diff-section">
      <h3>Timing Breakdown
        <span style="font-size:12px; font-weight:400; color:var(--text-muted); margin-left:12px;">
          <span style="color:var(--accent-blue);">&#9632;</span> ${{a.scenario}}
          &nbsp;&nbsp;
          <span style="color:var(--accent-green);">&#9632;</span> ${{b.scenario}}
        </span>
      </h3>
      ${{timingBarsHtml}}
    </div>
  `;
}}

// Init
applyFilters();
</script>
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
    """Generate dashboard HTML."""
    df = load_log(results_dir, log_file)
    if df.empty:
        print("Tidak ada data log. Jalankan experiment_runner dulu.")
        return {}

    _ensure_fig_dir()
    paths = {}

    dash = generate_dashboard_html(
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
