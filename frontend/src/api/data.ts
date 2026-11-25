import { getJson } from "./client";

export type UnitData = {
  unitId: string;
  unitName: string;
  values: {
    year: number;
    value: number | null;
    attributeId: number;
    attributeName: string | null;
    attributeDescription: string | null;
    attributeSymbol: string | null;
  }[];
};

export type VariableDataResponse = {
  measureUnit: { id: number; name: string | null };
  lastUpdate: string | null;
  units: UnitData[];
};

export function fetchVariableData(
  variableId: number,
  years: number[],
  unitLevel: number,
  unitParentId: string | null,
  signal?: AbortSignal,
): Promise<VariableDataResponse> {
  const query = new URLSearchParams();
  years.forEach((year) => query.append("year", String(year)));
  query.set("unit_level", String(unitLevel));
  if (unitParentId) query.set("unit_parent_id", unitParentId);
  else query.set("single_page", "true");
  return getJson<VariableDataResponse>(
    `/data/by-variable/${variableId}?${query}`,
    {
      signal,
    },
  );
}
