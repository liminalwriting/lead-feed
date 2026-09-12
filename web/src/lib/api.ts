const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export type ApiChannel = {
  id: number;
  username: string;
  title: string | null;
  tg_id: number | null;
  last_message_id: number | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ApiPost = {
  id: number;
  channel_id: number;
  tg_message_id: number;
  posted_at: string;
  text: string;
  url: string | null;
  is_repost: boolean;
  forward_from_name: string | null;
  forward_from_username: string | null;
  forward_from_tg_id: number | null;
  forward_from_message_id: number | null;
  forward_from_url: string | null;
  forward_date: string | null;
  created_at: string;
  channel: ApiChannel | null;
};

export type PostsPage = {
  items: ApiPost[];
  next_cursor: string | null;
};

export type ApiFolder = {
  id: number;
  title: string;
};

export type SyncChannelResult = {
  username: string;
  added: number;
  error: string | null;
};

export type SyncResponse = {
  status: string;
  message: string;
  added: number;
  channels: SyncChannelResult[];
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function fetchPosts(opts?: {
  limit?: number;
  cursor?: string | null;
  folder?: string | null;
}): Promise<PostsPage> {
  const limit = opts?.limit ?? 20;
  const params = new URLSearchParams({ limit: String(limit) });
  if (opts?.cursor) params.set("cursor", opts.cursor);
  if (opts?.folder && opts.folder !== "all") params.set("folder", opts.folder);
  return apiFetch<PostsPage>(`/posts?${params.toString()}`);
}

export function fetchFolders(): Promise<ApiFolder[]> {
  return apiFetch<ApiFolder[]>("/folders");
}

export function runSync(): Promise<SyncResponse> {
  return apiFetch<SyncResponse>("/sync", { method: "POST" });
}
