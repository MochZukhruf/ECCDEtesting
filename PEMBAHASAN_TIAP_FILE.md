# Pembahasan Tiap File dalam Percobaan ECC + DE

Dokumen ini memuat pembahasan (penjelasan peran, isi, dan alur) **setiap file** yang terlibat dalam percobaan resource ECC + Differential Evolution.

---

## Daftar Isi

1. [config.py](#1-configpy)
2. [ecc_engine.py](#2-ecc_enginepy)
3. [scalar_generator.py](#3-scalar_generatorpy)
4. [resource_monitor.py](#4-resource_monitorpy)
5. [experiment_runner.py](#5-experiment_runnerpy)
6. [analysis.py](#6-analysispy)
7. [visualization.py](#7-visualizationpy)
8. [main.py](#8-mainpy)
9. [File output (log dan figures)](#9-file-output-log-dan-figures)

---

## 1. config.py

**Peran:** Menyimpan semua konfigurasi yang dipakai oleh skenario dan parameter sweep. Satu sumber kebenaran untuk curve, skenario, parameter DE, dan path output.

**Isi utama:**

- **CURVES** — Mapping nama curve (secp192r1, secp224r1, secp256r1, secp384r1, secp521r1) ke class kurva di library `ecdsa` (NIST192p–NIST521p). Dipakai oleh `ecc_engine` untuk memilih kurva.
- **SCENARIOS** — Daftar skenario tetap. Tiap skenario punya: `id`, `curve`, `scalar_type` (hanya "de" di percobaan ini), `ops`, `threads`. Contoh: S1 (secp192r1, 100 ops, 1 thread), S2 (secp256r1, 1000 ops, 4 threads), S3 (secp521r1, 5000 ops, 8 threads).
- **DE_PARAMS** — Nilai-nilai yang divariasikan saat parameter sweep: `population_size` [50, 100, 200], `generations` [10, 30, 50], `F` [0.5, 0.8, 1.0], `CR` [0.3, 0.7, 0.9].
- **DE_DEFAULT** — Nilai default DE jika tidak di-sweep: population 100, generations 30, F 0.8, CR 0.7.
- **BATCH_SIZES** dan **THREAD_COUNTS** — Daftar nilai untuk sweep “ops” dan “threads”.
- **RESULTS_DIR**, **LOG_FILE** — Folder hasil dan nama file log.

**Pembahasan:** Tanpa mengubah kode di tempat lain, peneliti bisa mengubah skenario, rentang DE, atau ukuran batch hanya dengan mengedit `config.py`. File ini menjadi jangkar desain eksperimen.

---

## 2. ecc_engine.py

**Peran:** Modul inti kriptografi — mengimplementasikan operasi **scalar multiplication** pada kurva eliptik NIST dan mendukung **batch** serta **paralel** untuk keperluan pengukuran resource.

**Isi utama:**

- **_CURVE_MAP** — Mapping nama curve ke class kurva (NIST192p–NIST521p) dari library `ecdsa`.
- **get_curve(curve_name)** — Mengembalikan class kurva dari nama; dipanggil oleh semua fungsi yang butuh kurva.
- **scalar_multiply(curve_name, scalar, point=None)** — Satu operasi scalar × generator (atau × point). Scalar dinormalisasi ke [1, n-1]. Return objek `Point`.
- **generate_key_pair(curve_name, entropy)** — Membangkitkan pasangan kunci ECDSA (opsional; tidak dipakai di alur utama percobaan).
- **run_batch_scalar_multiplication(curve_name, scalars, use_parallel, num_workers)** — Menjalankan banyak scalar multiplication. Jika `use_parallel=True` dan `num_workers > 1`, memakai `ProcessPoolExecutor`; setiap tugas memanggil **\_worker_scalar_multiply**.
- **_worker_scalar_multiply(curve_name, scalar)** — Fungsi level modul yang menerima nama kurva dan satu scalar, mengembalikan satu `Point`. Sengaja didefinisikan di level modul agar bisa di-pickle oleh multiprocessing (fungsi lokal tidak bisa di-pickle).
- **get_curve_order(curve_name)**, **get_curve_bit_size(curve_name)** — Helper untuk order kurva dan ukuran bit (192, 224, 256, 384, 521).

**Pembahasan:** Semua beban ECC (dan sebagian besar konsumsi RAM saat fase ECC) berasal dari sini. Batch besar dan paralel sengaja didukung agar percobaan bisa “stress” memori dan mengukur dampaknya. Ketergantungan hanya pada library `ecdsa`; tidak ada implementasi kurva custom.

---

## 3. scalar_generator.py

**Peran:** Membangkitkan scalar yang akan dipakai di ECC. Dalam percobaan ini hanya scalar **DE-optimized** yang dipakai; generator **random** tetap ada di kode untuk keperluan lain atau pengembangan.

**Isi utama:**

- **random_scalars(curve_name, count, seed)** — Menghasilkan list scalar acak dalam [1, n-1] dengan `random.randrange`. Tidak dipakai di skenario saat ini.
- **hamming_weight(k)** — Jumlah bit 1 pada representasi biner `k`. Dipakai sebagai fungsi objektif DE (minimasi).
- **_de_optimize_scalar(...)** — Implementasi inti Differential Evolution untuk **satu** scalar: populasi integer dalam [1, n-1], mutasi (mutant = pop[a] + F*(pop[b]-pop[c])), crossover dengan probabilitas CR, seleksi greedy. Mengembalikan satu scalar yang meminimalkan `objective` (default: Hamming weight).
- **de_optimized_scalars(curve_name, count, population_size, generations, F, CR, ...)** — Memanggil `_de_optimize_scalar` sebanyak `count` kali (dengan seed berbeda per indeks) sehingga dihasilkan list scalar hasil DE.
- **get_scalars(curve_name, count, scalar_type, de_*, seed)** — Satu entry point: jika `scalar_type == "random"` memanggil `random_scalars`, jika `"de"` memanggil `de_optimized_scalars`. Parameter `de_population`, `de_generations`, `de_F`, `de_CR` diteruskan ke DE.

**Pembahasan:** Parameter DE (population, generations, F, CR) secara langsung mempengaruhi waktu dan memori di modul ini: populasi besar menyimpan lebih banyak integer dan melakukan lebih banyak evaluasi fitness. Oleh karena itu modul ini menjadi sumber variasi resource yang kemudian dianalisis di `analysis.py`.

---

## 4. resource_monitor.py

**Peran:** Mengukur penggunaan resource (RAM, CPU, waktu) dari proses yang menjalankan eksperimen. Menyediakan context manager dan fungsi pembantu agar blok kode (termasuk pemanggilan generator scalar + ECC) bisa diukur dengan konsisten.

**Isi utama:**

- **get_current_memory_mb()** — RAM proses saat ini (RSS) dalam MB. Menggunakan `psutil.Process().memory_info().rss` jika tersedia; fallback ke `tracemalloc.get_traced_memory()`.
- **get_peak_memory_mb()** — Peak memory. Jika `tracemalloc` sedang aktif, peak dari tracemalloc; jika tidak, fallback ke RSS saat ini (psutil tidak menyediakan peak per proses secara built-in).
- **get_cpu_percent()** — Persentase CPU proses (interval 0.1 s) via psutil.
- **measure_block(use_tracemalloc)** — Context manager. Sebelum blok: optional `tracemalloc.start()`, catat memory sebelum, waktu mulai. Setelah blok: waktu selesai, memory setelah, peak dari tracemalloc (jika dipakai), CPU. Nilai ditulis ke dict yang di-yield (memory_before_mb, memory_after_mb, peak_memory_mb, time_sec, cpu_percent).
- **run_and_measure(fn, use_tracemalloc)** — Menjalankan `fn()` di dalam `measure_block` dan mengembalikan dict metrik. Dipakai oleh `experiment_runner` untuk mengukur satu skenario penuh (generate scalar + batch ECC).
- **format_metrics(metrics)** — Membulatkan nilai metrik untuk penyimpanan log/JSON (4 desimal untuk memory/time, 2 untuk CPU).

**Pembahasan:** Pengukuran dilakukan pada **proses yang sama** yang menjalankan DE dan ECC; sehingga peak memory mencerminkan total footprint (scalar generator + ECC + overhead). Untuk run paralel (threads > 1), proses utama yang diukur; proses worker bisa memakai RAM tambahan yang tidak tercermin penuh di RSS proses utama.

---

## 5. experiment_runner.py

**Peran:** Menjalankan **skenario** (S1–S3) dan **parameter sweep** (ops, threads, lalu empat parameter DE), menulis setiap hasil ke log JSONL, dan mengembalikan daftar hasil untuk keperluan analisis/visualisasi.

**Isi utama:**

- **_run_one_scenario(...)** — Untuk satu konfigurasi: (1) Di dalam closure `do_work()`: panggil `get_scalars` (sesuai curve, ops, scalar_type, parameter DE), lalu `run_batch_scalar_multiplication` dengan opsi paralel jika threads > 1. (2) Panggil `run_and_measure(do_work)` untuk mendapatkan metrik. (3) Bangun dict keluaran berisi scenario_id, curve, curve_bits, scalar_type, ops, threads, semua parameter DE, metrik (format_metrics), dan throughput_ops_per_sec. Return dict tersebut.
- **run_scenarios(scenarios, results_dir, log_file, de_overrides)** — Iterasi tiap skenario dari config (atau daftar yang diberikan), panggil `_run_one_scenario` dengan parameter DE dari DE_DEFAULT + overrides, append hasil ke `experiment_log.jsonl`, kumpulkan daftar hasil. Jika terjadi error, catat error ke daftar dan log.
- **run_parameter_sweep(...)** — (1) Sweep **ops**: untuk tiap nilai ops, satu run dengan scalar_type "de", threads=1; tulis ke `parameter_sweep.jsonl` dengan sweep_param "ops", sweep_value = ops. (2) Sweep **threads**: untuk tiap nilai threads, satu run dengan ops=500, scalar_type "de"; sweep_param "threads". (3) Sweep **de_population**: untuk tiap nilai population, satu run DE dengan ops=100, threads=1; sweep_param "de_population". (4) Sweep **de_generations**, **de_F**, **de_CR** dengan cara serupa (satu parameter divariasikan, lainnya pakai default). Semua run DE saja.

**Pembahasan:** Runner adalah “orkestrator” yang menyatukan config, scalar_generator, ecc_engine, dan resource_monitor. Log JSONL yang dihasilkan menjadi input bagi `analysis.py` dan `visualization.py`. Desain sweep memastikan tiap parameter DE divariasikan secara terpisah sehingga analisis sensitivitas bisa mengaitkan perubahan RAM dengan parameter tertentu.

---

## 6. analysis.py

**Peran:** Memuat log hasil percobaan, memfilter hanya data DE, lalu menghitung **sensitivitas parameter DE terhadap RAM** (ranking parameter yang paling mempengaruhi RAM) serta ringkasan lain (perbandingan per scalar_type jika ada, ringkasan per skenario).

**Isi utama:**

- **load_log(results_dir, log_file)** — Membaca file JSONL baris per baris, parse JSON tiap baris, kumpulkan ke list, return pandas DataFrame. Jika file tidak ada atau kosong, return DataFrame kosong.
- **load_sweep_log(...)** — Memanggil load_log untuk `parameter_sweep.jsonl`.
- **parameter_sensitivity_ram(df, target, param_columns)** — Target default: `peak_memory_mb`. Parameter yang dianalisis default hanya DE: de_population, de_generations, de_F, de_CR. Untuk tiap kolom parameter: hitung korelasi Pearson dengan target, hitung range (max−min) RAM ketika parameter itu divariasikan (groupby parameter). Gabungkan ke impact score (0.5×|korelasi| + 0.5×normalisasi range), urutkan menurun. Return DataFrame ranking.
- **compare_random_vs_de(df)** — Groupby `scalar_type`, agregasi mean/std/min/max untuk peak_memory_mb, time_sec, cpu_percent. Berguna jika nanti ada lagi tipe scalar selain DE.
- **summarize_scenarios(df)** — Groupby scenario_id, agregasi peak_memory_mb, time_sec, curve, scalar_type, ops, threads. Ringkasan per skenario.
- **run_analysis(results_dir, scenario_log, sweep_log)** — (1) Load scenario log dan sweep log; gabungan dipakai sebagai df. (2) Filter hanya baris dengan scalar_type == "de". (3) Panggil parameter_sensitivity_ram dengan param_columns hanya parameter DE; dapat ranking. (4) Bandingkan scalar_type (compare_random_vs_de), ringkasan skenario (hanya dari data DE). (5) Return dict: sensitivity_ranking, parameter_most_affects_RAM (elemen pertama ranking), random_vs_de, scenario_summary.

**Pembahasan:** Fokus analisis sengaja hanya pada **parameter DE** agar menjawab pertanyaan “parameter DE mana yang paling mempengaruhi RAM”. Korelasi dan range RAM bersama-sama membentuk impact score sehingga parameter yang benar-benar menggerakkan RAM (baik korelasi kuat maupun range besar) mendapat peringkat tinggi.

---

## 7. visualization.py

**Peran:** Membaca data dari log (via `analysis.load_log` / `load_sweep_log`), memfilter hanya data DE, lalu menghasilkan **grafik PNG** dan **dashboard HTML** yang menampilkan semua grafik serta ringkasan analisis.

**Isi utama:**

- **FIGURE_LABELS** — Mapping nama grafik ke judul Bahasa Indonesia (RAM vs Iterations, RAM vs Curve Size, RAM vs Threads, DE Summary, Parameter DE yang Paling Mempengaruhi RAM).
- **_ensure_fig_dir()** — Membuat folder figures jika belum ada.
- **plot_ram_vs_iterations(df, curve_name, save_path)** — Filter df menurut curve (jika ada kolom curve), plot peak_memory_mb vs ops per scalar_type (label "DE" untuk tipe de). Simpan PNG.
- **plot_ram_vs_curve_size(df, save_path)** — Plot rata-rata peak_memory_mb per curve_bits, per tipe scalar (hanya DE jika data sudah difilter).
- **plot_ram_vs_threads(df, curve_name, save_path)** — Plot rata-rata peak_memory_mb per threads.
- **plot_de_summary(df, save_path)** — Rata-rata peak_memory_mb, time_sec, cpu_percent dari seluruh df; tampilkan sebagai bar chart (de_summary.png).
- **plot_sensitivity_ranking(sensitivity_records, save_path)** — Bar chart horizontal: parameter vs impact score (sensitivity_ranking.png).
- **generate_dashboard_html(paths, analysis_result, figures_dir, open_browser)** — Menulis file HTML yang berisi: judul, ringkasan analisis (parameter paling mempengaruhi RAM + 5 besar ranking), dan kartu-kartu berisi gambar tiap grafik (src = nama file PNG). Opsi buka file di browser default.
- **generate_all(results_dir, ..., open_browser)** — Load log scenario dan sweep; gabung; filter hanya baris scalar_type == "de". Generate semua plot di atas, panggil run_analysis untuk dapat ranking, generate sensitivity_ranking plot, lalu generate_dashboard_html. Return dict nama grafik → path file; jika dashboard dibuat, tambah key "dashboard".

**Pembahasan:** Visualisasi sengaja hanya memakai data DE (filter di generate_all) agar grafik dan dashboard konsisten dengan fokus percobaan. Dashboard memudahkan peneliti melihat ringkasan dan semua grafik dalam satu halaman.

---

## 8. main.py

**Peran:** **Entry point** satu-satunya untuk menjalankan percobaan. Menerjemahkan argumen baris perintah (mode dan opsi) menjadi pemanggilan modul yang sesuai (experiment_runner, analysis, visualization).

**Isi utama:**

- **main()** — (1) Parse argumen: mode (scenarios | sweep | analysis | viz | all), --results-dir, --quick, --no-browser. (2) Jika --quick: override config (SCENARIOS, BATCH_SIZES, THREAD_COUNTS, DE_PARAMS population) untuk run lebih cepat. (3) Jika mode scenarios atau all: panggil run_scenarios. (4) Jika mode sweep atau all: panggil run_parameter_sweep. (5) Jika mode analysis atau all: panggil run_analysis, cetak parameter_most_affects_RAM dan lima besar sensitivity ranking. (6) Jika mode viz atau all: panggil generate_all (dengan open_browser jika tidak --no-browser), cetak path tiap grafik dan path dashboard. Return 0.
- **if __name__ == "__main__": sys.exit(main())** — Menjalankan main dan mengembalikan kode keluar ke shell.

**Pembahasan:** Semua alur percobaan (skenario → sweep → analisis → visualisasi) bisa dijalankan dari satu perintah; mode terpisah memungkinkan menjalankan hanya bagian yang diperlukan (misalnya hanya viz setelah log sudah ada). Opsi --quick dan --no-browser memudahkan pengujian dan lingkungan tanpa GUI.

---

## 9. File output (log dan figures)

**Peran:** Menyimpan hasil percobaan dan analisis agar bisa direproduksi, diolah ulang, atau dilaporkan.

### Log (JSONL)

- **results/experiment_log.jsonl** — Satu baris per run skenario (S1, S2, S3). Setiap baris: scenario_id, curve, curve_bits, scalar_type, ops, threads, de_*, memory_before_mb, memory_after_mb, peak_memory_mb, time_sec, cpu_percent, throughput_ops_per_sec.
- **results/parameter_sweep.jsonl** — Satu baris per run sweep. Field tambahan: sweep_param (ops | threads | de_population | de_generations | de_F | de_CR), sweep_value (nilai parameter yang divariasikan).

**Pembahasan:** Format JSONL memudahkan append tanpa memuat seluruh file; setiap baris independen sehingga bisa diparsing baris per baris. analysis.py dan visualization.py membaca file ini sebagai sumber data.

### Grafik (PNG)

- **results/figures/ram_vs_iterations.png** — RAM (sumbu Y) vs jumlah operasi (sumbu X); data DE.
- **results/figures/ram_vs_curve_size.png** — RAM vs ukuran curve (bits).
- **results/figures/ram_vs_threads.png** — RAM vs jumlah threads.
- **results/figures/de_summary.png** — Rata-rata peak memory, time, CPU (batang).
- **results/figures/sensitivity_ranking.png** — Ranking parameter DE menurut impact score (parameter mana paling mempengaruhi RAM).

**Pembahasan:** Grafik dihasilkan oleh visualization.py dari data log (setelah filter DE). Dipakai untuk laporan dan presentasi.

### Dashboard

- **results/figures/dashboard.html** — Halaman HTML yang memuat: judul, blok “Ringkasan Analisis” (parameter paling mempengaruhi RAM + 5 besar ranking), lalu semua grafik di atas dalam kartu. Gambar dirujuk dengan path relatif (nama file PNG). Bisa dibuka di browser untuk melihat seluruh hasil dalam satu halaman.

**Pembahasan:** Dashboard menggabungkan keluaran analisis (run_analysis) dan semua grafik (generate_all) sehingga peneliti tidak perlu membuka banyak file terpisah.

---

## Ringkasan Alur Antar-File

1. **config.py** → dibaca **experiment_runner** (skenario, DE_DEFAULT, DE_PARAMS, BATCH_SIZES, THREAD_COUNTS) dan **main** (RESULTS_DIR; main juga meng-override config saat --quick).
2. **experiment_runner** memanggil **scalar_generator.get_scalars** (untuk scalar DE), **ecc_engine.run_batch_scalar_multiplication**, dan **resource_monitor.run_and_measure**; menulis ke **results/*.jsonl**.
3. **analysis** membaca **results/*.jsonl**, memfilter DE, memanggil **parameter_sensitivity_ram**; hasil dipakai **visualization** (ranking) dan **main** (cetak ke konsol).
4. **visualization** membaca log (via analysis.load_log / load_sweep_log), memfilter DE, membuat grafik dan **results/figures/dashboard.html**.
5. **main** mengoordinasikan urutan: scenarios → sweep → analysis → viz (sesuai mode).

Dengan pembahasan per file di atas, setiap bagian percobaan dapat dilacak dari konfigurasi, eksekusi, pengukuran, analisis, hingga tampilan hasil.
