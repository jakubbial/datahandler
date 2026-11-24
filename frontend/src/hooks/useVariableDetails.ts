import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { fetchVariable, type VariableDetails } from "../api/variables";
import type { SubjectsErrorKind } from "./useSubjectPath";

export type VariableDetailsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: SubjectsErrorKind }
  | { status: "ready"; details: VariableDetails };

const variableDetailsCache = new Map<number, Promise<VariableDetails>>();

function loadVariableDetails(variableId: number): Promise<VariableDetails> {
  const cached = variableDetailsCache.get(variableId);
  if (cached) {
    return cached;
  }

  const request = fetchVariable(variableId);
  variableDetailsCache.set(variableId, request);
  request.catch(() => {
    if (variableDetailsCache.get(variableId) === request) {
      variableDetailsCache.delete(variableId);
    }
  });
  return request;
}

function toErrorKind(error: unknown): SubjectsErrorKind {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return "not-found";
      case 422:
        return "invalid-id";
      case 429:
        return "rate-limit";
      case 502:
        return "unavailable";
    }
  }
  return "unknown";
}

export function useVariableDetails(variableId: number | null) {
  const [result, setResult] = useState<{
    variableId: number;
    state: VariableDetailsState;
  } | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (variableId === null) {
      return;
    }

    let isActive = true;
    setResult(null);
    loadVariableDetails(variableId).then(
      (details) => {
        if (isActive) {
          setResult({
            variableId,
            state: { status: "ready", details },
          });
        }
      },
      (error: unknown) => {
        if (isActive) {
          setResult({
            variableId,
            state: { status: "error", error: toErrorKind(error) },
          });
        }
      },
    );

    return () => {
      isActive = false;
    };
  }, [variableId, retryCount]);

  const retry = useCallback(() => setRetryCount((count) => count + 1), []);

  const state: VariableDetailsState =
    variableId === null
      ? { status: "idle" }
      : result && result.variableId === variableId
        ? result.state
        : { status: "loading" };

  return { state, retry };
}
