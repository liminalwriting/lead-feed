import type { Post } from "@/types/feed";
import { Button } from "@/components/ui/Button";
import { Label } from "@/components/ui/Label";

type PostCardProps = {
  post: Post;
  isNew?: boolean;
};

function formatPostedAt(iso: string): string {
  try {
    return new Intl.DateTimeFormat("en", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function forwardLabel(post: Post): string {
  if (post.forwardFromName && post.forwardFromUsername) {
    return `${post.forwardFromName} (@${post.forwardFromUsername})`;
  }
  if (post.forwardFromName) return post.forwardFromName;
  if (post.forwardFromUsername) return `@${post.forwardFromUsername}`;
  return "unknown source";
}

export function PostCard({ post, isNew = false }: PostCardProps) {
  return (
    <article className="relative rounded-lf bg-surface px-5 py-5 shadow-sm sm:px-6">
      {isNew ? (
        <Label tone="new" size="m" className="absolute top-3 right-3">
          New
        </Label>
      ) : null}
      <header className={`mb-2 ${isNew ? "pr-14" : ""}`}>
        {post.isRepost ? (
          <p className="mb-1.5 text-sm text-muted">
            Репост
            {post.forwardFromUrl ? (
              <>
                {" · "}
                <a
                  href={post.forwardFromUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-danger underline-offset-2 hover:underline"
                >
                  {forwardLabel(post)}
                </a>
              </>
            ) : (
              <> · {forwardLabel(post)}</>
            )}
          </p>
        ) : null}
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="font-medium text-ink">{post.channel.title}</span>
          <span className="text-sm text-muted">@{post.channel.username}</span>
          <time
            className="text-sm text-muted"
            dateTime={post.postedAt}
            title={post.postedAt}
          >
            {formatPostedAt(post.postedAt)} UTC
          </time>
        </div>
      </header>
      <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed text-ink">
        {post.text}
      </p>
      <div className="mt-4 flex justify-end">
        <Button
          variant="secondary"
          size="m"
          href={post.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Open in Telegram
        </Button>
      </div>
    </article>
  );
}
