# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js + TypeScript frontend, FastAPI + Python backend, with the existing
Playwright crawler and JSON/CSV storage preserved during the incremental
migration.

## Users

Mahasiswa dan fresh graduate yang mencari lowongan magang publik tanpa akun.

## Product Purpose

MagangHub Job Finder mengumpulkan dan menyajikan lowongan magang secara
terstruktur agar pengguna dapat menemukan lowongan yang relevan lalu membuka
detailnya dalam kurang dari satu menit.

## Positioning

Produk menggabungkan data listing, detail, curriculum, snapshot, dan riwayat
perubahan dari crawler terkontrol menjadi katalog lowongan yang dapat dicari
dan dipantau secara publik.

## Operating Context

Pengguna mengakses dashboard melalui web desktop atau mobile. Data diperbarui
oleh crawler terpisah; request publik hanya membaca data yang sudah tersimpan.
Data sumber berasal dari MagangHub dan harus diverifikasi pengguna pada sumber
aslinya.

## Capabilities and Constraints

- Dashboard publik tanpa login.
- Pencarian, filter, sorting, pagination, detail, statistik, monitoring, dan
  export publik.
- Endpoint publik bersifat read-only.
- Playwright tidak boleh berjalan dalam request HTTP.
- JSON dan CSV legacy dipertahankan selama migrasi.
- PostgreSQL adalah target penyimpanan berikutnya.
- Rate limiting, burst protection, dan reverse proxy merupakan kebutuhan
  produksi.
- Jangan mengarang nilai untuk field yang tidak tersedia.

## Brand Commitments

Nama produk: MagangHub Job Finder.

Dashboard harus terasa editorial-data: tenang, terstruktur, mudah dipindai,
dan tidak terasa seperti admin panel internal atau antarmuka yang terlalu
ramai.

## Evidence on Hand

- PRD: [docs/PRD.md](docs/PRD.md)
- API read-only Phase 1: [backend/app/main.py](backend/app/main.py)
- Master data: [output/master/jobs.json](output/master/jobs.json)
- Snapshot dan histori perubahan di direktori `output/`.

Tidak ada testimonial, angka performa publik, atau aset brand tambahan yang
boleh difabrikasi.

## Product Principles

- Temukan yang relevan dengan cepat.
- Tampilkan data sumber secara jujur.
- Pisahkan pembacaan publik dari operasi crawler.
- Pertahankan histori dan perubahan data.
- Utamakan keterbacaan dan stabilitas.

## Accessibility & Inclusion

Dashboard harus responsif untuk desktop dan mobile, memiliki keyboard focus
yang jelas, label kontrol yang eksplisit, kontras teks yang memadai, serta
loading, empty, dan error states yang dapat dipahami.
