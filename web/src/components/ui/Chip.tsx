import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ChipSize = "m";

type ChipProps = {
  /** Selected = active filter chip */
  selected?: boolean;
  size?: ChipSize;
  children: ReactNode;
  className?: string;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children">;

const sizeClass: Record<ChipSize, string> = {
  m: "rounded-full px-3.5 py-1.5 text-sm font-medium",
};

function cx(...parts: Array<string | false | undefined>) {
  return parts.filter(Boolean).join(" ");
}

/**
 * Choice / filter Chip — one item in a single-select Chips group.
 *
 * States: idle | selected
 * Size: M
 *
 * Idle ≈ Secondary surface; selected ≈ Primary accent.
 */
export function Chip({
  selected = false,
  size = "m",
  type = "button",
  className,
  children,
  ...rest
}: ChipProps) {
  return (
    <button
      type={type}
      aria-pressed={selected}
      className={cx(
        "inline-flex shrink-0 items-center justify-center border transition-colors",
        "disabled:cursor-not-allowed disabled:opacity-50",
        sizeClass[size],
        selected
          ? "border-accent bg-accent text-surface hover:border-accent-hover hover:bg-accent-hover"
          : "border-border bg-surface text-ink hover:bg-canvas",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
