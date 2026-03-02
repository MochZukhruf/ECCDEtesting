# -*- coding: utf-8 -*-
"""
Entry point: ECC + DE Resource Experiment.
- Phase 1: ECC Implementation (ecc_engine)
- Phase 2: Scalar Generation — Random vs DE (scalar_generator)
- Phase 3: ECC Operation Execution (experiment_runner)
- Phase 4: Resource Measurement & Analysis (resource_monitor, analysis, visualization)

Tujuan: menganalisis parameter mana (curve, ops, threads, DE population/F/CR)
yang paling mempengaruhi konsumsi RAM.
"""

import argparse
import sys
from pathlib import Path

from config import RESULTS_DIR, SCENARIOS


def main():
    parser = argparse.ArgumentParser(
        description="ECC + DE Resource Experiment: analisis dampak parameter terhadap RAM/CPU/time."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="all",
        choices=["scenarios", "sweep", "analysis", "viz", "all"],
        help="scenarios=S1-S6, sweep=parameter sweep, analysis=sensitivity, viz=grafik, all=scenarios+sweep+analysis+viz",
    )
    parser.add_argument("--results-dir", default=RESULTS_DIR, help="Folder hasil log")
    parser.add_argument("--quick", action="store_true", help="Quick run: kurangi ops dan DE population")
    parser.add_argument("--no-browser", action="store_true", help="Jangan buka dashboard grafik di browser")
    args = parser.parse_args()

    if args.quick:
        # Override untuk tes cepat
        import config as cfg
        cfg.SCENARIOS = [
            {"id": "S1", "curve": "secp192r1", "scalar_type": "de", "ops": 20, "threads": 1},
            {"id": "S2", "curve": "secp256r1", "scalar_type": "de", "ops": 50, "threads": 1},
        ]
        cfg.BATCH_SIZES = [10, 50]
        cfg.THREAD_COUNTS = [1, 2]
        cfg.DE_PARAMS["population_size"] = [20, 50]

    if args.mode in ("scenarios", "all"):
        from experiment_runner import run_scenarios
        run_scenarios(results_dir=args.results_dir)

    if args.mode in ("sweep", "all"):
        from experiment_runner import run_parameter_sweep
        run_parameter_sweep(results_dir=args.results_dir)

    if args.mode in ("analysis", "all"):
        from analysis import run_analysis
        res = run_analysis(results_dir=args.results_dir)
        print("Parameter paling mempengaruhi RAM:", res.get("parameter_most_affects_RAM"))
        print("Sensitivity ranking (top 5):")
        for r in res.get("sensitivity_ranking", [])[:5]:
            print(" ", r.get("parameter"), "-> correlation:", r.get("correlation_with_RAM"), "range:", r.get("RAM_range_when_varied"))

    if args.mode in ("viz", "all"):
        from visualization import generate_all
        paths = generate_all(
            results_dir=args.results_dir,
            open_browser=not args.no_browser,
        )
        print("Grafik tersimpan:")
        for name, path in paths.items():
            print(" ", path)
        if paths.get("dashboard"):
            print("\nDashboard (semua grafik):", paths["dashboard"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
