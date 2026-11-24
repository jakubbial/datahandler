import { getJson } from "./client";

export type Variable = {
  id: number;
  name: string;
  level: number;
  measureUnitId: number;
  measureUnitName: string | null;
};

export type VariableDetails = Variable & {
  n1: string | null;
  n2: string | null;
  n3: string | null;
  n4: string | null;
  n5: string | null;
  subjectId: string | null;
  description: string | null;
  years: number[];
};

export function fetchVariables(
  subjectId: string,
  signal?: AbortSignal,
): Promise<Variable[]> {
  const query = new URLSearchParams({ subject_id: subjectId }).toString();
  return getJson<Variable[]>(`/variables?${query}`, { signal });
}

export function fetchVariable(
  variableId: number,
  signal?: AbortSignal,
): Promise<VariableDetails> {
  return getJson<VariableDetails>(`/variables/${variableId}`, { signal });
}
