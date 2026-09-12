export type Channel = {
  id: number;
  username: string;
  title: string;
};

export type Post = {
  id: number;
  channel: Channel;
  tgMessageId: number;
  postedAt: string; // ISO 8601
  text: string;
  url: string;
  isRepost: boolean;
  forwardFromName: string | null;
  forwardFromUsername: string | null;
  forwardFromUrl: string | null;
  forwardDate: string | null;
};
