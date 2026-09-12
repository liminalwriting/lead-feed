import type { ApiPost } from "@/lib/api";
import type { Post } from "@/types/feed";

export function mapApiPost(post: ApiPost): Post {
  const username = post.channel?.username ?? "unknown";
  const title = post.channel?.title?.trim() || username;

  return {
    id: post.id,
    channel: {
      id: post.channel?.id ?? post.channel_id,
      username,
      title,
    },
    tgMessageId: post.tg_message_id,
    postedAt: post.posted_at,
    text: post.text,
    url: post.url ?? `https://t.me/${username}/${post.tg_message_id}`,
    isRepost: Boolean(post.is_repost),
    forwardFromName: post.forward_from_name,
    forwardFromUsername: post.forward_from_username,
    forwardFromUrl: post.forward_from_url,
    forwardDate: post.forward_date,
  };
}
