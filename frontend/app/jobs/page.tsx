"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type Job = {
  listing?: { url?: string; title?: string; company?: string; location?: string; opportunity?: string; quota?: string | number };
  detail?: { description?: string; qualifications?: string[]; curriculum?: Array<{ title?: string; type?: string; month?: string; duration?: string; description?: string }> };
  scraping_status?: string;
};

function JobDetailContent() {
  const params = useSearchParams();
  const url = params.get("url") ?? "";
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!url) return;
    fetch(`${API_BASE}/api/v1/jobs/${encodeURIComponent(url)}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Lowongan tidak ditemukan.")))
      .then(setJob)
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Gagal memuat detail."));
  }, [url]);

  if (error) return <main className="detail-page"><Link href="/">← Kembali ke katalog</Link><div className="state-box error-state">{error}</div></main>;
  if (!job) return <main className="detail-page"><Link href="/">← Kembali ke katalog</Link><div className="state-box"><span className="pulse" />Memuat detail...</div></main>;

  const listing = job.listing ?? {};
  const detail = job.detail ?? {};
  return (
    <main className="detail-page">
      <Link className="back-link" href="/">← Kembali ke katalog</Link>
      <div className="detail-header">
        <p className="kicker">DETAIL LOWONGAN</p>
        <h1>{listing.title ?? "Tanpa judul"}</h1>
        <p className="detail-company">{listing.company} · {listing.location}</p>
        <span className="opportunity">{listing.opportunity ?? "Peluang belum tersedia"}</span>
      </div>
      <div className="detail-grid">
        <article>
          <h2>Tentang peran ini</h2>
          <p className="detail-description">{detail.description || "Deskripsi belum tersedia dari sumber."}</p>
          <h2>Yang akan dipelajari</h2>
          <div className="curriculum-list">
            {(detail.curriculum ?? []).map((item, index) => <div className="curriculum-item" key={`${item.title}-${index}`}><strong>{String(index + 1).padStart(2, "0")}</strong><div><b>{item.title}</b><small>{item.type} · {item.month} · {item.duration}</small><p>{item.description}</p></div></div>)}
          </div>
        </article>
        <aside>
          <h2>Persyaratan</h2>
          <ul>{(detail.qualifications ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
          <a className="primary-button" href={listing.url} target="_blank" rel="noreferrer">Buka sumber asli ↗</a>
        </aside>
      </div>
    </main>
  );
}

export default function JobDetail() {
  return (
    <Suspense fallback={<main className="detail-page"><Link href="/">← Kembali ke katalog</Link><div className="state-box"><span className="pulse" />Memuat detail...</div></main>}>
      <JobDetailContent />
    </Suspense>
  );
}
