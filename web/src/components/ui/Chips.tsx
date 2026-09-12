"use client";

import type { ReactNode } from "react";

import { Chip, type ChipSize } from "@/components/ui/Chip";

export type ChipOption<T extends string = string> = {
  value: T;
  label: ReactNode;
  disabled?: boolean;
};

type ChipsProps<T extends string = string> = {
  /** Controlled selected value — exactly one active chip */
  value: T;
  onValueChange: (value: T) => void;
  options: ChipOption<T>[];
  size?: ChipSize;
  /** Accessible name for the group */
  "aria-label"?: string;
  className?: string;
};

function cx(...parts: Array<string | false | undefined>) {
  return parts.filter(Boolean).join(" ");
}

/**
 * Single-select Chips group (choice chips).
 *
 * Use for feed filters: All | folder names | Without folders.
 * Only one chip is active at a time.
 */
export function Chips<T extends string = string>({
  value,
  onValueChange,
  options,
  size = "m",
  "aria-label": ariaLabel = "Filters",
  className,
}: ChipsProps<T>) {
  return (
    <div
      role="group"
      aria-label={ariaLabel}
      className={cx("flex flex-wrap gap-2", className)}
    >
      {options.map((option) => (
        <Chip
          key={option.value}
          size={size}
          selected={option.value === value}
          disabled={option.disabled}
          onClick={() => {
            if (!option.disabled && option.value !== value) {
              onValueChange(option.value);
            }
          }}
        >
          {option.label}
        </Chip>
      ))}
    </div>
  );
}
