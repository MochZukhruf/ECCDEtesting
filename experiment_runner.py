# -*- coding: utf-8 -*-
"""
Experiment Runner: menjalankan skenario ECC (S1–S6) dan parameter sweep
untuk mengidentifikasi parameter mana yang paling mempengaruhi RAM.
"""

import os
import json
import multiprocessing
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import SCENARIOS, CURVES, DE_DEFAULT, BATCH_SIZES, THREAD_COUNTS, DE_PARAMS
from ecc_engine import run_batch_scalar_multiplication, get_curve_bit_size
from scalar_generator import get_scalars
from resource_monitor import run_and_measure, format_metrics, measure_block

RESULTS_DIR = "results"
LOG_FILE = "experiment_log.jsonl"


def _run_one_scenario(
    scenario_id: str,
    curve_name: str,
    scalar_type: str,
    ops: int,
    threads: int,
    de_population: int = 100,
    de_generations: int = 30,
    de_F: float = 0.8,
    de_CR: float = 0.7,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Jalankan satu skenario: generate scalars, jalankan batch ECC, ukur resource.
    """
    # Generate scalars (random atau DE) — ini bisa memakan RAM untuk DE
    def do_work():
        scalars = get_scalars(
            curve_name,
            count=ops,
            scalar_type=scalar_type,
            de_population=de_population,
            de_generations=de_generations,
            de_F=de_F,
            de_CR=de_CR,
            seed=seed,
        )
        results = run_batch_scalar_multiplication(
            curve_name,
            scalars,
            use_parallel=(threads > 1),
            num_workers=threads,
        )
        return results  # simpan agar tidak di-GC sebelum ukur

    metrics = run_and_measure(do_work, use_tracemalloc=True)
    out = {
        "scenario_id": scenario_id,
        "curve": curve_name,
        "curve_bits": get_curve_bit_size(curve_name),
        "scalar_type": scalar_type,
        "ops": ops,
        "threads": threads,
        "de_population": de_population,
        "de_generations": de_generations,
        "de_F": de_F,
        "de_CR": de_CR,
        **format_metrics(metrics),
    }
    out["throughput_ops_per_sec"] = round(ops / out["time_sec"], 2) if out["time_sec"] > 0 else 0
    return out


def run_scenarios(
    scenarios: Optional[List[Dict]] = None,
    results_dir: str = RESULTS_DIR,
    log_file: str = LOG_FILE,
    de_overrides: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Jalankan daftar skenario (default: SCENARIOS dari config) dan tulis log.
    """
    scenarios = scenarios or SCENARIOS
    de = {**DE_DEFAULT, **(de_overrides or {})}
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(results_dir, log_file)
    all_results: List[Dict[str, Any]] = []

    for s in scenarios:
        sid = s.get("id", "unknown")
        print(f"Running {sid} ... curve={s['curve']} type={s['scalar_type']} ops={s['ops']} threads={s['threads']}")
        try:
            res = _run_one_scenario(
                scenario_id=sid,
                curve_name=s["curve"],
                scalar_type=s["scalar_type"],
                ops=s["ops"],
                threads=s["threads"],
                de_population=de.get("population_size", DE_DEFAULT["population_size"]),
                de_generations=de.get("generations", DE_DEFAULT["generations"]),
                de_F=de.get("F", DE_DEFAULT["F"]),
                de_CR=de.get("CR", DE_DEFAULT["CR"]),
            )
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error {sid}: {e}")
            all_results.append({
                "scenario_id": sid,
                "error": str(e),
                "curve": s.get("curve"),
                "scalar_type": s.get("scalar_type"),
                "ops": s.get("ops"),
                "threads": s.get("threads"),
            })

    return all_results


def run_parameter_sweep(
    curve_name: str = "secp256r1",
    ops_list: Optional[List[int]] = None,
    threads_list: Optional[List[int]] = None,
    de_population_list: Optional[List[int]] = None,
    results_dir: str = RESULTS_DIR,
    log_file: str = "parameter_sweep.jsonl",
) -> List[Dict[str, Any]]:
    """
    Parameter sweep: variasi ops, threads, DE population untuk analisis
    mana yang paling mempengaruhi RAM.
    """
    ops_list = ops_list or BATCH_SIZES
    threads_list = threads_list or THREAD_COUNTS
    de_population_list = de_population_list or DE_PARAMS["population_size"]
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(results_dir, log_file)
    all_results: List[Dict[str, Any]] = []

    # Sweep: ops (hanya DE)
    for ops in ops_list:
        th = 1
        print(f"Sweep ops: curve={curve_name} scalar_type=de ops={ops} threads={th}")
        try:
            res = _run_one_scenario(
                scenario_id=f"ops_{ops}_de",
                curve_name=curve_name,
                scalar_type="de",
                ops=ops,
                threads=th,
            )
            res["sweep_param"] = "ops"
            res["sweep_value"] = ops
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error: {e}")

    # Sweep: threads (hanya DE)
    for th in threads_list:
        ops = 500
        print(f"Sweep threads: curve={curve_name} scalar_type=de ops={ops} threads={th}")
        try:
            res = _run_one_scenario(
                scenario_id=f"threads_{th}_de",
                curve_name=curve_name,
                scalar_type="de",
                ops=ops,
                threads=th,
            )
            res["sweep_param"] = "threads"
            res["sweep_value"] = th
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error: {e}")

    # Sweep: DE population (hanya untuk scalar_type=de)
    for pop in de_population_list:
        print(f"Sweep DE population: curve={curve_name} population={pop}")
        try:
            res = _run_one_scenario(
                scenario_id=f"de_pop_{pop}",
                curve_name=curve_name,
                scalar_type="de",
                ops=100,
                threads=1,
                de_population=pop,
            )
            res["sweep_param"] = "de_population"
            res["sweep_value"] = pop
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error: {e}")

    # Sweep: DE generations
    de_generations_list = DE_PARAMS.get("generations", [10, 30, 50])
    for gen in de_generations_list:
        print(f"Sweep DE generations: curve={curve_name} generations={gen}")
        try:
            res = _run_one_scenario(
                scenario_id=f"de_gen_{gen}",
                curve_name=curve_name,
                scalar_type="de",
                ops=100,
                threads=1,
                de_generations=gen,
            )
            res["sweep_param"] = "de_generations"
            res["sweep_value"] = gen
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error: {e}")

    # Sweep: DE F (differential weight)
    de_F_list = DE_PARAMS.get("F", [0.5, 0.8, 1.0])
    for f in de_F_list:
        print(f"Sweep DE F: curve={curve_name} F={f}")
        try:
            res = _run_one_scenario(
                scenario_id=f"de_F_{f}",
                curve_name=curve_name,
                scalar_type="de",
                ops=100,
                threads=1,
                de_F=f,
            )
            res["sweep_param"] = "de_F"
            res["sweep_value"] = f
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error: {e}")

    # Sweep: DE CR (crossover rate)
    de_CR_list = DE_PARAMS.get("CR", [0.3, 0.7, 0.9])
    for cr in de_CR_list:
        print(f"Sweep DE CR: curve={curve_name} CR={cr}")
        try:
            res = _run_one_scenario(
                scenario_id=f"de_CR_{cr}",
                curve_name=curve_name,
                scalar_type="de",
                ops=100,
                threads=1,
                de_CR=cr,
            )
            res["sweep_param"] = "de_CR"
            res["sweep_value"] = cr
            all_results.append(res)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error: {e}")

    return all_results


if __name__ == "__main__":
    import sys
    mode = (sys.argv[1] if len(sys.argv) > 1 else "scenarios").lower()
    if mode == "sweep":
        run_parameter_sweep()
    else:
        run_scenarios()
