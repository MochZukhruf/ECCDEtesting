# -*- coding: utf-8 -*-
"""
Experiment Runner: menjalankan skenario blockchain S1–S6.
Workflow per skenario:
1. Generate scalars (random atau DE)
2. Generate ECC keypairs dari scalars
3. Create transactions (random sender/receiver/amount)
4. Sign all transactions
5. Verify all transactions
6. Build blocks via Node
7. Measure RAM/CPU/time
8. Run statistical tests pada scalars
9. Log results sebagai JSON
"""

import os
import json
import time
import random as rand_module
from typing import List, Dict, Any, Optional

from config import SCENARIOS, DE_PARAMS, RESULTS_DIR, LOG_FILE
from ecc_engine import (
    generate_key_pair_from_scalar,
    get_curve_bit_size,
)
from scalar_generator import get_scalars
from resource_monitor import measure_block, format_metrics
from blockchain_sim.transaction import Transaction
from blockchain_sim.node import Node
from analysis.statistical_analyzer import run_all_tests


def _generate_address(verifying_key) -> str:
    """Generate alamat dari public key (hex string)."""
    import hashlib
    vk_bytes = verifying_key.to_string()
    return hashlib.sha256(vk_bytes).hexdigest()[:40]


def _run_one_scenario(
    scenario: Dict[str, Any],
    de_params: Dict[str, Any],
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Jalankan satu skenario blockchain lengkap.
    Returns dict hasil eksperimen.
    """
    scenario_id = scenario["id"]
    curve_name = scenario["curve"]
    scalar_type = scenario["scalar_type"]
    num_transactions = scenario["transactions"]
    num_nodes = scenario["nodes"]

    print(f"\n{'='*60}")
    print(f"  Skenario {scenario_id}: {curve_name} | {scalar_type} | "
          f"{num_transactions} tx | {num_nodes} nodes")
    print(f"{'='*60}")

    bit_length = get_curve_bit_size(curve_name)
    result = {
        "scenario": scenario_id,
        "curve": curve_name,
        "scalar_type": scalar_type,
        "transactions": num_transactions,
        "nodes": num_nodes,
    }

    # ---- Measurement block ----
    with measure_block(use_tracemalloc=True) as metrics:

        # Step 1: Generate scalars
        print(f"  [1/7] Generate {num_transactions} scalars ({scalar_type})...")
        t0 = time.perf_counter()
        scalars = get_scalars(
            curve_name=curve_name,
            count=num_transactions,
            scalar_type=scalar_type,
            de_population=de_params["population_size"],
            de_generations=de_params["generations"],
            de_F=de_params["mutation_factor"],
            de_CR=de_params["crossover_rate"],
            seed=seed,
        )
        t_scalar = time.perf_counter() - t0
        print(f"       → {len(scalars)} scalars in {t_scalar:.2f}s")

        # Step 2: Generate keypairs dari scalars
        print(f"  [2/7] Generate {num_transactions} ECC keypairs...")
        t0 = time.perf_counter()
        keypairs = []
        for s in scalars:
            sk, vk = generate_key_pair_from_scalar(curve_name, s)
            keypairs.append((sk, vk))
        t_keygen = time.perf_counter() - t0
        print(f"       → {len(keypairs)} keypairs in {t_keygen:.2f}s")

        # Step 3: Create transactions
        print(f"  [3/7] Create {num_transactions} transactions...")
        t0 = time.perf_counter()
        rand_module.seed(seed)
        transactions: List[Transaction] = []
        addresses = [_generate_address(vk) for _, vk in keypairs]

        for i in range(num_transactions):
            sender_idx = i % len(keypairs)
            receiver_idx = (i + 1) % len(keypairs)
            tx = Transaction(
                sender=addresses[sender_idx],
                receiver=addresses[receiver_idx],
                amount=round(rand_module.uniform(0.01, 100.0), 4),
                timestamp=time.time() + i * 0.001,
            )
            transactions.append(tx)
        t_create = time.perf_counter() - t0
        print(f"       → {len(transactions)} transactions in {t_create:.4f}s")

        # Step 4: Sign all transactions
        print(f"  [4/7] Sign {num_transactions} transactions...")
        t0 = time.perf_counter()
        for i, tx in enumerate(transactions):
            sender_idx = i % len(keypairs)
            sk, vk = keypairs[sender_idx]
            tx.sign(sk)
        t_sign = time.perf_counter() - t0
        print(f"       → Signed in {t_sign:.2f}s")

        # Step 5: Verify all transactions
        print(f"  [5/7] Verify {num_transactions} transactions...")
        t0 = time.perf_counter()
        verified_count = sum(1 for tx in transactions if tx.verify())
        t_verify = time.perf_counter() - t0
        print(f"       → {verified_count}/{num_transactions} verified in {t_verify:.2f}s")

        # Step 6: Build blocks via Node(s)
        print(f"  [6/7] Build blockchain ({num_nodes} nodes)...")
        t0 = time.perf_counter()
        nodes: List[Node] = []
        for node_id in range(num_nodes):
            node = Node(node_id=node_id)
            # Distribusikan transaksi ke nodes (round-robin)
            node_txs = [
                tx for j, tx in enumerate(transactions)
                if j % num_nodes == node_id
            ]
            node.add_transactions(node_txs)
            blocks = node.mine_all_pending()
            nodes.append(node)
        t_block = time.perf_counter() - t0

        total_blocks = sum(len(n.blockchain) for n in nodes)
        chain_valid = all(n.validate_chain() for n in nodes)
        print(f"       → {total_blocks} blocks, chain_valid={chain_valid} in {t_block:.4f}s")

        # Step 7: Statistical tests pada scalars
        print(f"  [7/7] Run statistical tests...")
        t0 = time.perf_counter()
        stat_results = run_all_tests(scalars, bit_length)
        t_stats = time.perf_counter() - t0
        print(f"       → {len(stat_results)} tests in {t_stats:.4f}s")

    # ---- Compile results ----
    formatted = format_metrics(metrics)
    result["RAM_MB"] = formatted["peak_memory_mb"]
    result["CPU_percent"] = formatted["cpu_percent"]
    result["execution_time_ms"] = round(formatted["time_sec"] * 1000, 2)

    # Timing breakdown
    result["timing"] = {
        "scalar_gen_sec": round(t_scalar, 4),
        "keygen_sec": round(t_keygen, 4),
        "tx_create_sec": round(t_create, 4),
        "sign_sec": round(t_sign, 4),
        "verify_sec": round(t_verify, 4),
        "block_build_sec": round(t_block, 4),
        "stats_sec": round(t_stats, 4),
    }

    # Blockchain info
    result["blockchain"] = {
        "total_blocks": total_blocks,
        "chain_valid": chain_valid,
        "verified_transactions": verified_count,
    }

    # Statistical test results
    entropy_result = next(
        (r for r in stat_results if r["test_name"] == "Shannon Entropy"), {}
    )
    chi_result = next(
        (r for r in stat_results if r["test_name"] == "Chi-Square"), {}
    )
    result["entropy"] = entropy_result.get("statistic", 0)
    result["chi_square"] = chi_result.get("p_value", 0)
    result["statistical_tests"] = stat_results

    # Print summary
    print(f"\n  Summary {scenario_id}:")
    print(f"    RAM       : {result['RAM_MB']:.2f} MB")
    print(f"    CPU       : {result['CPU_percent']:.1f}%")
    print(f"    Time      : {result['execution_time_ms']:.1f} ms")
    print(f"    Entropy   : {result['entropy']:.6f}")
    print(f"    Chi-square: {result['chi_square']}")
    for st in stat_results:
        status = "✓ PASS" if st["passed"] else "✗ FAIL"
        print(f"    {st['test_name']:20s} : {status}  (stat={st['statistic']})")

    return result


def run_all_scenarios(
    scenarios: Optional[List[Dict]] = None,
    de_params: Optional[Dict] = None,
    results_dir: str = RESULTS_DIR,
    log_file: str = LOG_FILE,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Jalankan semua skenario (S1–S6) dan simpan log JSONL.
    """
    if scenarios is None:
        scenarios = SCENARIOS
    if de_params is None:
        de_params = DE_PARAMS

    os.makedirs(results_dir, exist_ok=True)
    log_path = os.path.join(results_dir, log_file)

    all_results = []

    print(f"\n{'#'*60}")
    print(f"  ECC-DE Blockchain Experiment")
    print(f"  {len(scenarios)} scenarios | DE: pop={de_params['population_size']}, "
          f"gen={de_params['generations']}, F={de_params['mutation_factor']}, "
          f"CR={de_params['crossover_rate']}")
    print(f"{'#'*60}")

    for scenario in scenarios:
        result = _run_one_scenario(scenario, de_params, seed=seed)
        all_results.append(result)

        # Append ke log file (JSONL)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, default=str) + "\n")

    # Print comparison table
    print(f"\n{'='*80}")
    print(f"  HASIL PERBANDINGAN")
    print(f"{'='*80}")
    print(f"  {'Scenario':<10} {'Curve':<12} {'Scalar':<8} {'TX':<6} "
          f"{'RAM_MB':<10} {'CPU%':<8} {'Time_ms':<12} {'Entropy':<10}")
    print(f"  {'-'*76}")
    for r in all_results:
        print(f"  {r['scenario']:<10} {r['curve']:<12} {r['scalar_type']:<8} "
              f"{r['transactions']:<6} {r['RAM_MB']:<10.2f} {r['CPU_percent']:<8.1f} "
              f"{r['execution_time_ms']:<12.1f} {r['entropy']:<10.6f}")

    print(f"\n  Log disimpan: {log_path}")
    return all_results


if __name__ == "__main__":
    run_all_scenarios()
