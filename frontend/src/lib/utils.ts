import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "agora mesmo";
  if (minutes < 60) return `${minutes}min atrás`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h atrás`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d atrás`;
  return formatDate(iso);
}

export function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR").format(n);
}

export function safeExternalUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.toString() : null;
  } catch {
    return null;
  }
}

export function confidenceColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "text-slate-400";
  if (score >= 0.8) return "text-success";
  if (score >= 0.5) return "text-warning";
  return "text-danger";
}

// Keys mirror the canonical `phase_normalized` vocabulary produced by
// ClinicalTrialsNormalizer.PHASE_MAP (backend/workers/connectors/clinicaltrials/normalizer.py)
// and reused as-is for drug_assets.development_stage.
export function phaseLabel(phase: string | null): string {
  if (!phase) return "—";
  const map: Record<string, string> = {
    PHASE1: "Fase I",
    PHASE2: "Fase II",
    PHASE3: "Fase III",
    PHASE4: "Fase IV",
    PHASE1_2: "Fase I/II",
    PHASE2_3: "Fase II/III",
    EARLY_PHASE1: "Fase I precoce",
    NA: "N/A",
  };
  return map[phase] ?? phase;
}

export function statusVariant(
  status: string | null
): "success" | "warning" | "danger" | "info" | "slate" {
  if (!status) return "slate";
  const s = status.toUpperCase();
  if (["RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED", "APPROVED"].includes(s)) return "success";
  if (["ENROLLING_BY_INVITATION", "AVAILABLE"].includes(s)) return "info";
  if (["NOT_YET_RECRUITING", "SUSPENDED"].includes(s)) return "warning";
  if (["TERMINATED", "WITHDRAWN", "REJECTED"].includes(s)) return "danger";
  return "slate";
}
