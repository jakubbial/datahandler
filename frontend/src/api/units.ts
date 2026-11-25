import { getJson } from "./client";

export type Unit = { id: string; name: string };

const cache = new Map<string, Promise<Unit[]>>();

export function fetchUnits(level: 2 | 5, parentId?: string): Promise<Unit[]> {
  const query = new URLSearchParams({ level: String(level) });
  if (parentId) query.set("parent_id", parentId);
  const key = query.toString();
  const cached = cache.get(key);
  if (cached) return cached;

  const request = getJson<Unit[]>(`/units?${key}`);
  cache.set(key, request);
  request.catch(() => {
    if (cache.get(key) === request) cache.delete(key);
  });
  return request;
}
