# -*- coding: utf-8 -*-
"""
Konfigurasi parameter ECC + DE untuk eksperimen resource (RAM/CPU/Time).
Parameter ini divariasikan untuk analisis: mana yang paling mempengaruhi RAM.
"""

# Mapping nama curve ke modul ecdsa (NIST)
CURVES = {
    "secp192r1": "NIST192p",   # P-192
    "secp224r1": "NIST224p",   # P-224
    "secp256r1": "NIST256p",   # P-256
    "secp384r1": "NIST384p",   # P-384
    "secp521r1": "NIST521p",   # P-521
}

# Skenario penelitian — hanya DE (scalar hasil Differential Evolution)
SCENARIOS = [
    {"id": "S1", "curve": "secp192r1", "scalar_type": "de", "ops": 100, "threads": 1},
    {"id": "S2", "curve": "secp256r1", "scalar_type": "de", "ops": 1000, "threads": 4},
    {"id": "S3", "curve": "secp521r1", "scalar_type": "de", "ops": 5000, "threads": 8},
]

# Parameter Differential Evolution (untuk analisis pengaruh ke RAM)
DE_PARAMS = {
    "population_size": [50, 100, 200],   # Populasi besar = RAM tinggi
    "generations": [10, 30, 50],
    "F": [0.5, 0.8, 1.0],                # Differential weight
    "CR": [0.3, 0.7, 0.9],               # Crossover probability
}

# Default DE (jika tidak divariasikan)
DE_DEFAULT = {
    "population_size": 100,
    "generations": 30,
    "F": 0.8,
    "CR": 0.7,
}

# Batch operasi untuk stress test RAM
BATCH_SIZES = [10, 100, 1000, 10000]

# Thread counts untuk parallel
THREAD_COUNTS = [1, 2, 4, 8, 16]

# Output
RESULTS_DIR = "results"
LOG_FILE = "experiment_log.jsonl"
