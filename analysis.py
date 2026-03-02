# -*- coding: utf-8 -*-
"""
Analisis: identifikasi parameter ECC/DE mana yang paling mempengaruhi RAM.
Menggunakan korelasi dan variansi untuk ranking pengaruh parameter.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import numpy as np
    import pandas as pd
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        f"{e}. Pasang dependensi: pip install -r requirements.txt"
    ) from e

RESULTS_DIR = "results"
LOG_FILE = "experiment_log.jsonl"
SWEEP_FILE = "parameter_sweep.jsonl"


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


def load_sweep_log(results_dir: str = RESULTS_DIR, log_file: str = SWEEP_FILE) -> pd.DataFrame:
    """Load parameter sweep log."""
    return load_log(results_dir, log_file)


def parameter_sensitivity_ram(
    df: pd.DataFrame,
    target: str = "peak_memory_mb",
    param_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Hitung sensitivitas parameter terhadap RAM (target).
    Metrik: korelasi Pearson, range (max-min) per parameter, dan
    rata-rata target per nilai parameter.
    Returns DataFrame ranking parameter by impact on RAM.
    """
    if df.empty or target not in df.columns:
        return pd.DataFrame()

    # Hanya parameter DE yang dihitung (sesuai fokus penelitian)
    if param_columns is None:
        param_columns = [
            "de_population",
            "de_generations",
            "de_F",
            "de_CR",
        ]
    param_columns = [c for c in param_columns if c in df.columns]

    numeric = df.select_dtypes(include=[np.number])
    if target not in numeric.columns:
        return pd.DataFrame()

    impacts = []
    for col in param_columns:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty or len(series) < 2:
            continue
        target_series = df.loc[series.index, target]
        target_series = pd.to_numeric(target_series, errors="coerce").dropna()
        common = series.index.intersection(target_series.index)
        if len(common) < 2:
            continue
        s = series.loc[common]
        t = target_series.loc[common]
        corr = s.corr(t) if s.std() > 0 and t.std() > 0 else 0
        # Range RAM ketika parameter ini divariasikan
        grp = df.groupby(col)[target].agg(["mean", "min", "max", "std"])
        grp["range"] = grp["max"] - grp["min"]
        range_impact = grp["range"].max() if not grp.empty else 0
        impacts.append({
            "parameter": col,
            "correlation_with_RAM": round(corr, 4),
            "RAM_range_when_varied": round(range_impact, 4),
            "mean_RAM_by_param": grp["mean"].mean(),
        })

    if not impacts:
        return pd.DataFrame()
    out = pd.DataFrame(impacts)
    # Rank by absolute correlation dan range
    out["impact_score"] = (
        out["correlation_with_RAM"].abs() * 0.5
        + out["RAM_range_when_varied"] / (out["RAM_range_when_varied"].max() or 1) * 0.5
    )
    out = out.sort_values("impact_score", ascending=False).reset_index(drop=True)
    return out


def compare_random_vs_de(df: pd.DataFrame) -> Dict[str, Any]:
    """Perbandingan statistik Random vs DE (memory, CPU, time)."""
    if df.empty or "scalar_type" not in df.columns:
        return {}
    g = df.groupby("scalar_type").agg({
        "peak_memory_mb": ["mean", "std", "min", "max"],
        "time_sec": ["mean", "std"],
        "cpu_percent": ["mean"],
    }).round(4)
    return g.to_dict() if not g.empty else {}


def summarize_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan per skenario (S1–S6)."""
    if df.empty:
        return pd.DataFrame()
    id_col = "scenario_id"
    if id_col not in df.columns:
        return df[[c for c in ["peak_memory_mb", "time_sec", "curve", "scalar_type"] if c in df.columns]]
    return df.groupby(id_col).agg({
        "peak_memory_mb": "max",
        "time_sec": "sum",
        "memory_after_mb": "max",
        "curve": "first",
        "scalar_type": "first",
        "ops": "first",
        "threads": "first",
    }).round(4)


def run_analysis(
    results_dir: str = RESULTS_DIR,
    scenario_log: str = LOG_FILE,
    sweep_log: str = SWEEP_FILE,
) -> Dict[str, Any]:
    """
    Jalankan seluruh analisis: load logs, sensitivity, comparison, summary.
    Return dict berisi:
      - sensitivity_ranking: parameter mana paling mempengaruhi RAM
      - random_vs_de: perbandingan Random vs DE
      - scenario_summary: ringkasan S1–S6
    """
    df_scenario = load_log(results_dir, scenario_log)
    df_sweep = load_sweep_log(results_dir, sweep_log)

    # Gabung untuk analisis sensitivitas jika sweep ada
    df = df_sweep if not df_sweep.empty else df_scenario
    if df.empty:
        return {
            "message": "Tidak ada data log. Jalankan experiment_runner dulu.",
            "sensitivity_ranking": [],
            "random_vs_de": {},
            "scenario_summary": [],
        }

    # Hanya data DE (buang baris random)
    if "scalar_type" in df.columns:
        df = df[df["scalar_type"] == "de"].copy()

    # Hanya parameter DE yang dipakai untuk ranking pengaruh RAM
    de_params_only = ["de_population", "de_generations", "de_F", "de_CR"]
    sensitivity = parameter_sensitivity_ram(
        df, target="peak_memory_mb", param_columns=de_params_only
    )
    ranking = sensitivity.to_dict("records") if not sensitivity.empty else []

    comparison = compare_random_vs_de(df)
    df_scenario_de = df_scenario[df_scenario["scalar_type"] == "de"] if "scalar_type" in df_scenario.columns and not df_scenario.empty else df_scenario
    summary = summarize_scenarios(df_scenario_de)
    summary_rec = summary.to_dict("records") if not summary.empty else []

    return {
        "sensitivity_ranking": ranking,
        "parameter_most_affects_RAM": ranking[0]["parameter"] if ranking else None,
        "random_vs_de": comparison,
        "scenario_summary": summary_rec,
    }


if __name__ == "__main__":
    r = run_analysis()
    print("Parameter paling mempengaruhi RAM:", r.get("parameter_most_affects_RAM"))
    print("Sensitivity ranking:")
    for row in r.get("sensitivity_ranking", [])[:10]:
        print(" ", row)
    print("Random vs DE:", r.get("random_vs_de"))
