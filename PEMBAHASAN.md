# Pembahasan — ECC + Differential Evolution: Dampak Parameter DE terhadap Konsumsi RAM

## 1. Konteks dan Tujuan Pembahasan

Penelitian ini memadukan **Elliptic Curve Cryptography (ECC)** dengan **Differential Evolution (DE)** untuk menghasilkan scalar yang dioptimasi (misalnya dengan Hamming weight rendah), lalu mengukur **konsumsi resource—khususnya RAM**—saat operasi ECC dijalankan dengan scalar tersebut. Pembahasan ini menjawab: **(1)** mengapa parameter DE dan konfigurasi eksperimen relevan untuk RAM, **(2)** bagaimana hasil pengukuran dan analisis sensitivitas diinterpretasikan, **(3)** keterbatasan metode, dan **(4)** implikasi untuk penelitian lanjutan.

---

## 2. Peran Scalar dan Differential Evolution dalam ECC

Di ECC, **scalar multiplication** (perkalian skalar titik pada kurva eliptik) adalah operasi inti. Scalar yang dipakai (bilangan bulat dalam rentang order kurva) menentukan keamanan dan, dalam konteks tertentu, efisiensi komputasi. **Differential Evolution** digunakan sebagai algoritma optimasi untuk mencari scalar yang memenuhi kriteria tertentu—dalam sistem ini, **minimasi Hamming weight** (jumlah bit 1 dalam representasi biner). Scalar dengan Hamming weight rendah dapat mengurangi jumlah operasi penjumlahan titik dalam implementasi tertentu (misalnya metode binary/NAF), sehingga DE di sini berperan sebagai **pembangkit scalar “optimized”** yang kemudian dijalankan pada mesin ECC.

Yang menjadi fokus bukan hanya kecepatan komputasi ECC, melainkan **resource yang dipakai oleh proses secara keseluruhan**, termasuk tahap **pembangkit scalar dengan DE** dan tahap **eksekusi ECC**. Dengan demikian, pertanyaan penelitian difokuskan pada: **parameter DE mana yang paling mempengaruhi konsumsi RAM** dalam pipeline ECC+DE ini.

---

## 3. Parameter DE dan Dampaknya terhadap Resource (RAM)

Parameter DE yang divariasikan adalah: **de_population**, **de_generations**, **de_F**, dan **de_CR**. Pembahasan masing-masing dalam kaitannya dengan RAM:

- **de_population (ukuran populasi)**  
  Populasi DE adalah himpunan sejumlah “individu” (calon solusi/scalar). Setiap individu menyimpan satu nilai scalar (dan mungkin nilai fitness). Semakin besar populasi, semakin banyak vektor solusi yang disimpan dan diproses per generasi, sehingga **alokasi memori untuk menyimpan populasi dan struktur data pendukung (misalnya fitness) meningkat**. Selain itu, operasi mutasi dan crossover mengakses banyak elemen populasi, sehingga cache dan penggunaan memori kerja juga terdampak. **Dampak terhadap RAM diharapkan paling nyata** dibanding parameter DE lainnya.

- **de_generations (jumlah generasi)**  
  Generasi menambah **lama waktu eksekusi** dan jumlah evaluasi fungsi objektif (Hamming weight), tetapi **ukuran struktur data per generasi relatif tetap** (populasi diganti in-place atau dengan struktur berukuran sama). Dengan demikian, **pengaruh de_generations terhadap peak RAM lebih kecil** daripada de_population; yang lebih berubah adalah waktu dan penggunaan CPU kumulatif.

- **de_F (faktor diferensial)**  
  F mengontrol skala vektor mutasi. Perubahan F mengubah **perilaku pencarian** (eksplorasi vs eksploitasi), bukan **jumlah atau ukuran struktur data** yang dialokasikan. Oleh karena itu **pengaruh de_F terhadap RAM diharapkan kecil**.

- **de_CR (crossover rate)**  
  CR mengatur probabilitas penggunaan komponen dari vektor mutan. Sama seperti F, CR hanya mempengaruhi **logika algoritma**, bukan ukuran populasi atau struktur data. **Pengaruh de_CR terhadap RAM juga diharapkan kecil**.

Dengan demikian, secara teoretis **de_population** adalah kandidat terkuat sebagai parameter yang paling mempengaruhi RAM; **de_generations** berdampak terutama pada waktu/CPU; **de_F** dan **de_CR** lebih ke kualitas solusi daripada konsumsi memori.

---

## 4. Metode Pengukuran dan Analisis Sensitivitas

- **Pengukuran RAM**  
  RAM diukur dengan **tracemalloc** (Python) dan **psutil** (RSS proses). Yang diukur adalah **proses yang menjalankan eksperimen** (termasuk pembangkitan scalar DE dan batch ECC). Metrik yang dicatat: memori sebelum/sesudah, **peak memory**, waktu eksekusi, dan persentase CPU. Dengan demikian, yang terlihat adalah **total footprint proses**, bukan hanya modul ECC atau hanya modul DE.

- **Analisis sensitivitas**  
  Analisis hanya memakai **parameter DE** (de_population, de_generations, de_F, de_CR). Untuk tiap parameter dihitung:
  - **Korelasi (Pearson)** dengan **peak_memory_mb**: seberapa kuat hubungan linier antara nilai parameter dan RAM.
  - **Range RAM** ketika parameter divariasikan (selisih max–min RAM untuk nilai-nilai parameter tersebut).
  - **Impact score**: kombinasi (misalnya 0.5×|korelasi| + 0.5×normalisasi range) untuk meranking parameter.  
  Parameter dengan **impact score tertinggi** dianggap **paling mempengaruhi RAM**. Grafik **sensitivity_ranking** dan ringkasan di dashboard menampilkan ranking ini.

