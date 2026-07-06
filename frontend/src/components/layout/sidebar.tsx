"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import {
  Activity,
  Archive,
  Beaker,
  Building2,
  FileSearch,
  FlaskConical,
  LayoutDashboard,
  Network,
  ServerCog,
  Shield,
  Stethoscope,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_GROUPS = [
  {
    label: "Ciência",
    items: [
      { href: "/", icon: LayoutDashboard, label: "Visão Geral" },
      { href: "/assets", icon: Beaker, label: "Ativos Terapêuticos" },
      { href: "/companies", icon: Building2, label: "Empresas" },
      { href: "/trials", icon: Stethoscope, label: "Ensaios Clínicos" },
      { href: "/indications", icon: FlaskConical, label: "Indicações" },
      { href: "/targets", icon: Network, label: "Targets" },
    ],
  },
  {
    label: "Operações",
    items: [
      { href: "/sources", icon: ServerCog, label: "Fontes de Dados" },
      { href: "/jobs", icon: Activity, label: "Jobs de Ingestão" },
      { href: "/mcp-logs", icon: FileSearch, label: "Logs MCP" },
      { href: "/security", icon: Shield, label: "Segurança" },
      { href: "/governance", icon: Archive, label: "Governança" },
    ],
  },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-30 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "fixed left-0 top-0 h-screen w-[var(--sidebar-width)] bg-white shadow-nav flex flex-col z-40",
          "transition-transform duration-200 ease-out lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-slate-100">
          <div className="h-7 w-7 rounded-lg bg-brand-rose flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold font-display">G</span>
          </div>
          <div>
            <span className="font-display font-bold text-slate-900 text-sm leading-none">GennomX</span>
            <span className="block text-[10px] text-slate-500 leading-none mt-0.5">AI Platform</span>
          </div>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 overflow-y-auto scrollbar-thin px-3 py-4 space-y-5">
          {NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <p className="px-3 mb-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
                {group.label}
              </p>
              <ul className="space-y-0.5">
                {group.items.map(({ href, icon: Icon, label }) => {
                  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
                  return (
                    <li key={href}>
                      <Link
                        href={href as Route}
                        onClick={onClose}
                        className={cn(
                          "nav-item",
                          active ? "nav-item-active" : "nav-item-default"
                        )}
                      >
                        <Icon className="h-4 w-4 flex-shrink-0" />
                        <span>{label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-slate-100 px-4 py-3">
          <p className="text-[10px] text-slate-500">v0.1.0 — MVP</p>
        </div>
      </aside>
    </>
  );
}
