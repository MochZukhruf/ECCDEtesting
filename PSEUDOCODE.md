# Pseudocode untuk Proses Utama dalam Simulasi ECC-DE

Dokumen ini berisi pseudocode untuk setiap algoritma dan proses utama yang digunakan dalam proyek ini. Pseudocode ini dibuat agar mudah dipahami secara logis tanpa terikat pada sintaks bahasa pemrograman tertentu.

---

## 1. Perhitungan Shannon Entropy (`shannon_entropy`)
Berfungsi untuk menghitung nilai entropy dari representasi bit sebuah skalar. Nilai maksimum adalah 1.0 (apabila jumlah bit 0 dan 1 seimbang, yaitu 50/50).

```text
FUNCTION shannon_entropy(k, bit_length):
    IF bit_length <= 0 THEN 
        RETURN 0.0
    
    // Ubah angka k ke representasi biner dan tambahkan padding 0 di depan
    bits = binary_string(k) padded to bit_length
    
    count_1 = jumlah kemunculan '1' dalam bits
    count_0 = jumlah kemunculan '0' dalam bits
    
    IF count_0 == 0 ATAU count_1 == 0 THEN 
        RETURN 0.0
        
    p1 = count_1 / bit_length
    p0 = count_0 / bit_length
    
    // Rumus Shannon Entropy
    RETURN -(p0 * log2(p0) + p1 * log2(p1))
```

---

## 2. Optimasi Skalar menggunakan Differential Evolution (`_de_optimize_scalar`)
Berfungsi mencari skalar secara iteratif menggunakan metode mutasi dan crossover dari Differential Evolution (DE) untuk memaksimalkan Shannon Entropy.

```text
FUNCTION de_optimize_scalar(curve_order, pop_size, generations, F, CR):
    lo = 1
    hi = curve_order - 1
    
    // Inisialisasi populasi awal secara acak
    population = array ukuran pop_size berisi angka acak antara lo dan hi
    // Objective meminimalkan negatif dari entropy (sehingga memaksimalkan entropy)
    fitness = [objective(k) for k in population] 

    FOR gen = 1 TO generations - 1:
        FOR i = 0 TO pop_size - 1:
            // Langkah 1: Mutasi
            Pilih 3 indeks secara acak (a, b, c) yang berbeda satu sama lain dan tidak sama dengan i
            mutant = population[a] + F * (population[b] - population[c])
            mutant = round_and_clip(mutant, lo, hi)

            // Langkah 2: Crossover
            IF random() < CR THEN:
                trial = mutant
            ELSE:
                trial = population[i]
            
            // Langkah 3: Seleksi
            f_trial = objective(trial)
            IF f_trial <= fitness[i]:
                population[i] = trial
                fitness[i] = f_trial

    best_index = indeks_nilai_minimum_dari(fitness)
    RETURN population[best_index]
```

---

## 3. Optimasi Skalar menggunakan GA + DE Sequential (`_ga_de_optimize_scalar`)
Menggabungkan algoritma GA (untuk fase awal/eksplorasi) dan DE (untuk fase kedua/eksploitasi).

