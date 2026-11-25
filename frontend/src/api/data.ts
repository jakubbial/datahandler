import { getJson } from "./client";

export type UnitData = {
  unitId: string;
  unitName: string;
  values: { year: number; value: number | null; attributeId: number }[];
};

export function fetchVariableData(
  variableId: number,
  years: number[],
  unitLevel: number,
  unitParentId: string | null,
  signal?: AbortSignal,
): Promise<UnitData[]> {
  const query = new URLSearchParams();
  years.forEach((year) => query.append("year", String(year)));
  query.set("unit_level", String(unitLevel));
  if (unitParentId) query.set("unit_parent_id", unitParentId);
  else query.set("single_page", "true");
  return getJson<UnitData[]>(`/data/by-variable/${variableId}?${query}`, {
    signal,
  });
}
