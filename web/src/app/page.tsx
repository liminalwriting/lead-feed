import { FeedPage } from "@/components/FeedPage";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <main className="mx-auto w-full max-w-feed flex-1 px-4 py-10 sm:px-6">
        <FeedPage />
      </main>
    </div>
  );
}
