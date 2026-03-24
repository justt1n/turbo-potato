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
    background: "#F4EFE6",
    surface: "#FFFDF8",
    surfaceAlt: "#F7F0E6",
    line: "rgba(20, 33, 38, 0.12)",
    text: "#142126",
    textMuted: "#65747A",
    accent: "#3D9B8A",
    accentSoft: "#DCEFE8",
    dangerSoft: "#F6D8CF",
    danger: "#DE7D67",
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