```text
FUNCTION ga_de_optimize_scalar(curve_order, pop_size, generations, de_F, de_CR, ga_MR, ga_CR):
    lo = 1, hi = curve_order - 1
    population = array ukuran pop_size berisi angka acak antara lo dan hi
    fitness = [objective(k) for k in population]

    ga_gens = generations / 2
    de_gens = generations - ga_gens

    // ==========================================
    // Fase 1: Genetic Algorithm (GA)
    // ==========================================
    FOR gen = 1 TO ga_gens:
        new_population = []
        FOR _ = 1 TO (pop_size + 1) / 2:
            // Seleksi Turnamen
            p1 = tournament_selection(population, fitness)
            p2 = tournament_selection(population, fitness)
            
            // Crossover GA
            IF random() < ga_CR:
                alpha = random()  // antara 0.0 - 1.0
                c1 = clip(alpha * p1 + (1 - alpha) * p2, lo, hi)
                c2 = clip((1 - alpha) * p1 + alpha * p2, lo, hi)
            ELSE:
                c1 = p1
                c2 = p2
                
            // Mutasi GA
            IF random() < ga_MR: c1 = mutate_randomly(c1, lo, hi)
            IF random() < ga_MR: c2 = mutate_randomly(c2, lo, hi)
            
            new_population.add(c1)
            new_population.add(c2)
            
        population = new_population[0 .. pop_size - 1]
        fitness = [objective(k) for k in population]

    // ==========================================
    // Fase 2: Differential Evolution (DE)
    // ==========================================
    FOR gen = 1 TO de_gens:
        FOR i = 0 TO pop_size - 1:
            Pilih 3 indeks (a, b, c) yang berbeda dan != i
            mutant = clip(population[a] + de_F * (population[b] - population[c]), lo, hi)
            
            // Crossover DE
            IF random() < de_CR THEN trial = mutant ELSE trial = population[i]
            
            // Seleksi
            f_trial = objective(trial)
            IF f_trial <= fitness[i]:
                population[i] = trial
                fitness[i] = f_trial

     best_index = indeks_nilai_minimum_dari(fitness)
    RETURN population[best_index]
```

---

## 4. Entropy Guided Scalar Initialization (`eg_scalars`)
Membuat skalar yang menjamin memiliki Shannon Entropy maksimal semenjak proses pembuatan dengan cara mengatur rasio 0 dan 1 yang selalu 50/50, tanpa menggunakan DE.

```text
FUNCTION eg_scalars(curve_order, bit_length):
    lo = 1, hi = curve_order - 1
    
    // Tentukan jumlah 1 dan 0 yang seimbang 
    ones_count = bit_length // 2
    zeros_count = bit_length - ones_count
    
    WHILE TRUE:
        // Buat deretan bit sesuai jumlah
        bits = array berisi '1' sebanyak ones_count dan '0' sebanyak zeros_count
        // Acak posisinya
        shuffle(bits) 
        
        // Konversi biner ke integer
        k = integer_from_binary_string(bits)
        
        IF lo <= k <= hi:
            RETURN k
```

---

## 5. Entropy Guided + Differential Evolution (`_eg_de_optimize_scalar`)
Langkah inisialisasi populasi tidak diacak melainkan digenerate oleh `Entropy Guided Initialization` terlebih dahulu sebelum diproses dan dioptimalkan lebih lanjut oleh DE.

```text
FUNCTION eg_de_optimize_scalar(curve_order, bit_length, pop_size, generations, F, CR):
    lo = 1, hi = curve_order - 1
    ones_count = bit_length // 2
    zeros_count = bit_length - ones_count
    population = []

    // Langkah 1: Populasi Awal Menggunakan Entropy Guided Initialization
    WHILE length(population) < pop_size:
        bits = array berisi '1' sebanyak ones_count dan '0' sebanyak zeros_count
        shuffle(bits)
        k = integer_from_binary_string(bits)
        IF lo <= k <= hi:
            population.append(k)

    fitness = [objective(k) for k in population]
    best_fitness = min(fitness)
    gens_without_improvement = 0

    // Langkah 2 & 3: Refinement Menggunakan DE dengan Early Stopping Validation
    FOR gen = 1 TO generations:
        // Berhenti jika sudah hampir optimal sempurna
        IF best_fitness <= -0.999 THEN BREAK
        // Berhenti jika 10 generasi tidak ada perubahan/peningkatan fitness
        IF gens_without_improvement >= 10 THEN BREAK

        gen_improved = FALSE

        FOR i = 0 TO pop_size - 1:
            Pilih 3 indeks (a, b, c) yang berbeda dan != i
            
            diff = population[b] - population[c]
            mutant = (population[a] + F * diff) modulo curve_order
            IF mutant == 0 THEN mutant = 1
            
            IF random() < CR THEN trial = mutant ELSE trial = population[i]
            
            f_trial = objective(trial)
            
            IF f_trial <= fitness[i]:
                population[i] = trial
                fitness[i] = f_trial
                
                IF f_trial < best_fitness:
                    best_fitness = f_trial
                    gen_improved = TRUE

        // Setel pelacak improvement per generasi
        IF gen_improved == FALSE THEN:
            gens_without_improvement = gens_without_improvement + 1
        ELSE:
            gens_without_improvement = 0

    best_index = indeks_nilai_minimum_dari(fitness)
    RETURN population[best_index]
```

