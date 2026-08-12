"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiUrl } from "@/lib/api-base";
import { withBasePath } from "@/lib/base-path";
import { setAccessTokenCookie } from "@/lib/auth-token";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const response = await fetch(apiUrl("api/v1/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: String(form.get("email") || ""),
        password: String(form.get("password") || ""),
      }),
    });

    let authError: string | undefined;
    if (response.ok) {
      const data = (await response.json()) as { access_token: string; expires_in: number };
      setAccessTokenCookie(data.access_token, data.expires_in);
    } else {
      const payload = (await response.json().catch(() => ({}))) as { detail?: string };
      authError = payload.detail ?? "Credenciais inválidas ou acesso não autorizado.";
    }
    setLoading(false);
    if (authError) return setError(authError);
    router.replace(withBasePath("/"));
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
