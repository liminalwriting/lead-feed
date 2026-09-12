"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Feed } from "@/components/Feed";
import {
  FeedFolderChips,
  FOLDER_ALL,
} from "@/components/FeedFolderChips";
import { FeedHeader } from "@/components/FeedHeader";
import { fetchFolders, fetchPosts, runSync } from "@/lib/api";
import { mapApiPost } from "@/lib/map-post";
import type { Post } from "@/types/feed";

const PAGE_SIZE = 20;

export function FeedPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [folders, setFolders] = useState<Array<{ id: number; title: string }>>(
    [],
  );
  const [folder, setFolder] = useState(FOLDER_ALL);
  const [newPostIds, setNewPostIds] = useState<Set<number>>(() => new Set());
  const seenPostIdsRef = useRef<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const rememberPosts = useCallback((items: Post[], markNew: boolean) => {
    const fresh: number[] = [];
    for (const post of items) {
      if (!seenPostIdsRef.current.has(post.id)) {
        seenPostIdsRef.current.add(post.id);
        if (markNew) fresh.push(post.id);
      }
    }
    if (markNew) {
      setNewPostIds(new Set(fresh));
    }
  }, []);

  const loadInitial = useCallback(
    async (folderKey: string, markNew = false) => {
      const page = await fetchPosts({ limit: PAGE_SIZE, folder: folderKey });
      const mapped = page.items.map(mapApiPost);
      rememberPosts(mapped, markNew);
      setPosts(mapped);
      setNextCursor(page.next_cursor);
    },
    [rememberPosts],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchFolders();
        if (!cancelled) setFolders(data);
      } catch {
        // Folders bar still works with Все / Без папок
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        await loadInitial(folder, false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load posts");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [folder, loadInitial]);

  const handleLoadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setError(null);
    try {
      const page = await fetchPosts({
        limit: PAGE_SIZE,
        cursor: nextCursor,
        folder,
      });
      const mapped = page.items.map(mapApiPost);
      rememberPosts(mapped, false);
      setPosts((prev) => {
        const seen = new Set(prev.map((p) => p.id));
        return [...prev, ...mapped.filter((p) => !seen.has(p.id))];
      });
      setNextCursor(page.next_cursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load more");
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    setStatus("Syncing…");
    try {
      const result = await runSync();
      setStatus(result.message);
      const folderData = await fetchFolders().catch(() => folders);
      setFolders(folderData);
      await loadInitial(folder, true);
    } catch (err) {
      setStatus(null);
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <>
      <FeedHeader
        onSync={handleSync}
        syncDisabled={loading || loadingMore}
        syncLoading={syncing}
        statusMessage={error ? `Error: ${error}` : status}
      />
      <FeedFolderChips
        value={folder}
        onValueChange={setFolder}
        folders={folders}
      />
      {loading ? (
        <p className="py-10 text-center text-muted">Loading feed…</p>
      ) : (
        <Feed
          posts={posts}
          newPostIds={newPostIds}
          hasMore={Boolean(nextCursor)}
          loadingMore={loadingMore}
          onLoadMore={handleLoadMore}
        />
      )}
    </>
  );
}
