# Pickapic

Pickapic adalah aplikasi desktop berbasis Python + Flet untuk membantu mencari foto duplikat, gambar mirip, dan gambar blur dari folder lokal. Aplikasi ini cocok untuk membersihkan koleksi gambar seperti hasil kamera, screenshot, atau folder arsip yang sudah menumpuk.

## Fitur Utama

- Scan folder gambar dari komputer lokal.
- Deteksi **Exact Dupes** untuk file yang benar-benar duplikat.
- Deteksi **Similar** untuk gambar yang sangat mirip.
- Deteksi **Blurry** untuk gambar yang terindikasi blur.
- Preview gambar langsung dari aplikasi.
- Aksi cepat untuk:
  - hapus file
  - pindahkan file
  - rename file
  - undo aksi terakhir
- Pengaturan sensitivitas deteksi similar dan blur.
- Menyimpan cache hasil scan ke database lokal agar scan berikutnya lebih efisien.

## Teknologi yang Dipakai

- [Python 3.11+](https://www.python.org/)
- [Flet](https://flet.dev/) untuk UI desktop
- Pillow untuk baca/proses gambar
- imagehash untuk hashing gambar
- OpenCV untuk blur detection
- hnswlib + NumPy untuk pencarian gambar mirip
- SQLite untuk cache dan penyimpanan hasil scan

## Struktur Singkat Project

- `main.py` : entry point sederhana untuk menjalankan app dari repo
- `src/pickpic/main.py` : entry point package `pickpic`
- `src/pickpic/ui/` : tampilan aplikasi
- `src/pickpic/core/` : logika scan, hashing, grouping, blur detection, dan database
- `README.md` : dokumentasi project

## Instalasi

Pastikan Python 3.11 atau lebih baru sudah terpasang.

### Opsi 1: pakai `uv`

```powershell
uv sync
```

### Opsi 2: pakai `pip`

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

## Download Aplikasi dari Release

Kalau tidak ingin menjalankan dari source code, aplikasi bisa diunduh dari halaman release GitHub:

- [GitHub Releases Pickapic](https://github.com/alisholihindev/pickapic/releases)

Langkah umum:

1. Buka halaman release.
2. Pilih versi release terbaru.
3. Download file aplikasi yang tersedia di bagian **Assets**.
4. Ekstrak file jika release dikemas dalam `.zip`.
5. Jalankan file aplikasi, misalnya `.exe`, jika asset executable sudah disediakan.

Catatan:

- Jika di release belum ada file aplikasi siap pakai, kamu masih bisa download source code lalu jalankan project dari source seperti langkah di bawah.
- Untuk Windows, biasanya pengguna akan mencari file `.exe` atau paket `.zip` yang berisi aplikasi.

## Cara Menjalankan

Dari root project, bisa pakai salah satu cara berikut.

### Menjalankan dari file utama

```powershell
python main.py
```

### Menjalankan sebagai module/package

```powershell
python -m pickpic.main
```

### Menjalankan command yang didaftarkan di project

```powershell
pickpic
```

## Cara Penggunaan

1. Jalankan aplikasi.
2. Klik **Add Folder** untuk menambahkan folder gambar.
3. Klik **Scan** untuk mulai proses pemindaian.
4. Tunggu sampai proses scan, grouping, dan analisis selesai.
5. Buka kategori di sidebar:
   - `Exact Dupes` untuk file duplikat
   - `Similar` untuk gambar yang mirip
   - `Blurry` untuk gambar blur
6. Bandingkan gambar dalam tiap group.
7. Pilih gambar yang ingin diproses.
8. Gunakan action bar di bawah untuk:
   - **Delete**
   - **Move to...**
   - **Rename**
   - **Undo**

## Pengaturan

Menu **Settings** menyediakan beberapa opsi:

- **Detection Preset**
  - `Strict`
  - `Normal`
  - `Loose`
- **Similar Images Sensitivity**
  Mengatur ambang kemiripan gambar.
- **Blur Detection Sensitivity**
  Mengatur ambang deteksi blur.
- **File Size Filter**
  Melewati file yang lebih kecil dari ukuran minimum tertentu.
- **Reset Cache**
  Menghapus data hasil scan dan grouping dari cache lokal tanpa menyentuh file gambar asli.

## Format Gambar yang Didukung

Saat scan, aplikasi mengenali ekstensi berikut:

- `.jpg`
- `.jpeg`
- `.png`
- `.gif`
- `.bmp`
- `.webp`
- `.tiff`
- `.tif`
- `.raw`
- `.cr2`
- `.nef`

Catatan: dukungan preview bisa bergantung pada kemampuan library gambar yang dipakai.

## Penyimpanan Data Lokal

Pickapic menyimpan data lokal di folder home user:

- database cache: `~/.pickpic/index.db`
- settings: `~/.pickpic/settings.json`

Data ini dipakai untuk menyimpan hasil scan, grouping, dan konfigurasi aplikasi.

## Workflow Singkat

- Aplikasi menemukan file gambar dari folder yang dipilih.
- File yang sudah pernah discan dan belum berubah bisa dilewati dari cache.
- Gambar diproses untuk mendapatkan hash, ukuran, dan skor blur.
- Hasil dipakai untuk membentuk group duplikat dan group gambar mirip.
- Hasil ditampilkan di UI agar pengguna bisa memutuskan file mana yang ingin dipertahankan atau dibersihkan.

## Catatan

- Sebelum menghapus atau memindahkan file dalam jumlah besar, sebaiknya cek group hasil scan terlebih dahulu.
- Untuk koleksi besar, scan pertama bisa memakan waktu lebih lama karena cache belum terbentuk.
- Jika hasil grouping dirasa kurang pas, ubah sensitivitas di menu **Settings** lalu simpan agar aplikasi melakukan re-grouping.

## Development

Beberapa perintah yang berguna saat development:

```powershell
python -m py_compile src\pickpic\core\index.py
python main.py
```

## Lisensi

MIT License. Lihat file `LICENSE`.
