# ECC + Differential Evolution — Resource Experiment

**Tujuan penelitian:** Menganalisis dampak penggunaan scalar hasil optimasi (DE) terhadap konsumsi memori dan performa komputasi pada algoritma Elliptic Curve Cryptography (ECC), serta **identifikasi parameter ECC/DE mana yang paling mempengaruhi RAM**.

## Skema Metodologi (4 Fase)

| Fase | Modul | Deskripsi |
|------|--------|-----------|
| 1 | `ecc_engine.py` | Implementasi ECC (curve NIST: secp192r1–secp521r1) |
| 2 | `scalar_generator.py` | Pembangkitan scalar: **DE-optimized** saja |
| 3 | `experiment_runner.py` | Eksekusi operasi ECC (batch, paralel) |
| 4 | `resource_monitor.py`, `analysis.py`, `visualization.py` | Pengukuran RAM/CPU/time, analisis sensitivitas, visualisasi |

## Arsitektur Eksperimen

```
Scalar Generator (DE Optimized)
            ↓
        ECC Engine (secp* curves)
            ↓
    Resource Monitor (RAM / CPU / Time)
            ↓
        Data Logger (results/*.jsonl)
            ↓
        Analysis → Parameter mana paling pengaruh RAM?
        Visualization → Grafik
```

## Parameter yang Divariasikan (untuk analisis RAM)

- **ECC:** curve (192–521 bit), jumlah operasi (ops), jumlah thread.
- **DE:** `population_size` (50, 100, 200), `generations`, `F`, `CR`.

Metrik yang diukur: **RAM (peak, before/after)**, CPU (%), waktu (s), throughput (ops/s).

## Instalasi

```bash
cd d:\S2\Bimbingan\TestUnit
pip install -r requirements.txt
```

## Cara Menjalankan

- **Skenario S1–S3 (hanya DE):**  
  `python main.py scenarios`

- **Parameter sweep (ops, threads, DE population):**  
  `python main.py sweep`

- **Analisis sensitivitas (parameter mana paling pengaruh RAM):**  
  `python main.py analysis`

- **Grafik (RAM vs iterations, curve, threads, ringkasan DE):**  
  `python main.py viz`

- **Semua (scenarios + sweep + analysis + viz):**  
  `python main.py all`

- **Tes cepat (ops dan DE population kecil):**  
  `python main.py all --quick`

## Output

- **Log:** `results/experiment_log.jsonl`, `results/parameter_sweep.jsonl`
- **Grafik:** `results/figures/`  
  - `ram_vs_iterations.png`  
  - `ram_vs_curve_size.png`  
  - `ram_vs_threads.png`  
  - `de_summary.png`  
  - `sensitivity_ranking.png` (parameter paling mempengaruhi RAM)

## Interpretasi Hasil

- **`analysis.py`** menghitung korelasi dan range RAM per parameter, lalu meranking parameter berdasarkan **impact score**. Parameter dengan skor tertinggi = **paling mempengaruhi RAM**.
- Grafik **sensitivity_ranking** menampilkan ranking parameter DE; grafik lain: RAM vs iterations, curve size, threads, dan ringkasan DE.

## Catatan

- Pengukuran RAM dengan `tracemalloc` + `psutil` (proses saat ini). Untuk run paralel (threads > 1), yang diukur adalah proses utama; untuk perbandingan ketat RAM per skenario, bisa gunakan `threads=1` atau jalankan tiap skenario terpisah.
- Curve: secp192r1, secp224r1, secp256r1, secp384r1, secp521r1 (library `ecdsa`).
