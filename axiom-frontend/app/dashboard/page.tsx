"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Shell } from "@/components/Shell";
import { useRequireAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

type SubjectProgress = { subject: string; subject_label: string; percent: number };
type Recommendation = { topic: string; reason: string };
type DashboardSummary = {
  grade: number | null;
  progress: SubjectProgress[];
  recommendations: Recommendation[];
  quick_actions: string[];
  has_diagnostic_result: boolean;
};

export default function DashboardPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiFetch<DashboardSummary>("/api/v1/dashboard/summary")
      .then(setSummary)
      .finally(() => setLoading(false));
  }, [user]);

  if (authLoading || !user) return null;

  return (
    <Shell>
      <h1 className="font-display font-extrabold text-2xl text-ink">
        Привет{user.email ? `, ${user.email.split("@")[0]}` : ""}!
      </h1>
      <p className="mt-1 text-sm text-muted">
        {summary?.grade ? `${summary.grade} класс · ` : ""}вот как продвигается подготовка.
      </p>

      {loading ? (
        <p className="mt-8 text-sm text-muted">Загрузка…</p>
      ) : (
        <>
          <section className="mt-8 grid gap-4 sm:grid-cols-2">
            {summary?.progress.map((p) => (
              <div
                key={p.subject}
                className="relative overflow-hidden rounded-card border border-hairline bg-card p-5"
              >
                <div className="absolute inset-0 bg-dot-grid opacity-40 pointer-events-none" />
                <div className="relative">
                  <p className="text-sm font-medium text-muted">{p.subject_label}</p>
                  <p className="mt-2 font-mono text-3xl font-semibold text-indigo">
                    {p.percent}%
                  </p>
                  <div className="mt-3 h-1.5 w-full rounded-full bg-hairline overflow-hidden">
                    <div
                      className="h-full rounded-full bg-teal"
                      style={{ width: `${p.percent}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </section>

          {!summary?.has_diagnostic_result && (
            <div className="mt-6 rounded-card border border-hairline bg-indigo-soft p-5 flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="font-medium text-ink">Пройдите входную диагностику</p>
                <p className="text-sm text-muted mt-0.5">
                  15–20 вопросов — узнаете, на каких темах стоит сосредоточиться.
                </p>
              </div>
              <Link
                href="/diagnostics"
                className="focus-ring rounded-lg bg-indigo px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-hover"
              >
                Начать диагностику
              </Link>
            </div>
          )}

          {!!summary?.recommendations.length && (
            <section className="mt-8">
              <h2 className="font-display font-bold text-lg text-ink">Рекомендации</h2>
              <div className="mt-3 space-y-2">
                {summary.recommendations.map((r, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg border border-hairline bg-card px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-ink">{r.topic}</p>
                      <p className="text-xs text-muted">{r.reason}</p>
                    </div>
                    <Link
                      href="/trainer"
                      className="focus-ring text-sm font-medium text-indigo hover:underline"
                    >
                      Тренировать
                    </Link>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="mt-8 flex gap-3">
            <Link
              href="/trainer"
              className="focus-ring rounded-lg border border-hairline bg-card px-4 py-2.5 text-sm font-semibold text-ink hover:bg-paper"
            >
              Открыть тренажёр
            </Link>
            <Link
              href="/diagnostics"
              className="focus-ring rounded-lg border border-hairline bg-card px-4 py-2.5 text-sm font-semibold text-ink hover:bg-paper"
            >
              Пройти диагностику
            </Link>
            <Link
              href="/assistant"
              className="focus-ring rounded-lg border border-hairline bg-card px-4 py-2.5 text-sm font-semibold text-ink hover:bg-paper"
            >
              Спросить ассистента
            </Link>
          </section>
        </>
      )}
    </Shell>
  );
}
