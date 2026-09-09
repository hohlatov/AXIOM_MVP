"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth, ApiError } from "@/lib/auth";
import { apiFetch, API_URL } from "@/lib/api";
import { Button, TextField } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError("Заполните email и пароль");
      return;
    }
    setSubmitting(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось войти");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVkLogin() {
    try {
      const { authorize_url } = await apiFetch<{ authorize_url: string }>(
        "/api/v1/auth/vk/login"
      );
      window.location.href = authorize_url;
    } catch {
      setError("VK ID временно недоступен");
    }
  }

  return (
    <div className="min-h-screen bg-dot-grid flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="font-display font-extrabold text-2xl tracking-tight text-indigo">
            AXIOM
          </span>
          <p className="mt-2 text-sm text-muted">Персональный ИИ-репетитор для ОГЭ</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-card border border-hairline rounded-card p-6 space-y-4"
        >
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            label="Пароль"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="flex justify-end -mt-2">
            <Link
              href="/forgot-password"
              className="focus-ring text-xs text-indigo hover:underline rounded"
            >
              Забыли пароль?
            </Link>
          </div>
          {error && <p className="text-sm text-brick">{error}</p>}
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Входим…" : "Войти"}
          </Button>
          <Button type="button" variant="secondary" onClick={handleVkLogin} className="w-full">
            Войти через VK ID
          </Button>
          <p className="text-center text-sm text-muted pt-1">
            <Link href="/register" className="text-indigo hover:underline focus-ring rounded">
              Ещё нет аккаунта? Зарегистрироваться
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
