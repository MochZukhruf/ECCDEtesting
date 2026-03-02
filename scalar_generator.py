# -*- coding: utf-8 -*-
"""
Scalar Generator: Random scalar vs DE-optimized scalar untuk ECC.
DE meminimalkan fungsi objektif (misalnya Hamming weight) sehingga scalar
"optimized" — fokus eksperimen: dampak DE (population, dll) terhadap RAM.
"""

import random
from typing import List, Callable, Optional

from ecc_engine import get_curve_order


def random_scalars(curve_name: str, count: int, seed: Optional[int] = None) -> List[int]:
    """Generate list scalar acak dalam range [1, n-1] untuk curve."""
    if seed is not None:
        random.seed(seed)
    order = get_curve_order(curve_name)
    return [random.randrange(1, order) for _ in range(count)]


def hamming_weight(k: int) -> int:
    """Jumlah bit 1 pada representasi biner k (untuk objektif DE)."""
    return bin(k).count("1")


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
    Differential Evolution: cari scalar dalam [1, n-1] yang meminimalkan objective.
    Returns satu scalar terbaik.
    """
    if seed is not None:
        random.seed(seed)
    order = get_curve_order(curve_name)
    # Batas untuk DE: scalar valid 1 .. n-1
    lo, hi = 1, order - 1
    dim = 1  # satu scalar per individu

    def clip(x: float) -> int:
        x = int(round(x))
        return max(lo, min(hi, x))

    # Populasi: list of (scalar, fitness)
    pop = [random.randrange(lo, hi + 1) for _ in range(population_size)]
    fitness = [objective(k) for k in pop]

    for _ in range(generations - 1):
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
    population_size: int = 100,
    generations: int = 30,
    F: float = 0.8,
    CR: float = 0.7,
    minimize_hamming: bool = True,
    seed: Optional[int] = None,
) -> List[int]:
    """
    Generate `count` scalar hasil optimasi DE.
    Objektif default: minimalkan Hamming weight (scalar dengan sedikit bit 1).
    """
    order = get_curve_order(curve_name)
    objective = hamming_weight if minimize_hamming else (lambda k: -hamming_weight(k))
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
    de_population: int = 100,
    de_generations: int = 30,
    de_F: float = 0.8,
    de_CR: float = 0.7,
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
