import { getJson } from "./client";

export type Subject = {
  id: string;
  parentId: string | null;
  name: string;
  hasVariables: boolean;
  levels: number[];
};

export function fetchSubjects(
  parentId?: string | null,
  signal?: AbortSignal,
): Promise<Subject[]> {
  const query = parentId
    ? `?${new URLSearchParams({ parent_id: parentId }).toString()}`
    : "";
  return getJson<Subject[]>(`/subjects${query}`, { signal });
}
