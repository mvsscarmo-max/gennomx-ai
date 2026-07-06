"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const { error: authError } = await getSupabaseBrowserClient().auth.signInWithPassword({
      email: String(form.get("email") || ""),
      password: String(form.get("password") || ""),
    });
    setLoading(false);
    if (authError) return setError("Credenciais inválidas ou acesso não autorizado.");
    router.replace("/");
    router.refresh();
  }

  return (
    <main className="min-h-screen grid place-items-center bg-surface-subtle p-6">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-6">
        <div className="flex items-center gap-2.5 mb-1">
          <div className="h-8 w-8 rounded-lg bg-brand-rose flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm font-bold font-display">G</span>
          </div>
          <div>
            <span className="font-display font-bold text-slate-900 text-sm leading-none">GennomX</span>
            <span className="block text-[10px] text-slate-500 leading-none mt-0.5">AI Platform</span>
          </div>
        </div>
        <h1 className="page-title">Acesso GennomX AI</h1>
        <label className="block text-sm text-slate-700">
          E-mail
          <input className="input mt-1" name="email" type="email" required autoComplete="email" />
        </label>
        <label className="block text-sm text-slate-700">
          Senha
          <input className="input mt-1" name="password" type="password" required autoComplete="current-password" />
        </label>
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        <button className="btn-primary w-full justify-center" disabled={loading}>
          {loading ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </main>
  );
}
