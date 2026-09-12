"use client";

import { Chips, type ChipOption } from "@/components/ui/Chips";

export const FOLDER_ALL = "all";
export const FOLDER_NONE = "none";

type FeedFolderChipsProps = {
  value: string;
  onValueChange: (value: string) => void;
  folders: Array<{ id: number; title: string }>;
};

export function FeedFolderChips({
  value,
  onValueChange,
  folders,
}: FeedFolderChipsProps) {
  const options: ChipOption[] = [
    { value: FOLDER_ALL, label: "Все" },
    ...folders.map((folder) => ({
      value: String(folder.id),
      label: folder.title,
    })),
    { value: FOLDER_NONE, label: "Без папок" },
  ];

  return (
    <Chips
      aria-label="Папки"
      value={value}
      onValueChange={onValueChange}
      options={options}
      className="mb-6"
    />
  );
}
