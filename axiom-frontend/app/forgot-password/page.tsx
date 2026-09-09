"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Button, TextField } from "@/components/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setSubmitting(true);
    try {
      // Backend всегда отвечает 202 одинаково, есть ли такой email или нет —
      // это защита от перебора, поэтому здесь нечего проверять на ошибку.
      await apiFetch("/api/v1/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  }

  return (
    <div className="min-h-screen bg-dot-grid flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="font-display font-extrabold text-2xl tracking-tight text-indigo">
            AXIOM
          </span>
          <p className="mt-2 text-sm text-muted">Восстановление пароля</p>
        </div>

        <div className="bg-card border border-hairline rounded-card p-6">
          {submitted ? (
            <div className="text-center">
              <p className="text-sm text-ink leading-relaxed">
                Если этот email зарегистрирован, на него отправлена ссылка для
                сброса пароля. Проверьте почту — ссылка действует 30 минут.
              </p>
              <Link
                href="/login"
                className="focus-ring mt-5 inline-block text-sm font-medium text-indigo hover:underline"
              >
                Вернуться ко входу
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <p className="text-sm text-muted">
                Укажите email, указанный при регистрации, — пришлём ссылку для
                сброса пароля.
              </p>
              <TextField
                label="Email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Button type="submit" disabled={submitting} className="w-full">
                {submitting ? "Отправляем…" : "Отправить ссылку"}
              </Button>
              <p className="text-center text-sm text-muted pt-1">
                <Link href="/login" className="text-indigo hover:underline focus-ring rounded">
                  Вернуться ко входу
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
