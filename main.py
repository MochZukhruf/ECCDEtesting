# -*- coding: utf-8 -*-
"""
Entry point: ECC + DE Blockchain Simulator Experiment.

Workflow:
1. Generate scalar (random / DE optimized)
2. Generate ECC keypair
3. Create transactions
4. Sign transactions
5. Verify transactions
6. Build blocks (blockchain)
7. Measure RAM/CPU/time
8. Run statistical tests
9. Compare results

Tujuan: melihat pengaruh scalar DE terhadap performa dan resource blockchain.
"""

import argparse
import sys
from pathlib import Path

from config import RESULTS_DIR, SCENARIOS, DE_PARAMS


def main():
    parser = argparse.ArgumentParser(
        description="ECC-DE Blockchain Simulator Experiment"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="all",
        choices=["scenarios", "viz", "all"],
        help="scenarios=S1-S6, viz=grafik, all=scenarios+viz",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Run specific scenario (e.g. S1, S2, S3)",
    )
    parser.add_argument("--results-dir", default=RESULTS_DIR, help="Folder hasil log")
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick run: kurangi jumlah transaksi (20 per skenario)"
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Jangan buka dashboard grafik di browser"
    )
    args = parser.parse_args()

    # Prepare scenarios
    scenarios = SCENARIOS
    de_params = dict(DE_PARAMS)

    if args.quick:
        # Override untuk tes cepat
        scenarios = [
            {"id": "S1", "curve": "secp192r1", "scalar_type": "random", "transactions": 20, "nodes": 1},
            {"id": "S2", "curve": "secp192r1", "scalar_type": "de",     "transactions": 20, "nodes": 1},
            {"id": "S3", "curve": "secp256r1", "scalar_type": "random", "transactions": 50, "nodes": 2},
            {"id": "S4", "curve": "secp256r1", "scalar_type": "de",     "transactions": 50, "nodes": 2},
        ]
        de_params["population_size"] = 20
        de_params["generations"] = 20

    if args.scenario:
        # Filter scenario by ID
        scenarios = [s for s in scenarios if s["id"] == args.scenario.upper()]
        if not scenarios:
            print(f"Scenario '{args.scenario}' tidak ditemukan. "
                  f"Pilihan: {[s['id'] for s in SCENARIOS]}")
            return 1

    if args.mode in ("scenarios", "all"):
        from experiment_runner import run_all_scenarios
        results = run_all_scenarios(
            scenarios=scenarios,
            de_params=de_params,
            results_dir=args.results_dir,
        )

    if args.mode in ("viz", "all"):
        from visualization import generate_all
        paths = generate_all(
            results_dir=args.results_dir,
            open_browser=not args.no_browser,
        )
        print("\nGrafik tersimpan:")
        for name, path in paths.items():
            print(f"  {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
