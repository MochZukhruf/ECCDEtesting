# -*- coding: utf-8 -*-
"""
Entry point: ECC + DE Blockchain Simulator Experiment.

Workflow:
1. Generate scalar (random / DE / GA / GA+DE / EG+DE)
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

import sys
from config import RESULTS_DIR


def main():
    from experiment_runner import show_menu, run_all_scenarios

    selected = show_menu()
    if not selected:
        return 0

    results = run_all_scenarios(
        scenarios=selected,
        results_dir=RESULTS_DIR,
    )

    # Tanya apakah ingin generate visualisasi
    print()
    viz_choice = input("  Generate visualisasi grafik? (y/n): ").strip().lower()
    if viz_choice == 'y':
        from visualization import generate_all
        paths = generate_all(
            results_dir=RESULTS_DIR,
            open_browser=True,
        )
        print("\nGrafik tersimpan:")
        for name, path in paths.items():
            print(f"  {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
