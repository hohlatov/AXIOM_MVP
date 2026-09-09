"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth, ApiError } from "@/lib/auth";
import { Button, TextField } from "@/components/ui";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [grade, setGrade] = useState("9");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || password.length < 8) {
      setError("Email обязателен, пароль — от 8 символов");
      return;
    }
    if (!consent) {
      setError("Нужно согласие родителя/законного представителя, чтобы продолжить");
      return;
    }
    setSubmitting(true);
    try {
      await register(email, password, grade ? Number(grade) : null, consent);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось зарегистрироваться");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-dot-grid flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="font-display font-extrabold text-2xl tracking-tight text-indigo">
            AXIOM
          </span>
          <p className="mt-2 text-sm text-muted">Регистрация ученика</p>
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
            autoComplete="new-password"
            placeholder="Минимум 8 символов"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <label className="block">
            <span className="block text-sm font-medium text-ink mb-1.5">Класс</span>
            <select
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
              className="focus-ring w-full rounded-lg border border-hairline bg-white px-3.5 py-2.5 text-sm text-ink"
            >
              <option value="9">9 класс</option>
              <option value="8">8 класс</option>
              <option value="10">10 класс</option>
              <option value="11">11 класс</option>
            </select>
          </label>
          <label className="flex items-start gap-2.5 text-sm text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5 focus-ring"
            />
            <span>
              Я родитель/законный представитель ученика и даю согласие на обработку
              его персональных данных в соответствии с 152-ФЗ, либо ученику уже
              исполнилось 14 лет и он действует с согласия родителя.
            </span>
          </label>
          {error && <p className="text-sm text-brick">{error}</p>}
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Создаём аккаунт…" : "Создать аккаунт"}
          </Button>
          <p className="text-center text-sm text-muted pt-1">
            <Link href="/login" className="text-indigo hover:underline focus-ring rounded">
              Уже есть аккаунт? Войти
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
