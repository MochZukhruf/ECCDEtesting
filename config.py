# -*- coding: utf-8 -*-
"""
Konfigurasi parameter ECC + DE untuk eksperimen blockchain simulator.
Parameter mengikuti spesifikasi jurnal penelitian.
"""

# Mapping nama curve ke modul ecdsa (NIST) — hanya 3 kurva jurnal
CURVES = {
    "secp192r1": "NIST192p",   # P-192
    "secp224r1": "NIST224p",   # P-224
    "secp256r1": "NIST256p",   # P-256
}

# Skenario penelitian (Scenario Matrix dari jurnal)
# S1-S2: P192, 100 tx, 1 node (Random vs DE)
# S3-S4: P224, 1000 tx, 3 nodes (Random vs DE)
# S5-S6: P256, 5000 tx, 5 nodes (Random vs DE)
SCENARIOS = [
    {"id": "S1", "curve": "secp192r1", "scalar_type": "random", "transactions": 100,  "nodes": 1},
    {"id": "S2", "curve": "secp192r1", "scalar_type": "de",     "transactions": 100,  "nodes": 1},
    {"id": "S3", "curve": "secp224r1", "scalar_type": "random", "transactions": 1000, "nodes": 3},
    {"id": "S4", "curve": "secp224r1", "scalar_type": "de",     "transactions": 1000, "nodes": 3},
    {"id": "S5", "curve": "secp256r1", "scalar_type": "random", "transactions": 5000, "nodes": 5},
    {"id": "S6", "curve": "secp256r1", "scalar_type": "de",     "transactions": 5000, "nodes": 5},
]

# Parameter Differential Evolution (sesuai jurnal)
DE_PARAMS = {
    "population_size": 50,   # M = 50
    "mutation_factor": 0.8,  # mr = 0.8
    "crossover_rate": 0.9,   # cr = 0.9
    "generations": 100,      # 100 generasi
}

# Output
RESULTS_DIR = "results"
LOG_FILE = "experiment_log.jsonl"
