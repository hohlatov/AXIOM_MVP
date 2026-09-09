"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api";
import { Button, TextField } from "@/components/ui";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) {
      setError("Ссылка недействительна — отсутствует токен");
      return;
    }
    if (password.length < 8) {
      setError("Пароль должен быть не короче 8 символов");
      return;
    }
    if (password !== confirm) {
      setError("Пароли не совпадают");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch("/api/v1/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
      });
      setDone(true);
      setTimeout(() => router.replace("/login"), 2000);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось обновить пароль"
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="text-center">
        <p className="text-sm text-brick">
          Ссылка недействительна. Проверьте, что перешли по полной ссылке из письма.
        </p>
        <Link
          href="/forgot-password"
          className="focus-ring mt-4 inline-block text-sm font-medium text-indigo hover:underline"
        >
          Запросить новую ссылку
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <p className="text-sm text-teal text-center">
        Пароль обновлён! Перенаправляем на вход…
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <TextField
        label="Новый пароль"
        type="password"
        autoComplete="new-password"
        placeholder="Минимум 8 символов"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <TextField
        label="Повторите пароль"
        type="password"
        autoComplete="new-password"
        placeholder="Ещё раз"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
      />
      {error && <p className="text-sm text-brick">{error}</p>}
      <Button type="submit" disabled={submitting} className="w-full">
        {submitting ? "Сохраняем…" : "Сохранить новый пароль"}
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-dot-grid flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="font-display font-extrabold text-2xl tracking-tight text-indigo">
            AXIOM
          </span>
          <p className="mt-2 text-sm text-muted">Новый пароль</p>
        </div>
        <div className="bg-card border border-hairline rounded-card p-6">
          <Suspense fallback={<p className="text-sm text-muted">Загрузка…</p>}>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
