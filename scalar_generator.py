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




def _ga_de_optimize_scalar(
    curve_name: str,
    population_size: int,
    generations: int,
    de_F: float,
    de_CR: float,
    ga_MR: float,
    ga_CR: float,
    objective: Callable[[int], float],
    seed: Optional[int] = None,
) -> int:
    if seed is not None:
        random.seed(seed)
    order = get_curve_order(curve_name)
    lo, hi = 1, order - 1

    def clip(x: float) -> int:
        x = int(round(x))
        return max(lo, min(hi, x))

    pop = [random.randrange(lo, hi + 1) for _ in range(population_size)]
    fitness = [objective(k) for k in pop]

    ga_gens = generations // 2
    de_gens = generations - ga_gens

    # Phase 1: GA
    for _gen in range(ga_gens):
        new_pop = []
        def select():
            k1, k2 = random.sample(range(population_size), 2)
            return k1 if fitness[k1] <= fitness[k2] else k2
            
        for _ in range((population_size + 1) // 2):
            p1 = pop[select()]
            p2 = pop[select()]
            
            if random.random() < ga_CR:
                alpha = random.random()
                c1 = clip(alpha * p1 + (1 - alpha) * p2)
                c2 = clip((1 - alpha) * p1 + alpha * p2)
            else:
                c1, c2 = p1, p2
                
            if random.random() < ga_MR:
                c1 = clip(c1 + random.uniform(-0.1, 0.1) * (hi - lo))
            if random.random() < ga_MR:
                c2 = clip(c2 + random.uniform(-0.1, 0.1) * (hi - lo))
                
            new_pop.extend([c1, c2])
            
        pop = new_pop[:population_size]
        fitness = [objective(k) for k in pop]

    # Phase 2: DE
    for _gen in range(de_gens):
        for i in range(population_size):
            idx = list(range(population_size))
            idx.remove(i)
            a, b, c = random.sample(idx, 3)
            mutant = clip(pop[a] + de_F * (pop[b] - pop[c]))
            trial = mutant if random.random() < de_CR else pop[i]
            
            f_trial = objective(trial)
            if f_trial <= fitness[i]:
                pop[i] = trial
                fitness[i] = f_trial

    best_idx = min(range(population_size), key=lambda i: fitness[i])
    return pop[best_idx]


def ga_de_optimized_scalars(
    curve_name: str,
    count: int,
    population_size: int = 50,
    generations: int = 100,
    de_F: float = 0.8,
    de_CR: float = 0.9,
    ga_MR: float = 0.1,
    ga_CR: float = 0.9,
    seed: Optional[int] = None,
) -> List[int]:
    bit_length = get_curve_bit_size(curve_name)
    def objective(k: int) -> float:
        return -shannon_entropy(k, bit_length)

    scalars: List[int] = []
    for i in range(count):
        s = _ga_de_optimize_scalar(
            curve_name,
            population_size=population_size,
            generations=generations,
            de_F=de_F,
            de_CR=de_CR,
            ga_MR=ga_MR,
            ga_CR=ga_CR,
            objective=objective,
            seed=(seed + i) if seed is not None else None,
        )
        scalars.append(s)
    return scalars


def eg_scalars(
    curve_name: str,
    count: int,
    seed: Optional[int] = None,
) -> List[int]:
    """Generate scalars menggunakan Entropy Guided Initialization saja (tanpa DE)."""
    if seed is not None:
        random.seed(seed)
    
    order = get_curve_order(curve_name)
    bit_length = get_curve_bit_size(curve_name)
    lo, hi = 1, order - 1
    
    scalars = []
    ones_count = bit_length // 2
    zeros_count = bit_length - ones_count
    
    for _ in range(count):
        while True:
            bits = ['1'] * ones_count + ['0'] * zeros_count
            random.shuffle(bits)
            k = int("".join(bits), 2)
            if lo <= k <= hi:
                scalars.append(k)
                break
                
    return scalars

def _eg_de_optimize_scalar(
    curve_name: str,
    population_size: int,
    generations: int,
    F: float,
    CR: float,
    objective: Callable[[int], float],
    seed: Optional[int] = None,
) -> int:
    if seed is not None:
        random.seed(seed)
    order = get_curve_order(curve_name)
    bit_length = get_curve_bit_size(curve_name)
    lo, hi = 1, order - 1

    # Step 1: Entropy Guided Scalar Initialization (EGI)
    pop = []
    # Target 50% ones
    ones_count = bit_length // 2
    zeros_count = bit_length - ones_count

    while len(pop) < population_size:
        # Create balanced bit list
        bits = ['1'] * ones_count + ['0'] * zeros_count
        random.shuffle(bits)
        # Convert to integer
        k = int("".join(bits), 2)
        if lo <= k <= hi:
            pop.append(k)

    fitness = [objective(k) for k in pop]
    
    # Track best for early stopping
    best_fitness = min(fitness)
    gens_without_improvement = 0

    # Step 3: DE Refinement
    for gen in range(generations):
        # Early stopping constraints
        # Stop if best entropy >= 0.999 (which means fitness <= -0.999)
        if best_fitness <= -0.999:
            break
        if gens_without_improvement >= 10:
            break
            
        gen_improved = False

        for i in range(population_size):
            idx = list(range(population_size))
            idx.remove(i)
            a, b, c = random.sample(idx, 3)
            
            # Mutation: vi = kr1 + F*(kr2 - kr3) mod n
            diff = pop[b] - pop[c]
            mutant = int(pop[a] + F * diff) % order
            # Ensure valid bounds (1 <= k <= n-1)
            if mutant == 0:
                mutant = 1
                
            # Crossover
            if random.random() < CR:
                trial = mutant
            else:
                trial = pop[i]
                
            f_trial = objective(trial)
            
            # Selection
            if f_trial <= fitness[i]:
                pop[i] = trial
                fitness[i] = f_trial
                
                if f_trial < best_fitness:
                    best_fitness = f_trial
                    gen_improved = True
                    
        if not gen_improved:
            gens_without_improvement += 1
        else:
            gens_without_improvement = 0

    best_idx = min(range(population_size), key=lambda i: fitness[i])
    return pop[best_idx]


def eg_de_optimized_scalars(
    curve_name: str,
    count: int,
    population_size: int = 50,
    generations: int = 100,
    F: float = 0.8,
    CR: float = 0.9,
    seed: Optional[int] = None,
) -> List[int]:
    bit_length = get_curve_bit_size(curve_name)
    def objective(k: int) -> float:
        return -shannon_entropy(k, bit_length)

    scalars: List[int] = []
    for i in range(count):
        s = _eg_de_optimize_scalar(
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
    de_params: Optional[dict] = None,
    ga_de_params: Optional[dict] = None,
    eg_de_params: Optional[dict] = None,
    seed: Optional[int] = 42,
) -> List[int]:
    if scalar_type == "random":
        return random_scalars(curve_name, count, seed=seed)
        
    if scalar_type == "de":
        if de_params is None: de_params = {}
        return de_optimized_scalars(
            curve_name,
            count,
            population_size=de_params.get("population_size", 50),
            generations=de_params.get("generations", 100),
            F=de_params.get("mutation_factor", 0.8),
            CR=de_params.get("crossover_rate", 0.9),
            seed=seed,
        )

    if scalar_type == "ga_de":
        if ga_de_params is None: ga_de_params = {}
        return ga_de_optimized_scalars(
            curve_name,
            count,
            population_size=ga_de_params.get("population_size", 50),
            generations=ga_de_params.get("generations", 100),
            de_F=ga_de_params.get("de_mutation_factor", 0.8),
            de_CR=ga_de_params.get("de_crossover_rate", 0.9),
            ga_MR=ga_de_params.get("ga_mutation_rate", 0.1),
            ga_CR=ga_de_params.get("ga_crossover_rate", 0.9),
            seed=seed,
        )

    if scalar_type == "eg":
        return eg_scalars(curve_name, count, seed=seed)

    if scalar_type == "eg_de":
        if eg_de_params is None: eg_de_params = {}
        return eg_de_optimized_scalars(
            curve_name,
            count,
            population_size=eg_de_params.get("population_size", 50),
            generations=eg_de_params.get("generations", 100),
            F=eg_de_params.get("mutation_factor", 0.8),
            CR=eg_de_params.get("crossover_rate", 0.9),
            seed=seed,
        )
        
    raise ValueError("scalar_type harus 'random', 'de', 'ga_de', 'eg', atau 'eg_de'")

