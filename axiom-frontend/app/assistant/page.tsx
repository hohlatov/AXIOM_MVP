"use client";

import { useEffect, useRef, useState } from "react";
import { Shell } from "@/components/Shell";
import { useRequireAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };
type ChatResponse = { session_id: string; answer: string; sources: string[] };

const SUBJECT_LABELS: Record<string, string> = { math: "Математика", russian: "Русский язык" };

export default function AssistantPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [subject, setSubject] = useState<"math" | "russian">("math");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function startNewChat(newSubject: "math" | "russian") {
    setSubject(newSubject);
    setSessionId(null);
    setMessages([]);
    setError(null);
  }

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await apiFetch<ChatResponse>("/api/v1/assistant/chat", {
        method: "POST",
        body: JSON.stringify(
          sessionId ? { session_id: sessionId, message: text } : { subject, message: text }
        ),
      });
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
    } catch {
      setError("Не удалось получить ответ. Попробуйте ещё раз.");
    } finally {
      setSending(false);
    }
  }

  if (authLoading || !user) return null;

  return (
    <Shell>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display font-extrabold text-2xl text-ink">ИИ-ассистент</h1>
        <div className="flex gap-1 rounded-lg border border-hairline bg-card p-1">
          {(["math", "russian"] as const).map((s) => (
            <button
              key={s}
              onClick={() => startNewChat(s)}
              className={`focus-ring rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                subject === s ? "bg-indigo text-white" : "text-muted hover:text-ink"
              }`}
            >
              {SUBJECT_LABELS[s]}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 max-w-2xl">
        <div className="rounded-card border border-hairline bg-card flex flex-col h-[60vh]">
          <div className="flex-1 overflow-y-auto p-5 space-y-3">
            {messages.length === 0 && (
              <p className="text-sm text-muted text-center mt-10">
                Задайте вопрос по теме «{SUBJECT_LABELS[subject]}» — объясним «на пальцах».
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-indigo text-white"
                      : "bg-paper text-ink border border-hairline"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="rounded-lg px-4 py-2.5 text-sm bg-paper border border-hairline text-muted">
                  Печатает…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-hairline p-3">
            {error && <p className="mb-2 text-xs text-brick px-1">{error}</p>}
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                placeholder="Введите вопрос…"
                className="focus-ring flex-1 rounded-lg border border-hairline bg-white px-3.5 py-2.5 text-sm text-ink"
              />
              <button
                onClick={send}
                disabled={sending || !input.trim()}
                className="focus-ring rounded-lg bg-indigo px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-hover disabled:opacity-50"
              >
                Отправить
              </button>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
