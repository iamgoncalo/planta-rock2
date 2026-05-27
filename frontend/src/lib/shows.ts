import type { Show } from "@/types";

export const STATIC_SHOWS: Show[] = [
  // 20 Jun
  {
    id: "s01",
    data: "2026-06-20",
    hora_inicio: "18:00",
    hora_fim: "19:00",
    artista: "Dino d'Santiago",
    palco: "PSB",
    headliner: false,
    genero: "Afro-Soul",
    surge_esperado_30min_apos: false,
    clusters_afectados: ["WC-03", "WC-05"],
  },
  {
    id: "s02",
    data: "2026-06-20",
    hora_inicio: "19:30",
    hora_fim: "20:30",
    artista: "Burna Boy",
    palco: "PM",
    headliner: false,
    genero: "Afrobeats",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-02", "WC-04"],
  },
  {
    id: "s03",
    data: "2026-06-20",
    hora_inicio: "21:00",
    hora_fim: "23:00",
    artista: "Taylor Swift",
    palco: "PM",
    headliner: true,
    genero: "Pop",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-02", "WC-03", "WC-04", "WC-05"],
  },
  // 21 Jun
  {
    id: "s04",
    data: "2026-06-21",
    hora_inicio: "17:00",
    hora_fim: "18:00",
    artista: "Conjunto Tempo",
    palco: "PBP",
    headliner: false,
    genero: "Kizomba",
    surge_esperado_30min_apos: false,
    clusters_afectados: ["WC-06", "WC-07"],
  },
  {
    id: "s05",
    data: "2026-06-21",
    hora_inicio: "20:00",
    hora_fim: "21:30",
    artista: "Bad Bunny",
    palco: "PM",
    headliner: false,
    genero: "Reggaeton",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-03", "WC-05"],
  },
  {
    id: "s06",
    data: "2026-06-21",
    hora_inicio: "22:00",
    hora_fim: "00:00",
    artista: "Kendrick Lamar",
    palco: "PM",
    headliner: true,
    genero: "Hip-Hop",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-02", "WC-03", "WC-04", "WC-06"],
  },
  // 27 Jun
  {
    id: "s07",
    data: "2026-06-27",
    hora_inicio: "18:30",
    hora_fim: "19:30",
    artista: "Wet Leg",
    palco: "PMV",
    headliner: false,
    genero: "Indie Rock",
    surge_esperado_30min_apos: false,
    clusters_afectados: ["WC-07", "WC-08"],
  },
  {
    id: "s08",
    data: "2026-06-27",
    hora_inicio: "20:30",
    hora_fim: "22:00",
    artista: "Olivia Rodrigo",
    palco: "PM",
    headliner: false,
    genero: "Pop Rock",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-02", "WC-03", "WC-04"],
  },
  {
    id: "s09",
    data: "2026-06-27",
    hora_inicio: "22:30",
    hora_fim: "00:30",
    artista: "Sabrina Carpenter",
    palco: "PM",
    headliner: true,
    genero: "Pop",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-02", "WC-03", "WC-04", "WC-05"],
  },
  // 28 Jun
  {
    id: "s10",
    data: "2026-06-28",
    hora_inicio: "17:30",
    hora_fim: "18:30",
    artista: "Sevdaliza",
    palco: "PSB",
    headliner: false,
    genero: "Electronic",
    surge_esperado_30min_apos: false,
    clusters_afectados: ["WC-05", "WC-06"],
  },
  {
    id: "s11",
    data: "2026-06-28",
    hora_inicio: "19:00",
    hora_fim: "20:30",
    artista: "The Weeknd",
    palco: "PM",
    headliner: false,
    genero: "R&B",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-04", "WC-07"],
  },
  {
    id: "s12",
    data: "2026-06-28",
    hora_inicio: "21:30",
    hora_fim: "23:30",
    artista: "Billie Eilish",
    palco: "PM",
    headliner: true,
    genero: "Alternative Pop",
    surge_esperado_30min_apos: true,
    clusters_afectados: ["WC-01", "WC-02", "WC-03", "WC-04", "WC-06", "WC-07"],
  },
];

export const FESTIVAL_DAYS = ["2026-06-20", "2026-06-21", "2026-06-27", "2026-06-28"];

export const STAGE_LABELS: Record<string, string> = {
  PM: "Palco Mundo",
  PMV: "Palco Mundo Verde",
  PSB: "Palco Super Bock",
  PBP: "Palco BPI by Palco",
};

export function getShowsForDay(day: string): Show[] {
  return STATIC_SHOWS.filter((s) => s.data === day).sort((a, b) =>
    a.hora_inicio.localeCompare(b.hora_inicio)
  );
}

export function getCurrentShow(now: Date = new Date()): Show | null {
  const dateStr = now.toISOString().slice(0, 10);
  const timeStr = now.toTimeString().slice(0, 5);

  return (
    STATIC_SHOWS.find(
      (s) =>
        s.data === dateStr &&
        s.hora_inicio <= timeStr &&
        s.hora_fim >= timeStr
    ) ?? null
  );
}
