# -*- coding: utf-8 -*-
"""
Scalar Generator: Random scalar vs DE-optimized scalar untuk ECC.
DE memaksimalkan Shannon entropy dari representasi bit scalar
sesuai spesifikasi jurnal penelitian.
"""

import math
import random
from typing import List, Callable, Optional

from ecc_engine import get_curve_order, get_curve_bit_size


def random_scalars(curve_name: str, count: int, seed: Optional[int] = None) -> List[int]:
    """Generate list scalar acak dalam range [1, n-1] untuk curve."""
    if seed is not None:
        random.seed(seed)
    order = get_curve_order(curve_name)
    return [random.randrange(1, order) for _ in range(count)]


def shannon_entropy(k: int, bit_length: int) -> float:
    """
    Hitung Shannon entropy dari representasi bit scalar k.
    H = -sum(p(x) * log2(p(x))) untuk x in {0, 1}
    Entropy maksimum = 1.0 (distribusi 50/50 bit 0 dan 1).
    """
    if bit_length <= 0:
        return 0.0
    bits = bin(k)[2:].zfill(bit_length)
    n = len(bits)
    count_1 = bits.count("1")
    count_0 = n - count_1
    if count_0 == 0 or count_1 == 0:
        return 0.0
    p1 = count_1 / n
    p0 = count_0 / n
    return -(p0 * math.log2(p0) + p1 * math.log2(p1))


def _de_optimize_scalar(
    curve_name: str,
    population_size: int,
    generations: int,
    F: float,
    CR: float,
    objective: Callable[[int], float],
    seed: Optional[int] = None,
) -> int:
    """
    Differential Evolution: cari scalar dalam [1, n-1] yang memaksimalkan objective.
    Objective: Shannon entropy (dimaksimalkan via negasi untuk minimisasi).
    Returns satu scalar terbaik.
    """
    if seed is not None:
        random.seed(seed)
    order = get_curve_order(curve_name)
    lo, hi = 1, order - 1

    def clip(x: float) -> int:
        x = int(round(x))
        return max(lo, min(hi, x))

    # Inisialisasi populasi
    pop = [random.randrange(lo, hi + 1) for _ in range(population_size)]
    fitness = [objective(k) for k in pop]

    for _gen in range(generations - 1):
        for i in range(population_size):
            # Mutasi: pilih 3 indeks berbeda
            idx = list(range(population_size))
            idx.remove(i)
            a, b, c = random.sample(idx, 3)
            # mutant = pop[a] + F * (pop[b] - pop[c])
            mutant = pop[a] + F * (pop[b] - pop[c])
            mutant = clip(mutant)
            # Crossover (CR)
            if random.random() < CR:
                trial = mutant
            else:
                trial = pop[i]
            trial = clip(trial)
            f_trial = objective(trial)
            if f_trial <= fitness[i]:
                pop[i] = trial
                fitness[i] = f_trial

    best_idx = min(range(population_size), key=lambda i: fitness[i])
    return pop[best_idx]


def de_optimized_scalars(
    curve_name: str,
    count: int,
    population_size: int = 50,
    generations: int = 100,
    F: float = 0.8,
    CR: float = 0.9,
    seed: Optional[int] = None,
) -> List[int]:
    """
    Generate `count` scalar hasil optimasi DE.
    Objektif: maksimalkan Shannon entropy (negate untuk minimisasi DE).
    """
    bit_length = get_curve_bit_size(curve_name)

    def objective(k: int) -> float:
        # Negasi karena DE meminimalkan, kita ingin memaksimalkan entropy
        return -shannon_entropy(k, bit_length)

    scalars: List[int] = []
    for i in range(count):
        s = _de_optimize_scalar(
            curve_name,
            population_size=population_size,
            generations=generations,
            F=F,
            CR=CR,
            objective=objective,
            seed=(seed + i) if seed is not None else None,
        )
        scalars.append(s)
    return scalars


def get_scalars(
    curve_name: str,
    count: int,
    scalar_type: str,
    de_population: int = 50,
    de_generations: int = 100,
    de_F: float = 0.8,
    de_CR: float = 0.9,
    seed: Optional[int] = 42,
) -> List[int]:
    """
    Satu entry point: scalar_type in ('random', 'de').
    """
    if scalar_type == "random":
        return random_scalars(curve_name, count, seed=seed)
    if scalar_type == "de":
        return de_optimized_scalars(
            curve_name,
            count,
            population_size=de_population,
            generations=de_generations,
            F=de_F,
            CR=de_CR,
            seed=seed,
        )
    raise ValueError("scalar_type harus 'random' atau 'de'")
