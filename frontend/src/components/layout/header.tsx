"use client";

import { Bell, Menu, Search } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface HeaderProps {
  title?: string;
  onMenuClick?: () => void;
}

export function Header({ title, onMenuClick }: HeaderProps) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/assets?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <header className="fixed top-0 left-0 lg:left-[var(--sidebar-width)] right-0 h-[var(--header-height)] bg-white border-b border-slate-100 flex items-center gap-4 px-4 sm:px-6 z-10">
      <button
        type="button"
        onClick={onMenuClick}
        className="p-2 -ml-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors lg:hidden"
        aria-label="Abrir menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {title && (
        <h1 className="page-title mr-2 hidden sm:block">{title}</h1>
      )}

      {/* Global search */}
      <form onSubmit={handleSearch} className="flex-1 max-w-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar ativos, empresas, trials..."
            className="input pl-9 text-sm h-9"
            autoComplete="off"
            spellCheck={false}
          />
        </div>
      </form>

      <div className="ml-auto flex items-center gap-2">
        <button
          className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
          aria-label="Notificações"
        >
          <Bell className="h-4 w-4" />
        </button>

        <div className="h-7 w-7 rounded-full bg-brand-rose/20 flex items-center justify-center">
          <span className="text-xs font-semibold text-brand-rose-dark">G</span>
        </div>
      </div>
    </header>
  );
}
