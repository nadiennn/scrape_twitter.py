# Scraping Tweet Isu Makan Bergizi Gratis (MBG)

Repositori ini berisi dataset, script scraping, dan dokumentasi untuk tugas analisis media sosial.
Data diambil dari platform X (Twitter) dengan topik **Program Makan Bergizi Gratis (MBG)**.

> Anggota kelompok 
 Nama: **Nadien Bija Manurun**
 **Muhammad ariel**
  **Annisa Nur Imani**, 
  **Nur Ain Hammad**
> Mata kuliah: **[Media Sosial Analisis**

---

## 1. Struktur Repositori

```
.
├── data/
│   ├── data_mbg.csv            # data mentah hasil scraping (sebelum disaring)
│   └── data_mbg_final.csv      # data final yang sudah disaring relevansinya (>= 1000 baris)
├── apify_mbg.py                # script scraping utama
├── ringkasan_data.py           # script untuk menghitung statistik dasar dataset
├── config.example.py           # contoh file konfigurasi token (isi sendiri, jangan di-upload)
├── requirements.txt            # daftar library Python
├── .gitignore                  # mencegah config.py (token) ikut ter-upload
└── README.md                   # dokumentasi ini
```

## 2. Latar Belakang Isu

MBG adalah program pemerintah yang banyak dibicarakan publik di media sosial, mulai dari menu,
kualitas makanan, kasus keracunan, hingga anggarannya. Karena topiknya luas dan terus dibahas,
X (Twitter) dipilih sebagai sumber data untuk melihat opini dan percakapan warganet.

## 3. Deskripsi Data

| Kolom | Penjelasan |
|---|---|
| `tweet_id` | ID unik tweet (dipakai untuk membuang duplikat) |
| `text` / `full_text` | Isi tweet |
| `author_handle` | Username penulis (dihapus jika `ANONIMKAN = True`) |
| `author_name` | Nama tampilan penulis (dihapus jika `ANONIMKAN = True`) |
| `author_followers` | Jumlah followers penulis (dihapus jika `ANONIMKAN = True`) |
| `created_at` | Waktu tweet dibuat |
| `like_count` | Jumlah like |
| `retweet_count` | Jumlah retweet |
| `reply_count` | Jumlah balasan |
| `quote_count` | Jumlah quote |
| `view_count` | Jumlah tayangan |
| `lang` | Kode bahasa tweet |
| `url` | Link tweet asli |
| `source_actor` | Nama actor Apify yang dipakai mengambil data |

Ringkasan dataset (isi dengan hasil `python ringkasan_data.py`):

- Jumlah baris data final: **[ISI]**
- Rentang tanggal tweet: **[ISI] s.d. [ISI]**
- Tanggal pengambilan data: **[ISI]**

## 4. Penjelasan Script Scraping (`apify_mbg.py`)

Script memakai **Apify API** dengan actor `xquik/x-tweet-scraper`. Apify dipilih karena scraping
dilakukan dari server mereka, sehingga tidak perlu login akun X dan tidak mudah terkena blokir IP.

Alur kerja script:

1. **Membaca token** dari `config.py` (atau environment variable `APIFY_TOKEN`).
2. **Memuat data lama** dari `data_mbg.csv` bila ada, sehingga script aman dijalankan berulang
   tanpa menghapus data sebelumnya.
3. **Tahap 1, scraping per kata kunci.** Tiap kata kunci (misalnya `MBG`, `makan bergizi gratis`,
   `keracunan MBG`, `anggaran MBG`) dijalankan sebagai satu run dengan maksimum 300 tweet.
   Filter `lang:id` membatasi ke bahasa Indonesia dan `-filter:nativeretweets` membuang retweet murni.
4. **Tahap 2, scraping per rentang tanggal.** Jika data relevan belum cukup, script memecah
   pencarian per 3 hari (`since:` dan `until:`) dari `START_DATE` sampai `END_DATE`
   agar mendapat tweet yang lebih beragam waktunya.
5. **Normalisasi.** Setiap tweet diubah ke format kolom yang seragam (lihat tabel di atas).
6. **Pembuangan duplikat** berdasarkan `tweet_id`.
7. **Penyaringan relevansi.** Hanya tweet yang memuat kata `MBG`, `makan bergizi gratis`,
   `badan gizi nasional`, atau `SPPG` (regex `RELEVAN`) yang masuk ke file final.
8. **Penghentian otomatis** ketika data relevan mencapai `STOP_AT = 1050`, sebagai cadangan
   agar tetap di atas target 1000 baris setelah pembersihan.

Parameter penting yang bisa diubah di bagian atas script:

| Parameter | Fungsi |
|---|---|
| `QUERIES` | Daftar kata kunci tahap 1 |
| `MAX_PER_RUN` | Batas tweet per run |
| `START_DATE`, `END_DATE`, `WINDOW_DAYS` | Rentang dan ukuran jendela tanggal tahap 2 |
| `TARGET`, `STOP_AT` | Target jumlah data dan batas berhenti |
| `ANONIMKAN` | `True` untuk menghapus kolom identitas penulis di file final |

## 5. Cara Menjalankan

1. Install library:
   ```
   pip install -r requirements.txt
   ```
2. Buat akun Apify (https://apify.com) dan salin Personal API token dari
   https://console.apify.com/settings/integrations.
3. Salin `config.example.py` menjadi `config.py`, lalu isi token:
   ```python
   APIFY_TOKEN = "token_kamu"
   ```
4. Jalankan scraping:
   ```
   python apify_mbg.py
   ```
5. (Opsional) Hitung statistik dataset:
   ```
   python ringkasan_data.py
   ```

Catatan: setiap run memakai kredit Apify. Pantau saldo sebelum menjalankan.

## 6. Etika dan Keterbatasan

- Data yang diambil hanya **tweet publik**. Penggunaan data ditujukan untuk keperluan akademik.
- Scraping dapat melanggar ketentuan layanan platform dan data pribadi dilindungi UU PDP,
  sehingga identitas penulis sebaiknya dianonimkan saat dilaporkan (aktifkan `ANONIMKAN = True`).
- Token API bersifat rahasia dan **tidak boleh** di-upload ke GitHub.
- Hasil scraping bergantung pada pihak ketiga (actor Apify) sehingga format output bisa berubah.
- Pengambilan memakai urutan "Latest" dan kata kunci tertentu, jadi data adalah **sampel**
  percakapan, bukan seluruh tweet tentang MBG. Opini yang tidak memakai kata kunci tidak tertangkap.
- Tweet berbahasa selain Indonesia tidak ikut karena filter `lang:id`.
