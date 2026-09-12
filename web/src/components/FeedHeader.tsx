import { SyncButton } from "@/components/SyncButton";

type FeedHeaderProps = {
  title?: string;
  onSync?: () => void;
  syncDisabled?: boolean;
  syncLoading?: boolean;
  statusMessage?: string | null;
};

export function FeedHeader({
  title = "Lead Feed",
  onSync,
  syncDisabled,
  syncLoading,
  statusMessage,
}: FeedHeaderProps) {
  return (
    <header className="mb-8 border-b border-border pb-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-display text-3xl tracking-tight text-ink">{title}</p>
          <p className="mt-1 text-sm text-muted">
            Channels in one timeline. Sync runs only when you ask.
          </p>
        </div>
        <SyncButton
          onSync={onSync}
          disabled={syncDisabled}
          loading={syncLoading}
        />
      </div>
      {statusMessage ? (
        <p className="mt-3 text-sm text-muted" role="status">
          {statusMessage}
        </p>
      ) : null}
    </header>
  );
}
