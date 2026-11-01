import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MagangHub Job Finder",
  description: "Temukan lowongan magang yang relevan dengan cepat.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
