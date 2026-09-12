"use client";

import { Button } from "@/components/ui/Button";

type SyncButtonProps = {
  onSync?: () => void;
  disabled?: boolean;
  loading?: boolean;
  label?: string;
};

export function SyncButton({
  onSync,
  disabled = false,
  loading = false,
  label = "Update feed",
}: SyncButtonProps) {
  return (
    <Button
      variant="primary"
      size="m"
      disabled={disabled || loading}
      onClick={onSync}
    >
      {loading ? "Updating…" : label}
    </Button>
  );
}
