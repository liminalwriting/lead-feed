import type { Post } from "@/types/feed";
import { PostCard } from "@/components/PostCard";
import { Button } from "@/components/ui/Button";

type FeedProps = {
  posts: Post[];
  newPostIds?: ReadonlySet<number>;
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
};

export function Feed({
  posts,
  newPostIds,
  hasMore = false,
  loadingMore = false,
  onLoadMore,
}: FeedProps) {
  if (posts.length === 0) {
    return (
      <p className="py-10 text-center text-muted">
        No posts yet. Add channels and hit Update when sync is ready.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {posts.map((post) => (
        <PostCard
          key={post.id}
          post={post}
          isNew={newPostIds?.has(post.id) ?? false}
        />
      ))}
      {hasMore ? (
        <div className="flex justify-center pt-2 pb-4">
          <Button
            variant="secondary"
            size="m"
            disabled={loadingMore}
            onClick={onLoadMore}
          >
            {loadingMore ? "Загрузка…" : "Загрузить ещё"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
