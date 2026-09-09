"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setAccessToken, API_URL } from "@/lib/api";
import { Button } from "@/components/ui";

function VkCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const code = searchParams.get("code");
  const errorParam = searchParams.get("error");

  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (errorParam) setError("VK не подтвердил авторизацию. Попробуйте войти ещё раз.");
    else if (!code) setError("Отсутствует код авторизации от VK. Попробуйте войти ещё раз.");
  }, [code, errorParam]);

  async function finish() {
    if (!code) return;
    if (!consent) {
      setError("Нужно согласие родителя/законного представителя, чтобы продолжить");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const params = new URLSearchParams({ code, parental_consent: "true" });
      const res = await fetch(`${API_URL}/api/v1/auth/vk/callback?${params.toString()}`);
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || "Не удалось войти через VK");
      }
      const tokens = await res.json();
      setAccessToken(tokens.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось войти через VK");
      setSubmitting(false);
    }
  }

  if (error) {
    return (
      <div className="text-center">
        <p className="text-sm text-brick">{error}</p>
        <a href="/login" className="focus-ring mt-4 inline-block text-sm font-medium text-indigo hover:underline">
          Вернуться ко входу
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-ink leading-relaxed">
        Почти готово — прежде чем создать аккаунт, подтвердите согласие на обработку
        персональных данных.
      </p>
      <label className="flex items-start gap-2.5 text-sm text-ink cursor-pointer">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          className="mt-0.5 focus-ring"
        />
        <span>
          Я родитель/законный представитель ученика и даю согласие на обработку его
          персональных данных в соответствии с 152-ФЗ, либо ученику уже исполнилось
          14 лет и он действует с согласия родителя.
        </span>
      </label>
      <Button onClick={finish} disabled={!consent || submitting} className="w-full">
        {submitting ? "Входим…" : "Продолжить"}
      </Button>
    </div>
  );
}

export default function VkCallbackPage() {
  return (
    <div className="min-h-screen bg-dot-grid flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="font-display font-extrabold text-2xl tracking-tight text-indigo">
            AXIOM
          </span>
          <p className="mt-2 text-sm text-muted">Вход через VK ID</p>
        </div>
        <div className="bg-card border border-hairline rounded-card p-6">
          <Suspense fallback={<p className="text-sm text-muted">Загрузка…</p>}>
            <VkCallbackInner />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
