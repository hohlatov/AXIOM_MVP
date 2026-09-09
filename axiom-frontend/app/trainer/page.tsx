"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { useRequireAuth } from "@/lib/auth";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui";

type Task = {
  id: string;
  subject: string;
  topic: string;
  difficulty: number;
  question: string;
  options: string[] | null;
};
type SubmitResult = { is_correct: boolean; correct_answer: string; explanation: string };

const SUBJECT_LABELS: Record<string, string> = { math: "Математика", russian: "Русский язык" };

export default function TrainerPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [subject, setSubject] = useState<"math" | "russian">("math");
  const [task, setTask] = useState<Task | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadNext() {
    setLoading(true);
    setResult(null);
    setAnswer("");
    setError(null);
    try {
      const t = await apiFetch<Task>(`/api/v1/trainer/next-task?subject=${subject}`);
      setTask(t);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? "Для этого предмета пока нет заданий"
          : "Не удалось загрузить задание"
      );
      setTask(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    loadNext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, subject]);

  async function handleSubmit(chosenAnswer?: string) {
    const value = chosenAnswer ?? answer;
    if (!value.trim()) {
      setError("Введите ответ перед проверкой");
      return;
    }
    if (!task) return;
    setSubmitting(true);
    setError(null);
    try {
      const r = await apiFetch<SubmitResult>("/api/v1/trainer/submit", {
        method: "POST",
        body: JSON.stringify({ task_id: task.id, answer: value }),
      });
      setResult(r);
    } catch {
      setError("Не удалось проверить ответ");
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading || !user) return null;

  return (
    <Shell>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display font-extrabold text-2xl text-ink">Тренажёр</h1>
        <div className="flex gap-1 rounded-lg border border-hairline bg-card p-1">
          {(["math", "russian"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSubject(s)}
              className={`focus-ring rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                subject === s ? "bg-indigo text-white" : "text-muted hover:text-ink"
              }`}
            >
              {SUBJECT_LABELS[s]}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 max-w-xl">
        {loading && <p className="text-sm text-muted">Загрузка задания…</p>}

        {!loading && error && !task && <p className="text-sm text-brick">{error}</p>}

        {!loading && task && (
          <div className="rounded-card border border-hairline bg-card p-6">
            <p className="text-xs font-medium text-indigo uppercase tracking-wide">
              {task.topic}
            </p>
            <p className="mt-3 text-base text-ink leading-relaxed">{task.question}</p>

            {!result ? (
              <div className="mt-5">
                {task.options ? (
                  <div className="flex flex-col gap-2">
                    {task.options.map((opt) => (
                      <button
                        key={opt}
                        onClick={() => handleSubmit(opt)}
                        disabled={submitting}
                        className="focus-ring text-left rounded-lg border border-hairline px-4 py-2.5 text-sm text-ink hover:bg-paper disabled:opacity-50"
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <input
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                      placeholder="Ваш ответ"
                      className="focus-ring flex-1 rounded-lg border border-hairline bg-white px-3.5 py-2.5 text-sm text-ink"
                    />
                    <Button onClick={() => handleSubmit()} disabled={submitting}>
                      {submitting ? "Проверяем…" : "Проверить"}
                    </Button>
                  </div>
                )}
                {error && <p className="mt-2 text-sm text-brick">{error}</p>}
              </div>
            ) : (
              <div className="mt-5">
                <div
                  className={`rounded-lg px-4 py-3 text-sm font-medium ${
                    result.is_correct ? "bg-teal-soft text-teal" : "bg-brick-soft text-brick"
                  }`}
                >
                  {result.is_correct ? "Верно!" : `Неверно. Правильный ответ: ${result.correct_answer}`}
                </div>
                <p className="mt-3 text-sm text-ink leading-relaxed">{result.explanation}</p>
                <Button onClick={loadNext} className="mt-4">
                  Следующее задание
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </Shell>
  );
}