---

## 6. Skenario Runner Eksperimen (`_run_one_scenario`)
Proses utama dari awal hingga akhir untuk menguji seberapa efisien algoritma scalar generator yang dibuat dan mengumpulkan matrix resource usage dan performa saat diaplikasikan ke skenario Blockchain sesungguhnya.

```text
FUNCTION run_one_scenario(scenario):
    // Memulai pemantauan resource (Memory RAM dan CPU)
    START RESOURCE_MONITORING
    
    // Langkah 1: Generate scalars berdasarkan algoritma (random, de, ga_de, eg, eg_de)
    scalars = get_scalars(scenario.count, scenario.scalar_type, scenario.curve_name)
    
    // Langkah 2: Buat Kunci ECC (Keypair) dari hasil scalars (Private & Public Key)
    keypairs = []
    FOR scalar IN scalars:
        private_key, public_key = generate_key_pair_from_scalar(scalar)
        keypairs.append((private_key, public_key))
        
    // Langkah 3: Mensimulasi Pembuatan Transaksi Blockchain
    transactions = []
    addresses = [generate_address(public_key) for public_key in keypairs]
    
    FOR i = 1 TO scenario.num_transactions:
        sender_address = addresses[i % length(addresses)]
        receiver_address = addresses[(i + 1) % length(addresses)]
        amount = random_float(0.01, 100.0)
        transactions.append(Transaction(sender_address, receiver_address, amount))
        
    // Langkah 4: Tanda tangani semua transaksi (Digital Signing ECDSA)
    FOR i = 0 TO length(transactions) - 1:
        private_key = keypairs[i % length(keypairs)].private_key
        transactions[i].sign(private_key)
        
    // Langkah 5: Verifikasi Digital Signature Semua Transaksi
    verified_count = 0
    FOR tx IN transactions:
        IF tx.verify() == TRUE THEN 
            verified_count = verified_count + 1
        
    // Langkah 6: Mine blocks dalam Node
    nodes = create_nodes(scenario.num_nodes)
    FOR EACH node IN nodes:
        assign_transactions_to_node(node, transactions)
        node.mine_all_pending() // Build blockchain
        
    // Langkah 7: Pengujian Statistik (Shannon Entropy Test & Chi-Square Test)
    statistical_results = run_all_tests(scalars, curve_bit_size)
    
    STOP RESOURCE_MONITORING
    
    // Kumpulkan seluruh data metrik waktu eksekusi dan memori
    result = compile_metrics(time_spent, memory_usage, cpu_usage, statistical_results)
    
    RETURN result
```

---

## 7. Generate ECC Key Pair dari Skalar (`generate_key_pair_from_scalar`)
Mengubah bilangan skalar bulat menjadi representasi bytewise agar bisa diterapkan langsung pada operasi elliptic curve digital signature.

```text
FUNCTION generate_key_pair_from_scalar(curve_name, scalar):
    curve = get_curve(curve_name)
    order = curve.order
    
    // Memastikan skalar tidak di luar batas order dari curve
    scalar = scalar modulo order
    IF scalar == 0 THEN scalar = 1
    
    // Ubah angka skalar bulat menjadi rentetan bytes sesuai panjang bit curve (misal: 256 bits = 32 bytes)
    scalar_bytes = int_to_bytes(scalar, byte_range = curve.baselen, byteorder = "big")
    
    // Mengubah scalar_bytes tadi menjadi kunci privat ECDSA
    private_key = import_private_key_from_string(scalar_bytes, curve)
    
    // Dapatkan public key
    public_key = private_key.get_verifying_key()
    
    RETURN private_key, public_key
```
