"use client";

import { useState } from "react";
import Link from "next/link";
import { Shell } from "@/components/Shell";
import { useRequireAuth } from "@/lib/auth";
import { apiFetch, ApiError } from "@/lib/api";
import { Button, Notice } from "@/components/ui";

type DiagnosticItem = {
  item_id: string | null;
  question: string | null;
  options: string[] | null;
  is_final: boolean;
};
type StartOut = { session_id: string; item: DiagnosticItem };
type TopicResult = { topic: string; ability_score: number; weak: boolean };
type ResultOut = { status: string; topics: TopicResult[] };

const SUBJECT_LABELS: Record<string, string> = { math: "Математика", russian: "Русский язык" };

type Stage = "intro" | "in-progress" | "finished";

export default function DiagnosticsPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [subject, setSubject] = useState<"math" | "russian">("math");
  const [stage, setStage] = useState<Stage>("intro");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [item, setItem] = useState<DiagnosticItem | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<ResultOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const res = await apiFetch<StartOut>(`/api/v1/diagnostics/start?subject=${subject}`, {
        method: "POST",
      });
      setSessionId(res.session_id);
      if (res.item.is_final) {
        await finish(res.session_id);
      } else {
        setItem(res.item);
        setStage("in-progress");
      }
    } catch {
      setError("Не удалось начать диагностику. Попробуйте позже.");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswer(value: string) {
    if (!sessionId || !item?.item_id) return;
    if (!value.trim()) {
      setError("Введите ответ");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await apiFetch<StartOut>("/api/v1/diagnostics/answer", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, item_id: item.item_id, answer: value }),
      });
      setAnswer("");
      if (res.item.is_final) {
        await finish(sessionId);
      } else {
        setItem(res.item);
      }
    } catch {
      setError("Не удалось отправить ответ");
    } finally {
      setBusy(false);
    }
  }

  async function finish(sid: string) {
    try {
      const res = await apiFetch<ResultOut>(`/api/v1/diagnostics/${sid}/finalize`, {
        method: "POST",
      });
      setResult(res);
      setStage("finished");
    } catch {
      setError("Не удалось получить результат диагностики");
    }
  }

  if (authLoading || !user) return null;

  return (
    <Shell>
      <h1 className="font-display font-extrabold text-2xl text-ink">Диагностика</h1>

      <Notice className="mt-4 max-w-md">
        Сейчас это упрощённая версия: несколько тестовых вопросов, результат пока не
        подстраивается под ваши ответы. Полноценную адаптивную диагностику мы дорабатываем.
      </Notice>

      {stage === "intro" && (
        <div className="mt-6 max-w-md rounded-card border border-hairline bg-card p-6">
          <p className="text-sm text-ink leading-relaxed">
            Короткий тест покажет пример того, как будет выглядеть диагностика темы.
          </p>
          <label className="block mt-5">
            <span className="block text-sm font-medium text-ink mb-1.5">Предмет</span>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value as "math" | "russian")}
              className="focus-ring w-full rounded-lg border border-hairline bg-white px-3.5 py-2.5 text-sm text-ink"
            >
              <option value="math">Математика</option>
              <option value="russian">Русский язык</option>
            </select>
          </label>
          {error && <p className="mt-3 text-sm text-brick">{error}</p>}
          <Button onClick={start} disabled={busy} className="mt-5 w-full">
            {busy ? "Начинаем…" : "Начать диагностику"}
          </Button>
        </div>
      )}

      {stage === "in-progress" && item && (
        <div className="mt-6 max-w-md rounded-card border border-hairline bg-card p-6">
          <p className="text-xs font-medium text-indigo uppercase tracking-wide">
            {SUBJECT_LABELS[subject]}
          </p>
          <p className="mt-3 text-base text-ink leading-relaxed">{item.question}</p>

          {item.options ? (
            <div className="mt-5 flex flex-col gap-2">
              {item.options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => submitAnswer(opt)}
                  disabled={busy}
                  className="focus-ring text-left rounded-lg border border-hairline px-4 py-2.5 text-sm text-ink hover:bg-paper disabled:opacity-50"
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <div className="mt-5 flex gap-2">
              <input
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submitAnswer(answer)}
                placeholder="Ваш ответ"
                className="focus-ring flex-1 rounded-lg border border-hairline bg-white px-3.5 py-2.5 text-sm text-ink"
              />
              <Button onClick={() => submitAnswer(answer)} disabled={busy}>
                Далее
              </Button>
            </div>
          )}
          {error && <p className="mt-3 text-sm text-brick">{error}</p>}
        </div>
      )}

      {stage === "finished" && result && (
        <div className="mt-6 max-w-md">
          <div className="rounded-card border border-hairline bg-card p-6">
            <p className="font-medium text-ink">Диагностика завершена</p>
            <div className="mt-4 space-y-2">
              {result.topics.map((t) => (
                <div
                  key={t.topic}
                  className={`flex items-center justify-between rounded-lg px-4 py-3 ${
                    t.weak ? "bg-amber-soft" : "bg-teal-soft"
                  }`}
                >
                  <span className={`text-sm font-medium ${t.weak ? "text-amber" : "text-teal"}`}>
                    {t.topic}
                  </span>
                  <span className="font-mono text-sm text-muted">
                    {Math.round(t.ability_score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
          <Link
            href="/dashboard"
            className="focus-ring mt-4 inline-block rounded-lg bg-indigo px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-hover"
          >
            В личный кабинет
          </Link>
        </div>
      )}
    </Shell>
  );
}
