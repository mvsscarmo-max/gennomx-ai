"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  total_pages: number;
  onPage: (p: number) => void;
}

export function Pagination({ page, total_pages, onPage }: PaginationProps) {
  if (total_pages <= 1) return null;

  return (
    <div className="flex items-center gap-1 justify-end mt-4">
      <button
        onClick={() => onPage(page - 1)}
        disabled={page <= 1}
        className={cn(
          "p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none",
          "transition-colors"
        )}
        aria-label="Página anterior"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      <span className="px-3 py-1 text-sm text-slate-600 tabular-nums">
        {page} / {total_pages}
      </span>

      <button
        onClick={() => onPage(page + 1)}
        disabled={page >= total_pages}
        className={cn(
          "p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none",
          "transition-colors"
        )}
        aria-label="Próxima página"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
