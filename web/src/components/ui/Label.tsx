import type { ReactNode } from "react";

export type LabelTone = "new";
export type LabelSize = "m";

type LabelProps = {
  tone?: LabelTone;
  size?: LabelSize;
  children: ReactNode;
  className?: string;
};

const toneClass: Record<LabelTone, string> = {
  new: "bg-accent text-surface",
};

const sizeClass: Record<LabelSize, string> = {
  m: "rounded-lf px-2 py-0.5 text-xs font-medium tracking-wide uppercase",
};

function cx(...parts: Array<string | false | undefined>) {
  return parts.filter(Boolean).join(" ");
}

/**
 * Design-system Label / badge.
 * Tones: New. Sizes: M.
 */
export function Label({
  tone = "new",
  size = "m",
  children,
  className,
}: LabelProps) {
  return (
    <span className={cx("inline-flex items-center", toneClass[tone], sizeClass[size], className)}>
      {children}
    </span>
  );
}
