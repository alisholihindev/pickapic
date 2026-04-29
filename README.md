<p align="center">
  <img src="src/pickpic/assets/pickapic-logo.png" alt="Pickapic Logo" width="120" />
</p>

<h1 align="center">Pickapic</h1>

<p align="center">
  Aplikasi desktop untuk membersihkan koleksi gambar lokal — temukan duplikat, gambar mirip, foto blur, dan masalah GPS dalam hitungan detik.
</p>

<p align="center">
  <img src="https://img.shields.io/github/v/release/alisholihindev/pickapic?style=flat-square&color=blue" alt="Latest Release" />
  <img src="https://img.shields.io/github/license/alisholihindev/pickapic?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/UI-Flet-purple?style=flat-square" alt="Flet" />
  <img src="https://img.shields.io/github/stars/alisholihindev/pickapic?style=flat-square" alt="Stars" />
  <img src="https://img.shields.io/github/downloads/alisholihindev/pickapic/total?style=flat-square&color=green" alt="Downloads" />
</p>

---

## Statistik Project

| Metrik | Detail |
|---|---|
| Bahasa | Python 3.11+ |
| UI Framework | [Flet](https://flet.dev/) (Flutter-based) |
| Database | SQLite (WAL mode) |
| Format Didukung | 11 format (JPG, PNG, GIF, BMP, WebP, TIFF, RAW, CR2, NEF) |
| Fitur Deteksi | 6 kategori (Exact Dupes, Similar, Dup Geotag, Blurry, No Geotag, Not North) |
| Scan Engine | Multi-threaded (hingga 8 workers) |
| Lisensi | MIT |

---

## Fitur Utama

- Scan folder gambar dari komputer lokal.
- Deteksi **Exact Dupes** untuk file yang benar-benar duplikat.
- Deteksi **Similar** untuk gambar yang sangat mirip.
- Deteksi **Blurry** untuk gambar yang terindikasi blur.
- Deteksi **Dup Geotag** untuk gambar yang diambil di lokasi yang sama.
- Deteksi **No Geotag** untuk gambar tanpa data GPS.
- Deteksi **Not North** untuk gambar yang tidak menghadap utara.
- **Pilih fitur yang diinginkan** — aktifkan/nonaktifkan deteksi Duplikat, Blur, atau GPS sesuai kebutuhan.
- Preview gambar langsung dari aplikasi dengan metadata EXIF lengkap.
- Aksi cepat untuk:
  - hapus file (ke Recycle Bin)
  - pindahkan file
  - rename file
  - undo aksi terakhir
- Pengaturan sensitivitas deteksi similar dan blur.
- Menyimpan cache hasil scan ke database lokal agar scan berikutnya lebih efisien.

## Teknologi yang Dipakai

| Library | Fungsi |
|---|---|
| [Python 3.11+](https://www.python.org/) | Runtime |
| [Flet](https://flet.dev/) | UI desktop (Flutter-based) |
| [Pillow](https://pillow.readthedocs.io/) | Baca/proses gambar, EXIF, thumbnail |
| [imagehash](https://github.com/JohannesBuchner/imagehash) | Perceptual hashing (pHash, dHash) |
| [OpenCV](https://opencv.org/) | Blur detection (Laplacian variance) |
| [hnswlib](https://github.com/nmslib/hnswlib) + NumPy | Pencarian gambar mirip |
| [send2trash](https://github.com/arsenetar/send2trash) | Hapus file ke Recycle Bin |
| SQLite | Cache dan penyimpanan hasil scan |

## Struktur Singkat Project

```
pickapic/
├── main.py                    # Entry point untuk menjalankan app dari repo
├── pyproject.toml             # Metadata package dan dependencies
├── src/pickpic/
│   ├── main.py                # Entry point package (CLI command)
│   ├── config.py              # Konstanta, path, Settings dataclass
│   ├── core/                  # Logika backend
│   │   ├── scanner.py         # Multi-threaded image discovery & processing
│   │   ├── hasher.py          # Perceptual hashing + EXIF GPS extraction
│   │   ├── blur.py            # Blur detection (Laplacian variance)
│   │   ├── similarity.py      # Grouping duplikat & gambar mirip
│   │   ├── index.py           # SQLite database layer
│   │   ├── actions.py         # File operations (delete/move/rename/undo)
│   │   └── scan_control.py    # Pause/resume/abort controller
│   ├── ui/                    # Tampilan aplikasi (Flet)
│   │   ├── app.py             # Main application controller
│   │   ├── components/        # Komponen UI (sidebar, image card, action bar)
│   │   └── views/             # Halaman (scanner, results, settings, about)
│   └── assets/                # Logo dan icon
└── README.md
```

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
3. (Opsional) Buka **Settings** untuk memilih fitur deteksi yang diinginkan:
   - **Duplicate Detection** — Exact Dupes & Similar
   - **Blur Detection** — Gambar blur
   - **GPS Analysis** — Dup Geotag, No Geotag, Not North
4. Klik **Scan** untuk mulai proses pemindaian.
5. Tunggu sampai proses scan, grouping, dan analisis selesai.
6. Buka kategori di sidebar:
   - `Exact Dupes` untuk file duplikat
   - `Similar` untuk gambar yang mirip
   - `Dup Geotag` untuk gambar di lokasi yang sama
   - `Blurry` untuk gambar blur
   - `No Geotag` untuk gambar tanpa GPS
   - `Not North` untuk gambar tidak menghadap utara
7. Bandingkan gambar dalam tiap group.
8. Pilih gambar yang ingin diproses.
9. Gunakan action bar di bawah untuk:
   - **Delete**
   - **Move to...**
   - **Rename**
   - **Undo**

## Pengaturan

Menu **Settings** menyediakan beberapa opsi:

- **Enabled Features**
  Pilih fitur deteksi yang ingin dijalankan saat scan:
  - `Duplicate Detection` — Exact Dupes & Similar
  - `Blur Detection` — Gambar blur
  - `GPS Analysis` — Dup Geotag, No Geotag, Not North
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
- **Image Display Mode**
  Pilih tampilan card gambar: Portrait atau Landscape.
- **Reset Cache**
  Menghapus data hasil scan dan grouping dari cache lokal tanpa menyentuh file gambar asli.

## Format Gambar yang Didukung

Saat scan, aplikasi mengenali ekstensi berikut:

| Format | Ekstensi |
|---|---|
| JPEG | `.jpg`, `.jpeg` |
| PNG | `.png` |
| GIF | `.gif` |
| BMP | `.bmp` |
| WebP | `.webp` |
| TIFF | `.tiff`, `.tif` |
| RAW | `.raw`, `.cr2`, `.nef` |

Catatan: dukungan preview bisa bergantung pada kemampuan library gambar yang dipakai.

## Penyimpanan Data Lokal

Pickapic menyimpan data lokal di folder home user:

| File | Lokasi | Fungsi |
|---|---|---|
| Database cache | `~/.pickpic/index.db` | Hasil scan, grouping, undo log |
| Settings | `~/.pickpic/settings.json` | Konfigurasi aplikasi |
| Thumbnails | `~/.pickpic/thumbs/` | Cache thumbnail gambar |

Data ini dipakai untuk menyimpan hasil scan, grouping, dan konfigurasi aplikasi.

## Workflow Singkat

```
Pilih Folder → Pilih Fitur → Scan
    │
    ├── Discover file gambar
    ├── Skip file yang sudah di-cache
    ├── Proses hash, blur score, GPS (multi-threaded)
    ├── Simpan ke SQLite
    │
    ├── [Jika Duplicate aktif] Grouping exact & similar
    ├── [Jika GPS aktif] Grouping geotag duplikat
    │
    └── Tampilkan hasil → User pilih aksi (Delete/Move/Rename/Undo)
```

## Catatan

- Sebelum menghapus atau memindahkan file dalam jumlah besar, sebaiknya cek group hasil scan terlebih dahulu.
- Untuk koleksi besar, scan pertama bisa memakan waktu lebih lama karena cache belum terbentuk.
- Jika hasil grouping dirasa kurang pas, ubah sensitivitas di menu **Settings** lalu simpan agar aplikasi melakukan re-grouping.
- Fitur yang dinonaktifkan akan melewati komputasi terkait, sehingga scan lebih cepat.

## Development

Beberapa perintah yang berguna saat development:

```powershell
python -m py_compile src\pickpic\core\index.py
python main.py
```

## Lisensi

MIT License. Lihat file [`LICENSE`](LICENSE).