Interpretasi: parameter dengan **korelasi tinggi (positif/negatif)** dan **range RAM besar** saat divariasikan akan mendapat skor tinggi; parameter yang nilainya hampir tidak mengubah RAM (korelasi mendekati 0, range kecil) akan mendapat skor rendah.

---

## 5. Interpretasi Hasil dan Skenario yang Mungkin

- **Jika de_population menduduki peringkat teratas**  
  Konsisten dengan argumen di atas: ukuran populasi langsung menentukan banyaknya solusi yang disimpan dan diproses, sehingga peningkatan RAM ketika population dinaikkan (misalnya 50 → 100 → 200) wajar. Implikasi: untuk lingkungan dengan batasan RAM ketat, membatasi **de_population** lebih efektif daripada hanya menurunkan de_generations atau mengubah F/CR.

- **Jika de_generations juga tampak berpengaruh**  
  Bisa terjadi jika implementasi menyimpan riwayat generasi atau objek tambahan per generasi; atau jika pengukuran menangkap efek samping (misalnya fragmentasi memori setelah banyak iterasi). Pembahasan dapat menyebutkan bahwa pengaruh de_generations terhadap **waktu** lebih langsung daripada terhadap **peak RAM**, dan bahwa hasil eksperimen menunjukkan sejauh mana hal itu terlihat di lingkungan pengukuran Anda.

- **Jika de_F atau de_CR tampak berpengaruh kecil**  
  Sesuai harapan: keduanya tidak mengubah ukuran struktur data. Jika dalam data mereka tetap memiliki korelasi atau range tidak nol, itu bisa disebabkan variasi sampel, konfounding (parameter lain ikut berubah dalam sweep), atau efek tidak langsung yang kecil.

- **Peran skenario (curve, ops, threads)**  
  Meskipun analisis sensitivitas **hanya memakai parameter DE**, skenario tetap memvariasikan curve (192–521 bit), jumlah operasi (ops), dan threads. Grafik **RAM vs iterations**, **RAM vs curve size**, dan **RAM vs threads** memberikan konteks: dalam kondisi DE mana (population, dll.) dan beban ECC mana (ops, curve, paralelisme) konsumsi RAM menjadi tinggi. Pembahasan dapat menyatakan bahwa **parameter DE yang paling mempengaruhi RAM** diidentifikasi dengan mengontrol konteks ECC tersebut (curve, ops, threads) melalui desain skenario dan sweep.

---

## 6. Keterbatasan Metode

- **Lingkungan pengukuran**  
  Pengukuran dilakukan pada **satu proses** (tracemalloc/psutil). Untuk run dengan **threads > 1**, yang diukur adalah proses utama; proses anak (worker) mungkin memakai RAM tambahan yang tidak sepenuhnya tercermin pada RSS proses induk. Untuk interpretasi ketat pengaruh “threads” terhadap RAM, perlu dipertimbangkan pengukuran sistem (total RAM) atau pengukuran per proses.

- **Implementasi DE dan ECC**  
  Hasil bergantung pada implementasi konkret: bagaimana populasi DE disimpan (list, array), apakah ada salinan tambahan, dan bagaimana ECC (library ecdsa) mengalokasikan memori. Perubahan implementasi atau versi library dapat menggeser ranking parameter.

- **Sensitivity hanya parameter DE**  
  Ops, threads, dan curve sengaja tidak dimasukkan ke dalam ranking sensitivitas agar fokus pada **parameter DE**. Pembahasan dapat menegaskan bahwa kesimpulan “parameter DE mana yang paling mempengaruhi RAM” dibatasi pada keempat parameter DE dan pada desain eksperimen saat ini.

- **Data dan reproduktibilitas**  
  Hasil sensitivitas bergantung pada rentang nilai yang di-sweep dan banyaknya run. Seed dan jumlah repetisi per konfigurasi dapat mempengaruhi kestabilan korelasi dan range; pembahasan dapat merekomendasikan beberapa run atau seed untuk hasil yang lebih andal.

---

## 7. Implikasi dan Saran Penelitian Lanjutan

- **Implikasi**  
  Sistem ini menunjukkan bahwa **bukan hanya kecepatan atau kualitas scalar** yang relevan ketika DE dipadukan dengan ECC, tetapi juga **konsumsi RAM**. Parameter **de_population** secara teoretis dan (bila terlihat dalam hasil) secara empiris menjadi pengungkit utama; pengaturan DE (terutama population) dapat dipertimbangkan dalam desain sistem yang berjalan di lingkungan terbatas memori.

- **Saran lanjutan**  
  - Menambah repetisi dan seed untuk tiap konfigurasi agar ranking sensitivitas lebih stabil.  
  - Memisahkan pengukuran RAM untuk fase “hanya DE” (generate scalar) dan fase “hanya ECC” (scalar multiplication) untuk mengurai kontribusi masing-masing.  
  - Memperluas ke curve dan ukuran populasi lain, serta membandingkan dengan scalar acak (random) secara eksplisit dari sisi RAM, jika ingin menonjolkan novelty “resource usage DE vs non-DE” dalam konteks ECC.
