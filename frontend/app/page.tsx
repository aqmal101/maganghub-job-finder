"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";

type Listing = {
  url?: string;
  title?: string;
  company?: string;
  location?: string;
  opportunity?: string;
  quota?: number | string | null;
  applicants?: number | string | null;
};

type Job = {
  listing?: Listing;
  detail?: {
    description?: string;
    qualifications?: string[];
    curriculum?: Array<{ title?: string; type?: string; month?: string }>;
  };
  scraping_status?: string;
  last_seen_at?: string;
};

type JobsResponse = {
  items: Job[];
  pagination: { page: number; page_size: number; total: number; total_pages: number };
};

type Stats = {
  total_jobs: number;
  successful_jobs: number;
  partial_jobs: number;
  failed_jobs: number;
  new_jobs: number;
  last_updated_at?: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

function formatDate(value?: string | null) {
  if (!value) return "Belum tersedia";
  return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date(value));
}

function statusLabel(status?: string) {
  if (status === "success") return "Terverifikasi";
  if (status === "partial") return "Sebagian";
  return "Perlu ditinjau";
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<JobsResponse["pagination"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async (nextPage = page, search = submittedQuery, nextLocation = location) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({
        page: String(nextPage),
        page_size: "8",
      });
      if (search) params.set("search", search);
      if (nextLocation) params.set("location", nextLocation);
      const [jobsResponse, statsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/v1/jobs?${params}`),
        fetch(`${API_BASE}/api/v1/statistics`),
      ]);
      if (!jobsResponse.ok || !statsResponse.ok) throw new Error("API tidak dapat dihubungi.");
      const jobsData: JobsResponse = await jobsResponse.json();
      setJobs(jobsData.items);
      setPagination(jobsData.pagination);
      setStats(await statsResponse.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Terjadi kesalahan.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData(1, "", "");
    // Initial request only; filters trigger an explicit submit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const locations = useMemo(
    () => Array.from(new Set(jobs.map((job) => job.listing?.location).filter(Boolean))),
    [jobs],
  );

  function submitFilters(event: FormEvent) {
    event.preventDefault();
    setSubmittedQuery(query.trim());
    setPage(1);
    void loadData(1, query.trim(), location);
  }

  function changePage(nextPage: number) {
    setPage(nextPage);
    void loadData(nextPage, submittedQuery, location);
  }

  return (
    <main>
      <header className="topbar">
        <Link className="brand" href="/">
          <span className="brand-mark">MH</span>
          <span>MagangHub <em>Job Finder</em></span>
        </Link>
        <nav>
          <a href="#jobs">Lowongan</a>
          <a href="#monitoring">Monitoring</a>
          <a href="#about">Tentang</a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="kicker">KATALOG MAGANG PUBLIK</p>
          <h1>Temukan tempat untuk<br /><span>mulai bergerak.</span></h1>
          <p className="hero-lede">
            Lowongan magang terkurasi dari MagangHub, disusun agar kamu bisa
            menemukan yang relevan sebelum satu menit berlalu.
          </p>
          <form className="searchbar" onSubmit={submitFilters}>
            <label htmlFor="search">Cari posisi, perusahaan, atau jurusan</label>
            <div className="search-row">
              <input
                id="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="mis. software engineer"
              />
              <button type="submit">Cari lowongan</button>
            </div>
          </form>
        </div>
        <div className="hero-index" aria-label="Ringkasan katalog">
          <span className="index-label">LIVE INDEX</span>
          <strong>{stats?.total_jobs ?? "—"}</strong>
          <span>lowongan terlacak</span>
          <div className="index-rule" />
          <small>Pembaruan terakhir<br />{formatDate(stats?.last_updated_at)}</small>
        </div>
      </section>

      <section className="stats-strip" id="monitoring">
        <div><span>Total lowongan</span><strong>{stats?.total_jobs ?? "—"}</strong></div>
        <div><span>Detail terverifikasi</span><strong>{stats?.successful_jobs ?? "—"}</strong></div>
        <div><span>Lowongan baru</span><strong>{stats?.new_jobs ?? "—"}</strong></div>
        <div><span>Status indeks</span><strong className="status-live">● Aktif</strong></div>
      </section>

      <section className="catalog" id="jobs">
        <div className="section-heading">
          <div>
            <p className="kicker">PAPAN KEBERANGKATAN</p>
            <h2>Lowongan yang tersedia</h2>
          </div>
          <p className="result-count">{pagination?.total ?? 0} hasil ditemukan</p>
        </div>

        <form className="filters" onSubmit={submitFilters}>
          <label>
            Lokasi
            <select value={location} onChange={(event) => setLocation(event.target.value)}>
              <option value="">Semua lokasi</option>
              {locations.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <button type="submit" className="filter-button">Terapkan filter</button>
          <a className="download-link" href={`${API_BASE}/api/v1/exports/jobs.csv`}>Unduh CSV</a>
        </form>

        {error && <div className="state-box error-state"><strong>Data belum dapat dimuat.</strong><span>{error} Pastikan API berjalan di port 8000.</span><button onClick={() => void loadData()}>Coba lagi</button></div>}
        {!error && loading && <div className="state-box"><span className="pulse" />Memuat katalog terbaru...</div>}
        {!error && !loading && jobs.length === 0 && <div className="state-box"><strong>Tidak ada lowongan yang cocok.</strong><span>Coba kata kunci atau lokasi yang lebih umum.</span></div>}
        {!error && !loading && jobs.length > 0 && (
          <div className="board" role="table" aria-label="Daftar lowongan">
            <div className="board-head" role="row">
              <span>Posisi / penyelenggara</span><span>Lokasi</span><span>Peluang</span><span>Status</span><span />
            </div>
            {jobs.map((job, index) => {
              const listing = job.listing ?? {};
              const href = `/jobs?url=${encodeURIComponent(listing.url ?? "")}`;
              return (
                <Link className="job-row" href={href} key={listing.url ?? index} role="row">
                  <span className="job-name"><b>{listing.title ?? "Tanpa judul"}</b><small>{listing.company ?? "Penyelenggara tidak tersedia"}</small></span>
                  <span>{listing.location ?? "—"}</span>
                  <span className="opportunity">{listing.opportunity ?? "—"}</span>
                  <span><i className={`status-dot ${job.scraping_status}`} />{statusLabel(job.scraping_status)}</span>
                  <span className="arrow" aria-hidden="true">↗</span>
                </Link>
              );
            })}
          </div>
        )}
        {pagination && pagination.total_pages > 1 && (
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => changePage(page - 1)}>Sebelumnya</button>
            <span>Halaman {page} / {pagination.total_pages}</span>
            <button disabled={page >= pagination.total_pages} onClick={() => changePage(page + 1)}>Berikutnya</button>
          </div>
        )}
      </section>

      <footer id="about">
        <div><span className="brand-mark">MH</span><p>Data membantu menemukan arah.<br />Keputusan tetap milikmu.</p></div>
        <span>Data bersumber dari MagangHub dan perlu diverifikasi pada sumber asli.</span>
      </footer>
    </main>
  );
}
