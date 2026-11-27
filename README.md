# Sistem PMB API

REST API untuk pengelolaan Penerimaan Mahasiswa Baru (PMB) yang dibangun menggunakan **FastAPI**, **SQLAlchemy**, **Pydantic**, dan **SQLite**.

## Fitur Utama
- **Pendaftaran Calon Mahasiswa (`POST /api/pmb/register`)**: menyimpan data pendaftar (`CalonMahasiswa`) berdasarkan pilihan jalur masuk (`SNBP`, `SNBT`, `Mandiri`) dan program studi (`ProgramStudi`), dengan status awal `pending`.
- **Cek Status Pendaftaran (`GET /api/pmb/status/{id}`)**: melihat status pendaftaran calon mahasiswa berdasarkan ID.
- **Persetujuan Kandidat (`PUT /api/pmb/approve/{id}`)**: memproses persetujuan kandidat menjadi `approved` (termasuk pengisian `nim` dan `approved_at`) atau penolakan (`rejected`).
- **Statistik Pendaftaran (`GET /api/pmb/stats`)**: menampilkan ringkasan statistik data pendaftaran PMB.

## Struktur Proyek
- `main.py` — Konfigurasi aplikasi FastAPI, database, dan *endpoint* API.
- `models.py` — Definisi *enum* (`JalurEnum`, `StatusEnum`) serta model SQLAlchemy (`ProgramStudi`, `CalonMahasiswa`).
- `schemas.py` — Skema validasi data Pydantic (termasuk validasi nomor telepon format Indonesia).
- `database.py` — Pengaturan koneksi dan sesi *database*.
- `pmb.db` — *Database* lokal SQLite.
- `test_pmb.py` — Pengujian otomatis (*unit/API test*) untuk modul PMB.

## Cara Menjalankan Proyek

1. **Aktifkan *virtual environment* (PowerShell)**
   ```powershell
   .\venv\Scripts\Activate.ps1