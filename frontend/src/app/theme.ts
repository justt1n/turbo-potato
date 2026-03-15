export interface ThemePalette {
  background: string;
  surface: string;
  surfaceAlt: string;
  line: string;
  text: string;
  textMuted: string;
  accent: string;
  accentSoft: string;
  dangerSoft: string;
  danger: string;
}

export const palettes = {
  springRadar: {
    background: "#F0FFDF",
    surface: "#FFFFFF",
    surfaceAlt: "#F6FFE9",
    line: "rgba(36, 49, 39, 0.12)",
    text: "#1E2A20",
    textMuted: "#5E695F",
    accent: "#A8DF8E",
    accentSoft: "#F0FFDF",
    dangerSoft: "#FFD8DF",
    danger: "#FFAAB8",
  },
} satisfies Record<string, ThemePalette>;

export type PaletteName = keyof typeof palettes;

export function applyPalette(name: PaletteName): void {
  const palette = palettes[name];
  const root = document.documentElement;

  root.style.setProperty("--tp-bg", palette.background);
  root.style.setProperty("--tp-surface", palette.surface);
  root.style.setProperty("--tp-surface-alt", palette.surfaceAlt);
  root.style.setProperty("--tp-line", palette.line);
  root.style.setProperty("--tp-text", palette.text);
  root.style.setProperty("--tp-muted", palette.textMuted);
  root.style.setProperty("--tp-accent", palette.accent);
  root.style.setProperty("--tp-accent-soft", palette.accentSoft);
  root.style.setProperty("--tp-danger-soft", palette.dangerSoft);
  root.style.setProperty("--tp-danger", palette.danger);
}

