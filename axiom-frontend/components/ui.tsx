"use client";

import { ButtonHTMLAttributes, InputHTMLAttributes, forwardRef } from "react";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" }) {
  const base =
    "focus-ring inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const styles =
    variant === "primary"
      ? "bg-indigo text-white hover:bg-indigo-hover"
      : "bg-transparent border border-hairline text-ink hover:bg-paper";
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}

export const TextField = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }
>(function TextField({ label, error, className = "", ...props }, ref) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-ink mb-1.5">{label}</span>
      <input
        ref={ref}
        className={`focus-ring w-full rounded-lg border ${
          error ? "border-brick" : "border-hairline"
        } bg-white px-3.5 py-2.5 text-sm text-ink placeholder:text-muted ${className}`}
        {...props}
      />
      {error && <span className="mt-1 block text-xs text-brick">{error}</span>}
    </label>
  );
});
