# -*- coding: utf-8 -*-
"""
Statistical Analyzer: 5 pengujian statistik untuk kualitas randomness scalar ECC.

Tests (sesuai jurnal):
1. Shannon Entropy
2. Frequency (Monobit) Test
3. Chi-Square Test
4. Runs Test
5. Autocorrelation Test
"""

import math
from typing import List, Dict, Any

import numpy as np
from scipy import stats


# ============================================================================
# 1. Shannon Entropy
# ============================================================================

def shannon_entropy_test(scalars: List[int], bit_length: int) -> Dict[str, Any]:
    """
    Hitung Shannon entropy rata-rata dari daftar scalar.
    H = -sum(p(x) * log2(p(x))) untuk x in {0, 1}
    
    Entropy maksimum = 1.0 (distribusi 50/50 bit 0 dan 1).
    Scalar yang baik memiliki entropy mendekati 1.0.
    """
    if not scalars or bit_length <= 0:
        return {"test_name": "Shannon Entropy", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    entropies = []
    for k in scalars:
        bits = bin(k)[2:].zfill(bit_length)
        n = len(bits)
        count_1 = bits.count("1")
        count_0 = n - count_1
        if count_0 == 0 or count_1 == 0:
            entropies.append(0.0)
        else:
            p1 = count_1 / n
            p0 = count_0 / n
            h = -(p0 * math.log2(p0) + p1 * math.log2(p1))
            entropies.append(h)

    avg_entropy = float(np.mean(entropies))
    # Entropy >= 0.95 dianggap baik (mendekati random ideal)
    passed = avg_entropy >= 0.95

    return {
        "test_name": "Shannon Entropy",
        "statistic": round(avg_entropy, 6),
        "p_value": None,  # entropy bukan p-value test
        "passed": passed,
        "detail": {
            "min_entropy": round(float(np.min(entropies)), 6),
            "max_entropy": round(float(np.max(entropies)), 6),
            "std_entropy": round(float(np.std(entropies)), 6),
        },
    }


# ============================================================================
# 2. Frequency (Monobit) Test
# ============================================================================

def frequency_test(scalars: List[int], bit_length: int) -> Dict[str, Any]:
    """
    Frequency (monobit) test: cek proporsi bit 0 vs bit 1.
    Seharusnya mendekati 50/50 untuk scalar random yang baik.
    
    Menggunakan z-score dan p-value (two-tailed).
    H0: proporsi bit 1 = 0.5
    """
    if not scalars or bit_length <= 0:
        return {"test_name": "Frequency (Monobit)", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    # Gabungkan semua bit
    all_bits = ""
    for k in scalars:
        all_bits += bin(k)[2:].zfill(bit_length)

    n = len(all_bits)
    count_1 = all_bits.count("1")
    
    # Konversi ke +1/-1
    s_n = 2 * count_1 - n  # S_n = jumlah (+1) - jumlah (-1)
    
    # Statistik uji
    s_obs = abs(s_n) / math.sqrt(n)
    
    # P-value (two-tailed, standard normal)
    p_value = math.erfc(s_obs / math.sqrt(2))
    
    passed = p_value >= 0.01  # significance level 1%

    return {
        "test_name": "Frequency (Monobit)",
        "statistic": round(s_obs, 6),
        "p_value": round(p_value, 6),
        "passed": passed,
        "detail": {
            "total_bits": n,
            "count_ones": count_1,
            "proportion_ones": round(count_1 / n, 6),
        },
    }


# ============================================================================
# 3. Chi-Square Test
# ============================================================================

def chi_square_test(scalars: List[int], bit_length: int) -> Dict[str, Any]:
    """
    Chi-square test pada distribusi byte (8-bit chunks) dari scalar.
    H0: distribusi byte seragam (uniform).
    
    Menggunakan scipy.stats.chisquare.
    """
    if not scalars or bit_length <= 0:
        return {"test_name": "Chi-Square", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    # Gabungkan semua bit, potong per 8-bit
    all_bits = ""
    for k in scalars:
        all_bits += bin(k)[2:].zfill(bit_length)

    # Potong menjadi byte (8-bit chunks)
    n_bytes = len(all_bits) // 8
    if n_bytes < 4:
        return {"test_name": "Chi-Square", "statistic": 0.0,
                "p_value": 0.0, "passed": False,
                "detail": {"error": "data terlalu sedikit"}}

    byte_values = []
    for i in range(n_bytes):
        byte_str = all_bits[i * 8:(i + 1) * 8]
        byte_values.append(int(byte_str, 2))

    # Hitung frekuensi observasi (256 kategori: 0-255)
    observed = np.zeros(256)
    for b in byte_values:
        observed[b] += 1

    # Frekuensi harapan (uniform)
    expected = np.full(256, n_bytes / 256.0)

    # Filter: hanya gunakan kategori dengan frekuensi harapan > 0
    chi2_stat, p_value = stats.chisquare(observed, f_exp=expected)

    passed = p_value >= 0.01

    return {
        "test_name": "Chi-Square",
        "statistic": round(float(chi2_stat), 6),
        "p_value": round(float(p_value), 6),
        "passed": passed,
        "detail": {
            "total_bytes": n_bytes,
            "degrees_of_freedom": 255,
        },
    }


# ============================================================================
# 4. Runs Test
# ============================================================================

def runs_test(scalars: List[int], bit_length: int) -> Dict[str, Any]:
    """
    Runs test: hitung jumlah 'run' (urutan bit berturut-turut yang sama)
    dan bandingkan dengan yang diharapkan.
    
    H0: urutan bit bersifat random (independen).
    """
    if not scalars or bit_length <= 0:
        return {"test_name": "Runs Test", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    # Gabungkan semua bit
    all_bits = ""
    for k in scalars:
        all_bits += bin(k)[2:].zfill(bit_length)

    n = len(all_bits)
    if n < 2:
        return {"test_name": "Runs Test", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    # Proporsi bit 1
    n1 = all_bits.count("1")
    pi = n1 / n

    # Pre-test: frequency test harus lulus dulu
    tau = 2.0 / math.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return {
            "test_name": "Runs Test",
            "statistic": 0.0,
            "p_value": 0.0,
            "passed": False,
            "detail": {"error": "frequency pre-test gagal", "pi": round(pi, 6)},
        }

    # Hitung jumlah runs
    v_obs = 1
    for i in range(1, n):
        if all_bits[i] != all_bits[i - 1]:
            v_obs += 1

    # Statistik Z
    numerator = v_obs - 2 * n * pi * (1 - pi)
    denominator = 2 * math.sqrt(2 * n) * pi * (1 - pi)
    if denominator == 0:
        return {"test_name": "Runs Test", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    z = numerator / denominator
    p_value = math.erfc(abs(z) / math.sqrt(2))

    passed = p_value >= 0.01

    return {
        "test_name": "Runs Test",
        "statistic": round(abs(z), 6),
        "p_value": round(p_value, 6),
        "passed": passed,
        "detail": {
            "observed_runs": v_obs,
            "expected_runs": round(2 * n * pi * (1 - pi) + 1, 2),
            "proportion_ones": round(pi, 6),
        },
    }


# ============================================================================
# 5. Autocorrelation Test
# ============================================================================

def autocorrelation_test(scalars: List[int], bit_length: int, lag: int = 1) -> Dict[str, Any]:
    """
    Autocorrelation test: cek korelasi antara bit pada posisi i dan i+lag.
    Bit stream yang random seharusnya tidak berkorelasi antar posisi.
    
    H0: tidak ada korelasi antar bit pada lag tertentu.
    """
    if not scalars or bit_length <= 0:
        return {"test_name": "Autocorrelation", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    # Gabungkan semua bit, konversi ke array numerik
    all_bits = ""
    for k in scalars:
        all_bits += bin(k)[2:].zfill(bit_length)

    n = len(all_bits)
    if n <= lag:
        return {"test_name": "Autocorrelation", "statistic": 0.0,
                "p_value": 0.0, "passed": False}

    bits_array = np.array([int(b) for b in all_bits], dtype=np.float64)

    # XOR antara bit[i] dan bit[i+lag]
    d = n - lag
    xor_sum = 0
    for i in range(d):
        xor_sum += int(bits_array[i]) ^ int(bits_array[i + lag])

    # Statistik Z
    z = (xor_sum - d / 2.0) / (math.sqrt(d) / 2.0)
    p_value = math.erfc(abs(z) / math.sqrt(2))

    passed = p_value >= 0.01

    return {
        "test_name": "Autocorrelation",
        "statistic": round(abs(z), 6),
        "p_value": round(p_value, 6),
        "passed": passed,
        "detail": {
            "lag": lag,
            "xor_count": xor_sum,
            "total_pairs": d,
            "proportion_xor": round(xor_sum / d, 6) if d > 0 else 0,
        },
    }


# ============================================================================
# Aggregator: jalankan semua test
# ============================================================================

def run_all_tests(scalars: List[int], bit_length: int) -> List[Dict[str, Any]]:
    """
    Jalankan semua 5 pengujian statistik pada daftar scalar.
    
    Returns list of test results, masing-masing berisi:
    - test_name: nama test
    - statistic: nilai statistik uji
    - p_value: p-value (None untuk entropy)
    - passed: True/False
    - detail: informasi tambahan
    """
    results = [
        shannon_entropy_test(scalars, bit_length),
        frequency_test(scalars, bit_length),
        chi_square_test(scalars, bit_length),
        runs_test(scalars, bit_length),
        autocorrelation_test(scalars, bit_length),
    ]
    return results
