# Dokumentasi Proyek — ECC + Differential Evolution Resource Experiment

Dokumentasi lengkap untuk proyek eksperimen resource (RAM/CPU/waktu) pada pipeline **Elliptic Curve Cryptography (ECC)** dengan scalar hasil optimasi **Differential Evolution (DE)**.

---

## Daftar Isi

1. [Ringkasan Proyek](#1-ringkasan-proyek)
2. [Persyaratan dan Instalasi](#2-persyaratan-dan-instalasi)
3. [Struktur Proyek](#3-struktur-proyek)
4. [Konfigurasi](#4-konfigurasi)
5. [Cara Menjalankan](#5-cara-menjalankan)
6. [Output dan Hasil](#6-output-dan-hasil)
7. [Referensi Modul](#7-referensi-modul)
8. [Dokumen Terkait](#8-dokumen-terkait)

---

## 1. Ringkasan Proyek

### Tujuan

- Menganalisis **dampak scalar hasil optimasi DE** terhadap **konsumsi memori (RAM)** dan performa komputasi pada ECC.
- Mengidentifikasi **parameter DE mana yang paling mempengaruhi RAM** (de_population, de_generations, de_F, de_CR).

### Arsitektur (4 Fase)

```
Scalar Generator (DE)  →  ECC Engine (curve secp*)  →  Resource Monitor (RAM/CPU/Time)
        →  Data Logger (results/*.jsonl)  →  Analysis (ranking parameter DE)  →  Grafik & Dashboard
```

| Fase | Modul | Fungsi |
|------|--------|--------|
| 1 | `ecc_engine.py` | Operasi scalar multiplication pada curve NIST (secp192r1–secp521r1), batch, paralel |
| 2 | `scalar_generator.py` | Pembangkitan scalar DE (optimasi Hamming weight) |
| 3 | `experiment_runner.py` | Menjalankan skenario dan parameter sweep, menulis log |
| 4 | `resource_monitor.py`, `analysis.py`, `visualization.py` | Pengukuran resource, analisis sensitivitas, grafik & dashboard HTML |

### Metrik yang Diukur

- **RAM:** memory_before_mb, memory_after_mb, **peak_memory_mb**
- **Waktu:** time_sec (detik)
- **CPU:** cpu_percent (%)
- **Throughput:** throughput_ops_per_sec (ops/detik)

---

## 2. Persyaratan dan Instalasi

### Persyaratan

- **Python:** 3.8 atau lebih baru (disarankan 3.10+)
- **Sistem operasi:** Windows, Linux, atau macOS

### Dependensi (requirements.txt)

| Paket | Versi minimal | Fungsi |
|-------|----------------|--------|
| ecdsa | 0.19.0 | Kurva eliptik NIST, operasi ECC |
| psutil | 5.9.0 | Pengukuran RAM/CPU proses |
| pandas | 2.0.0 | Load log, analisis data |
| numpy | 1.24.0 | Perhitungan numerik |
| matplotlib | 3.7.0 | Grafik |
| scipy | 1.11.0 | (opsional) Dukungan numerik |
| memory-profiler | 0.61.0 | (opsional) Profiling memori |

### Instalasi

```bash
cd d:\S2\Bimbingan\TestUnit
pip install -r requirements.txt
```

Untuk lingkungan virtual (opsional):

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

---

## 3. Struktur Proyek

```
TestUnit/
├── main.py                 # Entry point: scenarios, sweep, analysis, viz, all
├── config.py               # Konfigurasi: curve, skenario, parameter DE, path output
├── ecc_engine.py           # Engine ECC (scalar multiplication, batch, paralel)
├── scalar_generator.py     # Generator scalar DE (dan random, tidak dipakai di skenario)
├── resource_monitor.py     # Pengukuran RAM/CPU/waktu (tracemalloc, psutil)
├── experiment_runner.py     # Runner skenario S1–S3 dan parameter sweep
├── analysis.py             # Analisis sensitivitas (ranking parameter DE vs RAM)
├── visualization.py        # Grafik dan dashboard HTML
├── requirements.txt
├── README.md
├── DOCUMENTATION.md        # Dokumen ini
├── PEMBAHASAN.md           # Pembahasan penelitian
└── results/                # Dibuat saat menjalankan eksperimen
    ├── experiment_log.jsonl
    ├── parameter_sweep.jsonl
    └── figures/
        ├── ram_vs_iterations.png
        ├── ram_vs_curve_size.png
        ├── ram_vs_threads.png
        ├── de_summary.png
        ├── sensitivity_ranking.png
        └── dashboard.html
```

---

## 4. Konfigurasi

File **`config.py`** mengatur semua parameter yang dipakai skenario dan sweep.

### Curve ECC (NIST)

| Nama config | Curve library | Bit size |
|-------------|----------------|----------|
| secp192r1 | NIST192p | 192 |
| secp224r1 | NIST224p | 224 |
| secp256r1 | NIST256p | 256 |
| secp384r1 | NIST384p | 384 |
| secp521r1 | NIST521p | 521 |

### Skenario (SCENARIOS)

Skenario tetap menggunakan **hanya scalar DE**. Default:

| ID | Curve | Ops | Threads |
|----|--------|-----|--------|
| S1 | secp192r1 | 100 | 1 |
| S2 | secp256r1 | 1000 | 4 |
| S3 | secp521r1 | 5000 | 8 |

### Parameter DE

- **DE_PARAMS** (nilai yang divariasikan saat sweep):
  - `population_size`: [50, 100, 200]
  - `generations`: [10, 30, 50]
  - `F`: [0.5, 0.8, 1.0]
  - `CR`: [0.3, 0.7, 0.9]

- **DE_DEFAULT** (nilai tetap jika tidak di-sweep):
  - population_size: 100, generations: 30, F: 0.8, CR: 0.7

### Lainnya

- **BATCH_SIZES:** [10, 100, 1000, 10000] — variasi ops saat sweep
- **THREAD_COUNTS:** [1, 2, 4, 8, 16] — variasi threads saat sweep
- **RESULTS_DIR:** `"results"`, **LOG_FILE:** `"experiment_log.jsonl"`

---

## 5. Cara Menjalankan

### Entry point

Semua perintah melalui **`main.py`**:

```bash
python main.py [mode] [opsi]
```

### Mode

| Mode | Deskripsi |
|------|-----------|
| **scenarios** | Menjalankan skenario S1–S3 (hanya DE), menulis ke `experiment_log.jsonl`. |
| **sweep** | Parameter sweep: ops, threads, lalu DE (population, generations, F, CR). Hasil ke `parameter_sweep.jsonl`. |
| **analysis** | Load log, hitung sensitivitas parameter DE terhadap RAM, tampilkan ranking di konsol. |
| **viz** | Generate semua grafik dan dashboard HTML; opsi buka browser. |
| **all** | Jalankan scenarios → sweep → analysis → viz (urutan lengkap). |

Default mode jika tidak ditulis: **all**.

### Opsi

| Opsi | Deskripsi |
|------|-----------|
| `--results-dir PATH` | Folder untuk log dan figures (default: `results`). |
| `--quick` | Tes cepat: kurangi ops, threads, dan DE population (override config). |
| `--no-browser` | Jangan buka dashboard di browser setelah `viz`. |

### Contoh

```bash
# Hanya jalankan skenario
python main.py scenarios

# Sweep parameter lalu analisis
python main.py sweep
python main.py analysis

# Generate grafik dan buka dashboard
python main.py viz

# Jalankan lengkap (scenarios + sweep + analysis + viz)
python main.py all

# Tes cepat, tanpa buka browser
python main.py all --quick --no-browser

# Simpan hasil ke folder lain
python main.py all --results-dir my_results
```

---

## 6. Output dan Hasil

### Log (JSONL)

Setiap baris satu objek JSON (satu run).

- **`results/experiment_log.jsonl`** — hasil skenario S1–S3.
- **`results/parameter_sweep.jsonl`** — hasil sweep (ops, threads, de_population, de_generations, de_F, de_CR).

Contoh field per baris:

- Identitas: `scenario_id`, `curve`, `curve_bits`, `scalar_type`, `ops`, `threads`
- Parameter DE: `de_population`, `de_generations`, `de_F`, `de_CR`
- Resource: `memory_before_mb`, `memory_after_mb`, `peak_memory_mb`, `time_sec`, `cpu_percent`, `throughput_ops_per_sec`
- Sweep (jika ada): `sweep_param`, `sweep_value`

### Grafik (PNG)

Semua di **`results/figures/`** (atau `{results_dir}/figures/`):

| File | Isi |
|------|-----|
| ram_vs_iterations.png | RAM (peak) vs jumlah operasi (ops), data DE saja. |
| ram_vs_curve_size.png | RAM vs ukuran curve (bits). |
| ram_vs_threads.png | RAM vs jumlah threads. |
| de_summary.png | Rata-rata peak memory, time, CPU (ringkasan DE). |
| sensitivity_ranking.png | Ranking parameter DE yang paling mempengaruhi RAM (impact score). |

### Dashboard Web

- **`results/figures/dashboard.html`**
- Berisi: ringkasan analisis (parameter paling mempengaruhi RAM + 5 besar ranking) dan semua grafik di atas.
- Dibuka otomatis di browser setelah `viz` (kecuali pakai `--no-browser`).
- Bisa dibuka manual dengan membuka file HTML di browser.

### Interpretasi Analisis

- **Analisis sensitivitas** hanya memakai **parameter DE** (de_population, de_generations, de_F, de_CR).
- Untuk tiap parameter: korelasi Pearson dengan `peak_memory_mb`, range RAM saat parameter divariasikan, lalu **impact score** (gabungan korelasi dan range).
- Parameter dengan **impact score tertinggi** = **paling mempengaruhi RAM** dalam eksperimen ini.

---

## 7. Referensi Modul

### ecc_engine.py

- **get_curve(curve_name)** — Mengembalikan class curve (NIST192p, dll.) dari nama.
- **scalar_multiply(curve_name, scalar, point=None)** — Satu operasi scalar multiplication; return Point.
- **run_batch_scalar_multiplication(curve_name, scalars, use_parallel, num_workers)** — Batch scalar multiplication; bisa paralel (ProcessPoolExecutor). Return list Point.
- **get_curve_order(curve_name)**, **get_curve_bit_size(curve_name)** — Order dan bit size curve.
- **\_worker_scalar_multiply(curve_name, scalar)** — Worker level modul untuk multiprocessing (picklable).

### scalar_generator.py

- **random_scalars(curve_name, count, seed)** — List scalar acak [1, n-1] (tidak dipakai di skenario).
- **de_optimized_scalars(curve_name, count, population_size, generations, F, CR, ...)** — List scalar hasil optimasi DE (objektif: minimasi Hamming weight).
- **get_scalars(curve_name, count, scalar_type, de_*, seed)** — Entry point: `scalar_type` "random" atau "de".

### resource_monitor.py

- **get_current_memory_mb()**, **get_peak_memory_mb()**, **get_cpu_percent()** — Pengukuran saat ini.
- **measure_block(use_tracemalloc)** — Context manager: ukur memory before/after, peak, time_sec, cpu_percent.
- **run_and_measure(fn, use_tracemalloc)** — Jalankan `fn()` dan return dict metrik.
- **format_metrics(metrics)** — Format numerik untuk log/JSON.

### experiment_runner.py

- **_run_one_scenario(...)** — Satu skenario: generate scalar, batch ECC, ukur resource; return dict hasil.
- **run_scenarios(scenarios, results_dir, log_file, de_overrides)** — Jalankan daftar skenario, append ke log.
- **run_parameter_sweep(curve_name, ops_list, threads_list, de_population_list, ...)** — Sweep ops, threads, lalu DE (population, generations, F, CR); append ke parameter_sweep.jsonl.

### analysis.py

- **load_log(results_dir, log_file)** — Load JSONL ke pandas DataFrame.
- **load_sweep_log(...)** — Load parameter_sweep.jsonl.
- **parameter_sensitivity_ram(df, target, param_columns)** — Hitung sensitivitas; default param_columns hanya parameter DE. Return DataFrame ranking.
- **compare_random_vs_de(df)** — Groupby scalar_type, agregasi memory/time/CPU (jika ada tipe lain).
- **summarize_scenarios(df)** — Ringkasan per scenario_id.
- **run_analysis(results_dir, ...)** — Load log, filter hanya DE, sensitivity, comparison, summary; return dict (sensitivity_ranking, parameter_most_affects_RAM, random_vs_de, scenario_summary).

### visualization.py

- **plot_ram_vs_iterations(df, curve_name, save_path)** — Grafik RAM vs ops.
- **plot_ram_vs_curve_size(df, save_path)** — Grafik RAM vs curve_bits.
- **plot_ram_vs_threads(df, curve_name, save_path)** — Grafik RAM vs threads.
- **plot_de_summary(df, save_path)** — Grafik batang rata-rata memory, time, CPU (DE).
- **plot_sensitivity_ranking(sensitivity_records, save_path)** — Bar chart ranking parameter DE.
- **generate_dashboard_html(paths, analysis_result, figures_dir, open_browser)** — Buat dashboard.html, opsi buka browser.
- **generate_all(results_dir, ..., open_browser)** — Generate semua grafik (hanya data DE), lalu dashboard; return dict path.

---

## 8. Dokumen Terkait

- **README.md** — Ringkasan singkat, instalasi, cara menjalankan, output.
- **PEMBAHASAN.md** — Pembahasan penelitian: konteks, parameter DE vs RAM, metode pengukuran, interpretasi hasil, keterbatasan, implikasi dan saran lanjutan.

Untuk pertanyaan teknis atau penyesuaian eksperimen, gunakan **config.py** dan opsi **main.py**; untuk interpretasi dan konteks penelitian, lihat **PEMBAHASAN.md**.
