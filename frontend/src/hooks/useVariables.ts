import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { fetchVariables, type Variable } from "../api/variables";
import type { SubjectsErrorKind } from "./useSubjectPath";

export type VariablesState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: SubjectsErrorKind }
  | { status: "ready"; variables: Variable[] };

const variablesSubjectIdPattern = /^P[A-Za-z0-9]{1,15}$/;

const variablesCache = new Map<string, Promise<Variable[]>>();

function loadVariables(subjectId: string): Promise<Variable[]> {
  const cached = variablesCache.get(subjectId);
  if (cached) {
    return cached;
  }

  const request = fetchVariables(subjectId);
  variablesCache.set(subjectId, request);
  // Failed requests must not stay cached, so a retry sends a new request.
  request.catch(() => {
    if (variablesCache.get(subjectId) === request) {
      variablesCache.delete(subjectId);
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

export function useVariables(subjectId: string | null) {
  const [result, setResult] = useState<{
    subjectId: string;
    state: VariablesState;
  } | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (subjectId === null) {
      return;
    }

    if (!variablesSubjectIdPattern.test(subjectId)) {
      setResult({ subjectId, state: { status: "error", error: "invalid-id" } });
      return;
    }

    let isActive = true;
    setResult(null);
    loadVariables(subjectId).then(
      (variables) => {
        if (isActive) {
          setResult({ subjectId, state: { status: "ready", variables } });
        }
      },
      (error: unknown) => {
        if (isActive) {
          setResult({
            subjectId,
            state: { status: "error", error: toErrorKind(error) },
          });
        }
      },
    );

    return () => {
      isActive = false;
    };
  }, [subjectId, retryCount]);

  const retry = useCallback(() => setRetryCount((count) => count + 1), []);

  // A result for a previous subject must not be shown after the subject changes.
  const state: VariablesState =
    subjectId === null
      ? { status: "idle" }
      : result && result.subjectId === subjectId
        ? result.state
        : { status: "loading" };

  return { state, retry };
}
